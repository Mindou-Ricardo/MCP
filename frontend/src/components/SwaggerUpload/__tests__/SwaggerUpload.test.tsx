import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../../../services/api';
import { SwaggerUpload } from '../SwaggerUpload';
import type { SpecParseResult } from '../../../types';

vi.mock('../../../services/api', () => ({
  api: {
    uploadSwagger: vi.fn(),
    parseSwaggerByUrl: vi.fn(),
  },
}));

const parsed: SpecParseResult = {
  spec_id: 1,
  filename: 'petstore.json',
  source_type: 'file',
  title: 'Petstore',
  openapi_version: '3.0.x',
  endpoints: [],
  endpoints_count: 0,
};

describe('SwaggerUpload', () => {
  beforeEach(() => {
    vi.mocked(api.uploadSwagger).mockReset();
    vi.mocked(api.parseSwaggerByUrl).mockReset();
  });

  it('upload un fichier et notifie le parent', async () => {
    vi.mocked(api.uploadSwagger).mockResolvedValue(parsed);
    const onParsed = vi.fn();
    render(<SwaggerUpload onParsed={onParsed} />);

    const input = screen.getByTestId('file-input') as HTMLInputElement;
    const file = new File(['{"openapi": "3.0.0"}'], 'petstore.json', { type: 'application/json' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => expect(onParsed).toHaveBeenCalledWith(parsed));
  });

  it('parse une URL et notifie le parent', async () => {
    vi.mocked(api.parseSwaggerByUrl).mockResolvedValue(parsed);
    const onParsed = vi.fn();
    render(<SwaggerUpload onParsed={onParsed} />);

    fireEvent.change(screen.getByTestId('url-input'), {
      target: { value: 'https://api.example.com/openapi.json' },
    });
    fireEvent.click(screen.getByTestId('url-parse-button'));

    await waitFor(() => expect(onParsed).toHaveBeenCalledWith(parsed));
  });

  it('affiche une erreur si le backend échoue', async () => {
    vi.mocked(api.parseSwaggerByUrl).mockRejectedValue(new Error('Spec invalide'));
    render(<SwaggerUpload onParsed={vi.fn()} />);

    fireEvent.change(screen.getByTestId('url-input'), {
      target: { value: 'https://api.example.com/openapi.json' },
    });
    fireEvent.click(screen.getByTestId('url-parse-button'));

    await waitFor(() => expect(screen.getByText('Spec invalide')).toBeInTheDocument());
  });
});
