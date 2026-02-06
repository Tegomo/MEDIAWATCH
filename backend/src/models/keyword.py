"""Modèle Keyword - Mot-clé à surveiller"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.db.base import Base


class KeywordCategory(str, enum.Enum):
    """Catégories de mots-clés"""

    BRAND = "brand"
    PRODUCT = "product"
    PERSON = "person"
    COMPETITOR = "competitor"
    CUSTOM = "custom"


class Keyword(Base):
    """Mot-clé à surveiller"""

    __tablename__ = "keywords"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    text = Column(String(255), nullable=False, index=True)
    normalized_text = Column(String(255), nullable=False, index=True)
    category = Column(SQLEnum(KeywordCategory), nullable=False, default=KeywordCategory.CUSTOM)
    enabled = Column(Boolean, nullable=False, default=True)
    alert_enabled = Column(Boolean, nullable=False, default=True)
    alert_threshold = Column(Float, nullable=False, default=0.3)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    total_mentions_count = Column(Integer, nullable=False, default=0)
    last_mention_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    organization = relationship("Organization", back_populates="keywords")
    mentions = relationship("Mention", back_populates="keyword", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Keyword {self.text} ({self.category})>"
