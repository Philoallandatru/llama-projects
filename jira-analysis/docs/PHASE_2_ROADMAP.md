# Jira Analysis System - Phase 2 Roadmap

## Overview

Phase 2 will transform the single-page LlamaIndex UI into a comprehensive multi-page Next.js application with advanced features for report generation, knowledge base management, and data visualization.

**Status**: 📋 Planning Phase  
**Target Start**: After Phase 1 deployment and user feedback  
**Estimated Duration**: 4-6 weeks  

---

## Phase 2 Goals

### Primary Objectives

1. **Multi-page Navigation**: Separate pages for Deep Analysis, Reports, and Knowledge Base
2. **Advanced Reporting**: Batch analysis with filtering, grouping, and export
3. **Knowledge Management**: Browse, search, and manage extracted knowledge
4. **Data Visualization**: Charts and graphs for insights and trends
5. **Enhanced UX**: Better workflows, state management, and user preferences

### Success Metrics

- User can generate daily/weekly reports with custom filters
- Knowledge base is searchable and browsable
- Charts provide actionable insights
- Page load time < 2 seconds
- Lighthouse score > 90

---

## Architecture Changes

### Current (Phase 1)

```
LlamaIndex Server UI (Single Page)
├── Chat Interface
├── Event Components
└── Real-time Streaming
```

### Proposed (Phase 2)

```
Next.js Application (Multi-page)
├── App Router
├── Server Components
├── Client Components
├── API Routes
└── State Management (React Context)
```

---

## Feature Breakdown

### 1. Deep Analysis Page

**Purpose**: Enhanced single-issue analysis with better UX

**Features**:
- Issue key input with autocomplete
- Analysis mode selector (strict/balanced/exploratory)
- Profile override option
- History of recent analyses
- Save/bookmark functionality
- Share analysis link

**Components**:
- `IssueSearchInput` - Autocomplete input
- `AnalysisModeSelector` - Mode dropdown
- `AnalysisHistory` - Recent analyses list
- `AnalysisDisplay` - Enhanced result display
- `ShareButton` - Share functionality

**Estimated Time**: 1 week

---

### 2. Report Generation Page

**Purpose**: Batch analysis with filtering and reporting

**Features**:
- Date range picker (today, this week, last week, custom)
- Project filter (multi-select)
- Issue type filter (Bug, Task, Story, etc.)
- Status filter (Open, In Progress, Done, etc.)
- Assignee filter (multi-select)
- JQL editor for advanced users
- Preview issue count before analysis
- Batch progress tracking
- Report summary with charts
- Export to PDF/Markdown
- Save report to knowledge base

**Components**:
- `DateRangePicker` - Date selection
- `FilterPanel` - All filters
- `JQLEditor` - Advanced query editor
- `IssuePreview` - Preview list
- `BatchProgress` - Enhanced progress tracker
- `ReportSummary` - Summary with charts
- `ExportButton` - Export functionality

**Charts** (using recharts):
- Issue distribution by type (pie chart)
- Status over time (line chart)
- Profile breakdown (bar chart)
- Evidence sources (stacked bar)

**Estimated Time**: 2 weeks

---

### 3. Knowledge Base Page

**Purpose**: Browse and manage extracted knowledge

**Features**:
- Search functionality (full-text)
- Category filter (RCA, Traceability, Best Practices, etc.)
- Tag filter (multi-select)
- Date filter (recent, this week, this month)
- Sort options (relevance, date, popularity)
- Grid/List view toggle
- Knowledge entry detail view
- Edit/Delete functionality
- Create new entry
- Link to related issues
- Export entry

**Components**:
- `SearchBar` - Full-text search
- `FilterSidebar` - Category, tags, date filters
- `KnowledgeGrid` - Grid view
- `KnowledgeList` - List view
- `KnowledgeDetail` - Entry detail page
- `KnowledgeEditor` - Create/edit form
- `RelatedIssues` - Related issues list

**Estimated Time**: 1.5 weeks

---

### 4. Navigation & Layout

**Purpose**: Consistent navigation and layout

**Features**:
- Top navigation bar with tabs
- Breadcrumbs for deep pages
- User menu (settings, logout)
- Theme toggle (light/dark)
- Responsive sidebar for mobile
- Footer with links

**Components**:
- `Navigation` - Top nav bar
- `Breadcrumbs` - Breadcrumb trail
- `UserMenu` - User dropdown
- `ThemeToggle` - Theme switcher
- `MobileSidebar` - Mobile nav
- `Footer` - Footer component

**Estimated Time**: 3 days

---

### 5. API Integration

**Purpose**: Connect to backend workflows

**Features**:
- API client with error handling
- Request/response types
- Loading states
- Error boundaries
- Retry logic
- Caching strategy

**Implementation**:
- Next.js API routes as proxy
- React Query for data fetching
- Optimistic updates
- Error handling with toast notifications

