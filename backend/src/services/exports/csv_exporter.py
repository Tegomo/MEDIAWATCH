"""Export des mentions au format CSV"""
import csv
import io
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.services.mention_service import MentionService
from src.lib.logger import logger


class CSVExporter:
    """Génère un fichier CSV à partir des mentions filtrées"""

    HEADERS = [
        "Date détection",
        "Mot-clé",
        "Catégorie",
        "Titre article",
        "Source",
        "Auteur",
        "Date publication",
        "Sentiment",
        "Score sentiment",
        "Visibilité",
        "Thème",
        "Contexte",
        "URL article",
    ]

    def __init__(self, db: Session):
        self.db = db

    def export(
        self,
        organization_id: UUID,
        sentiment: Optional[str] = None,
        source_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        theme: Optional[str] = None,
        keyword_id: Optional[UUID] = None,
        max_rows: int = 5000,
    ) -> tuple[str, int]:
        """
        Exporte les mentions filtrées en CSV.
        Retourne (contenu_csv, nombre_de_lignes).
        """
        service = MentionService(self.db)
        mentions, total = service.list_mentions(
            organization_id=organization_id,
            limit=max_rows,
            offset=0,
            keyword_id=keyword_id,
            sentiment=sentiment,
            source_id=source_id,
            date_from=date_from,
            date_to=date_to,
            search=search,
            theme=theme,
        )

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(self.HEADERS)

        for mention in mentions:
            article = mention.article
            keyword = mention.keyword
            source = article.source if article else None

            writer.writerow([
                mention.detected_at.strftime("%Y-%m-%d %H:%M") if mention.detected_at else "",
                keyword.text if keyword else "",
                keyword.category.value if keyword and keyword.category else "",
                article.title if article else "",
                source.name if source else "",
                article.author or "" if article else "",
                article.published_at.strftime("%Y-%m-%d %H:%M") if article and article.published_at else "",
                mention.sentiment_label.value if mention.sentiment_label else "",
                f"{mention.sentiment_score:.3f}" if mention.sentiment_score is not None else "",
                f"{mention.visibility_score:.2f}" if mention.visibility_score is not None else "",
                mention.theme.value if mention.theme else "",
                mention.match_context or "",
                article.url if article else "",
            ])

        content = output.getvalue()
        output.close()

        logger.info(f"CSV export: {len(mentions)} mentions exportées")
        return content, len(mentions)

    def get_filename(self) -> str:
        """Génère un nom de fichier avec timestamp."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"mediawatch_mentions_{ts}.csv"
