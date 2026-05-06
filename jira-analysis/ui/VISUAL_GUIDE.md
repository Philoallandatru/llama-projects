# Jira Analysis UI - Component Visual Guide

## Component Layouts

### 1. ProgressEvent Component

```
┌─────────────────────────────────────────────────────────┐
│  📥  load_issue    Loading issue NVME-777...            │
│  [Status: inprogress - Blue left border]                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ✓  analyze        Analysis complete                    │
│  [Status: done - Green left border, faded]              │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Emoji icon for visual identification
- Stage name in monospace font
- Status-based left border color
- Hover effect with shadow

---

### 2. BatchProgressEvent Component

```
┌─────────────────────────────────────────────────────────┐
│  Analyzing                              15 / 23 (65%)   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  [Progress bar with shimmer animation]                  │
│                                                           │
│  Processing issues...                                    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ✓  NVME-777  RCA                    [DONE]     │   │
│  │  ✓  NVME-778  Traceability           [DONE]     │   │
│  │  ⟳  NVME-779  RCA                    [PROGRESS] │   │
│  │  ⏳  NVME-780  Change Impact          [PENDING]  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Header with stage and progress stats
- Animated progress bar with gradient
- Scrollable item list (max 400px height)
- Status badges with color coding
- Hover effects on items

---

### 3. AnalysisResult Component

```
┌─────────────────────────────────────────────────────────┐
│  📋 Analysis: NVME-777                            [▼]   │
│  ─────────────────────────────────────────────────────  │
│                                                           │
│  Profile: RCA    Mode: strict    Evidence: 11 sources   │
│                                                           │
│  ## Root Cause Analysis                                  │
│                                                           │
│  The issue is caused by a timeout in the NVMe           │
│  controller under heavy load conditions...               │
│                                                           │
│  **Evidence**: Multiple similar issues found...          │
│                                                           │
│  ### Recommendations                                     │
│  1. Increase timeout threshold                          │
│  2. Implement retry logic                               │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Collapsible content (expand/collapse button)
- Metadata badges (profile, mode, evidence count)
- Markdown rendering with styling
- Clean typography hierarchy

---

### 4. EvidenceEvent Component

```
┌─────────────────────────────────────────────────────────┐
│  🔗 Evidence (5 sources)                                 │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  [JIRA]                                          │   │
│  │  NVME-555: Similar timeout issue                │   │
│  │  Controller timeout under load, resolved by...   │   │
│  │  Score: 87%              View Source →          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  [CONFLUENCE]                                    │   │
│  │  NVMe Controller Design Spec                    │   │
│  │  Timeout configuration and best practices...     │   │
│  │  Score: 82%              View Source →          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  [SPECS]                                         │   │
│  │  NVMe Protocol Specification v1.4               │   │
│  │  Section 3.2: Timeout handling requirements...   │   │
│  │  Score: 78%              View Source →          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Source type badges (color-coded)
- Relevance scores (percentage)
- Excerpt preview
- Links to original sources
- Hover effects with lift animation

---

## Color Coding

### Status Colors

- **Pending**: Gray (#94A3B8)
- **In Progress**: Blue (#0065FF)
- **Done**: Green (#10B981)
- **Error**: Red (#EF4444)

### Source Type Colors

- **JIRA**: Blue (#0065FF)
- **CONFLUENCE**: Purple (#6366F1)
- **SPECS**: Indigo (#4F46E5)

---

## Responsive Behavior

### Desktop (1024px+)
- Full width layouts
- Side-by-side metadata
- Horizontal item lists

### Tablet (768px - 1023px)
- Stacked layouts
- Wrapped metadata
- Vertical item lists

### Mobile (< 768px)
- Single column
- Stacked components
- Touch-friendly targets (44px min)

---

## Interaction States

### Hover States
- Cards: Lift effect (translateY(-2px)) + shadow
- Buttons: Background color change
- Links: Color change + underline

### Focus States
- 2px blue outline (#0065FF)
- 2px offset for clarity
- Visible on all interactive elements

### Active States
- Slight scale down (0.98)
- Darker background
- Immediate visual feedback

---

## Animation Timings

- **Fast** (150ms): Hover states, button clicks
- **Base** (200ms): Card transitions, color changes
- **Slow** (300ms): Progress bar, complex animations

All animations respect `prefers-reduced-motion` setting.

---

## Typography Scale

```
Heading 1: 1.5rem (24px) - Bold
Heading 2: 1.25rem (20px) - Bold
Heading 3: 1.125rem (18px) - Semibold
Body: 1rem (16px) - Regular
Small: 0.875rem (14px) - Regular
Tiny: 0.75rem (12px) - Semibold (badges)
```

---

## Spacing Examples

```
Card padding: 2rem (32px)
Section gap: 1.5rem (24px)
Item gap: 1rem (16px)
Inline gap: 0.5rem (8px)
Badge padding: 0.25rem 0.5rem (4px 8px)
```

---

## Shadow Hierarchy

```
Level 1 (sm): Subtle elevation (buttons, inputs)
Level 2 (md): Medium elevation (cards on hover)
Level 3 (lg): High elevation (modals, dropdowns)
```

---

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Enter/Space to activate buttons
- Escape to close modals
- Arrow keys for lists

### Screen Reader Support
- Semantic HTML (header, main, section, article)
- ARIA labels on icon-only buttons
- Status announcements for progress
- Descriptive link text

### Visual Accessibility
- Minimum 16px font size
- 4.5:1 contrast ratio for text
- 3:1 contrast ratio for UI elements
- No color-only indicators

---

## Component States

### Loading
- Shimmer animation on progress bars
- Spinner icons where appropriate
- Skeleton screens for content

### Empty
- Friendly empty state messages
- Suggestions for next actions
- Clear visual indicators

### Error
- Red color coding
- Clear error messages
- Retry options where applicable
- No technical jargon

---

## Best Practices

1. **Always provide feedback**: Every action should have visual feedback
2. **Be consistent**: Use the same patterns throughout
3. **Be accessible**: Test with keyboard and screen readers
4. **Be responsive**: Test on multiple screen sizes
5. **Be performant**: Keep animations smooth at 60fps
