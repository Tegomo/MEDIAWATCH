"""Schémas pour les mots-clés"""
from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class KeywordCategory(str, Enum):
    BRAND = "BRAND"
    PRODUCT = "PRODUCT"
    PERSON = "PERSON"
    COMPETITOR = "COMPETITOR"
    ORGANIZATION = "ORGANIZATION"
    TOPIC = "TOPIC"
    CUSTOM = "CUSTOM"


class KeywordCreate(BaseModel):
    """Schéma pour créer un mot-clé"""
    text: str = Field(..., min_length=2, max_length=255, description="Texte du mot-clé")
    category: KeywordCategory = Field(default=KeywordCategory.CUSTOM, description="Catégorie du mot-clé")
    enabled: bool = Field(default=True, description="Activer la surveillance")
    alert_enabled: bool = Field(default=True, description="Activer les alertes")
    alert_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Seuil d'alerte (0-1)")
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Valider le texte du mot-clé"""
        # Supprimer les espaces en début/fin
        v = v.strip()
        
        # Vérifier qu'il ne contient pas de caractères interdits
        forbidden_chars = ['<', '>', '{', '}', '[', ']', '\\', '|']
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f"Le mot-clé ne peut pas contenir le caractère '{char}'")
        
        return v


class KeywordUpdate(BaseModel):
    """Schéma pour mettre à jour un mot-clé"""
    text: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = None
    enabled: Optional[bool] = None
    alert_enabled: Optional[bool] = None
    alert_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        """Valider le texte du mot-clé"""
        if v is None:
            return v
        
        v = v.strip()
        forbidden_chars = ['<', '>', '{', '}', '[', ']', '\\', '|']
        for char in forbidden_chars:
            if char in v:
                raise ValueError(f"Le mot-clé ne peut pas contenir le caractère '{char}'")
        
        return v


class KeywordResponse(BaseModel):
    """Schéma de réponse pour un mot-clé"""
    id: str
    text: str
    normalized_text: str
    category: str
    enabled: bool
    alert_enabled: bool
    alert_threshold: float
    organization_id: str
    total_mentions_count: int
    last_mention_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KeywordListResponse(BaseModel):
    """Schéma de réponse pour une liste de mots-clés"""
    keywords: list[KeywordResponse]
    total: int
    limit: int
    offset: int
