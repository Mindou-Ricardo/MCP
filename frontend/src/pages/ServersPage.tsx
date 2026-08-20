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
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900">Serveurs</h1>
        <p className="text-sm text-slate-500">
          Vos serveurs MCP générés : téléchargez le code, régénérez ou testez chaque serveur dans le
          playground.
        </p>
      </div>

      <ServersList
        onPlayground={(server) => navigate(`/playground/${server.id}`)}
        onNavigateHome={() => navigate('/')}
      />

      <p className="text-xs text-slate-400">
        <Link to="/" className="underline underline-offset-2 hover:text-blue-600">
          Importez
        </Link>{' '}
        une spec Swagger puis générez un serveur MCP depuis la page « Générer ».
      </p>
    </div>
  );
}
