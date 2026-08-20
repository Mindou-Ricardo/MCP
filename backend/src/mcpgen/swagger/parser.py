"""Parsing des specs Swagger/OpenAPI : chargement, validation, résolution $ref."""

from __future__ import annotations

import json
from typing import Any

import httpx
import yaml

from mcpgen.swagger.validator import validate_spec


class SpecParseError(Exception):
    """Erreur de parsing de la spec."""


def detect_openapi_version(spec: dict[str, Any]) -> str:
    if "swagger" in spec:
        return str(spec["swagger"])  # "2.0"
    if "openapi" in spec:
        parts = str(spec["openapi"]).split(".")
        return ".".join(parts[:2]) + ".x"  # 3.0.3 -> 3.0.x
    raise SpecParseError("Spécification invalide : ni `swagger` ni `openapi` présent.")


def load_spec_content(content: str) -> dict[str, Any]:
    """Charge du contenu JSON ou YAML en dictionnaire."""
    if not content or not content.strip():
        raise SpecParseError("Contenu vide.")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SpecParseError(f"JSON/YAML invalide : {exc}") from exc
    if not isinstance(parsed, dict):
        raise SpecParseError("La spec doit être un objet (mapping) JSON/YAML.")
    return parsed


def fetch_spec_from_url(url: str, timeout: float = 30.0) -> str:
    """Télécharge le contenu d'une spec depuis une URL publique."""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        raise SpecParseError(f"Impossible de télécharger la spec ({url}) : {exc}") from exc


def _load_with_prance(spec: dict[str, Any]) -> dict[str, Any]:
    """Résout les $ref via prance et retourne la spec normalisée."""
    try:
        from prance import ResolvingParser
    except ImportError as exc:  # pragma: no cover
        raise SpecParseError("prance n'est pas installé.") from exc

    try:
        parser = ResolvingParser(spec_string=json.dumps(spec))
        specification = parser.specification
        if not isinstance(specification, dict):
            raise SpecParseError("La spec résolue n'est pas un objet.")
        return specification
    except SpecParseError:
        raise
    except Exception as exc:  # prance lève divers types d'erreurs
        raise SpecParseError(f"Résolution des $ref impossible : {exc}") from exc


def _json_pointer_get(document: dict[str, Any], pointer: str) -> Any:
    """Resolve une référence JSON Pointer locale (#/a/b/c)."""
    if not pointer.startswith("#/"):
        return None
    parts = pointer[2:].split("/")
    node: Any = document
    for part in parts:
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return None
    return node


def resolve_remaining_refs(document: dict[str, Any]) -> dict[str, Any]:
    """Résout les $ref restants (après prance) de façon cyclique-safe."""
    expanding: set[str] = set()

    def resolve(node: Any, pointer: str = "") -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/"):
                if ref in expanding:
                    return {"description": "(référence récursive)", "$ref": ref}
                target = _json_pointer_get(document, ref)
                if target is None:
                    return node
                if pointer == ref or target is node:
                    return node
                expanding.add(ref)
                resolved = resolve(target, pointer=ref)
                expanding.discard(ref)
                return resolved
            return {k: resolve(v, pointer) for k, v in node.items()}
        if isinstance(node, list):
            return [resolve(item, pointer) for item in node]
        return node

    return resolve(document)


def parse_and_resolve_spec(content: str) -> dict[str, Any]:
    """Charge, valide et résout une spec à partir de son contenu texte."""
    spec = load_spec_content(content)
    validate_spec(spec)
    resolved = _load_with_prance(spec)
    return resolve_remaining_refs(resolved)


def parse_spec_from_url(url: str) -> dict[str, Any]:
    """Télécharge puis parse une spec distante."""
    content = fetch_spec_from_url(url)
    return parse_and_resolve_spec(content)
