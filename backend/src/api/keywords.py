"""Endpoints pour la gestion des mots-clés"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.models.keyword import KeywordCategory
from src.schemas.keyword import (
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    KeywordListResponse,
)
from src.services.keyword_service import KeywordService

router = APIRouter(prefix="/keywords", tags=["Keywords"])


@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    keyword_data: KeywordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> KeywordResponse:
    """
    Créer un nouveau mot-clé.
    
    Vérifie automatiquement la limite du plan d'abonnement.
    """
    keyword = KeywordService.create_keyword(db, keyword_data, current_user)
    
    return KeywordResponse(
        id=str(keyword.id),
        text=keyword.text,
        normalized_text=keyword.normalized_text,
        category=keyword.category.value,
        enabled=keyword.enabled,
        alert_enabled=keyword.alert_enabled,
        alert_threshold=keyword.alert_threshold,
        organization_id=str(keyword.organization_id),
        total_mentions_count=keyword.total_mentions_count,
        last_mention_at=keyword.last_mention_at,
        created_at=keyword.created_at,
        updated_at=keyword.updated_at,
    )


@router.get("", response_model=KeywordListResponse)
async def list_keywords(
    enabled_only: bool = Query(False, description="Ne retourner que les mots-clés activés"),
    category: Optional[KeywordCategory] = Query(None, description="Filtrer par catégorie"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> KeywordListResponse:
    """
    Lister les mots-clés de l'organisation.
    
    Supporte la pagination et le filtrage.
    """
    keywords, total = KeywordService.get_keywords(
        db=db,
        organization_id=current_user.organization_id,
        enabled_only=enabled_only,
        category=category,
        limit=limit,
        offset=offset,
    )
    
    keyword_responses = [
        KeywordResponse(
            id=str(kw.id),
            text=kw.text,
            normalized_text=kw.normalized_text,
            category=kw.category.value,
            enabled=kw.enabled,
            alert_enabled=kw.alert_enabled,
            alert_threshold=kw.alert_threshold,
            organization_id=str(kw.organization_id),
            total_mentions_count=kw.total_mentions_count,
            last_mention_at=kw.last_mention_at,
            created_at=kw.created_at,
            updated_at=kw.updated_at,
        )
        for kw in keywords
    ]
    
    return KeywordListResponse(
        keywords=keyword_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> KeywordResponse:
    """
    Récupérer un mot-clé par son ID.
    """
    keyword = KeywordService.get_keyword(db, keyword_id, current_user.organization_id)
    
    return KeywordResponse(
        id=str(keyword.id),
        text=keyword.text,
        normalized_text=keyword.normalized_text,
        category=keyword.category.value,
        enabled=keyword.enabled,
        alert_enabled=keyword.alert_enabled,
        alert_threshold=keyword.alert_threshold,
        organization_id=str(keyword.organization_id),
        total_mentions_count=keyword.total_mentions_count,
        last_mention_at=keyword.last_mention_at,
        created_at=keyword.created_at,
        updated_at=keyword.updated_at,
    )


@router.patch("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: UUID,
    keyword_data: KeywordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> KeywordResponse:
    """
    Mettre à jour un mot-clé.
    """
    keyword = KeywordService.update_keyword(db, keyword_id, keyword_data, current_user)
    
    return KeywordResponse(
        id=str(keyword.id),
        text=keyword.text,
        normalized_text=keyword.normalized_text,
        category=keyword.category.value,
        enabled=keyword.enabled,
        alert_enabled=keyword.alert_enabled,
        alert_threshold=keyword.alert_threshold,
        organization_id=str(keyword.organization_id),
        total_mentions_count=keyword.total_mentions_count,
        last_mention_at=keyword.last_mention_at,
        created_at=keyword.created_at,
        updated_at=keyword.updated_at,
    )


@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Supprimer un mot-clé.
    """
    KeywordService.delete_keyword(db, keyword_id, current_user)
    return None
