import { EventComponent } from "@llamaindex/server/ui";

interface BatchItem {
  key: string;
  status: 'pending' | 'inprogress' | 'done' | 'error';
  profile?: string;
}

interface BatchProgressEventData {
  stage: string;
  message: string;
  current: number;
  total: number;
  items?: BatchItem[];
}

export default function BatchProgressEvent({ data }: EventComponent<BatchProgressEventData>) {
  const percentage = data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;

  const stageLabels: Record<string, string> = {
    load: "Loading Issues",
    analyze: "Analyzing",
    report: "Generating Report",
  };

  const statusIcons: Record<string, string> = {
    pending: "⏳",
    inprogress: "⟳",
    done: "✓",
    error: "✗",
  };

  return (
    <div className="batch-progress-event">
      <div className="progress-header">
        <span className="stage-label">{stageLabels[data.stage] || data.stage}</span>
        <span className="progress-text">
          {data.current} / {data.total} ({percentage}%)
        </span>
      </div>

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div className="progress-message">{data.message}</div>

      {data.items && data.items.length > 0 && (
        <div className="batch-items-list">
          {data.items.map((item, index) => (
            <div key={index} className="batch-item">
              <span className="batch-item-icon">{statusIcons[item.status]}</span>
              <span className="batch-item-key">{item.key}</span>
              {item.profile && (
                <span className="batch-item-profile">{item.profile}</span>
              )}
              <span className={`batch-item-status ${item.status}`}>
                {item.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
