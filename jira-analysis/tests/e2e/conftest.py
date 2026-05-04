"""
E2E 测试配置和 fixtures
"""
import asyncio
import subprocess
import time
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """项目根目录"""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def llama_deploy_process(project_root: Path) -> Generator[subprocess.Popen, None, None]:
    """启动 LlamaDeploy API 服务器"""
    # 启动服务器
    process = subprocess.Popen(
        ["uv", "run", "-m", "llama_deploy.apiserver"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 等待服务器启动
    time.sleep(5)

    # 检查服务器是否启动成功
    import requests
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8100/docs")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            if i == max_retries - 1:
                process.kill()
                raise RuntimeError("LlamaDeploy server failed to start")
            time.sleep(2)

    yield process

    # 清理
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture(scope="session")
def deployment_process(
    project_root: Path, llama_deploy_process: subprocess.Popen
) -> Generator[subprocess.Popen, None, None]:
    """部署工作流"""
    # 等待 API 服务器完全启动
    time.sleep(2)

    # 部署工作流
    process = subprocess.Popen(
        ["uv", "run", "llamactl", "deploy", "llama_deploy.yml"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 等待部署完成
    time.sleep(5)

    yield process

    # 清理
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """创建浏览器实例"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """创建浏览器上下文"""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
    )
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """创建页面"""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """LlamaDeploy API 基础 URL"""
    return "http://localhost:8100"


@pytest.fixture(scope="session")
def ui_url() -> str:
    """UI URL (独立 Next.js 服务)"""
    return "http://localhost:3001"


@pytest.fixture
def api_url(base_url: str) -> str:
    """API URL"""
    return f"{base_url}/deployments/jira-analysis"
