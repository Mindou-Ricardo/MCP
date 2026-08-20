# AGENTS.md

Instructions destinées aux agents OpenCode travaillant sur ce dépôt.

## Commandes de vérification (fallback LSP)

Le LSP est activé via `opencode.json` (pyright, typescript-language-server).
Si les diagnostics LSP ne sont pas disponibles ou posent des problèmes de
performance, utiliser les commandes suivantes pour obtenir un feedback fiable.

### Backend (répertoire `backend/`)

```bash
# Lint Python (Ruff — format + check)
uv run ruff check src tests
uv run ruff format --check src tests

# Typecheck Python (Pyright)
uv run pyright src

# Tests
uv run pytest
```

Si `uv` n'est pas disponible, utiliser l'environnement virtuel :

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS
pip install -e ".[dev]"
ruff check src tests
pyright src
pytest
```

### Frontend (répertoire `frontend/`)

```bash
# Installer les dépendances
npm install

# Typecheck TypeScript
npx tsc --noEmit

# Lint ESLint
npx eslint src --ext .ts,.tsx

# Format (Prettier)
npx prettier --check .

# Tests
npm run test
```

## Conventions

- **Commits** : Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`).
- **Branches** : `main` (stable), `develop` (intégration), `feature/*` (fonctionnalités).
- **Python** : Python 3.11+, typage complet, no `Any` sauf si réellement nécessaire.
- **TypeScript** : React 18, strict mode activé, pas de `any` implicite.
- **Secrets** : jamais de clé API en dur ; tout passe par `.env` (voir `.env.example`).

## Points d'entrée

- Backend FastAPI : `backend/src/api/main.py`
- Frontend React : `frontend/src/main.tsx`
- Lancement local : voir `README.md` / `docker-compose.yml`