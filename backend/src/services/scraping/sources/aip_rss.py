"""Scraper RSS pour l'AIP (Agence Ivoirienne de Presse)"""
import httpx
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree

from src.services.scraping.base import MediaScraper, ScrapedArticle
from src.services.scraping.jina_reader import get_jina_reader


class AipRss(MediaScraper):
    """Scraper RSS pour l'Agence Ivoirienne de Presse"""

    def __init__(self):
        super().__init__(
            source_name="AIP",
            base_url="https://www.aip.ci",
        )
        self.feed_urls = [
            "https://www.aip.ci/feed/",
            "https://www.aip.ci/feed/rss/",
        ]

    async def get_article_urls(self, max_pages: int = 3) -> list[str]:
        """Récupère les URLs des articles depuis le flux RSS."""
        urls = []
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=30,
            follow_redirects=True,
        ) as client:
            for feed_url in self.feed_urls:
                try:
                    response = await client.get(feed_url)
                    if response.status_code != 200:
                        continue

                    root = ElementTree.fromstring(response.text)

                    # RSS 2.0 format
                    for item in root.findall(".//item"):
                        link = item.find("link")
                        if link is not None and link.text:
                            url = link.text.strip()
                            if url and url not in urls:
                                urls.append(url)

                    # Atom format fallback
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall(".//atom:entry", ns):
                        link = entry.find("atom:link[@rel='alternate']", ns)
                        if link is None:
                            link = entry.find("atom:link", ns)
                        if link is not None:
                            href = link.get("href", "")
                            if href and href not in urls:
                                urls.append(href)

                    if urls:
                        break  # Un flux a fonctionné, pas besoin d'essayer les autres

                except Exception as e:
                    self.logger.warning(f"Erreur flux RSS {feed_url}: {str(e)}")
                    continue

        return urls

    async def parse_article(self, url: str) -> Optional[ScrapedArticle]:
        """Parse un article AIP avec Jina AI Reader."""
        jina = get_jina_reader()
        
        try:
            data = await jina.read_url(url)
            if not data:
                return None
            
            title = data.get("title", "")
            content = data.get("content", "")
            
            if not title or len(content) < 50:
                return None
            
            # Jina AI retourne déjà du markdown propre
            cleaned_content = content
            
            # Date de publication
            published_at = datetime.utcnow()
            if data.get("published_date"):
                parsed_date = jina.parse_published_date(data["published_date"])
                if parsed_date:
                    published_at = parsed_date
            
            # Auteur (AIP par défaut)
            author = data.get("author") or "AIP"
            
            return ScrapedArticle(
                title=title,
                url=url,
                raw_content=content,  # Markdown brut
                cleaned_content=cleaned_content,
                published_at=published_at,
                author=author,
                metadata={
                    "description": data.get("description", ""),
                    "images": data.get("images", []),
                }
            )
            
        except Exception as e:
            self.logger.error(f"Erreur Jina AI pour {url}: {str(e)}")
            return None
