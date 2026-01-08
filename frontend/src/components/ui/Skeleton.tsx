import { HTMLAttributes } from 'react';
import { cn } from '../../utils/cn';

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export default function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  style,
  ...props
}: SkeletonProps) {
  const baseStyles = 'animate-shimmer bg-gray-200 dark:bg-gray-700 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 bg-[length:200%_100%]';

  const variants = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded',
  };

  return (
    <div
      className={cn(baseStyles, variants[variant], className)}
      style={{
        width: width || (variant === 'circular' ? height || '40px' : undefined),
        height: height || (variant === 'text' ? '1rem' : variant === 'circular' ? width || '40px' : '1rem'),
        ...style,
      }}
      {...props}
    />
  );
}
