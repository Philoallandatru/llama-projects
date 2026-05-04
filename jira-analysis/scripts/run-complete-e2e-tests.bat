@echo off
REM 完整工作流 E2E 测试启动脚本 (Windows)

echo 🚀 启动 Jira Analysis 完整工作流 E2E 测试
echo ==========================================

REM 检查是否在正确的目录
if not exist "llama_deploy.yml" (
    echo ❌ 错误：请在 jira-analysis\ 目录下运行此脚本
    exit /b 1
)

REM 检查依赖
echo 📦 检查依赖...
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ 错误：未安装 uv
    echo    安装命令：powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    exit /b 1
)

REM 安装测试依赖
echo 📦 安装测试依赖...
call uv sync

REM 检查 Playwright 浏览器
echo 🌐 检查 Playwright 浏览器...
call uv run playwright --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 📥 安装 Playwright 浏览器...
    call uv run playwright install chromium
)

REM 检查环境变量
echo 🔍 检查环境配置...
if not exist "src\.env" (
    echo ⚠️  警告：未找到 src\.env 文件
    echo    请确保配置了 Jira 和 LLM 相关环境变量
)

REM 创建截图目录
set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%-%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set SCREENSHOT_DIR=test-screenshots-%TIMESTAMP%
mkdir "%SCREENSHOT_DIR%" 2>nul
echo 📸 截图将保存到: %SCREENSHOT_DIR%

REM 启动服务（后台）
echo.
echo 🔧 启动 LlamaDeploy 服务...
echo    这可能需要几分钟时间...

REM 检查端口是否被占用
netstat -ano | findstr ":4501" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ⚠️  警告：端口 4501 已被占用
    echo    如果服务已在运行，将使用现有服务
    set SERVICES_RUNNING=true
) else (
    set SERVICES_RUNNING=false

    REM 启动 API 服务器
    echo    启动 API 服务器...
    start /B cmd /c "uv run -m llama_deploy.apiserver > nul 2>&1"

    REM 等待 API 服务器启动
    echo    等待 API 服务器就绪...
    set /a RETRY=0
    :wait_api
    timeout /t 2 /nobreak >nul
    curl -s http://localhost:4501/docs >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo    ✅ API 服务器已就绪
        goto api_ready
    )
    set /a RETRY+=1
    if %RETRY% lss 30 goto wait_api
    echo    ❌ API 服务器启动超时
    taskkill /F /FI "WINDOWTITLE eq llama_deploy*" >nul 2>&1
    exit /b 1

    :api_ready

    REM 部署工作流
    echo    部署工作流...
    start /B cmd /c "uv run llamactl deploy llama_deploy.yml > nul 2>&1"

    REM 等待部署完成
    timeout /t 10 /nobreak >nul
)

REM 运行测试
echo.
echo 🧪 运行完整工作流 E2E 测试...
echo ==========================================

REM 运行测试
call uv run pytest tests/e2e/test_complete_workflow.py -v --tb=short --screenshot=only-on-failure --video=retain-on-failure -k test_complete_workflow

set TEST_RESULT=%ERRORLEVEL%

if %TEST_RESULT% equ 0 (
    echo.
    echo ✅ 所有测试通过！
) else (
    echo.
    echo ❌ 部分测试失败
)

REM 清理服务
if "%SERVICES_RUNNING%"=="false" (
    echo.
    echo 🧹 清理服务...
    taskkill /F /FI "WINDOWTITLE eq llama_deploy*" >nul 2>&1
    taskkill /F /FI "IMAGENAME eq python.exe" /FI "COMMANDLINE eq *llama_deploy*" >nul 2>&1
)

REM 显示截图位置
echo.
echo 📸 测试截图位置：
echo    临时目录: %TEMP%\pytest-of-%USERNAME%\pytest-current\
echo    失败截图: test-results\

REM 生成测试报告
echo.
echo 📊 生成测试报告...
if exist "test-results" (
    echo    测试结果已保存到: test-results\
)

echo.
echo ==========================================
if %TEST_RESULT% equ 0 (
    echo ✅ 测试完成！所有测试通过
) else (
    echo ⚠️  测试完成，但有失败的测试
    echo    请查看上面的错误信息和截图
)

exit /b %TEST_RESULT%
