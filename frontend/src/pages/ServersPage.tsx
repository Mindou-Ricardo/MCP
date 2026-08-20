import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ServersList } from '../components/ServersList';
import { useAppStore } from '../store/useAppStore';

/**
 * Page « Serveurs » : liste des serveurs MCP générés avec statut temps réel,
 * téléchargement, régénération, suppression et accès au playground.
 */
export function ServersPage() {
  const { fetchServers } = useAppStore();
  const navigate = useNavigate();

  useEffect(() => {
    void fetchServers();
  }, [fetchServers]);

  return (
    <div className="mx-auto max-w-5xl p-6">
      <ServersList
        onPlayground={(server) => navigate(`/playground/${server.id}`)}
        onNavigateHome={() => navigate('/')}
      />
      <p className="mt-4 text-xs text-slate-400">
        <Link to="/" className="underline">
          Importez
        </Link>{' '}
        une spec Swagger puis générez un serveur MCP depuis la page « Générer ».
      </p>
    </div>
  );
}
