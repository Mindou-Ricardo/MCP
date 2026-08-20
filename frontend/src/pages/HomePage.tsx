import { useNavigate } from 'react-router-dom';

import { SwaggerUpload } from '../components/SwaggerUpload';
import { useAppStore } from '../store/useAppStore';

/**
 * Page d'accueil : import de la spec Swagger/OpenAPI (upload ou URL).
 */
export function HomePage() {
  const { setCurrentSpec } = useAppStore();
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-900">Générateur de serveurs MCP</h1>
        <p className="mt-2 text-slate-500">
          Importez une spec Swagger/OpenAPI et générez un serveur MCP exposant chaque endpoint comme
          un tool, testable dans un chat connecté à LiteLLM.
        </p>
      </div>

      <SwaggerUpload
        onParsed={(spec) => {
          setCurrentSpec(spec);
          navigate('/generate');
        }}
      />

      <div className="text-center">
        <button type="button" className="btn-primary" onClick={() => navigate('/generate')}>
          Aller à la génération →
        </button>
      </div>
    </div>
  );
}
