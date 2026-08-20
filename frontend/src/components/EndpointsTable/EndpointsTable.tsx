import { useMemo, useState } from 'react';

import type { ParsedEndpoint } from '../../types';

interface EndpointsTableProps {
  endpoints: ParsedEndpoint[];
  selected: Set<string>;
  onToggle: (name: string) => void;
  onSelectAll: (names: string[]) => void;
}

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-emerald-100 text-emerald-700',
  POST: 'bg-blue-100 text-blue-700',
  PUT: 'bg-amber-100 text-amber-700',
  PATCH: 'bg-violet-100 text-violet-700',
  DELETE: 'bg-red-100 text-red-700',
  HEAD: 'bg-slate-100 text-slate-600',
  OPTIONS: 'bg-slate-100 text-slate-600',
};

export function EndpointsTable({
  endpoints,
  selected,
  onToggle,
  onSelectAll,
}: EndpointsTableProps) {
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return endpoints;
    return endpoints.filter(
      (e) =>
        e.name.toLowerCase().includes(q) ||
        e.path.toLowerCase().includes(q) ||
        e.method.toLowerCase().includes(q),
    );
  }, [endpoints, query]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <input
          className="input max-w-xs"
          placeholder="Filtrer (nom, chemin, méthode)…"
          value={query}
          data-testid="filter-input"
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="button"
          className="btn-secondary"
          onClick={() =>
            onSelectAll(selected.size === endpoints.length ? [] : endpoints.map((e) => e.name))
          }
        >
          {selected.size === endpoints.length ? 'Tout désélectionner' : 'Tout sélectionner'}
        </button>
      </div>

      <div className="max-h-96 overflow-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">Tool MCP</th>
              <th className="px-3 py-2">Méthode</th>
              <th className="px-3 py-2">Chemin</th>
              <th className="px-3 py-2">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((endpoint) => (
              <tr
                key={endpoint.name}
                className={selected.has(endpoint.name) ? 'bg-blue-50/50' : ''}
              >
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    aria-label={`Sélectionner ${endpoint.name}`}
                    checked={selected.has(endpoint.name)}
                    onChange={() => onToggle(endpoint.name)}
                  />
                </td>
                <td className="px-3 py-2 font-mono text-xs">{endpoint.name}</td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-semibold ${METHOD_COLORS[endpoint.method] ?? ''}`}
                  >
                    {endpoint.method}
                  </span>
                </td>
                <td className="px-3 py-2 font-mono text-xs">{endpoint.path}</td>
                <td className="max-w-md truncate px-3 py-2 text-xs text-slate-500">
                  {endpoint.summary ?? endpoint.description ?? '—'}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-6 text-center text-slate-400">
                  Aucun endpoint ne correspond au filtre.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400">
        {selected.size} / {endpoints.length} endpoints sélectionnés
      </p>
    </div>
  );
}
