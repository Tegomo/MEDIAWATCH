"""Tests unitaires pour le CSVExporter"""
import csv
import io
from unittest.mock import MagicMock, patch
from datetime import datetime
from uuid import uuid4

import pytest


class FakeSentimentLabel:
    def __init__(self, v):
        self.value = v

class FakeTheme:
    def __init__(self, v):
        self.value = v

class FakeCategory:
    def __init__(self, v):
        self.value = v


def _make_mention(
    text="Orange CI",
    sentiment="positive",
    score=0.85,
    theme="economy",
    title="Test Article",
    source_name="Fraternité Matin",
    detected_at=None,
):
    mention = MagicMock()
    mention.detected_at = detected_at or datetime(2026, 1, 15, 10, 30)
    mention.sentiment_label = FakeSentimentLabel(sentiment)
    mention.sentiment_score = score
    mention.visibility_score = 0.7
    mention.theme = FakeTheme(theme)
    mention.matched_text = text
    mention.match_context = f"Contexte de {text}"

    keyword = MagicMock()
    keyword.text = text
    keyword.category = FakeCategory("brand")
    mention.keyword = keyword

    source = MagicMock()
    source.name = source_name

    article = MagicMock()
    article.title = title
    article.url = "https://example.com/article"
    article.author = "Auteur Test"
    article.published_at = datetime(2026, 1, 15, 8, 0)
    article.source = source
    mention.article = article

    return mention


def test_csv_exporter_headers():
    """Vérifie que les headers CSV sont corrects."""
    from src.services.exports.csv_exporter import CSVExporter

    assert len(CSVExporter.HEADERS) == 13
    assert "Date détection" in CSVExporter.HEADERS
    assert "Sentiment" in CSVExporter.HEADERS
    assert "URL article" in CSVExporter.HEADERS


@patch("src.services.exports.csv_exporter.MentionService")
def test_csv_export_content(mock_service_cls):
    """Vérifie le contenu CSV généré."""
    from src.services.exports.csv_exporter import CSVExporter

    mentions = [_make_mention(), _make_mention(text="MTN CI", sentiment="negative", score=0.3)]
    mock_service = MagicMock()
    mock_service.list_mentions.return_value = (mentions, 2)
    mock_service_cls.return_value = mock_service

    db = MagicMock()
    exporter = CSVExporter(db)
    content, count = exporter.export(organization_id=uuid4())

    assert count == 2
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 3  # header + 2 data rows
    assert rows[0][0] == "Date détection"
    assert rows[1][1] == "Orange CI"
    assert rows[2][1] == "MTN CI"


@patch("src.services.exports.csv_exporter.MentionService")
def test_csv_export_empty(mock_service_cls):
    """Vérifie l'export CSV vide."""
    from src.services.exports.csv_exporter import CSVExporter

    mock_service = MagicMock()
    mock_service.list_mentions.return_value = ([], 0)
    mock_service_cls.return_value = mock_service

    db = MagicMock()
    exporter = CSVExporter(db)
    content, count = exporter.export(organization_id=uuid4())

    assert count == 0
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1  # header only


def test_csv_filename():
    """Vérifie le format du nom de fichier."""
    from src.services.exports.csv_exporter import CSVExporter

    db = MagicMock()
    exporter = CSVExporter(db)
    filename = exporter.get_filename()
    assert filename.startswith("mediawatch_mentions_")
    assert filename.endswith(".csv")
