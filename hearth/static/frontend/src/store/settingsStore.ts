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
      const list: ModelStatus[] = Object.entries(res.models.models).map(
        ([name, info]) => ({
          name,
          loaded: info.status === 'ready',
          model_type: 'chat' as const,
          size: '',
          modified_at: info.loaded_at ?? '',
        }),
      );
      set({ modelStatus: list });
    } catch {
      set({ error: 'Failed to load model status' });
    }
  },

  updateSettings: async (partial: Partial<AppSettings>) => {
    try {
      const updated = await settingsApi.update(partial);
      // API returns only the keys that changed — merge with current state
      set((s) => ({
        settings: s.settings ? { ...s.settings, ...updated } : updated,
        error: null,
      }));
    } catch {
      set({ error: 'Failed to update settings' });
    }
  },
}));
