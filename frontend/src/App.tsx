import { useState, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Filter, RefreshCw } from 'lucide-react';
import { TimelineView } from './components/timeline/TimelineView';
import { EventDetail } from './components/event/EventDetail';
import { SearchBar } from './components/search/SearchBar';
import { ImportWizard } from './components/import/ImportWizard';
import { eventsApi } from './api/events';
import { api } from './api/client';
import { useFilterStore } from './stores/filterStore';
import { getSourceColor, getSourceLabel } from './components/ui/sourceColors';
import type { TimelineEvent, HealthStatus, SourceCount } from './types';
import './App.css';

export default function App() {
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [showImport, setShowImport] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const queryClient = useQueryClient();
  const { selectedSources, toggleSource, setSelectedSources } = useFilterStore();

  const { data: health } = useQuery<HealthStatus>({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
    refetchInterval: 30000,
    staleTime: 10000,
  });

  const { data: sources = [] } = useQuery<SourceCount[]>({
    queryKey: ['sources'],
    queryFn: () => eventsApi.sources(),
    staleTime: 60000,
  });

  const { data: eventsData, isLoading, refetch } = useQuery({
    queryKey: ['events', selectedSources],
    queryFn: () =>
      eventsApi.list({
        sources: selectedSources.length ? selectedSources : undefined,
        limit: 2000,
        sort: 'occurred_at_asc',
      }),
    staleTime: 30000,
  });

  const events = eventsData?.items ?? [];

  const handleEventSelect = useCallback((ev: TimelineEvent) => {
    setSelectedEvent(ev);
  }, []);

  const handleSearchResult = useCallback((ev: TimelineEvent) => {
    setSelectedEvent(ev);
  }, []);

  const handleImportDone = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['events'] });
    queryClient.invalidateQueries({ queryKey: ['sources'] });
    setTimeout(() => refetch(), 1000);
  }, [queryClient, refetch]);

  return (
    <div className="app-container">
      <header className="top-bar">
        <div className="top-bar-left">
          <span className="app-logo">⏳ Meine Timeline</span>
          {health && (
            <span className={`ai-badge ${health.ai_available ? 'ai-on' : 'ai-off'}`} title={`AI Backend: ${health.ai_backend}`}>
              {health.ai_available ? `✦ ${health.ai_backend}` : '● KI aus'}
            </span>
          )}
        </div>

        <div className="top-bar-center">
          <SearchBar onResultSelect={handleSearchResult} aiAvailable={!!health?.ai_available} />
        </div>

        <div className="top-bar-right">
          {isLoading && <RefreshCw size={16} className="spin" style={{ color: '#9ca3af' }} />}
          <span className="event-count">{events.length.toLocaleString('de')} Events</span>
          <button className={`icon-btn ${showFilters ? 'active' : ''}`} onClick={() => setShowFilters(f => !f)} title="Filter">
            <Filter size={16} />
          </button>
          <button className="import-btn" onClick={() => setShowImport(true)}>
            <Plus size={16} />
            Importieren
          </button>
        </div>
      </header>

      {showFilters && sources.length > 0 && (
        <div className="filter-strip">
          <span className="filter-label">Quellen:</span>
          {sources.map(s => (
            <button
              key={s.source}
              onClick={() => toggleSource(s.source)}
              className={`source-chip ${selectedSources.includes(s.source) ? 'active' : ''}`}
              style={selectedSources.includes(s.source) ? { background: getSourceColor(s.source), color: '#fff', borderColor: getSourceColor(s.source) } : {}}
            >
              {getSourceLabel(s.source)} <span className="chip-count">{s.count.toLocaleString('de')}</span>
            </button>
          ))}
          {selectedSources.length > 0 && (
            <button className="clear-btn" onClick={() => setSelectedSources([])}>Alle anzeigen</button>
          )}
        </div>
      )}

      <main className="main-area" style={{ right: selectedEvent ? 420 : 0 }}>
        {events.length === 0 && !isLoading ? (
          <div className="empty-state">
            <div style={{ fontSize: 64, marginBottom: 16 }}>⏳</div>
            <h2>Noch keine Events</h2>
            <p>Importiere deine ersten Daten, um deine Timeline zu starten.</p>
            <button className="import-btn large" onClick={() => setShowImport(true)}>
              <Plus size={18} /> Erste Daten importieren
            </button>
          </div>
        ) : (
          <TimelineView events={events} onEventSelect={handleEventSelect} />
        )}
      </main>

      {selectedEvent && (
        <EventDetail event={selectedEvent} onClose={() => setSelectedEvent(null)} />
      )}

      {showImport && (
        <ImportWizard onClose={() => setShowImport(false)} onImportDone={handleImportDone} />
      )}
    </div>
  );
}
