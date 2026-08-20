import { useEffect, useState } from 'react';

import { api } from '../../services/api';
import { useAppStore } from '../../store/useAppStore';
import type { GeneratedServer } from '../../types';
import { useServerStatus } from '../../hooks/useServerStatus';
import { timeAgo } from '../../utils/time';
import { ConfirmDialog } from '../ConfirmDialog';

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

function StatusBadge({ status }: { status: string }) {
  const busyStatus = status === 'pending' || status === 'generating' || status === 'regenerating';
  return (
    <span className={`badge ${STATUS_BADGE[status] ?? 'bg-slate-100 text-slate-600'}`}>
      {busyStatus && <span className="spinner !size-3" aria-hidden="true" />}
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

export function ServersList({ onPlayground, onNavigateHome }: ServersListProps) {
  const { servers, fetchServers, removeServer } = useAppStore();
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [actedServerId, setActedServerId] = useState<number | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<GeneratedServer | null>(null);

  useEffect(() => {
    void fetchServers();
  }, [fetchServers]);

  async function handleDelete(server: GeneratedServer) {
    setConfirmTarget(null);
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
    setDeleteError(null);
    try {
      await api.regenerateServer(server.id);
      void fetchServers();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Régénération impossible');
      setActedServerId(null);
    }
  }

  const readyCount = servers.filter((s) => s.status === 'ready').length;
  const failedCount = servers.filter((s) => s.status === 'failed').length;

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Serveurs MCP générés</h2>
          {servers.length > 0 && (
            <span className="badge border border-slate-200 bg-white text-slate-500">
              {servers.length} au total · {readyCount} prêt{readyCount > 1 ? 's' : ''}
              {failedCount > 0 && <span className="text-red-500"> · {failedCount} en échec</span>}
            </span>
          )}
        </div>
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

      {deleteError && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
          {deleteError}
        </p>
      )}

      {servers.length === 0 ? (
        <div className="card flex flex-col items-center gap-3 py-10 text-center">
          <svg
            className="size-10 text-slate-300"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <rect x="2" y="2" width="20" height="8" rx="2" />
            <rect x="2" y="14" width="20" height="8" rx="2" />
            <line x1="6" x2="6.01" y1="6" y2="6" />
            <line x1="6" x2="6.01" y1="18" y2="18" />
          </svg>
          <p className="text-sm text-slate-400">
            Aucun serveur généré pour l'instant. Importez une spec pour commencer.
          </p>
          <button type="button" className="btn-primary" onClick={onNavigateHome}>
            Importer une spec
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {servers.map((server) => (
            <ServerRow
              key={server.id}
              server={server}
              acting={actedServerId === server.id}
              onDelete={() => setConfirmTarget(server)}
              onRegenerate={() => void handleRegenerate(server)}
              onDownload={() => void api.downloadServer(server.id, server.name)}
              onPlayground={() => onPlayground(server)}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={confirmTarget !== null}
        danger
        title="Supprimer le serveur"
        message={
          confirmTarget
            ? `Supprimer le serveur « ${confirmTarget.name} » et ses fichiers générés ? Cette action est irréversible.`
            : ''
        }
        confirmLabel="Supprimer"
        onCancel={() => setConfirmTarget(null)}
        onConfirm={() => {
          if (confirmTarget) void handleDelete(confirmTarget);
        }}
      />
    </section>
  );
}

interface ServerRowProps {
  server: GeneratedServer;
  acting: boolean;
  onDelete: () => void;
  onRegenerate: () => void;
  onDownload: () => void;
  onPlayground: () => void;
}

function ServerRow({
  server,
  acting,
  onDelete,
  onRegenerate,
  onDownload,
  onPlayground,
}: ServerRowProps) {
  const { status } = useServerStatus(
    server.status === 'generating' ||
      server.status === 'pending' ||
      server.status === 'regenerating'
      ? server.id
      : null,
    api.serverStatusUrl,
  );
  const currentStatus = status ?? server.status;
  const ready = currentStatus === 'ready';

  return (
    <div className="card flex flex-wrap items-center justify-between gap-3 !py-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-900">{server.name}</span>
          <StatusBadge status={currentStatus} />
          <span
            className="text-xs text-slate-300"
            aria-label={`Créé ${timeAgo(server.created_at)}`}
          >
            {timeAgo(server.created_at)}
          </span>
        </div>
        <p className="mt-1 truncate font-mono text-xs text-slate-400">
          {server.base_url ?? '—'} · {server.endpoints_count} tool
          {server.endpoints_count > 1 ? 's' : ''}
        </p>
        {currentStatus === 'failed' && server.error && (
          <p className="mt-2 max-w-xl rounded-lg border border-red-100 bg-red-50 px-2.5 py-1.5 text-xs text-red-600">
            {server.error}
          </p>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="btn-secondary"
          disabled={!ready}
          title="Télécharger le zip"
          onClick={onDownload}
        >
          Télécharger
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={acting || (currentStatus !== 'ready' && currentStatus !== 'failed')}
          onClick={onRegenerate}
        >
          {acting ? (
            <>
              <span className="spinner" /> Régénération…
            </>
          ) : (
            'Régénérer'
          )}
        </button>
        <button
          type="button"
          className="btn-primary"
          disabled={!ready}
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
