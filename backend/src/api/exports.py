"""Endpoints API pour les exports CSV et PDF"""
from typing import Optional
from uuid import UUID
from datetime import datetime
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.api.auth import get_current_active_user
from src.lib.logger import logger

router = APIRouter(prefix="/exports", tags=["Exports"])


def _get_mentions_for_export(db: SupabaseDB, org_id, **filters):
    """Récupère les mentions pour l'export."""
    keywords = db.select("keywords", columns="id", organization_id=f"eq.{org_id}")
    keyword_ids = [k["id"] for k in keywords]
    if not keyword_ids:
        return [], 0

    query_filters = {
        "keyword_id": f"in.({','.join(str(k) for k in keyword_ids)})",
        "order": "detected_at.desc",
    }
    if filters.get("keyword_id"):
        query_filters["keyword_id"] = f"eq.{filters['keyword_id']}"
    if filters.get("sentiment"):
        query_filters["sentiment_label"] = f"eq.{filters['sentiment'].upper()}"
    if filters.get("date_from"):
        query_filters["detected_at"] = f"gte.{filters['date_from'].isoformat()}"
    if filters.get("date_to"):
        query_filters["detected_at"] = f"lte.{filters['date_to'].isoformat()}"

    columns = "*,keyword:keywords(text,category),article:articles(title,url,author,published_at,source:sources(name))"
    mentions = db.select("mentions", columns=columns, **query_filters)
    return mentions, len(mentions)


@router.post("/csv")
async def export_csv(
    sentiment: Optional[str] = Query(None),
    source_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    keyword_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Export CSV des mentions filtrées."""
    mentions, count = _get_mentions_for_export(
        db, current_user["organization_id"],
        sentiment=sentiment, source_id=source_id,
        date_from=date_from, date_to=date_to,
        search=search, theme=theme, keyword_id=keyword_id,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Mot-clé", "Catégorie", "Source", "Article", "URL", "Sentiment", "Score", "Contexte"])

    for m in mentions:
        kw = m.get("keyword", {})
        article = m.get("article", {})
        source = article.get("source", {}) if article else {}
        writer.writerow([
            m.get("detected_at", ""),
            kw.get("text", ""),
            kw.get("category", ""),
            source.get("name", ""),
            article.get("title", ""),
            article.get("url", ""),
            m.get("sentiment_label", ""),
            m.get("sentiment_score", ""),
            m.get("match_context", "")[:200],
        ])

    csv_content = output.getvalue()
    filename = f"mediawatch_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

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
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Export PDF des mentions filtrées (simplifié - retourne JSON pour l'instant)."""
    mentions, count = _get_mentions_for_export(
        db, current_user["organization_id"],
        sentiment=sentiment, source_id=source_id,
        date_from=date_from, date_to=date_to,
        search=search, theme=theme, keyword_id=keyword_id,
    )

    return {
        "status": "success",
        "message": f"Export de {count} mentions",
        "count": count,
    }


@router.get("/download/{file_id}")
async def download_export(
    file_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Télécharge un fichier d'export généré de manière asynchrone."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Fichier non trouvé ou expiré",
    )


@router.get("/status/{task_id}")
async def get_export_status(
    task_id: str,
    current_user: dict = Depends(get_current_active_user),
):
    """Vérifie le statut d'un export async."""
    return {"task_id": task_id, "status": "not_available"}
