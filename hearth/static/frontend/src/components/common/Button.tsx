import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-hearth-600 hover:bg-hearth-700 text-white shadow-sm',
  secondary:
    'bg-gray-100 hover:bg-gray-200 text-gray-800 dark:bg-hearth-700 dark:hover:bg-hearth-600 dark:text-gray-100',
  ghost:
    'bg-transparent hover:bg-gray-100 dark:hover:bg-hearth-700 text-gray-700 dark:text-gray-300',
};

export function Button({
  variant = 'primary',
  className = '',
  disabled,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`
        inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium
        transition-colors focus:outline-none focus:ring-2 focus:ring-hearth-400 focus:ring-offset-1
        dark:focus:ring-offset-hearth-900
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${className}
      `.trim()}
      disabled={disabled}
      {...rest}
    >
      {children}
    </button>
  );
}