**Estimated Time**: 1 week

---

## Technology Stack

### Frontend

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **UI Library**: shadcn/ui (Radix UI + Tailwind)
- **Charts**: recharts
- **Forms**: React Hook Form + Zod
- **State**: React Context + React Query
- **Styling**: Tailwind CSS

### Development Tools

- **Package Manager**: pnpm (faster than npm)
- **Linting**: ESLint + Prettier
- **Testing**: Vitest + React Testing Library
- **E2E Testing**: Playwright
- **Type Checking**: TypeScript strict mode

---

## Design System

### Component Library: shadcn/ui

**Why shadcn/ui?**
- Copy-paste components (no npm dependency)
- Built on Radix UI (accessible)
- Tailwind CSS styling
- Customizable and themeable
- TypeScript support

**Core Components to Use**:
- Button, Input, Select, Checkbox, Radio
- Card, Dialog, Dropdown, Popover
- Table, Tabs, Toast, Tooltip
- Form, Label, Textarea
- Calendar, DatePicker

### Color Palette (Consistent with Phase 1)

```css
Primary:    #0065FF (Jira blue)
Secondary:  #6366F1 (Indigo)
Success:    #10B981 (Green)
Warning:    #F59E0B (Amber)
Error:      #EF4444 (Red)
Neutral:    Slate scale
```

### Typography

```css
Font Family: Inter (system fallback)
Headings:    2xl, xl, lg (bold)
Body:        base (regular)
Small:       sm (regular)
Code:        JetBrains Mono
```

---

## Implementation Plan

### Week 1: Setup & Foundation

**Tasks**:
- [ ] Initialize Next.js project
- [ ] Setup Tailwind CSS + shadcn/ui
- [ ] Configure TypeScript strict mode
- [ ] Setup ESLint + Prettier
- [ ] Create base layout components
- [ ] Implement navigation structure
- [ ] Setup React Query
- [ ] Create API client

**Deliverables**:
- Working Next.js app with navigation
- Base layout and routing
- API integration foundation

---

### Week 2: Deep Analysis Page

**Tasks**:
- [ ] Build issue search input with autocomplete
- [ ] Implement analysis mode selector
- [ ] Create analysis history component
- [ ] Enhance analysis display
- [ ] Add share functionality
- [ ] Implement save/bookmark
- [ ] Add loading states
- [ ] Error handling

**Deliverables**:
- Fully functional Deep Analysis page
- Better UX than Phase 1
- History and sharing features

---

### Week 3-4: Report Generation Page

**Tasks**:
- [ ] Build date range picker
- [ ] Implement filter panel (project, type, status, assignee)
- [ ] Create JQL editor
- [ ] Build issue preview
- [ ] Enhance batch progress tracker
- [ ] Create report summary with charts
- [ ] Implement export functionality
- [ ] Add save to knowledge base

**Deliverables**:
- Complete report generation workflow
- Interactive charts with recharts
- Export to PDF/Markdown
- Save reports to knowledge base

---

### Week 5: Knowledge Base Page

**Tasks**:
- [ ] Build search functionality
- [ ] Implement filter sidebar
- [ ] Create grid/list views
- [ ] Build knowledge detail page
- [ ] Implement create/edit form
- [ ] Add related issues linking
- [ ] Implement delete functionality
- [ ] Add export feature

**Deliverables**:
- Searchable knowledge base
- CRUD operations for entries
- Related issues linking

---

### Week 6: Polish & Testing

**Tasks**:
- [ ] Write unit tests for components
- [ ] Write integration tests
- [ ] E2E tests with Playwright
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Browser compatibility testing
- [ ] Documentation updates
- [ ] Deployment preparation

**Deliverables**:
- Test coverage > 80%
- Performance optimized
- Accessibility verified
- Production-ready

---

## State Management Strategy

### Global State (React Context)

```typescript
// User preferences
- theme (light/dark)
- language (en/zh)
- recent analyses
- bookmarks

// App state
- current user
- notifications
- loading states
```

### Server State (React Query)

```typescript
// Data fetching
- issues
- analyses
- reports
- knowledge entries

// Mutations
- create analysis
- generate report
- save knowledge
```

### Local State (useState)

```typescript
// Component-specific
- form inputs
- UI toggles
- temporary data
```

---

## API Design

### Endpoints

```typescript
// Deep Analysis
POST /api/analysis/single
  Body: { issue_key, mode, profile? }
  Response: { task_id, status }

GET /api/analysis/:task_id
  Response: { status, result, progress }

// Batch Analysis
POST /api/analysis/batch
  Body: { issue_keys[], mode, max_concurrent }
  Response: { task_id, status }

GET /api/analysis/batch/:task_id
  Response: { status, results[], progress }

// Reports
POST /api/reports/generate
  Body: { filters, date_range }
  Response: { report_id, status }

GET /api/reports/:report_id
  Response: { report, charts_data }

// Knowledge Base
GET /api/knowledge
  Query: { search, category, tags, page }
  Response: { entries[], total, page }

POST /api/knowledge
  Body: { title, content, category, tags }
  Response: { entry_id }

PUT /api/knowledge/:id
  Body: { title, content, category, tags }
  Response: { success }

DELETE /api/knowledge/:id
  Response: { success }
```

