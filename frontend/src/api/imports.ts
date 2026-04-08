import { API } from './client';
import type { ImportJob, ParserInfo } from '../types';

export const importsApi = {
  list: async (): Promise<ImportJob[]> => {
    const res = await fetch(`${API}/imports`);
    return res.json();
  },

  get: async (id: string): Promise<ImportJob> => {
    const res = await fetch(`${API}/imports/${id}`);
    return res.json();
  },

  parsers: async (): Promise<ParserInfo[]> => {
    const res = await fetch(`${API}/imports/parsers`);
    return res.json();
  },

  upload: async (file: File, source: string): Promise<ImportJob> => {
    const form = new FormData();
    form.append('file', file);
    form.append('source', source);
    const res = await fetch(`${API}/imports`, { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
    return res.json();
  },

  streamProgress: (jobId: string): EventSource => {
    return new EventSource(`${API}/imports/${jobId}/stream`);
  },
};
