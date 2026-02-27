"""Gestion globale des erreurs"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import httpx

from src.lib.logger import logger


class MediaWatchException(Exception):
    """Exception de base pour MediaWatch CI"""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundException(MediaWatchException):
    """Ressource non trouvée"""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} avec ID {resource_id} non trouvé",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class LimitExceededException(MediaWatchException):
    """Limite de plan atteinte"""

    def __init__(self, resource: str, limit: int):
        super().__init__(
            message=f"Limite de {resource} atteinte ({limit}). Veuillez upgrader votre plan.",
            status_code=status.HTTP_409_CONFLICT,
        )


class UnauthorizedException(MediaWatchException):
    """Non autorisé"""

    def __init__(self, message: str = "Non autorisé"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(MediaWatchException):
    """Accès interdit"""

    def __init__(self, message: str = "Accès interdit"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


def setup_exception_handlers(app: FastAPI):
    """Configure les gestionnaires d'exceptions globaux"""

    @app.exception_handler(MediaWatchException)
    async def mediawatch_exception_handler(request: Request, exc: MediaWatchException):
        logger.error(f"MediaWatch Exception: {exc.message}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation Error: {exc.errors()}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "ValidationError", "message": "Données invalides", "details": exc.errors()},
        )

    @app.exception_handler(httpx.HTTPStatusError)
    async def http_exception_handler(request: Request, exc: httpx.HTTPStatusError):
        logger.error(f"Database/HTTP Error: {str(exc)}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "DatabaseError", "message": "Erreur de base de données"},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled Exception: {str(exc)}", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "message": "Erreur interne du serveur"},
        )
