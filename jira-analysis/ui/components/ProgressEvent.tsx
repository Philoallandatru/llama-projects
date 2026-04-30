import { EventComponent } from "@llamaindex/server/ui";

interface ProgressEventData {
  stage: string;
  message: string;
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

  return (
    <div className="progress-event">
      <span className="stage-emoji">{emoji}</span>
      <span className="stage-name">{data.stage}</span>
      <span className="message">{data.message}</span>
    </div>
  );
}
