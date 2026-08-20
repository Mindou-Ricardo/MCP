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

const ALL_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

export function EndpointsTable({
  endpoints,
  selected,
  onToggle,
  onSelectAll,
}: EndpointsTableProps) {
  const [query, setQuery] = useState('');
  const [method, setMethod] = useState('ALL');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return endpoints.filter(
      (e) =>
        (method === 'ALL' || e.method === method) &&
        (!q ||
          e.name.toLowerCase().includes(q) ||
          e.path.toLowerCase().includes(q) ||
          e.method.toLowerCase().includes(q)),
    );
  }, [endpoints, query, method]);

  const allSelected = selected.size === endpoints.length;
  const visibleSelected = filtered.filter((e) => selected.has(e.name)).length;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-1 flex-wrap items-center gap-2">
          <input
            className="input max-w-xs"
            placeholder="Filtrer (nom, chemin, méthode)…"
            value={query}
            data-testid="filter-input"
            aria-label="Filtrer les endpoints"
            onChange={(e) => setQuery(e.target.value)}
          />
          <select
            className="input w-auto"
            value={method}
            aria-label="Filtrer par méthode HTTP"
            onChange={(e) => setMethod(e.target.value)}
          >
            <option value="ALL">Toutes les méthodes</option>
            {ALL_METHODS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onSelectAll(allSelected ? [] : endpoints.map((e) => e.name))}
        >
          {allSelected ? 'Tout désélectionner' : 'Tout sélectionner'}
        </button>
      </div>

      <div className="scroll-thin max-h-96 overflow-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 z-10 bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="w-10 px-3 py-2">#</th>
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
                className={`transition-colors ${
                  selected.has(endpoint.name) ? 'bg-blue-50/60' : 'hover:bg-slate-50'
                }`}
              >
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    aria-label={`Sélectionner ${endpoint.name}`}
                    checked={selected.has(endpoint.name)}
                    className="size-4 accent-blue-600"
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
                <td className="px-3 py-2 font-mono text-xs text-slate-700">{endpoint.path}</td>
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

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
        <span>
          <strong className="font-semibold text-slate-600">{selected.size}</strong> /{' '}
          {endpoints.length} endpoints sélectionnés
          {visibleSelected !== selected.size && filtered.length !== endpoints.length && (
            <span className="ml-1">({visibleSelected} visibles)</span>
          )}
        </span>
        {query && (
          <button
            type="button"
            className="btn-ghost !px-2 !py-1 text-xs"
            onClick={() => setQuery('')}
          >
            Réinitialiser le filtre
          </button>
        )}
      </div>
    </div>
  );
}
