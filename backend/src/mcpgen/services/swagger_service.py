"""Service métier de parsing / persistance des specs Swagger."""

from __future__ import annotations

from sqlalchemy.orm import Session

from mcpgen.core.config import Settings
from mcpgen.models.db_models import SwaggerSpec
from mcpgen.swagger.normalizer import ParsedSpec
from mcpgen.swagger.parser import (
    SpecParseError,
    parse_and_resolve_spec,
    parse_spec_from_url,
)


class SwaggerSpecNotFoundError(Exception):
    pass


class SwaggerService:
    """Ingestion de specs Swagger/OpenAPI (upload ou URL) + persistance."""

    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def parse_content(self, filename: str, content: str) -> ParsedSpec:
        try:
            resolved = parse_and_resolve_spec(content)
        except (SpecParseError, ValueError) as exc:
            raise SpecParseError(str(exc)) from exc
        from mcpgen.swagger.normalizer import normalize_spec

        return normalize_spec(resolved)

    def parse_url(self, url: str) -> ParsedSpec:
        resolved = parse_spec_from_url(url)
        from mcpgen.swagger.normalizer import normalize_spec

        return normalize_spec(resolved)

    def fetch_and_parse_url(self, url: str) -> tuple[ParsedSpec, str]:
        """Télécharge, parse et retourne (ParsedSpec, contenu brut) pour persistance."""
        from mcpgen.swagger.parser import fetch_spec_from_url

        content = fetch_spec_from_url(url)
        return self.parse_content(url.rsplit("/", 1)[-1], content), content

    def persist(
        self,
        filename: str,
        source_type: str,
        content: str,
        parsed: ParsedSpec,
    ) -> SwaggerSpec:
        spec = SwaggerSpec(
            filename=filename,
            source_type=source_type,
            content=content,
            title=parsed.title,
            version=parsed.version,
            openapi_version=parsed.openapi_version,
            base_url=parsed.base_url,
            endpoints_count=parsed.endpoints_count,
        )
        self.session.add(spec)
        self.session.commit()
        self.session.refresh(spec)
        return spec

    def get(self, spec_id: int) -> SwaggerSpec:
        spec = self.session.get(SwaggerSpec, spec_id)
        if spec is None:
            raise SwaggerSpecNotFoundError(f"Spec {spec_id} introuvable")
        return spec

    def list(self) -> list[SwaggerSpec]:
        return self.session.query(SwaggerSpec).order_by(SwaggerSpec.created_at.desc()).all()
