"""Modèle AlertSetting - Paramètres d'alertes par utilisateur"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.db.base import Base


class AlertChannel(str, enum.Enum):
    """Canaux d'alerte disponibles"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class AlertFrequency(str, enum.Enum):
    """Fréquence d'envoi des alertes"""
    IMMEDIATE = "immediate"
    BATCH_1H = "batch_1h"
    BATCH_4H = "batch_4h"
    DAILY = "daily"


class AlertSetting(Base):
    """Paramètres d'alertes pour un utilisateur"""

    __tablename__ = "alert_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)
    channel = Column(SQLEnum(AlertChannel), nullable=False, default=AlertChannel.EMAIL)
    frequency = Column(SQLEnum(AlertFrequency), nullable=False, default=AlertFrequency.BATCH_1H)
    negative_only = Column(Boolean, nullable=False, default=True)
    min_sentiment_score = Column(Float, nullable=False, default=0.3)
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)  # "07:00"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    user = relationship("User", backref="alert_settings")

    def __repr__(self):
        return f"<AlertSetting user={self.user_id} enabled={self.enabled} channel={self.channel}>"
