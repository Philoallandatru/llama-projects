/**
 * Shared event type definitions for SSE streaming
 *
 * These types match the backend event structure from the workflow
 */

export interface ProgressEvent {
  type: "ProgressEvent" | "progress";
  step: string;
  message: string;
  status: "pending" | "running" | "completed" | "error";
  timestamp?: string;
}

export interface AnalysisResultEvent {
  type: "AnalysisResultEvent" | "result";
  data: {
    issue_key: string;
    profile: string;
    mode: string;
    analysis: string;
    evidence_count?: {
      similar_issues: number;
      confluence: number;
      specs: number;
    };
    evidence?: Array<{
      source: string;
      title: string;
      content: string;
      score: number;
      url?: string;
    }>;
  };
}

export interface BatchProgressEvent {
  type: "BatchProgressEvent" | "batch_progress";
  data: {
    current: number;
    total: number;
    message: string;
    estimated_time_remaining?: number;
    items: Array<{
      key: string;
      status: "pending" | "running" | "completed" | "error";
      profile?: string;
      message?: string;
    }>;
  };
}

export interface BatchReportEvent {
  type: "BatchReportEvent" | "batch_report";
  data: {
    summary: {
      total: number;
      completed: number;
      errors: number;
      profiles: Record<string, number>;
    };
    reports: Array<{
      issue_key: string;
      profile: string;
      content: string;
      error?: string;
    }>;
  };
}

export interface ErrorEvent {
  type: "error";
  message: string;
  details?: any;
}

export type SSEEvent =
  | ProgressEvent
  | AnalysisResultEvent
  | BatchProgressEvent
  | BatchReportEvent
  | ErrorEvent;
