import { useEffect, useRef, useCallback } from 'react';
import { DataSet } from 'vis-data';
import { Timeline } from 'vis-timeline/standalone';
import 'vis-timeline/styles/vis-timeline-graph2d.css';
import type { TimelineEvent } from '../../types';
import { getSourceColor, getSourceLabel, getEventEmoji } from '../ui/sourceColors';
import { useTimelineStore } from '../../stores/timelineStore';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';

interface Props {
  events: TimelineEvent[];
  onEventSelect?: (event: TimelineEvent) => void;
}

export function TimelineView({ events, onEventSelect }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<Timeline | null>(null);
  const itemsRef = useRef(new DataSet<any>([]));
  const groupsRef = useRef(new DataSet<any>([]));
  const { setVisibleRange } = useTimelineStore();

  // Build groups from unique sources
  const buildGroups = useCallback((evs: TimelineEvent[]) => {
    const sources = [...new Set(evs.map(e => e.source))].sort();
    groupsRef.current.clear();
    groupsRef.current.add(
      sources.map(s => ({
        id: s,
        content: `<span style="color:${getSourceColor(s)};font-weight:600">${getSourceLabel(s)}</span>`,
      }))
    );
  }, []);

  // Convert events to vis-timeline items
  const buildItems = useCallback((evs: TimelineEvent[]) => {
    itemsRef.current.clear();
    itemsRef.current.add(
      evs.map(e => {
        const color = getSourceColor(e.source);
        const emoji = getEventEmoji(e.event_type);
        const label = e.title ? (e.title.length > 40 ? e.title.slice(0, 40) + '…' : e.title) : e.event_type;
        const hasThumbnail = e.media.length > 0 && e.media[0].thumbnail_path;
        return {
          id: e.id,
          group: e.source,
          start: new Date(e.occurred_at),
          content: hasThumbnail
            ? `<img src="http://localhost:8000/media/${e.media[0].thumbnail_path}" style="height:28px;border-radius:3px;vertical-align:middle;margin-right:4px">${emoji}`
            : `${emoji} ${label}`,
          title: `${format(new Date(e.occurred_at), 'PPp', { locale: de })}\n${label}`,
          style: `background-color:${color}22;border-color:${color};border-radius:4px;color:#1a1a2e`,
          className: 'timeline-item',
        };
      })
    );
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    buildGroups(events);
    buildItems(events);

    if (!timelineRef.current) {
      const tl = new Timeline(containerRef.current, itemsRef.current, groupsRef.current, {
        height: '100%',
        stack: true,
        showMajorLabels: true,
        showMinorLabels: true,
        orientation: { axis: 'top' },
        groupOrder: 'content',
        zoomMin: 1000 * 60 * 60,           // 1 hour min zoom
        zoomMax: 1000 * 60 * 60 * 24 * 365 * 50, // 50 years max zoom
        locale: 'de',
        tooltip: { followMouse: true },
        selectable: true,
        multiselect: false,
      });

      tl.on('select', (props: { items: string[] }) => {
        const id = props.items[0];
        if (id) {
          const ev = events.find(e => e.id === id);
          if (ev && onEventSelect) onEventSelect(ev);
        }
      });

      tl.on('rangechanged', (props: { start: Date; end: Date }) => {
        setVisibleRange(props.start, props.end);
      });

      timelineRef.current = tl;

      // Fit to all events if available
      if (events.length > 0) {
        setTimeout(() => tl.fit(), 100);
      }
    } else {
      timelineRef.current.setGroups(groupsRef.current);
      timelineRef.current.setItems(itemsRef.current);
    }

    return () => {};
  }, [events]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timelineRef.current) {
        timelineRef.current.destroy();
        timelineRef.current = null;
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ height: '100%', width: '100%' }}
      className="vis-timeline-container"
    />
  );
}
