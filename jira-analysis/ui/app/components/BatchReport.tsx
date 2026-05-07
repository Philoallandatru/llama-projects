"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, ChevronDown, ChevronRight, Download, BookOpen } from "lucide-react";

interface BatchReportProps {
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
}

export default function BatchReport({ summary, reports }: BatchReportProps) {
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());

  const toggleIssue = (key: string) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(key)) {
      newExpanded.delete(key);
    } else {
      newExpanded.add(key);
    }
    setExpandedIssues(newExpanded);
  };

  const expandAll = () => {
    setExpandedIssues(new Set(reports.map(r => r.issue_key)));
  };

  const collapseAll = () => {
    setExpandedIssues(new Set());
  };

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="glass rounded-2xl p-8 shadow-lg">
        <h2 className="text-2xl font-semibold text-slate-900 mb-6">Batch Analysis Summary</h2>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-200">
            <div className="text-sm font-medium text-purple-900 mb-1">Total Issues</div>
            <div className="text-3xl font-bold text-purple-600">{summary.total}</div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
            <div className="text-sm font-medium text-green-900 mb-1">Completed</div>
            <div className="text-3xl font-bold text-green-600">{summary.completed}</div>
          </div>

          <div className="bg-gradient-to-br from-red-50 to-rose-50 rounded-lg p-4 border border-red-200">
            <div className="text-sm font-medium text-red-900 mb-1">Errors</div>
            <div className="text-3xl font-bold text-red-600">{summary.errors}</div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4 border border-blue-200">
            <div className="text-sm font-medium text-blue-900 mb-1">Success Rate</div>
            <div className="text-3xl font-bold text-blue-600">
              {summary.total > 0 ? Math.round((summary.completed / summary.total) * 100) : 0}%
            </div>
          </div>
        </div>

        {/* Profile Distribution */}
        {Object.keys(summary.profiles).length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-3">Profile Distribution</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(summary.profiles).map(([profile, count]) => (
                <div
                  key={profile}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-200"
                >
                  <span className="text-sm font-medium text-slate-700">{profile}</span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-sm font-semibold">
                    {count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Reports List */}
      <div className="glass rounded-2xl p-8 shadow-lg">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-slate-900">Individual Reports</h2>
          <div className="flex gap-2">
            <button
              onClick={expandAll}
              className="px-3 py-1.5 text-sm font-medium text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 rounded-lg transition-colors"
            >
              Collapse All
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {reports.map((report) => {
            const isExpanded = expandedIssues.has(report.issue_key);
            const hasError = !!report.error;

            return (
              <div
                key={report.issue_key}
                className={`border rounded-lg overflow-hidden transition-all ${
                  hasError ? "border-red-300 bg-red-50" : "border-slate-200 bg-white"
                }`}
              >
                {/* Header */}
                <button
                  onClick={() => toggleIssue(report.issue_key)}
                  className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    )}
                    <FileText className={`w-5 h-5 ${hasError ? "text-red-600" : "text-purple-600"}`} />
                    <span className="font-mono font-semibold text-slate-900">
                      {report.issue_key}
                    </span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                      {report.profile}
                    </span>
                  </div>
                  {hasError && (
                    <span className="text-sm text-red-600 font-medium">Error</span>
                  )}
                </button>

                {/* Content */}
                {isExpanded && (
                  <div className="border-t border-slate-200 p-6 bg-white">
                    {hasError ? (
                      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">{report.error}</p>
                      </div>
                    ) : (
                      <div className="prose prose-slate max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {report.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
