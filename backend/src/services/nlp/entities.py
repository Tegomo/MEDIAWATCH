"""Extraction d'entités nommées pour les articles en français"""
from dataclasses import dataclass, field
from typing import Optional

from src.lib.logger import logger


@dataclass
class ExtractedEntity:
    """Entité nommée extraite"""
    text: str
    label: str  # PER, ORG, LOC, MISC
    start: int
    end: int
    confidence: float = 0.0


@dataclass
class EntityExtractionResult:
    """Résultat complet d'extraction d'entités"""
    persons: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    misc: list[str] = field(default_factory=list)
    raw_entities: list[ExtractedEntity] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour stockage JSONB."""
        return {
            "persons": self.persons,
            "organizations": self.organizations,
            "locations": self.locations,
            "misc": self.misc,
        }


# Mapping des labels spaCy vers nos catégories
SPACY_LABEL_MAP = {
    "PER": "persons",
    "PERSON": "persons",
    "ORG": "organizations",
    "LOC": "locations",
    "GPE": "locations",
    "MISC": "misc",
    "NORP": "misc",
    "EVENT": "misc",
    "PRODUCT": "misc",
}


class EntityExtractor:
    """Extraction d'entités nommées utilisant spaCy (modèle français)"""

    def __init__(self):
        self._nlp = None

    def _get_nlp(self):
        """Lazy loading du modèle spaCy."""
        if self._nlp is None:
            from src.services.nlp.models.config import get_ner_model
            self._nlp = get_ner_model()
        return self._nlp

    def extract(self, text: str) -> EntityExtractionResult:
        """
        Extrait les entités nommées d'un texte.
        Retourne un EntityExtractionResult avec les entités classées.
        """
        nlp = self._get_nlp()

        if nlp is None:
            logger.warning("Modèle NER non disponible, retour vide")
            return EntityExtractionResult()

        try:
            # Tronquer si trop long (spaCy a une limite)
            max_chars = 100000
            truncated = text[:max_chars]

            doc = nlp(truncated)

            result = EntityExtractionResult()
            seen = set()

            for ent in doc.ents:
                entity = ExtractedEntity(
                    text=ent.text.strip(),
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                )
                result.raw_entities.append(entity)

                # Classifier l'entité
                category = SPACY_LABEL_MAP.get(ent.label_)
                if category and ent.text.strip():
                    clean_text = ent.text.strip()
                    # Dédupliquer (insensible à la casse)
                    key = (category, clean_text.lower())
                    if key not in seen:
                        seen.add(key)
                        getattr(result, category).append(clean_text)

            return result

        except Exception as e:
            logger.error(f"Erreur extraction entités: {str(e)}")
            return EntityExtractionResult()

    def extract_from_context(
        self, full_text: str, keyword: str, window: int = 1000
    ) -> EntityExtractionResult:
        """
        Extrait les entités du contexte autour d'un mot-clé.
        Plus rapide que l'extraction sur le texte complet.
        """
        text_lower = full_text.lower()
        keyword_lower = keyword.lower()

        idx = text_lower.find(keyword_lower)
        if idx == -1:
            # Fallback: analyser les premiers 2000 caractères
            return self.extract(full_text[:2000])

        start = max(0, idx - window)
        end = min(len(full_text), idx + len(keyword) + window)
        context = full_text[start:end]

        return self.extract(context)
