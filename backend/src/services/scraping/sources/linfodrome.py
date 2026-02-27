"""Scraper pour Linfodrome.com - Site d'actualités ivoirien"""
import httpx
from datetime import datetime
from typing import Optional
from selectolax.parser import HTMLParser

from src.services.scraping.base import MediaScraper, ScrapedArticle
from src.services.scraping.jina_reader import get_jina_reader


class Linfodrome(MediaScraper):
    """Scraper pour le site Linfodrome.com"""

    def __init__(self):
        super().__init__(
            source_name="Linfodrome",
            base_url="https://www.linfodrome.com",
        )

    async def get_article_urls(self, max_pages: int = 3) -> list[str]:
        """Récupère les URLs des articles depuis les pages de listing."""
        urls = []
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=30,
            follow_redirects=True,
        ) as client:
            for page in range(1, max_pages + 1):
                try:
                    if page == 1:
                        response = await client.get(self.base_url)
                    else:
                        response = await client.get(f"{self.base_url}/page/{page}")

                    if response.status_code != 200:
                        break

                    tree = HTMLParser(response.text)

                    for node in tree.css("article a[href], .post-title a[href], h2 a[href], h3 a[href]"):
                        href = node.attributes.get("href", "")
                        if href and href.startswith(("http", "/")):
                            if href.startswith("/"):
                                href = f"{self.base_url}{href}"
                            if "linfodrome.com" in href and href not in urls:
                                urls.append(href)

                except Exception as e:
                    self.logger.warning(f"Erreur page {page}: {str(e)}")
                    break

        return urls

    async def parse_article(self, url: str) -> Optional[ScrapedArticle]:
        """Parse un article Linfodrome avec Jina AI Reader."""
        jina = get_jina_reader()
        
        try:
            data = await jina.read_url(url)
            if not data:
                return None
            
            title = data.get("title", "")
            content = data.get("content", "")
            
            if not title or len(content) < 100:
                return None
            
            # Jina AI retourne déjà du markdown propre
            cleaned_content = content
            
            # Date de publication
            published_at = datetime.utcnow()
            if data.get("published_date"):
                parsed_date = jina.parse_published_date(data["published_date"])
                if parsed_date:
                    published_at = parsed_date
            
            # Auteur
            author = data.get("author")
            
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
