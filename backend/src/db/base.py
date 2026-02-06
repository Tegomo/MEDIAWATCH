"""Configuration de la base de données SQLAlchemy"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.config import settings

# Créer le moteur de base de données
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

# Créer la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


def get_db():
    """Générateur de session de base de données pour FastAPI dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
