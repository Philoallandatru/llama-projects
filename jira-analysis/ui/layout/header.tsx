import { Header } from "@llamaindex/server/ui";

export default function CustomHeader() {
  return (
    <Header
      title="Jira Issue Deep Analysis"
      description="AI-powered deep analysis for Jira issues using LlamaIndex Workflows"
      logo={
        <svg
          width="32"
          height="32"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect width="32" height="32" rx="6" fill="#0052CC" />
          <path
            d="M16 8L8 16L16 24L24 16L16 8Z"
            fill="white"
          />
        </svg>
      }
    />
  );
}
