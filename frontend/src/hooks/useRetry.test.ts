import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useRetry, fetchWithRetry } from './useRetry';

describe('useRetry', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('returns data on successful call', async () => {
    const mockFn = vi.fn().mockResolvedValue({ data: 'success' });
    const { result } = renderHook(() => useRetry(mockFn));

    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.data).toEqual({ data: 'success' });
    expect(result.current.error).toBeNull();
    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it('retries on failure', async () => {
    const mockFn = vi.fn()
      .mockRejectedValueOnce(new Error('First fail'))
      .mockRejectedValueOnce(new Error('Second fail'))
      .mockResolvedValue({ data: 'success' });

    const { result } = renderHook(() => 
      useRetry(mockFn, { maxRetries: 3, initialDelay: 100 })
    );

    const executePromise = act(async () => {
      await result.current.execute();
    });

    await vi.advanceTimersByTimeAsync(100); // First retry delay
    await vi.advanceTimersByTimeAsync(200); // Second retry delay

    await executePromise;

    expect(mockFn).toHaveBeenCalledTimes(3);
    expect(result.current.data).toEqual({ data: 'success' });
  });

  it('returns error after max retries', async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error('Always fails'));
    const { result } = renderHook(() => 
      useRetry(mockFn, { maxRetries: 2, initialDelay: 100 })
    );

    await act(async () => {
      try {
        await result.current.execute();
      } catch (e) {
        // Expected
      }
    });

    await vi.advanceTimersByTimeAsync(300); // All delays

    expect(result.current.error).toBeInstanceOf(Error);
    expect(mockFn).toHaveBeenCalledTimes(3); // Initial + 2 retries
  });

  it('resets state correctly', () => {
    const mockFn = vi.fn().mockResolvedValue({ data: 'success' });
    const { result } = renderHook(() => useRetry(mockFn));

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('calls onRetry callback', async () => {
    const onRetry = vi.fn();
    const mockFn = vi.fn()
      .mockRejectedValueOnce(new Error('Fail'))
      .mockResolvedValue({ data: 'success' });

    const { result } = renderHook(() => 
      useRetry(mockFn, { maxRetries: 2, initialDelay: 100, onRetry })
    );

    await act(async () => {
      await result.current.execute();
    });

    await vi.advanceTimersByTimeAsync(100);

    expect(onRetry).toHaveBeenCalledWith(1, expect.any(Error));
  });
});

describe('fetchWithRetry', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('returns data on successful fetch', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'success' }),
    });

    const result = await fetchWithRetry('/api/test');
    expect(result).toEqual({ data: 'success' });
  });

  it('does not retry on 4xx errors (except 429)', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
    });

    await expect(fetchWithRetry('/api/test', {}, { maxRetries: 3 }))
      .rejects.toThrow('HTTP 400');
    
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});
