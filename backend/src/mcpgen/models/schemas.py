"""Schémas Pydantic (DTO) exposés par l'API REST."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- Swagger


class SwaggerParseByUrl(BaseModel):
    url: str = Field(..., description="URL publique de la spec Swagger/OpenAPI")


class ParsedParameterView(BaseModel):
    name: str
    in_: str = Field(alias="in")
    required: bool = False
    description: str | None = None
    schema_: dict[str, Any] | None = Field(default=None, alias="schema")


class ParsedEndpointView(BaseModel):
    method: str
    path: str
    name: str
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    security: list[dict[str, list[str]]] = Field(default_factory=list)


class SpecParseResponse(BaseModel):
    spec_id: int
    filename: str
    source_type: str
    title: str | None = None
    version: str | None = None
    openapi_version: str
    base_url: str | None = None
    endpoints: list[ParsedEndpointView]
    endpoints_count: int


class SpecRead(BaseModel):
    id: int
    filename: str
    source_type: str
    title: str | None = None
    version: str | None = None
    openapi_version: str | None = None
    base_url: str | None = None
    endpoints_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------- Serveurs


class AuthConfig(BaseModel):
    type: Literal["none", "api_key", "bearer", "basic"] = "none"
    header_name: str | None = None  # pour api_key
    api_key: str | None = None  # jamais stocké : utilisé à la génération
    username: str | None = None
    password: str | None = None


class ServerCreateRequest(BaseModel):
    spec_id: int
    name: str = Field(..., min_length=2, max_length=120, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = None
    base_url: str | None = Field(
        None, description="Override de l'URL cible (sinon celle de la spec)"
    )
    auth: AuthConfig = Field(default_factory=AuthConfig)
    include_endpoints: list[str] | None = None  # None = tous
    timeout: float = Field(30.0, gt=0, le=300)
    retries: int = Field(2, ge=0, le=10)


class ServerRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    base_url: str | None = None
    auth_type: str
    status: str
    dir_name: str | None = None
    endpoints_count: int
    error: str | None = None
    spec_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateResponse(BaseModel):
    server_id: int
    status: str = "pending"


# ---------------------------------------------------------------- Chat


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatRequest(BaseModel):
    server_id: int
    messages: list[ChatMessage]
    model: str | None = Field(None, description="Modèle LiteLLM (ex: mistral/mistral-large-latest)")
    max_tool_iterations: int = Field(5, ge=1, le=20)


class ExecuteToolRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatProvider(BaseModel):
    id: str
    display_name: str
    default_model: str
    models: list[str]


# ---------------------------------------------------------------- Divers


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    app_name: str
