"""Celery tasks pour le traitement NLP des articles"""
from datetime import datetime

from src.workers.celery_app import celery_app
from src.lib.logger import logger


@celery_app.task(name="src.workers.tasks.nlp.process_pending_articles")
def process_pending_articles():
    """
    Tâche périodique: traite les articles en attente de NLP.
    Exécutée toutes les 5 minutes par Celery Beat.
    Pour chaque article non traité:
    1. Analyse de sentiment (CamemBERT)
    2. Extraction d'entités (spaCy)
    3. Marque l'article comme traité
    """
    from src.db.base import SessionLocal
    from src.models.article import Article

    db = SessionLocal()
    try:
        # Articles non encore traités par NLP
        pending = (
            db.query(Article)
            .filter(Article.nlp_processed.is_(None))
            .order_by(Article.scraped_at.desc())
            .limit(50)
            .all()
        )

        if not pending:
            return

        logger.info(f"NLP: {len(pending)} articles en attente de traitement")

        for article in pending:
            process_article_nlp.delay(str(article.id))

    except Exception as e:
        logger.error(f"Erreur process_pending_articles: {str(e)}")
    finally:
        db.close()


@celery_app.task(name="src.workers.tasks.nlp.process_article_nlp")
def process_article_nlp(article_id: str):
    """
    Traite un article individuel avec le pipeline NLP:
    1. Analyse de sentiment sur le contenu nettoyé
    2. Extraction d'entités nommées
    3. Matching avec les mots-clés actifs
    4. Création des mentions détectées
    """
    from src.db.base import SessionLocal
    from src.models.article import Article
    from src.models.keyword import Keyword
    from src.models.mention import Mention, SentimentLabel, Theme
    from src.services.nlp.sentiment import SentimentAnalyzer
    from src.services.nlp.entities import EntityExtractor

    db = SessionLocal()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.error(f"Article {article_id} non trouvé")
            return

        if article.nlp_processed:
            return

        logger.info(f"NLP traitement article: {article.title[:60]}...")

        sentiment_analyzer = SentimentAnalyzer()
        entity_extractor = EntityExtractor()

        # Récupérer tous les keywords actifs
        active_keywords = (
            db.query(Keyword)
            .filter(Keyword.enabled.is_(True))
            .all()
        )

        content = article.cleaned_content
        content_lower = content.lower()
        mentions_created = 0

        for keyword in active_keywords:
            # Matching mot-clé dans le contenu
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

            # Extraire le contexte
            idx = content_lower.find(kw_lower)
            start = max(0, idx - 200)
            end = min(len(content), idx + len(kw_lower) + 200)
            context = content[start:end]
            if start > 0:
                context = "..." + context
            if end < len(content):
                context = context + "..."

            # Analyse de sentiment sur le contexte
            sentiment = sentiment_analyzer.analyze_context(content, keyword.text)

            # Extraction d'entités sur le contexte
            entities = entity_extractor.extract_from_context(content, keyword.text)

            # Mapper le label de sentiment
            sentiment_label_map = {
                "positive": SentimentLabel.POSITIVE,
                "negative": SentimentLabel.NEGATIVE,
                "neutral": SentimentLabel.NEUTRAL,
            }
            label = sentiment_label_map.get(sentiment.label, SentimentLabel.NEUTRAL)

            # Détecter le thème basé sur les entités et le contenu
            theme = _detect_theme(content, entities)

            # Créer la mention
            mention = Mention(
                keyword_id=keyword.id,
                article_id=article.id,
                matched_text=keyword.text,
                match_context=context,
                sentiment_score=sentiment.score,
                sentiment_label=label,
                visibility_score=_calculate_visibility(article),
                theme=theme,
                extracted_entities=entities.to_dict(),
                detected_at=datetime.utcnow(),
            )
            db.add(mention)
            mentions_created += 1

            # Mettre à jour le compteur du keyword
            keyword.total_mentions_count += 1
            keyword.last_mention_at = datetime.utcnow()

        # Marquer l'article comme traité
        article.nlp_processed = datetime.utcnow()
        db.commit()

        if mentions_created:
            logger.info(
                f"NLP article {article_id}: {mentions_created} mentions créées"
            )

            # Déclencher les alertes pour les mentions négatives
            from src.workers.tasks.mention_detection import _trigger_alerts_for_mention
            for mention in (
                db.query(Mention)
                .filter(
                    Mention.article_id == article.id,
                    Mention.sentiment_label == SentimentLabel.NEGATIVE,
                )
                .all()
            ):
                keyword = db.query(Keyword).filter(Keyword.id == mention.keyword_id).first()
                if keyword and keyword.alert_enabled:
                    _trigger_alerts_for_mention(
                        db, str(mention.id), str(keyword.organization_id)
                    )

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur NLP article {article_id}: {str(e)}")
    finally:
        db.close()


def _detect_theme(content: str, entities) -> Theme | None:
    """Détecte le thème d'un article basé sur des heuristiques simples."""
    from src.models.mention import Theme

    content_lower = content.lower()

    theme_keywords = {
        Theme.POLITICS: [
            "président", "gouvernement", "ministre", "élection", "parlement",
            "politique", "opposition", "parti", "assemblée", "sénat",
            "rhdp", "pdci", "fpi", "ouattara", "bédié",
        ],
        Theme.ECONOMY: [
            "économie", "croissance", "pib", "investissement", "banque",
            "bourse", "inflation", "emploi", "entreprise", "commerce",
            "fcfa", "bceao", "exportation", "cacao", "pétrole",
        ],
        Theme.SPORT: [
            "football", "can", "fif", "éléphants", "match",
            "championnat", "ligue", "joueur", "stade", "sport",
        ],
        Theme.TECHNOLOGY: [
            "technologie", "numérique", "digital", "startup", "innovation",
            "internet", "mobile", "application", "data", "intelligence artificielle",
        ],
        Theme.CULTURE: [
            "culture", "musique", "cinéma", "festival", "artiste",
            "exposition", "livre", "théâtre", "danse", "patrimoine",
        ],
        Theme.SOCIETY: [
            "société", "éducation", "santé", "sécurité", "justice",
            "environnement", "population", "jeunesse", "femmes", "droits",
        ],
    }

    scores = {}
    for theme, keywords in theme_keywords.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scores[theme] = score

    if scores:
        return max(scores, key=scores.get)

    return Theme.OTHER


def _calculate_visibility(article) -> float:
    """
    T067 - Calcule le score de visibilité d'un article.
    Basé sur le prestige de la source et la fraîcheur.
    """
    score = 0.5  # Score par défaut

    # Bonus prestige source
    if article.source:
        score = article.source.prestige_score

    # Bonus fraîcheur (articles récents = plus visibles)
    if article.published_at:
        from datetime import timedelta
        age = datetime.utcnow() - article.published_at
        if age < timedelta(hours=6):
            score = min(1.0, score + 0.2)
        elif age < timedelta(hours=24):
            score = min(1.0, score + 0.1)
        elif age > timedelta(days=7):
            score = max(0.1, score - 0.2)

    return round(score, 2)
