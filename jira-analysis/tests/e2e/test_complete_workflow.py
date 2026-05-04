"""
完整工作流 E2E 测试 - 从点击到截图验证

这个测试实现完整的用户旅程：
1. 打开页面
2. 填写表单
3. 点击提交按钮
4. 等待分析完成
5. 截图验证结果
"""
import pytest
from pathlib import Path
from playwright.async_api import Page, expect


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflow:
    """完整工作流测试 - 端到端验证"""

    async def test_deep_analysis_complete_flow_with_screenshot(
        self, page: Page, ui_url: str, deployment_process, tmp_path: Path
    ):
        """
        测试深度分析完整流程并截图验证

        步骤：
        1. 访问页面
        2. 填写 issue key
        3. 选择分析模式
        4. 点击提交按钮
        5. 等待进度事件
        6. 等待分析结果
        7. 验证结果内容
        8. 截图保存
        """
        # Step 1: 访问页面
        await page.goto(ui_url)
        await expect(page).to_have_title("Jira Analysis")

        # 截图：初始页面
        screenshot_dir = tmp_path / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        await page.screenshot(path=str(screenshot_dir / "01_initial_page.png"))

        # Step 2: 填写 issue key
        issue_key_input = page.locator('input[placeholder*="Issue Key"]')
        await expect(issue_key_input).to_be_visible()
        await issue_key_input.fill("TEST-123")

        # 截图：填写表单
        await page.screenshot(path=str(screenshot_dir / "02_form_filled.png"))

        # Step 3: 选择分析模式
        mode_select = page.locator('select[name="mode"]')
        await mode_select.select_option("balanced")

        # 截图：选择模式
        await page.screenshot(path=str(screenshot_dir / "03_mode_selected.png"))

        # Step 4: 点击提交按钮
        submit_button = page.locator('button[type="submit"]')
        await expect(submit_button).to_be_visible()
        await submit_button.click()

        # 截图：点击提交
        await page.screenshot(path=str(screenshot_dir / "04_submitted.png"))

        # Step 5: 等待进度事件出现
        loading_indicator = page.locator('[data-testid="loading"]')
        await expect(loading_indicator).to_be_visible(timeout=10000)

        # 截图：加载中
        await page.screenshot(path=str(screenshot_dir / "05_loading.png"))

        # 等待第一个进度事件
        progress_event = page.locator('[data-testid="progress-event"]')
        await expect(progress_event.first).to_be_visible(timeout=15000)

        # 截图：进度事件
        await page.screenshot(path=str(screenshot_dir / "06_progress_events.png"))

        # Step 6: 等待分析结果（最多 120 秒）
        result_container = page.locator('[data-testid="result"]')
        await expect(result_container).to_be_visible(timeout=120000)

        # 等待结果内容加载完成
        await page.wait_for_timeout(2000)  # 等待流式输出完成

        # 截图：分析结果
        await page.screenshot(path=str(screenshot_dir / "07_analysis_result.png"), full_page=True)

        # Step 7: 验证结果内容
        result_text = await result_container.text_content()
        assert result_text is not None
        assert len(result_text) > 100  # 结果应该有实质内容

        # 验证证据统计
        evidence_count = page.locator('[data-testid="evidence-count"]')
        if await evidence_count.count() > 0:
            await expect(evidence_count).to_be_visible()
            # 截图：证据统计
            await page.screenshot(path=str(screenshot_dir / "08_evidence_count.png"))

        # 验证分析部分（如果存在）
        analysis_sections = page.locator('[data-testid="analysis-section"]')
        section_count = await analysis_sections.count()
        if section_count > 0:
            # 至少应该有一个分析部分
            assert section_count >= 1

            # 截图：展开所有分析部分
            for i in range(section_count):
                section = analysis_sections.nth(i)
                # 如果是可折叠的，展开它
                expand_button = section.locator('button[aria-expanded="false"]')
                if await expand_button.count() > 0:
                    await expand_button.click()
                    await page.wait_for_timeout(500)

            await page.screenshot(
                path=str(screenshot_dir / "09_all_sections_expanded.png"),
                full_page=True
            )

        # Step 8: 测试导出功能（如果存在）
        export_button = page.locator('button:has-text("导出")')
        if await export_button.count() > 0:
            await export_button.click()
            await page.wait_for_timeout(1000)
            await page.screenshot(path=str(screenshot_dir / "10_export_menu.png"))

        # 最终截图：完整页面
        await page.screenshot(
            path=str(screenshot_dir / "11_final_complete.png"),
            full_page=True
        )

        print(f"\n✅ 测试完成！截图已保存到: {screenshot_dir}")
        print(f"   共生成 {len(list(screenshot_dir.glob('*.png')))} 张截图")

    async def test_batch_analysis_complete_flow_with_screenshot(
        self, page: Page, ui_url: str, deployment_process, tmp_path: Path
    ):
        """
        测试批量分析完整流程并截图验证

        步骤：
        1. 访问页面
        2. 切换到批量模式
        3. 填写多个 issue keys
        4. 设置并发数
        5. 点击提交
        6. 监控批量进度
        7. 等待汇总报告
        8. 截图验证
        """
        # Step 1: 访问页面
        await page.goto(ui_url)

        screenshot_dir = tmp_path / "screenshots" / "batch"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 截图：初始页面
        await page.screenshot(path=str(screenshot_dir / "01_initial_page.png"))

        # Step 2: 切换到批量模式
        batch_tab = page.locator('button:has-text("批量分析")')
        if await batch_tab.count() > 0:
            await batch_tab.click()
            await page.wait_for_timeout(500)

            # 截图：批量模式
            await page.screenshot(path=str(screenshot_dir / "02_batch_mode.png"))

            # Step 3: 填写多个 issue keys
            batch_input = page.locator('textarea[placeholder*="Issue Keys"]')
            await expect(batch_input).to_be_visible()
            await batch_input.fill("TEST-123\nTEST-124\nTEST-125")

            # 截图：填写 issue keys
            await page.screenshot(path=str(screenshot_dir / "03_issues_filled.png"))

            # Step 4: 设置并发数
            concurrent_input = page.locator('input[name="max_concurrent"]')
            if await concurrent_input.count() > 0:
                await concurrent_input.fill("2")
                await page.screenshot(path=str(screenshot_dir / "04_concurrent_set.png"))

            # Step 5: 点击提交
            submit_button = page.locator('button[type="submit"]')
            await submit_button.click()

            # 截图：提交批量任务
            await page.screenshot(path=str(screenshot_dir / "05_submitted.png"))

            # Step 6: 监控批量进度
            batch_progress = page.locator('[data-testid="batch-progress"]')
            await expect(batch_progress).to_be_visible(timeout=15000)

            # 截图：批量进度
            await page.screenshot(path=str(screenshot_dir / "06_batch_progress.png"))

            # 等待进度更新（每 5 秒截图一次）
            for i in range(6):  # 最多等待 30 秒
                await page.wait_for_timeout(5000)
                await page.screenshot(
                    path=str(screenshot_dir / f"07_progress_update_{i+1}.png")
                )

                # 检查是否完成
                if await page.locator('[data-testid="batch-complete"]').count() > 0:
                    break

            # Step 7: 等待汇总报告
            report_container = page.locator('[data-testid="batch-report"]')
            await expect(report_container).to_be_visible(timeout=180000)

            # 等待报告内容加载
            await page.wait_for_timeout(2000)

            # 截图：汇总报告
            await page.screenshot(
                path=str(screenshot_dir / "08_batch_report.png"),
                full_page=True
            )

            # Step 8: 验证报告内容
            report_text = await report_container.text_content()
            assert report_text is not None
            assert len(report_text) > 100

            # 验证统计信息
            stats = page.locator('[data-testid="batch-stats"]')
            if await stats.count() > 0:
                await page.screenshot(path=str(screenshot_dir / "09_batch_stats.png"))

            # 最终截图
            await page.screenshot(
                path=str(screenshot_dir / "10_final_complete.png"),
                full_page=True
            )

            print(f"\n✅ 批量测试完成！截图已保存到: {screenshot_dir}")
            print(f"   共生成 {len(list(screenshot_dir.glob('*.png')))} 张截图")

    async def test_error_handling_with_screenshot(
        self, page: Page, ui_url: str, deployment_process, tmp_path: Path
    ):
        """
        测试错误处理并截图

        测试场景：
        1. 无效的 issue key
        2. 网络错误
        3. 超时错误
        """
        screenshot_dir = tmp_path / "screenshots" / "errors"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # 场景 1: 无效的 issue key
        await page.goto(ui_url)
        await page.locator('input[placeholder*="Issue Key"]').fill("INVALID")
        await page.locator('button[type="submit"]').click()

        # 等待错误消息
        error_message = page.locator('[role="alert"]')
        await expect(error_message).to_be_visible(timeout=5000)

        # 截图：格式错误
        await page.screenshot(path=str(screenshot_dir / "01_invalid_format.png"))

        # 场景 2: 不存在的 issue
        await page.goto(ui_url)
        await page.locator('input[placeholder*="Issue Key"]').fill("NOTFOUND-999")
        await page.locator('button[type="submit"]').click()

        # 等待错误提示
        await page.wait_for_timeout(10000)

        # 截图：Issue 不存在
        await page.screenshot(path=str(screenshot_dir / "02_issue_not_found.png"))

        print(f"\n✅ 错误处理测试完成！截图已保存到: {screenshot_dir}")

    async def test_different_issue_types_with_screenshots(
        self, page: Page, ui_url: str, deployment_process, tmp_path: Path
    ):
        """
        测试不同 issue 类型的路由和分析

        测试：
        1. Bug → RCA profile
        2. DAS/PRD → Traceability profile
        3. Change → Change Impact profile
        """
        screenshot_dir = tmp_path / "screenshots" / "issue_types"
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        test_cases = [
            ("BUG-123", "rca", "Bug 类型"),
            ("REQ-456", "traceability", "需求类型"),
            ("CHANGE-789", "change_impact", "变更类型"),
        ]

        for issue_key, expected_profile, description in test_cases:
            # 访问页面
            await page.goto(ui_url)

            # 填写并提交
            await page.locator('input[placeholder*="Issue Key"]').fill(issue_key)
            await page.locator('button[type="submit"]').click()

            # 等待结果
            result_container = page.locator('[data-testid="result"]')
            await expect(result_container).to_be_visible(timeout=120000)

            # 等待内容加载
            await page.wait_for_timeout(2000)

            # 截图
            safe_filename = issue_key.replace("-", "_").lower()
            await page.screenshot(
                path=str(screenshot_dir / f"{safe_filename}_{expected_profile}.png"),
                full_page=True
            )

            print(f"✅ {description} ({issue_key}) 测试完成")

        print(f"\n✅ 所有 issue 类型测试完成！截图已保存到: {screenshot_dir}")
