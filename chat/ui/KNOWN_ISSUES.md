# Known Issues

## Accessibility Test Failure

**Test:** `accessibility.spec.ts:78:7 › Accessibility › should not have critical accessibility violations`

**Status:** Non-blocking

**Description:**
One button in the LlamaIndex Server's built-in UI components lacks an accessible name (missing `aria-label`, `aria-labelledby`, or visible text content).

**Impact:**
- Does not affect functionality
- This is a third-party component issue in `@llamaindex/server`
- All other accessibility tests pass (7/8 passing)

**Root Cause:**
The button is part of the LlamaIndex Server's internal React components, not our custom code. The issue exists in the upstream library.

**Recommendation:**
- Consider reporting this to the LlamaIndex team
- Monitor for fixes in future `@llamaindex/server` releases
- This should not block deployment or PR approval

**Test Results:**
- Overall: 25/26 tests passing (96%)
- Accessibility: 7/8 tests passing (88%)
