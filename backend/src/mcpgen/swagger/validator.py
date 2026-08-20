"""Validation des specs Swagger/OpenAPI (2.0, 3.0, 3.1+)."""

from __future__ import annotations

from typing import Any

from openapi_spec_validator import (
    OpenAPIV2SpecValidator,
    OpenAPIV30SpecValidator,
    OpenAPIV31SpecValidator,
    OpenAPIV32SpecValidator,
)


class SpecValidationError(Exception):
    """La spec ne respecte pas le schéma OpenAPI."""


_VALIDATOR_BY_MAJOR_MINOR = {
    "2.0": OpenAPIV2SpecValidator,
    "3.0": OpenAPIV30SpecValidator,
    "3.1": OpenAPIV31SpecValidator,
    "3.2": OpenAPIV32SpecValidator,
}


def _detect_version(spec: dict[str, Any]) -> str:
    if "swagger" in spec:
        return str(spec["swagger"])
    if "openapi" in spec:
        parts = str(spec["openapi"]).split(".")
        return ".".join(parts[:2])
    raise SpecValidationError("Spécification invalide : ni `swagger` ni `openapi` présent.")


def validate_spec(spec: dict[str, Any]) -> None:
    """Valide une spec (Swagger 2.0 / OpenAPI 3.0 / 3.1 / 3.2).

    Lève `SpecValidationError` si la spec est invalide ou non supportée.
    """
    version = _detect_version(spec)
    validator_class = _VALIDATOR_BY_MAJOR_MINOR.get(version)
    if validator_class is None:
        raise SpecValidationError(f"Version OpenAPI non supportée : {version}")

    errors: list[str] = []
    try:
        validator_class(spec).validate()
    except Exception as exc:
        raw_errors = getattr(exc, "errors", None) or [exc]
        errors = [str(error) for error in raw_errors]
        raise SpecValidationError(
            f"Spec OpenAPI {version} invalide : {'; '.join(errors) or exc}"
        ) from exc
