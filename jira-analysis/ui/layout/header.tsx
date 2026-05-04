import { Header } from "@llamaindex/server/ui";

export default function CustomHeader() {
  return (
    <Header
      title="Jira Analysis System"
      description="AI-powered deep analysis for Jira issues with evidence retrieval and knowledge extraction"
      logo={
        <svg
          width="32"
          height="32"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="jiraGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0052CC" />
              <stop offset="100%" stopColor="#0065FF" />
            </linearGradient>
          </defs>
          <rect width="32" height="32" rx="8" fill="url(#jiraGradient)" />
          <path
            d="M16 8L8 16L16 24L24 16L16 8Z"
            fill="white"
            opacity="0.9"
          />
          <circle cx="16" cy="16" r="3" fill="white" />
        </svg>
      }
    />
  );
}
