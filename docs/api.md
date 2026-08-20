# API — Documentation

Base URL (dev) : `http://localhost:8000`. Auth : via `X-API-Key` si `API_KEYS` est configuré
(sinon pas d'authentification — prévoir un réseau interne).

## Vue d'ensemble

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | Healthcheck (passe aussi par `/api/health`) |
| POST | `/api/swagger/upload` | Upload d'une spec (multipart) |
| POST | `/api/swagger` | Import d'une spec par URL |
| GET | `/api/swagger` | Liste des specs importées |
| GET | `/api/swagger/{id}` | Détail + endpoints normalisés |
| DELETE | `/api/swagger/{id}` | Suppression d'une spec |
| POST | `/api/servers/generate` | Lance la génération d'un serveur MCP |
| POST | `/api/servers/{id}/regenerate` | Régénère (idempotent) |
| GET | `/api/servers` | Liste des serveurs générés + statuts |
| GET | `/api/servers/{id}/status` | Statut en temps réel (SSE) |
| GET | `/api/servers/{id}/download` | Télécharge le zip généré |
| GET | `/api/servers/{id}/extract/{file}` | Contenu d'un fichier généré |
| DELETE | `/api/servers/{id}` | Supprimer serveur + fichiers |
| POST | `/api/chat` | Streaming de chat (SSE) |

---

## Specs Swagger

### POST `/api/swagger/upload`

Multipart : `file` (`.json`/`.yaml`, Swagger 2.0 / OpenAPI 3.x).

```json
{
  "id": "uuid",
  "original_filename": "petstore.yaml",
  "spec_version": "3.0.3",
  "source_type": "upload",
  "source": { "content": "...", "content_type": "yaml" },
  "created_at": "2026-01-01T00:00:00Z"
}
```

### POST `/api/swagger`

```json
{ "url": "https://petstore3.swagger.io/api/v3/openapi.json" }
```

### GET `/api/swagger/{id}`

Retourne `SwaggerSpecDetail` : `spec` (objet OpenAPI + info + servers) et `endpoints`
(liste triée de `ParsedEndpoint`).

`ParsedEndpoint` :

```json
{
  "id": "get-pet-by-id",
  "name": "getPetById",
  "method": "get",
  "path": "/pet/{petId}",
  "summary": "Find pet by ID",
  "parameters": [
    {
      "name": "petId",
      "in": "path",                 // champ "in_" (sans alias pydantic)
      "schema": { "type": "integer", "format": "int64" },
      "required": true
    }
  ],
  "request_body": { "required": false, "schema": { "type": "object" } },
  "responses": { "200": { "description": "successful operation" } },
  "tags": ["pet"]
}
```

---

## Serveurs générés

### POST `/api/servers/generate`

```json
{
  "spec_id": "uuid",
  "server_name": "mon-api",
  "base_url": "https://api.exemple.com",
  "auth": { "type": "bearer", "token": "..." },
  "timeout": 30,
  "retries": 3,
  "endpoint_ids": ["get-pet-by-id"]   // optionnel : tous par défaut
}
```

Réponse : `{ "server_id": "uuid", "status": "pending" }`.
La génération s'exécute en arrière-plan (`status` : `pending → generating → ready`, ou `failed`).

### GET `/api/servers/{id}/status` — SSE

Événements :

```
event: status
data: {"status": "generating", "progress": 0.5}
```

```
event: done
data: {"status": "ready", "dir_name": "mon-api"}
```

```
event: error
data: {"detail": "message d'erreur"}
```

### GET `/api/servers/{id}/download`

Retourne `application/zip` : `Content-Disposition: attachment; filename="<dir_name>.zip"`.

### GET `/api/servers/{id}/extract/{file}`

Retourne le contenu texte d'un fichier généré (ex. `server.py`, `tools.py`, `config.json`).
La génération état `ready` est nécessaire.

### Delete `/api/servers/{id}`

Supprime l'entrée en base + le répertoire des fichiers générés.

---

## Chat (playground)

### POST `/api/chat` — SSE

```json
{
  "server_id": "uuid",
  "message": "Récupère le pet 42",
  "server_config": null          // optionnel : surcharge CONFIG
}
```

Le backend charge la spec et les tools associés au serveur, les envoie au LLM (via LiteLLM)
avec la demande, puis exécute les `tool_calls` sur l'API cible réelle (`HttpToolRunner`).

Événements :

| event | data | Description |
|---|---|---|
| `start` | `{"message_id": "..."}` | Début du flux |
| `delta` | `{"message_id": "...", "content": "...", "tool_call_id": null}` | Token de réponse |
| `tool_calls` | `{"message_id": "...", "tool_calls": [{...}]}` | Le LLM demande des tools |
| `tool_result` | `{"message_id": "...", "tool_call_id": "...", "name": "...", "content": "...", "is_error": false}` | Résultat d'exécution |
| `done` | `{"message_id": "..."}` | Fin du flux |
| `error` | `{"detail": "..."}` | Erreur (statut 200 + event error) |

## Codes d'erreur

| Code | Situation |
|---|---|
| 400 | spec invalide, URL inaccessible, nom de serveur pris (`ServerNameTakenError`) |
| 404 | spec/serveur introuvable (`SwaggerSpecNotFoundError`, `GeneratedServerNotFoundError`) |
| 422 | validation pydantic des body |
| 401 | `X-API-Key` manquante/invalide si le mode est activé |

OpenAPI interactive : http://localhost:8000/docs (Swagger UI) et `/openapi.json`.