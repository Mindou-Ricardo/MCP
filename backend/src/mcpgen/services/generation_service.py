"""Service de génération : ParsedSpec -> serveur MCP persisté sur disque."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from sqlalchemy.orm import sessionmaker

from mcpgen.core.config import Settings
from mcpgen.core.logging import get_logger
from mcpgen.mcp_generator.generator import GenerationConfig, MCPGenerator
from mcpgen.mcp_generator.packager import pack_server
from mcpgen.models.db_models import GeneratedServer, ServerStatus, SwaggerSpec
from mcpgen.models.schemas import AuthConfig, ServerCreateRequest
from mcpgen.swagger.normalizer import ParsedEndpoint, ParsedSpec
from mcpgen.swagger.parser import parse_and_resolve_spec

logger = get_logger(__name__)


class ServerNameTakenError(Exception):
    pass


class GeneratedServerNotFoundError(Exception):
    pass


class GenerationService:
    """CRUD + génération des serveurs MCP."""

    def __init__(self, session_factory: sessionmaker, settings: Settings) -> None:
        self.session_factory = session_factory
        self.settings = settings

    @property
    def servers_dir(self) -> Path:
        return Path(self.settings.generated_servers_dir)

    # ------------------------------------------------------------------ helpers

    def _rebuild(self, spec: SwaggerSpec) -> ParsedSpec:
        from mcpgen.swagger.normalizer import normalize_spec

        resolved = parse_and_resolve_spec(spec.content)
        return normalize_spec(resolved)

    def _endpoints_json(self, parsed: ParsedSpec, include: list[str] | None) -> str:
        selected = parsed.endpoints
        if include is not None:
            allowed = set(include)
            selected = [e for e in selected if e.name in allowed]
        return json.dumps(
            [e.model_dump(by_alias=True) for e in selected],
            ensure_ascii=False,
        )

    @staticmethod
    def _auth_config_to_dict(auth) -> dict[str, Any]:
        return {
            "type": auth.type,
            "header_name": auth.header_name,
            "api_key": auth.api_key,
            "username": auth.username,
            "password": auth.password,
        }

    @staticmethod
    def parse_endpoints(endpoints_json: str | None) -> list[ParsedEndpoint]:
        if not endpoints_json:
            return []
        return [ParsedEndpoint.model_validate(item) for item in json.loads(endpoints_json)]

    # ------------------------------------------------------------------ CRUD

    def create(self, request: ServerCreateRequest, spec: SwaggerSpec) -> GeneratedServer:
        with self.session_factory() as session:
            existing = session.query(GeneratedServer).filter_by(name=request.name).first()
            if existing is not None:
                raise ServerNameTakenError(f"Un serveur nommé '{request.name}' existe déjà")

            parsed = self._rebuild(spec)
            endpoints_json = self._endpoints_json(parsed, request.include_endpoints)
            server = GeneratedServer(
                name=request.name,
                description=request.description,
                base_url=request.base_url or parsed.base_url,
                auth_type=request.auth.type,
                auth_config=json.dumps(self._auth_config_to_dict(request.auth)),
                endpoints=endpoints_json,
                endpoints_count=len(self.parse_endpoints(endpoints_json)),
                status=ServerStatus.pending,
                spec_id=spec.id,
            )
            session.add(server)
            session.commit()
            session.refresh(server)
            return server

    def run_generation(self, server_id: int) -> None:
        """Génère (en tâche de fond) le serveur MCP pour l'id donné."""
        with self.session_factory() as session:
            server = session.get(GeneratedServer, server_id)
            if server is None:
                logger.error(
                    "generation_failed",
                    extra={
                        "extra_fields": {
                            "server_id": server_id,
                            "reason": "not_found",
                        }
                    },
                )
                return
            server.status = ServerStatus.generating
            server.error = None
            session.commit()
        try:
            self._generate_files(server_id)
            with self.session_factory() as session:
                server = session.get(GeneratedServer, server_id)
                server.status = ServerStatus.ready
                session.commit()
            logger.info("server_generated", extra={"extra_fields": {"server_id": server_id}})
        except Exception as exc:  # noqa: BLE001 - erreur reportée en base
            logger.exception("generation_failed")
            with self.session_factory() as session:
                server = session.get(GeneratedServer, server_id)
                server.status = ServerStatus.failed
                server.error = str(exc)[:2000]
                session.commit()

    def _generate_files(self, server_id: int) -> None:
        with self.session_factory() as session:
            server = session.get(GeneratedServer, server_id)
            if server is None or server.spec is None:
                raise ValueError("Serveur ou spec introuvable")
            spec = server.spec
            parsed = self._rebuild(spec)
            endpoints = self.parse_endpoints(server.endpoints)
            include = [e.name for e in endpoints]
            auth = json.loads(server.auth_config or "{}")
            config = GenerationConfig(
                name=server.name,
                description=server.description,
                base_url=server.base_url or parsed.base_url,
                auth=AuthConfig(
                    type=auth.get("type", "none"),
                    header_name=auth.get("header_name"),
                    api_key=auth.get("api_key"),
                    username=auth.get("username"),
                    password=auth.get("password"),
                ),
                include_endpoints=include,
                timeout=30.0,
                retries=2,
            )
            result = MCPGenerator().generate(parsed, config, self.servers_dir)
            server.dir_name = result.output_dir.name
            session.commit()

    def get(self, server_id: int) -> GeneratedServer:
        with self.session_factory() as session:
            server = session.get(GeneratedServer, server_id)
            if server is None:
                raise GeneratedServerNotFoundError(f"Serveur {server_id} introuvable")
            session.expunge(server)
            return server

    def list(self) -> list[GeneratedServer]:
        with self.session_factory() as session:
            return session.query(GeneratedServer).order_by(GeneratedServer.created_at.desc()).all()

    def delete(self, server_id: int) -> None:
        with self.session_factory() as session:
            server = session.get(GeneratedServer, server_id)
            if server is None:
                raise GeneratedServerNotFoundError(f"Serveur {server_id} introuvable")
            if server.dir_name:
                shutil.rmtree(self.servers_dir / server.dir_name, ignore_errors=True)
            session.delete(server)
            session.commit()

    def server_dir(self, server: GeneratedServer) -> Path:
        if not server.dir_name:
            raise FileNotFoundError("Le serveur n'a pas encore été généré")
        path = self.servers_dir / server.dir_name
        if not path.is_dir():
            raise FileNotFoundError(f"Dossier du serveur introuvable : {path}")
        return path

    def zip_path(self, server: GeneratedServer) -> Path:
        return pack_server(self.server_dir(server))
