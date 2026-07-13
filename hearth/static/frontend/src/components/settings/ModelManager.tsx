import { useEffect, useState, useRef, useCallback } from 'react';
import { models as modelsApi } from '@/api/client';

interface ModelItem {
  name: string;
  filename: string;
  size: string;
  status: 'not_downloaded' | 'downloading' | 'downloaded' | 'error';
  progress: { downloaded?: number; total?: number; error?: string };
}

export function ModelManager() {
  const [items, setItems] = useState<ModelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const esRefs = useRef<Record<string, EventSource>>({});

  const fetchList = useCallback(async () => {
    try {
      const res = await modelsApi.downloads();
      setItems(res.items as ModelItem[]);
    } catch {
      // silently ignore — show stale state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchList();
    return () => {
      // close any open SSE connections on unmount
      Object.values(esRefs.current).forEach((es) => es.close());
    };
  }, [fetchList]);

  const startDownload = async (name: string) => {
    // Mark as downloading immediately
    setItems((prev) =>
      prev.map((m) => (m.name === name ? { ...m, status: 'downloading', progress: { downloaded: 0, total: 0 } } : m))
    );

    try {
      await modelsApi.download(name);
    } catch (e: any) {
      setItems((prev) =>
        prev.map((m) =>
          m.name === name ? { ...m, status: 'error', progress: { error: e.message } } : m
        )
      );
      return;
    }

    // Open SSE stream for progress
    const es = modelsApi.downloadProgress(name);
    esRefs.current[name] = es;

    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        setItems((prev) =>
          prev.map((m) =>
            m.name === name
              ? {
                  ...m,
                  status: data.status === 'done' ? 'downloaded' : data.status === 'error' ? 'error' : 'downloading',
                  progress: data,
                }
              : m
          )
        );
        if (data.status === 'done' || data.status === 'error') {
          es.close();
          delete esRefs.current[name];
          if (data.status === 'done') fetchList();
        }
      } catch {}
    };

    es.onerror = () => {
      es.close();
      delete esRefs.current[name];
    };
  };

  if (loading) {
    return <p className="text-xs text-gray-400 dark:text-gray-500">Loading models...</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const pct =
          item.status === 'downloading' && item.progress.total && item.progress.total > 0
            ? Math.round(((item.progress.downloaded ?? 0) / item.progress.total) * 100)
            : null;

        return (
          <div key={item.name} className="rounded-lg border border-gray-200 dark:border-hearth-600 p-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">{item.name}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">{item.filename}</p>
              </div>

              {item.status === 'downloaded' && (
                <span className="text-xs font-medium text-green-600 dark:text-green-400 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Ready · {item.size}
                </span>
              )}

              {item.status === 'not_downloaded' && (
                <button
                  onClick={() => startDownload(item.name)}
                  className="text-xs px-2.5 py-1 rounded-md bg-hearth-600 hover:bg-hearth-700 text-white transition-colors"
                >
                  Download
                </button>
              )}

              {item.status === 'error' && (
                <button
                  onClick={() => startDownload(item.name)}
                  className="text-xs px-2.5 py-1 rounded-md bg-red-500 hover:bg-red-600 text-white transition-colors"
                >
                  Retry
                </button>
              )}
            </div>

            {item.status === 'downloading' && (
              <div className="space-y-1">
                <div className="w-full bg-gray-200 dark:bg-hearth-700 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-hearth-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${pct ?? 0}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {pct !== null ? `${pct}%` : 'Starting…'}{' '}
                  {item.progress.total && item.progress.total > 0
                    ? `· ${Math.round((item.progress.downloaded ?? 0) / 1024 / 1024)} / ${Math.round(item.progress.total / 1024 / 1024)} MB`
                    : ''}
                </p>
              </div>
            )}

            {item.status === 'error' && item.progress.error && (
              <p className="text-xs text-red-500">{item.progress.error}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
