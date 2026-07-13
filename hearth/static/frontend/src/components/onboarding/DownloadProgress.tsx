import { useState, useEffect, useRef } from 'react';

interface DownloadState {
  status: 'pending' | 'downloading' | 'done' | 'error';
  downloaded: number;
  total: number;
  filename: string;
  error?: string;
}

interface DownloadProgressProps {
  models: string[];
  onComplete: () => void;
}

export function DownloadProgress({ models, onComplete }: DownloadProgressProps) {
  const [progress, setProgress] = useState<Record<string, DownloadState>>({});
  const [activeIndex, setActiveIndex] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (activeIndex >= models.length) {
      onComplete();
      return;
    }

    const modelName = models[activeIndex];
    const { filename } = getDownloadInfo(modelName);

    // Start download
    fetch('/api/models/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: modelName }),
    }).catch(() => {
      setProgress(prev => ({
        ...prev,
        [modelName]: { status: 'error', downloaded: 0, total: 0, filename, error: 'Failed to start download' },
      }));
    });

    // Listen for SSE
    eventSourceRef.current = new EventSource(`/api/models/download/${encodeURIComponent(modelName)}/progress`);
    eventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress(prev => ({
          ...prev,
          [modelName]: {
            status: data.status,
            downloaded: data.downloaded || 0,
            total: data.total || 0,
            filename,
          },
        }));
      } catch (e) {
        console.error('Error parsing SSE data:', e);
      }
    };
    eventSourceRef.current.onerror = () => {
      setProgress(prev => ({
        ...prev,
        [modelName]: { status: 'error', downloaded: 0, total: 0, filename, error: 'Download failed' },
      }));
      eventSourceRef.current?.close();
    };

    return () => eventSourceRef.current?.close();
  }, [activeIndex, models, onComplete]);

  useEffect(() => {
    // Check if current download is done
    const current = progress[models[activeIndex]];
    if (current?.status === 'done') {
      setTimeout(() => setActiveIndex(i => i + 1), 500);
    }
  }, [progress, activeIndex, models]);

  if (activeIndex >= models.length) {
    return <div className="p-6 text-center text-green-600">All downloads complete!</div>;
  }

  const currentModel = models[activeIndex];
  const current = progress[currentModel] || { status: 'pending', downloaded: 0, total: 0 };
  const percent = current.total > 0 ? Math.round((current.downloaded / current.total) * 100) : 0;

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold">Downloading Models</h2>
      <p className="text-gray-600">Model {activeIndex + 1} of {models.length}</p>

      {models.map((m, i) => {
        const p = progress[m];
        return (
          <div key={m} className={`p-3 rounded ${i === activeIndex ? 'bg-blue-50' : 'bg-gray-50'}`}>
            <div className="flex justify-between text-sm">
              <span>{m}</span>
              <span>{i < activeIndex ? '✅' : i === activeIndex ? `${percent}%` : '⏳'}</span>
            </div>
            {i === activeIndex && p && p.downloaded > 0 && (
              <div className="mt-2 bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${percent}%` }} />
              </div>
            )}
          </div>
        );
      })}

      {current.status === 'error' && (
        <div className="text-red-600 mt-4">Download failed: {current.error}</div>
      )}
    </div>
  );
}

function getDownloadInfo(modelName: string) {
  const registry: Record<string, { filename: string; url: string }> = {
    'nomic-embed-text-v1.5': {
      filename: 'nomic-embed-text-v1.5.Q4_K_M.gguf',
      url: 'https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q4_K_M.gguf',
    },
    'llama-3.2-1b': {
      filename: 'Llama-3.2-1B-Instruct-Q4_K_M.gguf',
      url: 'https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf',
    },
  };
  return registry[modelName] || { filename: '', url: '' };
}