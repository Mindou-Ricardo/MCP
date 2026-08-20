import { useRef, useState } from 'react';

import { api } from '../../services/api';
import type { SpecParseResult } from '../../types';

interface SwaggerUploadProps {
  onParsed: (result: SpecParseResult) => void;
}

const EXAMPLE_URLS = [
  { label: 'Petstore v3', url: 'https://petstore3.swagger.io/api/v3/openapi.json' },
  { label: 'Petstore v2', url: 'https://petstore.swagger.io/v2/swagger.json' },
];

export function SwaggerUpload({ onParsed }: SwaggerUploadProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState('');
  const [pickedFile, setPickedFile] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleFileUpload(file: File | undefined) {
    if (!file || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api.uploadSwagger(file);
      onParsed(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur pendant l'upload");
    } finally {
      setBusy(false);
    }
  }

  async function handleUrlParse() {
    const value = url.trim();
    if (!value || busy) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api.parseSwaggerByUrl(value);
      onParsed(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur pendant le parsing');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card space-y-4">
      <h2 className="text-lg font-semibold text-slate-900">Importer une spec Swagger/OpenAPI</h2>

      <label
        htmlFor="file-input"
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFileUpload(e.dataTransfer.files?.[0]);
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed px-4 py-6 text-center transition-colors ${
          dragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50/40'
        }`}
      >
        <svg
          className="size-7 text-slate-400"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" x2="12" y1="3" y2="15" />
        </svg>
        <span className="text-sm font-medium text-slate-600">
          Glissez-déposez votre fichier ou{' '}
          <span className="text-blue-600 underline underline-offset-2">
            {pickedFile ? `changez ${pickedFile}` : 'parcourez vos fichiers'}
          </span>
        </span>
        <span className="text-xs text-slate-400">JSON ou YAML — Swagger 2.0 / OpenAPI 3.x</span>
      </label>

      <input
        ref={fileRef}
        id="file-input"
        type="file"
        accept=".json,.yaml,.yml,application/json,application/x-yaml"
        className="sr-only"
        data-testid="file-input"
        onChange={(e) => {
          const file = e.target.files?.[0];
          setPickedFile(file?.name ?? null);
          void handleFileUpload(file);
        }}
      />

      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-400">ou</span>
        <input
          type="url"
          className="input flex-1"
          placeholder="https://exemple.com/openapi.json"
          value={url}
          data-testid="url-input"
          aria-label="URL de la spec"
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') void handleUrlParse();
          }}
        />
        <button
          type="button"
          className="btn-secondary min-w-36"
          disabled={busy || !url.trim()}
          data-testid="url-parse-button"
          onClick={() => void handleUrlParse()}
        >
          {busy ? (
            <>
              <span className="spinner" /> Analyse…
            </>
          ) : (
            'Charger l\u2019URL'
          )}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400">Exemples :</span>
        {EXAMPLE_URLS.map((example) => (
          <button
            key={example.url}
            type="button"
            className="chip"
            disabled={busy}
            onClick={() => setUrl(example.url)}
          >
            {example.label}
          </button>
        ))}
      </div>

      {error && (
        <p
          className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600"
          role="alert"
        >
          <span aria-hidden="true">⚠</span> {error}
        </p>
      )}
    </section>
  );
}
