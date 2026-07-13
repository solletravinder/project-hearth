import { useEffect, useState } from 'react';
import { models as modelsApi } from '@/api/client';

const PROFILE_META: Record<string, { label: string; description: string; icon: string }> = {
  fast: { label: 'Fast', description: 'Small model, instant responses', icon: '⚡' },
  balanced: { label: 'Balanced', description: 'Best speed/quality trade-off', icon: '⚖️' },
  accurate: { label: 'Accurate', description: 'Largest model, best quality', icon: '🎯' },
};

export function ModelProfileCard() {
  const [profiles, setProfiles] = useState<string[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [switching, setSwitching] = useState<string | null>(null);

  useEffect(() => {
    modelsApi.profiles().then((res) => {
      const names = Object.keys(res.profiles ?? {});
      setProfiles(names);
      setActive(res.active ?? names[0] ?? null);
    }).catch(() => {});
  }, []);

  const selectProfile = async (name: string) => {
    if (name === active || switching) return;
    setSwitching(name);
    try {
      await modelsApi.setProfile(name);
      setActive(name);
    } catch {
      // keep previous active on error
    } finally {
      setSwitching(null);
    }
  };

  if (profiles.length === 0) {
    return <p className="text-xs text-gray-400 dark:text-gray-500">No profiles configured.</p>;
  }

  return (
    <div className="space-y-2">
      {profiles.map((name) => {
        const meta = PROFILE_META[name] ?? { label: name, description: '', icon: '🔧' };
        const isActive = active === name;
        const isLoading = switching === name;
        return (
          <button
            key={name}
            onClick={() => selectProfile(name)}
            disabled={!!switching}
            className={[
              'w-full text-left rounded-lg border p-3 flex items-start gap-3 transition-colors',
              isActive
                ? 'border-hearth-500 bg-hearth-50 dark:bg-hearth-900/40'
                : 'border-gray-200 dark:border-hearth-600 hover:border-hearth-400 hover:bg-gray-50 dark:hover:bg-hearth-800/50',
              switching ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer',
            ].join(' ')}
          >
            <span className="text-lg mt-0.5">{meta.icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200 flex items-center gap-2">
                {meta.label}
                {isActive && (
                  <span className="text-xs font-normal text-hearth-600 dark:text-hearth-400">(active)</span>
                )}
                {isLoading && (
                  <span className="text-xs font-normal text-gray-400 animate-pulse">switching…</span>
                )}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{meta.description}</p>
            </div>
            {isActive && (
              <svg className="w-4 h-4 text-hearth-500 shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        );
      })}
    </div>
  );
}
