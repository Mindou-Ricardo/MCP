"""Tests du générateur MCP (tool_builder, generator, packager)."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from mcpgen.mcp_generator.generator import GenerationConfig, MCPGenerator
from mcpgen.mcp_generator.packager import pack_server
from mcpgen.mcp_generator.tool_builder import build_input_schema, build_tool_spec
from mcpgen.models.schemas import AuthConfig
from mcpgen.swagger.normalizer import normalize_spec
from tests.conftest import SAMPLE_OPENAPI_30


def _parsed():
    return normalize_spec(SAMPLE_OPENAPI_30)


class TestToolBuilder:
    def test_input_schema_valid_json_schema(self):
        endpoint = _parsed().endpoints[0]
        schema = build_input_schema(endpoint)
        assert schema["type"] == "object"
        assert "properties" in schema
        json.dumps(schema)  # sérialisable

    def test_path_param_in_required(self):
        parsed = _parsed()
        endpoint = next(e for e in parsed.endpoints if e.name == "get_pet_by_id")
        schema = build_input_schema(endpoint)
        assert "pet_id" in schema["properties"]
        assert "pet_id" in schema["required"]

    def test_body_is_required_when_required(self):
        parsed = _parsed()
        endpoint = next(e for e in parsed.endpoints if e.name == "create_pet")
        schema = build_input_schema(endpoint)
        assert "body" in schema["properties"]
        assert "body" in schema["required"]

    def test_query_optional_not_required(self):
        parsed = _parsed()
        endpoint = next(e for e in parsed.endpoints if e.name == "list_pets")
        schema = build_input_schema(endpoint)
        assert "limit" in schema["properties"]
        assert "limit" not in schema["required"]

    def test_build_tool_spec(self):
        parsed = _parsed()
        endpoint = next(e for e in parsed.endpoints if e.name == "list_pets")
        spec = build_tool_spec(endpoint)
        assert spec.name == "list_pets"
        assert spec.method == "GET"
        assert spec.path == "/pets"
        assert "Liste les animaux" in spec.description
        assert spec.query_params == ["limit"]


class TestGenerator:
    def test_generate_is_deterministic(self, tmp_path: Path):
        generator = MCPGenerator()
        config = GenerationConfig(
            name="petstore-server",
            description="Serveur de test",
            base_url="https://api.example.com/v1",
        )
        result1 = generator.generate(_parsed(), config, tmp_path)
        tools1 = (result1.output_dir / "tools.py").read_text(encoding="utf-8")
        server1 = (result1.output_dir / "server.py").read_text(encoding="utf-8")
        config1 = (result1.output_dir / "config.json").read_text(encoding="utf-8")

        result2 = generator.generate(_parsed(), config, tmp_path)
        tools2 = (result2.output_dir / "tools.py").read_text(encoding="utf-8")
        server2 = (result2.output_dir / "server.py").read_text(encoding="utf-8")
        config2 = (result2.output_dir / "config.json").read_text(encoding="utf-8")

        assert tools1 == tools2
        assert server1 == server2
        assert config1 == config2
        assert result1.tools_count == 3

    def test_generate_requires_base_url(self, tmp_path: Path):
        generator = MCPGenerator()
        parsed = normalize_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "x"},
                "paths": {"/a": {"get": {"responses": {}}}},
            }
        )
        with pytest.raises(ValueError, match="URL cible"):
            generator.generate(parsed, GenerationConfig(name="no-url"), tmp_path)

    def test_generate_include_endpoints(self, tmp_path: Path):
        generator = MCPGenerator()
        config = GenerationConfig(
            name="subset",
            base_url="https://api.example.com",
            include_endpoints=["list_pets"],
        )
        result = generator.generate(_parsed(), config, tmp_path)
        assert result.tools_count == 1
        tools_py = (result.output_dir / "tools.py").read_text(encoding="utf-8")
        assert '"name": "list_pets"' in tools_py
        assert '"name": "create_pet"' not in tools_py

    def test_generated_files_present(self, tmp_path: Path):
        generator = MCPGenerator()
        result = generator.generate(
            _parsed(), GenerationConfig(name="files-check", base_url="https://x.test"), tmp_path
        )
        expected = {
            "Dockerfile",
            "README.md",
            "config.json",
            "requirements.txt",
            "server.py",
            "tools.py",
        }
        assert expected <= set(result.files)

    def test_auth_embedded_in_config(self, tmp_path: Path):
        generator = MCPGenerator()
        auth = AuthConfig(type="bearer", api_key="sk-test")
        result = generator.generate(
            _parsed(),
            GenerationConfig(name="auth-check", base_url="https://x.test", auth=auth),
            tmp_path,
        )
        config = json.loads((result.output_dir / "config.json").read_text(encoding="utf-8"))
        assert config["auth"]["type"] == "bearer"
        assert config["auth"]["api_key"] == "sk-test"


class TestPackager:
    def test_pack_server(self, tmp_path: Path):
        source = tmp_path / "my-server"
        source.mkdir()
        (source / "server.py").write_text("print('hello')", encoding="utf-8")
        target = tmp_path / "archive"
        target.mkdir()
        zip_path = pack_server(source, target / "my-server.zip")
        assert zip_path.exists()
        with ZipFile(zip_path) as archive:
            names = archive.namelist()
            assert "my-server/server.py" in names
