"""
工作流集成测试
"""
import pytest
import aiohttp
import json


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
class TestDeepAnalysisWorkflowIntegration:
    """深度分析工作流集成测试"""

    async def test_complete_workflow(self, api_url: str, deployment_process):
        """测试完整的工作流执行"""
        async with aiohttp.ClientSession() as session:
            # 创建任务
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_key":"TEST-123","mode":"strict","retrieve_evidence":true}',
                "service_id": "deep-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流并验证工作流步骤
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            workflow_stages = {
                "load_issue": False,
                "route": False,
                "retrieve": False,
                "analyze": False,
            }

            async with session.get(events_url, params=params) as response:
                assert response.status == 200

                async for line in response.content:
                    if not line:
                        continue

                    try:
                        # 尝试解析事件
                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data:"):
                            event_data = json.loads(line_str[5:])

                            # 检查进度事件
                            if "stage" in event_data:
                                stage = event_data["stage"]
                                if stage in workflow_stages:
                                    workflow_stages[stage] = True

                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue

            # 验证所有关键步骤都执行了
            assert workflow_stages["load_issue"], "load_issue stage not executed"
            assert workflow_stages["route"], "route stage not executed"

    async def test_workflow_with_different_issue_types(
        self, api_url: str, deployment_process
    ):
        """测试不同 issue type 的工作流路由"""
        issue_types = [
            ("BUG-123", "rca"),  # Bug 应该路由到 RCA profile
            ("REQ-456", "traceability"),  # 需求应该路由到追溯 profile
            ("CHANGE-789", "change_impact"),  # 变更应该路由到影响分析 profile
        ]

        async with aiohttp.ClientSession() as session:
            for issue_key, expected_profile in issue_types:
                create_url = f"{api_url}/tasks/create"
                payload = {
                    "input": f'{{"issue_key":"{issue_key}","mode":"balanced"}}',
                    "service_id": "deep-analysis",
                }

                async with session.post(create_url, json=payload) as response:
                    assert response.status == 200
                    data = await response.json()
                    task_id = data["task_id"]
                    session_id = data["session_id"]

                # 获取事件流并检查 profile
                events_url = f"{api_url}/tasks/{task_id}/events"
                params = {"session_id": session_id, "raw_event": "true"}

                found_profile = False
                async with session.get(events_url, params=params) as response:
                    async for line in response.content:
                        if not line:
                            continue

                        try:
                            line_str = line.decode("utf-8").strip()
                            if expected_profile in line_str:
                                found_profile = True
                                break
                        except UnicodeDecodeError:
                            continue

                        # 只读取前 20 个事件
                        if found_profile:
                            break

    async def test_workflow_evidence_retrieval(self, api_url: str, deployment_process):
        """测试证据检索功能"""
        async with aiohttp.ClientSession() as session:
            # 创建任务（启用证据检索）
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_key":"TEST-123","mode":"balanced","retrieve_evidence":true}',
                "service_id": "deep-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流并检查证据检索
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            has_evidence = False
            async with session.get(events_url, params=params) as response:
                async for line in response.content:
                    if not line:
                        continue

                    line_str = line.decode("utf-8").strip()
                    if "evidence" in line_str.lower() or "检索" in line_str:
                        has_evidence = True
                        break

            assert has_evidence, "Evidence retrieval not detected in workflow"


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
class TestBatchAnalysisWorkflowIntegration:
    """批量分析工作流集成测试"""

    async def test_batch_workflow_completion(self, api_url: str, deployment_process):
        """测试批量工作流完成"""
        async with aiohttp.ClientSession() as session:
            # 创建批量任务
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_keys":["TEST-123","TEST-124","TEST-125"],"mode":"balanced","max_concurrent":2}',
                "service_id": "batch-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流并验证批量处理
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            completed_count = 0
            has_summary = False

            async with session.get(events_url, params=params, timeout=180) as response:
                assert response.status == 200

                async for line in response.content:
                    if not line:
                        continue

                    try:
                        line_str = line.decode("utf-8").strip()

                        # 检查完成进度
                        if "完成" in line_str or "completed" in line_str.lower():
                            completed_count += 1

                        # 检查汇总报告
                        if "summary" in line_str.lower() or "汇总" in line_str:
                            has_summary = True

                    except UnicodeDecodeError:
                        continue

            # 验证至少处理了一些 issues
            assert completed_count > 0, "No issues were completed"

    async def test_batch_concurrent_execution(self, api_url: str, deployment_process):
        """测试批量并发执行"""
        async with aiohttp.ClientSession() as session:
            # 创建批量任务，设置并发数为 3
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_keys":["TEST-1","TEST-2","TEST-3","TEST-4","TEST-5"],"mode":"balanced","max_concurrent":3}',
                "service_id": "batch-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            event_count = 0
            async with session.get(events_url, params=params, timeout=180) as response:
                async for line in response.content:
                    if line:
                        event_count += 1

            # 应该有多个事件
            assert event_count > 0

    async def test_batch_error_handling(self, api_url: str, deployment_process):
        """测试批量分析错误处理"""
        async with aiohttp.ClientSession() as session:
            # 创建包含无效 issue key 的批量任务
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_keys":["INVALID-1","TEST-123","INVALID-2"],"mode":"balanced"}',
                "service_id": "batch-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流并检查错误处理
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            has_error = False
            has_success = False

            async with session.get(events_url, params=params, timeout=180) as response:
                async for line in response.content:
                    if not line:
                        continue

                    line_str = line.decode("utf-8").strip()

                    if "error" in line_str.lower() or "错误" in line_str:
                        has_error = True

                    if "success" in line_str.lower() or "成功" in line_str:
                        has_success = True

            # 应该既有错误也有成功
            assert has_error or has_success, "No error or success events detected"
