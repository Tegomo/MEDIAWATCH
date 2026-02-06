"""Endpoints API pour les mentions"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.services.mention_service import MentionService
from src.schemas.mention import (
    MentionResponse,
    MentionDetailResponse,
    MentionListResponse,
    ArticleResponse,
    SourceResponse,
    KeywordBrief,
)

router = APIRouter(prefix="/mentions", tags=["Mentions"])


def _mention_to_response(mention) -> MentionResponse:
    """Convertit un objet Mention en MentionResponse."""
    article_resp = None
    if mention.article:
        source_resp = None
        if mention.article.source:
            source_resp = SourceResponse(
                id=mention.article.source.id,
                name=mention.article.source.name,
                url=mention.article.source.url,
                type=mention.article.source.type.value,
            )
        article_resp = ArticleResponse(
            id=mention.article.id,
            title=mention.article.title,
            url=mention.article.url,
            author=mention.article.author,
            published_at=mention.article.published_at,
            source=source_resp,
        )

    keyword_resp = None
    if mention.keyword:
        keyword_resp = KeywordBrief(
            id=mention.keyword.id,
            text=mention.keyword.text,
            category=mention.keyword.category.value,
        )

    return MentionResponse(
        id=mention.id,
        matched_text=mention.matched_text,
        match_context=mention.match_context,
        sentiment_score=mention.sentiment_score,
        sentiment_label=mention.sentiment_label.value,
        visibility_score=mention.visibility_score,
        theme=mention.theme.value if mention.theme else None,
        detected_at=mention.detected_at,
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MentionListResponse:
    """
    Liste les mentions pour l'organisation de l'utilisateur.
    Supporte pagination, filtres par keyword, sentiment, source, dates, thème et recherche texte.
    """
    service = MentionService(db)
    mentions, total = service.list_mentions(
        organization_id=current_user.organization_id,
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


@router.post("/scan")
async def scan_mentions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Lance un scan manuel: scrape les sources actives puis traite les articles
    avec le pipeline NLP pour détecter de nouvelles mentions.
    """
    from src.models.source import Source
    from src.models.article import Article
    from src.models.keyword import Keyword
    from src.models.mention import Mention, SentimentLabel, Theme
    from src.services.scraping.registry import get_scraper
    from src.services.scraping.deduplication import DeduplicationService
    import asyncio

    org_id = current_user.organization_id

    # Vérifier que l'org a des mots-clés actifs
    active_keywords = (
        db.query(Keyword)
        .filter(Keyword.organization_id == org_id, Keyword.enabled.is_(True))
        .all()
    )
    if not active_keywords:
        return {
            "success": False,
            "message": "Aucun mot-clé actif. Ajoutez des mots-clés avant de lancer un scan.",
        }

    # 1. Scraper les sources actives
    sources = (
        db.query(Source)
        .filter(Source.scraping_enabled.is_(True))
        .all()
    )

    total_scraped = 0
    total_new_articles = 0
    scrape_errors = []

    for source in sources:
        scraper = get_scraper(source.scraper_class)
        if not scraper:
            scrape_errors.append(f"{source.name}: scraper '{source.scraper_class}' introuvable")
            continue

        try:
            # Timeout de 45s par source pour éviter de bloquer tout le scan
            articles = await asyncio.wait_for(scraper.scrape(), timeout=45)

            total_scraped += len(articles)

            dedup = DeduplicationService(db)
            new_articles = dedup.filter_new_articles(articles, source.id)

            for scraped in new_articles:
                article = Article(
                    title=scraped.title,
                    url=scraped.url,
                    content_hash=scraped.content_hash,
                    raw_content=scraped.raw_content,
                    cleaned_content=scraped.cleaned_content,
                    author=scraped.author,
                    published_at=scraped.published_at,
                    source_id=source.id,
                )
                db.add(article)
                total_new_articles += 1

            source.last_scrape_at = datetime.utcnow()
            source.last_success_at = datetime.utcnow()
            source.consecutive_failures = 0
            source.last_error_message = None
            db.commit()

        except Exception as e:
            db.rollback()
            scrape_errors.append(f"{source.name}: {str(e)[:100]}")
            try:
                source = db.query(Source).filter(Source.id == source.id).first()
                if source:
                    source.consecutive_failures += 1
                    source.last_error_message = str(e)[:500]
                    source.last_scrape_at = datetime.utcnow()
                    db.commit()
            except Exception:
                pass

    # 2. Traiter les articles non traités par NLP
    pending_articles = (
        db.query(Article)
        .filter(Article.nlp_processed.is_(None))
        .order_by(Article.scraped_at.desc())
        .limit(100)
        .all()
    )

    mentions_created = 0
    nlp_errors = 0

    if pending_articles:
        try:
            from src.services.nlp.sentiment import SentimentAnalyzer
            from src.services.nlp.entities import EntityExtractor

            sentiment_analyzer = SentimentAnalyzer()
            entity_extractor = EntityExtractor()
        except Exception:
            sentiment_analyzer = None
            entity_extractor = None

        for article in pending_articles:
            try:
                content = article.cleaned_content
                if not content:
                    article.nlp_processed = datetime.utcnow()
                    continue

                content_lower = content.lower()

                for keyword in active_keywords:
                    kw_lower = keyword.normalized_text.lower()
                    if kw_lower not in content_lower:
                        continue

                    # Vérifier doublon
                    existing = (
                        db.query(Mention)
                        .filter(
                            Mention.keyword_id == keyword.id,
                            Mention.article_id == article.id,
                        )
                        .first()
                    )
                    if existing:
                        continue

                    # Contexte
                    idx = content_lower.find(kw_lower)
                    start = max(0, idx - 200)
                    end = min(len(content), idx + len(kw_lower) + 200)
                    context = content[start:end]
                    if start > 0:
                        context = "..." + context
                    if end < len(content):
                        context = context + "..."

                    # Sentiment
                    if sentiment_analyzer:
                        sentiment = sentiment_analyzer.analyze_context(content, keyword.text)
                        sentiment_label_map = {
                            "positive": SentimentLabel.POSITIVE,
                            "negative": SentimentLabel.NEGATIVE,
                            "neutral": SentimentLabel.NEUTRAL,
                        }
                        label = sentiment_label_map.get(sentiment.label, SentimentLabel.NEUTRAL)
                        score = sentiment.score
                    else:
                        label = SentimentLabel.NEUTRAL
                        score = 0.0

                    # Entités
                    if entity_extractor:
                        entities = entity_extractor.extract_from_context(content, keyword.text)
                        entities_dict = entities.to_dict()
                    else:
                        entities_dict = {}

                    # Thème
                    from src.workers.tasks.nlp import _detect_theme
                    theme = _detect_theme(content, None)

                    mention = Mention(
                        keyword_id=keyword.id,
                        article_id=article.id,
                        matched_text=keyword.text,
                        match_context=context,
                        sentiment_score=score,
                        sentiment_label=label,
                        visibility_score=0.5,
                        theme=theme,
                        extracted_entities=entities_dict,
                        detected_at=datetime.utcnow(),
                    )
                    db.add(mention)
                    mentions_created += 1

                    keyword.total_mentions_count += 1
                    keyword.last_mention_at = datetime.utcnow()

                article.nlp_processed = datetime.utcnow()
                db.commit()

            except Exception as e:
                db.rollback()
                nlp_errors += 1

    return {
        "success": True,
        "message": f"Scan terminé",
        "details": {
            "sources_scannees": len(sources),
            "articles_trouves": total_scraped,
            "nouveaux_articles": total_new_articles,
            "articles_analyses": len(pending_articles),
            "mentions_creees": mentions_created,
            "erreurs_scraping": scrape_errors,
            "erreurs_nlp": nlp_errors,
        },
    }


@router.get("/stats")
async def get_mention_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques rapides des mentions pour le dashboard."""
    service = MentionService(db)
    return service.get_stats(current_user.organization_id)


@router.get("/{mention_id}", response_model=MentionDetailResponse)
async def get_mention(
    mention_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MentionDetailResponse:
    """Récupère les détails complets d'une mention."""
    service = MentionService(db)
    mention = service.get_mention(mention_id, current_user.organization_id)

    if not mention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mention non trouvée",
        )

    base = _mention_to_response(mention)

    return MentionDetailResponse(
        **base.model_dump(),
        extracted_entities=mention.extracted_entities,
        alert_sent=mention.alert_sent,
        article_content=mention.article.cleaned_content if mention.article else None,
    )
