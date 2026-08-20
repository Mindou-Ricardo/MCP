import type { ServerStatus } from '../types';

export interface StatusEventHandlers {
  onStatus: (status: ServerStatus, error?: string | null) => void;
  onDone: (finalStatus: ServerStatus) => void;
  onError: (message: string) => void;
}

export interface SseStreamHandle {
  close: () => void;
}

export function openServerStatusStream(
  url: string,
  handlers: StatusEventHandlers,
): SseStreamHandle {
  let closed = false;
  let retryCount = 0;

  const connect = () => {
    const source = new EventSource(url);
    source.addEventListener('status', (ev) => {
      const data = JSON.parse(ev.data) as { status: ServerStatus; error?: string | null };
      handlers.onStatus(data.status, data.error);
    });
    source.addEventListener('done', (ev) => {
      const data = JSON.parse(ev.data) as { final: ServerStatus };
      handlers.onDone(data.final);
      source.close();
    });
    source.addEventListener('error', () => {
      if (closed) return;
      if (source.readyState === EventSource.CLOSED && retryCount < 3) {
        retryCount += 1;
        setTimeout(() => {
          if (!closed) connect();
        }, 1500 * retryCount);
      } else if (source.readyState === EventSource.CLOSED) {
        handlers.onError('Connexion au flux de statut perdue');
      }
    });
  };

  connect();
  return {
    close: () => {
      closed = true;
    },
  };
}

export async function readSse(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: string, data: unknown) => void,
  onRaw?: (raw: string) => void,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';
      for (const part of parts) {
        const event =
          part
            .split('\n')
            .find((line) => line.startsWith('event:'))
            ?.slice(6)
            .trim() ?? '';
        const dataLine = part
          .split('\n')
          .filter((line) => line.startsWith('data:'))
          .map((line) => line.slice(5).trim())
          .join('\n');
        if (event && dataLine) {
          try {
            onEvent(event, JSON.parse(dataLine));
          } catch {
            onEvent(event, dataLine);
          }
          onRaw?.(part);
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
