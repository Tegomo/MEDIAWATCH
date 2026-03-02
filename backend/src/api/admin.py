"""Endpoints API admin pour le monitoring des sources et la gestion des organisations"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.api.auth import get_current_active_user

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateSourceRequest(BaseModel):
    name: str
    url: str
    source_type: str = "PRESS"
    scraper_class: str = "generic"
    prestige_score: float = 50.0
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
    subscription_plan: str = "BASIC"
    subscription_status: str = "TRIAL"
    keyword_limit: int = 10
    user_limit: int = 1


class UpdateOrganizationRequest(BaseModel):
    name: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    keyword_limit: Optional[int] = None
    user_limit: Optional[int] = None


def _require_admin(user: dict):
    """Vérifie que l'utilisateur est admin."""
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )


@router.get("/sources")
async def list_sources(
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Liste toutes les sources avec leur statut de santé."""
    _require_admin(current_user)
    sources = db.select("sources", order="name.asc")

    # Récupérer les articles récents (24h) groupés par source
    from datetime import timedelta
    day_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    recent_articles = db.select("articles", columns="source_id", scraped_at=f"gte.{day_ago}")
    recent_counts: dict[str, int] = {}
    for a in recent_articles:
        sid = a.get("source_id")
        if sid:
            recent_counts[sid] = recent_counts.get(sid, 0) + 1

    # Total articles par source
    all_articles = db.select("articles", columns="source_id")
    total_counts: dict[str, int] = {}
    for a in all_articles:
        sid = a.get("source_id")
        if sid:
            total_counts[sid] = total_counts.get(sid, 0) + 1

    # Calculer le statut et enrichir chaque source
    counts = {"ok": 0, "warning": 0, "error": 0, "disabled": 0}
    for s in sources:
        sid = s["id"]
        failures = s.get("consecutive_failures", 0)
        enabled = s.get("scraping_enabled", True)

        if not enabled:
            s["status"] = "disabled"
        elif failures >= 5:
            s["status"] = "error"
        elif failures > 0:
            s["status"] = "warning"
        else:
            s["status"] = "ok"

        counts[s["status"]] += 1
        s["articles_24h"] = recent_counts.get(sid, 0)
        s["total_articles"] = total_counts.get(sid, 0)

    return {
        "sources": sources,
        "summary": {
            "total": len(sources),
            "enabled": len(sources) - counts["disabled"],
            "ok": counts["ok"],
            "warning": counts["warning"],
            "error": counts["error"],
            "disabled": counts["disabled"],
        },
    }


@router.get("/sources/{source_id}")
async def get_source(
    source_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Détails d'une source spécifique."""
    _require_admin(current_user)
    source = db.select_one("sources", id=f"eq.{source_id}")
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return source


@router.post("/sources/{source_id}/retry")
async def retry_source(
    source_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Réactive une source et relance le scraping."""
    _require_admin(current_user)
    result = db.update("sources", {
        "scraping_enabled": True,
        "consecutive_failures": 0,
        "last_error_message": None,
        "updated_at": datetime.utcnow().isoformat(),
    }, id=f"eq.{source_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return {"success": True, "source": result[0]}


@router.post("/sources/{source_id}/toggle")
async def toggle_source(
    source_id: UUID,
    enabled: bool,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Active ou désactive une source."""
    _require_admin(current_user)
    result = db.update("sources", {
        "scraping_enabled": enabled,
        "updated_at": datetime.utcnow().isoformat(),
    }, id=f"eq.{source_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return {"success": True, "source": result[0]}


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(
    body: CreateSourceRequest,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Crée une nouvelle source média."""
    _require_admin(current_user)
    now = datetime.utcnow().isoformat()
    source = db.insert_one("sources", {
        "name": body.name,
        "url": body.url,
        "type": body.source_type.upper(),
        "scraper_class": body.scraper_class,
        "prestige_score": body.prestige_score,
        "scraping_enabled": body.scraping_enabled,
        "created_at": now,
        "updated_at": now,
    })
    return {"success": True, "source": source}


@router.put("/sources/{source_id}")
async def update_source(
    source_id: UUID,
    body: UpdateSourceRequest,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Met à jour une source média."""
    _require_admin(current_user)
    update_data = body.model_dump(exclude_unset=True)
    if "source_type" in update_data:
        update_data["type"] = update_data.pop("source_type").upper()
    update_data["updated_at"] = datetime.utcnow().isoformat()
    result = db.update("sources", update_data, id=f"eq.{source_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    return {"success": True, "source": result[0]}


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Supprime une source et tous ses articles."""
    _require_admin(current_user)
    # Supprimer les mentions liées aux articles de cette source
    articles = db.select("articles", columns="id", source_id=f"eq.{source_id}")
    for a in articles:
        db.delete("mentions", article_id=f"eq.{a['id']}")
    db.delete("articles", source_id=f"eq.{source_id}")
    db.delete("sources", id=f"eq.{source_id}")
    return {"success": True}


# ------------------------------------------------------------------ #
# Organizations Admin
# ------------------------------------------------------------------ #


@router.get("/organizations")
async def list_organizations(
    plan: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Liste toutes les organisations avec statistiques."""
    _require_admin(current_user)
    filters = {"order": "created_at.desc"}
    if plan:
        filters["subscription_plan"] = f"eq.{plan.upper()}"
    if status_filter:
        filters["subscription_status"] = f"eq.{status_filter.upper()}"
    orgs = db.select("organizations", **filters)
    return {"organizations": orgs}


@router.get("/organizations/{org_id}")
async def get_organization(
    org_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Détails complets d'une organisation."""
    _require_admin(current_user)
    org = db.select_one("organizations", id=f"eq.{org_id}")
    if not org:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    users = db.select("users", columns="id,email,full_name,role", organization_id=f"eq.{org_id}")
    org["users"] = users
    return org


@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(
    org_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Suspend une organisation."""
    _require_admin(current_user)
    result = db.update("organizations", {
        "subscription_status": "SUSPENDED",
        "updated_at": datetime.utcnow().isoformat(),
    }, id=f"eq.{org_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    return {"success": True}


@router.post("/organizations/{org_id}/reactivate")
async def reactivate_organization(
    org_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Réactive une organisation suspendue."""
    _require_admin(current_user)
    result = db.update("organizations", {
        "subscription_status": "ACTIVE",
        "updated_at": datetime.utcnow().isoformat(),
    }, id=f"eq.{org_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    return {"success": True}


@router.patch("/organizations/{org_id}/limits")
async def update_organization_limits(
    org_id: UUID,
    body: UpdateLimitsRequest,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Met à jour les limites d'une organisation."""
    _require_admin(current_user)
    update_data = body.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()
    result = db.update("organizations", update_data, id=f"eq.{org_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    return {"success": True, "organization": result[0]}


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: CreateOrganizationRequest,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Crée une nouvelle organisation."""
    _require_admin(current_user)
    now = datetime.utcnow().isoformat()
    org = db.insert_one("organizations", {
        "name": body.name,
        "subscription_plan": body.subscription_plan.upper(),
        "subscription_status": body.subscription_status.upper(),
        "keyword_limit": body.keyword_limit,
        "user_limit": body.user_limit,
        "created_at": now,
        "updated_at": now,
    })
    return {"success": True, "organization": org}


@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: UUID,
    body: UpdateOrganizationRequest,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Met à jour une organisation."""
    _require_admin(current_user)
    update_data = body.model_dump(exclude_unset=True)
    if "subscription_plan" in update_data and update_data["subscription_plan"]:
        update_data["subscription_plan"] = update_data["subscription_plan"].upper()
    if "subscription_status" in update_data and update_data["subscription_status"]:
        update_data["subscription_status"] = update_data["subscription_status"].upper()
    update_data["updated_at"] = datetime.utcnow().isoformat()
    result = db.update("organizations", update_data, id=f"eq.{org_id}")
    if not result:
        raise HTTPException(status_code=404, detail="Organisation non trouvée")
    return {"success": True, "organization": result[0]}


@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Supprime une organisation et toutes ses données."""
    _require_admin(current_user)
    # Supprimer en cascade
    keywords = db.select("keywords", columns="id", organization_id=f"eq.{org_id}")
    for kw in keywords:
        db.delete("mentions", keyword_id=f"eq.{kw['id']}")
    db.delete("keywords", organization_id=f"eq.{org_id}")
    users = db.select("users", columns="id", organization_id=f"eq.{org_id}")
    for u in users:
        db.delete("alert_settings", user_id=f"eq.{u['id']}")
    db.delete("users", organization_id=f"eq.{org_id}")
    db.delete("organizations", id=f"eq.{org_id}")
    return {"success": True}
