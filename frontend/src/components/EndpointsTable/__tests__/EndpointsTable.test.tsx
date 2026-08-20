import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { EndpointsTable } from '../EndpointsTable';
import type { ParsedEndpoint } from '../../../types';

const endpoints: ParsedEndpoint[] = [
  { method: 'GET', path: '/pets', name: 'list_pets', summary: 'Liste les animaux', security: [] },
  { method: 'POST', path: '/pets', name: 'create_pet', summary: 'Crée un animal', security: [] },
  { method: 'GET', path: '/pets/{pet_id}', name: 'get_pet_by_id', summary: null, security: [] },
];

describe('EndpointsTable', () => {
  it('affiche chaque endpoint', () => {
    render(
      <EndpointsTable
        endpoints={endpoints}
        selected={new Set()}
        onToggle={vi.fn()}
        onSelectAll={vi.fn()}
      />,
    );
    expect(screen.getByText('list_pets')).toBeInTheDocument();
    expect(screen.getByText('create_pet')).toBeInTheDocument();
    expect(screen.getByText('/pets/{pet_id}')).toBeInTheDocument();
  });

  it('filtre par nom', () => {
    render(
      <EndpointsTable
        endpoints={endpoints}
        selected={new Set()}
        onToggle={vi.fn()}
        onSelectAll={vi.fn()}
      />,
    );
    fireEvent.change(screen.getByTestId('filter-input'), { target: { value: 'create' } });
    expect(screen.getByText('create_pet')).toBeInTheDocument();
    expect(screen.queryByText('list_pets')).not.toBeInTheDocument();
  });

  it('sélectionne/désélectionne un endpoint', () => {
    const onToggle = vi.fn();
    render(
      <EndpointsTable
        endpoints={endpoints}
        selected={new Set(['list_pets'])}
        onToggle={onToggle}
        onSelectAll={vi.fn()}
      />,
    );
    const checkbox = screen.getByLabelText('Sélectionner create_pet');
    fireEvent.click(checkbox);
    expect(onToggle).toHaveBeenCalledWith('create_pet');
  });

  it('compte la sélection', () => {
    render(
      <EndpointsTable
        endpoints={endpoints}
        selected={new Set(['list_pets'])}
        onToggle={vi.fn()}
        onSelectAll={vi.fn()}
      />,
    );
    expect(
      screen.getAllByText(
        (_, node) => node !== null && node.textContent === '1 / 3 endpoints sélectionnés',
      ).length,
    ).toBeGreaterThan(0);
  });
});
