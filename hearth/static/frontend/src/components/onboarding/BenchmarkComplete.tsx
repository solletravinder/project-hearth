interface BenchmarkCompleteProps {
  onClose: () => void;
}

export function BenchmarkComplete({ onClose }: BenchmarkCompleteProps) {
  const handleFinish = async () => {
    try {
      await fetch('/api/settings/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wizard_completed: 'true' }),
      });
    } catch {
      // non-critical — wizard won't re-show from this session anyway
    }
    onClose();
  };

  return (
    <div className="p-6 space-y-4 text-center">
      <h2 className="text-2xl font-semibold text-green-600">✅ Setup Complete</h2>
      <p className="text-gray-600">
        Models downloaded and benchmarked. Hearth is ready to use.
      </p>
      <div className="mt-4 p-4 bg-gray-50 rounded-lg text-left">
        <h3 className="font-medium mb-2">What's ready:</h3>
        <ul className="space-y-1 text-sm text-gray-600">
          <li>✅ Embedding model (gte-small)</li>
          <li>✅ Chat model (Qwen2.5-1.5B)</li>
          <li>✅ Citation verification (Qwen3-0.6B)</li>
          <li>✅ OCR & ASR models</li>
        </ul>
      </div>
      <button
        onClick={handleFinish}
        className="mt-6 px-8 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
      >
        Start Using Hearth
      </button>
    </div>
  );
}
