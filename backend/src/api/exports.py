"""Endpoints API pour les exports CSV et PDF"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.services.exports.csv_exporter import CSVExporter
from src.services.exports.pdf_exporter import PDFExporter
from src.services.storage_service import StorageService
from src.lib.logger import logger

router = APIRouter(prefix="/exports", tags=["Exports"])

# T097 - Seuil pour export sync vs async
CSV_SYNC_THRESHOLD = 500


@router.post("/csv")
async def export_csv(
    sentiment: Optional[str] = Query(None),
    source_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    keyword_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Export CSV des mentions filtrées.
    Sync si <500 mentions, sinon retourne un fichier directement (streaming).
    """
    exporter = CSVExporter(db)
    csv_content, count = exporter.export(
        organization_id=current_user.organization_id,
        sentiment=sentiment,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        theme=theme,
        keyword_id=keyword_id,
    )

    filename = exporter.get_filename()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Count": str(count),
        },
    )


@router.post("/pdf")
async def export_pdf(
    sentiment: Optional[str] = Query(None),
    source_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    keyword_id: Optional[UUID] = Query(None),
    async_export: bool = Query(False, alias="async"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Export PDF des mentions filtrées.
    - sync (défaut): retourne le PDF directement
    - async=true: lance une tâche Celery et notifie par email
    """
    if async_export:
        from src.workers.tasks.exports import generate_pdf_export
        task = generate_pdf_export.delay(
            organization_id=str(current_user.organization_id),
            user_email=current_user.email,
            sentiment=sentiment,
            source_id=str(source_id) if source_id else None,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            search=search,
            theme=theme,
            keyword_id=str(keyword_id) if keyword_id else None,
        )
        return {
            "status": "processing",
            "task_id": task.id,
            "message": "Le rapport PDF est en cours de génération. Vous recevrez un email avec le lien de téléchargement.",
        }

    # Export sync
    exporter = PDFExporter(db)
    pdf_bytes, count = exporter.export(
        organization_id=current_user.organization_id,
        sentiment=sentiment,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        theme=theme,
        keyword_id=keyword_id,
    )

    filename = exporter.get_filename()

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Count": str(count),
        },
    )


@router.get("/download/{file_id}")
async def download_export(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Télécharge un fichier d'export généré de manière asynchrone."""
    storage = StorageService()
    content = storage.get_file(file_id)

    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier non trouvé ou expiré",
        )

    # Déterminer le content-type
    if file_id.endswith(".pdf"):
        media_type = "application/pdf"
    elif file_id.endswith(".csv"):
        media_type = "text/csv"
    else:
        media_type = "application/octet-stream"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{file_id.split("_", 1)[-1]}"'},
    )


@router.get("/status/{task_id}")
async def get_export_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """Vérifie le statut d'un export async."""
    from src.workers.celery_app import celery_app
    result = celery_app.AsyncResult(task_id)

    response = {"task_id": task_id, "status": result.status}

    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.result)

    return response
