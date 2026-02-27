"""Health check endpoint pour le monitoring"""
from datetime import datetime

from fastapi import APIRouter

from src.db.base import SessionLocal
from src.lib.logger import logger

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Vérifie la santé de l'application.
    Retourne le statut de la DB, Redis et des services.
    """
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    # Check DB (Supabase REST)
    try:
        db = SessionLocal()
        if db.health_check():
            checks["services"]["database"] = {"status": "ok"}
        else:
            checks["services"]["database"] = {"status": "error", "detail": "Health check failed"}
            checks["status"] = "degraded"
    except Exception as e:
        checks["services"]["database"] = {"status": "error", "detail": str(e)}
        checks["status"] = "degraded"

    # Check Redis
    try:
        import redis
        from src.config import settings
        r = redis.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        checks["services"]["redis"] = {"status": "ok"}
    except Exception as e:
        checks["services"]["redis"] = {"status": "error", "detail": str(e)}
        checks["status"] = "degraded"

    return checks
