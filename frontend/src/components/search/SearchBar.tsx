import { useState, useCallback, useRef } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { useFilterStore } from '../../stores/filterStore';
import { searchApi } from '../../api/search';
import type { TimelineEvent } from '../../types';
import { getSourceColor, getSourceLabel, getEventEmoji } from '../ui/sourceColors';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';

interface Props {
  onResultSelect: (event: TimelineEvent) => void;
  aiAvailable: boolean;
}

export function SearchBar({ onResultSelect, aiAvailable }: Props) {
  const { searchQuery, setSearchQuery } = useFilterStore();
  const [results, setResults] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<'fts' | 'hybrid'>('hybrid');
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const doSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) {
        setResults([]);
        setOpen(false);
        return;
      }
      setLoading(true);
      try {
        const resp = await searchApi.search(q, aiAvailable ? mode : 'fts');
        setResults(resp.items.slice(0, 8));
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [mode, aiAvailable]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value;
    setSearchQuery(q);
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => doSearch(q), 350);
  };

  const handleClear = () => {
    setSearchQuery('');
    setResults([]);
    setOpen(false);
  };

  const handleSelect = (ev: TimelineEvent) => {
    setOpen(false);
    onResultSelect(ev);
  };

  return (
    <div style={{ position: 'relative', flex: 1, maxWidth: 520 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          background: '#fff',
          border: '1.5px solid #e5e7eb',
          borderRadius: 10,
          padding: '6px 12px',
          gap: 8,
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
        }}
      >
        {loading ? <Loader2 size={16} className="spin" style={{ color: '#9ca3af' }} /> : <Search size={16} style={{ color: '#9ca3af' }} />}
        <input
          value={searchQuery}
          onChange={handleChange}
          onFocus={() => results.length && setOpen(true)}
          placeholder="Suche in deiner Timeline…"
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            fontSize: 14,
            background: 'transparent',
            color: '#111',
          }}
        />
        {searchQuery && (
          <button onClick={handleClear} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af', padding: 0 }}>
            <X size={15} />
          </button>
        )}
        {aiAvailable && (
          <button
            onClick={() => setMode(m => m === 'fts' ? 'hybrid' : 'fts')}
            style={{
              background: mode === 'hybrid' ? '#6366f1' : '#e5e7eb',
              color: mode === 'hybrid' ? '#fff' : '#555',
              border: 'none',
              borderRadius: 6,
              padding: '2px 8px',
              fontSize: 11,
              cursor: 'pointer',
              fontWeight: 600,
            }}
            title={mode === 'hybrid' ? 'Semantische Suche aktiv' : 'Nur Textsuche'}
          >
            {mode === 'hybrid' ? '✦ KI' : 'Text'}
          </button>
        )}
      </div>

      {open && results.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: 4,
            background: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
            zIndex: 500,
            overflow: 'hidden',
          }}
        >
          {results.map(ev => (
            <button
              key={ev.id}
              onClick={() => handleSelect(ev)}
              style={{
                display: 'flex',
                width: '100%',
                padding: '10px 14px',
                gap: 10,
                alignItems: 'flex-start',
                background: 'none',
                border: 'none',
                borderBottom: '1px solid #f3f4f6',
                cursor: 'pointer',
                textAlign: 'left',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = '#f9fafb')}
              onMouseLeave={e => (e.currentTarget.style.background = 'none')}
            >
              <span style={{ fontSize: 18, lineHeight: 1 }}>{getEventEmoji(ev.event_type)}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: '#111', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {ev.title || ev.event_type}
                </div>
                <div style={{ fontSize: 12, color: '#888', display: 'flex', gap: 6, marginTop: 2 }}>
                  <span style={{ color: getSourceColor(ev.source), fontWeight: 600 }}>{getSourceLabel(ev.source)}</span>
                  <span>&middot;</span>
                  <span>{format(new Date(ev.occurred_at), 'dd.MM.yyyy', { locale: de })}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
