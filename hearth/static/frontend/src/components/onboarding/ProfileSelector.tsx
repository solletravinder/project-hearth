import { useState } from 'react';

export interface ModelProfile {
  name: string;
  generator: string;
  ramNeeded: number;
  totalDownload: string;
  description: string;
}

const PROFILES: ModelProfile[] = [
  { name: 'fast', generator: 'Qwen3-0.6B', ramNeeded: 8, totalDownload: '~700 MB', description: 'Fastest inference, lower RAM footprint' },
  { name: 'balanced', generator: 'Qwen2.5-1.5B', ramNeeded: 8, totalDownload: '~1.3 GB', description: 'Best balance of speed and quality' },
  { name: 'accurate', generator: 'Llama-3.2-3B', ramNeeded: 16, totalDownload: '~3 GB', description: 'Highest quality, needs more RAM' },
];

interface ProfileSelectorProps {
  onSelect: (profile: string) => void;
}

export function ProfileSelector({ onSelect }: ProfileSelectorProps) {
  const [selected, setSelected] = useState('balanced');

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-xl font-semibold">Choose Model Profile</h2>
      {PROFILES.map(p => (
        <div
          key={p.name}
          className={`p-4 border rounded-lg cursor-pointer ${selected === p.name ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
          onClick={() => setSelected(p.name)}
        >
          <div className="flex items-center justify-between">
            <h3 className="font-medium">{p.generator}</h3>
            <span className="text-sm text-gray-500">{p.totalDownload}</span>
          </div>
          <p className="text-sm text-gray-600 mt-1">{p.description}</p>
        </div>
      ))}
      <button
        onClick={() => onSelect(selected)}
        className="mt-4 w-full px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Download Models
      </button>
    </div>
  );
}