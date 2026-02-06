"""Service d'alertes email via SendGrid (Twilio)"""
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from src.config import settings
from src.lib.logger import logger
from src.models.mention import Mention, SentimentLabel
from src.models.article import Article
from src.models.keyword import Keyword
from src.models.user import User

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)

SENTIMENT_FR = {
    "negative": "Négatif",
    "positive": "Positif",
    "neutral": "Neutre",
}


class AlertService:
    """Service pour l'envoi d'alertes email via SendGrid"""

    def __init__(self, db: Session, redis_client=None):
        self.db = db
        self.redis = redis_client

    # ------------------------------------------------------------------ #
    # Email sending via SendGrid
    # ------------------------------------------------------------------ #

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Envoie un email via l'API SendGrid."""
        if not settings.sendgrid_api_key:
            logger.warning("SendGrid API key non configurée, email non envoyé")
            return False

        try:
            import httpx

            response = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {
                        "email": settings.sendgrid_from_email,
                        "name": settings.sendgrid_from_name,
                    },
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_content}],
                },
                timeout=30,
            )

            if response.status_code in (200, 201, 202):
                logger.info(f"Email envoyé à {to_email}: {subject}")
                return True
            else:
                logger.error(
                    f"Erreur SendGrid {response.status_code}: {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Erreur envoi email à {to_email}: {str(e)}")
            return False

    # ------------------------------------------------------------------ #
    # T047 - Retry logic avec backoff exponentiel
    # ------------------------------------------------------------------ #

    def send_email_with_retry(
        self, to_email: str, subject: str, html_content: str
    ) -> bool:
        """Envoie un email avec retry et backoff exponentiel."""
        max_retries = settings.alert_max_retries
        base_delay = settings.alert_retry_base_delay

        for attempt in range(max_retries):
            success = self._send_email(to_email, subject, html_content)
            if success:
                return True

            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} pour {to_email}, "
                    f"attente {delay}s"
                )
                time.sleep(delay)

        logger.error(
            f"Échec envoi email à {to_email} après {max_retries} tentatives"
        )
        return False

    # ------------------------------------------------------------------ #
    # Single alert
    # ------------------------------------------------------------------ #

    def send_single_alert(
        self,
        mention: Mention,
        user: User,
        dashboard_url: str = "http://localhost:5174/dashboard",
    ) -> bool:
        """Envoie une alerte email pour une seule mention."""
        template = jinja_env.get_template("alert_single.html")

        article = mention.article
        keyword = mention.keyword

        html = template.render(
            keyword_text=keyword.text if keyword else "N/A",
            source_name=article.source.name if article and article.source else "Source inconnue",
            article_title=article.title if article else "Article inconnu",
            published_at=article.published_at.strftime("%d/%m/%Y %H:%M") if article else "",
            author=article.author if article else None,
            sentiment_label=mention.sentiment_label.value,
            sentiment_label_fr=SENTIMENT_FR.get(mention.sentiment_label.value, "Inconnu"),
            sentiment_score=f"{abs(mention.sentiment_score) * 100:.0f}",
            match_context=mention.match_context,
            article_url=article.url if article else "#",
            dashboard_url=dashboard_url,
            unsubscribe_url=f"{dashboard_url.rstrip('/')}/settings/alerts",
        )

        subject = f"[MediaWatch] Mention négative : {keyword.text if keyword else 'N/A'}"
        return self.send_email_with_retry(user.email, subject, html)

    # ------------------------------------------------------------------ #
    # T048 - Batching alertes fenêtre 1h Redis
    # ------------------------------------------------------------------ #

    def queue_alert_for_batching(self, mention_id: UUID, user_id: UUID) -> None:
        """Ajoute une mention à la file de batching Redis pour un utilisateur."""
        if not self.redis:
            logger.warning("Redis non disponible, envoi immédiat impossible via batch")
            return

        key = f"alert_batch:{user_id}"
        self.redis.rpush(key, str(mention_id))
        # TTL de 2h pour nettoyage automatique
        self.redis.expire(key, 7200)
        logger.info(f"Mention {mention_id} ajoutée au batch pour user {user_id}")

    def get_pending_batch(self, user_id: UUID) -> list[str]:
        """Récupère et vide la file de mentions en attente pour un utilisateur."""
        if not self.redis:
            return []

        key = f"alert_batch:{user_id}"
        mention_ids = self.redis.lrange(key, 0, -1)
        if mention_ids:
            self.redis.delete(key)
        return [mid.decode() if isinstance(mid, bytes) else mid for mid in mention_ids]

    def should_send_batch(self, user_id: UUID) -> bool:
        """Vérifie si la fenêtre de batching est écoulée pour cet utilisateur."""
        if not self.redis:
            return True

        key = f"alert_batch_last_sent:{user_id}"
        last_sent = self.redis.get(key)

        if not last_sent:
            return True

        last_sent_time = datetime.fromisoformat(
            last_sent.decode() if isinstance(last_sent, bytes) else last_sent
        )
        window = timedelta(minutes=settings.alert_batch_window_minutes)
        return datetime.utcnow() - last_sent_time >= window

    def mark_batch_sent(self, user_id: UUID) -> None:
        """Marque le dernier envoi de batch pour cet utilisateur."""
        if not self.redis:
            return

        key = f"alert_batch_last_sent:{user_id}"
        self.redis.set(key, datetime.utcnow().isoformat(), ex=7200)

    def send_batch_alert(
        self,
        user: User,
        mention_ids: list[str],
        dashboard_url: str = "http://localhost:5174/dashboard",
    ) -> bool:
        """Envoie un email batch regroupant plusieurs mentions."""
        if not mention_ids:
            return True

        mentions = (
            self.db.query(Mention)
            .filter(Mention.id.in_(mention_ids))
            .all()
        )

        if not mentions:
            return True

        template = jinja_env.get_template("alert_batch.html")

        mention_data = []
        negative_count = 0
        keyword_set = set()

        for m in mentions:
            article = m.article
            keyword = m.keyword
            if keyword:
                keyword_set.add(keyword.text)
            if m.sentiment_label == SentimentLabel.NEGATIVE:
                negative_count += 1

            mention_data.append({
                "article_title": article.title if article else "Article inconnu",
                "source_name": article.source.name if article and article.source else "Source inconnue",
                "published_at": article.published_at.strftime("%d/%m/%Y %H:%M") if article else "",
                "sentiment_label": m.sentiment_label.value,
                "sentiment_label_fr": SENTIMENT_FR.get(m.sentiment_label.value, "Inconnu"),
                "keyword_text": keyword.text if keyword else "N/A",
                "match_context": m.match_context,
            })

        html = template.render(
            mention_count=len(mentions),
            negative_count=negative_count,
            keyword_count=len(keyword_set),
            mentions=mention_data,
            dashboard_url=dashboard_url,
            unsubscribe_url=f"{dashboard_url.rstrip('/')}/settings/alerts",
        )

        subject = f"[MediaWatch] {len(mentions)} mention(s) détectée(s)"
        success = self.send_email_with_retry(user.email, subject, html)

        if success:
            self.mark_batch_sent(user.id)
            # Marquer les mentions comme alertées
            for m in mentions:
                m.alert_sent = datetime.utcnow()
            self.db.commit()

        return success
