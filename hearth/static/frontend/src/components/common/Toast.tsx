import { useEffect, useState } from 'react';

type ToastType = 'info' | 'error' | 'success';

interface ToastProps {
  message: string;
  type?: ToastType;
  duration?: number;
  onDismiss?: () => void;
}

const typeStyles: Record<ToastType, string> = {
  info: 'bg-hearth-600 text-white',
  error: 'bg-red-600 text-white',
  success: 'bg-green-600 text-white',
};

export function Toast({
  message,
  type = 'info',
  duration = 4000,
  onDismiss,
}: ToastProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      onDismiss?.();
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onDismiss]);

  if (!visible) return null;

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-lg shadow-lg text-sm font-medium transition-all ${typeStyles[type]}`}
      role="alert"
    >
      {message}
    </div>
  );
}
