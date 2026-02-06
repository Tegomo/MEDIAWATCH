"""Point d'entrée principal de l'API FastAPI MediaWatch CI"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.api.errors import setup_exception_handlers
from src.lib.logger import logger

# Sentry monitoring (T130)
if settings.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            traces_sample_rate=0.1,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        )
        logger.info("Sentry monitoring activé")
    except ImportError:
        logger.warning("sentry-sdk non installé, monitoring désactivé")
from src.api import auth, keywords, mentions, alerts, analytics, exports, admin, health
from src.api.webhooks import stripe as stripe_webhook
from src.api.webhooks import orange_money as om_webhook

# Créer l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    description="API REST pour la plateforme MediaWatch CI - Veille médias automatisée",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
from src.api.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=120, burst_limit=20)

# Configuration des gestionnaires d'erreurs
setup_exception_handlers(app)

# Enregistrement des routes
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(keywords.router, prefix=settings.api_v1_prefix)
app.include_router(mentions.router, prefix=settings.api_v1_prefix)
app.include_router(alerts.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(exports.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(health.router)
app.include_router(stripe_webhook.router, prefix=settings.api_v1_prefix)
app.include_router(om_webhook.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Route racine"""
    return {
        "message": "MediaWatch CI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


# Import et enregistrement des routes (à ajouter après création des endpoints)
# from src.api import auth, keywords, mentions, analytics, alerts, exports, admin
# app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
# app.include_router(keywords.router, prefix=f"{settings.api_v1_prefix}/keywords", tags=["keywords"])
# app.include_router(mentions.router, prefix=f"{settings.api_v1_prefix}/mentions", tags=["mentions"])
# app.include_router(analytics.router, prefix=f"{settings.api_v1_prefix}/analytics", tags=["analytics"])
# app.include_router(alerts.router, prefix=f"{settings.api_v1_prefix}/alerts", tags=["alerts"])
# app.include_router(exports.router, prefix=f"{settings.api_v1_prefix}/exports", tags=["exports"])
# app.include_router(admin.router, prefix=f"{settings.api_v1_prefix}/admin", tags=["admin"])


@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'application"""
    logger.info(f"Démarrage de {settings.app_name} en mode {settings.app_env}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions à l'arrêt de l'application"""
    logger.info(f"Arrêt de {settings.app_name}")
    logger.info(f"Arrêt de {settings.app_name}")
