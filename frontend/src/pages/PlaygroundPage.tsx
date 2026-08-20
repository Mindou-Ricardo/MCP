import { useEffect, useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';

import { ChatPlayground } from '../components/ChatPlayground';
import { api } from '../services/api';
import type { GeneratedServer } from '../types';

/**
 * Page « Playground » : chat outillé (LiteLLM) pour tester un serveur MCP généré.
 */
export function PlaygroundPage() {
  const { serverId = '' } = useParams();
  const id = Number(serverId);
  const navigate = useNavigate();
  const [server, setServer] = useState<GeneratedServer | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError('Identifiant de serveur invalide.');
      return;
    }
    void api
      .getServer(id)
      .then(setServer)
      .catch((err) => setError(err instanceof Error ? err.message : 'Serveur introuvable'));
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl p-6">
        <div className="card space-y-3 text-sm text-red-600">
          <p>{error}</p>
          <button type="button" className="btn-secondary" onClick={() => navigate('/servers')}>
            ← Retour aux serveurs
          </button>
        </div>
      </div>
    );
  }
  if (!server) {
    return (
      <div className="mx-auto max-w-5xl space-y-4 p-6">
        <div className="card space-y-3">
          <div className="skeleton h-5 w-48" />
          <div className="skeleton h-72" />
        </div>
      </div>
    );
  }
  if (server.status !== 'ready') {
    return <Navigate to="/servers" replace />;
  }
  return (
    <div className="mx-auto max-w-5xl p-6">
      <ChatPlayground server={server} onBack={() => navigate('/servers')} />
    </div>
  );
}
