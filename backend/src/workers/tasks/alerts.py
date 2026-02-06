"""Celery tasks pour l'envoi d'alertes email"""
from src.workers.celery_app import celery_app
from src.lib.logger import logger


@celery_app.task(name="src.workers.tasks.alerts.send_alert_for_mention")
def send_alert_for_mention(mention_id: str, user_id: str):
    """Envoie une alerte email immédiate pour une mention spécifique."""
    from src.db.base import SessionLocal
    from src.models.user import User
    from src.models.mention import Mention
    from src.services.alerts.alert_service import AlertService

    db = SessionLocal()
    try:
        mention = db.query(Mention).filter(Mention.id == mention_id).first()
        user = db.query(User).filter(User.id == user_id).first()

        if not mention or not user:
            logger.error(f"Mention {mention_id} ou User {user_id} non trouvé")
            return False

        service = AlertService(db)
        return service.send_single_alert(mention, user)
    except Exception as e:
        logger.error(f"Erreur envoi alerte mention {mention_id}: {str(e)}")
        return False
    finally:
        db.close()


@celery_app.task(name="src.workers.tasks.alerts.queue_alert_batch")
def queue_alert_batch(mention_id: str, user_id: str):
    """Ajoute une mention à la file de batching pour envoi groupé."""
    try:
        import redis
        redis_client = redis.from_url("redis://localhost:6379/0")

        from src.db.base import SessionLocal
        from src.services.alerts.alert_service import AlertService

        db = SessionLocal()
        try:
            service = AlertService(db, redis_client=redis_client)
            service.queue_alert_for_batching(mention_id, user_id)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur queue batch mention {mention_id}: {str(e)}")


@celery_app.task(name="src.workers.tasks.alerts.send_pending_alerts")
def send_pending_alerts():
    """
    Tâche périodique: envoie les alertes batch en attente.
    Exécutée toutes les 5 minutes par Celery Beat.
    """
    from src.db.base import SessionLocal
    from src.models.user import User
    from src.models.keyword import Keyword
    from src.services.alerts.alert_service import AlertService

    try:
        import redis
        redis_client = redis.from_url("redis://localhost:6379/0")
    except Exception as e:
        logger.error(f"Redis non disponible pour batch alerts: {str(e)}")
        return

    db = SessionLocal()
    try:
        # Trouver tous les utilisateurs avec des alertes en attente
        keys = redis_client.keys("alert_batch:*")
        if not keys:
            return

        sent_count = 0
        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            user_id = key_str.replace("alert_batch:", "")

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                redis_client.delete(key)
                continue

            service = AlertService(db, redis_client=redis_client)

            if not service.should_send_batch(user_id):
                continue

            mention_ids = service.get_pending_batch(user_id)
            if not mention_ids:
                continue

            success = service.send_batch_alert(user, mention_ids)
            if success:
                sent_count += 1
                logger.info(
                    f"Batch alert envoyé à {user.email}: "
                    f"{len(mention_ids)} mention(s)"
                )

        if sent_count:
            logger.info(f"Batch alerts: {sent_count} email(s) envoyé(s)")

    except Exception as e:
        logger.error(f"Erreur send_pending_alerts: {str(e)}")
    finally:
        db.close()
