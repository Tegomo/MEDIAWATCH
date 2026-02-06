"""Endpoints API admin pour le monitoring des sources et la gestion des organisations"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.services.admin.source_health_service import SourceHealthService
from src.services.admin.organization_service import OrganizationAdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateSourceRequest(BaseModel):
    name: str
    url: str
    source_type: str = "press"
    scraper_class: str = "generic"
    prestige_score: float = 0.5
    scraping_enabled: bool = True


class UpdateSourceRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    scraper_class: Optional[str] = None
    prestige_score: Optional[float] = None
    scraping_enabled: Optional[bool] = None


class UpdateLimitsRequest(BaseModel):
    keyword_limit: Optional[int] = None
    user_limit: Optional[int] = None


class CreateOrganizationRequest(BaseModel):
    name: str
    subscription_plan: str = "basic"
    subscription_status: str = "trial"
    keyword_limit: int = 10
    user_limit: int = 1


class UpdateOrganizationRequest(BaseModel):
    name: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    keyword_limit: Optional[int] = None
    user_limit: Optional[int] = None


def _require_admin(user: User):
    """Vérifie que l'utilisateur est admin."""
    if not getattr(user, 'is_admin', False) and getattr(user, 'role', None) != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )


@router.get("/sources")
async def list_sources(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste toutes les sources avec leur statut de santé."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    sources = service.list_sources()
    summary = service.get_health_summary()
    return {"sources": sources, "summary": summary}


@router.get("/sources/{source_id}")
async def get_source(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Détails d'une source spécifique."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    source = service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return source


@router.post("/sources/{source_id}/retry")
async def retry_source(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Réactive une source et relance le scraping."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    result = service.retry_source(source_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/sources/{source_id}/toggle")
async def toggle_source(
    source_id: UUID,
    enabled: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Active ou désactive une source."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    result = service.toggle_source(source_id, enabled)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(
    body: CreateSourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle source média."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    result = service.create_source(
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        scraper_class=body.scraper_class,
        prestige_score=body.prestige_score,
        scraping_enabled=body.scraping_enabled,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/sources/{source_id}")
async def update_source(
    source_id: UUID,
    body: UpdateSourceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une source média."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    result = service.update_source(
        source_id=source_id,
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        scraper_class=body.scraper_class,
        prestige_score=body.prestige_score,
        scraping_enabled=body.scraping_enabled,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Supprime une source et tous ses articles."""
    _require_admin(current_user)
    service = SourceHealthService(db)
    result = service.delete_source(source_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ------------------------------------------------------------------ #
# Organizations Admin
# ------------------------------------------------------------------ #


@router.get("/organizations")
async def list_organizations(
    plan: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Liste toutes les organisations avec statistiques."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    return {"organizations": service.list_organizations(plan=plan, status=status_filter)}


@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Détails complets d'une organisation."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    org = service.get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    return org


@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Suspend une organisation."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    result = service.suspend_organization(org_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/organizations/{org_id}/reactivate")
async def reactivate_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Réactive une organisation suspendue."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    result = service.reactivate_organization(org_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.patch("/organizations/{org_id}/limits")
async def update_organization_limits(
    org_id: UUID,
    body: UpdateLimitsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour les limites d'une organisation."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    result = service.update_limits(org_id, keyword_limit=body.keyword_limit, user_limit=body.user_limit)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: CreateOrganizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Crée une nouvelle organisation."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    result = service.create_organization(
        name=body.name,
        subscription_plan=body.subscription_plan,
        subscription_status=body.subscription_status,
        keyword_limit=body.keyword_limit,
        user_limit=body.user_limit,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: UUID,
    body: UpdateOrganizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Met à jour une organisation (nom, plan, statut, limites)."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    result = service.update_organization(
        org_id=org_id,
        name=body.name,
        subscription_plan=body.subscription_plan,
        subscription_status=body.subscription_status,
        keyword_limit=body.keyword_limit,
        user_limit=body.user_limit,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Supprime une organisation et toutes ses données."""
    _require_admin(current_user)
    service = OrganizationAdminService(db)
    result = service.delete_organization(org_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
