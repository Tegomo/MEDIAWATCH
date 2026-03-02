"""Modèle Source - Source média à scraper"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.db.base import Base


class SourceType(str, enum.Enum):
    """Types de sources"""

    PRESS = "press"  # Site de presse
    WHATSAPP = "whatsapp"  # Groupe WhatsApp
    RSS = "rss"  # Flux RSS
    API = "api"  # API externe


class Source(Base):
    """Source média à scraper"""

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    url = Column(String(512), nullable=False)
    type = Column(SQLEnum(SourceType), nullable=False, default=SourceType.PRESS)
    scraper_class = Column(String(100), nullable=False)
    scraping_enabled = Column(Boolean, nullable=False, default=True)
    prestige_score = Column(Float, nullable=False, default=0.5)
    last_scrape_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    last_error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source {self.name} ({self.type})>"
