import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../api';
import type { GeneratedServer } from '../../types';

const baseUrl = '/api';

function mockFetch(response: Response | Promise<Response>) {
  return vi.fn().mockResolvedValue(response);
}

describe('api service', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('listServers retourne les serveurs', async () => {
    const servers: GeneratedServer[] = [
      {
        id: 1,
        name: 'petstore',
        status: 'ready',
        auth_type: 'none',
        endpoints_count: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ];
    globalThis.fetch = mockFetch(new Response(JSON.stringify(servers), { status: 200 }));

    const result = await api.listServers();
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('petstore');
    expect(globalThis.fetch).toHaveBeenCalledWith(`${baseUrl}/servers`, expect.anything());
  });

  it('lève ApiError avec le detail du backend', async () => {
    globalThis.fetch = mockFetch(
      new Response(JSON.stringify({ detail: 'Spec invalide' }), { status: 400 }),
    );
    await expect(api.parseSwaggerByUrl('https://x.test')).rejects.toThrow('Spec invalide');
  });

  it('uploadSwagger envoie un FormData', async () => {
    globalThis.fetch = mockFetch(
      new Response(
        JSON.stringify({
          spec_id: 5,
          endpoints_count: 2,
          openapi_version: '3.0.x',
          filename: 's.yaml',
          source_type: 'file',
          endpoints: [],
        }),
        {
          status: 201,
        },
      ),
    );
    const file = new File(['{"openapi": "3.0.0"}'], 'spec.json', { type: 'application/json' });

    const result = await api.uploadSwagger(file);
    expect(result.spec_id).toBe(5);
    const init = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1] as RequestInit;
    expect(init.body).toBeInstanceOf(FormData);
  });

  it('executesTool POST le nom et les arguments', async () => {
    globalThis.fetch = mockFetch(
      new Response(JSON.stringify({ tool: 'list_pets', result: { status_code: 200 } }), {
        status: 200,
      }),
    );
    const result = await api.executeTool(3, 'list_pets', { limit: 5 });
    expect(result.tool).toBe('list_pets');
    const [url, init] = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toBe(`${baseUrl}/chat/3/execute-tool`);
    expect(JSON.parse(init.body as string)).toEqual({ name: 'list_pets', arguments: { limit: 5 } });
  });
});
