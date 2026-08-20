import { NavLink, Route, Routes } from 'react-router-dom';

import { GeneratePage } from './pages/GeneratePage';
import { HomePage } from './pages/HomePage';
import { PlaygroundPage } from './pages/PlaygroundPage';
import { ServersPage } from './pages/ServersPage';

function NavBar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-100 text-blue-700'
        : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
    }`;

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between p-4">
        <NavLink to="/" className="text-lg font-bold text-slate-900">
          ⚙️ MCP Generator
        </NavLink>
        <nav className="flex gap-1">
          <NavLink to="/" className={linkClass} end>
            Accueil
          </NavLink>
          <NavLink to="/generate" className={linkClass}>
            Générer
          </NavLink>
          <NavLink to="/servers" className={linkClass}>
            Serveurs
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <NavBar />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/generate" element={<GeneratePage />} />
          <Route path="/servers" element={<ServersPage />} />
          <Route path="/playground/:serverId" element={<PlaygroundPage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </main>
    </div>
  );
}
