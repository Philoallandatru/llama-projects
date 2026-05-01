#!/bin/bash
# E2E 测试快速启动脚本

set -e

echo "🚀 Jira Analysis E2E 测试启动脚本"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在 jira-analysis 目录下运行此脚本"
    exit 1
fi

# 1. 安装依赖
echo ""
echo "📦 步骤 1/5: 安装依赖..."
uv sync --extra e2e

# 2. 安装 Playwright 浏览器
echo ""
echo "🌐 步骤 2/5: 安装 Playwright 浏览器..."
uv run playwright install chromium

# 3. 检查环境变量
echo ""
echo "🔍 步骤 3/5: 检查环境变量..."
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件填写正确的配置"
    exit 1
fi

# 4. 启动服务（后台）
echo ""
echo "🔧 步骤 4/5: 启动 LlamaDeploy 服务..."

# 检查端口是否被占用
if lsof -Pi :4501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 4501 已被占用，跳过服务启动"
else
    echo "启动 API 服务器..."
    uv run -m llama_deploy.apiserver > /tmp/llama_deploy.log 2>&1 &
    APISERVER_PID=$!

    echo "等待服务器启动..."
    sleep 5

    echo "部署工作流..."
    uv run llamactl deploy llama_deploy.yml > /tmp/llama_deploy_deploy.log 2>&1 &
    DEPLOY_PID=$!

    sleep 3

    echo "✅ 服务已启动 (API Server PID: $APISERVER_PID, Deploy PID: $DEPLOY_PID)"
fi

# 5. 运行测试
echo ""
echo "🧪 步骤 5/5: 运行 E2E 测试..."
echo ""

# 解析命令行参数
TEST_ARGS="$@"

if [ -z "$TEST_ARGS" ]; then
    # 默认运行所有测试
    uv run pytest tests/e2e/ -v
else
    # 运行指定的测试
    uv run pytest tests/e2e/ $TEST_ARGS
fi

TEST_EXIT_CODE=$?

# 清理
echo ""
echo "🧹 清理..."
if [ ! -z "$APISERVER_PID" ]; then
    kill $APISERVER_PID 2>/dev/null || true
fi
if [ ! -z "$DEPLOY_PID" ]; then
    kill $DEPLOY_PID 2>/dev/null || true
fi

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ 测试通过！"
else
    echo "❌ 测试失败"
    echo "查看日志: /tmp/llama_deploy.log"
fi

exit $TEST_EXIT_CODE
