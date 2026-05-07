"use client";

import { useMemo } from "react";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import type { ProgressEvent } from "@/types/events";

interface AnalysisProgressProps {
  events: ProgressEvent[];
}

const STEPS = [
  { key: "load_issue", label: "Loading Issue", description: "Fetching issue details from Jira" },
  { key: "route_profile", label: "Routing Profile", description: "Determining analysis approach" },
  { key: "retrieve_evidence", label: "Retrieving Evidence", description: "Searching knowledge base" },
  { key: "generate_analysis", label: "Generating Analysis", description: "AI analysis in progress" },
];

export default function AnalysisProgress({ events }: AnalysisProgressProps) {
  // Memoize status map to avoid O(n²) array scans on every render
  const statusMap = useMemo(() => {
    return events.reduce((acc, event) => {
      acc[event.step] = event;
      return acc;
    }, {} as Record<string, ProgressEvent>);
  }, [events]);

  return (
    <div className="glass rounded-2xl p-8 shadow-lg mb-8">
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">Analysis Progress</h2>

      <div className="space-y-4">
        {STEPS.map((step, index) => {
          const event = statusMap[step.key];
          const status = event?.status || "pending";
          const message = event?.message || "";

          return (
            <div key={step.key} className="flex items-start gap-4">
              {/* Icon */}
              <div className="flex-shrink-0 mt-1">
                {status === "completed" && (
                  <CheckCircle2 className="w-6 h-6 text-green-500" />
                )}
                {status === "running" && (
                  <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                )}
                {status === "pending" && (
                  <Circle className="w-6 h-6 text-slate-300" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className={`font-medium ${
                    status === "completed" ? "text-slate-900" :
                    status === "running" ? "text-blue-600" :
                    "text-slate-400"
                  }`}>
                    {step.label}
                  </h3>
                  {status === "running" && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                      In Progress
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-500 mb-1">{step.description}</p>
                {message && (
                  <p className="text-sm text-slate-600 bg-slate-50 rounded px-3 py-2 mt-2">
                    {message}
                  </p>
                )}
              </div>

              {/* Connector Line */}
              {index < STEPS.length - 1 && (
                <div className="absolute left-[2.75rem] mt-8 w-0.5 h-12 bg-slate-200" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
