"""Service de monitoring de santé des sources média"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.source import Source
from src.models.article import Article
from src.lib.logger import logger


class SourceHealthService:
    """Service pour le monitoring et la gestion des sources de scraping"""

    def __init__(self, db: Session):
        self.db = db

    def list_sources(self) -> list[dict]:
        """
        Liste toutes les sources avec leurs statistiques de santé.
        """
        sources = self.db.query(Source).order_by(Source.name).all()

        result = []
        for source in sources:
            # Compter les articles des dernières 24h
            from datetime import timedelta
            day_ago = datetime.utcnow() - timedelta(hours=24)
            articles_24h = (
                self.db.query(func.count(Article.id))
                .filter(Article.source_id == source.id, Article.scraped_at >= day_ago)
                .scalar()
            )

            # Total articles
            total_articles = (
                self.db.query(func.count(Article.id))
                .filter(Article.source_id == source.id)
                .scalar()
            )

            # Déterminer le statut
            if not source.scraping_enabled:
                status = "disabled"
            elif source.consecutive_failures >= 5:
                status = "error"
            elif source.consecutive_failures > 0:
                status = "warning"
            else:
                status = "ok"

            result.append({
                "id": str(source.id),
                "name": source.name,
                "url": source.url,
                "type": source.type.value,
                "scraper_class": source.scraper_class,
                "scraping_enabled": source.scraping_enabled,
                "prestige_score": source.prestige_score,
                "status": status,
                "consecutive_failures": source.consecutive_failures,
                "last_scrape_at": source.last_scrape_at.isoformat() if source.last_scrape_at else None,
                "last_success_at": source.last_success_at.isoformat() if source.last_success_at else None,
                "last_error_message": source.last_error_message,
                "articles_24h": articles_24h,
                "total_articles": total_articles,
            })

        return result

    def get_source(self, source_id: UUID) -> Optional[dict]:
        """Récupère les détails d'une source."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return None

        sources = self.list_sources()
        return next((s for s in sources if s["id"] == str(source_id)), None)

    def retry_source(self, source_id: UUID) -> dict:
        """
        Réactive une source et réinitialise ses compteurs d'erreur.
        Lance un scraping immédiat via Celery.
        """
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"success": False, "error": "Source non trouvée"}

        # Réinitialiser les compteurs
        source.scraping_enabled = True
        source.consecutive_failures = 0
        source.last_error_message = None
        source.updated_at = datetime.utcnow()
        self.db.commit()

        # Lancer un scraping immédiat
        try:
            from src.workers.tasks.scraping import scrape_source
            scrape_source.delay(str(source.id))
            logger.info(f"Retry source {source.name}: scraping relancé")
        except Exception as e:
            logger.warning(f"Impossible de lancer le scraping pour {source.name}: {str(e)}")

        return {
            "success": True,
            "message": f"Source {source.name} réactivée, scraping en cours",
        }

    def toggle_source(self, source_id: UUID, enabled: bool) -> dict:
        """Active ou désactive une source."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"success": False, "error": "Source non trouvée"}

        source.scraping_enabled = enabled
        if enabled:
            source.consecutive_failures = 0
            source.last_error_message = None
        source.updated_at = datetime.utcnow()
        self.db.commit()

        action = "activée" if enabled else "désactivée"
        logger.info(f"Source {source.name} {action}")
        return {"success": True, "message": f"Source {source.name} {action}"}

    def create_source(
        self,
        name: str,
        url: str,
        source_type: str = "press",
        scraper_class: str = "generic",
        prestige_score: float = 0.5,
        scraping_enabled: bool = True,
    ) -> dict:
        """Crée une nouvelle source."""
        from src.models.source import SourceType

        # Vérifier unicité du nom
        existing = self.db.query(Source).filter(Source.name == name).first()
        if existing:
            return {"success": False, "error": f"Une source nommée '{name}' existe déjà"}

        try:
            type_enum = SourceType(source_type)
        except ValueError:
            return {"success": False, "error": f"Type invalide: {source_type}. Valeurs: press, rss, api, whatsapp"}

        source = Source(
            name=name,
            url=url,
            type=type_enum,
            scraper_class=scraper_class,
            prestige_score=prestige_score,
            scraping_enabled=scraping_enabled,
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        logger.info(f"Source créée: {source.name} ({source.url})")
        return {
            "success": True,
            "message": f"Source {source.name} créée",
            "id": str(source.id),
        }

    def update_source(
        self,
        source_id: UUID,
        name: Optional[str] = None,
        url: Optional[str] = None,
        source_type: Optional[str] = None,
        scraper_class: Optional[str] = None,
        prestige_score: Optional[float] = None,
        scraping_enabled: Optional[bool] = None,
    ) -> dict:
        """Met à jour une source existante."""
        from src.models.source import SourceType

        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"success": False, "error": "Source non trouvée"}

        if name is not None:
            # Vérifier unicité
            dup = self.db.query(Source).filter(Source.name == name, Source.id != source_id).first()
            if dup:
                return {"success": False, "error": f"Une source nommée '{name}' existe déjà"}
            source.name = name

        if url is not None:
            source.url = url

        if source_type is not None:
            try:
                source.type = SourceType(source_type)
            except ValueError:
                return {"success": False, "error": f"Type invalide: {source_type}"}

        if scraper_class is not None:
            source.scraper_class = scraper_class

        if prestige_score is not None:
            source.prestige_score = prestige_score

        if scraping_enabled is not None:
            source.scraping_enabled = scraping_enabled
            if scraping_enabled:
                source.consecutive_failures = 0
                source.last_error_message = None

        source.updated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Source mise à jour: {source.name}")
        return {
            "success": True,
            "message": f"Source {source.name} mise à jour",
            "source": {
                "id": str(source.id),
                "name": source.name,
                "url": source.url,
                "type": source.type.value,
                "scraper_class": source.scraper_class,
                "prestige_score": source.prestige_score,
                "scraping_enabled": source.scraping_enabled,
            },
        }

    def delete_source(self, source_id: UUID) -> dict:
        """Supprime une source et tous ses articles associés."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"success": False, "error": "Source non trouvée"}

        source_name = source.name
        self.db.delete(source)
        self.db.commit()

        logger.info(f"Source supprimée: {source_name}")
        return {"success": True, "message": f"Source {source_name} supprimée"}

    def get_health_summary(self) -> dict:
        """Résumé global de la santé des sources."""
        sources = self.db.query(Source).all()

        total = len(sources)
        enabled = sum(1 for s in sources if s.scraping_enabled)
        ok = sum(1 for s in sources if s.scraping_enabled and s.consecutive_failures == 0)
        warning = sum(1 for s in sources if s.scraping_enabled and 0 < s.consecutive_failures < 5)
        error = sum(1 for s in sources if s.scraping_enabled and s.consecutive_failures >= 5)
        disabled = total - enabled

        return {
            "total": total,
            "enabled": enabled,
            "ok": ok,
            "warning": warning,
            "error": error,
            "disabled": disabled,
        }
