import { useCallback, useRef, useState } from "react";
import type { SSEEvent, ProgressEvent, AnalysisResultEvent } from "@/types/events";

interface SSEStreamOptions {
  url: string;
  maxEvents?: number; // Sliding window size to prevent memory leak
}

/**
 * Custom hook for handling Server-Sent Events (SSE) streams with consolidated state
 *
 * Features:
 * - Consolidated state management (events, results, streaming status)
 * - Memory leak prevention with sliding window
 * - Error handling and cleanup
 * - TypeScript support
 *
 * @example
 * const { events, results, isStreaming, startAnalysis, reset } = useSSEStream({
 *   url: '/api/analyze',
 *   maxEvents: 100
 * });
 *
 * await startAnalysis({ issue_key: 'KAN-9', mode: 'balanced' });
 */
export function useSSEStream(options: SSEStreamOptions) {
  const {
    url,
    maxEvents = 100, // Default: keep last 100 events
  } = options;

  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [results, setResults] = useState<AnalysisResultEvent["data"] | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const startAnalysis = useCallback(async (body: any) => {
    // Clean up previous stream if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Reset state
    setIsStreaming(true);
    setError(null);

    // Create new abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
          setIsStreaming(false);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              // Handle different event types
              if (data.type === "ProgressEvent" || data.type === "progress") {
                setEvents((prev) => {
                  const updated = [...prev, data];
                  return updated.length > maxEvents ? updated.slice(-maxEvents) : updated;
                });
              } else if (data.type === "result" || data.type === "AnalysisResultEvent") {
                setResults(data.data || data);
              } else if (data.type === "error") {
                const errorMsg = data.message || "Stream error";
                setError(errorMsg);
                setIsStreaming(false);
              } else {
                // Generic progress event
                setEvents((prev) => {
                  const updated = [...prev, data];
                  return updated.length > maxEvents ? updated.slice(-maxEvents) : updated;
                });
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
        setIsStreaming(false);
      } else {
        const errorMessage = error.message || "Stream connection failed";
        setError(errorMessage);
        setIsStreaming(false);
      }
    }
  }, [url, maxEvents]);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const reset = useCallback(() => {
    setEvents([]);
    setResults(null);
    setError(null);
  }, []);

  return {
    events,
    results,
    isStreaming,
    error,
    startAnalysis,
    stopStream,
    reset,
  };
}
