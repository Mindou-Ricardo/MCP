"""Orchestrateur de génération : templates Jinja2 -> serveur MCP exécutable."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from mcpgen.mcp_generator.tool_builder import build_tool_specs
from mcpgen.models.schemas import AuthConfig
from mcpgen.swagger.normalizer import ParsedSpec
from mcpgen.utils.names import make_identifier

_TEMPLATES_DIR = Path(__file__).parent / "templates"


@dataclass
class GenerationConfig:
    """Configuration de génération d'un serveur MCP."""

    name: str
    description: str | None = None
    base_url: str | None = None
    auth: AuthConfig = field(default_factory=AuthConfig)
    include_endpoints: list[str] | None = None
    timeout: float = 30.0
    retries: int = 2


@dataclass
class GenerationResult:
    """Résultat d'une génération."""

    output_dir: Path
    tools_count: int
    files: list[str]


class MCPGenerator:
    """Génère un serveur MCP complet, de manière déterministe."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self.env = Environment(
            loader=FileSystemLoader(templates_dir or _TEMPLATES_DIR),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            # templates générant du code Python (pas de HTML/XSS)
            autoescape=False,  # noqa: S701
        )

    def generate(
        self,
        parsed: ParsedSpec,
        config: GenerationConfig,
        output_root: Path,
    ) -> GenerationResult:
        """Génère le serveur dans `output_root/<slug>` et retourne le résultat."""
        base_url = (config.base_url or parsed.base_url or "").rstrip("/")
        if not base_url:
            raise ValueError(
                "Aucune URL cible : la spec ne définit pas de "
                "`servers`/`host` — fournir `base_url`."
            )

        tools = sorted(
            build_tool_specs(parsed.endpoints, config.include_endpoints),
            key=lambda t: (t.name, t.method, t.path),
        )
        if not tools:
            raise ValueError("Aucun endpoint sélectionné pour la génération.")

        dir_name = make_identifier(config.name.replace(" ", "_").lower(), fallback="mcp-server")
        output_dir = Path(output_root) / dir_name
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        auth_dict = {
            "type": config.auth.type,
            "header_name": config.auth.header_name,
            "api_key": config.auth.api_key,
            "username": config.auth.username,
            "password": config.auth.password,
        }
        ctx = {
            "server_name": config.name,
            "description": config.description or f"Serveur MCP pour {base_url}",
            "base_url": base_url,
            "auth": auth_dict,
            "config_json": {
                "base_url": base_url,
                "auth": auth_dict,
                "timeout": config.timeout,
                "retries": config.retries,
            },
            "timeout": config.timeout,
            "retries": config.retries,
            "tools": tools,
        }

        templates = (
            "server.py",
            "tools.py",
            "requirements.txt",
            "Dockerfile",
            "README.md",
            "config.json",
        )
        for template_name in templates:
            template = self.env.get_template(f"{template_name}.j2")
            output_dir.joinpath(template_name).write_text(template.render(**ctx), encoding="utf-8")

        return GenerationResult(
            output_dir=output_dir,
            tools_count=len(tools),
            files=sorted(p.name for p in output_dir.iterdir()),
        )
