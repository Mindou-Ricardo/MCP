"""Construction des définitions de tools MCP à partir des endpoints normalisés."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mcpgen.swagger.normalizer import ParsedEndpoint

# Paramètres gérés dynamiquement par le handler HTTP (pas dans l'input_schema).
_STRUCTURAL_PARAMS = {"path", "query", "header", "cookie", "body"}


@dataclass
class ToolSpec:
    """Spécification d'un tool MCP (nom, description, JSON Schema)."""

    name: str
    description: str
    input_schema: dict[str, Any]
    method: str
    path: str
    path_params: list[str] = field(default_factory=list)
    query_params: list[str] = field(default_factory=list)
    header_params: list[str] = field(default_factory=list)
    has_body: bool = False
    body_schema: dict[str, Any] | None = None
    security: list[dict[str, list[str]]] = field(default_factory=list)


def _schema_fragment(schema: dict[str, Any] | None) -> dict[str, Any]:
    """Fragment JSON Schema sûr (valide pour le protocole MCP)."""
    if not isinstance(schema, dict):
        return {"type": "string"}
    fragment: dict[str, Any] = {}
    schema_keys = (
        "type",
        "format",
        "description",
        "default",
        "enum",
        "items",
        "properties",
        "required",
    )
    for key in schema_keys:
        if key in schema:
            fragment[key] = schema[key]
    if "type" not in fragment:
        fragment["type"] = "string"
    if "description" not in fragment and schema.get("title"):
        fragment["description"] = str(schema["title"])
    if "additionalProperties" in schema:
        fragment["additionalProperties"] = schema["additionalProperties"]
    return fragment


def _build_description(endpoint: ParsedEndpoint) -> str:
    parts: list[str] = []
    summary = (endpoint.summary or "").strip()
    description = (endpoint.description or "").strip()
    if summary and summary != description:
        parts.append(summary)
    if description and (not summary or description != summary):
        parts.append(description)
    text = "\n\n".join(parts) or f"Appel HTTP {endpoint.method.upper()} {endpoint.path}"
    return f"{text}\n\nMéthode HTTP : {endpoint.method.upper()}.\nChemin : {endpoint.path}."


def build_input_schema(endpoint: ParsedEndpoint) -> dict[str, Any]:
    """Génère un JSON Schema valide (draft) pour l'`input_schema` du tool."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in endpoint.parameters:
        if param.in_ not in ("path", "query", "header"):
            continue
        fragment = _schema_fragment(param.schema_)
        if param.description:
            fragment["description"] = param.description
        properties[param.name] = fragment
        if param.required:
            required.append(param.name)

    if endpoint.request_body_schema is not None:
        body_schema = endpoint.request_body_schema
        fragment = _schema_fragment(body_schema)
        property_desc = fragment.pop("description", None)
        if property_desc:
            fragment = {"description": property_desc, **fragment}
        properties["body"] = fragment
        if endpoint.request_body_required:
            required.append("body")

    return {"type": "object", "properties": properties, "required": required}


def build_tool_spec(endpoint: ParsedEndpoint) -> ToolSpec:
    """Transforme un `ParsedEndpoint` en `ToolSpec` MCP."""
    path_params = [p.name for p in endpoint.parameters if p.in_ == "path"]
    query_params = [p.name for p in endpoint.parameters if p.in_ == "query"]
    header_params = [p.name for p in endpoint.parameters if p.in_ == "header"]
    return ToolSpec(
        name=endpoint.name,
        description=_build_description(endpoint),
        input_schema=build_input_schema(endpoint),
        method=endpoint.method,
        path=endpoint.path,
        path_params=path_params,
        query_params=query_params,
        header_params=header_params,
        has_body=endpoint.request_body_schema is not None,
        body_schema=endpoint.request_body_schema,
        security=endpoint.security,
    )


def build_tool_specs(
    endpoints: list[ParsedEndpoint],
    include_endpoints: list[str] | None = None,
) -> list[ToolSpec]:
    """Construit les ToolSpec de tous les endpoints (ou seulement ceux inclus)."""
    selected = endpoints
    if include_endpoints is not None:
        allowed = set(include_endpoints)
        selected = [e for e in endpoints if e.name in allowed]
    return [build_tool_spec(ep) for ep in selected]
