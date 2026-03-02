"""Endpoints pour la gestion des mots-clés"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.api.auth import get_current_active_user
from src.schemas.keyword import (
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    KeywordListResponse,
)

router = APIRouter(prefix="/keywords", tags=["Keywords"])


def _kw_to_response(kw: dict) -> KeywordResponse:
    return KeywordResponse(
        id=str(kw["id"]),
        text=kw["text"],
        normalized_text=kw["normalized_text"],
        category=kw["category"],
        enabled=kw["enabled"],
        alert_enabled=kw["alert_enabled"],
        alert_threshold=kw["alert_threshold"],
        organization_id=str(kw["organization_id"]),
        total_mentions_count=kw["total_mentions_count"],
        last_mention_at=kw.get("last_mention_at"),
        created_at=kw["created_at"],
        updated_at=kw["updated_at"],
    )


@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    keyword_data: KeywordCreate,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> KeywordResponse:
    """Créer un nouveau mot-clé."""
    org_id = current_user["organization_id"]

    # Vérifier la limite
    org = current_user.get("_organization") or db.select_one("organizations", id=f"eq.{org_id}")
    current_count = db.count("keywords", organization_id=f"eq.{org_id}")
    if org and current_count >= org.get("keyword_limit", 10):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limite de mots-clés atteinte ({org.get('keyword_limit', 10)})",
        )

    now = datetime.utcnow().isoformat()
    kw = db.insert_one("keywords", {
        "text": keyword_data.text,
        "normalized_text": keyword_data.text.lower().strip(),
        "category": getattr(keyword_data, "category", "BRAND"),
        "enabled": True,
        "alert_enabled": getattr(keyword_data, "alert_enabled", True),
        "alert_threshold": getattr(keyword_data, "alert_threshold", 0.7),
        "organization_id": org_id,
        "total_mentions_count": 0,
        "created_at": now,
        "updated_at": now,
    })

    return _kw_to_response(kw)


@router.get("", response_model=KeywordListResponse)
async def list_keywords(
    enabled_only: bool = Query(False),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> KeywordListResponse:
    """Lister les mots-clés de l'organisation."""
    org_id = current_user["organization_id"]
    filters = {
        "organization_id": f"eq.{org_id}",
        "order": "created_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }
    if enabled_only:
        filters["enabled"] = "eq.true"
    if category:
        filters["category"] = f"eq.{category.upper()}"

    keywords, total = db.select_with_count("keywords", **filters)

    return KeywordListResponse(
        keywords=[_kw_to_response(kw) for kw in keywords],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(
    keyword_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> KeywordResponse:
    """Récupérer un mot-clé par son ID."""
    kw = db.select_one("keywords", id=f"eq.{keyword_id}", organization_id=f"eq.{current_user['organization_id']}")
    if not kw:
        raise HTTPException(status_code=404, detail="Mot-clé non trouvé")
    return _kw_to_response(kw)


@router.patch("/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: UUID,
    keyword_data: KeywordUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> KeywordResponse:
    """Mettre à jour un mot-clé."""
    org_id = current_user["organization_id"]
    existing = db.select_one("keywords", id=f"eq.{keyword_id}", organization_id=f"eq.{org_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="Mot-clé non trouvé")

    update_data = keyword_data.model_dump(exclude_unset=True)
    if "text" in update_data:
        update_data["normalized_text"] = update_data["text"].lower().strip()
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = db.update("keywords", update_data, id=f"eq.{keyword_id}")
    return _kw_to_response(result[0] if result else existing)


@router.delete("/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Supprimer un mot-clé."""
    org_id = current_user["organization_id"]
    existing = db.select_one("keywords", id=f"eq.{keyword_id}", organization_id=f"eq.{org_id}")
    if not existing:
        raise HTTPException(status_code=404, detail="Mot-clé non trouvé")
    db.delete("keywords", id=f"eq.{keyword_id}")
    return None
