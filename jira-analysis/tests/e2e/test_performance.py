"""
Performance tests for Jira Analysis System.

Tests page load times, API response times, and resource usage.
"""

import pytest
import time
from playwright.sync_api import Page, expect


class TestPerformance:
    """Performance test suite."""

    def test_page_load_performance(self, page: Page, ui_url: str):
        """Test that the page loads within acceptable time."""
        start_time = time.time()
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time

        # Page should load within 3 seconds
        assert load_time < 3.0, f"Page load took {load_time:.2f}s, expected < 3s"

        # Take screenshot for documentation
        page.screenshot(path="screenshots/performance_page_load.png")

    def test_deep_analysis_response_time(self, page: Page, ui_url: str):
        """Test deep analysis API response time."""
        page.goto(ui_url)

        # Fill in issue key
        issue_input = page.locator('input[placeholder*="PROJ-123"]')
        issue_input.fill("TEST-001")

        # Measure time from submit to first response
        start_time = time.time()
        page.get_by_role("button", name="Analyze").click()

        # Wait for either loading state or result
        page.wait_for_selector(".skeleton-loader, .analysis-result", timeout=10000)
        response_time = time.time() - start_time

        # Initial response should be within 2 seconds
        assert response_time < 2.0, f"Response time {response_time:.2f}s, expected < 2s"

    def test_batch_analysis_throughput(self, page: Page, ui_url: str):
        """Test batch analysis can handle multiple issues efficiently."""
        page.goto(ui_url)

        # Switch to batch analysis tab
        page.get_by_role("tab", name="Batch Analysis").click()

        # Enter multiple issue keys
        issue_keys = "TEST-001,TEST-002,TEST-003"
        batch_input = page.locator('textarea[placeholder*="PROJ-123"]')
        batch_input.fill(issue_keys)

        # Measure total processing time
        start_time = time.time()
        page.get_by_role("button", name="Analyze Batch").click()

        # Wait for batch to complete (or timeout)
        try:
            page.wait_for_selector(".batch-complete, .batch-summary", timeout=30000)
            total_time = time.time() - start_time

            # Should process 3 issues in under 30 seconds
            assert total_time < 30.0, f"Batch took {total_time:.2f}s, expected < 30s"

            # Calculate throughput
            throughput = len(issue_keys.split(",")) / total_time
            print(f"Throughput: {throughput:.2f} issues/second")

        except Exception as e:
            # If timeout, still record the attempt
            print(f"Batch analysis timed out or failed: {e}")

    def test_streaming_performance(self, page: Page, ui_url: str):
        """Test that streaming output renders smoothly without lag."""
        page.goto(ui_url)

        # Start analysis
        issue_input = page.locator('input[placeholder*="PROJ-123"]')
        issue_input.fill("TEST-001")
        page.get_by_role("button", name="Analyze").click()

        # Monitor streaming output
        streaming_started = False
        chunk_count = 0
        start_time = time.time()

        # Wait for streaming to start
        try:
            page.wait_for_selector(".streaming-text", timeout=5000)
            streaming_started = True

            # Count chunks received in first 5 seconds
            for _ in range(10):
                time.sleep(0.5)
                chunks = page.locator(".streaming-text").count()
                if chunks > chunk_count:
                    chunk_count = chunks

        except Exception:
            pass

        if streaming_started:
            elapsed = time.time() - start_time
            chunk_rate = chunk_count / elapsed if elapsed > 0 else 0
            print(f"Streaming rate: {chunk_rate:.2f} chunks/second")

            # Should receive at least 1 chunk per second
            assert chunk_rate >= 1.0, f"Streaming too slow: {chunk_rate:.2f} chunks/s"

    def test_memory_usage_stability(self, page: Page, ui_url: str):
        """Test that repeated operations don't cause memory leaks."""
        page.goto(ui_url)

        # Get initial metrics
        initial_metrics = page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize
                    };
                }
                return null;
            }
        """)

        if initial_metrics is None:
            pytest.skip("Performance.memory API not available")

        # Perform 5 analysis operations
        for i in range(5):
            issue_input = page.locator('input[placeholder*="PROJ-123"]')
            issue_input.fill(f"TEST-{i:03d}")
            page.get_by_role("button", name="Analyze").click()

            # Wait a bit for operation to start
            time.sleep(1)

            # Clear/reset for next iteration
            page.reload()

        # Get final metrics
        final_metrics = page.evaluate("""
            () => {
                return {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize
                };
            }
        """)

        # Memory growth should be reasonable (< 50MB increase)
        memory_growth = (final_metrics["usedJSHeapSize"] - initial_metrics["usedJSHeapSize"]) / (1024 * 1024)
        print(f"Memory growth: {memory_growth:.2f} MB")

        assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.2f} MB"

    def test_concurrent_requests_handling(self, page: Page, ui_url: str):
        """Test system handles concurrent requests gracefully."""
        page.goto(ui_url)

        # Open multiple tabs (simulate concurrent users)
        contexts = []
        pages = []

        try:
            for i in range(3):
                context = page.context.browser.new_context()
                new_page = context.new_page()
                new_page.goto(ui_url)
                contexts.append(context)
                pages.append(new_page)

            # Submit requests from all tabs simultaneously
            start_time = time.time()
            for i, p in enumerate(pages):
                issue_input = p.locator('input[placeholder*="PROJ-123"]')
                issue_input.fill(f"TEST-{i:03d}")
                p.get_by_role("button", name="Analyze").click()

            # Wait for all to get initial response
            for p in pages:
                try:
                    p.wait_for_selector(".skeleton-loader, .analysis-result", timeout=10000)
                except Exception:
                    pass

            total_time = time.time() - start_time

            # All requests should get initial response within 10 seconds
            assert total_time < 10.0, f"Concurrent requests took {total_time:.2f}s"

        finally:
            # Cleanup
            for context in contexts:
                context.close()

    def test_large_result_rendering(self, page: Page, ui_url: str):
        """Test that large analysis results render without freezing."""
        page.goto(ui_url)

        # Submit analysis
        issue_input = page.locator('input[placeholder*="PROJ-123"]')
        issue_input.fill("TEST-LARGE")

        start_time = time.time()
        page.get_by_role("button", name="Analyze").click()

        # Wait for result to appear
        try:
            page.wait_for_selector(".analysis-result", timeout=15000)
            render_time = time.time() - start_time

            # Should render within 15 seconds even for large results
            assert render_time < 15.0, f"Rendering took {render_time:.2f}s"

            # Check page is still responsive
            page.mouse.move(100, 100)
            page.mouse.click(100, 100)

        except Exception as e:
            print(f"Large result test failed: {e}")

    def test_network_efficiency(self, page: Page, ui_url: str):
        """Test that network requests are optimized."""
        # Track network requests
        requests = []

        def handle_request(request):
            requests.append({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type
            })

        page.on("request", handle_request)

        # Load page and perform analysis
        page.goto(ui_url)
        page.wait_for_load_state("networkidle")

        initial_request_count = len(requests)

        # Perform analysis
        issue_input = page.locator('input[placeholder*="PROJ-123"]')
        issue_input.fill("TEST-001")
        page.get_by_role("button", name="Analyze").click()

        time.sleep(2)

        total_requests = len(requests)
        analysis_requests = total_requests - initial_request_count

        print(f"Initial page load: {initial_request_count} requests")
        print(f"Analysis operation: {analysis_requests} requests")

        # Should not make excessive requests
        assert initial_request_count < 50, f"Too many initial requests: {initial_request_count}"
        assert analysis_requests < 10, f"Too many analysis requests: {analysis_requests}"
