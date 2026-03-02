"""Celery tasks pour les exports PDF async"""
from src.workers.celery_app import celery_app
from src.lib.logger import logger


@celery_app.task(name="src.workers.tasks.exports.generate_pdf_export")
def generate_pdf_export(
    organization_id: str,
    user_email: str,
    sentiment: str | None = None,
    source_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    theme: str | None = None,
    keyword_id: str | None = None,
):
    """
    Génère un export PDF de manière asynchrone.
    Sauvegarde le fichier et envoie un email avec le lien de téléchargement.
    """
    from datetime import datetime
    from uuid import UUID
    from src.db.base import SessionLocal
    from src.services.exports.pdf_exporter import PDFExporter
    from src.services.storage_service import StorageService

    db = SessionLocal()
    try:
        logger.info(f"Export PDF async pour {user_email}")

        # Parser les dates si fournies
        parsed_date_from = datetime.fromisoformat(date_from) if date_from else None
        parsed_date_to = datetime.fromisoformat(date_to) if date_to else None
        parsed_source_id = UUID(source_id) if source_id else None
        parsed_keyword_id = UUID(keyword_id) if keyword_id else None

        exporter = PDFExporter(db)
        pdf_bytes, count = exporter.export(
            organization_id=UUID(organization_id),
            sentiment=sentiment,
            source_id=parsed_source_id,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            search=search,
            theme=theme,
            keyword_id=parsed_keyword_id,
        )

        # Sauvegarder le fichier
        storage = StorageService()
        filename = exporter.get_filename()
        file_id = storage.save_file(pdf_bytes, filename, "application/pdf")
        download_url = storage.get_download_url(file_id)

        logger.info(f"Export PDF terminé: {count} mentions, fichier {file_id}")

        # Envoyer email de notification (best-effort)
        try:
            from src.services.alerts.alert_service import AlertService
            alert_service = AlertService(db)
            alert_service._send_email(
                to_email=user_email,
                subject="Votre export MediaWatch est prêt",
                html_content=f"""
                <h2>Export PDF prêt</h2>
                <p>Votre rapport contenant <strong>{count} mentions</strong> est disponible.</p>
                <p><a href="{download_url}">Télécharger le rapport</a></p>
                <p><em>Ce lien expire dans 24 heures.</em></p>
                """,
            )
        except Exception as e:
            logger.warning(f"Email notification export échoué: {str(e)}")

        return {"file_id": file_id, "download_url": download_url, "count": count}

    except Exception as e:
        logger.error(f"Erreur export PDF async: {str(e)}")
        raise
    finally:
        db.close()
