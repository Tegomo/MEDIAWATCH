"""Service pour la gestion des mentions"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from src.models.mention import Mention, SentimentLabel
from src.models.article import Article
from src.models.keyword import Keyword
from src.models.source import Source


class MentionService:
    """Service pour les opérations sur les mentions"""

    def __init__(self, db: Session):
        self.db = db

    def list_mentions(
        self,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
        keyword_id: Optional[UUID] = None,
        sentiment: Optional[str] = None,
        source_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        theme: Optional[str] = None,
    ) -> tuple[list[Mention], int]:
        """
        Liste les mentions pour une organisation avec filtres et pagination.
        Retourne (mentions, total_count).
        """
        query = (
            self.db.query(Mention)
            .join(Keyword, Mention.keyword_id == Keyword.id)
            .join(Article, Mention.article_id == Article.id)
            .join(Source, Article.source_id == Source.id)
            .options(
                joinedload(Mention.keyword),
                joinedload(Mention.article).joinedload(Article.source),
            )
            .filter(Keyword.organization_id == organization_id)
        )

        # Filtres
        if keyword_id:
            query = query.filter(Mention.keyword_id == keyword_id)

        if sentiment:
            try:
                sentiment_enum = SentimentLabel(sentiment)
                query = query.filter(Mention.sentiment_label == sentiment_enum)
            except ValueError:
                pass

        if source_id:
            query = query.filter(Article.source_id == source_id)

        if date_from:
            query = query.filter(Mention.detected_at >= date_from)

        if date_to:
            query = query.filter(Mention.detected_at <= date_to)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Mention.matched_text.ilike(search_pattern))
                | (Mention.match_context.ilike(search_pattern))
                | (Article.title.ilike(search_pattern))
            )

        if theme:
            from src.models.mention import Theme
            try:
                theme_enum = Theme(theme)
                query = query.filter(Mention.theme == theme_enum)
            except ValueError:
                pass

        # Total count
        total = query.count()

        # Tri et pagination
        mentions = (
            query.order_by(desc(Mention.detected_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return mentions, total

    def get_mention(self, mention_id: UUID, organization_id: UUID) -> Optional[Mention]:
        """Récupère une mention par ID avec vérification d'accès organisation."""
        mention = (
            self.db.query(Mention)
            .join(Keyword, Mention.keyword_id == Keyword.id)
            .options(
                joinedload(Mention.keyword),
                joinedload(Mention.article).joinedload(Article.source),
            )
            .filter(
                Mention.id == mention_id,
                Keyword.organization_id == organization_id,
            )
            .first()
        )
        return mention

    def get_stats(self, organization_id: UUID) -> dict:
        """Statistiques rapides des mentions pour le dashboard."""
        base_query = (
            self.db.query(Mention)
            .join(Keyword, Mention.keyword_id == Keyword.id)
            .filter(Keyword.organization_id == organization_id)
        )

        total = base_query.count()

        sentiment_counts = (
            base_query.with_entities(
                Mention.sentiment_label,
                func.count(Mention.id),
            )
            .group_by(Mention.sentiment_label)
            .all()
        )

        return {
            "total_mentions": total,
            "by_sentiment": {
                label.value: count for label, count in sentiment_counts
            },
        }
