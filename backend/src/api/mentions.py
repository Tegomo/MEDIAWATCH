"""Endpoints API pour les mentions"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from urllib.parse import urlparse
import asyncio
import hashlib
import logging
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.api.auth import get_current_active_user
from src.services.mention_service import MentionService
from src.services.scraping.jina_reader import get_jina_reader
from src.services.ai.openrouter import get_openrouter_service, REJET_MARKER
from src.services.ai.content_filter import is_valid_article, is_blocked_url, clean_markdown
from src.schemas.mention import (
    MentionResponse,
    MentionDetailResponse,
    MentionListResponse,
    ArticleResponse,
    SourceResponse,
    KeywordBrief,
)

_scan_logger = logging.getLogger("scan")

# État global du scan (dict en mémoire, suffisant pour single-worker)
_scan_state = {
    "running": False,
    "progress": "",
    "result": None,
    "counts": {
        "articles": 0,
        "mentions": 0,
    },
}

router = APIRouter(prefix="/mentions", tags=["Mentions"])


def _mention_to_response(mention: dict) -> MentionResponse:
    """Convertit un dict mention Supabase en MentionResponse."""
    article_resp = None
    article = mention.get("article")
    if article:
        source_resp = None
        source = article.get("source")
        if source:
            source_resp = SourceResponse(
                id=source["id"],
                name=source["name"],
                url=source["url"],
                type=source["type"],
            )
        article_resp = ArticleResponse(
            id=article["id"],
            title=article["title"],
            url=article["url"],
            author=article.get("author"),
            published_at=article["published_at"],
            source=source_resp,
        )

    keyword_resp = None
    keyword = mention.get("keyword")
    if keyword:
        keyword_resp = KeywordBrief(
            id=keyword["id"],
            text=keyword["text"],
            category=keyword["category"],
        )

    return MentionResponse(
        id=mention["id"],
        matched_text=mention["matched_text"],
        match_context=mention["match_context"],
        sentiment_score=mention["sentiment_score"],
        sentiment_label=mention["sentiment_label"],
        visibility_score=mention["visibility_score"],
        theme=mention.get("theme"),
        detected_at=mention["detected_at"],
        keyword=keyword_resp,
        article=article_resp,
    )


@router.get("", response_model=MentionListResponse)
async def list_mentions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword_id: Optional[UUID] = Query(None),
    sentiment: Optional[str] = Query(None),
    source_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> MentionListResponse:
    """
    Liste les mentions pour l'organisation de l'utilisateur.
    Supporte pagination, filtres par keyword, sentiment, source, dates, thème et recherche texte.
    """
    service = MentionService(db)
    mentions, total = service.list_mentions(
        organization_id=current_user["organization_id"],
        limit=limit,
        offset=offset,
        keyword_id=keyword_id,
        sentiment=sentiment,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        theme=theme,
    )

    return MentionListResponse(
        mentions=[_mention_to_response(m) for m in mentions],
        total=total,
        limit=limit,
        offset=offset,
    )


async def _db_call(fn, *args, **kwargs):
    """Exécute un appel SupabaseDB synchrone sans bloquer l'event loop."""
    return await asyncio.to_thread(fn, *args, **kwargs)


def _normalize(text: str) -> str:
    """Minuscule + suppression des accents (é→e, à→a, etc.)."""
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def _keyword_matches(kw_text: str, text_lower: str) -> bool:
    """
    Vérifie si un mot-clé matche dans un texte (insensible à la casse et aux accents).
    Stratégie : match exact OU tous les mots significatifs (≥3 chars) présents.
    """
    kw_norm = _normalize(kw_text)
    text_norm = _normalize(text_lower)
    # Match exact
    if kw_norm in text_norm:
        return True
    # Match large : tous les mots significatifs du mot-clé doivent être présents
    words = [w for w in re.split(r'[\s:,;/\-]+', kw_norm) if len(w) >= 3]
    if words and all(w in text_norm for w in words):
        return True
    return False


