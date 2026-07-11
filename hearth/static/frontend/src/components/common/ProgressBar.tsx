interface ProgressBarProps {
  value: number;
  label?: string;
  className?: string;
}

export function ProgressBar({ value, label, className = '' }: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={`w-full ${className}`}>
      {(label || clamped < 100) && (
        <div className="flex justify-between items-center mb-1">
          {label && (
            <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
          )}
          <span className="text-xs text-gray-500 dark:text-gray-400">{Math.round(clamped)}%</span>
        </div>
      )}
      <div className="w-full h-2 bg-gray-200 dark:bg-hearth-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-hearth-500 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
