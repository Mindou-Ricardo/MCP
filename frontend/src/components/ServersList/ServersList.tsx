import { useEffect, useState } from 'react';

import { api } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';
import type { GeneratedServer } from '../../types';
import { useServerStatus } from '../../hooks/useServerStatus';

interface ServersListProps {
  onPlayground: (server: GeneratedServer) => void;
  onNavigateHome: () => void;
}

const STATUS_BADGE: Record<string, string> = {
  pending: 'bg-slate-100 text-slate-600',
  generating: 'bg-amber-100 text-amber-700',
  regenerating: 'bg-amber-100 text-amber-700',
  ready: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-red-100 text-red-700',
};

const STATUS_LABEL: Record<string, string> = {
  pending: 'En attente',
  generating: 'Génération…',
  regenerating: 'Régénération…',
  ready: 'Prêt',
  failed: 'Échec',
};

export function ServersList({ onPlayground, onNavigateHome }: ServersListProps) {
  const { servers, fetchServers, removeServer } = useAppStore();
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [actedServerId, setActedServerId] = useState<number | null>(null);

  useEffect(() => {
    void fetchServers();
  }, [fetchServers]);

  async function handleDelete(server: GeneratedServer) {
    if (!window.confirm(`Supprimer le serveur « ${server.name} » et ses fichiers générés ?`)) {
      return;
    }
    setDeleteError(null);
    try {
      await removeServer(server.id);
      if (actedServerId === server.id) setActedServerId(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Suppression impossible');
    }
  }

  async function handleRegenerate(server: GeneratedServer) {
    setActedServerId(server.id);
    try {
      await api.regenerateServer(server.id);
      void fetchServers();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Régénération impossible');
      setActedServerId(null);
    }
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Serveurs MCP générés</h2>
        <div className="flex gap-2">
          <button
            type="button"
            className="btn-secondary"
            data-testid="refresh-servers"
            onClick={() => void fetchServers()}
          >
            Rafraîchir
          </button>
          <button type="button" className="btn-primary" onClick={onNavigateHome}>
            + Nouveau serveur
          </button>
        </div>
      </div>

      {deleteError && <p className="text-sm text-red-600">{deleteError}</p>}

      {servers.length === 0 ? (
        <div className="card text-center text-sm text-slate-400">
          Aucun serveur généré pour l'instant. Importez une spec pour commencer.
        </div>
      ) : (
        <div className="space-y-2">
          {servers.map((server) => (
            <ServerRow
              key={server.id}
              server={server}
              onDelete={() => void handleDelete(server)}
              onRegenerate={() => void handleRegenerate(server)}
              onDownload={() => void api.downloadServer(server.id, server.name)}
              onPlayground={() => onPlayground(server)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

interface ServerRowProps {
  server: GeneratedServer;
  onDelete: () => void;
  onRegenerate: () => void;
  onDownload: () => void;
  onPlayground: () => void;
}

function ServerRow({ server, onDelete, onRegenerate, onDownload, onPlayground }: ServerRowProps) {
  const { status } = useServerStatus(
    server.status === 'generating' ||
      server.status === 'pending' ||
      server.status === 'regenerating'
      ? server.id
      : null,
    api.serverStatusUrl,
  );
  const currentStatus = status ?? server.status;

  return (
    <div className="card flex flex-wrap items-center justify-between gap-3 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{server.name}</span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[currentStatus] ?? ''}`}
          >
            {STATUS_LABEL[currentStatus] ?? currentStatus}
          </span>
        </div>
        <p className="mt-1 truncate font-mono text-xs text-slate-400">
          {server.base_url ?? '—'} · {server.endpoints_count} tool(s)
        </p>
        {currentStatus === 'failed' && server.error && (
          <p className="mt-1 max-w-xl text-xs text-red-500">{server.error}</p>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="btn-secondary"
          disabled={currentStatus !== 'ready'}
          title="Télécharger le zip"
          onClick={onDownload}
        >
          Télécharger
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={currentStatus !== 'ready' && currentStatus !== 'failed'}
          onClick={onRegenerate}
        >
          Régénérer
        </button>
        <button
          type="button"
          className="btn-primary"
          disabled={currentStatus !== 'ready'}
          data-testid={`playground-${server.id}`}
          onClick={onPlayground}
        >
          Tester dans le playground
        </button>
        <button type="button" className="btn-danger" onClick={onDelete}>
          Supprimer
        </button>
      </div>
    </div>
  );
}