def _extract_context(content: str, kw_text: str, max_chars: int = 200) -> str:
    """Extrait le contexte autour de la première occurrence du mot-clé."""
    kw_lower = kw_text.lower()
    content_lower = content.lower()
    # Chercher le match exact d'abord
    idx = content_lower.find(kw_lower)
    if idx == -1:
        # Sinon chercher le premier mot significatif
        words = [w for w in re.split(r'[\s:,;/\-]+', kw_lower) if len(w) >= 3]
        for w in words:
            idx = content_lower.find(w)
            if idx != -1:
                break
    if idx == -1:
        return content[:max_chars * 2]

    start = max(0, idx - max_chars)
    end = min(len(content), idx + len(kw_text) + max_chars)
    context = content[start:end]
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."
    return context


async def _process_article_nlp(
    db: SupabaseDB,
    article: dict,
    active_keywords: list[dict],
) -> int:
    """
    Analyse NLP d'un seul article : matching mots-clés et création de mentions.
    Cherche dans le titre ET le contenu avec un matching large.
    Appelé immédiatement après l'insertion de chaque article.
    Retourne le nombre de mentions créées.
    """
    title = article.get("title", "")
    content = article.get("cleaned_content") or article.get("raw_content", "")
    if not title and not content:
        await _db_call(db.update, "articles", {"nlp_processed": datetime.utcnow().isoformat()}, id=f"eq.{article['id']}")
        return 0

    title_lower = title.lower()
    content_lower = content.lower()
    # Texte combiné pour la recherche
    searchable = title_lower + " " + content_lower
    mentions_created = 0

    for keyword in active_keywords:
        kw_text = keyword.get("normalized_text") or keyword.get("text", "")
        if not kw_text:
            continue

        if not _keyword_matches(kw_text, searchable):
            continue

        existing = await _db_call(
            db.select_one, "mentions",
            keyword_id=f"eq.{keyword['id']}", article_id=f"eq.{article['id']}",
        )
        if existing:
            continue

        # Extraire le contexte du contenu ou du titre
        if _keyword_matches(kw_text, content_lower):
            context = _extract_context(content, kw_text)
        else:
            context = _extract_context(title, kw_text)

        now = datetime.utcnow().isoformat()
        await _db_call(db.insert_one, "mentions", {
            "keyword_id": keyword["id"],
            "article_id": article["id"],
            "matched_text": keyword["text"],
            "match_context": context,
            "sentiment_score": 0.0,
            "sentiment_label": "NEUTRAL",
            "visibility_score": 0.5,
            "detected_at": now,
        })
        mentions_created += 1
        await _db_call(db.update, "keywords", {
            "total_mentions_count": keyword.get("total_mentions_count", 0) + 1,
            "last_mention_at": now,
        }, id=f"eq.{keyword['id']}")

    await _db_call(db.update, "articles", {"nlp_processed": datetime.utcnow().isoformat()}, id=f"eq.{article['id']}")
    return mentions_created


