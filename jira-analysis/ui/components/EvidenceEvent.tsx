import { EventComponent } from "@llamaindex/server/ui";

interface EvidenceItem {
  source_type: string;
  title: string;
  excerpt: string;
  score: number;
  url?: string;
}

interface EvidenceEventData {
  issue_key: string;
  evidence: EvidenceItem[];
}

export default function EvidenceEvent({ data }: EventComponent<EvidenceEventData>) {
  if (!data.evidence || data.evidence.length === 0) {
    return null;
  }

  return (
    <div className="evidence-container">
      <h3 className="evidence-header">
        🔗 Evidence ({data.evidence.length} sources)
      </h3>
      <div className="evidence-list">
        {data.evidence.map((item, index) => (
          <div key={index} className="evidence-card">
            <span className="evidence-source-type">{item.source_type}</span>
            <h4 className="evidence-title">{item.title}</h4>
            <p className="evidence-excerpt">{item.excerpt}</p>
            <div className="evidence-metadata">
              <span className="evidence-score">
                Score: {(item.score * 100).toFixed(0)}%
              </span>
              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="evidence-link"
                >
                  View Source →
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
