import { create } from 'zustand';

interface FilterState {
  selectedSources: string[];
  selectedTags: string[];
  searchQuery: string;
  setSelectedSources: (s: string[]) => void;
  toggleSource: (s: string) => void;
  setSearchQuery: (q: string) => void;
  clearAll: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  selectedSources: [],
  selectedTags: [],
  searchQuery: '',

  setSelectedSources: (s) => set({ selectedSources: s }),
  toggleSource: (s) =>
    set((state) => ({
      selectedSources: state.selectedSources.includes(s)
        ? state.selectedSources.filter((x) => x !== s)
        : [...state.selectedSources, s],
    })),
  setSearchQuery: (q) => set({ searchQuery: q }),
  clearAll: () => set({ selectedSources: [], selectedTags: [], searchQuery: '' }),
}));
