import { EventComponent } from "@llamaindex/server/ui";

interface BatchProgressEventData {
  stage: string;
  message: string;
  current: number;
  total: number;
}

export default function BatchProgressEvent({ data }: EventComponent<BatchProgressEventData>) {
  const percentage = data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;

  const stageLabels: Record<string, string> = {
    load: "Loading Issues",
    analyze: "Analyzing",
    report: "Generating Report",
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
    </div>
  );
}
