"use client";

import { useState } from "react";
import { FileText, Sparkles } from "lucide-react";
import BatchConfigPanel, { BatchConfig } from "@/components/BatchConfigPanel";
import BatchProgress from "@/components/BatchProgress";
import BatchReport from "@/components/BatchReport";
import ExportOptions from "@/components/ExportOptions";

interface BatchProgressEvent {
  type: "batch_progress";
  data: {
    current: number;
    total: number;
    message: string;
    items: Array<{
      key: string;
      status: "pending" | "running" | "completed" | "error";
      profile?: string;
      message?: string;
    }>;
  };
}

interface BatchResultEvent {
  type: "result";
  data: {
    total: number;
    completed: number;
    errors: number;
    profiles: Record<string, number>;
    reports: Array<{
      issue_key: string;
      profile: string;
      content: string;
      error?: string;
    }>;
  };
}

export default function ReportsPage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState<BatchProgressEvent["data"] | null>(null);
  const [results, setResults] = useState<BatchResultEvent["data"] | null>(null);

  const handleStartAnalysis = async (config: BatchConfig) => {
    setIsAnalyzing(true);
    setProgress(null);
    setResults(null);

    try {
      const response = await fetch("http://localhost:4501/api/batch-analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!response.ok) throw new Error("Failed to start batch analysis");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No response body");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "BatchProgressEvent") {
                setProgress(data.data);
              } else if (data.type === "result") {
                setResults(data.data);
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Batch analysis failed:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="container mx-auto px-6 py-12 max-w-6xl">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-100 text-purple-700 text-sm font-medium mb-4">
          <Sparkles className="w-4 h-4" />
          <span>Batch Analysis & Reports</span>
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Generate Reports
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Analyze multiple issues in batch and generate comprehensive reports with AI-powered insights.
        </p>
      </div>

      {/* Configuration Panel */}
      <div className="mb-8">
        <BatchConfigPanel
          onStartAnalysis={handleStartAnalysis}
          isAnalyzing={isAnalyzing}
        />
      </div>

      {/* Progress Display */}
      {isAnalyzing && progress && (
        <div className="mb-8">
          <BatchProgress
            total={progress.total}
            current={progress.current}
            items={progress.items}
          />
        </div>
      )}

      {/* Results Display */}
      {results && (
        <>
          <div className="mb-8">
            <ExportOptions
              reportData={{
                summary: {
                  total: results.total,
                  completed: results.completed,
                  errors: results.errors,
                  profiles: results.profiles,
                },
                reports: results.reports,
              }}
            />
          </div>
          <BatchReport
            summary={{
              total: results.total,
              completed: results.completed,
              errors: results.errors,
              profiles: results.profiles,
            }}
            reports={results.reports}
          />
        </>
      )}

      {/* Empty State */}
      {!isAnalyzing && !progress && !results && (
        <div className="glass rounded-2xl p-12 shadow-lg text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <FileText className="w-10 h-10 text-purple-600" />
          </div>
          <h2 className="text-2xl font-semibold text-slate-900 mb-3">
            Ready to Analyze
          </h2>
          <p className="text-slate-600 mb-8 max-w-md mx-auto">
            Add issue keys above and click "Analyze" to start batch analysis.
            You can analyze multiple issues at once and get a comprehensive report.
          </p>

          <div className="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="bg-white rounded-lg p-6 border border-slate-200">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Batch Processing</h3>
              <p className="text-sm text-slate-600">
                Analyze multiple issues simultaneously with real-time progress tracking
              </p>
            </div>

            <div className="bg-white rounded-lg p-6 border border-slate-200">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-indigo-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">AI Insights</h3>
              <p className="text-sm text-slate-600">
                Get comprehensive analysis with evidence retrieval and recommendations
              </p>
            </div>

            <div className="bg-white rounded-lg p-6 border border-slate-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900 mb-2">Detailed Reports</h3>
              <p className="text-sm text-slate-600">
                View summary statistics and individual issue reports in one place
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
