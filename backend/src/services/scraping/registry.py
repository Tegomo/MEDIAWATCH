"""Registry des scrapers disponibles - mappe les noms de sources aux classes de scrapers"""
from typing import Type

from src.services.scraping.base import MediaScraper
from src.services.scraping.sources.fraternite_matin import FraterniteMatin
from src.services.scraping.sources.abidjan_net import AbidjanNet
from src.services.scraping.sources.koaci import Koaci
from src.services.scraping.sources.linfodrome import Linfodrome
from src.services.scraping.sources.aip_rss import AipRss
from src.lib.logger import logger


# Mapping nom de classe scraper -> classe
# Supporte à la fois le format snake_case (BD) et PascalCase
SCRAPER_REGISTRY: dict[str, Type[MediaScraper]] = {
    "fraternite_matin": FraterniteMatin,
    "abidjan_net": AbidjanNet,
    "koaci": Koaci,
    "linfodrome": Linfodrome,
    "aip_rss": AipRss,
    "FraterniteMatin": FraterniteMatin,
    "AbidjanNet": AbidjanNet,
    "Koaci": Koaci,
    "Linfodrome": Linfodrome,
}


def get_scraper(scraper_class_name: str) -> MediaScraper | None:
    """
    Retourne une instance du scraper correspondant au nom de classe.
    Le champ `scraper_class` de la table `sources` doit correspondre
    à une clé du SCRAPER_REGISTRY.
    """
    cls = SCRAPER_REGISTRY.get(scraper_class_name)
    if cls is None:
        logger.error(f"Scraper inconnu: {scraper_class_name}")
        return None
    return cls()


def list_scrapers() -> list[str]:
    """Retourne la liste des noms de scrapers disponibles."""
    return list(SCRAPER_REGISTRY.keys())
