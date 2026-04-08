import { API } from './client';
import type { SearchResponse } from '../types';

export const searchApi = {
  search: async (
    q: string,
    mode: 'fts' | 'semantic' | 'hybrid' = 'hybrid',
    limit = 50,
  ): Promise<SearchResponse> => {
    const params = new URLSearchParams({ q, mode, limit: String(limit) });
    const res = await fetch(`${API}/search?${params}`);
    if (!res.ok) throw new Error('Search failed');
    return res.json();
  },
};
