import { NavLink, Route, Routes } from 'react-router-dom';

import { GeneratePage } from './pages/GeneratePage';
import { HomePage } from './pages/HomePage';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { ServersPage } from './pages/ServersPage';

function LogoIcon() {
  return (
    <svg
      className="size-6 text-blue-600"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  );
}

function NavIcon({ type }: { type: 'home' | 'generate' | 'servers' }) {
  const common = {
    className: 'size-4',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
  };
  if (type === 'home') {
    return (
      <svg {...common}>
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
    );
  }
  if (type === 'generate') {
    return (
      <svg {...common}>
        <path d="M12 3l1.9 5.8a2 2 0 0 0 1.3 1.3L21 12l-5.8 1.9a2 2 0 0 0-1.3 1.3L12 21l-1.9-5.8a2 2 0 0 0-1.3-1.3L3 12l5.8-1.9a2 2 0 0 0 1.3-1.3z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <rect x="2" y="2" width="20" height="8" rx="2" />
      <rect x="2" y="14" width="20" height="8" rx="2" />
      <line x1="6" x2="6.01" y1="6" y2="6" />
      <line x1="6" x2="6.01" y1="18" y2="18" />
    </svg>
  );
}

const NAV_ITEMS = [
  { to: '/', label: 'Accueil', icon: 'home' as const, end: true },
  { to: '/generate', label: 'Générer', icon: 'generate' as const, end: false },
  { to: '/servers', label: 'Serveurs', icon: 'servers' as const, end: false },
];

function NavBar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-50 text-blue-700'
        : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 p-4">
        <NavLink to="/" className="flex items-center gap-2 text-lg font-bold text-slate-900">
          <LogoIcon />
          MCP Generator
        </NavLink>
        <nav className="flex flex-wrap items-center gap-1" aria-label="Navigation principale">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={linkClass}>
              <NavIcon type={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white/60">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-6 py-6 text-xs text-slate-400 sm:flex-row">
        <p>MCP Generator — serveurs MCP générés depuis une spec Swagger/OpenAPI</p>
        <p>
          OpenAPI 2.0 · 3.x —{' '}
          <a
            href="https://github.com/Mindou-Ricardo/MCP"
            target="_blank"
            rel="noreferrer"
            className="font-medium text-slate-500 underline-offset-2 hover:text-blue-600 hover:underline"
          >
            GitHub
          </a>
        </p>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <NavBar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/generate" element={<GeneratePage />} />
          <Route path="/servers" element={<ServersPage />} />
          <Route path="/playground/:serverId" element={<PlaygroundPage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
