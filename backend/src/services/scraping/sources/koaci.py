"""Scraper pour Koaci.com - Site d'actualités ivoirien (rendu JavaScript, nécessite Playwright)"""
from datetime import datetime
from typing import Optional

from src.config import settings
from src.services.scraping.base import MediaScraper, ScrapedArticle


class Koaci(MediaScraper):
    """Scraper pour le site Koaci.com utilisant Playwright pour le rendu JS"""

    def __init__(self):
        super().__init__(
            source_name="Koaci",
            base_url="https://www.koaci.com",
        )

    async def _get_browser_page(self):
        """Crée une page Playwright."""
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=settings.playwright_headless)
        context = await browser.new_context(
            user_agent=self.user_agent,
            locale="fr-FR",
        )
        page = await context.new_page()
        return pw, browser, page

    async def get_article_urls(self, max_pages: int = 3) -> list[str]:
        """Récupère les URLs des articles via Playwright (rendu JS)."""
        urls = []
        pw, browser, page = await self._get_browser_page()

        try:
            for page_num in range(1, max_pages + 1):
                try:
                    if page_num == 1:
                        await page.goto(
                            f"{self.base_url}/cote-divoire",
                            wait_until="domcontentloaded",
                            timeout=30000,
                        )
                    else:
                        await page.goto(
                            f"{self.base_url}/cote-divoire?page={page_num}",
                            wait_until="domcontentloaded",
                            timeout=30000,
                        )

                    # Attendre le chargement des articles
                    await page.wait_for_selector(
                        "article a, .article-link, h2 a, h3 a",
                        timeout=10000,
                    )

                    # Extraire les liens
                    links = await page.eval_on_selector_all(
                        "article a[href], .article-item a[href], h2 a[href], h3 a[href]",
                        "elements => elements.map(el => el.href)",
                    )

                    for href in links:
                        if (
                            href
                            and "koaci.com" in href
                            and href not in urls
                            and "/cote-divoire/" in href
                        ):
                            urls.append(href)

                except Exception as e:
                    self.logger.warning(f"Erreur page {page_num}: {str(e)}")
                    break

        finally:
            await browser.close()
            await pw.stop()

        return urls

    async def parse_article(self, url: str) -> Optional[ScrapedArticle]:
        """Parse un article Koaci via Playwright."""
        pw, browser, page = await self._get_browser_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Titre
            title_el = await page.query_selector("h1.article-title, h1.entry-title, h1")
            if not title_el:
                return None
            title = (await title_el.inner_text()).strip()

            # Contenu
            content_el = await page.query_selector(
                ".article-body, .article-content, .entry-content, .post-content"
            )
            if not content_el:
                return None

            raw_content = await content_el.inner_html()
            cleaned_content = self.clean_text(await content_el.inner_text())

            if len(cleaned_content) < 100:
                return None

            # Auteur
            author = None
            author_el = await page.query_selector(".article-author, .author, [rel='author']")
            if author_el:
                author = (await author_el.inner_text()).strip()

            # Date
            published_at = datetime.utcnow()
            date_el = await page.query_selector("time[datetime], .article-date, .date")
            if date_el:
                dt_attr = await date_el.get_attribute("datetime")
                if dt_attr:
                    parsed = self.extract_date(dt_attr)
                    if parsed:
                        published_at = parsed
                else:
                    date_text = (await date_el.inner_text()).strip()
                    parsed = self.extract_date(date_text)
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

        finally:
            await browser.close()
            await pw.stop()
