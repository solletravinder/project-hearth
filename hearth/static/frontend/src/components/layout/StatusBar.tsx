import { useSettingsStore } from '@/store/settingsStore';

export function StatusBar() {
  const { modelStatus, settings } = useSettingsStore();

  const loadedModels = modelStatus.filter((m) => m.loaded);
  const modelLabel = loadedModels.length > 0
    ? loadedModels.map((m) => m.name).join(', ')
    : 'No model loaded';

  const memoryIndicator = settings?.pii_filter_enabled ? 'PII ON' : 'PII OFF';

  return (
    <footer className="flex items-center justify-between h-6 px-3 border-t border-gray-200 dark:border-hearth-700 bg-gray-50 dark:bg-hearth-800 text-xs text-gray-400 dark:text-gray-500 shrink-0">
      <span className="truncate" title={modelLabel}>
        Model: {modelLabel}
      </span>
      <span className="shrink-0 ml-2">{memoryIndicator}</span>
    </footer>
  );
}
