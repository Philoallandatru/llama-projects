import { useCallback, useRef, useState } from "react";

interface SSEStreamOptions<T> {
  url: string;
  onProgress?: (data: any) => void;
  onResult?: (data: T) => void;
  onError?: (error: Error) => void;
  maxEvents?: number; // Sliding window size to prevent memory leak
}

interface SSEStreamState {
  isStreaming: boolean;
  error: string | null;
}

/**
 * Custom hook for handling Server-Sent Events (SSE) streams
 *
 * Features:
 * - Automatic connection management
 * - Memory leak prevention with sliding window
 * - Error handling and cleanup
 * - TypeScript support
 *
 * @example
 * const { startStream, stopStream, isStreaming } = useSSEStream({
 *   url: '/api/analyze',
 *   onProgress: (data) => console.log('Progress:', data),
 *   onResult: (data) => console.log('Result:', data),
 *   maxEvents: 100
 * });
 */
export function useSSEStream<T = any>(options: SSEStreamOptions<T>) {
  const {
    url,
    onProgress,
    onResult,
    onError,
    maxEvents = 100, // Default: keep last 100 events
  } = options;

  const [state, setState] = useState<SSEStreamState>({
    isStreaming: false,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const eventsRef = useRef<any[]>([]);

  const startStream = useCallback(async () => {
    // Clean up previous stream if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Reset state
    setState({ isStreaming: true, error: null });
    eventsRef.current = [];

    // Create new abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch(url, {
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          setState({ isStreaming: false, error: null });
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              // Implement sliding window to prevent memory leak
              eventsRef.current.push(data);
              if (eventsRef.current.length > maxEvents) {
                eventsRef.current = eventsRef.current.slice(-maxEvents);
              }

              // Handle different event types
              if (data.type === "ProgressEvent" || data.type === "progress") {
                onProgress?.(data.data || data);
              } else if (
                data.type === "result" ||
                data.type === "AnalysisResultEvent"
              ) {
                onResult?.(data.data || data);
              } else if (data.type === "error") {
                const error = new Error(data.message || "Stream error");
                onError?.(error);
                setState({ isStreaming: false, error: error.message });
              } else {
                // Generic progress event
                onProgress?.(data);
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        // Stream was intentionally aborted
        setState({ isStreaming: false, error: null });
      } else {
        const errorMessage = error.message || "Stream connection failed";
        setState({ isStreaming: false, error: errorMessage });
        onError?.(error);
      }
    }
  }, [url, onProgress, onResult, onError, maxEvents]);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState({ isStreaming: false, error: null });
  }, []);

  return {
    startStream,
    stopStream,
    isStreaming: state.isStreaming,
    error: state.error,
    events: eventsRef.current,
  };
}
