"""Configuration et chargement des modèles NLP"""
from functools import lru_cache
from typing import Optional

from src.config import settings
from src.lib.logger import logger


@lru_cache(maxsize=1)
def get_sentiment_model():
    """
    Charge le modèle CamemBERT pour l'analyse de sentiment.
    Utilise un pipeline Hugging Face pré-entraîné pour le français.
    Le modèle est mis en cache après le premier chargement.
    """
    try:
        from transformers import pipeline

        model_name = "tblard/tf-allocine"  # CamemBERT fine-tuné sentiment FR
        logger.info(f"Chargement modèle sentiment: {model_name}")

        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            max_length=512,
            truncation=True,
        )

        logger.info("Modèle sentiment chargé avec succès")
        return sentiment_pipeline

    except Exception as e:
        logger.error(f"Erreur chargement modèle sentiment: {str(e)}")
        return None


@lru_cache(maxsize=1)
def get_ner_model():
    """
    Charge le modèle spaCy pour l'extraction d'entités nommées en français.
    Fallback sur le modèle moyen si le grand n'est pas disponible.
    """
    try:
        import spacy

        model_name = settings.spacy_model
        try:
            nlp = spacy.load(model_name)
            logger.info(f"Modèle NER chargé: {model_name}")
        except OSError:
            # Fallback sur modèle moyen
            fallback = "fr_core_news_md"
            try:
                nlp = spacy.load(fallback)
                logger.warning(f"Fallback NER: {fallback} (modèle {model_name} non disponible)")
            except OSError:
                # Dernier fallback: petit modèle
                fallback_sm = "fr_core_news_sm"
                nlp = spacy.load(fallback_sm)
                logger.warning(f"Fallback NER: {fallback_sm}")

        return nlp

    except Exception as e:
        logger.error(f"Erreur chargement modèle NER: {str(e)}")
        return None
