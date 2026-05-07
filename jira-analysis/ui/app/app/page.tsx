"use client";

import { useState } from "react";
import { Search, Sparkles } from "lucide-react";
import AnalysisProgress from "@/components/AnalysisProgress";
import AnalysisResults from "@/components/AnalysisResults";

export default function DeepAnalysisPage() {
  const [issueKey, setIssueKey] = useState("");
  const [analysisMode, setAnalysisMode] = useState<"deep" | "quick">("deep");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [results, setResults] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!issueKey.trim()) return;

    setIsAnalyzing(true);
    setEvents([]);
    setResults(null);

    try {
      const response = await fetch("http://localhost:4501/deployments/jira-analysis/tasks/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow: "deep_analysis",
          params: { issue_key: issueKey.trim() },
        }),
      });

      if (!response.ok) throw new Error("Failed to start analysis");

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
            const data = JSON.parse(line.slice(6));

            if (data.type === "progress") {
              setEvents((prev) => [...prev, data]);
            } else if (data.type === "result") {
              setResults(data.data);
            }
          }
        }
      }
    } catch (error) {
      console.error("Analysis failed:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="container mx-auto px-6 py-12 max-w-6xl">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 text-blue-700 text-sm font-medium mb-4">
          <Sparkles className="w-4 h-4" />
          <span>AI-Powered Deep Analysis</span>
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-4">
          Analyze Jira Issues
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Get comprehensive insights with cross-source evidence retrieval, root cause analysis, and actionable recommendations.
        </p>
      </div>

      {/* Input Section */}
      <div className="glass rounded-2xl p-8 shadow-lg mb-8">
        <div className="flex flex-col gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Issue Key
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={issueKey}
                onChange={(e) => setIssueKey(e.target.value)}
                placeholder="e.g., KAN-9"
                className="flex-1 px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isAnalyzing}
              />
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing || !issueKey.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow-md"
              >
                <Search className="w-5 h-5" />
                {isAnalyzing ? "Analyzing..." : "Analyze"}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Analysis Mode
            </label>
            <div className="flex gap-3">
              <button
                onClick={() => setAnalysisMode("deep")}
                className={`flex-1 px-4 py-3 rounded-lg font-medium transition-all ${
                  analysisMode === "deep"
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-white text-slate-700 border border-slate-300 hover:border-blue-400"
                }`}
                disabled={isAnalyzing}
              >
                Deep Analysis
              </button>
              <button
                onClick={() => setAnalysisMode("quick")}
                className={`flex-1 px-4 py-3 rounded-lg font-medium transition-all ${
                  analysisMode === "quick"
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-white text-slate-700 border border-slate-300 hover:border-blue-400"
                }`}
                disabled={isAnalyzing}
              >
                Quick Analysis
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Section */}
      {isAnalyzing && events.length > 0 && (
        <AnalysisProgress events={events} />
      )}

      {/* Results Section */}
      {results && (
        <AnalysisResults results={results} issueKey={issueKey} />
      )}
    </div>
  );
}
