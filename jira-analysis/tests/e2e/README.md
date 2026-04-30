# Jira Analysis E2E 测试指南

## 概述

本目录包含 jira-analysis 项目的端到端（E2E）测试，使用 Playwright 进行 UI 测试和 aiohttp 进行 API 测试。

## 测试结构

```
tests/e2e/
├── conftest.py                      # 测试配置和 fixtures
├── pytest.ini                       # Pytest 配置
├── test_ui_deep_analysis.py        # 深度分析 UI 测试
├── test_ui_batch_analysis.py       # 批量分析 UI 测试
├── test_api.py                     # API 测试
├── test_workflow_integration.py    # 工作流集成测试
└── README.md                       # 本文件
```

## 测试类型

### 1. UI 测试

**深度分析 UI** (`test_ui_deep_analysis.py`):
- 页面加载和基本元素
- 输入表单验证
- 分析模式选择
- 提交和结果显示
- 进度事件显示
- 响应式设计
- 键盘导航

**批量分析 UI** (`test_ui_batch_analysis.py`):
- 批量模式切换
- 批量输入格式
- 进度跟踪
- 结果汇总
- 导出功能
- 并发限制设置
- 错误处理

### 2. API 测试

**深度分析 API** (`test_api.py`):
- 创建分析任务
- 事件流获取
- 不同分析模式
- 错误处理

**批量分析 API** (`test_api.py`):
- 创建批量任务
- JQL 查询支持
- 并发限制
- 进度事件

### 3. 工作流集成测试

**深度分析工作流** (`test_workflow_integration.py`):
- 完整工作流执行
- Issue type 路由
- 证据检索

**批量分析工作流** (`test_workflow_integration.py`):
- 批量工作流完成
- 并发执行
- 错误处理

## 安装依赖

```bash
cd jira-analysis

# 安装测试依赖
uv add --dev playwright pytest-playwright aiohttp

# 安装 Playwright 浏览器
uv run playwright install chromium
```

## 运行测试

### 运行所有 E2E 测试

```bash
uv run pytest tests/e2e/ -v
```

### 运行特定类型的测试

```bash
# 只运行 UI 测试
uv run pytest tests/e2e/ -m ui -v

# 只运行 API 测试
uv run pytest tests/e2e/ -m api -v

# 只运行集成测试
uv run pytest tests/e2e/ -m integration -v

# 跳过慢速测试
uv run pytest tests/e2e/ -m "not slow" -v
```

### 运行特定测试文件

```bash
# 深度分析 UI 测试
uv run pytest tests/e2e/test_ui_deep_analysis.py -v

# 批量分析 UI 测试
uv run pytest tests/e2e/test_ui_batch_analysis.py -v

# API 测试
uv run pytest tests/e2e/test_api.py -v

# 工作流集成测试
uv run pytest tests/e2e/test_workflow_integration.py -v
```

### 运行特定测试

```bash
# 运行单个测试
uv run pytest tests/e2e/test_ui_deep_analysis.py::TestDeepAnalysisUI::test_page_loads -v

# 运行测试类
uv run pytest tests/e2e/test_ui_deep_analysis.py::TestDeepAnalysisUI -v
```

### 调试模式

```bash
# 显示浏览器窗口（非 headless 模式）
PWDEBUG=1 uv run pytest tests/e2e/test_ui_deep_analysis.py -v

# 慢速执行（便于观察）
uv run pytest tests/e2e/ -v --slowmo=1000

# 保存失败截图
uv run pytest tests/e2e/ -v --screenshot=only-on-failure
```

## 前置条件

### 1. 启动 LlamaDeploy 服务

测试会自动启动和停止服务，但如果需要手动控制：

```bash
# 终端 1: 启动 API 服务器
uv run -m llama_deploy.apiserver

# 终端 2: 部署工作流
uv run llamactl deploy llama_deploy.yml
```

### 2. 配置环境变量

确保 `.env` 文件配置正确：

```bash
# Jira 配置
JIRA_SERVER=https://jira.example.com
JIRA_EMAIL=user@example.com
JIRA_TOKEN=your_token

# LLM 配置
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b

# 索引路径
INDEX_BASE_PATH=../datasource/data/indexes
```

