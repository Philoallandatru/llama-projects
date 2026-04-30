"""
深度分析 UI E2E 测试
"""
import pytest
from playwright.async_api import Page, expect


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDeepAnalysisUI:
    """深度分析 UI 测试"""

    async def test_page_loads(self, page: Page, ui_url: str, deployment_process):
        """测试页面加载"""
        await page.goto(ui_url)

        # 检查页面标题
        await expect(page).to_have_title("Jira Analysis")

        # 检查主要元素存在
        await expect(page.locator("h1")).to_contain_text("Jira Issue 深度分析")

    async def test_input_form_exists(self, page: Page, ui_url: str, deployment_process):
        """测试输入表单存在"""
        await page.goto(ui_url)

        # 检查输入框
        issue_key_input = page.locator('input[placeholder*="Issue Key"]')
        await expect(issue_key_input).to_be_visible()

        # 检查模式选择
        mode_select = page.locator('select[name="mode"]')
        await expect(mode_select).to_be_visible()

        # 检查提交按钮
        submit_button = page.locator('button[type="submit"]')
        await expect(submit_button).to_be_visible()

    async def test_mode_options(self, page: Page, ui_url: str, deployment_process):
        """测试分析模式选项"""
        await page.goto(ui_url)

        mode_select = page.locator('select[name="mode"]')

        # 检查三个模式选项
        options = await mode_select.locator("option").all_text_contents()
        assert "strict" in " ".join(options).lower()
        assert "balanced" in " ".join(options).lower()
        assert "exploratory" in " ".join(options).lower()

    async def test_starter_questions(self, page: Page, ui_url: str, deployment_process):
        """测试预设问题"""
        await page.goto(ui_url)

        # 检查是否有预设问题
        starter_questions = page.locator('[data-testid="starter-question"]')
        count = await starter_questions.count()

        # 应该至少有 2 个预设问题
        assert count >= 2

    async def test_input_validation(self, page: Page, ui_url: str, deployment_process):
        """测试输入验证"""
        await page.goto(ui_url)

        # 尝试提交空表单
        submit_button = page.locator('button[type="submit"]')
        await submit_button.click()

        # 应该显示验证错误
        error_message = page.locator('[role="alert"]')
        await expect(error_message).to_be_visible(timeout=2000)

    async def test_issue_key_format(self, page: Page, ui_url: str, deployment_process):
        """测试 Issue Key 格式验证"""
        await page.goto(ui_url)

        issue_key_input = page.locator('input[placeholder*="Issue Key"]')

        # 输入无效格式
        await issue_key_input.fill("invalid")
        await page.locator('button[type="submit"]').click()

        # 应该显示格式错误
        error_message = page.locator('text=/.*格式.*|.*format.*/i')
        await expect(error_message).to_be_visible(timeout=2000)

    async def test_submit_analysis(self, page: Page, ui_url: str, deployment_process):
        """测试提交分析（模拟）"""
        await page.goto(ui_url)

        # 填写表单
        await page.locator('input[placeholder*="Issue Key"]').fill("TEST-123")
        await page.locator('select[name="mode"]').select_option("strict")

        # 提交
        await page.locator('button[type="submit"]').click()

        # 等待加载指示器出现
        loading_indicator = page.locator('[data-testid="loading"]')
        await expect(loading_indicator).to_be_visible(timeout=5000)

    async def test_progress_events_display(self, page: Page, ui_url: str, deployment_process):
        """测试进度事件显示"""
        await page.goto(ui_url)

        # 填写并提交
        await page.locator('input[placeholder*="Issue Key"]').fill("TEST-123")
        await page.locator('button[type="submit"]').click()

        # 等待进度事件出现
        progress_event = page.locator('[data-testid="progress-event"]')
        await expect(progress_event.first).to_be_visible(timeout=10000)

    async def test_result_display(self, page: Page, ui_url: str, deployment_process):
        """测试结果显示"""
        await page.goto(ui_url)

        # 填写并提交
        await page.locator('input[placeholder*="Issue Key"]').fill("TEST-123")
        await page.locator('button[type="submit"]').click()

        # 等待结果显示（最多等待 60 秒）
        result_container = page.locator('[data-testid="result"]')
        await expect(result_container).to_be_visible(timeout=60000)

    async def test_evidence_count_display(self, page: Page, ui_url: str, deployment_process):
        """测试证据数量显示"""
        await page.goto(ui_url)

        # 填写并提交
        await page.locator('input[placeholder*="Issue Key"]').fill("TEST-123")
        await page.locator('button[type="submit"]').click()

        # 等待证据统计显示
        evidence_count = page.locator('[data-testid="evidence-count"]')
        await expect(evidence_count).to_be_visible(timeout=60000)

        # 检查是否显示了三类证据
        text = await evidence_count.text_content()
        assert "similar" in text.lower() or "相似" in text
        assert "confluence" in text.lower()
        assert "spec" in text.lower() or "规格" in text

    async def test_new_analysis_button(self, page: Page, ui_url: str, deployment_process):
        """测试新建分析按钮"""
        await page.goto(ui_url)

        # 完成一次分析
        await page.locator('input[placeholder*="Issue Key"]').fill("TEST-123")
        await page.locator('button[type="submit"]').click()

        # 等待结果
        await page.locator('[data-testid="result"]').wait_for(timeout=60000)

        # 点击新建分析按钮
        new_analysis_button = page.locator('button:has-text("新建分析")')
        await new_analysis_button.click()

        # 表单应该重置
        issue_key_input = page.locator('input[placeholder*="Issue Key"]')
        value = await issue_key_input.input_value()
        assert value == ""

    async def test_responsive_design(self, page: Page, ui_url: str, deployment_process):
        """测试响应式设计"""
        # 测试桌面视图
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(ui_url)
        await expect(page.locator("h1")).to_be_visible()

        # 测试平板视图
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.goto(ui_url)
        await expect(page.locator("h1")).to_be_visible()

        # 测试移动视图
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto(ui_url)
        await expect(page.locator("h1")).to_be_visible()

    async def test_keyboard_navigation(self, page: Page, ui_url: str, deployment_process):
        """测试键盘导航"""
        await page.goto(ui_url)

        # Tab 到输入框
        await page.keyboard.press("Tab")
        issue_key_input = page.locator('input[placeholder*="Issue Key"]')
        await expect(issue_key_input).to_be_focused()

        # 输入内容
        await page.keyboard.type("TEST-123")

        # Tab 到模式选择
        await page.keyboard.press("Tab")
        mode_select = page.locator('select[name="mode"]')
        await expect(mode_select).to_be_focused()

        # Tab 到提交按钮
        await page.keyboard.press("Tab")
        submit_button = page.locator('button[type="submit"]')
        await expect(submit_button).to_be_focused()

        # Enter 提交
        await page.keyboard.press("Enter")

        # 应该开始分析
        loading_indicator = page.locator('[data-testid="loading"]')
        await expect(loading_indicator).to_be_visible(timeout=5000)
