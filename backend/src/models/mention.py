"""Modèle Mention - Mention d'un mot-clé dans un article"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from src.db.base import Base


class SentimentLabel(str, enum.Enum):
    """Labels de sentiment"""

    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class Theme(str, enum.Enum):
    """Thèmes d'articles"""

    POLITICS = "politics"
    ECONOMY = "economy"
    SPORT = "sport"
    SOCIETY = "society"
    TECHNOLOGY = "technology"
    CULTURE = "culture"
    OTHER = "other"


class Mention(Base):
    """Mention d'un mot-clé dans un article"""

    __tablename__ = "mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    keyword_id = Column(UUID(as_uuid=True), ForeignKey("keywords.id"), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False, index=True)
    matched_text = Column(String(255), nullable=False)
    match_context = Column(Text, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    sentiment_label = Column(SQLEnum(SentimentLabel), nullable=False)
    visibility_score = Column(Float, nullable=False, default=0.5)
    theme = Column(SQLEnum(Theme), nullable=True)
    extracted_entities = Column(JSONB, nullable=True)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    alert_sent = Column(DateTime, nullable=True)

    # Relations
    keyword = relationship("Keyword", back_populates="mentions")
    article = relationship("Article", back_populates="mentions")

    # Index composé pour éviter doublons et optimiser requêtes
    __table_args__ = (
        Index("idx_mention_keyword_article", "keyword_id", "article_id", unique=True),
        Index("idx_mention_sentiment_date", "sentiment_label", "detected_at"),
        Index("idx_mention_theme", "theme"),
    )

    def __repr__(self):
        return f"<Mention {self.matched_text} ({self.sentiment_label})>"
