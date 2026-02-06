"""Schémas pour l'authentification et l'inscription"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from src.models.organization import SubscriptionPlan


class SignupRequest(BaseModel):
    """Requête d'inscription avec paiement"""
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    full_name: str = Field(..., min_length=2, max_length=255, description="Nom complet")
    organization_name: str = Field(..., min_length=2, max_length=255, description="Nom de l'organisation")
    password: str = Field(..., min_length=8, description="Mot de passe (min 8 caractères)")
    subscription_plan: SubscriptionPlan = Field(default=SubscriptionPlan.BASIC, description="Plan d'abonnement")
    stripe_payment_method_id: Optional[str] = Field(None, description="ID du moyen de paiement Stripe")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valider la force du mot de passe"""
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.islower() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v


class SignupResponse(BaseModel):
    """Réponse après inscription réussie"""
    user_id: str = Field(..., description="ID de l'utilisateur créé")
    organization_id: str = Field(..., description="ID de l'organisation créée")
    email: str = Field(..., description="Email de l'utilisateur")
    full_name: str = Field(..., description="Nom complet")
    subscription_plan: str = Field(..., description="Plan d'abonnement")
    access_token: str = Field(..., description="Token d'accès JWT")
    refresh_token: str = Field(..., description="Token de rafraîchissement")
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Requête de connexion"""
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    password: str = Field(..., description="Mot de passe")


class LoginResponse(BaseModel):
    """Réponse après connexion réussie"""
    user_id: str = Field(..., description="ID de l'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")
    full_name: str = Field(..., description="Nom complet")
    role: str = Field(..., description="Rôle de l'utilisateur")
    organization_id: str = Field(..., description="ID de l'organisation")
    access_token: str = Field(..., description="Token d'accès JWT")
    refresh_token: str = Field(..., description="Token de rafraîchissement")
    
    class Config:
        from_attributes = True
