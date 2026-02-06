"""Tests d'intégration pour l'endpoint health"""
import pytest
from unittest.mock import patch, MagicMock


def test_health_endpoint_structure():
    """Vérifie la structure de la réponse health."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]


def test_root_endpoint():
    """Vérifie la route racine."""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "MediaWatch CI API"
    assert data["version"] == "1.0.0"
