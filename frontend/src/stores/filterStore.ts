import { create } from 'zustand';

interface FilterState {
  dateRange: { from: string; to: string } | null;
  districts: string[];
  activityType: string;
  policeStation: string;
  reviewStatus: ('approved' | 'pending' | 'rejected')[];
  resetFilters: () => void;
  setFilter: (key: keyof Omit<FilterState, 'resetFilters' | 'setFilter'>, value: any) => void;
}

const initialFilters = {
  dateRange: null,
  districts: [],
  activityType: '',
  policeStation: '',
  reviewStatus: ['approved'] as ('approved' | 'pending' | 'rejected')[],
};

export const useFilterStore = create<FilterState>((set) => ({
  ...initialFilters,
  resetFilters: () => set(initialFilters),
  setFilter: (key, value) => set({ [key]: value }),
}));
