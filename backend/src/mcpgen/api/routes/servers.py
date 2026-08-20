"""Routes : CRUD des serveurs MCP générés + téléchargement + statut en temps réel."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import sessionmaker

from mcpgen.api.deps import get_app_settings, get_db_factory
from mcpgen.core.config import Settings
from mcpgen.models.db_models import GeneratedServer, ServerStatus
from mcpgen.models.schemas import ServerRead
from mcpgen.services.generation_service import (
    GeneratedServerNotFoundError,
    GenerationService,
)

router = APIRouter(prefix="/api/servers", tags=["servers"])

STATUS_ORDER = {
    ServerStatus.ready: 0,
    ServerStatus.generating: 1,
    ServerStatus.regenerating: 1,
    ServerStatus.pending: 2,
    ServerStatus.failed: 3,
}


def _to_read(server: GeneratedServer) -> ServerRead:
    return ServerRead(
        id=server.id,
        name=server.name,
        description=server.description,
        base_url=server.base_url,
        auth_type=server.auth_type,
        status=(
            server.status.value if isinstance(server.status, ServerStatus) else str(server.status)
        ),
        dir_name=server.dir_name,
        endpoints_count=server.endpoints_count,
        error=server.error,
        spec_id=server.spec_id,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


@router.get("", response_model=list[ServerRead])
def list_servers(
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> list[ServerRead]:
    service = GenerationService(factory, settings)
    servers = service.list()
    servers.sort(key=lambda s: STATUS_ORDER.get(s.status, 9))
    return [_to_read(s) for s in servers]


@router.get("/{server_id}", response_model=ServerRead)
def get_server(
    server_id: int,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> ServerRead:
    service = GenerationService(factory, settings)
    try:
        return _to_read(service.get(server_id))
    except GeneratedServerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{server_id}", status_code=204)
def delete_server(
    server_id: int,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> None:
    service = GenerationService(factory, settings)
    try:
        service.delete(server_id)
    except GeneratedServerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{server_id}/download")
def download_server(
    server_id: int,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> FileResponse:
    """Télécharge le serveur MCP généré (zip exportable)."""
    service = GenerationService(factory, settings)
    try:
        server = service.get(server_id)
        if server.status not in (ServerStatus.ready,):
            raise HTTPException(
                status_code=409,
                detail=f"Serveur non prêt (statut : {server.status})",
            )
        zip_path = service.zip_path(server)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{server.name}.zip",
        )
    except GeneratedServerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{server_id}/status")
async def server_status_stream(
    server_id: int,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> StreamingResponse:
    """Flux SSE : statut de génération en temps réel (pending/generating/ready/failed)."""

    async def event_stream():
        service = GenerationService(factory, settings)
        last_status: str | None = None
        while True:
            try:
                server = service.get(server_id)
                current = _to_read(server).status
            except GeneratedServerNotFoundError:
                yield f"event: error\ndata: {json.dumps({'error': 'server_not_found'})}\n\n"
                return
            if current != last_status:
                status_data = json.dumps(
                    {"status": current, "error": server.error}, ensure_ascii=False
                )
                yield f"event: status\ndata: {status_data}\n\n"
                last_status = current
            if current in ("ready", "failed"):
                yield f"event: done\ndata: {json.dumps({'final': current})}\n\n"
                return
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
