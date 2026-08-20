import { useNavigate } from 'react-router-dom';

import { SwaggerUpload } from '../components/SwaggerUpload';
import { useAppStore } from '../store/useAppStore';

const STEPS = [
  {
    number: '1',
    title: 'Importer',
    text: 'Upload d\u2019un fichier JSON/YAML ou d\u2019une URL publique.',
  },
  {
    number: '2',
    title: 'Configurer',
    text: 'Choisissez les endpoints exposés comme tools MCP et les paramètres.',
  },
  {
    number: '3',
    title: 'Tester',
    text: 'Discutez avec votre API dans le playground connecté à LiteLLM.',
  },
];

/**
 * Page d'accueil : présentation + import de la spec Swagger/OpenAPI (upload ou URL).
 */
export function HomePage() {
  const { currentSpec, setCurrentSpec } = useAppStore();
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-6">
      <div className="space-y-4 pt-6 text-center">
        <span className="badge border border-blue-200 bg-blue-50 text-blue-700">
          Swagger 2.0 · OpenAPI 3.x
        </span>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">
          Générateur de{' '}
          <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            serveurs MCP
          </span>
        </h1>
        <p className="mx-auto max-w-xl text-slate-500">
          Importez une spec Swagger/OpenAPI et générez un serveur MCP exposant chaque endpoint comme
          un tool, testable dans un chat connecté à LiteLLM.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {STEPS.map((step) => (
          <div key={step.number} className="card flex items-start gap-3 !p-4">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
              {step.number}
            </span>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">{step.title}</h3>
              <p className="mt-0.5 text-xs leading-relaxed text-slate-500">{step.text}</p>
            </div>
          </div>
        ))}
      </div>

      <SwaggerUpload
        onParsed={(spec) => {
          setCurrentSpec(spec);
          navigate('/generate');
        }}
      />

      {currentSpec && (
        <div className="text-center">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate('/generate')}
            data-testid="go-to-generation"
          >
            Continuer avec « {currentSpec.title ?? currentSpec.filename} » →
          </button>
        </div>
      )}
    </div>
  );
}
