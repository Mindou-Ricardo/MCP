import type {
  ChatProvider,
  ChatRequestPayload,
  GeneratedServer,
  ServerCreateRequest,
  SpecParseResult,
} from '../types';
import { readSse } from './ws';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      /* corps non JSON */
    }
    throw new ApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  async parseSwaggerByUrl(url: string): Promise<SpecParseResult> {
    return request<SpecParseResult>('/swagger/parse', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },

  async uploadSwagger(file: File): Promise<SpecParseResult> {
    const form = new FormData();
    form.append('file', file);
    const response = await fetch(`${API_BASE}/swagger/upload`, {
      method: 'POST',
      body: form,
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = (await response.json()) as { detail?: string };
        detail = body.detail ?? detail;
      } catch {
        /* corps non JSON */
      }
      throw new ApiError(detail, response.status);
    }
    return response.json() as Promise<SpecParseResult>;
  },

  async generateServer(payload: ServerCreateRequest): Promise<{ server_id: number }> {
    return request<{ server_id: number }>('/servers/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async regenerateServer(serverId: number): Promise<{ server_id: number }> {
    return request<{ server_id: number }>(`/servers/${serverId}/regenerate`, {
      method: 'POST',
    });
  },

  async listServers(): Promise<GeneratedServer[]> {
    return request<GeneratedServer[]>('/servers');
  },

  async getServer(serverId: number): Promise<GeneratedServer> {
    return request<GeneratedServer>(`/servers/${serverId}`);
  },

  async deleteServer(serverId: number): Promise<void> {
    const response = await fetch(`${API_BASE}/servers/${serverId}`, { method: 'DELETE' });
    if (!response.ok) {
      throw new ApiError(response.statusText, response.status);
    }
  },

  async downloadServer(serverId: number, name: string): Promise<void> {
    const response = await fetch(`${API_BASE}/servers/${serverId}/download`);
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = (await response.json()) as { detail?: string };
        detail = body.detail ?? detail;
      } catch {
        /* corps non JSON */
      }
      throw new ApiError(detail, response.status);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${name}.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },

  async listProviders(): Promise<ChatProvider[]> {
    return request<ChatProvider[]>('/chat/providers');
  },

  async executeTool(
    serverId: number,
    name: string,
    arguments_: Record<string, unknown>,
  ): Promise<{ tool: string; result: unknown }> {
    return request<{ tool: string; result: unknown }>(`/chat/${serverId}/execute-tool`, {
      method: 'POST',
      body: JSON.stringify({ name, arguments: arguments_ }),
    });
  },

  serverStatusUrl(serverId: number): string {
    return `${API_BASE}/servers/${serverId}/status`;
  },

  async streamChat(
    payload: ChatRequestPayload,
    handlers: {
      onDelta: (text: string) => void;
      onToolCalls: (
        toolCalls: { id: string; name: string; arguments: Record<string, unknown> }[],
      ) => void;
      onToolResult: (event: { id: string; result: string }) => void;
      onDone: (hasError: boolean) => void;
      onError: (message: string) => void;
    },
    signal?: AbortSignal,
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    });
    if (!response.ok || !response.body) {
      throw new ApiError(`Chat indisponible (${response.status})`, response.status);
    }
    await readSse(response.body, (event, data) => {
      switch (event) {
        case 'delta':
          handlers.onDelta(String(data));
          break;
        case 'tool_calls':
          handlers.onToolCalls(
            data as { id: string; name: string; arguments: Record<string, unknown> }[],
          );
          break;
        case 'tool_result':
          handlers.onToolResult(data as { id: string; result: string });
          break;
        case 'done':
          handlers.onDone((data as { error?: boolean })?.error ?? false);
          break;
        case 'error':
          handlers.onError(String((data as { message?: string })?.message ?? data));
          break;
        default:
          break;
      }
    });
  },
};
