import { useEffect, useState, useCallback } from 'react';

interface LogEntry {
  id: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  component: string;
  message: string;
  details: string | null;
  created_at: string;
}

const LEVEL_STYLES: Record<string, string> = {
  debug:   'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  info:    'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400',
  warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400',
  error:   'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400',
};

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(iso).toLocaleDateString();
}

export function TraceInspector() {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const perPage = 20;

  const fetchLogs = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/system/logs?page=${p}&per_page=${perPage}`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data.items ?? []);
        setTotal(data.total ?? 0);
        setPage(p);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLogs(1); }, [fetchLogs]);

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return (
    <div className="space-y-2">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-400 dark:text-gray-500">
          {total} trace {total === 1 ? 'entry' : 'entries'}
        </p>
        <button
          onClick={() => fetchLogs(page)}
          disabled={loading}
          className="text-xs px-2 py-1 rounded-md border border-gray-200 dark:border-hearth-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-hearth-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Loading…' : '↻ Refresh'}
        </button>
      </div>

      {/* Entries */}
      <div className="space-y-1 max-h-72 overflow-y-auto pr-1">
        {entries.length === 0 && !loading && (
          <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-4">No trace entries yet.</p>
        )}
        {entries.map((entry) => (
          <div key={entry.id} className="rounded-md border border-gray-100 dark:border-hearth-700 p-2 text-xs space-y-0.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${LEVEL_STYLES[entry.level] ?? LEVEL_STYLES.info}`}>
                {entry.level}
              </span>
              <span className="text-gray-500 dark:text-gray-400 font-mono">{entry.component}</span>
              <span className="ml-auto text-gray-400 dark:text-gray-500 shrink-0">{timeAgo(entry.created_at)}</span>
            </div>
            <p className="text-gray-700 dark:text-gray-300 leading-snug">{entry.message}</p>
            {entry.details && (
              <p className="text-gray-400 dark:text-gray-500 font-mono truncate">{entry.details}</p>
            )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-1">
          <button
            onClick={() => fetchLogs(page - 1)}
            disabled={page <= 1 || loading}
            className="text-xs px-2 py-0.5 rounded border border-gray-200 dark:border-hearth-600 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-hearth-700"
          >
            ‹ Prev
          </button>
          <span className="text-xs text-gray-400">{page} / {totalPages}</span>
          <button
            onClick={() => fetchLogs(page + 1)}
            disabled={page >= totalPages || loading}
            className="text-xs px-2 py-0.5 rounded border border-gray-200 dark:border-hearth-600 disabled:opacity-40 hover:bg-gray-50 dark:hover:bg-hearth-700"
          >
            Next ›
          </button>
        </div>
      )}
    </div>
  );
}
