import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { AlertCircle, CheckCircle2, Info, AlertTriangle, X } from 'lucide-react';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'success' | 'error' | 'warning' | 'info';
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
}

const Alert = forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'info', title, dismissible, onDismiss, children, ...props }, ref) => {
    const variants = {
      success: {
        container: 'bg-success-50 dark:bg-success-950/20 border-success-200 dark:border-success-800',
        icon: 'text-success-600 dark:text-success-400',
        title: 'text-success-800 dark:text-success-200',
        text: 'text-success-700 dark:text-success-300',
        iconComponent: CheckCircle2,
      },
      error: {
        container: 'bg-error-50 dark:bg-error-950/20 border-error-200 dark:border-error-800',
        icon: 'text-error-600 dark:text-error-400',
        title: 'text-error-800 dark:text-error-200',
        text: 'text-error-700 dark:text-error-300',
        iconComponent: AlertCircle,
      },
      warning: {
        container: 'bg-warning-50 dark:bg-warning-950/20 border-warning-200 dark:border-warning-800',
        icon: 'text-warning-600 dark:text-warning-400',
        title: 'text-warning-800 dark:text-warning-200',
        text: 'text-warning-700 dark:text-warning-300',
        iconComponent: AlertTriangle,
      },
      info: {
        container: 'bg-info-50 dark:bg-info-950/20 border-info-200 dark:border-info-800',
        icon: 'text-info-600 dark:text-info-400',
        title: 'text-info-800 dark:text-info-200',
        text: 'text-info-700 dark:text-info-300',
        iconComponent: Info,
      },
    };

    const variantStyles = variants[variant];
    const IconComponent = variantStyles.iconComponent;

    return (
      <div
        ref={ref}
        className={cn(
          'relative flex items-start gap-3 rounded-lg border p-4',
          variantStyles.container,
          className
        )}
        role="alert"
        {...props}
      >
        <IconComponent className={cn('h-5 w-5 flex-shrink-0 mt-0.5', variantStyles.icon)} />
        <div className="flex-1">
          {title && (
            <h4 className={cn('font-semibold mb-1', variantStyles.title)}>
              {title}
            </h4>
          )}
          <div className={cn('text-sm', variantStyles.text)}>
            {children}
          </div>
        </div>
        {dismissible && (
          <button
            onClick={onDismiss}
            className={cn('ml-auto flex-shrink-0 rounded-md p-1 transition-colors hover:bg-black/5 dark:hover:bg-white/5', variantStyles.text)}
            aria-label="Dismiss alert"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;
