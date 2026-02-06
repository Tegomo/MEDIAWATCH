"""Configuration Celery pour tâches asynchrones"""
from celery import Celery
from celery.schedules import crontab

from src.config import settings

celery_app = Celery(
    "mediawatch",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.workers.tasks.scraping",
        "src.workers.tasks.nlp",
        "src.workers.tasks.mention_detection",
        "src.workers.tasks.alerts",
        "src.workers.tasks.exports",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    "scrape-all-sources": {
        "task": "src.workers.tasks.scraping.scrape_all_sources",
        "schedule": crontab(minute="*/30"),
    },
    "process-pending-nlp": {
        "task": "src.workers.tasks.nlp.process_pending_articles",
        "schedule": crontab(minute="*/5"),
    },
    "detect-mentions": {
        "task": "src.workers.tasks.mention_detection.detect_all_mentions",
        "schedule": crontab(minute="*/10"),
    },
    "send-alert-batches": {
        "task": "src.workers.tasks.alerts.send_pending_alerts",
        "schedule": crontab(minute="*/5"),
    },
}

if __name__ == "__main__":
    celery_app.start()
