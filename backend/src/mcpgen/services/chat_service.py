"""Service de chat : boucle LLM (LiteLLM) + exécution des tools MCP sur l'API réelle."""

from __future__ import annotations

import asyncio
import base64
import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from mcpgen.core.config import Settings
from mcpgen.core.logging import get_logger
from mcpgen.llm.litellm_client import ChatEvent, LiteLLMClient
from mcpgen.llm.providers import provider_list
from mcpgen.mcp_generator.tool_builder import build_tool_specs
from mcpgen.models.db_models import GeneratedServer
from mcpgen.models.schemas import ChatRequest
from mcpgen.services.generation_service import GenerationService

logger = get_logger(__name__)


class HttpToolRunner:
    """Exécute les appels HTTP réels vers l'API cible (utilisé par le playground)."""

    def __init__(
        self,
        base_url: str,
        auth: dict[str, Any],
        timeout: float = 30.0,
        retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth or {}
        self.timeout = timeout
        self.retries = retries

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Accept": "application/json"}
        auth_type = self.auth.get("type", "none")
        if auth_type == "api_key":
            header = self.auth.get("header_name") or "X-API-Key"
            key = self.auth.get("api_key") or ""
            if key:
                headers[header] = key
        elif auth_type == "bearer":
            key = self.auth.get("api_key") or ""
            if key:
                headers["Authorization"] = f"Bearer {key}"
        elif auth_type == "basic":
            username = self.auth.get("username", "")
            password = self.auth.get("password", "")
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        return headers

    @staticmethod
    def _build_url(base: str, path: str, args: dict[str, Any]) -> str:
        url = base + path
        for key, value in args.items():
            url = url.replace("{" + key + "}", str(value))
        return url

    async def execute(self, tool: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
        url = self._build_url(self.base_url, tool["path"], arguments)
        query = {key: arguments[key] for key in tool.get("query_params", []) if key in arguments}
        headers = self._headers()
        for key in tool.get("header_params", []):
            if key in arguments:
                headers[key] = str(arguments[key])
        content: str | None = None
        if tool.get("has_body") and "body" in arguments:
            content = json.dumps(arguments["body"], ensure_ascii=False)
            headers["Content-Type"] = "application/json"

        last_error: str | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.retries + 1):
                try:
                    response = await client.request(
                        tool["method"], url, params=query, headers=headers, content=content
                    )
                    try:
                        payload: Any = response.json()
                    except ValueError:
                        payload = {"text": response.text[:200_000]}
                    return {"status_code": response.status_code, "data": payload}
                except httpx.HTTPError as exc:
                    last_error = str(exc)
                    if attempt < self.retries:
                        await asyncio.sleep(0.5 * (attempt + 1))
        return {"error": f"Échec après {self.retries + 1} tentative(s) : {last_error}"}


class ChatService:
    """Orchestration du playground : LLM (LiteLLM) outillé avec les tools MCP."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = LiteLLMClient(settings)

    @staticmethod
    def list_providers() -> list[dict[str, Any]]:
        return provider_list()

    @staticmethod
    def _tools_for_server(server: GeneratedServer) -> list[dict[str, Any]]:
        endpoints = GenerationService.parse_endpoints(server.endpoints)
        specs = build_tool_specs(endpoints)
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "input_schema": spec.input_schema,
                "method": spec.method,
                "path": spec.path,
                "path_params": spec.path_params,
                "query_params": spec.query_params,
                "header_params": spec.header_params,
                "has_body": spec.has_body,
            }
            for spec in specs
        ]

    @staticmethod
    def _runner_for_server(server: GeneratedServer) -> HttpToolRunner:
        auth = json.loads(server.auth_config or "{}")
        return HttpToolRunner(
            base_url=server.base_url or "",
            auth=auth,
            timeout=30.0,
            retries=2,
        )

    async def stream_chat(
        self,
        server: GeneratedServer,
        request: ChatRequest,
    ) -> AsyncIterator[ChatEvent]:
        """Boucle de chat outillé : LLM <-> tools <-> API réelle (SSE events)."""
        tools = self._tools_for_server(server)
        if not tools:
            yield ChatEvent(kind="error", data="Le serveur MCP ne contient aucun tool")
            return

        runner = self._runner_for_server(server)
        messages = [m.model_dump(exclude_none=True) for m in request.messages]
        model = request.model or self.settings.litellm_model

        for _iteration in range(request.max_tool_iterations):
            emitted = False
            had_tool_calls = False
            async for event in self.client.stream_chat(messages, model, tools):
                emitted = True
                if event.kind == "tool_calls":
                    had_tool_calls = True
                    yield ChatEvent(kind="tool_calls", data=event.data)
                    assistant_args = {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": json.dumps(tc.arguments),
                                },
                            }
                            for tc in event.data
                        ],
                    }
                    messages.append(assistant_args)
                    for tc in event.data:
                        tool = next((t for t in tools if t["name"] == tc.name), None)
                        if tool is None:
                            result = json.dumps({"error": f"Tool inconnu : {tc.name}"})
                        else:
                            result = json.dumps(
                                await runner.execute(tool, tc.arguments), ensure_ascii=False
                            )
                        yield ChatEvent(kind="tool_result", data={"id": tc.id, "result": result})
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                else:
                    yield event
            if not emitted:
                yield ChatEvent(kind="error", data="Aucune réponse du LLM")
                return
            if not had_tool_calls:
                return

        raise RuntimeError(f"Nombre maximal d'itérations atteint ({request.max_tool_iterations})")

    async def execute_tool(
        self, server: GeneratedServer, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Exécute un tool directement (debug) sans passer par le LLM."""
        tool = next((t for t in self._tools_for_server(server) if t["name"] == name), None)
        if tool is None:
            raise ValueError(f"Tool inconnu : {name}")
        return await self._runner_for_server(server).execute(tool, arguments)
