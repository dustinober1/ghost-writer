import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    const variants = {
      default: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
      success: 'bg-success-100 text-success-800 dark:bg-success-900/30 dark:text-success-300',
      error: 'bg-error-100 text-error-800 dark:bg-error-900/30 dark:text-error-300',
      warning: 'bg-warning-100 text-warning-800 dark:bg-warning-900/30 dark:text-warning-300',
      info: 'bg-info-100 text-info-800 dark:bg-info-900/30 dark:text-info-300',
      outline: 'border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-2.5 py-1 text-sm',
      lg: 'px-3 py-1.5 text-base',
    };

    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full font-medium',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
