"""Routes : playground de chat (LiteLLM + tools MCP), streaming SSE."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import sessionmaker

from mcpgen.api.deps import get_app_settings, get_db_factory
from mcpgen.core.config import Settings
from mcpgen.models.schemas import ChatProvider, ChatRequest, ExecuteToolRequest
from mcpgen.services.chat_service import ChatService
from mcpgen.services.generation_service import GeneratedServerNotFoundError, GenerationService

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _serialize_event_data(kind: str, data: Any) -> Any:
    """Sérialise les événements pour le flux SSE (ToolCallInfo -> dict JSON)."""
    if kind == "tool_calls" and isinstance(data, list):
        return [asdict(item) for item in data]
    return data


@router.get("/providers", response_model=list[ChatProvider])
def list_providers() -> list[ChatProvider]:
    """Providers disponibles (Mistral par défaut, extensible via LiteLLM)."""
    return [ChatProvider(**provider) for provider in ChatService.list_providers()]


@router.post("")
async def chat_stream(
    payload: ChatRequest,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> StreamingResponse:
    """Chat outillé : flux SSE avec deltas de texte, tool calls et résultats."""
    generation = GenerationService(factory, settings)
    try:
        server = generation.get(payload.server_id)
    except GeneratedServerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    service = ChatService(settings)

    async def event_stream():
        yield "event: start\ndata: {}\n\n"
        try:
            async for event in service.stream_chat(server, payload):
                data = json.dumps(
                    _serialize_event_data(event.kind, event.data),
                    ensure_ascii=False,
                    default=str,
                )
                yield f"event: {event.kind}\ndata: {data}\n\n"
                if event.kind == "error":
                    yield 'event: done\ndata: {"error": true}\n\n'
                    return
            yield 'event: done\ndata: {"error": false}\n\n'
        except Exception as exc:  # noqa: BLE001 - sérialisé vers le client SSE
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"
            yield 'event: done\ndata: {"error": true}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{server_id}/execute-tool")
async def execute_tool(
    server_id: int,
    payload: ExecuteToolRequest,
    factory: sessionmaker = Depends(get_db_factory),
    settings: Settings = Depends(get_app_settings),
) -> dict:
    """Exécute un tool manuellement (debug) — sans passer par le LLM."""
    generation = GenerationService(factory, settings)
    try:
        server = generation.get(server_id)
    except GeneratedServerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    service = ChatService(settings)
    try:
        result = await service.execute_tool(server, payload.name, payload.arguments)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"tool": payload.name, "result": result}
