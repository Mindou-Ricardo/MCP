"""Routes : ingestion Swagger (upload fichier / URL)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from mcpgen.api.deps import get_app_settings, get_db
from mcpgen.core.config import Settings
from mcpgen.models.db_models import SwaggerSpec
from mcpgen.models.schemas import ParsedEndpointView, SpecParseResponse, SwaggerParseByUrl
from mcpgen.services.swagger_service import SwaggerService
from mcpgen.swagger.parser import SpecParseError

router = APIRouter(prefix="/api/swagger", tags=["swagger"])


def _to_view(endpoint) -> ParsedEndpointView:
    return ParsedEndpointView(
        method=endpoint.method,
        path=endpoint.path,
        name=endpoint.name,
        operation_id=endpoint.operation_id,
        summary=endpoint.summary,
        description=endpoint.description,
        security=[
            {name: list(scopes)}
            for requirement in endpoint.security
            for name, scopes in requirement.items()
        ],
    )


@router.post("/parse", response_model=SpecParseResponse, status_code=201)
async def parse_swagger(
    payload: SwaggerParseByUrl,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SpecParseResponse:
    """Parse une spec depuis une URL publique."""
    service = SwaggerService(db, settings)
    try:
        parsed, content = service.fetch_and_parse_url(payload.url)
    except (SpecParseError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    spec = service.persist(
        filename=payload.url.rsplit("/", 1)[-1], source_type="url", content=content, parsed=parsed
    )
    return _response(spec, parsed)


@router.post("/upload", response_model=SpecParseResponse, status_code=201)
async def upload_swagger(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SpecParseResponse:
    """Parse une spec à partir d'un fichier `.json` / `.yaml` uploadé."""
    content = (await file.read()).decode("utf-8", errors="replace")
    service = SwaggerService(db, settings)
    try:
        parsed = service.parse_content(file.filename or "spec.yaml", content)
    except SpecParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    spec = service.persist(
        filename=file.filename or "spec.yaml", source_type="file", content=content, parsed=parsed
    )
    return _response(spec, parsed)


@router.get("/specs", response_model=list[dict])
def list_specs(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> list[dict]:
    service = SwaggerService(db, settings)
    return [
        {
            "id": s.id,
            "filename": s.filename,
            "source_type": s.source_type,
            "title": s.title,
            "version": s.version,
            "openapi_version": s.openapi_version,
            "endpoints_count": s.endpoints_count,
            "created_at": s.created_at.isoformat(),
        }
        for s in service.list()
    ]


def _response(spec: SwaggerSpec, parsed) -> SpecParseResponse:
    return SpecParseResponse(
        spec_id=spec.id,
        filename=spec.filename,
        source_type=spec.source_type,
        title=parsed.title,
        version=parsed.version,
        openapi_version=parsed.openapi_version,
        base_url=parsed.base_url,
        endpoints=[_to_view(e) for e in parsed.endpoints],
        endpoints_count=parsed.endpoints_count,
    )
