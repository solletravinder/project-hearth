import type { ReactNode } from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {icon && (
        <div className="mb-4 text-gray-300 dark:text-gray-600">{icon}</div>
      )}
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h3>
      {description && (
        <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 max-w-xs">
          {description}
        </p>
      )}
      {action && (
        <Button variant="secondary" className="mt-4" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
