import { useState, useEffect, useRef, useCallback, forwardRef } from 'react';

interface DebouncedInputProps {
  value: string;
  onChange: (value: string) => void;
  delay?: number;
  placeholder?: string;
  type?: string;
  className?: string;
  ariaLabel?: string;
}

export const DebouncedInput = forwardRef<HTMLInputElement, DebouncedInputProps>(
  ({ value, onChange, delay = 300, placeholder, type = 'text', className, ariaLabel }, ref) => {
    const [localValue, setLocalValue] = useState(value);
    const debounceRef = useRef<ReturnType<typeof setTimeout>>();

    useEffect(() => {
      setLocalValue(value);
    }, [value]);

    const handleChange = useCallback(
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const next = e.target.value;
        setLocalValue(next);

        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => {
          onChange(next);
        }, delay);
      },
      [onChange, delay],
    );

    useEffect(() => {
      return () => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
      };
    }, []);

    return (
      <input
        ref={ref}
        type={type}
        value={localValue}
        onChange={handleChange}
        placeholder={placeholder}
        className={className}
        aria-label={ariaLabel}
      />
    );
  },
);

DebouncedInput.displayName = 'DebouncedInput';
