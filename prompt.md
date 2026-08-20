# Prompt — Générateur de serveurs MCP à partir d'une spec Swagger/OpenAPI

## Rôle

Tu es un **ingénieur fullstack senior spécialisé en IA générative et en Model Context Protocol (MCP)**. Tu dois concevoir et livrer un projet complet, prêt à être poussé sur `https://github.com/Mindou-Ricardo/MCP.git`, dont le but est le suivant :

> À partir d'une spécification **Swagger/OpenAPI (2.0 ou 3.x)** fournie par l'utilisateur (upload de fichier JSON/YAML ou URL), l'application génère automatiquement un **serveur MCP fonctionnel** exposant chaque endpoint de l'API comme un **tool MCP**, testable directement dans une interface de chat connectée à **LiteLLM** (provider par défaut : **Mistral**).

Le livrable final doit être un monorepo complet : backend, frontend, conteneurisation Docker, documentation et configuration Git.

---

## Stack technique imposée

| Composant | Choix |
|---|---|
| Backend | Python 3.11+, FastAPI, SDK officiel `mcp` (Model Context Protocol) |
| Parsing Swagger | `openapi-spec-validator` + `prance` (ou équivalent) pour résoudre les `$ref` |
| Génération de code | Templates Jinja2 → génère le serveur MCP (tools, schemas, handlers HTTP) |
| Orchestration LLM | LiteLLM (proxy ou SDK Python) |
| Provider LLM par défaut | Mistral (clé API via variable d'env `MISTRAL_API_KEY`), architecture pensée pour rester agnostique (OpenAI, Anthropic, Ollama en fallback via LiteLLM) |
| Frontend | React 18 + TypeScript + Vite, TailwindCSS |
| Communication front/back | REST (FastAPI) + WebSocket ou SSE pour le streaming des réponses du chat/playground |
| Conteneurisation | Docker multi-stage + Docker Compose (services : backend, frontend, litellm-proxy, éventuellement redis pour le cache des specs) |
| Tests | Pytest (backend), Vitest/React Testing Library (frontend) |
| Qualité de code | Ruff/Black (Python), ESLint/Prettier (TS) |
| CI | GitHub Actions (lint + tests + build docker) |
| Dépôt Git | `https://github.com/Mindou-Ricardo/MCP.git` |

---

## Environnement de développement — OpenCode & LSP

Le code sera généré et maintenu via **OpenCode**. Le LSP (Language Server Protocol) doit être **activé** dès l'initialisation du projet afin que l'agent dispose de diagnostics temps réel (erreurs de typage, imports invalides, etc.) sur le code Python et TypeScript généré.

- Créer un fichier de config `opencode.json` (ou `opencode.jsonc`) **à la racine du repo**, avec le schéma officiel :

```json
{
  "$schema": "https://opencode.ai/config.json",
  "lsp": {
    "pyright": {
      "command": ["pyright-langserver", "--stdio"],
      "extensions": [".py"]
    },
    "typescript": {
      "command": ["typescript-language-server", "--stdio"],
      "extensions": [".ts", ".tsx"]
    }
  }
}
```

- Alternative rapide : `"lsp": true` pour activer tous les serveurs LSP intégrés (Python/pyright, TypeScript, etc.) sans configuration fine.
- S'assurer que les dépendances des serveurs LSP sont disponibles dans l'environnement de dev :
  - Backend : `pyright` (via `pip`/`npm`) ou équivalent, cohérent avec `pyproject.toml`/Ruff.
  - Frontend : `typescript-language-server` + `typescript` (déjà présent comme devDependency Vite/TS).
- Documenter dans le `README.md` (section "Développement") comment activer/désactiver le LSP, et préciser que si les diagnostics LSP posent un problème de perf, l'agent doit se rabattre sur les commandes CLI de lint/typecheck du projet (`ruff check`, `mypy`, `tsc --noEmit`, `eslint`) — à documenter également dans un fichier `AGENTS.md` à la racine, pour qu'OpenCode sache quelles commandes exécuter pour obtenir un feedback fiable.
- Ajouter `opencode.json` et `AGENTS.md` à la structure de répertoires (voir ci-dessous), et les committer (pas de secrets dedans, donc pas de `.gitignore` nécessaire pour ces fichiers).

---

## Fonctionnalités attendues

### 1. Ingestion Swagger
- Upload d'un fichier `.json`/`.yaml` OU saisie d'une URL publique.
- Validation de la spec (OpenAPI 2.0 et 3.0/3.1).
- Résolution des `$ref` et normalisation en un modèle interne (`ParsedEndpoint`).
- Extraction : path, méthode HTTP, paramètres (query/path/header/body), schémas de requête/réponse, sécurité (API Key, Bearer, OAuth2 basique).

### 2. Génération du serveur MCP
- Chaque endpoint devient un **tool MCP** avec :
  - Nom normalisé (snake_case, dérivé de `operationId` ou path+méthode).
  - `input_schema` JSON généré depuis les paramètres/body.
  - Description reprise du `summary`/`description` OpenAPI.
  - Handler qui exécute l'appel HTTP réel vers l'API cible (avec gestion auth, headers, timeout, retries).
- Génération d'un serveur MCP conforme au protocole (stdio ET/OU transport HTTP/SSE selon le SDK `mcp`).
- Le code généré est **exportable** (zip / dossier) et **exécutable directement en local** ou packagé en image Docker autonome.
- Persistance des serveurs générés (métadonnées + config) en base (SQLite par défaut, migration facile vers Postgres).

### 3. Playground de test (LiteLLM + Mistral)
- Interface de chat dans le frontend permettant de discuter avec un LLM (via LiteLLM) qui a accès aux tools du serveur MCP généré.
- Sélecteur de provider/modèle (Mistral par défaut, extensible).
- Affichage des tool calls, arguments envoyés, réponse de l'API réelle.
- Configuration des clés API via `.env`, jamais en dur ni committées.

### 4. Frontend
- Page d'upload/import de la spec Swagger.
- Vue de prévisualisation des endpoints détectés (tableau filtrable, statut de génération).
- Formulaire de configuration du serveur MCP (nom, base URL cible, méthode d'auth, endpoints à inclure/exclure).
- Bouton "Générer" → appel au backend → statut en temps réel (WebSocket/SSE).
- Liste des serveurs MCP déjà générés, avec actions : télécharger, relancer, supprimer, tester dans le playground.
- Playground de chat (voir point 3).

### 5. Docker & déploiement
- `Dockerfile` multi-stage pour le backend (build + runtime allégé).
- `Dockerfile` multi-stage pour le frontend (build Vite → Nginx).
- `docker-compose.yml` à la racine orchestrant : `backend`, `frontend`, `litellm-proxy`, `db` (optionnel), avec réseau dédié et volumes pour les serveurs générés.
- Fichier `.env.example` documentant toutes les variables (`MISTRAL_API_KEY`, `LITELLM_MASTER_KEY`, `DATABASE_URL`, etc.).

### 6. Git & documentation
- Initialiser le repo avec remote `https://github.com/Mindou-Ricardo/MCP.git`.
- `.gitignore` excluant : `node_modules`, `__pycache__`, `.env`, `generated-servers/*` (sauf `.gitkeep`), `dist/`, `*.db`.
- `README.md` complet : présentation, architecture, quickstart (`docker compose up`), variables d'environnement, exemples d'usage.
- `docs/architecture.md` avec un schéma (Mermaid) du flux : Swagger → Parser → Générateur MCP → Serveur MCP → LiteLLM/Mistral → Chat.
- Convention de commits (Conventional Commits) et structure de branches (`main`, `develop`, `feature/*`).

---

## Structure de répertoires attendue

```
MCP/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py                 # point d'entrée FastAPI
│   │   │   ├── routes/
│   │   │   │   ├── swagger.py          # upload / parsing spec
│   │   │   │   ├── generate.py         # génération du serveur MCP
│   │   │   │   ├── servers.py          # CRUD serveurs générés
│   │   │   │   └── chat.py             # endpoint playground (LiteLLM)
│   │   │   └── deps.py                 # dépendances FastAPI (auth, db session...)
│   │   ├── core/
│   │   │   ├── config.py               # settings (pydantic-settings)
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── swagger/
│   │   │   ├── parser.py               # parsing + résolution $ref
│   │   │   ├── normalizer.py           # -> ParsedEndpoint
│   │   │   └── validator.py
│   │   ├── mcp_generator/
│   │   │   ├── generator.py            # orchestrateur de génération
│   │   │   ├── tool_builder.py         # endpoint -> tool MCP
│   │   │   ├── templates/              # templates Jinja2 du serveur MCP
│   │   │   │   ├── server.py.j2
│   │   │   │   ├── tools.py.j2
│   │   │   │   └── Dockerfile.j2
│   │   │   └── packager.py             # zip / dossier exportable
│   │   ├── llm/
│   │   │   ├── litellm_client.py       # wrapper LiteLLM
│   │   │   └── providers.py            # config Mistral (+ autres)
│   │   ├── models/
│   │   │   ├── db_models.py            # SQLAlchemy
│   │   │   └── schemas.py              # Pydantic (DTO API)
│   │   ├── services/
│   │   │   ├── swagger_service.py
│   │   │   ├── generation_service.py
│   │   │   └── chat_service.py
│   │   └── utils/
│   ├── tests/
│   │   ├── test_parser.py
│   │   ├── test_generator.py
│   │   └── test_chat.py
│   ├── generated-servers/              # sortie des serveurs MCP générés (gitignore)
│   │   └── .gitkeep
│   ├── requirements.txt / pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   └── alembic/                        # migrations DB (si Postgres)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SwaggerUpload/
│   │   │   ├── EndpointsTable/
│   │   │   ├── ServerConfigForm/
│   │   │   ├── ServersList/
│   │   │   └── ChatPlayground/
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── GeneratePage.tsx
│   │   │   ├── ServersPage.tsx
│   │   │   └── PlaygroundPage.tsx
│   │   ├── services/
│   │   │   ├── api.ts                  # client REST backend
│   │   │   └── ws.ts                   # client WebSocket/SSE
│   │   ├── hooks/
│   │   ├── store/                      # état global (Zustand/Redux)
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── .env.example
│
├── litellm/
│   └── config.yaml                     # config LiteLLM (modèles, routing, provider Mistral par défaut)
│
├── docs/
│   ├── architecture.md
│   └── api.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── docker-build.yml
│
├── docker-compose.yml
├── docker-compose.override.yml         # config dev (hot reload)
├── .env.example
├── .gitignore
├── opencode.json                       # config LSP OpenCode (pyright, typescript-language-server...)
├── AGENTS.md                           # commandes lint/typecheck/tests pour l'agent OpenCode
├── LICENSE
└── README.md
```

---

## Contraintes techniques à respecter

1. **Sécurité** : aucune clé API en dur dans le code ; tout passe par `.env` / secrets Docker. Le `.env` réel ne doit jamais être committé (seul `.env.example`).
2. **Idempotence** : régénérer un serveur MCP à partir de la même spec doit produire un résultat déterministe.
3. **Extensibilité provider** : LiteLLM doit être configuré pour que changer de provider (Mistral → OpenAI/Anthropic/Ollama) ne nécessite qu'une modification de config (`litellm/config.yaml`), sans toucher au code métier.
4. **Conformité MCP** : respecter strictement le schéma des tools (JSON Schema valide pour `input_schema`) et le protocole d'échange du SDK officiel `mcp`.
5. **Découplage** : le module de parsing Swagger et le module de génération MCP doivent être testables indépendamment du framework web (pas de dépendance directe à FastAPI dans `swagger/` et `mcp_generator/`).
6. **Observabilité** : logs structurés (JSON) côté backend, et exposition d'un endpoint `/health`.
7. **Outillage OpenCode/LSP** : le LSP doit être actif (`opencode.json`) dès le début du développement pour que les diagnostics (typage, imports, erreurs de syntaxe) remontent en continu à l'agent pendant la génération du code ; les commandes de fallback (lint/typecheck/tests) doivent être listées dans `AGENTS.md`.

---

## Instructions d'exécution (étapes à suivre par le LLM codeur)

1. Initialiser le dépôt local et configurer le remote `https://github.com/Mindou-Ricardo/MCP.git`.
2. Créer la structure de répertoires ci-dessus (fichiers vides ou stubs si nécessaire), en incluant `opencode.json` (LSP activé pour Python/TypeScript) et `AGENTS.md` (commandes de lint/typecheck/tests à disposition de l'agent OpenCode).
3. Implémenter le backend dans cet ordre : `core/config.py` → `swagger/` (parser + validator) → `models/` → `mcp_generator/` (templates puis générateur) → `llm/` (client LiteLLM + config Mistral) → `api/routes/` → tests.
4. Implémenter le frontend dans cet ordre : setup Vite/Tailwind → `services/api.ts` → composants d'upload/preview → formulaire de génération → liste des serveurs → playground de chat.
5. Écrire les `Dockerfile` (backend, frontend) et le `docker-compose.yml`, avec un service `litellm-proxy` basé sur l'image officielle LiteLLM et `litellm/config.yaml` pointant sur Mistral par défaut.
6. Rédiger le `README.md` et `docs/architecture.md`.
7. Ajouter les workflows CI GitHub Actions (lint, tests, build des images).
8. Vérifier le tout avec `docker compose up --build` : upload d'un Swagger de test → génération d'un serveur MCP → test dans le playground avec Mistral.
9. Commit initial (`chore: bootstrap MCP generator project`) et push sur `main`.

---

## Livrables attendus

- Code source complet backend + frontend.
- `docker-compose.yml` fonctionnel (`docker compose up` démarre tout l'environnement).
- Documentation (`README.md`, `docs/architecture.md`).
- Suite de tests minimale passante (backend + frontend).
- Configuration LiteLLM prête à l'emploi avec Mistral comme provider par défaut.
- Repo poussé sur `https://github.com/Mindou-Ricardo/MCP.git`.