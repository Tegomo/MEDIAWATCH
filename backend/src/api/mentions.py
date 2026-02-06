"""Endpoints API pour les mentions"""
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.db.base import get_db
from src.api.auth import get_current_active_user
from src.models.user import User
from src.services.mention_service import MentionService
from src.schemas.mention import (
    MentionResponse,
    MentionDetailResponse,
    MentionListResponse,
    ArticleResponse,
    SourceResponse,
    KeywordBrief,
)

router = APIRouter(prefix="/mentions", tags=["Mentions"])


def _mention_to_response(mention) -> MentionResponse:
    """Convertit un objet Mention en MentionResponse."""
    article_resp = None
    if mention.article:
        source_resp = None
        if mention.article.source:
            source_resp = SourceResponse(
                id=mention.article.source.id,
                name=mention.article.source.name,
                url=mention.article.source.url,
                type=mention.article.source.type.value,
            )
        article_resp = ArticleResponse(
            id=mention.article.id,
            title=mention.article.title,
            url=mention.article.url,
            author=mention.article.author,
            published_at=mention.article.published_at,
            source=source_resp,
        )

    keyword_resp = None
    if mention.keyword:
        keyword_resp = KeywordBrief(
            id=mention.keyword.id,
            text=mention.keyword.text,
            category=mention.keyword.category.value,
        )

    return MentionResponse(
        id=mention.id,
        matched_text=mention.matched_text,
        match_context=mention.match_context,
        sentiment_score=mention.sentiment_score,
        sentiment_label=mention.sentiment_label.value,
        visibility_score=mention.visibility_score,
        theme=mention.theme.value if mention.theme else None,
        detected_at=mention.detected_at,
        keyword=keyword_resp,
        article=article_resp,
    )


@router.get("", response_model=MentionListResponse)
async def list_mentions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    keyword_id: Optional[UUID] = Query(None),
    sentiment: Optional[str] = Query(None),
    source_id: Optional[UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MentionListResponse:
    """
    Liste les mentions pour l'organisation de l'utilisateur.
    Supporte pagination, filtres par keyword, sentiment, source, dates, thème et recherche texte.
    """
    service = MentionService(db)
    mentions, total = service.list_mentions(
        organization_id=current_user.organization_id,
        limit=limit,
        offset=offset,
        keyword_id=keyword_id,
        sentiment=sentiment,
        source_id=source_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        theme=theme,
    )

    return MentionListResponse(
        mentions=[_mention_to_response(m) for m in mentions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats")
async def get_mention_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Statistiques rapides des mentions pour le dashboard."""
    service = MentionService(db)
    return service.get_stats(current_user.organization_id)


@router.get("/{mention_id}", response_model=MentionDetailResponse)
async def get_mention(
    mention_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MentionDetailResponse:
    """Récupère les détails complets d'une mention."""
    service = MentionService(db)
    mention = service.get_mention(mention_id, current_user.organization_id)

    if not mention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mention non trouvée",
        )

    base = _mention_to_response(mention)

    return MentionDetailResponse(
        **base.model_dump(),
        extracted_entities=mention.extracted_entities,
        alert_sent=mention.alert_sent,
        article_content=mention.article.cleaned_content if mention.article else None,
    )
