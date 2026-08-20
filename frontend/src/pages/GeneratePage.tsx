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
          <p className="mb-3 text-slate-500">Aucune spec importée.</p>
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
      <section className="card space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Endpoints détectés</h2>
          <p className="text-sm text-slate-400">
            {currentSpec.title ?? currentSpec.filename} — OpenAPI {currentSpec.openapi_version} (
            {currentSpec.endpoints_count})
          </p>
        </div>
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
        <p className="text-sm text-red-600" data-testid="generation-error">
          {error}
        </p>
      )}
      {generatedId !== null && (
        <div
          className="card border-emerald-200 bg-emerald-50 text-sm text-emerald-800"
          data-testid="generation-started"
        >
          Génération lancée (serveur #{generatedId}). Le statut est suivi en temps réel sur la page{' '}
          <Link to="/servers" className="font-semibold underline">
            Serveurs
          </Link>
          .
        </div>
      )}
    </div>
  );
}
