"""
批量分析 UI E2E 测试
"""
import pytest
from playwright.async_api import Page, expect


@pytest.mark.asyncio
@pytest.mark.e2e
class TestBatchAnalysisUI:
    """批量分析 UI 测试"""

    async def test_batch_mode_switch(self, page: Page, ui_url: str, deployment_process):
        """测试切换到批量模式"""
        await page.goto(ui_url)

        # 查找批量模式切换按钮
        batch_mode_button = page.locator('button:has-text("批量分析")')
        await batch_mode_button.click()

        # 检查批量输入界面
        batch_input = page.locator('textarea[placeholder*="Issue Keys"]')
        await expect(batch_input).to_be_visible()

    async def test_batch_input_format(self, page: Page, ui_url: str, deployment_process):
        """测试批量输入格式"""
        await page.goto(ui_url)

        # 切换到批量模式
        await page.locator('button:has-text("批量分析")').click()

        # 输入多个 issue keys
        batch_input = page.locator('textarea[placeholder*="Issue Keys"]')
        await batch_input.fill("TEST-123\nTEST-124\nTEST-125")

        # 提交
        await page.locator('button[type="submit"]').click()

        # 应该开始批量分析
        loading_indicator = page.locator('[data-testid="loading"]')
        await expect(loading_indicator).to_be_visible(timeout=5000)

    async def test_batch_progress_tracking(self, page: Page, ui_url: str, deployment_process):
        """测试批量分析进度跟踪"""
        await page.goto(ui_url)

        # 切换到批量模式并提交
        await page.locator('button:has-text("批量分析")').click()
        await page.locator('textarea[placeholder*="Issue Keys"]').fill("TEST-123\nTEST-124")
        await page.locator('button[type="submit"]').click()

        # 等待进度显示
        progress_bar = page.locator('[data-testid="batch-progress"]')
        await expect(progress_bar).to_be_visible(timeout=10000)

        # 检查进度文本（例如 "1/2 完成"）
        progress_text = page.locator('[data-testid="batch-progress-text"]')
        await expect(progress_text).to_be_visible()

    async def test_batch_results_summary(self, page: Page, ui_url: str, deployment_process):
        """测试批量结果汇总"""
        await page.goto(ui_url)

        # 提交批量分析
        await page.locator('button:has-text("批量分析")').click()
        await page.locator('textarea[placeholder*="Issue Keys"]').fill("TEST-123\nTEST-124")
        await page.locator('button[type="submit"]').click()

        # 等待汇总结果
        summary = page.locator('[data-testid="batch-summary"]')
        await expect(summary).to_be_visible(timeout=120000)

        # 检查汇总信息
        text = await summary.text_content()
        assert "总计" in text or "total" in text.lower()
        assert "成功" in text or "success" in text.lower()

    async def test_batch_individual_results(self, page: Page, ui_url: str, deployment_process):
        """测试批量分析的单个结果"""
        await page.goto(ui_url)

        # 提交批量分析
        await page.locator('button:has-text("批量分析")').click()
        await page.locator('textarea[placeholder*="Issue Keys"]').fill("TEST-123\nTEST-124")
        await page.locator('button[type="submit"]').click()

        # 等待结果
        await page.locator('[data-testid="batch-summary"]').wait_for(timeout=120000)

        # 检查单个结果项
        result_items = page.locator('[data-testid="batch-result-item"]')
        count = await result_items.count()
        assert count >= 2

    async def test_batch_export_results(self, page: Page, ui_url: str, deployment_process):
        """测试导出批量结果"""
        await page.goto(ui_url)

        # 完成批量分析
        await page.locator('button:has-text("批量分析")').click()
        await page.locator('textarea[placeholder*="Issue Keys"]').fill("TEST-123\nTEST-124")
        await page.locator('button[type="submit"]').click()

        # 等待结果
        await page.locator('[data-testid="batch-summary"]').wait_for(timeout=120000)

        # 点击导出按钮
        export_button = page.locator('button:has-text("导出")')

        # 监听下载事件
        async with page.expect_download() as download_info:
            await export_button.click()

        download = await download_info.value

        # 检查文件名
        assert download.suggested_filename.endswith((".json", ".csv", ".xlsx"))

    async def test_batch_concurrent_limit(self, page: Page, ui_url: str, deployment_process):
        """测试并发限制设置"""
        await page.goto(ui_url)

        # 切换到批量模式
        await page.locator('button:has-text("批量分析")').click()

        # 查找并发数设置
        concurrent_input = page.locator('input[name="max_concurrent"]')

        if await concurrent_input.is_visible():
            # 设置并发数
            await concurrent_input.fill("3")

            # 提交
            await page.locator('textarea[placeholder*="Issue Keys"]').fill("TEST-123\nTEST-124\nTEST-125")
            await page.locator('button[type="submit"]').click()

            # 应该开始分析
            loading_indicator = page.locator('[data-testid="loading"]')
            await expect(loading_indicator).to_be_visible(timeout=5000)

    async def test_batch_error_handling(self, page: Page, ui_url: str, deployment_process):
        """测试批量分析错误处理"""
        await page.goto(ui_url)

        # 提交包含无效 issue key 的批量分析
        await page.locator('button:has-text("批量分析")').click()
        await page.locator('textarea[placeholder*="Issue Keys"]').fill("INVALID\nTEST-123")
        await page.locator('button[type="submit"]').click()

        # 等待结果
        await page.locator('[data-testid="batch-summary"]').wait_for(timeout=120000)

        # 应该显示错误信息
        error_items = page.locator('[data-testid="batch-error-item"]')
        count = await error_items.count()
        assert count >= 1

    async def test_batch_cancel(self, page: Page, ui_url: str, deployment_process):
        """测试取消批量分析"""
        await page.goto(ui_url)

        # 开始批量分析
        await page.locator('button:has-text("批量分析")').click()
        await page.locator('textarea[placeholder*="Issue Keys"]').fill("TEST-123\nTEST-124\nTEST-125")
        await page.locator('button[type="submit"]').click()

        # 等待进度显示
        await page.locator('[data-testid="batch-progress"]').wait_for(timeout=10000)

        # 点击取消按钮
        cancel_button = page.locator('button:has-text("取消")')
        if await cancel_button.is_visible():
            await cancel_button.click()

            # 应该显示取消确认
            confirm_dialog = page.locator('[role="dialog"]')
            await expect(confirm_dialog).to_be_visible()
