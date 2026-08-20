# 🧩 MCP Generator

> À partir d'une spécification **Swagger/OpenAPI (2.0 / 3.x)** fournie par upload de fichier
> (JSON/YAML) ou par URL, cette application génère automatiquement un **serveur MCP fonctionnel**
> exposant chaque endpoint de l'API comme un **tool MCP**, testable directement dans une interface
> de chat connectée à **LiteLLM** (provider par défaut : **Mistral**).

## Fonctionnalités

- **Ingestion Swagger** : upload `.json`/`.yaml` ou URL publique, validation OpenAPI 2.0/3.0/3.1,
  résolution `$ref` (prance) et normalisation.
- **Génération de serveur MCP** : chaque endpoint devient un tool MCP (`input_schema` JSON Schema),
  handler HTTP réel (auth, timeout, retries). Code généré exportable en zip et exécutable en local
  ou avec Docker.
- **Playground de chat** : interface de chat branchée sur LiteLLM (Mistral par défaut, extensible
  OpenAI / Anthropic / Ollama). Affichage en streaming des deltas, des tool calls et des réponses
  de l'API réelle.
- **Frontend React** (Vite + Tailwind) : import de spec, prévisualisation filtrable des endpoints,
  configuration du serveur, statut de génération en temps réel (SSE), liste des serveurs
  (téléchargement / régénération / suppression), playground.
- **Conteneurisation** : Docker multi-stage + Docker Compose (`backend`, `frontend`,
  `litellm-proxy`, `db` optionnel en profil Postgres).

## Architecture

```
Swagger/OpenAPI ─▶ Parser+Validator ─▶ Normalizer ─▶ Générateur MCP ─▶ Serveur MCP (code + zip)
       (upload/URL)    (prance/$ref)      (endpoints)    (Jinja2)          │
                                                          │                ▼
                                                          │          Playground (chat)
                                                          └────────▶ LiteLLM ─▶ Mistral
```

Schéma détaillé (Mermaid) : voir [docs/architecture.md](docs/architecture.md).

## Quickstart (Docker)

```bash
cp .env.example .env
# Renseigner MISTRAL_API_KEY (et éventuellement LITELLM_MASTER_KEY)

docker compose up --build
```

Puis :

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 (dev) / http://localhost:8080 (prod-like) |
| Backend API (Swagger UI) | http://localhost:8000/docs |
| LiteLLM proxy | http://localhost:4000 |

> `docker-compose.override.yml` est appliqué automatiquement pour le développement
> (hot reload backend + Vite). Pour un run sans override : `docker compose -f docker-compose.yml up`.

### Sans Docker (développement local)

```bash
# Backend (à la racine de backend/)
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
uvicorn mcpgen.api.main:app --reload

# LiteLLM (optionnel, sinon le backend utilise LITELLM_API_BASE)
docker run -p 4000:4000 -v ./litellm/config.yaml:/app/config.yaml -e MISTRAL_API_KEY=... ghcr.io/berriai/litellm:main-stable --config /app/config.yaml

# Frontend (à la racine de frontend/)
npm install
npm run dev
```

## Variables d'environnement

Voir [.env.example](.env.example). Les plus importantes :

| Variable | Description | Défaut |
|---|---|---|
| `MISTRAL_API_KEY` | Clé Mistral (provider par défaut) | — |
| `LITELLM_API_BASE` | URL du proxy LiteLLM | `http://litellm-proxy:4000` |
| `LITELLM_MASTER_KEY` | Clé maître du proxy LiteLLM | `sk-mcp-master-key...` |
| `LITELLM_MODEL` | Modèle par défaut | `mistral/mistral-large-latest` |
| `DATABASE_URL` | URL SQLAlchemy (SQLite par défaut, Postgres possible) | `sqlite:///./mcp_generator.db` |
| `CORS_ORIGINS` | Origines CORS autorisées | `http://localhost:5173,...` |
| `GENERATED_SERVERS_DIR` | Dossier des serveurs générés | `./generated-servers` |

**Sécurité** : aucune clé API en dur — tout passe par `.env` (jamais committé).
Le fournisseur LLM se change dans `litellm/config.yaml`, sans toucher au code métier.

## Exemple de flux d'utilisation

1. Ouvrir http://localhost:5173 → importer une spec (ex. Petstore) ou saisir une URL.
2. La liste des endpoints détectés s'affiche → configurer nom, URL cible, auth, endpoints inclus.
3. « Générer le serveur MCP » → statut de génération en temps réel (SSE).
4. Depuis la page **Serveurs** : télécharger le zip, régénérer, supprimer ou **tester dans le playground**.
5. Dans le playground, discuter avec Mistral : le LLM peut appeler les tools MCP générés
   (l'appel HTTP réel vers l'API cible est exécuté et le résultat est affiché).

## Tests & qualité

```bash
# Backend
cd backend && uv run pytest && uv run ruff check src tests && uv run pyright src

# Frontend
cd frontend && npm run test && npm run lint && npx tsc --noEmit && npm run format:check
```

CI : lints, tests et build des images sur chaque push (voir `.github/workflows/`).

## Structure du dépôt

```
backend/      FastAPI + parsing Swagger + générateur MCP + LiteLLM (Python)
frontend/     React 18 + TypeScript + Vite + Tailwind
litellm/      config.yaml du proxy LiteLLM (Mistral par défaut)
docs/         architecture (Mermaid) + API
.github/      CI GitHub Actions
docker-compose.yml + override dev
```

## Conventions

- **Commits** : Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, …).
- **Branches** : `main` (stable), `develop` (intégration), `feature/*`.
- **OpenCode/LSP** : config du LSP dans `opencode.json`, commandes de fallback dans `AGENTS.md`.

## Licence

MIT — voir [LICENSE](LICENSE).