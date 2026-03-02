"""Endpoints API pour les analytics et tendances"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from src.db.base import get_db
from src.db.supabase_client import SupabaseDB
from src.api.auth import get_current_active_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/trends")
async def get_trends(
    days: int = Query(7, ge=1, le=90),
    keyword_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Tendances des mentions sur une période donnée."""
    org_id = current_user["organization_id"]
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    keywords = db.select("keywords", columns="id", organization_id=f"eq.{org_id}")
    keyword_ids = [k["id"] for k in keywords]
    if not keyword_ids:
        return {"trends": [], "period_days": days}

    filters = {
        "keyword_id": f"in.({','.join(str(k) for k in keyword_ids)})",
        "detected_at": f"gte.{since}",
        "order": "detected_at.asc",
    }
    if keyword_id:
        filters["keyword_id"] = f"eq.{keyword_id}"

    mentions = db.select("mentions", columns="detected_at,sentiment_label", **filters)

    # Grouper par jour
    daily = {}
    for m in mentions:
        day = m["detected_at"][:10]
        if day not in daily:
            daily[day] = {"date": day, "total": 0, "positive": 0, "negative": 0, "neutral": 0}
        daily[day]["total"] += 1
        label = m.get("sentiment_label", "NEUTRAL").lower()
        if label in daily[day]:
            daily[day][label] += 1

    return {"trends": list(daily.values()), "period_days": days}


@router.get("/sources")
async def get_source_distribution(
    days: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Répartition des mentions par source média."""
    org_id = current_user["organization_id"]
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()

    keywords = db.select("keywords", columns="id", organization_id=f"eq.{org_id}")
    keyword_ids = [k["id"] for k in keywords]
    if not keyword_ids:
        return {"sources": []}

    mentions = db.select(
        "mentions",
        columns="sentiment_score,article:articles(source:sources(id,name))",
        keyword_id=f"in.({','.join(str(k) for k in keyword_ids)})",
        detected_at=f"gte.{since}",
    )

    source_stats = {}
    for m in mentions:
        article = m.get("article", {})
        source = article.get("source", {}) if article else {}
        if not source:
            continue
        sid = source["id"]
        if sid not in source_stats:
            source_stats[sid] = {"id": sid, "name": source["name"], "count": 0, "sentiment_sum": 0}
        source_stats[sid]["count"] += 1
        source_stats[sid]["sentiment_sum"] += m.get("sentiment_score", 0)

    result = []
    for s in source_stats.values():
        result.append({
            "source_id": s["id"],
            "source_name": s["name"],
            "mention_count": s["count"],
            "avg_sentiment": round(s["sentiment_sum"] / s["count"], 3) if s["count"] else 0,
        })

    return {"sources": sorted(result, key=lambda x: x["mention_count"], reverse=True)}


@router.get("/keywords")
async def get_top_keywords(
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
    db: SupabaseDB = Depends(get_db),
):
    """Top mots-clés les plus mentionnés."""
    org_id = current_user["organization_id"]
    keywords = db.select(
        "keywords",
        columns="id,text,category,total_mentions_count",
        organization_id=f"eq.{org_id}",
        order="total_mentions_count.desc",
        limit=str(limit),
    )
    return {"keywords": keywords}
