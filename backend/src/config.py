"""Configuration de l'application MediaWatch CI"""
import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application chargée depuis les variables d'environnement"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "MediaWatch CI"
    app_env: str = "development"
    debug: bool = True
    secret_key: str
    api_v1_prefix: str = "/v1"

    # Database (optionnel - utilise Supabase REST API par défaut)
    database_url: Optional[str] = None

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # SendGrid (Twilio Email)
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: str = "alerts@mediawatch.ci"
    sendgrid_from_name: str = "MediaWatch CI"

    # Alerts
    alert_batch_window_minutes: int = 60
    alert_max_retries: int = 3
    alert_retry_base_delay: int = 30

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    # Orange Money
    orange_money_api_key: Optional[str] = None
    orange_money_merchant_key: Optional[str] = None
    orange_money_api_url: Optional[str] = None

    # Storage
    storage_bucket: str = "mediawatch-exports"
    storage_url: Optional[str] = None

    # NLP Models
    spacy_model: str = "fr_core_news_lg"
    camembert_model: str = "camembert-base"

    # Scraping
    scraping_user_agent: str = "MediaWatch CI Bot/1.0"
    scraping_rate_limit: int = 30
    playwright_headless: bool = True
    
    # Jina AI Reader
    jina_api_key: Optional[str] = None

    # OpenRouter AI (résumé/nettoyage d'articles)
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "google/gemini-2.0-flash-001"

    # Monitoring
    sentry_dsn: Optional[str] = None

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Retourne la liste des origines CORS autorisées"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Retourne l'instance singleton des paramètres de configuration"""
    return Settings()


settings = get_settings()
