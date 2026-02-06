"""Service de déduplication des articles scrapés"""
from uuid import UUID

from sqlalchemy.orm import Session

from src.models.article import Article
from src.services.scraping.base import ScrapedArticle
from src.lib.logger import logger


class DeduplicationService:
    """Vérifie et filtre les articles déjà existants en base."""

    def __init__(self, db: Session):
        self.db = db

    def is_duplicate(self, article: ScrapedArticle, source_id: UUID) -> bool:
        """Vérifie si un article existe déjà (par content_hash ou URL)."""
        existing = (
            self.db.query(Article.id)
            .filter(
                (Article.content_hash == article.content_hash)
                | (Article.url == article.url)
            )
            .first()
        )
        return existing is not None

    def filter_new_articles(
        self, articles: list[ScrapedArticle], source_id: UUID
    ) -> list[ScrapedArticle]:
        """Filtre et retourne uniquement les articles non-dupliqués."""
        if not articles:
            return []

        # Récupérer tous les hashes et URLs existants en un seul query
        urls = [a.url for a in articles]
        hashes = [a.content_hash for a in articles]

        existing = (
            self.db.query(Article.url, Article.content_hash)
            .filter(
                (Article.url.in_(urls)) | (Article.content_hash.in_(hashes))
            )
            .all()
        )

        existing_urls = {row.url for row in existing}
        existing_hashes = {row.content_hash for row in existing}

        new_articles = [
            a
            for a in articles
            if a.url not in existing_urls and a.content_hash not in existing_hashes
        ]

        duplicates_count = len(articles) - len(new_articles)
        if duplicates_count:
            logger.info(
                f"Déduplication: {duplicates_count} doublons filtrés, "
                f"{len(new_articles)} nouveaux articles"
            )

        return new_articles
