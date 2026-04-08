import { create } from 'zustand';

interface TimelineState {
  visibleFrom: Date | null;
  visibleTo: Date | null;
  selectedEventId: string | null;
  activeSources: string[];
  setVisibleRange: (from: Date, to: Date) => void;
  setSelectedEvent: (id: string | null) => void;
  setActiveSources: (sources: string[]) => void;
  toggleSource: (source: string) => void;
}

export const useTimelineStore = create<TimelineState>((set) => ({
  visibleFrom: null,
  visibleTo: null,
  selectedEventId: null,
  activeSources: [],

  setVisibleRange: (from, to) => set({ visibleFrom: from, visibleTo: to }),
  setSelectedEvent: (id) => set({ selectedEventId: id }),
  setActiveSources: (sources) => set({ activeSources: sources }),
  toggleSource: (source) =>
    set((state) => ({
      activeSources: state.activeSources.includes(source)
        ? state.activeSources.filter((s) => s !== source)
        : [...state.activeSources, source],
    })),
}));
