import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import App from '../App';
import { api } from '../services/api';
import { useAppStore } from '../store/useAppStore';

vi.mock('../services/api', () => ({
  api: {
    listServers: vi.fn().mockResolvedValue([]),
    listProviders: vi.fn().mockResolvedValue([]),
  },
}));

describe('App', () => {
  it("affiche la barre de navigation et la page d'accueil", () => {
    useAppStore.setState({ currentSpec: null });
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getAllByText(/MCP Generator/).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: 'Générer' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Serveurs' })).toBeInTheDocument();
    expect(screen.getByText('Importer une spec Swagger/OpenAPI')).toBeInTheDocument();
  });

  it('affiche le playground sur /playground/:id quand le serveur est prêt', async () => {
    api.getServer = vi.fn().mockResolvedValue({
      id: 1,
      name: 'petstore',
      status: 'ready',
      auth_type: 'none',
      endpoints_count: 2,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
    render(
      <MemoryRouter initialEntries={['/playground/1']}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/Playground — petstore/)).toBeInTheDocument();
  });
});
