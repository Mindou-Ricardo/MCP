import { useEffect, useRef, useState } from 'react';

import { openServerStatusStream, type SseStreamHandle } from '../services/ws';
import type { ServerStatus } from '../types';

interface UseServerStatus {
  status: ServerStatus | null;
  error: string | null;
}

/**
 * Abonne un composant au flux SSE de statut de génération d'un serveur.
 * Le statut "ready"|"failed" termine le flux.
 */
export function useServerStatus(
  serverId: number | null,
  statusUrl: (id: number) => string,
): UseServerStatus {
  const [status, setStatus] = useState<ServerStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const handleRef = useRef<SseStreamHandle | null>(null);

  useEffect(() => {
    if (serverId === null) return;
    if (handleRef.current) {
      handleRef.current.close();
    }
    setStatus(null);
    setError(null);

    handleRef.current = openServerStatusStream(statusUrl(serverId), {
      onStatus: (next) => setStatus(next),
      onDone: (final) => setStatus(final),
      onError: (message) => setError(message),
    });
    return () => {
      handleRef.current?.close();
      handleRef.current = null;
    };
  }, [serverId, statusUrl]);

  return { status, error };
}