async def _run_scan(
    org_id: str,
    keyword_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Exécute le scan en arrière-plan. Met à jour _scan_state au fur et à mesure.
    
    Args:
        org_id: ID de l'organisation
        keyword_id: Si fourni, ne scanner que ce mot-clé
        date_from: Date début (ISO) pour filtrer la recherche web
        date_to: Date fin (ISO) pour filtrer la recherche web
    """
    db = SupabaseDB()

    try:
        kw_filters = {"organization_id": f"eq.{org_id}", "enabled": f"eq.true"}
        if keyword_id:
            kw_filters["id"] = f"eq.{keyword_id}"
        active_keywords = await _db_call(db.select, "keywords", **kw_filters)
        if not active_keywords:
            _scan_state["result"] = {"success": False, "message": "Aucun mot-clé actif" + (" pour cet ID." if keyword_id else ".")}
            return

        jina = get_jina_reader()
        ai = get_openrouter_service()
        ai_enabled = ai.is_configured
        if ai_enabled:
            _scan_logger.info(f"IA activée (modèle: {ai.model})")
        else:
            _scan_logger.info("IA non configurée, stockage du contenu brut")
        sources = await _db_call(db.select, "sources", scraping_enabled=f"eq.true")
        _scan_state["progress"] = f"0/{len(sources)} sources"
        _scan_logger.info(f"Scan: {len(sources)} sources, {len(active_keywords)} mots-clés")

        total_article_links = 0
        total_new_articles = 0
        total_mentions = 0
        scrape_errors: list[str] = []
        MAX_ARTICLES_PER_SOURCE = 5
        _scan_state["counts"] = {"articles": 0, "mentions": 0}

        for i, source in enumerate(sources):
            source_url = source["url"]
            source_name = source["name"]
            domain = urlparse(source_url).netloc.replace("www.", "")
            _scan_state["progress"] = f"{i+1}/{len(sources)} — {source_name}"

            try:
                _scan_logger.info(f"Scan [{source_name}]: découverte liens sur {source_url}")
                article_urls = await asyncio.wait_for(
                    jina.extract_article_links(source_url, domain),
                    timeout=60,
                )
                total_article_links += len(article_urls)
                _scan_logger.info(f"Scan [{source_name}]: {len(article_urls)} liens")

                if not article_urls:
                    scrape_errors.append(f"{source_name}: aucun lien trouvé")
                    await _db_call(db.update, "sources", {
                        "last_scrape_at": datetime.utcnow().isoformat(),
                        "last_error_message": "Aucun lien d'article trouvé",
                    }, id=f"eq.{source['id']}")
                    continue

                new_for_source = 0
                for article_url in article_urls:
                    if new_for_source >= MAX_ARTICLES_PER_SOURCE:
                        break

                    existing = await _db_call(db.select_one, "articles", url=f"eq.{article_url}")
                    if existing:
                        continue

                    try:
                        _scan_state["progress"] = f"{i+1}/{len(sources)} — {source_name} — article {new_for_source+1}"
                        data = await asyncio.wait_for(jina.read_url(article_url), timeout=60)
                        if not data:
                            continue

                        title = data.get("title", "")
                        content = data.get("content", "")
                        if not title or len(content) < 100:
                            continue

                        # Filtre de qualité : rejeter les pages non-articles
                        if not is_valid_article(title, content):
                            _scan_logger.info(f"Scan [{source_name}]: rejeté (qualité): {title[:50]}")
                            continue

                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        now = datetime.utcnow().isoformat()

                        published_at = now
                        if data.get("published_date"):
                            parsed = jina.parse_published_date(data["published_date"])
                            if parsed:
                                published_at = parsed.isoformat()

                        # Nettoyage IA si configuré, sinon nettoyage basique markdown
                        cleaned = clean_markdown(content)
                        if ai_enabled:
                            try:
                                _scan_state["progress"] = f"{i+1}/{len(sources)} — {source_name} — IA article {new_for_source+1}"
                                ai_result = await asyncio.wait_for(
                                    ai.cleanup_article(content, title),
                                    timeout=120,
                                )
                                if ai_result == REJET_MARKER:
                                    cleaned = f"{title}\n\nSource : {article_url}\n\n[Contenu non-article : page vidéo, galerie, navigation ou autre contenu non éditorial]"
                                    _scan_logger.info(f"Scan [{source_name}]: non-article sauvé: {title[:50]}")
                                elif ai_result:
                                    cleaned = ai_result
                                    _scan_logger.info(f"Scan [{source_name}]: IA nettoyé: {title[:40]}")
                            except Exception as ai_err:
                                _scan_logger.warning(f"Scan [{source_name}]: IA erreur: {str(ai_err)[:80]}")

                        inserted = await _db_call(db.insert_one, "articles", {
                            "title": title,
                            "url": article_url,
                            "content_hash": content_hash,
                            "raw_content": content,
                            "cleaned_content": cleaned,
                            "author": data.get("author"),
                            "published_at": published_at,
                            "scraped_at": now,
                            "source_id": source["id"],
                        })
                        total_new_articles += 1
                        new_for_source += 1
                        _scan_state["counts"]["articles"] = total_new_articles
                        _scan_logger.info(f"Scan [{source_name}]: sauvé: {title[:60]}")

                        # NLP immédiat : créer les mentions pour cet article
                        try:
                            m = await _process_article_nlp(db, inserted, active_keywords)
                            total_mentions += m
                            _scan_state["counts"]["mentions"] = total_mentions
                            if m:
                                _scan_logger.info(f"Scan [{source_name}]: {m} mention(s) créée(s)")
                        except Exception as nlp_err:
                            _scan_logger.warning(f"Scan [{source_name}]: NLP erreur: {str(nlp_err)[:80]}")

                    except asyncio.TimeoutError:
                        scrape_errors.append(f"{source_name}: timeout article")
                    except Exception as e:
                        scrape_errors.append(f"{source_name}: {str(e)[:80]}")

                await _db_call(db.update, "sources", {
                    "last_scrape_at": datetime.utcnow().isoformat(),
                    "last_success_at": datetime.utcnow().isoformat(),
                    "consecutive_failures": 0,
                    "last_error_message": None,
                }, id=f"eq.{source['id']}")

            except asyncio.TimeoutError:
                scrape_errors.append(f"{source_name}: timeout découverte liens")
                try:
                    await _db_call(db.update, "sources", {
                        "consecutive_failures": source.get("consecutive_failures", 0) + 1,
                        "last_error_message": "Timeout découverte liens",
                        "last_scrape_at": datetime.utcnow().isoformat(),
                    }, id=f"eq.{source['id']}")
                except Exception:
                    pass
            except Exception as e:
                scrape_errors.append(f"{source_name}: {str(e)[:100]}")
                try:
                    await _db_call(db.update, "sources", {
                        "consecutive_failures": source.get("consecutive_failures", 0) + 1,
                        "last_error_message": str(e)[:500],
                        "last_scrape_at": datetime.utcnow().isoformat(),
                    }, id=f"eq.{source['id']}")
                except Exception:
                    pass

        # ── Phase 2 : Recherche globale internet via Jina Search ──
        _scan_state["progress"] = "Recherche globale internet…"
        _scan_logger.info("Phase 2: recherche globale internet")
        MAX_SEARCH_RESULTS = 5
        search_new_articles = 0
        search_errors: list[str] = []
        nlp_errors = 0

        # Créer ou récupérer la source spéciale "Recherche Web"
        web_search_source = await _db_call(
            db.select_one, "sources", name="eq.Recherche Web",
        )
        if not web_search_source:
            now_ts = datetime.utcnow().isoformat()
            web_search_source = await _db_call(db.insert_one, "sources", {
                "name": "Recherche Web",
                "url": "https://s.jina.ai",
                "type": "API",
                "scraper_class": "jina_search",
                "scraping_enabled": False,
                "prestige_score": 30.0,
                "consecutive_failures": 0,
                "created_at": now_ts,
                "updated_at": now_ts,
            })
            _scan_logger.info("Source 'Recherche Web' créée")
        web_search_source_id = web_search_source["id"]

        for ki, keyword in enumerate(active_keywords):
            kw_text = keyword.get("text", "")
            if not kw_text:
                continue

            # Enrichir la requête de recherche avec la période si fournie
            search_query = kw_text
            if date_from or date_to:
                if date_from and date_to:
                    search_query = f"{kw_text} after:{date_from[:10]} before:{date_to[:10]}"
                elif date_from:
                    search_query = f"{kw_text} after:{date_from[:10]}"
                elif date_to:
                    search_query = f"{kw_text} before:{date_to[:10]}"

            _scan_state["progress"] = f"Recherche web {ki+1}/{len(active_keywords)} — \"{kw_text}\""
            try:
                results = await asyncio.wait_for(
                    jina.search_web(search_query, num_results=MAX_SEARCH_RESULTS),
                    timeout=60,
                )
                _scan_logger.info(f"Search [{kw_text}]: {len(results)} résultats")

                for result in results:
                    result_url = result.get("url", "")
                    if not result_url:
                        continue

                    # Filtrer les réseaux sociaux et domaines non pertinents
                    if is_blocked_url(result_url):
                        _scan_logger.info(f"Search [{kw_text}]: URL bloquée: {result_url[:60]}")
                        continue

                    existing = await _db_call(db.select_one, "articles", url=f"eq.{result_url}")
                    if existing:
                        continue

                    try:
                        data = await asyncio.wait_for(jina.read_url(result_url), timeout=60)
                        if not data:
                            continue

                        title = data.get("title", "")
                        content = data.get("content", "")
                        if not title or len(content) < 100:
                            continue

                        # Filtre de qualité : rejeter les pages non-articles
                        if not is_valid_article(title, content):
                            _scan_logger.info(f"Search [{kw_text}]: rejeté (qualité): {title[:50]}")
                            continue

                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        now = datetime.utcnow().isoformat()

                        published_at = now
                        if data.get("published_date"):
                            parsed_date = jina.parse_published_date(data["published_date"])
                            if parsed_date:
                                published_at = parsed_date.isoformat()

                        # Nettoyage IA si configuré, sinon nettoyage basique markdown
                        cleaned = clean_markdown(content)
                        if ai_enabled:
                            try:
                                _scan_state["progress"] = f"Recherche web {ki+1}/{len(active_keywords)} — IA \"{kw_text}\""
                                ai_result = await asyncio.wait_for(
                                    ai.cleanup_article(content, title),
                                    timeout=120,
                                )
                                if ai_result == REJET_MARKER:
                                    cleaned = f"{title}\n\nSource : {result_url}\n\n[Contenu non-article : page vidéo, galerie, navigation ou autre contenu non éditorial]"
                                    _scan_logger.info(f"Search [{kw_text}]: non-article sauvé: {title[:50]}")
                                elif ai_result:
                                    cleaned = ai_result
                                    _scan_logger.info(f"Search [{kw_text}]: IA nettoyé: {title[:40]}")
                            except Exception as ai_err:
                                _scan_logger.warning(f"Search [{kw_text}]: IA erreur: {str(ai_err)[:80]}")

                        inserted = await _db_call(db.insert_one, "articles", {
                            "title": title,
                            "url": result_url,
                            "content_hash": content_hash,
                            "raw_content": content,
                            "cleaned_content": cleaned,
                            "author": data.get("author"),
                            "published_at": published_at,
                            "scraped_at": now,
                            "source_id": web_search_source_id,
                        })
                        search_new_articles += 1
                        total_new_articles += 1
                        _scan_state["counts"]["articles"] = total_new_articles
                        _scan_logger.info(f"Search [{kw_text}]: sauvé: {title[:60]}")

                        # NLP immédiat : créer les mentions pour cet article
                        try:
                            m = await _process_article_nlp(db, inserted, active_keywords)
                            total_mentions += m
                            _scan_state["counts"]["mentions"] = total_mentions
                            if m:
                                _scan_logger.info(f"Search [{kw_text}]: {m} mention(s) créée(s)")
                        except Exception as nlp_err:
                            nlp_errors += 1
                            _scan_logger.warning(f"Search [{kw_text}]: NLP erreur: {str(nlp_err)[:80]}")

                    except asyncio.TimeoutError:
                        search_errors.append(f"search({kw_text}): timeout article")
                    except Exception as e:
                        search_errors.append(f"search({kw_text}): {str(e)[:80]}")

            except asyncio.TimeoutError:
                search_errors.append(f"search({kw_text}): timeout recherche")
            except Exception as e:
                search_errors.append(f"search({kw_text}): {str(e)[:80]}")

        scrape_errors.extend(search_errors)
        _scan_logger.info(f"Recherche globale: {search_new_articles} nouveaux articles")

        _scan_state["result"] = {
            "success": True,
            "message": "Scan terminé",
            "details": {
                "sources_scannees": len(sources),
                "liens_articles": total_article_links,
                "nouveaux_articles_sources": total_new_articles - search_new_articles,
                "nouveaux_articles_recherche": search_new_articles,
                "nouveaux_articles_total": total_new_articles,
                "articles_analyses": total_new_articles,
                "mentions_creees": total_mentions,
                "erreurs_scraping": scrape_errors,
                "erreurs_nlp": nlp_errors,
            },
        }
        _scan_logger.info(f"Scan terminé: {total_new_articles} articles ({search_new_articles} via recherche), {total_mentions} mentions")

    except Exception as e:
        _scan_state["result"] = {"success": False, "message": f"Erreur scan: {str(e)[:200]}"}
        _scan_logger.error(f"Scan erreur fatale: {e}", exc_info=True)
    finally:
        _scan_state["running"] = False


class ScanRequest(BaseModel):
    keyword_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@router.post("/scan")
async def scan_mentions(
    body: ScanRequest = ScanRequest(),
    current_user: dict = Depends(get_current_active_user),
):
    """Lance un scan en arrière-plan. Retourne immédiatement.
    
    Body optionnel:
        keyword_id: Scanner uniquement ce mot-clé
        date_from: Date début (ISO) pour filtrer la recherche
        date_to: Date fin (ISO) pour filtrer la recherche
    """
    if _scan_state["running"]:
        return {"success": False, "message": "Un scan est déjà en cours.", "progress": _scan_state["progress"]}

    org_id = current_user["organization_id"]
    _scan_state["running"] = True
    _scan_state["progress"] = "Démarrage…"
    _scan_state["result"] = None

    asyncio.create_task(_run_scan(
        org_id,
        keyword_id=body.keyword_id,
        date_from=body.date_from,
        date_to=body.date_to,
    ))

    return {"success": True, "message": "Scan lancé en arrière-plan."}


@router.get("/scan/status")
async def scan_status(
    current_user: dict = Depends(get_current_active_user),
):
    """Retourne l'état du scan en cours ou le dernier résultat."""
    return {
        "running": _scan_state["running"],
        "progress": _scan_state["progress"],
        "result": _scan_state["result"],
        "counts": _scan_state.get("counts", {"articles": 0, "mentions": 0}),
    }


class ScanUrlRequest(BaseModel):
    url: str


@router.post("/scan/url")
async def scan_url(
    body: ScanUrlRequest,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """
    Scanne une URL spécifique manuellement.
    Scrape l'article, applique le nettoyage IA, et crée les mentions immédiatement.
    """
    org_id = current_user["organization_id"]
    article_url = body.url.strip()

    if not article_url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL invalide")

    # Vérifier si l'article existe déjà
    existing = db.select_one("articles", url=f"eq.{article_url}")
    if existing:
        # Re-analyser le NLP sur cet article existant
        kw_filters = {"organization_id": f"eq.{org_id}", "enabled": "eq.true"}
        active_keywords = db.select("keywords", **kw_filters)
        mentions = await _process_article_nlp(db, existing, active_keywords)
        return {
            "success": True,
            "message": f"Article déjà en base. {mentions} nouvelle(s) mention(s) créée(s).",
            "article_id": existing["id"],
            "mentions_created": mentions,
        }

    # Scraper l'URL
    jina = get_jina_reader()
    try:
        data = await asyncio.wait_for(jina.read_url(article_url), timeout=60)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Timeout lors du scraping de l'URL")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur scraping: {str(e)[:200]}")

    if not data:
        raise HTTPException(status_code=422, detail="Impossible d'extraire le contenu de cette URL")

    title = data.get("title", "")
    content = data.get("content", "")
    if not title or len(content) < 50:
        raise HTTPException(status_code=422, detail="Contenu insuffisant (titre manquant ou contenu trop court)")

    # Nettoyage
    cleaned = clean_markdown(content)
    ai_rejected = False
    ai = get_openrouter_service()
    if ai.is_configured:
        try:
            ai_result = await asyncio.wait_for(ai.cleanup_article(content, title), timeout=120)
            if ai_result == REJET_MARKER:
                ai_rejected = True
                cleaned = f"{title}\n\nSource : {article_url}\n\n[Contenu non-article : page vidéo, galerie, navigation ou autre contenu non éditorial]"
                logger.info(f"scan_url: non-article sauvé: {title[:60]}")
            elif ai_result:
                cleaned = ai_result
                logger.info(f"scan_url: IA nettoyé ({len(ai_result)} chars): {title[:60]}")
        except Exception as e:
            logger.warning(f"scan_url: IA erreur: {str(e)[:120]}")

    content_hash = hashlib.sha256(content.encode()).hexdigest()
    now = datetime.utcnow().isoformat()
    published_at = now
    if data.get("published_date"):
        parsed = jina.parse_published_date(data["published_date"])
        if parsed:
            published_at = parsed.isoformat()

    # Trouver ou créer la source "Scan Manuel"
    manual_source = db.select_one("sources", name="eq.Scan Manuel")
    if not manual_source:
        manual_source = db.insert_one("sources", {
            "name": "Scan Manuel",
            "url": "manual",
            "type": "API",
            "scraper_class": "manual",
            "scraping_enabled": False,
            "prestige_score": 50,
            "consecutive_failures": 0,
            "created_at": now,
            "updated_at": now,
        })

    inserted = db.insert_one("articles", {
        "title": title,
        "url": article_url,
        "content_hash": content_hash,
        "raw_content": content,
        "cleaned_content": cleaned,
        "author": data.get("author"),
        "published_at": published_at,
        "scraped_at": now,
        "source_id": manual_source["id"],
    })

    # NLP immédiat
    kw_filters = {"organization_id": f"eq.{org_id}", "enabled": "eq.true"}
    active_keywords = db.select("keywords", **kw_filters)
    mentions = await _process_article_nlp(db, inserted, active_keywords)

    warning = ""
    if ai_rejected:
        warning = " (Attention: contenu identifié comme non-article par l'IA — page vidéo, navigation, etc.)"

    return {
        "success": True,
        "message": f"Article scanné: \"{title[:60]}\". {mentions} mention(s) créée(s).{warning}",
        "article_id": inserted["id"],
        "article_title": title,
        "mentions_created": mentions,
        "ai_rejected": ai_rejected,
    }


@router.get("/stats")
async def get_mention_stats(
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Statistiques rapides des mentions pour le dashboard."""
    service = MentionService(db)
    return service.get_stats(current_user["organization_id"])


@router.get("/{mention_id}", response_model=MentionDetailResponse)
async def get_mention(
    mention_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> MentionDetailResponse:
    """Récupère les détails complets d'une mention."""
    service = MentionService(db)
    mention = service.get_mention(mention_id, current_user["organization_id"])

    if not mention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mention non trouvée",
        )

    base = _mention_to_response(mention)
    article = mention.get("article", {})

    return MentionDetailResponse(
        **base.model_dump(),
        extracted_entities=mention.get("extracted_entities"),
        alert_sent=mention.get("alert_sent"),
        article_content=article.get("cleaned_content") if article else None,
    )
