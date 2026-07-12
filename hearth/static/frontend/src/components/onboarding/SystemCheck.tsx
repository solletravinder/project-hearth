import { useState, useEffect } from 'react';

interface SystemInfo {
  cpu: string;
  ram: { total: number; available: number };
  disk: { total: number; available: number };
  gpu: { available: boolean; model: string | null };
}

interface SystemCheckProps {
  onComplete: (info: SystemInfo) => void;
}

export function SystemCheck({ onComplete }: SystemCheckProps) {
  const [info, setInfo] = useState<SystemInfo | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    checkSystem().then((systemInfo) => {
      setInfo(systemInfo);
      setChecking(false);
    });
  }, []);

  if (checking) return <div className="p-8 text-center">Running system diagnostics...</div>;
  if (!info) return <div className="p-8 text-red-500">System check failed</div>;

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold">System Check</h2>
      <StatusRow label="CPU" value={info.cpu} status="ok" />
      <StatusRow label="RAM" value={`${info.ram.available} / ${info.ram.total} GB`} status="ok" />
      <StatusRow label="Disk" value={`${info.disk.available} / ${info.disk.total} GB available`} status="ok" />
      <StatusRow
        label="GPU"
        value={info.gpu.available ? info.gpu.model ?? 'Available' : 'None (CPU mode)'}
        status={info.gpu.available ? 'ok' : 'warning'}
      />
      <button
        onClick={() => onComplete(info)}
        className="mt-4 w-full px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Continue
      </button>
    </div>
  );
}

function StatusRow({ label, value, status }: { label: string; value: string; status: 'ok' | 'warning' | 'error' }) {
  const colors = { ok: 'text-green-600', warning: 'text-yellow-600', error: 'text-red-600' };
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}:</span>
      <span className={colors[status]}>{value}</span>
    </div>
  );
}

async function checkSystem(): Promise<SystemInfo> {
  // In a real implementation, this would query the backend for system info
  // For now, we return mock data
  return {
    cpu: '12 cores (Apple M2 Max)',
    ram: { total: 32, available: 24 },
    disk: { total: 500, available: 200 },
    gpu: { available: true, model: 'Apple M2 Max (Metal)' },
  };
}