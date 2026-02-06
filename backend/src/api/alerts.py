"""Endpoints API pour les paramètres d'alertes"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.models.alert_setting import AlertSetting, AlertChannel, AlertFrequency
from src.schemas.alert_setting import AlertSettingResponse, AlertSettingUpdate

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _get_or_create_settings(db: Session, user: User) -> AlertSetting:
    """Récupère ou crée les paramètres d'alertes pour un utilisateur."""
    settings = db.query(AlertSetting).filter(AlertSetting.user_id == user.id).first()
    if not settings:
        settings = AlertSetting(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/settings", response_model=AlertSettingResponse)
async def get_alert_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AlertSettingResponse:
    """Récupère les paramètres d'alertes de l'utilisateur."""
    settings = _get_or_create_settings(db, current_user)
    return AlertSettingResponse(
        id=settings.id,
        user_id=settings.user_id,
        enabled=settings.enabled,
        channel=settings.channel.value,
        frequency=settings.frequency.value,
        negative_only=settings.negative_only,
        min_sentiment_score=settings.min_sentiment_score,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
    )


@router.patch("/settings", response_model=AlertSettingResponse)
async def update_alert_settings(
    data: AlertSettingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AlertSettingResponse:
    """Met à jour les paramètres d'alertes de l'utilisateur."""
    settings = _get_or_create_settings(db, current_user)

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "channel" and value is not None:
            value = AlertChannel(value)
        elif field == "frequency" and value is not None:
            value = AlertFrequency(value)
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return AlertSettingResponse(
        id=settings.id,
        user_id=settings.user_id,
        enabled=settings.enabled,
        channel=settings.channel.value,
        frequency=settings.frequency.value,
        negative_only=settings.negative_only,
        min_sentiment_score=settings.min_sentiment_score,
        quiet_hours_start=settings.quiet_hours_start,
        quiet_hours_end=settings.quiet_hours_end,
    )
