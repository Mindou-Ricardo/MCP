import { useCallback, useEffect, useRef, useState } from 'react';

import { api } from '../../services/api';
import type { ChatMessage, ChatProvider, GeneratedServer, ToolCallInfo } from '../../types';

interface ChatPlaygroundProps {
  server: GeneratedServer;
  onBack: () => void;
}

interface ChatEntry {
  id: string;
  role: 'user' | 'assistant' | 'tool' | 'system' | 'error';
  content: string;
  toolCalls?: ToolCallInfo[];
  toolResult?: string;
  toolName?: string;
  streaming?: boolean;
}

function newId(): string {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function ChatPlayground({ server, onBack }: ChatPlaygroundProps) {
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState('');
  const [providers, setProviders] = useState<ChatProvider[]>([]);
  const [model, setModel] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void api
      .listProviders()
      .then(setProviders)
      .catch(() => setError('Providers indisponibles'));
    const greeting: ChatEntry = {
      id: newId(),
      role: 'system',
      content: `Serveur MCP « ${server.name} » prêt : ${server.endpoints_count} tool(s) disponibles.`,
    };
    setEntries([greeting]);
  }, [server.id, server.name, server.endpoints_count]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [entries]);

  const toApiMessages = useCallback(
    (list: ChatEntry[]): ChatMessage[] =>
      list
        .filter((e) => e.role !== 'system' && e.role !== 'error')
        .map((e): ChatMessage => {
          if (e.role === 'tool') {
            return {
              role: 'tool',
              tool_call_id: e.id,
              name: e.toolName ?? 'tool',
              content: e.toolResult ?? '',
            };
          }
          if (e.role === 'assistant') {
            return {
              role: 'assistant',
              content: e.content || null,
              tool_calls:
                e.toolCalls && e.toolCalls.length > 0
                  ? e.toolCalls.map((tc) => ({
                      id: tc.id,
                      type: 'function',
                      function: { name: tc.name, arguments: JSON.stringify(tc.arguments) },
                    }))
                  : null,
            };
          }
          return { role: e.role, content: e.content } as ChatMessage;
        }),
    [],
  );

  async function handleSend() {
    const text = input.trim();
    if (!text || busy) return;
    const userEntry: ChatEntry = { id: newId(), role: 'user', content: text };
    setEntries((prev) => [...prev, userEntry]);
    setInput('');
    setBusy(true);
    setError(null);

    const assistantEntry: ChatEntry = {
      id: newId(),
      role: 'assistant',
      content: '',
      streaming: true,
    };
    setEntries((prev) => [...prev, assistantEntry]);
    abortRef.current = new AbortController();

    try {
      await api.streamChat(
        {
          server_id: server.id,
          messages: toApiMessages([...entries, userEntry]),
          model: providers.some((p) => p.default_model === model) ? model : null,
        },
        {
          onDelta: (delta) => {
            setEntries((prev) =>
              prev.map((e) =>
                e.id === assistantEntry.id ? { ...e, content: e.content + delta } : e,
              ),
            );
          },
          onToolCalls: (calls) => {
            setEntries((prev) =>
              prev.map((e) =>
                e.id === assistantEntry.id
                  ? { ...e, content: e.content || '— appel d\u2019outils —', toolCalls: calls }
                  : e,
              ),
            );
            for (const call of calls) {
              setEntries((prev) => [
                ...prev,
                {
                  id: call.id,
                  role: 'tool',
                  toolName: call.name,
                  content: '',
                  toolResult: '',
                  toolCalls: undefined,
                },
              ]);
            }
          },
          onToolResult: (event) => {
            setEntries((prev) =>
              prev.map((e) =>
                e.id === event.id
                  ? { ...e, toolResult: event.result, content: formatToolResult(event.result) }
                  : e,
              ),
            );
          },
          onDone: () => {
            setEntries((prev) =>
              prev.map((e) => (e.id === assistantEntry.id ? { ...e, streaming: false } : e)),
            );
          },
          onError: (message) => setError(message),
        },
        abortRef.current.signal,
      );
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        setError('Génération interrompue.');
      } else {
        setError(err instanceof Error ? err.message : 'Erreur de chat');
      }
      setEntries((prev) =>
        prev.map((e) => (e.id === assistantEntry.id ? { ...e, streaming: false } : e)),
      );
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  return (
    <section className="flex h-[70vh] flex-col space-y-3">
      <div className="card flex items-center justify-between">
        <div>
          <button
            type="button"
            className="mb-1 text-xs font-medium text-blue-600 hover:underline"
            onClick={onBack}
          >
            ← Retour aux serveurs
          </button>
          <h2 className="text-lg font-semibold">Playground — {server.name}</h2>
        </div>
        <div className="flex items-center gap-2">
          <label className="label mb-0" htmlFor="model-select">
            Modèle
          </label>
          <select
            id="model-select"
            className="input w-72"
            value={model}
            data-testid="model-select"
            onChange={(e) => setModel(e.target.value)}
          >
            {providers.length === 0 && <option value="">Chargement…</option>}
            {providers.map((provider) => (
              <optgroup key={provider.id} label={provider.display_name}>
                {provider.models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="card flex-1 space-y-3 overflow-y-auto">
        {entries.map((entry) => (
          <MessageBubble key={entry.id} entry={entry} />
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="card flex items-center gap-2 !py-2">
        <textarea
          className="input flex-1 resize-none"
          rows={1}
          placeholder="Demandez à l'API quelque chose (ex : « liste les animaux »)…"
          value={input}
          disabled={busy}
          data-testid="chat-input"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              void handleSend();
            }
          }}
        />
        {busy ? (
          <button type="button" className="btn-danger" onClick={handleStop}>
            Arrêter
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary"
            disabled={!input.trim()}
            data-testid="send-button"
            onClick={() => void handleSend()}
          >
            Envoyer
          </button>
        )}
      </div>
    </section>
  );
}

function formatToolResult(raw: string): string {
  try {
    const parsed = JSON.parse(raw) as {
      status_code?: number;
      data?: unknown;
      error?: string;
    };
    if (parsed.error) return `Échec de l'appel : ${parsed.error}`;
    return `HTTP ${parsed.status_code ?? '?'} → ${JSON.stringify(parsed.data ?? {}, null, 2)}`;
  } catch {
    return raw;
  }
}

function MessageBubble({ entry }: { entry: ChatEntry }) {
  if (entry.role === 'system') {
    return <p className="text-center text-xs text-slate-400">{entry.content}</p>;
  }
  if (entry.role === 'tool') {
    return (
      <div className="rounded-lg border border-violet-100 bg-violet-50/60 px-3 py-2">
        <p className="text-xs font-semibold text-violet-700">
          🛠 {entry.toolName} — résultat de l&apos;API
        </p>
        <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap font-mono text-xs text-slate-600">
          {entry.toolResult ?? entry.content}
        </pre>
      </div>
    );
  }
  const user = entry.role === 'user';
  return (
    <div className={`flex ${user ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
          user ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-800'
        }`}
        data-testid={`message-${entry.role}`}
      >
        {entry.content ? (
          <p className="whitespace-pre-wrap">{entry.content}</p>
        ) : (
          <p className="italic text-slate-400">(réponse vide)</p>
        )}
        {entry.streaming && <TypingIndicator />}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <span className="mt-1 inline-block animate-pulse text-xs" aria-label="Génération en cours">
      ⏳
    </span>
  );
}
