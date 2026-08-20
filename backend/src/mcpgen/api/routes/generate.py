"""Routes : génération de serveurs MCP."""

from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import sessionmaker

from mcpgen.api.deps import get_app_settings, get_db_factory
from mcpgen.core.config import Settings
from mcpgen.models.schemas import GenerateResponse, ServerCreateRequest
from mcpgen.services.generation_service import GenerationService, ServerNameTakenError
from mcpgen.services.swagger_service import SwaggerService, SwaggerSpecNotFoundError

router = APIRouter(prefix="/api/servers", tags=["generate"])


def _schedule_generation(factory: sessionmaker, settings: Settings, server_id: int) -> None:
    """Lance la génération en arrière-plan (thread) — statut suivi via SSE."""

    def run() -> None:
        GenerationService(factory, settings).run_generation(server_id)

    threading.Thread(target=run, daemon=True, name=f"gen-{server_id}").start()


@router.post("/generate", response_model=GenerateResponse, status_code=202)
def generate_server(
    payload: ServerCreateRequest,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> GenerateResponse:
    """Crée un serveur MCP depuis une spec parsée et lance sa génération."""
    service = GenerationService(factory, settings)
    try:
        spec = SwaggerService(factory(), settings).get(payload.spec_id)
    except SwaggerSpecNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        server = service.create(payload, spec)
    except ServerNameTakenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _schedule_generation(factory, settings, server.id)
    return GenerateResponse(server_id=server.id, status="pending")


@router.post("/{server_id}/regenerate", response_model=GenerateResponse, status_code=202)
def regenerate_server(
    server_id: int,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> GenerateResponse:
    """Relance la génération d'un serveur existant (déterministe et idempotente)."""
    service = GenerationService(factory, settings)
    server = service.get(server_id)
    _schedule_generation(factory, settings, server.id)
    return GenerateResponse(server_id=server.id, status="generating")
