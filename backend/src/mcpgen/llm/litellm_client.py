"""Client LiteLLM : streaming des réponses LLM avec tool calls (format OpenAI)."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from mcpgen.core.config import Settings


class LiteLLMError(Exception):
    """Erreur d'appel au LLM via LiteLLM."""


@dataclass
class ToolCallInfo:
    """Appel de tool demandé par le LLM."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    arguments_raw: str = ""


@dataclass
class ChatEvent:
    """Événement émis par le client (streaming chat)."""

    kind: str  # "delta" | "tool_calls" | "done" | "error"
    data: Any = None


class LiteLLMClient:
    """Wrapper autour de `litellm.acompletion` (streaming, tools OpenAI)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        # Les clés de providers sont injectées via l'environnement (jamais en dur).
        for env_var in ("MISTRAL_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
            value = getattr(settings, env_var.lower(), None)
            if value:
                os.environ.setdefault(env_var, value)

    def _completion_kwargs(self, model: str) -> dict[str, Any]:
        """Construit les kwargs d'appel selon le provider (proxy LiteLLM ou direct)."""

        base_kwargs: dict[str, Any] = {
            "model": model,
            "timeout": self.settings.litellm_timeout,
            "drop_params": True,
        }
        if model.startswith("ollama/"):
            base_kwargs["api_base"] = self.settings.ollama_api_base
            base_kwargs.pop("drop_params", None)
        else:
            base_kwargs["api_base"] = self.settings.litellm_api_base
            base_kwargs["api_key"] = self.settings.litellm_master_key
        # S'assure que les clés provider sont visibles par litellm
        for name, value in (
            ("MISTRAL_API_KEY", self.settings.mistral_api_key),
            ("OPENAI_API_KEY", self.settings.openai_api_key),
            ("ANTHROPIC_API_KEY", self.settings.anthropic_api_key),
        ):
            if value:
                os.environ[name] = value
        return base_kwargs

    @staticmethod
    def to_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convertit des tools MCP (name/description/input_schema) au format OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
            for tool in tools
        ]

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        model: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[ChatEvent]:
        """Stream la réponse du LLM. Émet `delta`, puis `tool_calls` OU `done`."""
        import litellm  # import lent : différé

        kwargs = self._completion_kwargs(model)
        try:
            # `stream=True` : litellm retourne un AsyncStream — typé Any par compatibilité
            response: Any = await litellm.acompletion(
                messages=messages,
                stream=True,
                tools=self.to_openai_tools(tools) if tools else None,
                **kwargs,
            )
        except Exception as exc:  # litellm expose plusieurs types d'erreurs
            raise LiteLLMError(f"Échec de l'appel LLM ({model}) : {exc}") from exc

        text_buffer: list[str] = []
        tool_calls: dict[int, ToolCallInfo] = {}

        try:
            async for chunk in response:
                choices = chunk.choices or []
                if not choices:
                    continue
                delta = choices[0].delta
                if delta is None:
                    continue
                if delta.content:
                    text_buffer.append(delta.content)
                    yield ChatEvent(kind="delta", data=delta.content)
                for tool_call in delta.tool_calls or []:
                    index = tool_call.index or 0
                    if tool_call.id:
                        tool_calls[index] = ToolCallInfo(id=tool_call.id, name="", arguments_raw="")
                    entry = tool_calls.get(index)
                    if entry is None:
                        entry = ToolCallInfo(id=tool_call.id or "", name="", arguments_raw="")
                        tool_calls[index] = entry
                    if tool_call.function:
                        if tool_call.function.name:
                            entry.name += tool_call.function.name
                        if tool_call.function.arguments:
                            entry.arguments_raw += tool_call.function.arguments
        except Exception as exc:
            raise LiteLLMError(f"Erreur pendant le streaming LLM : {exc}") from exc

        if tool_calls:
            for entry in tool_calls.values():
                raw = entry.arguments_raw or "{}"
                try:
                    entry.arguments = json.loads(raw) if raw.strip() else {}
                except json.JSONDecodeError:
                    entry.arguments = {"_error": f"arguments non JSON : {raw[:200]}"}
            yield ChatEvent(kind="tool_calls", data=[entry for entry in tool_calls.values()])
        else:
            yield ChatEvent(kind="done", data="".join(text_buffer))
