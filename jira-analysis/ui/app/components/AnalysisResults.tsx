"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { FileText, ExternalLink, Tag } from "lucide-react";

interface AnalysisResultsProps {
  results: {
    issue_key: string;
    summary: string;
    profile: string;
    analysis: string;
    evidence: Array<{
      source: string;
      content: string;
      score: number;
      metadata?: Record<string, any>;
    }>;
  };
  issueKey: string;
}

export default function AnalysisResults({ results, issueKey }: AnalysisResultsProps) {
  return (
    <div className="space-y-6">
      {/* Issue Header */}
      <div className="glass rounded-2xl p-6 shadow-lg">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg font-mono text-sm font-medium">
                {results.issue_key}
              </span>
              <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium">
                {results.profile}
              </span>
            </div>
            <h2 className="text-2xl font-semibold text-slate-900">{results.summary}</h2>
          </div>
          <a
            href={`https://your-domain.atlassian.net/browse/${results.issue_key}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <span className="text-sm font-medium">View in Jira</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>

      {/* Analysis Content */}
      <div className="glass rounded-2xl p-8 shadow-lg">
        <div className="flex items-center gap-2 mb-6">
          <FileText className="w-5 h-5 text-blue-600" />
          <h3 className="text-xl font-semibold text-slate-900">Analysis Report</h3>
        </div>

        <div className="prose prose-slate max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              h1: ({ children }) => (
                <h1 className="text-2xl font-bold text-slate-900 mt-6 mb-4">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-xl font-semibold text-slate-900 mt-5 mb-3">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold text-slate-800 mt-4 mb-2">{children}</h3>
              ),
              p: ({ children }) => (
                <p className="text-slate-700 leading-relaxed mb-4">{children}</p>
              ),
              ul: ({ children }) => (
                <ul className="list-disc list-inside space-y-2 mb-4 text-slate-700">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-inside space-y-2 mb-4 text-slate-700">{children}</ol>
              ),
              code: ({ inline, children, ...props }: any) =>
                inline ? (
                  <code className="px-1.5 py-0.5 bg-slate-100 text-slate-800 rounded text-sm font-mono" {...props}>
                    {children}
                  </code>
                ) : (
                  <code className="block bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm font-mono" {...props}>
                    {children}
                  </code>
                ),
            }}
          >
            {results.analysis}
          </ReactMarkdown>
        </div>
      </div>

      {/* Evidence Section */}
      {results.evidence && results.evidence.length > 0 && (
        <div className="glass rounded-2xl p-8 shadow-lg">
          <div className="flex items-center gap-2 mb-6">
            <Tag className="w-5 h-5 text-purple-600" />
            <h3 className="text-xl font-semibold text-slate-900">Supporting Evidence</h3>
            <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-sm font-medium">
              {results.evidence.length} sources
            </span>
          </div>

          <div className="grid gap-4">
            {results.evidence.map((item, index) => (
              <div
                key={index}
                className="bg-white rounded-lg p-4 border border-slate-200 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-900">{item.source}</span>
                    {item.metadata?.issue_key && (
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-mono">
                        {item.metadata.issue_key}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-500">
                    Score: {(item.score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-sm text-slate-600 leading-relaxed">{item.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
