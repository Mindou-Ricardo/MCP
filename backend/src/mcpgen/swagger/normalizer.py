"""Normalisation : spec OpenAPI résolue -> liste de `ParsedEndpoint`."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from mcpgen.swagger.parser import detect_openapi_version, load_spec_content
from mcpgen.utils.names import ensure_unique_name, make_identifier

_HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


class ParsedParameter(BaseModel):
    """Paramètre d'un endpoint (path/query/header/cookie)."""

    name: str
    in_: str
    required: bool = False
    description: str | None = None
    schema_: dict[str, Any] | None = None


class ParsedEndpoint(BaseModel):
    """Endpoint normalisé, prêt pour la génération MCP."""

    method: str
    path: str
    operation_id: str | None = None
    name: str  # snake_case, unique
    summary: str | None = None
    description: str | None = None
    parameters: list[ParsedParameter] = Field(default_factory=list)
    request_body_schema: dict[str, Any] | None = None
    request_body_required: bool = False
    responses: dict[str, dict[str, Any]] = Field(default_factory=dict)
    security: list[dict[str, list[str]]] = Field(default_factory=list)

    @property
    def display(self) -> str:
        return f"{self.method.upper()} {self.path}"


class ParsedSpec(BaseModel):
    """Résultat de la normalisation d'une spec."""

    raw: dict[str, Any]
    openapi_version: str
    title: str | None = None
    version: str | None = None
    base_url: str | None = None
    endpoints: list[ParsedEndpoint] = Field(default_factory=list)

    @property
    def endpoints_count(self) -> int:
        return len(self.endpoints)


def _extract_schema(node: Any) -> dict[str, Any] | None:
    """Récupère le schéma d'un objet (2.0 `schema` / 3.x `schema`), en excluant les exemples."""
    if not isinstance(node, dict) or "schema" not in node:
        return None
    schema = node["schema"]
    if not isinstance(schema, dict):
        return None
    return schema


def _extract_base_url(spec: dict[str, Any]) -> str | None:
    """Détermine l'URL cible (servers[0] en 3.x, scheme+host+basePath en 2.0)."""
    servers = spec.get("servers")
    if isinstance(servers, list) and servers and isinstance(servers[0], dict):
        return servers[0].get("url")
    if "schemes" in spec or "host" in spec or "basePath" in spec:
        schemes = spec.get("schemes") or ["https"]
        scheme = schemes[0] if isinstance(schemes, list) and schemes else "https"
        host = spec.get("host") or ""
        base_path = spec.get("basePath") or ""
        return f"{scheme}://{host}{base_path}" if host else None
    return None


def _build_param_schema(param: dict[str, Any]) -> dict[str, Any] | None:
    """Construit un fragment JSON Schema depuis un objet paramètre OpenAPI."""
    schema = _extract_schema(param)
    if schema is not None:
        return schema
    if "content" in param:
        for media in param["content"].values():
            if isinstance(media, dict) and "schema" in media:
                return media["schema"]
    return {"type": "string"}


def _default_name(method: str, path: str) -> str:
    path_part = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
    return f"{method}_{path_part}" if path_part else f"{method}_root"


def _collect_security(
    spec: dict[str, Any], operation: dict[str, Any]
) -> list[dict[str, list[str]]]:
    """Sécurité effective d'une opération (op > global, en 2.0 et 3.x)."""
    if "security" in operation:
        reqs = operation["security"]
    elif "security" in spec:
        reqs = spec["security"]
    else:
        return []
    if not isinstance(reqs, list):
        return []
    return [
        {str(name): list(scopes) if isinstance(scopes, list) else []}
        for req in reqs
        if isinstance(req, dict)
        for name, scopes in req.items()
    ]


def _extract_endpoints(
    spec: dict[str, Any], security_schemes: dict[str, dict[str, Any]]
) -> list[ParsedEndpoint]:
    endpoints: list[ParsedEndpoint] = []
    used_names: set[str] = set()
    methods_to_cases = {m: m.upper() for m in _HTTP_METHODS}

    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_key = method.lower()
            if method_key not in methods_to_cases or not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            base_name = make_identifier(
                operation_id or _default_name(method_key, path),
                fallback="tool",
            )
            name = ensure_unique_name(base_name, used_names)
            used_names.add(name)

            parameters: list[ParsedParameter] = []
            for param in path_item.get("parameters", []) + operation.get("parameters", []):
                if not isinstance(param, dict):
                    continue
                parameters.append(
                    ParsedParameter(
                        name=param.get("name", "unknown"),
                        in_=param.get("in", "query"),
                        required=bool(param.get("required", False)),
                        description=param.get("description"),
                        schema_=_build_param_schema(param),
                    )
                )

            request_body_schema: dict[str, Any] | None = None
            request_body_required = False
            if "requestBody" in operation and isinstance(operation["requestBody"], dict):
                body = operation["requestBody"]
                request_body_required = bool(body.get("required", False))
                for media in (body.get("content") or {}).values():
                    if isinstance(media, dict) and "schema" in media:
                        request_body_schema = media["schema"]
                        break
            elif "parameters" in path_item:
                for param in operation.get("parameters", []):
                    if isinstance(param, dict) and param.get("in") == "body":
                        request_body_schema = _extract_schema(param)
                        request_body_required = bool(param.get("required", False))

            responses: dict[str, dict[str, Any]] = {}
            for code, resp in (operation.get("responses") or {}).items():
                if not isinstance(resp, dict):
                    continue
                responses[str(code)] = {"schema": _extract_schema(resp)}

            summary = operation.get("summary")
            description = operation.get("description") or operation.get("summary")
            if isinstance(description, str) and summary and description == summary:
                description = summary

            security = _collect_security(spec, operation)
            endpoints.append(
                ParsedEndpoint(
                    method=methods_to_cases[method_key],
                    path=path,
                    operation_id=operation_id,
                    name=name,
                    summary=summary,
                    description=description,
                    parameters=parameters,
                    request_body_schema=request_body_schema,
                    request_body_required=request_body_required,
                    responses=responses,
                    security=security,
                )
            )
    return endpoints


def normalize_spec(spec: dict[str, Any]) -> ParsedSpec:
    """Normalise une spec résolue en `ParsedSpec` (liste de ParsedEndpoint)."""
    openapi_version = detect_openapi_version(spec)
    info = spec.get("info") or {}
    security_schemes = spec.get("components", {}).get("securitySchemes", {})
    endpoints = _extract_endpoints(spec, security_schemes)
    return ParsedSpec(
        raw=spec,
        openapi_version=openapi_version,
        title=info.get("title"),
        version=info.get("version"),
        base_url=_extract_base_url(spec),
        endpoints=endpoints,
    )


def normalize_spec_content(content: str) -> ParsedSpec:
    """Charge puis normalise une spec depuis son contenu texte."""
    raw = load_spec_content(content)
    return normalize_spec(raw)