---

## Testing Strategy

### Unit Tests (Vitest)

- Component rendering
- Event handling
- State management
- Utility functions

**Target**: 80% coverage

### Integration Tests

- API integration
- Form submissions
- Navigation flows
- Error handling

**Target**: Key user flows covered

### E2E Tests (Playwright)

- Complete user workflows
- Cross-browser testing
- Mobile responsiveness
- Accessibility

**Target**: Critical paths covered

---

## Performance Targets

### Metrics

- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: > 90
- **Bundle Size**: < 500KB (gzipped)

### Optimization Strategies

- Code splitting by route
- Image optimization (Next.js Image)
- Font optimization (next/font)
- API response caching
- Lazy loading components
- Debounced search inputs

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

- [ ] Color contrast ≥ 4.5:1
- [ ] Keyboard navigation
- [ ] Focus management
- [ ] Screen reader support
- [ ] ARIA labels
- [ ] Form validation
- [ ] Error messages
- [ ] Skip links

### Testing Tools

- axe DevTools
- WAVE
- Lighthouse
- Screen reader testing (NVDA/JAWS)

---

## Deployment Strategy

### Hosting Options

1. **Vercel** (Recommended)
   - Native Next.js support
   - Automatic deployments
   - Edge functions
   - Analytics

2. **Netlify**
   - Good Next.js support
   - Form handling
   - Split testing

3. **Self-hosted**
   - Docker container
   - Node.js server
   - Nginx reverse proxy

### CI/CD Pipeline

```yaml
# GitHub Actions workflow
- Lint & Type Check
- Run Tests
- Build Application
- Deploy to Staging
- Run E2E Tests
- Deploy to Production
```

---

## Migration Strategy

### Phase 1 → Phase 2 Transition

**Option A: Gradual Migration**
- Keep Phase 1 running
- Deploy Phase 2 to new URL
- Migrate users gradually
- Sunset Phase 1 after validation

**Option B: Direct Replacement**
- Deploy Phase 2 to same URL
- Redirect old routes
- Provide migration guide
- Monitor for issues

**Recommendation**: Option A (safer)

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Next.js learning curve | Medium | Training, documentation |
| API integration issues | High | Thorough testing, error handling |
| Performance degradation | Medium | Performance monitoring, optimization |
| Browser compatibility | Low | Testing, polyfills |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Strict scope management |
| Dependency delays | Medium | Buffer time in schedule |
| Testing delays | Medium | Parallel testing |

---

## Success Criteria

### Functional

- [ ] All three pages functional
- [ ] Navigation works smoothly
- [ ] API integration complete
- [ ] Charts display correctly
- [ ] Export functionality works
- [ ] Search is fast and accurate

### Non-Functional

- [ ] Performance targets met
- [ ] Accessibility compliant
- [ ] Test coverage > 80%
- [ ] Documentation complete
- [ ] Browser compatibility verified

### Business

- [ ] User feedback positive
- [ ] Adoption rate > 80%
- [ ] Bug rate < 5%
- [ ] Support tickets minimal

---

## Budget Estimate

### Development Time

- Setup & Foundation: 40 hours
- Deep Analysis Page: 40 hours
- Report Generation: 80 hours
- Knowledge Base: 60 hours
- Polish & Testing: 40 hours
- **Total**: 260 hours (~6.5 weeks)

### Additional Costs

- Design mockups: 20 hours
- Code review: 20 hours
- Documentation: 20 hours
- **Total**: 60 hours

**Grand Total**: 320 hours (~8 weeks with buffer)

---

## Next Steps

### Immediate Actions

1. **Gather User Feedback** on Phase 1
2. **Prioritize Features** based on feedback
3. **Create Design Mockups** for Phase 2
4. **Review and Approve** this roadmap
5. **Allocate Resources** for development

### Before Starting Phase 2

- [ ] Phase 1 deployed to production
- [ ] User feedback collected
- [ ] Design mockups approved
- [ ] Development team assigned
- [ ] Timeline confirmed

---

## Appendix

### Related Documents

- `docs/PHASE_1_COMPLETION.md` - Phase 1 summary
- `.planning/jira-analysis-design.md` - Original design
- `ui/README.md` - Current UI documentation

### References

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com)
- [recharts Documentation](https://recharts.org)
- [React Query Guide](https://tanstack.com/query)

### Contact

For questions about Phase 2 planning:
- Review this roadmap
- Check Phase 1 completion report
- Refer to original design document
