"""Configuration des providers LLM (Mistral par défaut, extensible via LiteLLM)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderConfig:
    """Description d'un provider disponible à travers LiteLLM."""

    id: str
    display_name: str
    default_model: str
    models: list[str] = field(default_factory=list)
    env_var: str | None = None
    uses_proxy: bool = True


PROVIDERS: dict[str, ProviderConfig] = {
    "mistral": ProviderConfig(
        id="mistral",
        display_name="Mistral",
        default_model="mistral/mistral-large-latest",
        models=[
            "mistral/mistral-large-latest",
            "mistral/mistral-medium",
            "mistral/mistral-small",
        ],
        env_var="MISTRAL_API_KEY",
    ),
    "openai": ProviderConfig(
        id="openai",
        display_name="OpenAI",
        default_model="openai/gpt-4o",
        models=["openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-4-turbo"],
        env_var="OPENAI_API_KEY",
    ),
    "anthropic": ProviderConfig(
        id="anthropic",
        display_name="Anthropic",
        default_model="anthropic/claude-3-5-sonnet-latest",
        models=[
            "anthropic/claude-3-5-sonnet-latest",
            "anthropic/claude-3-5-haiku-latest",
        ],
        env_var="ANTHROPIC_API_KEY",
    ),
    "ollama": ProviderConfig(
        id="ollama",
        display_name="Ollama (local)",
        default_model="ollama/llama3.1",
        models=["ollama/llama3.1", "ollama/mistral", "ollama/qwen2.5"],
        env_var="OLLAMA_API_BASE",
        uses_proxy=False,
    ),
}


def get_provider(provider_id: str) -> ProviderConfig:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise KeyError(f"Provider inconnu : {provider_id}")
    return provider


def provider_list() -> list[dict[str, str | list[str]]]:
    """Liste des providers pour l'API (frontend)."""
    return [
        {
            "id": p.id,
            "display_name": p.display_name,
            "default_model": p.default_model,
            "models": p.models,
        }
        for p in PROVIDERS.values()
    ]
