# Jira Analysis UI

TypeScript UI for the Jira Analysis System.

## Setup

```bash
cd ui
npm install
```

## Development

```bash
npm run dev
```

The UI will be available at `http://localhost:4501/deployments/jira-analysis/ui`

## Features

- **Single Issue Analysis**: Analyze individual Jira issues with real-time progress updates
- **Batch Analysis**: Analyze multiple issues in parallel with progress tracking
- **Custom Components**: 
  - `ProgressEvent`: Shows analysis progress for single issues
  - `BatchProgressEvent`: Shows batch analysis progress with progress bar
- **Custom Header**: Branded header with Jira-style logo

## Configuration

The UI is configured in `index.ts`:

```typescript
{
  starterQuestions: [
    "分析 issue NVME-777",
    "批量分析 NVME-777, NVME-778, NVME-779",
    "使用严格模式分析 PROJ-123",
  ],
  llamaDeploy: {
    deployment: "jira-analysis",
    workflow: "deep-analysis"
  }
}
```

## Components

- `layout/header.tsx`: Custom header component
- `components/ProgressEvent.tsx`: Single issue progress display
- `components/BatchProgressEvent.tsx`: Batch analysis progress display
- `components/styles.css`: Component styles
