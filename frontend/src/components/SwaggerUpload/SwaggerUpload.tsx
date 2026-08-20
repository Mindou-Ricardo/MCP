import { useRef, useState } from 'react';

import { api } from '../../services/api';
import type { SpecParseResult } from '../../types';

interface SwaggerUploadProps {
  onParsed: (result: SpecParseResult) => void;
}

export function SwaggerUpload({ onParsed }: SwaggerUploadProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileUpload(file: File | undefined) {
    if (!file) return;
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
    if (!url.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await api.parseSwaggerByUrl(url.trim());
      onParsed(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur pendant le parsing');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card space-y-4">
      <h2 className="text-lg font-semibold">Importer une spec Swagger/OpenAPI</h2>

      <div className="flex items-center gap-3">
        <input
          ref={fileRef}
          type="file"
          accept=".json,.yaml,.yml,application/json,application/x-yaml"
          className="hidden"
          data-testid="file-input"
          onChange={(e) => handleFileUpload(e.target.files?.[0])}
        />
        <button
          type="button"
          className="btn-primary"
          disabled={busy}
          onClick={() => fileRef.current?.click()}
        >
          Uploader un fichier (.json / .yaml)
        </button>
        <span className="text-sm text-slate-400">ou</span>
        <input
          type="url"
          className="input flex-1"
          placeholder="https://exemple.com/openapi.json"
          value={url}
          data-testid="url-input"
          onChange={(e) => setUrl(e.target.value)}
        />
        <button
          type="button"
          className="btn-secondary"
          disabled={busy || !url.trim()}
          data-testid="url-parse-button"
          onClick={handleUrlParse}
        >
          {busy ? 'Analyse…' : 'Charger l\u2019URL'}
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </section>
  );
}
