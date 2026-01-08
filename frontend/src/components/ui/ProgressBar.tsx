import { HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  max?: number;
  showLabel?: boolean;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function ProgressBar({
  className,
  value,
  max = 100,
  showLabel = false,
  label,
  size = 'md',
  ...props
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={cn('w-full', className)} {...props}>
      {showLabel && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {label || `${Math.round(percentage)}%`}
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className={cn('w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden', sizes[size])}>
        <div
          className="h-full bg-primary-600 dark:bg-primary-500 transition-all duration-300 ease-out rounded-full"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
}
