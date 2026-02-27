"""Service OpenRouter AI pour le résumé et nettoyage d'articles"""
import httpx
import logging
from typing import Optional

from src.config import settings

logger = logging.getLogger(__name__)

ARTICLE_CLEANUP_PROMPT = """Tu es un assistant spécialisé dans le traitement d'articles de presse africains, en particulier ivoiriens.

À partir du contenu brut ci-dessous (souvent pollué par des menus, publicités, liens de navigation, etc.), tu dois produire une version propre et structurée.

**IMPORTANT — Détection de contenu invalide :**
Si le contenu n'est PAS un vrai article de presse (par exemple : page d'erreur, page de connexion, compte suspendu, page de maintenance, galerie d'images sans texte, page d'accueil de site, profil de réseau social, page produit e-commerce), réponds UNIQUEMENT par le mot :
REJET

**Instructions (si c'est un vrai article) :**
1. **Supprime** tout le bruit : menus de navigation, publicités, liens "lire aussi", footers, mentions de cookies, boutons de partage, etc.
2. **Conserve** uniquement le contenu éditorial de l'article (titre, chapeau, corps).
3. **Reformate** le texte en paragraphes clairs et lisibles.
4. **Produis un résumé** de 3 à 5 phrases en début de réponse, précédé de "**Résumé :**".
5. **Conserve les citations** exactes entre guillemets.
6. **Conserve les noms propres** (personnes, lieux, organisations) tels quels.
7. Réponds uniquement avec le contenu traité, sans commentaire ni explication.

**Format de sortie :**
**Résumé :** [3-5 phrases résumant l'essentiel]

---

[Contenu nettoyé et reformaté de l'article]
"""

REJET_MARKER = "REJET"


class OpenRouterService:
    """Service pour appeler l'API OpenRouter afin de résumer/nettoyer des articles."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "openrouter_api_key", None)
        self.model = model or getattr(settings, "openrouter_model", "google/gemini-2.0-flash-001")
        self.timeout = 120

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def cleanup_article(self, raw_content: str, title: str = "") -> Optional[str]:
        """
        Envoie le contenu brut d'un article à OpenRouter pour nettoyage et résumé.

        Args:
            raw_content: Contenu brut de l'article (markdown/texte)
            title: Titre de l'article (contexte supplémentaire)

        Returns:
            Contenu nettoyé et résumé, ou None en cas d'erreur
        """
        if not self.is_configured:
            logger.debug("OpenRouter non configuré, skip nettoyage IA")
            return None

        # Tronquer le contenu si trop long (économie de tokens)
        max_chars = 15000
        content = raw_content[:max_chars]
        if len(raw_content) > max_chars:
            content += "\n\n[... contenu tronqué ...]"

        user_message = f"**Titre :** {title}\n\n**Contenu brut :**\n{content}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mediawatch.ci",
            "X-Title": "MediaWatch CI",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ARTICLE_CLEANUP_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.API_URL, json=payload, headers=headers)
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    logger.warning("OpenRouter: réponse vide (pas de choices)")
                    return None

                result = choices[0].get("message", {}).get("content", "")
                if not result.strip():
                    logger.warning("OpenRouter: contenu de réponse vide")
                    return None

                cleaned = result.strip()

                # L'IA a détecté que ce n'est pas un article
                if cleaned.upper().startswith(REJET_MARKER):
                    logger.info(f"OpenRouter: contenu rejeté par l'IA (pas un article)")
                    return REJET_MARKER

                logger.info(f"OpenRouter: article nettoyé ({len(cleaned)} chars) — modèle {self.model}")
                return cleaned

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter HTTP {e.response.status_code}: {e.response.text[:200]}")
            return None
        except httpx.RequestError as e:
            logger.error(f"OpenRouter erreur réseau: {str(e)[:200]}")
            return None
        except Exception as e:
            logger.error(f"OpenRouter erreur inattendue: {str(e)[:200]}")
            return None


def get_openrouter_service() -> OpenRouterService:
    """Factory function pour obtenir une instance d'OpenRouterService."""
    return OpenRouterService()
