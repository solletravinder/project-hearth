import { create } from 'zustand';
import type { AppSettings, ModelStatus } from '@/types';
import { settings as settingsApi, models as modelsApi } from '@/api/client';

interface SettingsState {
  settings: AppSettings | null;
  modelStatus: ModelStatus[];
  isLoading: boolean;
  error: string | null;
}

interface SettingsActions {
  fetchSettings: () => Promise<void>;
  fetchModelStatus: () => Promise<void>;
  updateSettings: (partial: Partial<AppSettings>) => Promise<void>;
}

type SettingsStore = SettingsState & SettingsActions;

export const useSettingsStore = create<SettingsStore>((set) => ({
  settings: null,
  modelStatus: [],
  isLoading: true,
  error: null,

  fetchSettings: async () => {
    set({ isLoading: true, error: null });
    try {
      const settings = await settingsApi.get();
      set({ settings, isLoading: false });
    } catch {
      set({ error: 'Failed to load settings', isLoading: false });
    }
  },

  fetchModelStatus: async () => {
    try {
      const res = await modelsApi.status();
      set({ modelStatus: res.models });
    } catch {
      set({ error: 'Failed to load model status' });
    }
  },

  updateSettings: async (partial: Partial<AppSettings>) => {
    try {
      const updated = await settingsApi.update(partial);
      set({ settings: updated, error: null });
    } catch {
      set({ error: 'Failed to update settings' });
    }
  },
}));
