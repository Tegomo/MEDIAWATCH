"""Tests unitaires pour le StorageService"""
import os
import tempfile
from unittest.mock import patch

import pytest


def test_save_and_get_file():
    """Vérifie la sauvegarde et récupération d'un fichier."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.services.storage_service.EXPORTS_DIR", tmpdir):
            from src.services.storage_service import StorageService
            service = StorageService()

            content = b"Hello, MediaWatch!"
            file_id = service.save_file(content, "test.csv")

            assert file_id.endswith("test.csv")
            retrieved = service.get_file(file_id)
            assert retrieved == content


def test_get_nonexistent_file():
    """Vérifie le retour None pour un fichier inexistant."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.services.storage_service.EXPORTS_DIR", tmpdir):
            from src.services.storage_service import StorageService
            service = StorageService()
            assert service.get_file("nonexistent_file.csv") is None


def test_delete_file():
    """Vérifie la suppression d'un fichier."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.services.storage_service.EXPORTS_DIR", tmpdir):
            from src.services.storage_service import StorageService
            service = StorageService()

            file_id = service.save_file(b"data", "to_delete.csv")
            assert service.delete_file(file_id) is True
            assert service.get_file(file_id) is None
            assert service.delete_file(file_id) is False


def test_download_url():
    """Vérifie le format de l'URL de téléchargement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.services.storage_service.EXPORTS_DIR", tmpdir):
            from src.services.storage_service import StorageService
            service = StorageService()
            url = service.get_download_url("abc_test.pdf")
            assert url == "/api/v1/exports/download/abc_test.pdf"
