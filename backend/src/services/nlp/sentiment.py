"""Analyse de sentiment pour les articles en français"""
from dataclasses import dataclass
from typing import Optional

from src.lib.logger import logger


@dataclass
class SentimentResult:
    """Résultat d'analyse de sentiment"""
    label: str  # "positive", "negative", "neutral"
    score: float  # 0.0 à 1.0
    raw_label: str  # Label brut du modèle
    raw_score: float  # Score brut du modèle


class SentimentAnalyzer:
    """Analyse de sentiment utilisant CamemBERT (tblard/tf-allocine)"""

    # Mapping des labels du modèle tf-allocine vers nos labels
    LABEL_MAP = {
        "POSITIVE": "positive",
        "NEGATIVE": "negative",
    }

    def __init__(self):
        self._pipeline = None

    def _get_pipeline(self):
        """Lazy loading du pipeline de sentiment."""
        if self._pipeline is None:
            from src.services.nlp.models.config import get_sentiment_model
            self._pipeline = get_sentiment_model()
        return self._pipeline

    def analyze(self, text: str) -> SentimentResult:
        """
        Analyse le sentiment d'un texte.
        Retourne un SentimentResult avec label normalisé et score.
        """
        pipeline = self._get_pipeline()

        if pipeline is None:
            logger.warning("Pipeline sentiment non disponible, retour neutre")
            return SentimentResult(
                label="neutral", score=0.0, raw_label="UNAVAILABLE", raw_score=0.0
            )

        try:
            # Tronquer le texte si trop long (max 512 tokens)
            truncated = text[:2000]

            result = pipeline(truncated)[0]
            raw_label = result["label"]
            raw_score = result["score"]

            # Mapper le label
            label = self.LABEL_MAP.get(raw_label, "neutral")

            # Normaliser le score:
            # - positif: score positif (0 à 1)
            # - négatif: score négatif (-1 à 0)
            # - neutre: score proche de 0
            if label == "positive":
                score = raw_score
            elif label == "negative":
                score = -raw_score
            else:
                score = 0.0

            # Si le score est faible (< 0.6), considérer comme neutre
            if abs(raw_score) < 0.6:
                label = "neutral"
                score = 0.0

            return SentimentResult(
                label=label,
                score=score,
                raw_label=raw_label,
                raw_score=raw_score,
            )

        except Exception as e:
            logger.error(f"Erreur analyse sentiment: {str(e)}")
            return SentimentResult(
                label="neutral", score=0.0, raw_label="ERROR", raw_score=0.0
            )

    def analyze_context(self, full_text: str, keyword: str, window: int = 500) -> SentimentResult:
        """
        Analyse le sentiment du contexte autour d'un mot-clé dans le texte.
        Plus précis que l'analyse du texte complet.
        """
        text_lower = full_text.lower()
        keyword_lower = keyword.lower()

        idx = text_lower.find(keyword_lower)
        if idx == -1:
            return self.analyze(full_text)

        start = max(0, idx - window)
        end = min(len(full_text), idx + len(keyword) + window)
        context = full_text[start:end]

        return self.analyze(context)
