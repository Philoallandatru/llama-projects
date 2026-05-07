# Batch Analysis Feature - Testing Guide

## Overview
The batch analysis feature allows you to analyze multiple Jira issues simultaneously and generate comprehensive reports.

## Components Implemented

### 1. BatchConfigPanel (`components/BatchConfigPanel.tsx`)
- **Issue Keys Input**: Add multiple issue keys with tag-based UI
- **Analysis Mode Selection**: Choose between Strict, Balanced, or Exploratory modes
- **Evidence Retrieval Toggle**: Enable/disable knowledge base search
- **Validation**: Prevents duplicate keys and empty submissions

### 2. BatchProgress (`components/BatchProgress.tsx`)
- **Progress Bar**: Visual progress indicator with percentage
- **Statistics Cards**: Real-time counts for completed, in-progress, and errors
- **Issue List**: Detailed status for each issue with profile badges
- **Time Estimation**: Shows estimated time remaining (when available)

### 3. BatchReport (`components/BatchReport.tsx`)
- **Summary Statistics**: Total issues, completion rate, profile distribution
- **Expandable Reports**: Individual issue reports with markdown rendering
- **Error Handling**: Clear display of failed analyses
- **Expand/Collapse All**: Quick navigation controls

### 4. ExportOptions (`components/ExportOptions.tsx`)
- **Markdown Export**: Download complete report as .md file
- **JSON Export**: Download raw data as .json file
- **Knowledge Base Save**: (Coming soon) Save to knowledge base
- **Email Report**: (Coming soon) Email functionality

## How to Test

### Prerequisites
1. Backend API server running on `http://localhost:4501`
2. Frontend dev server running on `http://localhost:3001`

### Test Steps

1. **Navigate to Reports Page**
   - Open browser: `http://localhost:3001/reports`
   - You should see the batch configuration panel

2. **Add Issue Keys**
   - Type an issue key (e.g., `KAN-9`) in the input field
   - Press Enter or click "Add" button
   - Repeat to add multiple issues
   - Remove issues by clicking the X button on tags

3. **Configure Analysis**
   - Select analysis mode (Strict/Balanced/Exploratory)
   - Toggle "Retrieve Evidence" checkbox
   - Click "Analyze N Issues" button

4. **Monitor Progress**
   - Watch real-time progress bar
   - See statistics update (Completed, In Progress, Errors)
   - View individual issue status in the list

5. **View Results**
   - Export options appear when analysis completes
   - Summary statistics show overall results
   - Expand individual reports to see full analysis
   - Use "Expand All" / "Collapse All" for quick navigation

6. **Export Reports**
   - Click "Markdown" to download .md file
   - Click "JSON" to download raw data
   - Knowledge Base and Email features coming soon

## API Integration

### Endpoint
```
POST http://localhost:4501/api/batch-analyze
```

### Request Body
```json
{
  "issue_keys": ["KAN-9", "KAN-10"],
  "mode": "balanced",
  "retrieve_evidence": true
}
```

### Response (SSE Stream)
```
data: {"type": "BatchProgressEvent", "data": {...}}
data: {"type": "result", "data": {...}}
```

## UI Features

### Responsive Design
- Mobile: Single column layout
- Tablet: 2-column grid for statistics
- Desktop: Full 3-4 column layout

### Accessibility
- Keyboard navigation support
- ARIA labels for screen readers
- High contrast colors (WCAG 2.1 AA)
- Focus indicators on interactive elements

### Visual Design
- Glass morphism effects
- Gradient backgrounds (purple/indigo theme)
- Smooth transitions and animations
- Loading states with spinners
- Status-based color coding (green/blue/red)

## Known Limitations

1. **Backend Dependency**: Requires API server to be running
2. **CORS**: May need CORS configuration for production
3. **Error Recovery**: No retry mechanism for failed issues
4. **Batch Size**: No hard limit enforced (consider adding max)
5. **Export Features**: Knowledge Base and Email not yet implemented

## Next Steps

1. Test with real Jira issues
2. Verify SSE streaming works correctly
3. Test error handling with invalid issue keys
4. Implement Knowledge Base integration
5. Add email functionality
6. Add batch size limits and warnings
7. Implement retry mechanism for failed issues

## File Structure

```
ui/app/
├── app/
│   └── reports/
│       └── page.tsx          # Main reports page
└── components/
    ├── BatchConfigPanel.tsx  # Configuration UI
    ├── BatchProgress.tsx     # Progress tracking
    ├── BatchReport.tsx       # Results display
    └── ExportOptions.tsx     # Export functionality
```

## Development Notes

- All components use TypeScript for type safety
- Tailwind CSS for styling (v4)
- React hooks for state management
- SSE (Server-Sent Events) for real-time updates
- react-markdown for rendering analysis results
- lucide-react for icons
