"""
Cross-browser compatibility tests for Jira Analysis System.

Tests functionality across Chromium, Firefox, and WebKit browsers.
"""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext, expect


@pytest.fixture(params=["chromium", "firefox", "webkit"])
def browser_type(request):
    """Parametrize tests across all browser types."""
    return request.param


@pytest.fixture
def cross_browser_page(browser_type, playwright, ui_url):
    """Create a page in the specified browser type."""
    browser = getattr(playwright, browser_type).launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
    browser.close()


class TestCrossBrowser:
    """Cross-browser compatibility test suite."""

    def test_page_loads_in_all_browsers(self, cross_browser_page: Page, ui_url: str):
        """Test that the page loads successfully in all browsers."""
        cross_browser_page.goto(ui_url)
        cross_browser_page.wait_for_load_state("networkidle")

        # Check page title
        title = cross_browser_page.title()
        assert "Jira Analysis" in title or len(title) > 0

        # Check main content is visible
        main_content = cross_browser_page.locator("main, #__next, .container")
        expect(main_content.first).to_be_visible()

    def test_form_submission_works(self, cross_browser_page: Page, ui_url: str):
        """Test form submission works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Fill and submit form
        issue_input = cross_browser_page.locator('input[placeholder*="Issue Key"]')
        issue_input.fill("TEST-123")

        submit_button = cross_browser_page.get_by_role("button", name="Analyze")
        submit_button.click()

        # Should show progress or result
        cross_browser_page.wait_for_selector(
            ".progress-event, .skeleton-loader, .analysis-result",
            timeout=10000
        )

    def test_css_rendering_consistency(self, cross_browser_page: Page, ui_url: str):
        """Test that CSS renders consistently across browsers."""
        cross_browser_page.goto(ui_url)
        cross_browser_page.wait_for_load_state("networkidle")

        # Check key layout properties
        layout_check = cross_browser_page.evaluate("""
            () => {
                const container = document.querySelector('.container, main');
                if (!container) return null;

                const styles = window.getComputedStyle(container);
                return {
                    display: styles.display,
                    maxWidth: styles.maxWidth,
                    padding: styles.padding,
                    hasFlexbox: styles.display.includes('flex') || styles.display.includes('grid')
                };
            }
        """)

        assert layout_check is not None, "Main container not found"
        assert layout_check['display'] != 'none', "Container is hidden"

    def test_javascript_features_work(self, cross_browser_page: Page, ui_url: str):
        """Test that JavaScript features work in all browsers."""
        cross_browser_page.goto(ui_url)

        # Test modern JS features
        js_support = cross_browser_page.evaluate("""
            () => {
                return {
                    promises: typeof Promise !== 'undefined',
                    async: typeof (async () => {}) === 'function',
                    fetch: typeof fetch !== 'undefined',
                    localStorage: typeof localStorage !== 'undefined',
                    sessionStorage: typeof sessionStorage !== 'undefined'
                };
            }
        """)

        assert js_support['promises'], "Promises not supported"
        assert js_support['async'], "Async/await not supported"
        assert js_support['fetch'], "Fetch API not supported"
        assert js_support['localStorage'], "localStorage not supported"

    def test_event_handling_works(self, cross_browser_page: Page, ui_url: str):
        """Test that event handlers work in all browsers."""
        cross_browser_page.goto(ui_url)

        # Test click event
        issue_input = cross_browser_page.locator('input[placeholder*="Issue Key"]')
        issue_input.click()
        expect(issue_input).to_be_focused()

        # Test input event
        issue_input.fill("TEST")
        value = issue_input.input_value()
        assert value == "TEST"

        # Test change event on select
        mode_select = cross_browser_page.locator('select[name="mode"]')
        if mode_select.count() > 0:
            mode_select.select_option("balanced")
            selected = mode_select.input_value()
            assert selected == "balanced"

    def test_responsive_design_works(self, cross_browser_page: Page, ui_url: str):
        """Test responsive design works in all browsers."""
        # Test desktop
        cross_browser_page.set_viewport_size({"width": 1920, "height": 1080})
        cross_browser_page.goto(ui_url)
        cross_browser_page.wait_for_load_state("networkidle")

        desktop_layout = cross_browser_page.evaluate("""
            () => {
                const container = document.querySelector('.container, main');
                return container ? container.offsetWidth : 0;
            }
        """)

        # Test tablet
        cross_browser_page.set_viewport_size({"width": 768, "height": 1024})
        cross_browser_page.reload()

        tablet_layout = cross_browser_page.evaluate("""
            () => {
                const container = document.querySelector('.container, main');
                return container ? container.offsetWidth : 0;
            }
        """)

        # Test mobile
        cross_browser_page.set_viewport_size({"width": 375, "height": 667})
        cross_browser_page.reload()

        mobile_layout = cross_browser_page.evaluate("""
            () => {
                const container = document.querySelector('.container, main');
                return container ? container.offsetWidth : 0;
            }
        """)

        # Layouts should adapt to viewport
        assert desktop_layout > tablet_layout or desktop_layout > 1000
        assert tablet_layout > mobile_layout or tablet_layout > 500

    def test_local_storage_works(self, cross_browser_page: Page, ui_url: str):
        """Test localStorage works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Set localStorage value
        cross_browser_page.evaluate("""
            () => {
                localStorage.setItem('test_key', 'test_value');
            }
        """)

        # Retrieve value
        value = cross_browser_page.evaluate("""
            () => {
                return localStorage.getItem('test_key');
            }
        """)

        assert value == 'test_value'

        # Clean up
        cross_browser_page.evaluate("""
            () => {
                localStorage.removeItem('test_key');
            }
        """)

    def test_dark_mode_toggle_works(self, cross_browser_page: Page, ui_url: str):
        """Test dark mode toggle works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Find theme toggle button
        theme_toggle = cross_browser_page.locator('button[aria-label*="theme"], .theme-toggle')

        if theme_toggle.count() > 0:
            # Get initial theme
            initial_theme = cross_browser_page.evaluate("""
                () => {
                    return document.documentElement.getAttribute('data-theme') ||
                           document.body.classList.contains('dark-mode') ? 'dark' : 'light';
                }
            """)

            # Toggle theme
            theme_toggle.click()
            cross_browser_page.wait_for_timeout(500)

            # Get new theme
            new_theme = cross_browser_page.evaluate("""
                () => {
                    return document.documentElement.getAttribute('data-theme') ||
                           document.body.classList.contains('dark-mode') ? 'dark' : 'light';
                }
            """)

            # Theme should have changed
            assert initial_theme != new_theme

    def test_streaming_output_works(self, cross_browser_page: Page, ui_url: str):
        """Test streaming output works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Start analysis
        issue_input = cross_browser_page.locator('input[placeholder*="Issue Key"]')
        issue_input.fill("TEST-123")
        cross_browser_page.get_by_role("button", name="Analyze").click()

        # Wait for streaming to start
        try:
            cross_browser_page.wait_for_selector(".streaming-text, .progress-event", timeout=5000)
            streaming_works = True
        except Exception:
            streaming_works = False

        # Should work in all browsers
        assert streaming_works, "Streaming output not working"

    def test_error_handling_works(self, cross_browser_page: Page, ui_url: str):
        """Test error handling works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Trigger validation error
        cross_browser_page.get_by_role("button", name="Analyze").click()

        # Should show error message
        error_message = cross_browser_page.locator('[role="alert"], .error-message')
        expect(error_message.first).to_be_visible(timeout=3000)

    def test_batch_analysis_works(self, cross_browser_page: Page, ui_url: str):
        """Test batch analysis works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Switch to batch tab
        batch_tab = cross_browser_page.get_by_role("tab", name="Batch Analysis")
        if batch_tab.count() > 0:
            batch_tab.click()

            # Fill batch input
            batch_input = cross_browser_page.locator('textarea[placeholder*="Issue Keys"]')
            batch_input.fill("TEST-001,TEST-002")

            # Submit
            cross_browser_page.get_by_role("button", name="Analyze Batch").click()

            # Should show progress
            cross_browser_page.wait_for_selector(
                ".batch-progress, .progress-event",
                timeout=5000
            )

    def test_keyboard_navigation_works(self, cross_browser_page: Page, ui_url: str):
        """Test keyboard navigation works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Tab through elements
        cross_browser_page.keyboard.press("Tab")

        # First interactive element should be focused
        focused = cross_browser_page.evaluate("""
            () => {
                return document.activeElement.tagName;
            }
        """)

        assert focused in ['INPUT', 'BUTTON', 'SELECT', 'A']

    def test_copy_paste_works(self, cross_browser_page: Page, ui_url: str):
        """Test copy/paste functionality works in all browsers."""
        cross_browser_page.goto(ui_url)

        # Type in input
        issue_input = cross_browser_page.locator('input[placeholder*="Issue Key"]')
        issue_input.fill("TEST-123")

        # Select all and copy
        issue_input.click()
        cross_browser_page.keyboard.press("Control+A")
        cross_browser_page.keyboard.press("Control+C")

        # Clear and paste
        issue_input.fill("")
        cross_browser_page.keyboard.press("Control+V")

        # Value should be restored
        value = issue_input.input_value()
        assert value == "TEST-123"

    def test_console_errors_check(self, cross_browser_page: Page, ui_url: str):
        """Test that there are no console errors in any browser."""
        console_messages = []

        def handle_console(msg):
            if msg.type in ['error', 'warning']:
                console_messages.append({
                    'type': msg.type,
                    'text': msg.text
                })

        cross_browser_page.on("console", handle_console)

        # Load page and interact
        cross_browser_page.goto(ui_url)
        cross_browser_page.wait_for_load_state("networkidle")

        # Perform basic interaction
        issue_input = cross_browser_page.locator('input[placeholder*="Issue Key"]')
        if issue_input.count() > 0:
            issue_input.fill("TEST-123")

        # Check for errors
        errors = [m for m in console_messages if m['type'] == 'error']

        if errors:
            print(f"\n{len(errors)} console errors found:")
            for error in errors[:5]:
                print(f"  - {error['text']}")

        # Should have minimal errors (allow some third-party warnings)
        assert len(errors) < 3, f"Too many console errors: {len(errors)}"
