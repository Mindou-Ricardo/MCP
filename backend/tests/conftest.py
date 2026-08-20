"""Fixtures partagées des tests backend."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mcpgen.api.main import create_app
from mcpgen.core.config import Settings


@pytest.fixture()
def tmp_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        debug=False,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        generated_servers_dir=tmp_path / "generated-servers",
        litellm_api_base="http://test-proxy:4000",
        litellm_master_key="test-key",
        log_level="WARNING",
    )


@pytest.fixture()
def app_client(tmp_settings: Settings):
    app = create_app(tmp_settings)
    with TestClient(app) as client:
        yield client


SAMPLE_OPENAPI_30 = {
    "openapi": "3.0.3",
    "info": {"title": "Petstore API", "version": "1.0.0"},
    "servers": [{"url": "https://api.example.com/v1"}],
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "Liste les animaux",
                "description": "Retourne la liste des animaux de compagnie.",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}}
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Pet"},
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "operationId": "createPet",
                "summary": "Crée un animal",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/NewPet"}}
                    },
                },
                "responses": {"201": {"description": "Créé"}},
            },
        },
        "/pets/{pet_id}": {
            "get": {
                "operationId": "getPetById",
                "parameters": [
                    {"name": "pet_id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                },
            },
            "NewPet": {
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            },
        }
    },
}

SAMPLE_SWAGGER_20 = {
    "swagger": "2.0",
    "info": {"title": "Legacy API", "version": "1.0"},
    "host": "legacy.example.com",
    "basePath": "/api",
    "schemes": ["https"],
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "parameters": [{"name": "page", "in": "query", "type": "integer", "default": 1}],
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}


@pytest.fixture()
def sample_spec_30() -> str:
    return json.dumps(SAMPLE_OPENAPI_30)


@pytest.fixture()
def sample_spec_20() -> str:
    return json.dumps(SAMPLE_SWAGGER_20)


@pytest.fixture()
def resolved_spec_30(sample_spec_30: str) -> dict:
    """Spec 3.0 avec $ref résolus (flux de production)."""
    from mcpgen.swagger.parser import parse_and_resolve_spec

    return parse_and_resolve_spec(sample_spec_30)
