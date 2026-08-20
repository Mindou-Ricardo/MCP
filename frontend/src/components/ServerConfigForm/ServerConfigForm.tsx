import { useState } from 'react';

import type { AuthType, ServerCreateRequest, SpecParseResult } from '../../types';

interface ServerConfigFormProps {
  spec: SpecParseResult;
  selectedEndpoints: string[];
  onGenerate: (payload: ServerCreateRequest) => Promise<void>;
  busy?: boolean;
}

const AUTH_TYPES: { value: AuthType; label: string }[] = [
  { value: 'none', label: 'Aucune authentification' },
  { value: 'api_key', label: 'Clé API (header)' },
  { value: 'bearer', label: 'Bearer token' },
  { value: 'basic', label: 'Basic auth' },
];

export function ServerConfigForm({
  spec,
  selectedEndpoints,
  onGenerate,
  busy,
}: ServerConfigFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [baseUrl, setBaseUrl] = useState(spec.base_url ?? '');
  const [authType, setAuthType] = useState<AuthType>('none');
  const [headerName, setHeaderName] = useState('X-API-Key');
  const [apiKey, setApiKey] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const canSubmit = name.trim().length >= 2 && (baseUrl.trim() || spec.base_url) && !busy;

  const disabledReason = !name.trim()
    ? 'Indiquez un nom de serveur (2 caractères minimum)'
    : name.trim().length < 2
      ? 'Le nom du serveur doit contenir au moins 2 caractères'
      : !baseUrl.trim() && !spec.base_url
        ? "Indiquez l'URL cible (aucune trouvée dans la spec)"
        : null;

  async function handleSubmit() {
    setError(null);
    const payload: ServerCreateRequest = {
      spec_id: spec.spec_id,
      name: name.trim(),
      description: description.trim() || null,
      base_url: baseUrl.trim() || null,
      include_endpoints:
        selectedEndpoints.length === spec.endpoints.length ? null : [...selectedEndpoints],
      auth: {
        type: authType,
        header_name: authType === 'api_key' ? headerName.trim() : null,
        api_key: authType === 'api_key' || authType === 'bearer' ? apiKey.trim() || null : null,
        username: authType === 'basic' ? username.trim() || null : null,
        password: authType === 'basic' ? password.trim() || null : null,
      },
    };
    try {
      await onGenerate(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de génération');
    }
  }

  return (
    <section className="card space-y-4">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-semibold text-slate-900">Configurer le serveur MCP</h2>
        <span className="badge border border-slate-200 bg-slate-50 text-slate-600">
          {selectedEndpoints.length} endpoint{selectedEndpoints.length > 1 ? 's' : ''}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="server-name">
            Nom du serveur
          </label>
          <input
            id="server-name"
            className="input"
            placeholder="mon-serveur-mcp"
            value={name}
            data-testid="server-name"
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label className="label" htmlFor="server-base-url">
            URL cible (sinon celle de la spec)
          </label>
          <input
            id="server-base-url"
            className="input"
            placeholder={spec.base_url ?? 'https://api.exemple.com'}
            value={baseUrl}
            data-testid="server-base-url"
            onChange={(e) => setBaseUrl(e.target.value)}
          />
        </div>
      </div>

      <div>
        <label className="label" htmlFor="server-description">
          Description
        </label>
        <input
          id="server-description"
          className="input"
          placeholder="Serveur MCP exposant l'API…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="label" htmlFor="auth-type">
            Authentification
          </label>
          <select
            id="auth-type"
            className="input"
            value={authType}
            data-testid="auth-type"
            onChange={(e) => setAuthType(e.target.value as AuthType)}
          >
            {AUTH_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        {authType === 'api_key' && (
          <div>
            <label className="label" htmlFor="auth-header">
              Nom du header
            </label>
            <input
              id="auth-header"
              className="input"
              value={headerName}
              placeholder="X-API-Key"
              onChange={(e) => setHeaderName(e.target.value)}
            />
          </div>
        )}
      </div>

      {authType === 'api_key' && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="md:col-start-2">
            <label className="label" htmlFor="auth-key">
              Clé API
            </label>
            <input
              id="auth-key"
              className="input"
              type="password"
              autoComplete="off"
              value={apiKey}
              data-testid="auth-key"
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
        </div>
      )}
      {authType === 'bearer' && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="md:col-start-2">
            <label className="label" htmlFor="auth-bearer">
              Token
            </label>
            <input
              id="auth-bearer"
              className="input"
              type="password"
              autoComplete="off"
              value={apiKey}
              data-testid="auth-key"
              placeholder="Bearer …"
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
        </div>
      )}
      {authType === 'basic' && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="label" htmlFor="auth-user">
              Utilisateur
            </label>
            <input
              id="auth-user"
              className="input"
              autoComplete="off"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className="label" htmlFor="auth-pass">
              Mot de passe
            </label>
            <input
              id="auth-pass"
              className="input"
              type="password"
              autoComplete="off"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-100 pt-4 sm:flex-row">
        <p className="text-xs text-slate-400">
          Spec : <span className="font-semibold">{spec.filename}</span> — {selectedEndpoints.length}{' '}
          endpoint{selectedEndpoints.length > 1 ? 's' : ''} inclus
          {selectedEndpoints.length === 0 && (
            <span className="ml-1 text-amber-600">(sélectionnez au moins un endpoint)</span>
          )}
        </p>
        <button
          type="button"
          className="btn-primary min-w-56"
          disabled={!canSubmit}
          title={disabledReason ?? undefined}
          onClick={() => void handleSubmit()}
          data-testid="generate-button"
        >
          {busy ? (
            <>
              <span className="spinner" /> Génération en cours…
            </>
          ) : (
            'Générer le serveur MCP'
          )}
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </section>
  );
}
