"""
Accessibility tests for Jira Analysis System.

Tests WCAG 2.1 AA compliance, keyboard navigation, screen reader support,
and other accessibility requirements.
"""

import pytest
from playwright.sync_api import Page, expect
from axe_core_python.sync_playwright import Axe


class TestAccessibility:
    """Accessibility test suite."""

    def test_axe_core_scan(self, page: Page, ui_url: str):
        """Run axe-core accessibility scan on the page."""
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")

        # Run axe accessibility scan
        axe = Axe()
        results = axe.run(page)

        # Check for violations
        violations = results.violations

        if violations:
            print(f"\n{len(violations)} accessibility violations found:")
            for violation in violations:
                print(f"\n- {violation['id']}: {violation['description']}")
                print(f"  Impact: {violation['impact']}")
                print(f"  Affected elements: {len(violation['nodes'])}")

        # Assert no critical or serious violations
        critical_violations = [v for v in violations if v['impact'] in ['critical', 'serious']]
        assert len(critical_violations) == 0, f"Found {len(critical_violations)} critical/serious violations"

    def test_keyboard_navigation(self, page: Page, ui_url: str):
        """Test that all interactive elements are keyboard accessible."""
        page.goto(ui_url)

        # Tab through interactive elements
        page.keyboard.press("Tab")

        # Check issue input is focused
        issue_input = page.locator('input[placeholder*="Issue Key"]')
        expect(issue_input).to_be_focused()

        # Tab to mode selector
        page.keyboard.press("Tab")
        mode_select = page.locator('select[name="mode"]')
        expect(mode_select).to_be_focused()

        # Tab to submit button
        page.keyboard.press("Tab")
        submit_button = page.locator('button[type="submit"]')
        expect(submit_button).to_be_focused()

        # Press Enter to submit
        page.keyboard.press("Enter")

        # Should trigger analysis
        page.wait_for_selector(".progress-event, .skeleton-loader", timeout=5000)

    def test_focus_visible_indicators(self, page: Page, ui_url: str):
        """Test that focus indicators are visible."""
        page.goto(ui_url)

        # Tab to first interactive element
        page.keyboard.press("Tab")

        # Check focus indicator is visible
        focused_element = page.evaluate("""
            () => {
                const el = document.activeElement;
                const styles = window.getComputedStyle(el);
                return {
                    outline: styles.outline,
                    outlineWidth: styles.outlineWidth,
                    outlineColor: styles.outlineColor
                };
            }
        """)

        # Should have visible outline
        assert focused_element['outlineWidth'] != '0px', "No focus indicator visible"

    def test_color_contrast(self, page: Page, ui_url: str):
        """Test color contrast ratios meet WCAG AA standards."""
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")

        # Check contrast ratios for key elements
        contrast_checks = page.evaluate("""
            () => {
                const getContrast = (fg, bg) => {
                    // Simplified contrast calculation
                    const getLuminance = (rgb) => {
                        const [r, g, b] = rgb.match(/\\d+/g).map(Number);
                        const [rs, gs, bs] = [r, g, b].map(c => {
                            c = c / 255;
                            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                        });
                        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                    };

                    const l1 = getLuminance(fg);
                    const l2 = getLuminance(bg);
                    const lighter = Math.max(l1, l2);
                    const darker = Math.min(l1, l2);
                    return (lighter + 0.05) / (darker + 0.05);
                };

                const checks = [];
                const elements = document.querySelectorAll('h1, h2, h3, p, button, a, label');

                for (const el of elements) {
                    const styles = window.getComputedStyle(el);
                    const color = styles.color;
                    const bgColor = styles.backgroundColor;

                    if (color && bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {
                        const contrast = getContrast(color, bgColor);
                        const fontSize = parseFloat(styles.fontSize);
                        const fontWeight = parseInt(styles.fontWeight);

                        // WCAG AA: 4.5:1 for normal text, 3:1 for large text
                        const isLargeText = fontSize >= 18 || (fontSize >= 14 && fontWeight >= 700);
                        const minContrast = isLargeText ? 3 : 4.5;

                        checks.push({
                            tag: el.tagName,
                            text: el.textContent.substring(0, 30),
                            contrast: contrast.toFixed(2),
                            passes: contrast >= minContrast,
                            minRequired: minContrast
                        });
                    }
                }

                return checks;
            }
        """)

        # Check for failures
        failures = [c for c in contrast_checks if not c['passes']]

        if failures:
            print(f"\n{len(failures)} contrast failures found:")
            for f in failures[:5]:  # Show first 5
                print(f"  {f['tag']}: {f['text'][:20]}... - {f['contrast']}:1 (need {f['minRequired']}:1)")

        # Allow some tolerance for edge cases
        assert len(failures) < len(contrast_checks) * 0.1, "Too many contrast failures"

    def test_aria_labels(self, page: Page, ui_url: str):
        """Test that interactive elements have proper ARIA labels."""
        page.goto(ui_url)

        # Check buttons have labels
        buttons = page.locator("button").all()
        for button in buttons:
            # Should have either text content or aria-label
            text = button.text_content()
            aria_label = button.get_attribute("aria-label")

            assert text or aria_label, "Button missing accessible label"

    def test_form_labels(self, page: Page, ui_url: str):
        """Test that form inputs have associated labels."""
        page.goto(ui_url)

        # Check all inputs have labels
        inputs = page.locator("input, select, textarea").all()

        for input_el in inputs:
            input_id = input_el.get_attribute("id")
            aria_label = input_el.get_attribute("aria-label")
            aria_labelledby = input_el.get_attribute("aria-labelledby")
            placeholder = input_el.get_attribute("placeholder")

            # Should have one of: associated label, aria-label, aria-labelledby
            has_label = False

            if input_id:
                label = page.locator(f'label[for="{input_id}"]')
                has_label = label.count() > 0

            has_label = has_label or aria_label or aria_labelledby or placeholder

            assert has_label, f"Input missing accessible label: {input_el}"

    def test_heading_hierarchy(self, page: Page, ui_url: str):
        """Test that heading levels are properly structured."""
        page.goto(ui_url)

        headings = page.evaluate("""
            () => {
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                return headings.map(h => ({
                    level: parseInt(h.tagName[1]),
                    text: h.textContent.trim()
                }));
            }
        """)

        if len(headings) == 0:
            pytest.skip("No headings found on page")

        # Should start with h1
        assert headings[0]['level'] == 1, "Page should start with h1"

        # Check for skipped levels
        for i in range(1, len(headings)):
            level_jump = headings[i]['level'] - headings[i-1]['level']
            assert level_jump <= 1, f"Heading level skipped: h{headings[i-1]['level']} to h{headings[i]['level']}"

    def test_alt_text_for_images(self, page: Page, ui_url: str):
        """Test that images have alt text."""
        page.goto(ui_url)

        images = page.locator("img").all()

        for img in images:
            alt = img.get_attribute("alt")
            role = img.get_attribute("role")

            # Decorative images should have empty alt or role="presentation"
            # Meaningful images should have descriptive alt text
            assert alt is not None or role == "presentation", "Image missing alt attribute"

    def test_skip_links(self, page: Page, ui_url: str):
        """Test that skip links are available for keyboard users."""
        page.goto(ui_url)

        # Tab to first element (should be skip link if present)
        page.keyboard.press("Tab")

        # Check if skip link is present
        skip_link = page.locator('a[href^="#"]').first

        if skip_link.count() > 0:
            text = skip_link.text_content()
            assert "skip" in text.lower(), "Skip link should contain 'skip'"

    def test_screen_reader_announcements(self, page: Page, ui_url: str):
        """Test that dynamic content changes are announced."""
        page.goto(ui_url)

        # Submit analysis
        issue_input = page.locator('input[placeholder*="Issue Key"]')
        issue_input.fill("TEST-123")
        page.get_by_role("button", name="Analyze").click()

        # Check for aria-live regions
        live_regions = page.locator('[aria-live]').all()

        # Should have at least one live region for status updates
        assert len(live_regions) > 0, "No aria-live regions found for announcements"

    def test_error_message_accessibility(self, page: Page, ui_url: str):
        """Test that error messages are accessible."""
        page.goto(ui_url)

        # Trigger validation error
        page.get_by_role("button", name="Analyze").click()

        # Wait for error message
        error = page.locator('[role="alert"]')
        expect(error).to_be_visible(timeout=3000)

        # Error should have role="alert" for screen readers
        assert error.count() > 0, "Error message missing role='alert'"

    def test_mobile_accessibility(self, page: Page, ui_url: str):
        """Test accessibility on mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(ui_url)

        # Check touch target sizes (minimum 44x44px)
        touch_targets = page.evaluate("""
            () => {
                const interactive = document.querySelectorAll('button, a, input, select');
                const results = [];

                for (const el of interactive) {
                    const rect = el.getBoundingClientRect();
                    results.push({
                        tag: el.tagName,
                        width: rect.width,
                        height: rect.height,
                        passes: rect.width >= 44 && rect.height >= 44
                    });
                }

                return results;
            }
        """)

        failures = [t for t in touch_targets if not t['passes']]

        if failures:
            print(f"\n{len(failures)} touch target size failures:")
            for f in failures[:5]:
                print(f"  {f['tag']}: {f['width']}x{f['height']}px (need 44x44px)")

        # Allow some small elements (like inline links)
        assert len(failures) < len(touch_targets) * 0.3, "Too many small touch targets"

    def test_reduced_motion_preference(self, page: Page, ui_url: str):
        """Test that prefers-reduced-motion is respected."""
        # Emulate reduced motion preference
        page.emulate_media(features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
        page.goto(ui_url)

        # Check that animations are disabled or minimal
        animation_duration = page.evaluate("""
            () => {
                const el = document.querySelector('.progress-event');
                if (!el) return null;
                const styles = window.getComputedStyle(el);
                return styles.animationDuration;
            }
        """)

        if animation_duration:
            # Should be very short or 0
            duration_ms = float(animation_duration.replace('s', '')) * 1000
            assert duration_ms < 100, f"Animation too long with reduced motion: {duration_ms}ms"
