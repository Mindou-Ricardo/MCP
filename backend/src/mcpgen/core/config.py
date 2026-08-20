"""Configuration centralisée de l'application (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs, chargés depuis l'environnement / fichier .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "MCP Generator"
    app_env: str = "development"
    debug: bool = True
    backend_host: str = "0.0.0.0"  # noqa: S104 - hôte d'écoute par défaut (dockérable)
    backend_port: int = 8000
    log_level: str = "INFO"

    # Base de données
    database_url: str = "sqlite:///./mcp_generator.db"

    # Serveurs générés
    generated_servers_dir: Path = Path("./generated-servers")

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:80,http://localhost"

    # Sécurité
    secret_key: str = "change-me-in-production"  # noqa: S105 - remplacé par .env en prod
    access_token_expire_minutes: int = 60
    api_key: str | None = None

    # LiteLLM
    litellm_api_base: str = "http://litellm-proxy:4000"
    litellm_master_key: str = "sk-mcp-master-key-change-me"
    litellm_model: str = "mistral/mistral-large-latest"
    litellm_timeout: int = 120

    # Clés de providers LLM (never hardcoded, toujours via .env)
    mistral_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_api_base: str = "http://localhost:11434"

    @property
    def cors_origin_list(self) -> list[str]:
        """Liste des origines CORS autorisées."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance unique des settings."""
    return Settings()
