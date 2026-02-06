"""Scraper RSS pour l'AIP (Agence Ivoirienne de Presse)"""
import httpx
from datetime import datetime
from typing import Optional
from xml.etree import ElementTree

from src.services.scraping.base import MediaScraper, ScrapedArticle


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
        """Parse un article AIP depuis son URL."""
        try:
            from selectolax.parser import HTMLParser
        except ImportError:
            self.logger.error("selectolax non installé")
            return None

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

        if len(cleaned_content) < 50:
            return None

        # Auteur
        author = "AIP"
        author_node = tree.css_first(".author-name, .post-author, [rel='author']")
        if author_node:
            author = author_node.text(strip=True)

        # Date
        published_at = datetime.utcnow()
        date_node = tree.css_first("time[datetime], .post-date, .entry-date")
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
