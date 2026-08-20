"""Sécurité : clé API optionnelle pour protéger les routes d'administration."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from mcpgen.core.config import Settings, get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    api_key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Vérifie la clé API si elle est configurée (désactivé si `api_key` est vide)."""
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante",
        )
