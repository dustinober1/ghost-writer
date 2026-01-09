import { useState, useCallback } from 'react';

interface RetryOptions {
  maxRetries?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
  onRetry?: (attempt: number, error: Error) => void;
}

interface RetryState<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
  attempt: number;
}

export function useRetry<T>(
  asyncFn: () => Promise<T>,
  options: RetryOptions = {}
) {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    backoffFactor = 2,
    onRetry,
  } = options;

  const [state, setState] = useState<RetryState<T>>({
    data: null,
    error: null,
    isLoading: false,
    attempt: 0,
  });

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null, attempt: 0 }));

    let lastError: Error | null = null;
    let delay = initialDelay;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const data = await asyncFn();
        setState({ data, error: null, isLoading: false, attempt });
        return data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        if (attempt < maxRetries) {
          onRetry?.(attempt + 1, lastError);
          setState((prev) => ({ ...prev, attempt: attempt + 1 }));
          
          // Wait before retry with exponential backoff
          await new Promise((resolve) => setTimeout(resolve, delay));
          delay = Math.min(delay * backoffFactor, maxDelay);
        }
      }
    }

    setState((prev) => ({ ...prev, error: lastError, isLoading: false }));
    throw lastError;
  }, [asyncFn, maxRetries, initialDelay, maxDelay, backoffFactor, onRetry]);

  const reset = useCallback(() => {
    setState({ data: null, error: null, isLoading: false, attempt: 0 });
  }, []);

  return { ...state, execute, reset };
}

// Utility function for API calls with retry
export async function fetchWithRetry<T>(
  url: string,
  options: RequestInit = {},
  retryOptions: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    backoffFactor = 2,
  } = retryOptions;

  let lastError: Error | null = null;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        // Don't retry client errors (4xx) except 429 (rate limit)
        if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, delay));
        delay = Math.min(delay * backoffFactor, maxDelay);
      }
    }
  }

  throw lastError;
}

export default useRetry;
