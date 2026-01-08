import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { X, CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import { cn } from '../utils/cn';

export type ToastVariant = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (message: string, options?: Partial<Toast>) => void;
  error: (message: string, options?: Partial<Toast>) => void;
  warning: (message: string, options?: Partial<Toast>) => void;
  info: (message: string, options?: Partial<Toast>) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = { ...toast, id };
    
    setToasts((prev) => [...prev, newToast]);

    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const success = useCallback((message: string, options?: Partial<Toast>) => {
    addToast({ message, variant: 'success', ...options });
  }, [addToast]);

  const error = useCallback((message: string, options?: Partial<Toast>) => {
    addToast({ message, variant: 'error', ...options });
  }, [addToast]);

  const warning = useCallback((message: string, options?: Partial<Toast>) => {
    addToast({ message, variant: 'warning', ...options });
  }, [addToast]);

  const info = useCallback((message: string, options?: Partial<Toast>) => {
    addToast({ message, variant: 'info', ...options });
  }, [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({ toasts, removeToast }: { toasts: Toast[]; removeToast: (id: string) => void }) {
  if (toasts.length === 0) return null;

  const container = (
    <div className="fixed bottom-0 right-0 z-50 flex flex-col gap-2 p-4 w-full sm:w-96 max-w-full">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
      ))}
    </div>
  );

  return createPortal(container, document.body);
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const icons = {
    success: CheckCircle2,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  };

  const styles = {
    success: 'bg-success-50 dark:bg-success-950/20 border-success-200 dark:border-success-800 text-success-800 dark:text-success-200',
    error: 'bg-error-50 dark:bg-error-950/20 border-error-200 dark:border-error-800 text-error-800 dark:text-error-200',
    warning: 'bg-warning-50 dark:bg-warning-950/20 border-warning-200 dark:border-warning-800 text-warning-800 dark:text-warning-200',
    info: 'bg-info-50 dark:bg-info-950/20 border-info-200 dark:border-info-800 text-info-800 dark:text-info-200',
  };

  const Icon = icons[toast.variant];

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border p-4 shadow-large animate-slide-up',
        styles[toast.variant]
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{toast.message}</p>
        {toast.action && (
          <button
            onClick={toast.action.onClick}
            className="mt-2 text-sm font-semibold underline"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        onClick={() => onRemove(toast.id)}
        className="flex-shrink-0 rounded-md p-1 hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
