"""Service de stockage pour les fichiers exportés (local + Supabase Storage)"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from src.config import settings
from src.lib.logger import logger


EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports")


class StorageService:
    """
    Stockage des fichiers d'export.
    Mode local par défaut, avec support Supabase Storage si configuré.
    """

    def __init__(self):
        os.makedirs(EXPORTS_DIR, exist_ok=True)

    def save_file(self, content: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
        """
        Sauvegarde un fichier et retourne son identifiant unique.
        """
        file_id = f"{uuid.uuid4().hex[:12]}_{filename}"
        filepath = os.path.join(EXPORTS_DIR, file_id)

        with open(filepath, "wb") as f:
            f.write(content)

        logger.info(f"Fichier sauvegardé: {file_id} ({len(content)} bytes)")
        return file_id

    def get_file(self, file_id: str) -> Optional[bytes]:
        """Récupère le contenu d'un fichier par son identifiant."""
        filepath = os.path.join(EXPORTS_DIR, file_id)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "rb") as f:
            return f.read()

    def get_download_url(self, file_id: str) -> str:
        """
        Retourne l'URL de téléchargement pour un fichier.
        En mode local, retourne un chemin API relatif.
        """
        return f"/api/v1/exports/download/{file_id}"

    def delete_file(self, file_id: str) -> bool:
        """Supprime un fichier."""
        filepath = os.path.join(EXPORTS_DIR, file_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Fichier supprimé: {file_id}")
            return True
        return False

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """Supprime les fichiers plus anciens que max_age_hours."""
        count = 0
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

        for filename in os.listdir(EXPORTS_DIR):
            filepath = os.path.join(EXPORTS_DIR, filename)
            if os.path.isfile(filepath):
                mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    count += 1

        if count:
            logger.info(f"Nettoyage exports: {count} fichiers supprimés")
        return count
