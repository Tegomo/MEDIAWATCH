"""Configuration de la base de données - Client Supabase REST API"""
from src.db.supabase_client import SupabaseDB, get_supabase_db


# Compatibilité: SessionLocal retourne le client Supabase
def SessionLocal():
    """Retourne le client Supabase DB (compatibilité avec l'ancien code)."""
    return get_supabase_db()


# Base factice pour compatibilité avec les imports existants
class Base:
    pass


def get_db():
    """Dependency injection pour FastAPI - retourne le client Supabase."""
    yield get_supabase_db()
