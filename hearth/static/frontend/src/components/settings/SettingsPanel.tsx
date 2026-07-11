import { useEffect, useCallback } from 'react';
import { useSettings } from '@/hooks/useSettings';
import { ModelManager } from './ModelManager';
import { TraceInspector } from './TraceInspector';
import { Spinner } from '@/components/common/Spinner';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { settings, isLoading, updateSettings } = useSettings();

  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (isOpen) {
      window.addEventListener('keydown', handleEscape);
      return () => window.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, handleEscape]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-white dark:bg-hearth-800 shadow-2xl border-l border-gray-200 dark:border-hearth-700 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-hearth-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Settings
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-hearth-700"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-8">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner />
            </div>
          ) : (
            <>
              {/* General settings */}
              <section>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                  General
                </h3>
                <div className="space-y-3">
                  {/* Embedding provider */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Embedding Provider
                    </label>
                    <select
                      value={settings?.embedding_provider ?? 'local'}
                      onChange={(e) => updateSettings({ embedding_provider: e.target.value as 'local' | 'ollama' | 'openai' })}
                      className="w-full rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-900 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-hearth-400"
                    >
                      <option value="local">Local (sentence-transformers)</option>
                      <option value="ollama">Ollama</option>
                      <option value="openai">OpenAI-compatible (llama.cpp, LocalAI)</option>
                    </select>
                  </div>

                  {/* Chat provider */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Chat Provider
                    </label>
                    <select
                      value={settings?.chat_provider ?? 'ollama'}
                      onChange={(e) => updateSettings({ chat_provider: e.target.value as 'local' | 'ollama' | 'openai' })}
                      className="w-full rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-900 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-hearth-400"
                    >
                      <option value="local">Mock (no real provider)</option>
                      <option value="ollama">Ollama</option>
                      <option value="openai">OpenAI-compatible (llama.cpp, LocalAI)</option>
                    </select>
                  </div>

                  {/* Ollama base URL */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Ollama URL
                    </label>
                    <input
                      type="text"
                      value={settings?.ollama_base_url ?? ''}
                      onChange={(e) => updateSettings({ ollama_base_url: e.target.value })}
                      className="w-full rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-900 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-hearth-400"
                      placeholder="http://localhost:11434"
                    />
                  </div>

                  {/* OpenAI-compatible base URL */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      OpenAI-compatible URL
                    </label>
                    <input
                      type="text"
                      value={settings?.openai_base_url ?? ''}
                      onChange={(e) => updateSettings({ openai_base_url: e.target.value })}
                      className="w-full rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-900 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-hearth-400"
                      placeholder="http://localhost:11434/v1"
                    />
                  </div>

                  {/* Default model */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Default Model
                    </label>
                    <input
                      type="text"
                      value={settings?.default_model ?? ''}
                      onChange={(e) => updateSettings({ default_model: e.target.value })}
                      className="w-full rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-900 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-hearth-400"
                      placeholder="llama3.2"
                    />
                  </div>

                  {/* System prompt */}
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                      System Prompt
                    </label>
                    <textarea
                      value={settings?.system_prompt ?? ''}
                      onChange={(e) => updateSettings({ system_prompt: e.target.value })}
                      rows={3}
                      className="w-full rounded-lg border border-gray-300 dark:border-hearth-600 bg-white dark:bg-hearth-900 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-hearth-400 resize-none"
                    />
                  </div>
                </div>
              </section>

              {/* Models section */}
              <section>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                  Models
                </h3>
                <ModelManager />
              </section>

              {/* Traces section */}
              <section>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                  Traces
                </h3>
                <TraceInspector />
              </section>
            </>
          )}
        </div>
      </div>
    </>
  );
}
