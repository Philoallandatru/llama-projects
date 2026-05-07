"use client";

import { useState } from "react";
import { Calendar, Filter, Search, Plus, X } from "lucide-react";

interface BatchConfigProps {
  onStartAnalysis: (config: BatchConfig) => void;
  isAnalyzing: boolean;
}

export interface BatchConfig {
  issue_keys: string[];
  mode: "strict" | "balanced" | "exploratory";
  retrieve_evidence: boolean;
}

export default function BatchConfigPanel({ onStartAnalysis, isAnalyzing }: BatchConfigProps) {
  const [issueKeys, setIssueKeys] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [mode, setMode] = useState<"strict" | "balanced" | "exploratory">("balanced");
  const [retrieveEvidence, setRetrieveEvidence] = useState(true);

  const handleAddIssue = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !issueKeys.includes(trimmed)) {
      setIssueKeys([...issueKeys, trimmed]);
      setInputValue("");
    }
  };

  const handleRemoveIssue = (key: string) => {
    setIssueKeys(issueKeys.filter(k => k !== key));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddIssue();
    }
  };

  const handleStartAnalysis = () => {
    if (issueKeys.length > 0) {
      onStartAnalysis({
        issue_keys: issueKeys,
        mode,
        retrieve_evidence: retrieveEvidence,
      });
    }
  };

  return (
    <div className="glass rounded-2xl p-8 shadow-lg">
      <h2 className="text-2xl font-semibold text-slate-900 mb-6">Batch Configuration</h2>

      <div className="space-y-6">
        {/* Issue Keys Input */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Issue Keys
          </label>
          <div className="flex gap-3 mb-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., PROJ-123"
              className="flex-1 px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={isAnalyzing}
            />
            <button
              onClick={handleAddIssue}
              disabled={isAnalyzing || !inputValue.trim()}
              className="px-4 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Add
            </button>
          </div>

          {/* Issue Keys List */}
          {issueKeys.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {issueKeys.map((key) => (
                <div
                  key={key}
                  className="flex items-center gap-2 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg text-sm font-medium"
                >
                  <span className="font-mono">{key}</span>
                  <button
                    onClick={() => handleRemoveIssue(key)}
                    disabled={isAnalyzing}
                    className="hover:bg-purple-200 rounded p-0.5 transition-colors disabled:opacity-50"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <p className="text-sm text-slate-500 mt-2">
            {issueKeys.length} issue{issueKeys.length !== 1 ? "s" : ""} added
          </p>
        </div>

        {/* Analysis Mode */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Analysis Mode
          </label>
          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => setMode("strict")}
              disabled={isAnalyzing}
              className={`px-4 py-3 rounded-lg font-medium transition-all ${
                mode === "strict"
                  ? "bg-purple-600 text-white shadow-md"
                  : "bg-white text-slate-700 border border-slate-300 hover:border-purple-400"
              }`}
            >
              <div className="text-center">
                <div className="font-semibold">Strict</div>
                <div className="text-xs opacity-75">High precision</div>
              </div>
            </button>
            <button
              onClick={() => setMode("balanced")}
              disabled={isAnalyzing}
              className={`px-4 py-3 rounded-lg font-medium transition-all ${
                mode === "balanced"
                  ? "bg-purple-600 text-white shadow-md"
                  : "bg-white text-slate-700 border border-slate-300 hover:border-purple-400"
              }`}
            >
              <div className="text-center">
                <div className="font-semibold">Balanced</div>
                <div className="text-xs opacity-75">Recommended</div>
              </div>
            </button>
            <button
              onClick={() => setMode("exploratory")}
              disabled={isAnalyzing}
              className={`px-4 py-3 rounded-lg font-medium transition-all ${
                mode === "exploratory"
                  ? "bg-purple-600 text-white shadow-md"
                  : "bg-white text-slate-700 border border-slate-300 hover:border-purple-400"
              }`}
            >
              <div className="text-center">
                <div className="font-semibold">Exploratory</div>
                <div className="text-xs opacity-75">Broad search</div>
              </div>
            </button>
          </div>
        </div>

        {/* Options */}
        <div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={retrieveEvidence}
              onChange={(e) => setRetrieveEvidence(e.target.checked)}
              disabled={isAnalyzing}
              className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
            />
            <div>
              <div className="text-sm font-medium text-slate-700">Retrieve Evidence</div>
              <div className="text-xs text-slate-500">
                Search knowledge base for supporting evidence
              </div>
            </div>
          </label>
        </div>

        {/* Start Button */}
        <button
          onClick={handleStartAnalysis}
          disabled={isAnalyzing || issueKeys.length === 0}
          className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-lg"
        >
          <Search className="w-5 h-5" />
          {isAnalyzing ? "Analyzing..." : `Analyze ${issueKeys.length} Issue${issueKeys.length !== 1 ? "s" : ""}`}
        </button>
      </div>
    </div>
  );
}
