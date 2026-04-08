import { api } from './client';
import type { DateRange, EventListResponse, SourceCount, TimelineEvent } from '../types';

export interface EventsQuery {
  sources?: string[];
  event_types?: string[];
  tags?: string[];
  from_date?: string;
  to_date?: string;
  limit?: number;
  offset?: number;
  sort?: 'occurred_at_asc' | 'occurred_at_desc';
}

function buildQuery(params: Record<string, string | string[] | number | undefined>): string {
  const parts: string[] = [];
  for (const [key, val] of Object.entries(params)) {
    if (val === undefined || val === null) continue;
    if (Array.isArray(val)) {
      val.forEach(v => parts.push(`${key}=${encodeURIComponent(v)}`));
    } else {
      parts.push(`${key}=${encodeURIComponent(String(val))}`);
    }
  }
  return parts.length ? `?${parts.join('&')}` : '';
}

export const eventsApi = {
  list: (q: EventsQuery = {}) =>
    api.get<EventListResponse>(`/events${buildQuery({
      sources: q.sources,
      event_types: q.event_types,
      tags: q.tags,
      from_date: q.from_date,
      to_date: q.to_date,
      limit: q.limit ?? 500,
      offset: q.offset ?? 0,
      sort: q.sort ?? 'occurred_at_asc',
    })}`),

  get: (id: string) => api.get<TimelineEvent>(`/events/${id}`),

  sources: () => api.get<SourceCount[]>('/events/sources'),

  dateRange: () => api.get<DateRange>('/events/date-range'),
};
