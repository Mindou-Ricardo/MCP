"""Tests du service de chat (LiteLLM mocket + exécution de tools HTTP)."""

from __future__ import annotations

import asyncio
import json
import types
from pathlib import Path

import httpx
import pytest

from mcpgen.core.config import Settings
from mcpgen.llm.litellm_client import ChatEvent, ToolCallInfo
from mcpgen.mcp_generator.generator import GenerationConfig, MCPGenerator
from mcpgen.models.db_models import GeneratedServer, ServerStatus
from mcpgen.models.schemas import ChatMessage, ChatRequest
from mcpgen.services.chat_service import ChatService, HttpToolRunner
from mcpgen.swagger.normalizer import normalize_spec
from tests.conftest import SAMPLE_OPENAPI_30


def patched_httpx_module(handler) -> types.ModuleType:
    """Module httpx factice : AsyncClient remplacé par un MockTransport."""

    class PatchedAsyncClient(httpx.AsyncClient):  # type: ignore[misc]
        def __init__(self, *args, **kwargs):
            kwargs.pop("transport", None)
            super().__init__(*args, transport=httpx.MockTransport(handler), **kwargs)

    fake = types.ModuleType("httpx")
    fake.AsyncClient = PatchedAsyncClient
    fake.HTTPError = httpx.HTTPError
    fake.ConnectError = httpx.ConnectError
    return fake


def _server() -> GeneratedServer:
    return GeneratedServer(
        id=1,
        name="petstore",
        base_url="https://api.example.com/v1",
        auth_type="api_key",
        auth_config=json.dumps({"type": "api_key", "header_name": "X-API-Key", "api_key": "k123"}),
        status=ServerStatus.ready,
        endpoints=json.dumps(
            [
                {
                    "method": "GET",
                    "path": "/pets",
                    "name": "list_pets",
                    "summary": "Liste",
                    "description": "Liste",
                    "parameters": [
                        {
                            "name": "limit",
                            "in_": "query",
                            "required": False,
                            "schema_": {"type": "integer"},
                        }
                    ],
                },
                {
                    "method": "POST",
                    "path": "/pets",
                    "name": "create_pet",
                    "parameters": [],
                    "request_body_schema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {"name": {"type": "string"}},
                    },
                    "request_body_required": True,
                },
            ]
        ),
        endpoints_count=2,
    )


class TestHttpToolRunner:
    def test_get_with_headers_and_query(self, monkeypatch):
        import mcpgen.services.chat_service as chat_module

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/v1/pets"
            assert request.url.params["limit"] == "10"
            assert request.headers["X-API-Key"] == "k123"
            assert request.headers["Accept"] == "application/json"
            return httpx.Response(200, json=[{"id": 1}])

        runner = HttpToolRunner(
            "https://api.example.com/v1",
            {"type": "api_key", "header_name": "X-API-Key", "api_key": "k123"},
        )
        monkeypatch.setattr(chat_module, "httpx", patched_httpx_module(handler))

        result = asyncio.run(
            runner.execute(
                {
                    "method": "GET",
                    "path": "/pets",
                    "query_params": ["limit"],
                    "path_params": [],
                    "header_params": [],
                    "has_body": False,
                },
                {"limit": 10},
            )
        )
        assert result["status_code"] == 200
        assert result["data"] == [{"id": 1}]

    def test_path_param_substitution(self):
        path = HttpToolRunner._build_url(
            "https://api.example.com/v1", "/pets/{pet_id}", {"pet_id": "42"}
        )
        assert path == "https://api.example.com/v1/pets/42"

    def test_bearer_auth_headers(self):
        runner = HttpToolRunner("https://x.test", {"type": "bearer", "api_key": "tok"})
        assert runner._headers()["Authorization"] == "Bearer tok"

    def test_basic_auth_headers(self):
        runner = HttpToolRunner(
            "https://x.test", {"type": "basic", "username": "u", "password": "p"}
        )
        assert runner._headers()["Authorization"] == "Basic dTpw"

    def test_retries_on_network_error(self, monkeypatch):
        import mcpgen.services.chat_service as chat_module

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("down")

        runner = HttpToolRunner("https://x.test", {}, timeout=0.5, retries=2)
        monkeypatch.setattr(chat_module, "httpx", patched_httpx_module(handler))

        result = asyncio.run(
            runner.execute(
                {
                    "method": "GET",
                    "path": "/pets",
                    "query_params": [],
                    "path_params": [],
                    "header_params": [],
                    "has_body": False,
                },
                {},
            )
        )
        assert "error" in result


class FakeLiteLLMClient:
    """Remplace LiteLLMClient : simule un LLM qui appelle un tool puis conclut."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def stream_chat(self, messages, model, tools=None):
        if not any(m.get("role") == "tool" for m in messages):
            yield ChatEvent(
                kind="tool_calls",
                data=[ToolCallInfo(id="call_1", name="list_pets", arguments={"limit": 7})],
            )
        else:
            yield ChatEvent(kind="delta", data="J'ai ")
            yield ChatEvent(kind="delta", data="récupéré les animaux.")
            yield ChatEvent(kind="done", data="J'ai récupéré les animaux.")


@pytest.mark.asyncio
async def test_chat_service_tool_loop(tmp_settings: Settings, monkeypatch):
    import mcpgen.services.chat_service as chat_module

    handler = lambda request: httpx.Response(200, json=[{"id": 1}])  # noqa: E731
    monkeypatch.setattr(chat_module, "httpx", patched_httpx_module(handler))

    service = ChatService(tmp_settings)
    service.client = FakeLiteLLMClient(tmp_settings)  # type: ignore[assignment]

    request = ChatRequest(
        server_id=1,
        messages=[ChatMessage(role="user", content="Liste les animaux")],
    )
    events = [event async for event in service.stream_chat(_server(), request)]

    kinds = [e.kind for e in events]
    assert kinds.count("tool_calls") == 1  # une seule itération outils
    assert "tool_result" in kinds
    assert events[-1].kind == "done"
    assert "récupéré les animaux" in events[-1].data

    tool_result = next(e for e in events if e.kind == "tool_result")
    payload = json.loads(tool_result.data["result"])
    assert payload["status_code"] == 200


def test_chat_service_list_providers():
    providers = ChatService.list_providers()
    ids = {p["id"] for p in providers}
    assert "mistral" in ids  # provider par défaut
    assert "ollama" in ids


@pytest.mark.asyncio
async def test_chat_service_direct_error(tmp_settings: Settings):
    server = _server()
    server.endpoints = json.dumps([])
    service = ChatService(tmp_settings)
    request = ChatRequest(server_id=1, messages=[ChatMessage(role="user", content="Bonjour")])
    events = [event async for event in service.stream_chat(server, request)]
    assert events[0].kind == "error"


def test_generation_e2e(tmp_settings: Settings, tmp_path: Path):
    """Génération complète : spec -> serveur MCP sur disque."""
    parsed = normalize_spec(SAMPLE_OPENAPI_30)
    result = MCPGenerator().generate(
        parsed,
        GenerationConfig(name="e2e", base_url="https://api.example.com/v1"),
        tmp_path,
    )
    assert result.output_dir.exists()
    server_py = (result.output_dir / "server.py").read_text(encoding="utf-8")
    assert "list_tools" in server_py
    tools_py = (result.output_dir / "tools.py").read_text(encoding="utf-8")
    assert '"name": "list_pets"' in tools_py
