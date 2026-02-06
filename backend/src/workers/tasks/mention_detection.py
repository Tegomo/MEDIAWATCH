"""Celery tasks pour la détection de mentions et déclenchement d'alertes"""
from src.workers.celery_app import celery_app
from src.lib.logger import logger


@celery_app.task(name="src.workers.tasks.mention_detection.detect_all_mentions")
def detect_all_mentions():
    """
    Tâche périodique: détecte les mentions de mots-clés dans les articles
    récemment traités par le NLP et déclenche les alertes pour les mentions négatives.
    Exécutée toutes les 10 minutes par Celery Beat.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import and_
    from src.db.base import SessionLocal
    from src.models.article import Article
    from src.models.keyword import Keyword
    from src.models.mention import Mention, SentimentLabel
    from src.models.user import User

    db = SessionLocal()
    try:
        # Articles traités par NLP dans les 15 dernières minutes
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        recent_articles = (
            db.query(Article)
            .filter(
                Article.nlp_processed.isnot(None),
                Article.nlp_processed >= cutoff,
            )
            .all()
        )

        if not recent_articles:
            return

        logger.info(f"Détection mentions: {len(recent_articles)} articles récents")

        # Récupérer tous les keywords actifs
        active_keywords = (
            db.query(Keyword)
            .filter(Keyword.enabled.is_(True))
            .all()
        )

        new_mentions_count = 0
        alert_triggers = []

        for article in recent_articles:
            content_lower = article.cleaned_content.lower()

            for keyword in active_keywords:
                # Vérifier si le mot-clé est dans le contenu
                if keyword.normalized_text.lower() not in content_lower:
                    continue

                # Vérifier si la mention existe déjà
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

                # Extraire le contexte autour du mot-clé
                idx = content_lower.find(keyword.normalized_text.lower())
                start = max(0, idx - 150)
                end = min(len(article.cleaned_content), idx + len(keyword.normalized_text) + 150)
                context = article.cleaned_content[start:end]
                if start > 0:
                    context = "..." + context
                if end < len(article.cleaned_content):
                    context = context + "..."

                # Créer la mention (sentiment sera affiné par NLP)
                mention = Mention(
                    keyword_id=keyword.id,
                    article_id=article.id,
                    matched_text=keyword.text,
                    match_context=context,
                    sentiment_score=0.0,
                    sentiment_label=SentimentLabel.NEUTRAL,
                    visibility_score=0.5,
                    detected_at=datetime.utcnow(),
                )
                db.add(mention)
                db.flush()

                new_mentions_count += 1

                # Mettre à jour le compteur du keyword
                keyword.total_mentions_count += 1
                keyword.last_mention_at = datetime.utcnow()

                # Déclencher alerte si mention négative et alertes activées
                if (
                    mention.sentiment_label == SentimentLabel.NEGATIVE
                    and keyword.alert_enabled
                ):
                    alert_triggers.append({
                        "mention_id": str(mention.id),
                        "organization_id": str(keyword.organization_id),
                    })

        db.commit()

        if new_mentions_count:
            logger.info(f"Détection: {new_mentions_count} nouvelles mentions créées")

        # Déclencher les alertes pour les mentions négatives
        for trigger in alert_triggers:
            _trigger_alerts_for_mention(
                db, trigger["mention_id"], trigger["organization_id"]
            )

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur detect_all_mentions: {str(e)}")
        raise
    finally:
        db.close()


def _trigger_alerts_for_mention(db, mention_id: str, organization_id: str):
    """Déclenche les alertes pour une mention négative auprès des utilisateurs de l'organisation."""
    from src.models.user import User
    from src.workers.tasks.alerts import queue_alert_batch

    try:
        users = (
            db.query(User)
            .filter(User.organization_id == organization_id)
            .all()
        )

        for user in users:
            queue_alert_batch.delay(mention_id, str(user.id))
            logger.info(
                f"Alerte programmée: mention {mention_id} -> user {user.email}"
            )

    except Exception as e:
        logger.error(f"Erreur trigger alertes mention {mention_id}: {str(e)}")
