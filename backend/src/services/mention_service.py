"""Service pour la gestion des mentions - Client Supabase REST"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from src.db.supabase_client import SupabaseDB


class MentionService:
    """Service pour les opérations sur les mentions via Supabase REST"""

    def __init__(self, db: SupabaseDB):
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
    ) -> tuple[list[dict], int]:
        """
        Liste les mentions pour une organisation avec filtres et pagination.
        Retourne (mentions, total_count).
        """
        # Récupérer les keyword_ids de l'organisation
        keywords = self.db.select("keywords", columns="id", organization_id=f"eq.{organization_id}")
        keyword_ids = [k["id"] for k in keywords]

        if not keyword_ids:
            return [], 0

        # Construire les filtres
        filters = {
            "keyword_id": f"in.({','.join(str(k) for k in keyword_ids)})",
            "order": "detected_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }

        if keyword_id:
            filters["keyword_id"] = f"eq.{keyword_id}"

        if sentiment:
            filters["sentiment_label"] = f"eq.{sentiment.upper()}"

        if date_from:
            filters["detected_at"] = f"gte.{date_from.isoformat()}"

        if date_to:
            dt_filter = filters.get("detected_at", "")
            if dt_filter:
                # PostgREST ne supporte pas 2 filtres sur la même colonne facilement
                # On utilise le filtre le plus restrictif
                pass
            else:
                filters["detected_at"] = f"lte.{date_to.isoformat()}"

        if search:
            filters["or"] = f"(matched_text.ilike.%{search}%,match_context.ilike.%{search}%)"

        if theme:
            filters["theme"] = f"eq.{theme.upper()}"

        # Sélectionner avec relations imbriquées + count en 1 seule requête
        columns = "*,keyword:keywords(*),article:articles(*,source:sources(*))"

        mentions, total = self.db.select_with_count("mentions", columns=columns, **filters)

        # Filtrer par source_id si nécessaire (post-filtre car relation imbriquée)
        if source_id:
            mentions = [m for m in mentions if m.get("article", {}).get("source_id") == str(source_id)]

        return mentions, total

    def get_mention(self, mention_id: UUID, organization_id: UUID) -> Optional[dict]:
        """Récupère une mention par ID avec vérification d'accès organisation."""
        columns = "*,keyword:keywords(*),article:articles(*,source:sources(*))"
        mention = self.db.select_one("mentions", columns=columns, id=f"eq.{mention_id}")

        if not mention:
            return None

        # Vérifier que le keyword appartient à l'organisation
        keyword = mention.get("keyword", {})
        if keyword and str(keyword.get("organization_id")) != str(organization_id):
            return None

        return mention

    def get_stats(self, organization_id: UUID) -> dict:
        """Statistiques rapides des mentions pour le dashboard."""
        # Récupérer les keyword_ids de l'organisation
        keywords = self.db.select("keywords", columns="id", organization_id=f"eq.{organization_id}")
        keyword_ids = [k["id"] for k in keywords]

        if not keyword_ids:
            return {"total_mentions": 0, "by_sentiment": {}}

        kw_filter = f"in.({','.join(str(k) for k in keyword_ids)})"

        # 1 seule requête : récupérer les sentiment_label de toutes les mentions
        rows = self.db.select("mentions", columns="sentiment_label", keyword_id=kw_filter)

        by_sentiment = {}
        for row in rows:
            label = (row.get("sentiment_label") or "NEUTRAL").lower()
            by_sentiment[label] = by_sentiment.get(label, 0) + 1

        return {
            "total_mentions": len(rows),
            "by_sentiment": by_sentiment,
        }
