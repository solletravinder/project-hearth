export interface ProcessingStep {
  label: string;
  status: 'pending' | 'active' | 'done' | 'error';
}

interface ProcessingIndicatorProps {
  steps: ProcessingStep[];
}

const stepIcons: Record<string, string> = {
  pending: '⧣',
  active: '▶',
  done: '✓',
  error: '✗',
};

const stepColors: Record<string, string> = {
  pending: 'text-gray-400 dark:text-gray-500',
  active: 'text-blue-500 dark:text-blue-400',
  done: 'text-green-500 dark:text-green-400',
  error: 'text-red-500 dark:text-red-400',
};

export function ProcessingIndicator({ steps }: ProcessingIndicatorProps) {
  return (
    <div className="flex items-center gap-1 text-xs">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center gap-1">
          <span className={stepColors[step.status]}>{stepIcons[step.status]}</span>
          <span
            className={
              step.status === 'active'
                ? 'text-blue-600 dark:text-blue-400 font-medium'
                : 'text-gray-500 dark:text-gray-400'
            }
          >
            {step.label}
          </span>
          {i < steps.length - 1 && (
            <span className="text-gray-300 dark:text-gray-600 mx-1">&rarr;</span>
          )}
        </div>
      ))}
    </div>
  );
}
