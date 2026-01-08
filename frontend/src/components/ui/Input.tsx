import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  label?: string;
  helperText?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error, label, helperText, id, ...props }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
          >
            {label}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            'flex h-10 w-full rounded-lg border bg-white dark:bg-gray-800 px-3 py-2 text-sm',
            'ring-offset-white dark:ring-offset-gray-900',
            'file:border-0 file:bg-transparent file:text-sm file:font-medium',
            'placeholder:text-gray-400 dark:placeholder:text-gray-500',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error
              ? 'border-error-500 dark:border-error-500 focus-visible:ring-error-500'
              : 'border-gray-300 dark:border-gray-700',
            className
          )}
          ref={ref}
          {...props}
        />
        {helperText && (
          <p className={cn('mt-1.5 text-sm', error ? 'text-error-600 dark:text-error-400' : 'text-gray-500 dark:text-gray-400')}>
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
