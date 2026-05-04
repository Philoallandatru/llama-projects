# Jira Analysis UI

TypeScript UI for the Jira Analysis System with modern design and real-time progress tracking.

## Design System

**Style**: Modern Minimalism with Glassmorphism accents  
**Colors**: Jira brand colors (Blue gradient #0052CC → #0065FF)  
**Typography**: System fonts (Inter/SF Pro) + JetBrains Mono for code  
**Framework**: LlamaIndex Server UI + React + TypeScript

## Features

### Core Components

1. **ProgressEvent** - Single issue analysis progress
   - Real-time stage tracking (load → route → retrieve → analyze)
   - Status indicators (pending, in progress, done, error)
   - Emoji icons for visual clarity

2. **BatchProgressEvent** - Batch analysis progress
   - Progress bar with shimmer animation
   - Item-by-item status tracking
   - Percentage completion display

3. **AnalysisResult** - Analysis result display
   - Collapsible sections
   - Markdown rendering
   - Metadata display (profile, mode, evidence count)

4. **EvidenceEvent** - Evidence source display
   - Source type badges
   - Relevance scores
   - Direct links to sources

### Design Features

- **Responsive Design**: Mobile-first, works on all screen sizes
- **Accessibility**: WCAG 2.1 AA compliant
  - Keyboard navigation support
  - Focus states on all interactive elements
  - Color contrast ratio ≥ 4.5:1
  - Reduced motion support
- **Performance**: Smooth animations (150-300ms transitions)
- **Visual Hierarchy**: Clear card-based layouts with shadows

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

## File Structure

```
ui/
├── index.ts                    # LlamaIndexServer config
├── components/
│   ├── ProgressEvent.tsx       # Single issue progress
│   ├── BatchProgressEvent.tsx  # Batch progress tracker
│   ├── AnalysisResult.tsx      # Analysis result display
│   ├── EvidenceEvent.tsx       # Evidence display
│   └── styles.css              # Component styles
├── layout/
│   └── header.tsx              # Custom header
├── package.json
└── tsconfig.json
```

## Event Types

### ProgressEvent
```typescript
{
  type: 'progress_event',
  data: {
    stage: 'load_issue' | 'route' | 'retrieve' | 'analyze',
    message: string,
    status?: 'pending' | 'inprogress' | 'done' | 'error'
  }
}
```

### BatchProgressEvent
```typescript
{
  type: 'batch_progress',
  data: {
    stage: string,
    message: string,
    current: number,
    total: number,
    items?: Array<{
      key: string,
      status: 'pending' | 'inprogress' | 'done' | 'error',
      profile?: string
    }>
  }
}
```

### AnalysisResult
```typescript
{
  type: 'analysis_result',
  data: {
    issue_key: string,
    profile: string,
    mode: string,
    analysis: string,  // Markdown
    evidence_count?: {
      similar_issues: number,
      confluence: number,
      specs: number
    }
  }
}
```

### EvidenceEvent
```typescript
{
  type: 'evidence_event',
  data: {
    issue_key: string,
    evidence: Array<{
      source_type: string,
      title: string,
      excerpt: string,
      score: number,
      url?: string
    }>
  }
}
```

## Styling Guidelines

### Colors
- Primary: `#0065FF` (Jira blue)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)
- Neutral: Slate scale

### Spacing
- xs: 0.25rem
- sm: 0.5rem
- md: 1rem
- lg: 1.5rem
- xl: 2rem

### Transitions
- Fast: 150ms (hover states)
- Base: 200ms (standard transitions)
- Slow: 300ms (complex animations)

## Accessibility Checklist

- [x] Color contrast ≥ 4.5:1
- [x] Focus states on interactive elements
- [x] Keyboard navigation support
- [x] Reduced motion support
- [x] Semantic HTML
- [x] ARIA labels where needed

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Smooth 60fps animations
- Lazy loading for large result sets
- Optimized re-renders with React
- CSS transitions over JavaScript animations
