"""Service Jina AI Reader pour le scraping intelligent de contenu web"""
import re
import httpx
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse
import logging

from src.config import settings


logger = logging.getLogger(__name__)


class JinaReaderService:
    """
    Service pour utiliser Jina AI Reader API.
    
    Jina AI Reader convertit n'importe quelle URL en markdown propre,
    en gérant automatiquement le JavaScript, les paywall, et le nettoyage.
    
    API: https://r.jina.ai/{url}
    Docs: https://jina.ai/reader
    """

    BASE_URL = "https://r.jina.ai"
    SEARCH_URL = "https://s.jina.ai"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le service Jina Reader.
        
        Args:
            api_key: Clé API Jina (optionnel pour usage gratuit limité)
        """
        self.api_key = api_key
        self.timeout = 90
        
    async def read_url(self, url: str) -> Optional[dict]:
        """
        Lit une URL et retourne le contenu en markdown propre.
        
        Args:
            url: URL de l'article à scraper
            
        Returns:
            dict avec:
                - title: Titre de l'article
                - content: Contenu en markdown
                - url: URL source
                - published_date: Date de publication (si disponible)
                - author: Auteur (si disponible)
                - description: Meta description
                
        Raises:
            httpx.HTTPError: Si la requête échoue
        """
        headers = {
            "Accept": "application/json",
            "X-Return-Format": "markdown",
        }
        
        # Ajouter la clé API si disponible
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        jina_url = f"{self.BASE_URL}/{url}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(jina_url, headers=headers)
                response.raise_for_status()
                
                raw = response.json()
                
                # Jina AI retourne {code, status, data: {title, content, ...}, meta}
                data = raw.get("data", raw)
                
                return {
                    "title": data.get("title", ""),
                    "content": data.get("content", ""),
                    "url": data.get("url", url),
                    "published_date": data.get("publishedTime"),
                    "author": data.get("author"),
                    "description": data.get("description", ""),
                    "images": data.get("images", []),
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP Jina AI pour {url}: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Erreur requête Jina AI pour {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erreur inattendue Jina AI pour {url}: {str(e)}")
            raise
    
    async def read_url_simple(self, url: str) -> Optional[str]:
        """
        Version simplifiée qui retourne uniquement le contenu markdown.
        
        Args:
            url: URL à scraper
            
        Returns:
            Contenu en markdown ou None si erreur
        """
        try:
            data = await self.read_url(url)
            return data.get("content") if data else None
        except Exception as e:
            logger.warning(f"Impossible de lire {url} avec Jina AI: {str(e)}")
            return None
    
    async def extract_article_links(self, listing_url: str, source_domain: str) -> list[str]:
        """
        Lit une page de listing avec Jina et extrait les liens d'articles.
        
        Args:
            listing_url: URL de la page de listing (ex: https://news.abidjan.net/articles)
            source_domain: Domaine de la source pour filtrer les liens (ex: abidjan.net)
            
        Returns:
            Liste d'URLs d'articles uniques
        """
        try:
            data = await self.read_url(listing_url)
            if not data:
                return []
            
            content = data.get("content", "")
            
            # Extraire toutes les URLs (markdown et brutes)
            all_urls = re.findall(r'\((https?://[^)]+)\)', content)
            
            urls = []
            for url in all_urls:
                # Garder uniquement les liens du même domaine
                if source_domain not in url:
                    continue
                # Filtrer : un article a un path long avec un slug (au moins 3 segments)
                parsed = urlparse(url)
                path_parts = [p for p in parsed.path.split("/") if p]
                if len(path_parts) < 2:
                    continue
                # Exclure les images, CSS, JS
                if any(url.endswith(ext) for ext in (".png", ".jpg", ".gif", ".css", ".js", ".ico", ".svg")):
                    continue
                # Éviter les doublons
                if url not in urls:
                    urls.append(url)
            
            logger.info(f"Jina: {len(urls)} liens d'articles trouvés sur {listing_url}")
            return urls
            
        except Exception as e:
            logger.error(f"Erreur extraction liens depuis {listing_url}: {str(e)}")
            return []

    async def search_web(self, query: str, num_results: int = 5) -> list[dict]:
        """
        Recherche sur internet via Jina Search API (s.jina.ai).
        
        Args:
            query: Terme de recherche (ex: "McCANN Côte d'Ivoire")
            num_results: Nombre max de résultats (défaut: 5)
            
        Returns:
            Liste de dicts avec: title, url, content, description
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Respond-With": "no-content",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {"q": query, "num": num_results}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.SEARCH_URL}/",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                
                raw = response.json()
                results = raw.get("data", [])
                
                if not isinstance(results, list):
                    logger.warning(f"Jina Search: réponse inattendue pour '{query}'")
                    return []
                
                parsed = []
                for item in results:
                    url = item.get("url", "")
                    if not url:
                        continue
                    parsed.append({
                        "title": item.get("title", ""),
                        "url": url,
                        "description": item.get("description", ""),
                        "content": item.get("content", ""),
                    })
                
                logger.info(f"Jina Search: {len(parsed)} résultats pour '{query}'")
                return parsed
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Erreur HTTP Jina Search pour '{query}': {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Erreur Jina Search pour '{query}': {str(e)}")
            return []

    def parse_published_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse la date de publication retournée par Jina AI.
        
        Args:
            date_str: Date au format ISO 8601
            
        Returns:
            datetime object ou None
        """
        if not date_str:
            return None
            
        try:
            # Jina AI retourne généralement ISO 8601
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning(f"Impossible de parser la date: {date_str}")
            return None


def get_jina_reader() -> JinaReaderService:
    """Factory function pour obtenir une instance de JinaReaderService."""
    api_key = getattr(settings, "jina_api_key", None)
    return JinaReaderService(api_key=api_key)
