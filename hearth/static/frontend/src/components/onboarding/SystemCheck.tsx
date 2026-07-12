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
  try {
    const resp = await fetch('/api/system/info');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    const cpu = `${data.cpu_count} cores${data.processor ? ` (${data.processor})` : ''}`;
    return {
      cpu,
      ram: { total: data.ram.total_gb, available: data.ram.available_gb },
      disk: { total: data.disk.total_gb, available: data.disk.free_gb },
      gpu: data.gpu || { available: false, model: null },
    };
  } catch {
    // Fallback using Web APIs when backend is unreachable — no hardcoded default values
    const navExt = navigator as Navigator & { deviceMemory?: number; gpu?: object };

    const cpu = `${navigator.hardwareConcurrency ?? '?'} cores${navigator.platform ? ` (${navigator.platform})` : ''}`;

    let totalRam = 0;
    if (navExt.deviceMemory) {
      totalRam = navExt.deviceMemory;
    }

    let diskTotal = 0;
    let diskFree = 0;
    try {
      const storage = await navigator.storage.estimate();
      if (storage.quota) diskTotal = Math.round(storage.quota / (1024**3));
      if (storage.usage !== undefined) diskFree = Math.round((storage.quota! - storage.usage) / (1024**3));
    } catch {
      // navigator.storage.estimate() not available
    }

    let gpuAvailable = false;
    let gpuModel: string | null = null;
    if (navExt.gpu) {
      gpuAvailable = true;
      gpuModel = 'WebGPU compatible adapter';
    }

    return {
      cpu,
      ram: { total: totalRam || 0, available: 0 }, // available RAM unknown from browser APIs
      disk: { total: diskTotal, available: diskFree },
      gpu: { available: gpuAvailable, model: gpuModel },
    };
  }
}