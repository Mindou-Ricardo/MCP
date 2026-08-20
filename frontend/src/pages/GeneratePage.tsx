import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { EndpointsTable } from '../components/EndpointsTable';
import { ServerConfigForm } from '../components/ServerConfigForm';
import { api } from '../services/api';
import { useAppStore } from '../store/useAppStore';
import type { ServerCreateRequest } from '../types';

/**
 * Page « Générer » : prévisualisation des endpoints de la spec importée,
 * configuration du serveur MCP et lancement de la génération.
 */
export function GeneratePage() {
  const { currentSpec } = useAppStore();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [generating, setGenerating] = useState(false);
  const [generatedId, setGeneratedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (currentSpec) {
      setSelected(new Set(currentSpec.endpoints.map((e) => e.name)));
      setGeneratedId(null);
      setError(null);
    }
  }, [currentSpec]);

  if (!currentSpec) {
    return (
      <div className="mx-auto max-w-3xl p-6 text-center">
        <div className="card">
          <h1 className="text-lg font-semibold text-slate-900">Aucune spec importée</h1>
          <p className="mb-4 mt-1 text-sm text-slate-500">
            Importez une spec Swagger/OpenAPI pour commencer la génération.
          </p>
          <Link to="/" className="btn-primary">
            Importer une spec Swagger
          </Link>
        </div>
      </div>
    );
  }

  function toggleEndpoint(name: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  async function handleGenerate(payload: ServerCreateRequest) {
    setGenerating(true);
    setError(null);
    try {
      const { server_id } = await api.generateServer(payload);
      setGeneratedId(server_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de génération');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900">Générer un serveur</h1>
        <p className="text-sm text-slate-500">
          Spec :{' '}
          <span className="font-semibold text-slate-700">
            {currentSpec.title ?? currentSpec.filename}
          </span>{' '}
          — OpenAPI {currentSpec.openapi_version} ({currentSpec.endpoints_count} endpoint
          {currentSpec.endpoints_count > 1 ? 's' : ''})
        </p>
      </div>

      <section className="card space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Endpoints détectés</h2>
        <EndpointsTable
          endpoints={currentSpec.endpoints}
          selected={selected}
          onToggle={toggleEndpoint}
          onSelectAll={(names) => setSelected(new Set(names))}
        />
      </section>

      <ServerConfigForm
        spec={currentSpec}
        selectedEndpoints={[...selected]}
        onGenerate={handleGenerate}
        busy={generating}
      />

      {error && (
        <p
          className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
          role="alert"
          data-testid="generation-error"
        >
          {error}
        </p>
      )}
      {generatedId !== null && (
        <div
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800"
          data-testid="generation-started"
        >
          <p>
            ✅ Génération lancée (serveur #{generatedId}). Le statut est suivi en temps réel sur la
            page Serveurs.
          </p>
          <Link to="/servers" className="btn-primary !bg-emerald-600 hover:!bg-emerald-700">
            Voir les serveurs →
          </Link>
        </div>
      )}
    </div>
  );
}
