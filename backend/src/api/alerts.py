"""Endpoints API pour les paramètres d'alertes"""
from datetime import datetime

from fastapi import APIRouter, Depends, status

from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.api.auth import get_current_active_user
from src.schemas.alert_setting import AlertSettingResponse, AlertSettingUpdate

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _get_or_create_settings(db: SupabaseDB, user: dict) -> dict:
    """Récupère ou crée les paramètres d'alertes pour un utilisateur."""
    settings = db.select_one("alert_settings", user_id=f"eq.{user['id']}")
    if not settings:
        now = datetime.utcnow().isoformat()
        settings = db.insert_one("alert_settings", {
            "user_id": user["id"],
            "enabled": True,
            "channel": "EMAIL",
            "frequency": "BATCH_1H",
            "negative_only": True,
            "min_sentiment_score": 0.3,
            "created_at": now,
            "updated_at": now,
        })
    return settings


@router.get("/settings", response_model=AlertSettingResponse)
async def get_alert_settings(
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> AlertSettingResponse:
    """Récupère les paramètres d'alertes de l'utilisateur."""
    settings = _get_or_create_settings(db, current_user)
    return AlertSettingResponse(
        id=settings["id"],
        user_id=settings["user_id"],
        enabled=settings["enabled"],
        channel=settings["channel"],
        frequency=settings["frequency"],
        negative_only=settings["negative_only"],
        min_sentiment_score=settings["min_sentiment_score"],
        quiet_hours_start=settings.get("quiet_hours_start"),
        quiet_hours_end=settings.get("quiet_hours_end"),
    )


@router.patch("/settings", response_model=AlertSettingResponse)
async def update_alert_settings(
    data: AlertSettingUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
) -> AlertSettingResponse:
    """Met à jour les paramètres d'alertes de l'utilisateur."""
    settings = _get_or_create_settings(db, current_user)

    update_data = data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = db.update("alert_settings", update_data, id=f"eq.{settings['id']}")
    updated = result[0] if result else settings

    return AlertSettingResponse(
        id=updated["id"],
        user_id=updated["user_id"],
        enabled=updated["enabled"],
        channel=updated["channel"],
        frequency=updated["frequency"],
        negative_only=updated["negative_only"],
        min_sentiment_score=updated["min_sentiment_score"],
        quiet_hours_start=updated.get("quiet_hours_start"),
        quiet_hours_end=updated.get("quiet_hours_end"),
    )
