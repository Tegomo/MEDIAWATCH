"""Filtrage de qualité et nettoyage basique du contenu scrapé."""
import re
import logging

logger = logging.getLogger(__name__)

# Mots/phrases indiquant une page non-article (erreur, login, suspension, etc.)
REJECT_PATTERNS = [
    r"(?i)account\s+suspended",
    r"(?i)compte\s+(désactivé|suspendu|supprimé)",
    r"(?i)page\s+not\s+found",
    r"(?i)404\s+(not\s+found|error|erreur)",
    r"(?i)403\s+forbidden",
    r"(?i)503\s+service\s+unavailable",
    r"(?i)access\s+denied",
    r"(?i)log\s*in.*forgot\s*(account|password)",
    r"(?i)connectez[- ]vous",
    r"(?i)sign\s+in\s+to\s+continue",
    r"(?i)veuillez\s+vous\s+connecter",
    r"(?i)this\s+page\s+isn'?t\s+available",
    r"(?i)contenu\s+indisponible",
    r"(?i)cette\s+page\s+n'est\s+pas\s+disponible",
    r"(?i)contactez\s+votre\s+hébergeur",
    r"(?i)cpanel",
    r"(?i)domain\s+(is\s+)?for\s+sale",
    r"(?i)parked\s+domain",
    r"(?i)under\s+construction",
    r"(?i)en\s+construction",
    r"(?i)coming\s+soon",
]

# Domaines à exclure des résultats de recherche web
BLOCKED_DOMAINS = [
    "facebook.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "linkedin.com",
    "youtube.com",
    "pinterest.com",
    "reddit.com",
]


def is_blocked_url(url: str) -> bool:
    """Vérifie si l'URL appartient à un domaine bloqué (réseaux sociaux, etc.)."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in BLOCKED_DOMAINS)


def is_valid_article(title: str, content: str) -> bool:
    """
    Vérifie si le contenu scrapé ressemble à un vrai article de presse.
    
    Returns:
        True si le contenu semble être un article valide, False sinon.
    """
    if not title or not content:
        return False

    # Contenu trop court = probablement pas un article
    if len(content) < 200:
        logger.debug(f"Rejeté (trop court: {len(content)} chars): {title[:50]}")
        return False

    # Vérifier les patterns de rejet dans le titre ET le contenu
    combined = f"{title}\n{content[:2000]}"
    for pattern in REJECT_PATTERNS:
        if re.search(pattern, combined):
            logger.info(f"Rejeté (pattern: {pattern[:30]}): {title[:50]}")
            return False

    # Ratio de liens markdown trop élevé = page de navigation, pas un article
    link_count = len(re.findall(r'\[.*?\]\(.*?\)', content))
    word_count = len(content.split())
    if word_count > 0 and link_count / word_count > 0.3:
        logger.info(f"Rejeté (trop de liens: {link_count}/{word_count}): {title[:50]}")
        return False

    # Ratio d'images markdown trop élevé = page de galerie/erreur
    image_count = len(re.findall(r'!\[.*?\]\(.*?\)', content))
    text_without_markdown = re.sub(r'!?\[.*?\]\(.*?\)', '', content).strip()
    if len(text_without_markdown) < 150:
        logger.info(f"Rejeté (peu de texte hors markdown: {len(text_without_markdown)} chars): {title[:50]}")
        return False

    return True


def clean_markdown(content: str) -> str:
    """
    Nettoyage basique du markdown brut pour le rendre plus lisible.
    Utilisé comme fallback quand l'IA n'est pas configurée.
    """
    if not content:
        return content

    # Supprimer les images markdown
    cleaned = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)

    # Supprimer les lignes de séparateurs excessifs (===, ---, ***)
    cleaned = re.sub(r'^[=\-\*]{3,}\s*$', '', cleaned, flags=re.MULTILINE)

    # Convertir les liens markdown en texte simple (garder le label)
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)

    # Supprimer les lignes vides multiples
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    # Supprimer les espaces en début/fin de lignes
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))

    # Supprimer les lignes qui ne contiennent que des caractères spéciaux
    cleaned = re.sub(r'^[^\w\s]{2,}\s*$', '', cleaned, flags=re.MULTILINE)

    # Nettoyer à nouveau les lignes vides multiples après suppression
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()
