"""Schémas Pydantic pour les paramètres d'alertes"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AlertSettingResponse(BaseModel):
    """Réponse paramètres d'alertes"""
    id: UUID
    user_id: UUID
    enabled: bool
    channel: str
    frequency: str
    negative_only: bool
    min_sentiment_score: float
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

    class Config:
        from_attributes = True


class AlertSettingUpdate(BaseModel):
    """Mise à jour des paramètres d'alertes"""
    enabled: Optional[bool] = None
    channel: Optional[str] = None
    frequency: Optional[str] = None
    negative_only: Optional[bool] = None
    min_sentiment_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
