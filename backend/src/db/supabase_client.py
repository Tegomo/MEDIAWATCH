"""Client Supabase REST pour remplacer SQLAlchemy (contourne les problèmes DNS/IPv6)"""
import httpx
from typing import Optional, Any
from src.config import settings
from src.lib.logger import logger


class SupabaseDB:
    """
    Client REST Supabase qui utilise l'API PostgREST.
    Remplace SQLAlchemy pour les opérations CRUD.
    """

    def __init__(self):
        self.base_url = f"{settings.supabase_url}/rest/v1"
        self.headers = {
            "apikey": settings.supabase_service_key,
            "Authorization": f"Bearer {settings.supabase_service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self._client = httpx.Client(timeout=15, headers=self.headers)

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Effectue une requête HTTP synchrone vers PostgREST."""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("extra_headers", {})

        response = self._client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()

        if response.status_code == 204:
            return []

        try:
            return response.json()
        except Exception:
            return []

    def _request_raw(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Effectue une requête et retourne la Response brute."""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("extra_headers", {})
        response = self._client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    # =========================================================================
    # SELECT
    # =========================================================================

    def select(self, table: str, columns: str = "*", **filters) -> list[dict]:
        """
        SELECT depuis une table.
        
        Usage:
            db.select("users", columns="*", email="eq.john@example.com")
            db.select("mentions", columns="*,keyword:keywords(*),article:articles(*,source:sources(*))")
        """
        params = {"select": columns}
        for key, value in filters.items():
            params[key] = value

        return self._request("GET", f"/{table}", params=params)

    def select_one(self, table: str, columns: str = "*", **filters) -> Optional[dict]:
        """SELECT un seul enregistrement."""
        extra_headers = {"Accept": "application/vnd.pgrst.object+json"}
        params = {"select": columns, "limit": "1"}
        for key, value in filters.items():
            params[key] = value

        try:
            return self._request("GET", f"/{table}", params=params, extra_headers=extra_headers)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 406:
                return None
            raise

    def count(self, table: str, **filters) -> int:
        """COUNT des enregistrements."""
        extra_headers = {
            "Prefer": "count=exact",
            "Range-Unit": "items",
            "Range": "0-0",
        }
        params = {"select": "id"}
        for key, value in filters.items():
            params[key] = value

        response = self._request_raw("GET", f"/{table}", params=params, extra_headers=extra_headers)
        content_range = response.headers.get("content-range", "*/0")
        total = content_range.split("/")[-1]
        return int(total) if total != "*" else 0

    def select_with_count(self, table: str, columns: str = "*", **filters) -> tuple[list[dict], int]:
        """
        SELECT + COUNT en une seule requête HTTP.
        Retourne (rows, total_count).
        """
        extra_headers = {
            "Prefer": "count=exact",
        }
        params = {"select": columns}
        for key, value in filters.items():
            params[key] = value

        response = self._request_raw("GET", f"/{table}", params=params, extra_headers=extra_headers)
        content_range = response.headers.get("content-range", "*/0")
        total_str = content_range.split("/")[-1]
        total = int(total_str) if total_str != "*" else 0

        try:
            rows = response.json()
        except Exception:
            rows = []

        return rows, total

    # =========================================================================
    # INSERT
    # =========================================================================

    def insert(self, table: str, data: dict | list[dict]) -> list[dict]:
        """INSERT un ou plusieurs enregistrements."""
        if isinstance(data, dict):
            data = [data]
        return self._request("POST", f"/{table}", json=data)

    def insert_one(self, table: str, data: dict) -> Optional[dict]:
        """INSERT un seul enregistrement et retourne-le."""
        result = self.insert(table, data)
        return result[0] if result else None

    # =========================================================================
    # UPDATE
    # =========================================================================

    def update(self, table: str, data: dict, **filters) -> list[dict]:
        """UPDATE des enregistrements avec filtres."""
        params = {}
        for key, value in filters.items():
            params[key] = value

        return self._request("PATCH", f"/{table}", json=data, params=params)

    # =========================================================================
    # DELETE
    # =========================================================================

    def delete(self, table: str, **filters) -> list[dict]:
        """DELETE des enregistrements avec filtres."""
        params = {}
        for key, value in filters.items():
            params[key] = value

        return self._request("DELETE", f"/{table}", params=params)

    # =========================================================================
    # RPC (fonctions SQL)
    # =========================================================================

    def rpc(self, function_name: str, params: dict = None) -> Any:
        """Appelle une fonction PostgreSQL via RPC."""
        return self._request("POST", f"/rpc/{function_name}", json=params or {})

    # =========================================================================
    # Health check
    # =========================================================================

    def health_check(self) -> bool:
        """Vérifie la connexion à Supabase."""
        try:
            self.select("sources", columns="id", limit="1")
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False


# Singleton
_db_instance: Optional[SupabaseDB] = None


def get_supabase_db() -> SupabaseDB:
    """Retourne l'instance singleton du client Supabase DB."""
    global _db_instance
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance


def get_db():
    """Dependency injection compatible avec FastAPI."""
    return get_supabase_db()
