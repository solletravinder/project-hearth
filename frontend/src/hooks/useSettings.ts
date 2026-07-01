import { useEffect } from 'react';
import { useSettingsStore } from '@/store/settingsStore';

export function useSettings() {
  const store = useSettingsStore();

  useEffect(() => {
    store.fetchSettings();
    store.fetchModelStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return store;
}
