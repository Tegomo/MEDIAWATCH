"""Classe abstraite pour les scrapers de médias ivoiriens"""
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.config import settings
from src.lib.logger import logger


@dataclass
class ScrapedArticle:
    """Article scrapé depuis une source média"""
    title: str
    url: str
    raw_content: str
    cleaned_content: str
    published_at: datetime
    author: Optional[str] = None
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(
                self.cleaned_content.encode("utf-8")
            ).hexdigest()


class MediaScraper(ABC):
    """Classe abstraite pour tous les scrapers de sources médias"""

    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.user_agent = settings.scraping_user_agent
        self.rate_limit = settings.scraping_rate_limit
        self.logger = logger.bind(scraper=source_name)

    @abstractmethod
    async def get_article_urls(self, max_pages: int = 3) -> list[str]:
        """
        Récupère les URLs des articles récents depuis la page d'accueil
        ou les pages de listing.
        """
        ...

    @abstractmethod
    async def parse_article(self, url: str) -> Optional[ScrapedArticle]:
        """
        Parse un article individuel et retourne un ScrapedArticle.
        Retourne None si l'article ne peut pas être parsé.
        """
        ...

    async def scrape(self, max_pages: int = 3) -> list[ScrapedArticle]:
        """
        Pipeline principal de scraping:
        1. Récupère les URLs des articles
        2. Parse chaque article
        3. Retourne la liste des articles scrapés
        """
        self.logger.info(f"Début scraping {self.source_name}")
        articles = []

        try:
            urls = await self.get_article_urls(max_pages=max_pages)
            self.logger.info(f"{len(urls)} URLs trouvées pour {self.source_name}")

            for url in urls:
                try:
                    article = await self.parse_article(url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(
                        f"Erreur parsing article {url}: {str(e)}"
                    )
                    continue

        except Exception as e:
            self.logger.error(f"Erreur scraping {self.source_name}: {str(e)}")
            raise

        self.logger.info(
            f"Scraping {self.source_name} terminé: {len(articles)} articles"
        )
        return articles

    def clean_text(self, text: str) -> str:
        """Nettoie le texte brut d'un article."""
        import re

        # Supprimer les balises HTML restantes
        text = re.sub(r"<[^>]+>", "", text)
        # Normaliser les espaces
        text = re.sub(r"\s+", " ", text)
        # Supprimer les espaces en début/fin
        text = text.strip()
        return text

    def extract_date(self, date_str: str, formats: list[str] | None = None) -> Optional[datetime]:
        """Parse une date depuis différents formats courants."""
        if formats is None:
            formats = [
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%d %B %Y",
                "%d %b %Y",
                "%A %d %B %Y",
            ]

        import locale
        # Essayer avec locale française
        try:
            locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        except locale.Error:
            pass

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        self.logger.warning(f"Impossible de parser la date: {date_str}")
        return None