### 3. 生成测试索引

```bash
# 生成测试用的索引
uv run jira-index generate \
  --confluence-dir ./tests/fixtures/confluence \
  --spec-dir ./tests/fixtures/specs
```

## 测试标记（Markers）

- `@pytest.mark.e2e`: 端到端测试
- `@pytest.mark.slow`: 慢速测试（超过 30 秒）
- `@pytest.mark.ui`: UI 测试
- `@pytest.mark.api`: API 测试
- `@pytest.mark.integration`: 集成测试

## Fixtures

### 会话级 Fixtures

- `llama_deploy_process`: LlamaDeploy API 服务器进程
- `deployment_process`: 工作流部署进程
- `browser`: Playwright 浏览器实例

### 测试级 Fixtures

- `context`: 浏览器上下文
- `page`: 页面实例
- `base_url`: 基础 URL (http://localhost:4501)
- `ui_url`: UI URL
- `api_url`: API URL

## 测试数据

测试使用模拟的 Jira issues：

- `TEST-123`: 通用测试 issue
- `BUG-123`: Bug 类型 issue（应路由到 RCA profile）
- `REQ-456`: 需求类型 issue（应路由到 Traceability profile）
- `CHANGE-789`: 变更类型 issue（应路由到 Change Impact profile）

## 常见问题

### 1. 测试超时

如果测试超时，可以增加超时时间：

```python
await expect(element).to_be_visible(timeout=60000)  # 60 秒
```

### 2. 服务未启动

确保 LlamaDeploy 服务正常启动：

```bash
# 检查服务状态
curl http://localhost:4501/docs
```

### 3. 浏览器未安装

```bash
# 安装 Playwright 浏览器
uv run playwright install chromium
```

### 4. 端口冲突

如果端口 4501 被占用，修改 `llama_deploy.yml` 中的端口配置。

## 持续集成（CI）

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install dependencies
        run: |
          cd jira-analysis
          uv sync
          uv run playwright install chromium
      
      - name: Run E2E tests
        run: |
          cd jira-analysis
          uv run pytest tests/e2e/ -v --screenshot=only-on-failure
        env:
          JIRA_SERVER: ${{ secrets.JIRA_SERVER }}
          JIRA_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: tests/e2e/screenshots/
```

## 最佳实践

1. **独立性**: 每个测试应该独立运行，不依赖其他测试
2. **清理**: 使用 fixtures 确保测试后清理资源
3. **等待**: 使用 Playwright 的 `expect` 而不是 `time.sleep()`
4. **选择器**: 优先使用 `data-testid` 属性而不是 CSS 类名
5. **断言**: 使用清晰的断言消息
6. **超时**: 为长时间操作设置合理的超时时间
7. **并行**: 使用 `pytest-xdist` 并行运行测试（可选）

## 性能优化

### 并行执行

```bash
# 安装 pytest-xdist
uv add --dev pytest-xdist

# 并行运行测试
uv run pytest tests/e2e/ -n auto
```

### 复用浏览器

在 `conftest.py` 中使用 `scope="session"` 的 browser fixture 可以复用浏览器实例。

## 报告

### HTML 报告

```bash
# 安装 pytest-html
uv add --dev pytest-html

# 生成 HTML 报告
uv run pytest tests/e2e/ --html=report.html --self-contained-html
```

### 覆盖率报告

```bash
# 安装 pytest-cov
uv add --dev pytest-cov

# 生成覆盖率报告
uv run pytest tests/e2e/ --cov=src --cov-report=html
```

## 贡献指南

添加新测试时：

1. 遵循现有的测试结构和命名约定
2. 添加适当的测试标记
3. 更新本 README
4. 确保测试可以独立运行
5. 添加清晰的文档字符串

## 参考资源

- [Playwright Python 文档](https://playwright.dev/python/)
- [Pytest 文档](https://docs.pytest.org/)
- [LlamaDeploy 文档](https://docs.llamaindex.ai/en/stable/module_guides/llama_deploy/)
