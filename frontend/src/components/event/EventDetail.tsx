import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import { X, MapPin, Calendar, Tag } from 'lucide-react';
import type { TimelineEvent } from '../../types';
import { getSourceColor, getSourceLabel, getEventEmoji } from '../ui/sourceColors';
import { mediaUrl } from '../../api/client';

interface Props {
  event: TimelineEvent;
  onClose: () => void;
}

export function EventDetail({ event, onClose }: Props) {
  const color = getSourceColor(event.source);
  const emoji = getEventEmoji(event.event_type);
  const dt = new Date(event.occurred_at);

  return (
    <div
      style={{
        position: 'fixed',
        right: 0,
        top: 0,
        bottom: 0,
        width: '420px',
        background: '#fff',
        boxShadow: '-4px 0 20px rgba(0,0,0,0.15)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: `3px solid ${color}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          background: `${color}11`,
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span
              style={{
                background: color,
                color: '#fff',
                borderRadius: 12,
                padding: '2px 10px',
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              {getSourceLabel(event.source)}
            </span>
            <span style={{ fontSize: 12, color: '#666' }}>{event.event_type}</span>
          </div>
          <h2 style={{ margin: 0, fontSize: 16, fontWeight: 700, wordBreak: 'break-word' }}>
            {emoji} {event.title || '(kein Titel)'}
          </h2>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: 4,
            color: '#666',
            flexShrink: 0,
          }}
        >
          <X size={20} />
        </button>
      </div>

      {/* Scrollable body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
        {/* Date */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: '#555' }}>
          <Calendar size={15} />
          <span style={{ fontSize: 14 }}>
            {format(dt, 'EEEE, dd. MMMM yyyy', { locale: de })}
            {event.occurred_at_precision !== 'day' && (
              <> &middot; {format(dt, 'HH:mm', { locale: de })} Uhr</>
            )}
          </span>
        </div>

        {/* Location */}
        {(event.location_name || (event.location_lat && event.location_lng)) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, color: '#555' }}>
            <MapPin size={15} />
            <span style={{ fontSize: 14 }}>
              {event.location_name || `${event.location_lat?.toFixed(5)}, ${event.location_lng?.toFixed(5)}`}
            </span>
          </div>
        )}

        {/* Tags */}
        {event.tags.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 16 }}>
            <Tag size={15} style={{ marginTop: 3, color: '#888', flexShrink: 0 }} />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {event.tags.map(tag => (
                <span
                  key={tag.id}
                  style={{
                    background: tag.source === 'ai' ? '#e0e7ff' : tag.source === 'parser' ? '#f0fdf4' : '#fef9c3',
                    borderRadius: 8,
                    padding: '2px 8px',
                    fontSize: 12,
                    color: '#374151',
                  }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Body text */}
        {event.body && (
          <div
            style={{
              background: '#f8f9fa',
              borderRadius: 8,
              padding: '12px 14px',
              fontSize: 14,
              lineHeight: 1.6,
              color: '#333',
              marginBottom: 16,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              maxHeight: 300,
              overflowY: 'auto',
            }}
          >
            {event.body}
          </div>
        )}

        {/* Media */}
        {event.media.length > 0 && (
          <div>
            <h4 style={{ margin: '0 0 8px', fontSize: 13, color: '#888', fontWeight: 600, textTransform: 'uppercase' }}>
              Medien
            </h4>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
                gap: 8,
              }}
            >
              {event.media.map(m => (
                <div key={m.id} style={{ position: 'relative' }}>
                  {m.thumbnail_path ? (
                    <a href={mediaUrl(m.file_path)} target="_blank" rel="noreferrer">
                      <img
                        src={mediaUrl(m.thumbnail_path)}
                        alt="media"
                        style={{
                          width: '100%',
                          aspectRatio: '1',
                          objectFit: 'cover',
                          borderRadius: 6,
                          display: 'block',
                        }}
                      />
                    </a>
                  ) : (
                    <div
                      style={{
                        width: '100%',
                        aspectRatio: '1',
                        background: '#e5e7eb',
                        borderRadius: 6,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 24,
                      }}
                    >
                      📄
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
