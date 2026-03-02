"""Celery tasks pour le scraping avec circuit breaker"""
import asyncio
from datetime import datetime

from src.workers.celery_app import celery_app
from src.lib.logger import logger

# Circuit breaker: nombre max d'échecs consécutifs avant désactivation
MAX_CONSECUTIVE_FAILURES = 5


@celery_app.task(name="src.workers.tasks.scraping.scrape_all_sources")
def scrape_all_sources():
    """
    Tâche périodique: scrape toutes les sources actives.
    Exécutée toutes les 30 minutes par Celery Beat.
    Implémente un circuit breaker par source.
    """
    from src.db.base import SessionLocal
    from src.models.source import Source

    db = SessionLocal()
    try:
        sources = (
            db.query(Source)
            .filter(
                Source.scraping_enabled.is_(True),
                Source.consecutive_failures < MAX_CONSECUTIVE_FAILURES,
            )
            .all()
        )

        if not sources:
            logger.info("Aucune source active à scraper")
            return

        logger.info(f"Lancement scraping pour {len(sources)} sources")

        for source in sources:
            scrape_source.delay(str(source.id))

    except Exception as e:
        logger.error(f"Erreur scrape_all_sources: {str(e)}")
    finally:
        db.close()


@celery_app.task(
    name="src.workers.tasks.scraping.scrape_source",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def scrape_source(self, source_id: str):
    """
    Scrape une source individuelle.
    Implémente un circuit breaker: après MAX_CONSECUTIVE_FAILURES échecs,
    la source est désactivée automatiquement.
    """
    from src.db.base import SessionLocal
    from src.models.source import Source
    from src.models.article import Article
    from src.services.scraping.registry import get_scraper
    from src.services.scraping.deduplication import DeduplicationService

    db = SessionLocal()
    try:
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            logger.error(f"Source {source_id} non trouvée")
            return

        if not source.scraping_enabled:
            logger.info(f"Source {source.name} désactivée, skip")
            return

        # Circuit breaker check
        if source.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.warning(
                f"Circuit breaker ouvert pour {source.name}: "
                f"{source.consecutive_failures} échecs consécutifs"
            )
            source.scraping_enabled = False
            source.last_error_message = (
                f"Désactivé automatiquement après {source.consecutive_failures} échecs"
            )
            db.commit()
            return

        scraper = get_scraper(source.scraper_class)
        if not scraper:
            logger.error(f"Scraper {source.scraper_class} non trouvé pour {source.name}")
            return

        logger.info(f"Scraping {source.name}...")

        # Exécuter le scraping async
        loop = asyncio.new_event_loop()
        try:
            articles = loop.run_until_complete(scraper.scrape())
        finally:
            loop.close()

        # Déduplication
        dedup = DeduplicationService(db)
        new_articles = dedup.filter_new_articles(articles, source.id)

        # Sauvegarder les nouveaux articles
        saved_count = 0
        for scraped in new_articles:
            article = Article(
                title=scraped.title,
                url=scraped.url,
                content_hash=scraped.content_hash,
                raw_content=scraped.raw_content,
                cleaned_content=scraped.cleaned_content,
                author=scraped.author,
                published_at=scraped.published_at,
                source_id=source.id,
            )
            db.add(article)
            saved_count += 1

        # Mettre à jour la source: succès
        source.last_scrape_at = datetime.utcnow()
        source.last_success_at = datetime.utcnow()
        source.consecutive_failures = 0
        source.last_error_message = None

        db.commit()

        logger.info(
            f"Scraping {source.name} terminé: "
            f"{len(articles)} trouvés, {saved_count} nouveaux sauvegardés"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur scraping source {source_id}: {str(e)}")

        # Incrémenter le compteur d'échecs (circuit breaker)
        try:
            source = db.query(Source).filter(Source.id == source_id).first()
            if source:
                source.consecutive_failures += 1
                source.last_error_message = str(e)[:500]
                source.last_scrape_at = datetime.utcnow()
                db.commit()

                if source.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.warning(
                        f"Circuit breaker OUVERT pour {source.name} "
                        f"après {source.consecutive_failures} échecs"
                    )
        except Exception:
            pass

        # Retry Celery
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries atteint pour source {source_id}")

    finally:
        db.close()
