import { EventComponent } from "@llamaindex/server/ui";
import { useState } from "react";

interface AnalysisResultData {
  issue_key: string;
  profile: string;
  mode: string;
  analysis: string;
  evidence_count?: {
    similar_issues: number;
    confluence: number;
    specs: number;
  };
}

export default function AnalysisResult({ data }: EventComponent<AnalysisResultData>) {
  const [isExpanded, setIsExpanded] = useState(true);

  const totalEvidence = data.evidence_count
    ? data.evidence_count.similar_issues +
      data.evidence_count.confluence +
      data.evidence_count.specs
    : 0;

  return (
    <div className="analysis-result-card">
      <div className="result-card-header">
        <div className="result-card-title">
          <span className="result-card-icon">📋</span>
          <span>Analysis: {data.issue_key}</span>
        </div>
        <button
          className="expand-button"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-label={isExpanded ? "Collapse" : "Expand"}
        >
          {isExpanded ? "▼" : "▶"}
        </button>
      </div>

      {isExpanded && (
        <>
          <div className="result-metadata">
            <div className="metadata-item">
              <span className="metadata-label">Profile:</span>
              <span className="metadata-value">{data.profile}</span>
            </div>
            <div className="metadata-item">
              <span className="metadata-label">Mode:</span>
              <span className="metadata-value">{data.mode}</span>
            </div>
            {data.evidence_count && (
              <div className="metadata-item">
                <span className="metadata-label">Evidence:</span>
                <span className="metadata-value">{totalEvidence} sources</span>
              </div>
            )}
          </div>

          <div className="result-card-content">
            <div
              className="markdown-content"
              dangerouslySetInnerHTML={{ __html: formatMarkdown(data.analysis) }}
            />
          </div>
        </>
      )}
    </div>
  );
}

// Simple markdown formatter (basic support)
function formatMarkdown(text: string): string {
  return text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>');
}
