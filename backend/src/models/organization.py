"""Modèle Organization - Compte client/agence"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.db.base import Base


class SubscriptionPlan(str, enum.Enum):
    """Plans d'abonnement disponibles"""

    BASIC = "basic"  # 10 keywords, 1 user
    PRO = "pro"  # 50 keywords, 5 users
    ENTERPRISE = "enterprise"  # Unlimited keywords, unlimited users


class SubscriptionStatus(str, enum.Enum):
    """Statut d'abonnement"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELED = "canceled"
    TRIAL = "trial"


class Organization(Base):
    """Compte organisation/agence"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    subscription_plan = Column(
        SQLEnum(SubscriptionPlan), nullable=False, default=SubscriptionPlan.BASIC
    )
    subscription_status = Column(
        SQLEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL
    )
    keyword_limit = Column(Integer, nullable=False, default=10)
    user_limit = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    keywords = relationship("Keyword", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization {self.name} ({self.subscription_plan})>"
