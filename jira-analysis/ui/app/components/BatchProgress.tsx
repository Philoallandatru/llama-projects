"use client";

import { CheckCircle2, Loader2, Circle, XCircle, Clock } from "lucide-react";

interface BatchProgressProps {
  total: number;
  current: number;
  items: Array<{
    key: string;
    status: "pending" | "running" | "completed" | "error";
    profile?: string;
    message?: string;
  }>;
  estimatedTimeRemaining?: number;
}

export default function BatchProgress({ total, current, items, estimatedTimeRemaining }: BatchProgressProps) {
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
  const completed = items.filter(i => i.status === "completed").length;
  const errors = items.filter(i => i.status === "error").length;

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  return (
    <div className="glass rounded-2xl p-8 shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-slate-900">Batch Progress</h2>
        {estimatedTimeRemaining !== undefined && estimatedTimeRemaining > 0 && (
          <div className="flex items-center gap-2 text-slate-600">
            <Clock className="w-4 h-4" />
            <span className="text-sm">~{formatTime(estimatedTimeRemaining)} remaining</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-slate-700">
            {current} / {total} issues
          </span>
          <span className="text-sm font-semibold text-purple-600">{percentage}%</span>
        </div>
        <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-600 to-indigo-600 transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-900">Completed</span>
          </div>
          <div className="text-2xl font-bold text-green-600">{completed}</div>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center gap-2 mb-1">
            <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
            <span className="text-sm font-medium text-blue-900">In Progress</span>
          </div>
          <div className="text-2xl font-bold text-blue-600">{current - completed - errors}</div>
        </div>

        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <div className="flex items-center gap-2 mb-1">
            <XCircle className="w-4 h-4 text-red-600" />
            <span className="text-sm font-medium text-red-900">Errors</span>
          </div>
          <div className="text-2xl font-bold text-red-600">{errors}</div>
        </div>
      </div>

      {/* Issue List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {items.map((item) => (
          <div
            key={item.key}
            className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
              item.status === "completed"
                ? "bg-green-50 border border-green-200"
                : item.status === "error"
                ? "bg-red-50 border border-red-200"
                : item.status === "running"
                ? "bg-blue-50 border border-blue-200"
                : "bg-slate-50 border border-slate-200"
            }`}
          >
            {/* Status Icon */}
            <div className="flex-shrink-0">
              {item.status === "completed" && (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              )}
              {item.status === "running" && (
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              )}
              {item.status === "error" && (
                <XCircle className="w-5 h-5 text-red-600" />
              )}
              {item.status === "pending" && (
                <Circle className="w-5 h-5 text-slate-400" />
              )}
            </div>

            {/* Issue Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`font-mono text-sm font-medium ${
                  item.status === "completed"
                    ? "text-green-900"
                    : item.status === "error"
                    ? "text-red-900"
                    : item.status === "running"
                    ? "text-blue-900"
                    : "text-slate-600"
                }`}>
                  {item.key}
                </span>
                {item.profile && (
                  <span className="px-2 py-0.5 bg-white rounded text-xs font-medium text-slate-600">
                    {item.profile}
                  </span>
                )}
              </div>
              {item.message && (
                <p className="text-xs text-slate-600 mt-1 truncate">{item.message}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
