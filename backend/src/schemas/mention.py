"""Schémas Pydantic pour les mentions"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SourceResponse(BaseModel):
    """Réponse source simplifiée"""
    id: UUID
    name: str
    url: str
    type: str

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    """Réponse article simplifiée"""
    id: UUID
    title: str
    url: str
    author: Optional[str] = None
    published_at: datetime
    source: Optional[SourceResponse] = None

    class Config:
        from_attributes = True


class KeywordBrief(BaseModel):
    """Réponse keyword simplifiée"""
    id: UUID
    text: str
    category: str

    class Config:
        from_attributes = True


class MentionResponse(BaseModel):
    """Réponse mention pour la liste"""
    id: UUID
    matched_text: str
    match_context: str
    sentiment_score: float
    sentiment_label: str
    visibility_score: float
    theme: Optional[str] = None
    detected_at: datetime
    keyword: Optional[KeywordBrief] = None
    article: Optional[ArticleResponse] = None

    class Config:
        from_attributes = True


class MentionDetailResponse(MentionResponse):
    """Réponse mention détaillée avec contenu complet de l'article"""
    extracted_entities: Optional[dict] = None
    alert_sent: Optional[datetime] = None
    article_content: Optional[str] = None

    class Config:
        from_attributes = True


class MentionListResponse(BaseModel):
    """Réponse paginée de mentions"""
    mentions: list[MentionResponse]
    total: int
    limit: int
    offset: int
