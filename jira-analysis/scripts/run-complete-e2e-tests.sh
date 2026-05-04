#!/bin/bash
# 完整工作流 E2E 测试启动脚本

set -e

echo "🚀 启动 Jira Analysis 完整工作流 E2E 测试"
echo "=========================================="

# 检查是否在正确的目录
if [ ! -f "llama_deploy.yml" ]; then
    echo "❌ 错误：请在 jira-analysis/ 目录下运行此脚本"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! command -v uv &> /dev/null; then
    echo "❌ 错误：未安装 uv"
    echo "   安装命令：curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 安装测试依赖
echo "📦 安装测试依赖..."
uv sync

# 检查 Playwright 浏览器
echo "🌐 检查 Playwright 浏览器..."
if ! uv run playwright --version &> /dev/null; then
    echo "📥 安装 Playwright 浏览器..."
    uv run playwright install chromium
fi

# 检查环境变量
echo "🔍 检查环境配置..."
if [ ! -f "src/.env" ]; then
    echo "⚠️  警告：未找到 src/.env 文件"
    echo "   请确保配置了 Jira 和 LLM 相关环境变量"
fi

# 创建截图目录
SCREENSHOT_DIR="test-screenshots-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SCREENSHOT_DIR"
echo "📸 截图将保存到: $SCREENSHOT_DIR"

# 启动服务（后台）
echo ""
echo "🔧 启动 LlamaDeploy 服务..."
echo "   这可能需要几分钟时间..."

# 检查端口是否被占用
if lsof -Pi :4501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  警告：端口 4501 已被占用"
    echo "   如果服务已在运行，将使用现有服务"
    SERVICES_RUNNING=true
else
    SERVICES_RUNNING=false

    # 启动 API 服务器
    echo "   启动 API 服务器..."
    uv run -m llama_deploy.apiserver > /dev/null 2>&1 &
    API_SERVER_PID=$!

    # 等待 API 服务器启动
    echo "   等待 API 服务器就绪..."
    for i in {1..30}; do
        if curl -s http://localhost:4501/docs > /dev/null 2>&1; then
            echo "   ✅ API 服务器已就绪"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "   ❌ API 服务器启动超时"
            kill $API_SERVER_PID 2>/dev/null || true
            exit 1
        fi
        sleep 2
    done

    # 部署工作流
    echo "   部署工作流..."
    uv run llamactl deploy llama_deploy.yml > /dev/null 2>&1 &
    DEPLOY_PID=$!

    # 等待部署完成
    sleep 10
fi

# 运行测试
echo ""
echo "🧪 运行完整工作流 E2E 测试..."
echo "=========================================="

# 设置测试选项
TEST_OPTIONS=(
    "-v"                                    # 详细输出
    "--tb=short"                           # 简短的错误追踪
    "--screenshot=only-on-failure"         # 失败时截图
    "--video=retain-on-failure"            # 失败时保留视频
    "-k test_complete_workflow"            # 只运行完整工作流测试
)

# 运行测试
if uv run pytest tests/e2e/test_complete_workflow.py "${TEST_OPTIONS[@]}"; then
    echo ""
    echo "✅ 所有测试通过！"
    TEST_RESULT=0
else
    echo ""
    echo "❌ 部分测试失败"
    TEST_RESULT=1
fi

# 清理服务
if [ "$SERVICES_RUNNING" = false ]; then
    echo ""
    echo "🧹 清理服务..."
    if [ ! -z "$API_SERVER_PID" ]; then
        kill $API_SERVER_PID 2>/dev/null || true
    fi
    if [ ! -z "$DEPLOY_PID" ]; then
        kill $DEPLOY_PID 2>/dev/null || true
    fi

    # 清理可能残留的进程
    pkill -f "llama_deploy.apiserver" 2>/dev/null || true
    pkill -f "llamactl" 2>/dev/null || true
fi

# 显示截图位置
echo ""
echo "📸 测试截图位置："
echo "   临时目录: /tmp/pytest-of-$USER/pytest-current/"
echo "   失败截图: test-results/"

# 生成测试报告
echo ""
echo "📊 生成测试报告..."
if [ -d "test-results" ]; then
    echo "   测试结果已保存到: test-results/"
fi

echo ""
echo "=========================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ 测试完成！所有测试通过"
else
    echo "⚠️  测试完成，但有失败的测试"
    echo "   请查看上面的错误信息和截图"
fi

exit $TEST_RESULT
