import { useSettings } from '@/hooks/useSettings';

interface HeaderProps {
  onSearch: () => void;
  onSettings: () => void;
}

export function Header({ onSearch, onSettings }: HeaderProps) {
  const { settings, updateSettings } = useSettings();
  const piiEnabled = settings?.pii_filter_enabled ?? false;

  const togglePii = () => {
    updateSettings({ pii_filter_enabled: !piiEnabled });
  };

  return (
    <header className="flex items-center justify-between h-12 px-4 border-b border-gray-200 dark:border-hearth-700 bg-white dark:bg-hearth-900 shrink-0">
      {/* Left: Brand */}
      <div className="flex items-center gap-2">
        <span className="text-lg" role="img" aria-label="Hearth">
          &#x1F525;
        </span>
        <span className="font-semibold text-gray-900 dark:text-gray-100">
          Hearth
        </span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1">
        {/* Search button */}
        <button
          onClick={onSearch}
          className="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-hearth-700"
          title="Search (Ctrl+K)"
          aria-label="Search"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>

        {/* PII toggle */}
        <button
          onClick={togglePii}
          className={`p-2 rounded-md transition-colors ${
            piiEnabled
              ? 'text-green-500 hover:text-green-600 bg-green-50 dark:bg-green-900/20'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-hearth-700'
          }`}
          title="Toggle PII filter (Ctrl+Shift+P)"
          aria-label="Toggle PII filter"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </button>

        {/* Settings button */}
        <button
          onClick={onSettings}
          className="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-hearth-700"
          title="Settings (Ctrl+,)"
          aria-label="Settings"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>
    </header>
  );
}
