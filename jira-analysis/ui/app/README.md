# Jira Analysis Frontend

Modern Next.js frontend for the Jira Analysis System with AI-powered insights.

## Features

- **Deep Analysis**: Real-time analysis of individual Jira issues with streaming progress
- **Batch Reports**: Generate comprehensive reports from multiple issues (Coming Soon)
- **Knowledge Base**: Capture and organize insights from analyses (Coming Soon)

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **UI Components**: Custom components with Lucide icons
- **Markdown**: react-markdown with syntax highlighting

## Getting Started

### Prerequisites

- Node.js 20+
- Backend API running on `http://localhost:4501`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
app/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Deep Analysis page (home)
│   ├── reports/           # Batch Reports page
│   ├── knowledge/         # Knowledge Base page
│   ├── layout.tsx         # Root layout with header
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── Header.tsx         # Navigation header
│   ├── AnalysisProgress.tsx  # Progress tracker
│   └── AnalysisResults.tsx   # Results display
└── public/                # Static assets
```

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:4501`:

- `POST /api/analyze` - Single issue analysis (SSE streaming)
- `POST /api/batch-analyze` - Batch analysis (Coming Soon)

## Design System

### Colors

- **Primary**: Blue gradient (#0052CC → #0065FF) - Jira brand colors
- **Secondary**: Purple/Indigo (#6366F1 → #8B5CF6)
- **Background**: Gradient from slate to blue to indigo

### Typography

- **Font**: Inter (Google Fonts)
- **Headings**: Bold, slate-900
- **Body**: Regular, slate-700

### Components

- **Glass Effect**: Backdrop blur with transparency
- **Cards**: Rounded corners with subtle shadows
- **Buttons**: Gradient backgrounds with hover effects
- **Icons**: Lucide React icons

## Development Notes

### Current Status

- ✅ Deep Analysis page fully implemented
- ✅ Real-time progress tracking with SSE
- ✅ Markdown rendering with syntax highlighting
- ⏳ Batch Reports page (placeholder)
- ⏳ Knowledge Base page (placeholder)

### Known Issues

- API endpoint needs to be updated to match actual backend routes
- Evidence display structure needs to match backend response format
- Need to add error handling for failed API calls

### Next Steps

1. Test with actual backend API
2. Implement batch analysis workflow
3. Add knowledge base functionality
4. Add export features (PDF, Markdown)
5. Implement JQL query support

## Contributing

When adding new features:

1. Follow the existing component structure
2. Use TypeScript for type safety
3. Follow Tailwind CSS conventions
4. Add proper error handling
5. Test with the backend API

## License

Part of the llama-projects monorepo.
