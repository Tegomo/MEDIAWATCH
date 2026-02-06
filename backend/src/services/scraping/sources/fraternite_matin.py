"""Scraper pour Fraternité Matin (ffraternitématin.ci) - Journal officiel ivoirien"""
import httpx
from datetime import datetime
from typing import Optional
from selectolax.parser import HTMLParser

from src.services.scraping.base import MediaScraper, ScrapedArticle


class FraterniteMatin(MediaScraper):
    """Scraper pour le site Fraternité Matin"""

    def __init__(self):
        super().__init__(
            source_name="Fraternité Matin",
            base_url="https://www.fratmat.info",
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

                    # Sélecteurs pour les liens d'articles
                    for node in tree.css("article a[href], .post-title a[href], h2 a[href], h3 a[href]"):
                        href = node.attributes.get("href", "")
                        if href and href.startswith(("http", "/")):
                            if href.startswith("/"):
                                href = f"{self.base_url}{href}"
                            if self.base_url in href and href not in urls:
                                urls.append(href)

                except Exception as e:
                    self.logger.warning(f"Erreur page {page}: {str(e)}")
                    break

        return urls

    async def parse_article(self, url: str) -> Optional[ScrapedArticle]:
        """Parse un article Fraternité Matin."""
        async with httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=30,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return None

        tree = HTMLParser(response.text)

        # Titre
        title_node = tree.css_first("h1.entry-title, h1.post-title, h1")
        if not title_node:
            return None
        title = title_node.text(strip=True)

        # Contenu
        content_node = tree.css_first(
            ".entry-content, .post-content, .article-content, article .content"
        )
        if not content_node:
            return None

        raw_content = content_node.html or ""
        cleaned_content = self.clean_text(content_node.text(strip=True))

        if len(cleaned_content) < 100:
            return None

        # Auteur
        author = None
        author_node = tree.css_first(".author-name, .post-author, .entry-author, [rel='author']")
        if author_node:
            author = author_node.text(strip=True)

        # Date
        published_at = datetime.utcnow()
        date_node = tree.css_first("time[datetime], .post-date, .entry-date, .published")
        if date_node:
            dt_attr = date_node.attributes.get("datetime", "")
            if dt_attr:
                parsed = self.extract_date(dt_attr)
                if parsed:
                    published_at = parsed
            else:
                parsed = self.extract_date(date_node.text(strip=True))
                if parsed:
                    published_at = parsed

        return ScrapedArticle(
            title=title,
            url=url,
            raw_content=raw_content,
            cleaned_content=cleaned_content,
            published_at=published_at,
            author=author,
        )
