"""Service métier pour la gestion des mots-clés"""
from typing import Optional, List
from datetime import datetime
import uuid
import unicodedata
import re

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.keyword import Keyword, KeywordCategory
from src.models.organization import Organization
from src.models.user import User
from src.schemas.keyword import KeywordCreate, KeywordUpdate


class KeywordService:
    """Service pour gérer les mots-clés"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliser un texte pour la recherche.
        
        - Convertir en minuscules
        - Supprimer les accents
        - Supprimer les caractères spéciaux
        - Normaliser les espaces
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte normalisé
        """
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les accents
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Remplacer les caractères spéciaux par des espaces
        text = re.sub(r'[^\w\s-]', ' ', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def create_keyword(
        db: Session,
        keyword_data: KeywordCreate,
        current_user: User
    ) -> Keyword:
        """
        Créer un nouveau mot-clé.
        
        Vérifie les limites du plan avant création.
        
        Args:
            db: Session de base de données
            keyword_data: Données du mot-clé
            current_user: Utilisateur courant
            
        Returns:
            Mot-clé créé
            
        Raises:
            HTTPException: Si la limite est atteinte ou si le mot-clé existe déjà
        """
        organization = current_user.organization
        
        # Vérifier la limite de mots-clés
        current_count = db.query(Keyword).filter(
            Keyword.organization_id == organization.id
        ).count()
        
        if current_count >= organization.keyword_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de mots-clés atteinte ({organization.keyword_limit}). "
                       f"Veuillez upgrader votre plan pour ajouter plus de mots-clés."
            )
        
        # Normaliser le texte
        normalized_text = KeywordService.normalize_text(keyword_data.text)
        
        # Vérifier si le mot-clé existe déjà (même texte normalisé)
        existing = db.query(Keyword).filter(
            Keyword.organization_id == organization.id,
            Keyword.normalized_text == normalized_text
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un mot-clé similaire existe déjà: '{existing.text}'"
            )
        
        # Créer le mot-clé
        keyword = Keyword(
            id=uuid.uuid4(),
            text=keyword_data.text.strip(),
            normalized_text=normalized_text,
            category=keyword_data.category,
            enabled=keyword_data.enabled,
            alert_enabled=keyword_data.alert_enabled,
            alert_threshold=keyword_data.alert_threshold,
            organization_id=organization.id,
            total_mentions_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(keyword)
        db.commit()
        db.refresh(keyword)
        
        return keyword
    
    @staticmethod
    def get_keywords(
        db: Session,
        organization_id: uuid.UUID,
        enabled_only: bool = False,
        category: Optional[KeywordCategory] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Keyword], int]:
        """
        Récupérer les mots-clés d'une organisation.
        
        Args:
            db: Session de base de données
            organization_id: ID de l'organisation
            enabled_only: Ne retourner que les mots-clés activés
            category: Filtrer par catégorie
            limit: Nombre maximum de résultats
            offset: Décalage pour la pagination
            
        Returns:
            Tuple (liste de mots-clés, total)
        """
        query = db.query(Keyword).filter(Keyword.organization_id == organization_id)
        
        if enabled_only:
            query = query.filter(Keyword.enabled == True)
        
        if category:
            query = query.filter(Keyword.category == category)
        
        total = query.count()
        keywords = query.order_by(Keyword.created_at.desc()).limit(limit).offset(offset).all()
        
        return keywords, total
    
    @staticmethod
    def get_keyword(
        db: Session,
        keyword_id: uuid.UUID,
        organization_id: uuid.UUID
    ) -> Keyword:
        """
        Récupérer un mot-clé par son ID.
        
        Args:
            db: Session de base de données
            keyword_id: ID du mot-clé
            organization_id: ID de l'organisation (pour vérification)
            
        Returns:
            Mot-clé trouvé
            
        Raises:
            HTTPException: Si le mot-clé n'existe pas
        """
        keyword = db.query(Keyword).filter(
            Keyword.id == keyword_id,
            Keyword.organization_id == organization_id
        ).first()
        
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mot-clé non trouvé"
            )
        
        return keyword
    
    @staticmethod
    def update_keyword(
        db: Session,
        keyword_id: uuid.UUID,
        keyword_data: KeywordUpdate,
        current_user: User
    ) -> Keyword:
        """
        Mettre à jour un mot-clé.
        
        Args:
            db: Session de base de données
            keyword_id: ID du mot-clé
            keyword_data: Nouvelles données
            current_user: Utilisateur courant
            
        Returns:
            Mot-clé mis à jour
        """
        keyword = KeywordService.get_keyword(db, keyword_id, current_user.organization_id)
        
        # Mettre à jour les champs fournis
        if keyword_data.text is not None:
            keyword.text = keyword_data.text.strip()
            keyword.normalized_text = KeywordService.normalize_text(keyword_data.text)
        
        if keyword_data.category is not None:
            keyword.category = keyword_data.category
        
        if keyword_data.enabled is not None:
            keyword.enabled = keyword_data.enabled
        
        if keyword_data.alert_enabled is not None:
            keyword.alert_enabled = keyword_data.alert_enabled
        
        if keyword_data.alert_threshold is not None:
            keyword.alert_threshold = keyword_data.alert_threshold
        
        keyword.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(keyword)
        
        return keyword
    
    @staticmethod
    def delete_keyword(
        db: Session,
        keyword_id: uuid.UUID,
        current_user: User
    ) -> None:
        """
        Supprimer un mot-clé.
        
        Args:
            db: Session de base de données
            keyword_id: ID du mot-clé
            current_user: Utilisateur courant
        """
        keyword = KeywordService.get_keyword(db, keyword_id, current_user.organization_id)
        
        db.delete(keyword)
        db.commit()
