import { EventComponent } from "@llamaindex/server/ui";

interface ProgressEventData {
  stage: string;
  message: string;
  status?: 'pending' | 'inprogress' | 'done' | 'error';
}

export default function ProgressEvent({ data }: EventComponent<ProgressEventData>) {
  const stageEmoji: Record<string, string> = {
    load_issue: "📥",
    route: "🔀",
    retrieve: "🔍",
    analyze: "🤖",
    format: "📝",
  };

  const emoji = stageEmoji[data.stage] || "⚙️";
  const status = data.status || 'inprogress';

  return (
    <div className={`progress-event status-${status}`}>
      <span className="stage-emoji">{emoji}</span>
      <span className="stage-name">{data.stage.replace(/_/g, ' ')}</span>
      <span className="message">{data.message}</span>
    </div>
  );
}
