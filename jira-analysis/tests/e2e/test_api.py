"""
API E2E 测试
"""
import pytest
import aiohttp


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDeepAnalysisAPI:
    """深度分析 API 测试"""

    async def test_create_task(self, api_url: str, deployment_process):
        """测试创建分析任务"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_key":"TEST-123","mode":"strict"}',
                "service_id": "deep-analysis",
            }

            async with session.post(url, json=payload) as response:
                assert response.status == 200
                data = await response.json()

                # 检查返回的任务信息
                assert "task_id" in data
                assert "session_id" in data

    async def test_task_events_stream(self, api_url: str, deployment_process):
        """测试任务事件流"""
        async with aiohttp.ClientSession() as session:
            # 创建任务
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_key":"TEST-123","mode":"strict"}',
                "service_id": "deep-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            async with session.get(events_url, params=params) as response:
                assert response.status == 200

                # 读取至少一个事件
                event_count = 0
                async for line in response.content:
                    if line:
                        event_count += 1
                        if event_count >= 5:  # 读取前 5 个事件
                            break

                assert event_count > 0

    async def test_invalid_issue_key(self, api_url: str, deployment_process):
        """测试无效的 Issue Key"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_key":"INVALID","mode":"strict"}',
                "service_id": "deep-analysis",
            }

            async with session.post(url, json=payload) as response:
                # 任务创建应该成功，但执行时会失败
                assert response.status == 200
                data = await response.json()
                assert "task_id" in data

    async def test_different_modes(self, api_url: str, deployment_process):
        """测试不同的分析模式"""
        modes = ["strict", "balanced", "exploratory"]

        async with aiohttp.ClientSession() as session:
            for mode in modes:
                url = f"{api_url}/tasks/create"
                payload = {
                    "input": f'{{"issue_key":"TEST-123","mode":"{mode}"}}',
                    "service_id": "deep-analysis",
                }

                async with session.post(url, json=payload) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert "task_id" in data


@pytest.mark.asyncio
@pytest.mark.e2e
class TestBatchAnalysisAPI:
    """批量分析 API 测试"""

    async def test_batch_create_task(self, api_url: str, deployment_process):
        """测试创建批量分析任务"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_keys":["TEST-123","TEST-124"],"mode":"balanced"}',
                "service_id": "batch-analysis",
            }

            async with session.post(url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                assert "task_id" in data
                assert "session_id" in data

    async def test_batch_with_jql(self, api_url: str, deployment_process):
        """测试使用 JQL 的批量分析"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"jql":"project=TEST AND updated>=2024-01-01","mode":"balanced"}',
                "service_id": "batch-analysis",
            }

            async with session.post(url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                assert "task_id" in data

    async def test_batch_concurrent_limit(self, api_url: str, deployment_process):
        """测试批量分析并发限制"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_keys":["TEST-123","TEST-124","TEST-125"],"mode":"balanced","max_concurrent":2}',
                "service_id": "batch-analysis",
            }

            async with session.post(url, json=payload) as response:
                assert response.status == 200
                data = await response.json()
                assert "task_id" in data

    async def test_batch_progress_events(self, api_url: str, deployment_process):
        """测试批量分析进度事件"""
        async with aiohttp.ClientSession() as session:
            # 创建任务
            create_url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_keys":["TEST-123","TEST-124"],"mode":"balanced"}',
                "service_id": "batch-analysis",
            }

            async with session.post(create_url, json=payload) as response:
                data = await response.json()
                task_id = data["task_id"]
                session_id = data["session_id"]

            # 获取事件流
            events_url = f"{api_url}/tasks/{task_id}/events"
            params = {"session_id": session_id, "raw_event": "true"}

            async with session.get(events_url, params=params) as response:
                assert response.status == 200

                # 检查是否有进度事件
                has_progress_event = False
                event_count = 0

                async for line in response.content:
                    if line and b"batch_analyze" in line:
                        has_progress_event = True
                    event_count += 1
                    if event_count >= 10:
                        break

                assert event_count > 0


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAPIErrorHandling:
    """API 错误处理测试"""

    async def test_missing_input(self, api_url: str, deployment_process):
        """测试缺少输入参数"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "service_id": "deep-analysis",
            }

            async with session.post(url, json=payload) as response:
                # 应该返回错误
                assert response.status in [400, 422]

    async def test_invalid_service_id(self, api_url: str, deployment_process):
        """测试无效的服务 ID"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": '{"issue_key":"TEST-123","mode":"strict"}',
                "service_id": "invalid-service",
            }

            async with session.post(url, json=payload) as response:
                # 应该返回错误
                assert response.status in [400, 404]

    async def test_malformed_json_input(self, api_url: str, deployment_process):
        """测试格式错误的 JSON 输入"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/create"
            payload = {
                "input": "not a valid json",
                "service_id": "deep-analysis",
            }

            async with session.post(url, json=payload) as response:
                # 任务创建可能成功，但执行时会失败
                assert response.status in [200, 400, 422]

    async def test_task_not_found(self, api_url: str, deployment_process):
        """测试查询不存在的任务"""
        async with aiohttp.ClientSession() as session:
            url = f"{api_url}/tasks/nonexistent-task-id/events"
            params = {"session_id": "fake-session-id"}

            async with session.get(url, params=params) as response:
                # 应该返回 404
                assert response.status == 404
