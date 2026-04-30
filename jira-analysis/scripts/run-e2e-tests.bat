@echo off
REM E2E 测试快速启动脚本 (Windows)

echo 🚀 Jira Analysis E2E 测试启动脚本
echo ==================================

REM 检查是否在正确的目录
if not exist "pyproject.toml" (
    echo ❌ 错误: 请在 jira-analysis 目录下运行此脚本
    exit /b 1
)

REM 1. 安装依赖
echo.
echo 📦 步骤 1/5: 安装依赖...
uv sync --extra e2e

REM 2. 安装 Playwright 浏览器
echo.
echo 🌐 步骤 2/5: 安装 Playwright 浏览器...
uv run playwright install chromium

REM 3. 检查环境变量
echo.
echo 🔍 步骤 3/5: 检查环境变量...
if not exist ".env" (
    echo ⚠️  警告: .env 文件不存在，从 .env.example 复制...
    copy .env.example .env
    echo ⚠️  请编辑 .env 文件填写正确的配置
    exit /b 1
)

REM 4. 启动服务（后台）
echo.
echo 🔧 步骤 4/5: 启动 LlamaDeploy 服务...

REM 检查端口是否被占用
netstat -ano | findstr :4501 | findstr LISTENING >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口 4501 已被占用，跳过服务启动
) else (
    echo 启动 API 服务器...
    start /B uv run -m llama_deploy.apiserver > llama_deploy.log 2>&1

    echo 等待服务器启动...
    timeout /t 5 /nobreak >nul

    echo 部署工作流...
    start /B uv run llamactl deploy llama_deploy.yml > llama_deploy_deploy.log 2>&1

    timeout /t 3 /nobreak >nul

    echo ✅ 服务已启动
)

REM 5. 运行测试
echo.
echo 🧪 步骤 5/5: 运行 E2E 测试...
echo.

if "%~1"=="" (
    REM 默认运行所有测试
    uv run pytest tests/e2e/ -v
) else (
    REM 运行指定的测试
    uv run pytest tests/e2e/ %*
)

set TEST_EXIT_CODE=%errorlevel%

REM 清理
echo.
echo 🧹 清理...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq llama_deploy*" >nul 2>&1

echo.
if %TEST_EXIT_CODE% equ 0 (
    echo ✅ 测试通过！
) else (
    echo ❌ 测试失败
    echo 查看日志: llama_deploy.log
)

exit /b %TEST_EXIT_CODE%
