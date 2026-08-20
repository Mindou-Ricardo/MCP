"""Tests du parsing / de la normalisation des specs Swagger/OpenAPI."""

from __future__ import annotations

import json

import pytest

from mcpgen.swagger.normalizer import normalize_spec
from mcpgen.swagger.parser import (
    SpecParseError,
    load_spec_content,
    parse_and_resolve_spec,
    resolve_remaining_refs,
)
from mcpgen.swagger.validator import SpecValidationError, validate_spec


class TestLoadAndValidate:
    def test_load_json(self):
        spec = load_spec_content('{"openapi": "3.0.0"}')
        assert spec == {"openapi": "3.0.0"}

    def test_load_yaml(self):
        spec = load_spec_content("openapi: 3.0.0\ninfo:\n  title: t\n")
        assert spec["openapi"] == "3.0.0"

    def test_load_invalid(self):
        with pytest.raises(SpecParseError):
            load_spec_content("not: [valid")

    def test_empty_content(self):
        with pytest.raises(SpecParseError):
            load_spec_content("")

    def test_validate_ok(self, sample_spec_30: str):
        validate_spec(json.loads(sample_spec_30))

    def test_validate_ok_v2(self, sample_spec_20: str):
        validate_spec(json.loads(sample_spec_20))

    def test_validate_invalid(self):
        with pytest.raises(SpecValidationError):
            validate_spec({"openapi": "3.0.0", "paths": "not-a-dict"})


class TestRefResolution:
    def test_prance_resolves_refs(self, sample_spec_30: str):
        resolved = parse_and_resolve_spec(sample_spec_30)
        assert "$ref" not in json.dumps(resolved)

    def test_remaining_refs_cycle_safe(self):
        doc = {
            "$defs": {"Node": {"type": "object", "properties": {"next": {"$ref": "#/$defs/Node"}}}},
            "root": {"$ref": "#/$defs/Node"},
        }
        resolved = resolve_remaining_refs(doc)
        # La référence récursive est conservée mais le document reste JSON-sérialisable
        json.dumps(resolved)


class TestNormalization:
    def test_openapi_v3(self, sample_spec_30: str):
        parsed = normalize_spec(json.loads(sample_spec_30))
        assert parsed.openapi_version == "3.0.x"
        assert parsed.title == "Petstore API"
        assert parsed.base_url == "https://api.example.com/v1"
        assert parsed.endpoints_count == 3

    def test_swagger_v2(self, sample_spec_20: str):
        parsed = normalize_spec(json.loads(sample_spec_20))
        assert parsed.openapi_version == "2.0"
        assert parsed.base_url == "https://legacy.example.com/api"

    def test_endpoint_names_snake_case_and_unique(self, sample_spec_30: str):
        parsed = normalize_spec(json.loads(sample_spec_30))
        names = [e.name for e in parsed.endpoints]
        assert "list_pets" in names
        assert "create_pet" in names
        assert "get_pet_by_id" in names
        assert len(names) == len(set(names))

    def test_path_params_required(self, sample_spec_30: str):
        parsed = normalize_spec(json.loads(sample_spec_30))
        get_by_id = next(e for e in parsed.endpoints if e.name == "get_pet_by_id")
        pet_param = next(p for p in get_by_id.parameters if p.name == "pet_id")
        assert pet_param.in_ == "path"
        assert pet_param.required is True

    def test_body_schema(self, resolved_spec_30: dict):
        parsed = normalize_spec(resolved_spec_30)
        create = next(e for e in parsed.endpoints if e.name == "create_pet")
        assert create.request_body_schema is not None
        assert create.request_body_required is True
        assert create.request_body_schema["required"] == ["name"]

    def test_methods_upper(self, sample_spec_30: str):
        parsed = normalize_spec(json.loads(sample_spec_30))
        assert {e.method for e in parsed.endpoints} == {"GET", "POST"}
