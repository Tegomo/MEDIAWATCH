"""Endpoints API pour les analytics et tendances"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_redis():
    """Tente de se connecter à Redis, retourne None si indisponible."""
    try:
        import redis
        client = redis.from_url("redis://localhost:6379/0")
        client.ping()
        return client
    except Exception:
        return None


@router.get("/trends")
async def get_trends(
    days: int = Query(7, ge=1, le=90),
    keyword_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Tendances des mentions sur une période donnée.
    Retourne le nombre de mentions par jour avec répartition par sentiment.
    """
    service = AnalyticsService(db, redis_client=_get_redis())
    return service.get_trends(
        organization_id=current_user.organization_id,
        days=days,
        keyword_id=keyword_id,
    )


@router.get("/sources")
async def get_source_distribution(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Répartition des mentions par source média.
    Retourne le nombre de mentions et le sentiment moyen par source.
    """
    service = AnalyticsService(db, redis_client=_get_redis())
    return service.get_source_distribution(
        organization_id=current_user.organization_id,
        days=days,
    )


@router.get("/keywords")
async def get_top_keywords(
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Top mots-clés les plus mentionnés.
    """
    service = AnalyticsService(db, redis_client=_get_redis())
    return service.get_top_keywords(
        organization_id=current_user.organization_id,
        days=days,
        limit=limit,
    )
