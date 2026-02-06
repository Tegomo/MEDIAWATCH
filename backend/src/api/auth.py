"""Authentification et autorisation avec Supabase"""
from functools import wraps
from typing import Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from sqlalchemy.orm import Session

from src.config import settings
from src.db.base import get_db
from src.models.user import User, UserRole
from src.models.organization import Organization, SubscriptionPlan, SubscriptionStatus
from src.schemas.auth import SignupRequest, SignupResponse, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def supabase_auth_request(method: str, endpoint: str, data: dict = None):
    """Effectuer une requête HTTP à l'API Supabase Auth"""
    url = f"{settings.supabase_url}/auth/v1{endpoint}"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json"
    }
    
    with httpx.Client() as client:
        if method == "POST":
            response = client.post(url, json=data, headers=headers)
        elif method == "GET":
            response = client.get(url, headers=headers)
        else:
            raise ValueError(f"Méthode HTTP non supportée: {method}")
        
        response.raise_for_status()
        return response.json()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Récupère l'utilisateur courant depuis le token JWT Supabase"""
    token = credentials.credentials

    try:
        # Vérifier le token avec l'API Supabase
        url = f"{settings.supabase_url}/auth/v1/user"
        headers = {
            "apikey": settings.supabase_service_key,
            "Authorization": f"Bearer {token}",
        }
        
        with httpx.Client() as client:
            response = client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide ou expiré",
                )
            
            user_data = response.json()
            supabase_user_id = user_data.get("id")

        # Récupérer l'utilisateur depuis la DB
        user = db.query(User).filter(User.supabase_user_id == supabase_user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé",
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT invalide",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erreur d'authentification: {str(e)}",
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Vérifie que l'utilisateur est actif"""
    # Vérifier que l'organisation n'est pas suspendue
    if current_user.organization.subscription_status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte suspendu. Veuillez contacter le support.",
        )
    return current_user


def require_role(allowed_roles: list[UserRole]):
    """Décorateur pour vérifier le rôle de l'utilisateur"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_active_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permissions insuffisantes",
                )
            return await func(*args, current_user=current_user, **kwargs)

        return wrapper

    return decorator


async def get_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Vérifie que l'utilisateur est admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_user


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db),
) -> SignupResponse:
    """
    Créer un nouveau compte utilisateur avec organisation.
    
    Flux:
    1. Créer l'utilisateur dans Supabase Auth
    2. Créer l'organisation dans la DB
    3. Créer l'utilisateur dans la DB (lié à Supabase)
    4. Si paiement requis, traiter via Stripe (sera implémenté dans T021)
    5. Retourner les tokens d'authentification
    """
    try:
        # 1. Vérifier si l'email existe déjà
        existing_user = db.query(User).filter(User.email == signup_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un compte avec cet email existe déjà",
            )
        
        # 2. Créer l'utilisateur dans Supabase Auth
        try:
            auth_response = supabase_auth_request("POST", "/signup", {
                "email": signup_data.email,
                "password": signup_data.password,
            })
            
            if not auth_response.get("user"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur lors de la création du compte Supabase",
                )
            
            supabase_user_id = auth_response["user"]["id"]
            session_data = auth_response.get("session", {})
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur Supabase: {e.response.text}",
            )
        
        # 3. Déterminer les limites selon le plan
        plan_limits = {
            SubscriptionPlan.BASIC: {"keyword_limit": 10, "user_limit": 1},
            SubscriptionPlan.PRO: {"keyword_limit": 50, "user_limit": 5},
            SubscriptionPlan.ENTERPRISE: {"keyword_limit": 999, "user_limit": 999},
        }
        limits = plan_limits.get(signup_data.subscription_plan, plan_limits[SubscriptionPlan.BASIC])
        
        # 4. Créer l'organisation
        organization = Organization(
            id=uuid.uuid4(),
            name=signup_data.organization_name,
            subscription_plan=signup_data.subscription_plan,
            subscription_status=SubscriptionStatus.TRIAL,  # Commence en trial
            keyword_limit=limits["keyword_limit"],
            user_limit=limits["user_limit"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(organization)
        
        # 5. Créer l'utilisateur dans la DB
        user = User(
            id=uuid.uuid4(),
            email=signup_data.email,
            full_name=signup_data.full_name,
            role=UserRole.ADMIN,  # Premier utilisateur = admin de l'org
            organization_id=organization.id,
            supabase_user_id=supabase_user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        
        # 6. Commit les changements
        db.commit()
        db.refresh(organization)
        db.refresh(user)
        
        # 7. Retourner la réponse avec les tokens
        return SignupResponse(
            user_id=str(user.id),
            organization_id=str(organization.id),
            email=user.email,
            full_name=user.full_name,
            subscription_plan=organization.subscription_plan.value,
            access_token=session_data.get("access_token", ""),
            refresh_token=session_data.get("refresh_token", ""),
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Si erreur, supprimer l'utilisateur Supabase créé
        try:
            if 'supabase_user_id' in locals():
                supabase_auth_request("DELETE", f"/admin/users/{supabase_user_id}")
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'inscription: {str(e)}",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """
    Connexion d'un utilisateur existant.
    """
    try:
        # 1. Authentifier avec l'API Supabase
        try:
            auth_response = supabase_auth_request("POST", "/token?grant_type=password", {
                "email": login_data.email,
                "password": login_data.password,
            })
            
            if not auth_response.get("user") or not auth_response.get("access_token"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou mot de passe incorrect",
                )
        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
            )
        
        # 2. Récupérer l'utilisateur depuis la DB
        user = db.query(User).filter(
            User.supabase_user_id == auth_response["user"]["id"]
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé dans la base de données",
            )
        
        # 3. Vérifier que l'organisation n'est pas suspendue
        if user.organization.subscription_status == SubscriptionStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte suspendu. Veuillez contacter le support.",
            )
        
        # 4. Retourner la réponse avec les tokens
        return LoginResponse(
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            organization_id=str(user.organization_id),
            access_token=auth_response["access_token"],
            refresh_token=auth_response["refresh_token"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la connexion: {str(e)}",
        )
