"""Modèle Article - Article scrapé"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.base import Base


class Article(Base):
    """Article scrapé depuis une source"""

    __tablename__ = "articles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(512), nullable=False)
    url = Column(String(1024), nullable=False, unique=True, index=True)
    content_hash = Column(String(64), nullable=False, index=True)
    raw_content = Column(Text, nullable=False)
    cleaned_content = Column(Text, nullable=False)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=False, index=True)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True)
    nlp_processed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relations
    source = relationship("Source", back_populates="articles")
    mentions = relationship("Mention", back_populates="article", cascade="all, delete-orphan")

    # Index composé pour éviter doublons
    __table_args__ = (Index("idx_article_source_hash", "source_id", "content_hash"),)

    def __repr__(self):
        return f"<Article {self.title[:50]}>"
