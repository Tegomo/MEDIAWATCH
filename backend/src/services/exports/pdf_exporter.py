"""Export des mentions au format PDF via WeasyPrint"""
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from src.services.mention_service import MentionService
from src.lib.logger import logger


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

SENTIMENT_DISPLAY = {
    "POSITIVE": "Positif",
    "NEGATIVE": "Négatif",
    "NEUTRAL": "Neutre",
}

THEME_DISPLAY = {
    "POLITICS": "Politique",
    "ECONOMY": "Économie",
    "SPORT": "Sport",
    "SOCIETY": "Société",
    "TECHNOLOGY": "Technologie",
    "CULTURE": "Culture",
    "OTHER": "Autre",
}


class PDFExporter:
    """Génère un rapport PDF à partir des mentions filtrées"""

    def __init__(self, db: Session):
        self.db = db
        self.env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

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
        max_rows: int = 1000,
    ) -> tuple[bytes, int]:
        """
        Exporte les mentions filtrées en PDF.
        Retourne (contenu_pdf_bytes, nombre_de_mentions).
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

        # Préparer les données pour le template
        mention_rows = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        for m in mentions:
            label = m.sentiment_label.value if m.sentiment_label else "NEUTRAL"
            if label == "POSITIVE":
                positive_count += 1
            elif label == "NEGATIVE":
                negative_count += 1
            else:
                neutral_count += 1

            mention_rows.append({
                "detected_at": m.detected_at.strftime("%d/%m/%Y %H:%M") if m.detected_at else "",
                "keyword_text": m.keyword.text if m.keyword else "",
                "article_title": (m.article.title[:80] + "...") if m.article and len(m.article.title) > 80 else (m.article.title if m.article else ""),
                "source_name": m.article.source.name if m.article and m.article.source else "",
                "sentiment_label": label.lower(),
                "sentiment_label_display": SENTIMENT_DISPLAY.get(label, label),
                "sentiment_score": f"{m.sentiment_score:.2f}" if m.sentiment_score is not None else "",
                "theme": THEME_DISPLAY.get(m.theme.value, m.theme.value) if m.theme else "",
            })

        # Construire la description des filtres
        filters_parts = []
        if sentiment:
            filters_parts.append(f"Sentiment: {SENTIMENT_DISPLAY.get(sentiment, sentiment)}")
        if theme:
            filters_parts.append(f"Thème: {THEME_DISPLAY.get(theme, theme)}")
        if date_from:
            filters_parts.append(f"Du: {date_from.strftime('%d/%m/%Y')}")
        if date_to:
            filters_parts.append(f"Au: {date_to.strftime('%d/%m/%Y')}")
        if search:
            filters_parts.append(f"Recherche: \"{search}\"")
        filters_description = " | ".join(filters_parts) if filters_parts else None

        # Rendre le template HTML
        template = self.env.get_template("report.html")
        html_content = template.render(
            generated_at=datetime.utcnow().strftime("%d/%m/%Y à %H:%M UTC"),
            total_mentions=len(mentions),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            mentions=mention_rows,
            filters_description=filters_description,
        )

        # Convertir en PDF avec WeasyPrint
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
        except ImportError:
            logger.warning("WeasyPrint non installé, fallback HTML-to-bytes")
            pdf_bytes = html_content.encode("utf-8")

        logger.info(f"PDF export: {len(mentions)} mentions, {len(pdf_bytes)} bytes")
        return pdf_bytes, len(mentions)

    def get_filename(self) -> str:
        """Génère un nom de fichier avec timestamp."""
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"mediawatch_rapport_{ts}.pdf"
