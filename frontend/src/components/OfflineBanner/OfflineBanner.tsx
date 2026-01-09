import { useEffect, useState } from 'react';
import { WifiOff, Wifi, X } from 'lucide-react';
import { cn } from '../../utils/cn';
import useOfflineDetection from '../../hooks/useOfflineDetection';

export default function OfflineBanner() {
  const { isOnline, wasOffline, clearWasOffline } = useOfflineDetection();
  const [showReconnected, setShowReconnected] = useState(false);

  useEffect(() => {
    if (wasOffline && isOnline) {
      setShowReconnected(true);
      const timer = setTimeout(() => {
        setShowReconnected(false);
        clearWasOffline();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [wasOffline, isOnline, clearWasOffline]);

  if (isOnline && !showReconnected) {
    return null;
  }

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-50 px-4 py-3 flex items-center justify-center gap-2 text-sm font-medium transition-all duration-300',
        !isOnline
          ? 'bg-red-600 text-white'
          : 'bg-green-600 text-white'
      )}
    >
      {!isOnline ? (
        <>
          <WifiOff className="h-4 w-4" />
          <span>You are offline. Some features may not be available.</span>
        </>
      ) : (
        <>
          <Wifi className="h-4 w-4" />
          <span>Back online!</span>
          <button
            onClick={() => {
              setShowReconnected(false);
              clearWasOffline();
            }}
            className="ml-2 p-1 hover:bg-white/20 rounded"
          >
            <X className="h-4 w-4" />
          </button>
        </>
      )}
    </div>
  );
}
