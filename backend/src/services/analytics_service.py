"""Service d'analytics pour les tendances et statistiques"""
import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from src.models.mention import Mention, SentimentLabel
from src.models.article import Article
from src.models.keyword import Keyword
from src.models.source import Source
from src.lib.logger import logger


class AnalyticsService:
    """Service pour les requêtes analytics agrégées avec cache Redis optionnel"""

    def __init__(self, db: Session, redis_client=None):
        self.db = db
        self.redis = redis_client

    # ------------------------------------------------------------------ #
    # T072 - Cache Redis
    # ------------------------------------------------------------------ #

    def _cache_get(self, key: str) -> Optional[dict]:
        """Récupère une valeur du cache Redis."""
        if not self.redis:
            return None
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data.decode() if isinstance(data, bytes) else data)
        except Exception as e:
            logger.warning(f"Erreur cache get {key}: {str(e)}")
        return None

    def _cache_set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """Stocke une valeur dans le cache Redis (TTL 1h par défaut)."""
        if not self.redis:
            return
        try:
            self.redis.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception as e:
            logger.warning(f"Erreur cache set {key}: {str(e)}")

    # ------------------------------------------------------------------ #
    # T068 - Trends (tendances par jour)
    # ------------------------------------------------------------------ #

    def get_trends(
        self,
        organization_id: UUID,
        days: int = 7,
        keyword_id: Optional[UUID] = None,
    ) -> dict:
        """
        Retourne les tendances de mentions par jour sur une période donnée.
        Inclut le total, et la répartition par sentiment par jour.
        """
        cache_key = f"analytics:trends:{organization_id}:{days}:{keyword_id or 'all'}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        date_from = datetime.utcnow() - timedelta(days=days)

        base_query = (
            self.db.query(Mention)
            .join(Keyword, Mention.keyword_id == Keyword.id)
            .filter(
                Keyword.organization_id == organization_id,
                Mention.detected_at >= date_from,
            )
        )

        if keyword_id:
            base_query = base_query.filter(Mention.keyword_id == keyword_id)

        # Mentions par jour
        daily = (
            base_query.with_entities(
                cast(Mention.detected_at, Date).label("date"),
                func.count(Mention.id).label("total"),
            )
            .group_by(cast(Mention.detected_at, Date))
            .order_by(cast(Mention.detected_at, Date))
            .all()
        )

        # Mentions par jour et sentiment
        daily_sentiment = (
            base_query.with_entities(
                cast(Mention.detected_at, Date).label("date"),
                Mention.sentiment_label,
                func.count(Mention.id).label("count"),
            )
            .group_by(cast(Mention.detected_at, Date), Mention.sentiment_label)
            .order_by(cast(Mention.detected_at, Date))
            .all()
        )

        # Construire la série temporelle complète (inclure jours sans données)
        trend_data = []
        sentiment_by_date = {}
        for row in daily_sentiment:
            date_str = row.date.isoformat()
            if date_str not in sentiment_by_date:
                sentiment_by_date[date_str] = {"positive": 0, "negative": 0, "neutral": 0}
            sentiment_by_date[date_str][row.sentiment_label.value] = row.count

        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days - 1 - i)).date()
            date_str = date.isoformat()
            sentiments = sentiment_by_date.get(date_str, {"positive": 0, "negative": 0, "neutral": 0})
            total = sentiments["positive"] + sentiments["negative"] + sentiments["neutral"]
            trend_data.append({
                "date": date_str,
                "total": total,
                **sentiments,
            })

        # Totaux période
        total_mentions = sum(d["total"] for d in trend_data)
        total_positive = sum(d["positive"] for d in trend_data)
        total_negative = sum(d["negative"] for d in trend_data)
        total_neutral = sum(d["neutral"] for d in trend_data)

        result = {
            "period_days": days,
            "total_mentions": total_mentions,
            "total_positive": total_positive,
            "total_negative": total_negative,
            "total_neutral": total_neutral,
            "trend": trend_data,
        }

        self._cache_set(cache_key, result)
        return result

    # ------------------------------------------------------------------ #
    # T069 - Répartition par sources
    # ------------------------------------------------------------------ #

    def get_source_distribution(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> dict:
        """
        Retourne la répartition des mentions par source média.
        """
        cache_key = f"analytics:sources:{organization_id}:{days}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        date_from = datetime.utcnow() - timedelta(days=days)

        rows = (
            self.db.query(
                Source.name,
                Source.type,
                func.count(Mention.id).label("mention_count"),
                func.avg(Mention.sentiment_score).label("avg_sentiment"),
            )
            .join(Article, Article.source_id == Source.id)
            .join(Mention, Mention.article_id == Article.id)
            .join(Keyword, Mention.keyword_id == Keyword.id)
            .filter(
                Keyword.organization_id == organization_id,
                Mention.detected_at >= date_from,
            )
            .group_by(Source.name, Source.type)
            .order_by(func.count(Mention.id).desc())
            .all()
        )

        sources = []
        for row in rows:
            sources.append({
                "name": row.name,
                "type": row.type.value if hasattr(row.type, 'value') else str(row.type),
                "mention_count": row.mention_count,
                "avg_sentiment": round(float(row.avg_sentiment or 0), 3),
            })

        result = {
            "period_days": days,
            "sources": sources,
            "total_sources": len(sources),
        }

        self._cache_set(cache_key, result)
        return result

    # ------------------------------------------------------------------ #
    # Top keywords
    # ------------------------------------------------------------------ #

    def get_top_keywords(
        self,
        organization_id: UUID,
        days: int = 30,
        limit: int = 10,
    ) -> dict:
        """Retourne les mots-clés les plus mentionnés."""
        cache_key = f"analytics:keywords:{organization_id}:{days}:{limit}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        date_from = datetime.utcnow() - timedelta(days=days)

        rows = (
            self.db.query(
                Keyword.text,
                Keyword.category,
                func.count(Mention.id).label("mention_count"),
                func.avg(Mention.sentiment_score).label("avg_sentiment"),
            )
            .join(Mention, Mention.keyword_id == Keyword.id)
            .filter(
                Keyword.organization_id == organization_id,
                Mention.detected_at >= date_from,
            )
            .group_by(Keyword.text, Keyword.category)
            .order_by(func.count(Mention.id).desc())
            .limit(limit)
            .all()
        )

        keywords = []
        for row in rows:
            keywords.append({
                "text": row.text,
                "category": row.category.value if hasattr(row.category, 'value') else str(row.category),
                "mention_count": row.mention_count,
                "avg_sentiment": round(float(row.avg_sentiment or 0), 3),
            })

        result = {
            "period_days": days,
            "keywords": keywords,
        }

        self._cache_set(cache_key, result)
        return result
