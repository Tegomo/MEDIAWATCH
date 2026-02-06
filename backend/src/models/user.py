"""Modèle User - Utilisateur de la plateforme"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from src.db.base import Base


class UserRole(str, enum.Enum):
    """Rôles utilisateur"""

    ADMIN = "admin"  # Admin plateforme
    CLIENT = "client"  # Client avec accès complet à son org
    VIEWER = "viewer"  # Lecture seule


class User(Base):
    """Utilisateur de la plateforme"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.CLIENT)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    supabase_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    organization = relationship("Organization", back_populates="users")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
