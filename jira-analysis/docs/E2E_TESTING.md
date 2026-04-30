# E2E 测试

## 概述

jira-analysis 项目现在包含完整的端到端（E2E）测试套件，使用 Playwright 进行 UI 测试和 aiohttp 进行 API 测试。

## 测试覆盖

### UI 测试
- ✅ 深度分析界面（15+ 测试用例）
- ✅ 批量分析界面（10+ 测试用例）
- ✅ 响应式设计
- ✅ 键盘导航
- ✅ 表单验证

### API 测试
- ✅ 深度分析 API（5+ 测试用例）
- ✅ 批量分析 API（5+ 测试用例）
- ✅ 错误处理（5+ 测试用例）

### 工作流集成测试
- ✅ 完整工作流执行
- ✅ Issue type 路由
- ✅ 证据检索
- ✅ 批量并发处理

## 快速开始

### 1. 安装依赖

```bash
cd jira-analysis

# 安装测试依赖
uv sync --extra e2e

# 安装 Playwright 浏览器
uv run playwright install chromium
```

### 2. 配置环境

确保 `.env` 文件配置正确：

```bash
cp .env.example .env
# 编辑 .env 填写配置
```

### 3. 运行测试

**使用快速启动脚本（推荐）**：

```bash
# Linux/Mac
bash scripts/run-e2e-tests.sh

# Windows
scripts\run-e2e-tests.bat
```

**手动运行**：

```bash
# 运行所有测试
uv run pytest tests/e2e/ -v

# 只运行 UI 测试
uv run pytest tests/e2e/ -m ui -v

# 只运行 API 测试
uv run pytest tests/e2e/ -m api -v

# 运行特定测试文件
uv run pytest tests/e2e/test_ui_deep_analysis.py -v
```

## 测试结构

```
tests/e2e/
├── conftest.py                      # 测试配置和 fixtures
├── pytest.ini                       # Pytest 配置
├── test_ui_deep_analysis.py        # 深度分析 UI 测试（15 个测试）
├── test_ui_batch_analysis.py       # 批量分析 UI 测试（10 个测试）
├── test_api.py                     # API 测试（15 个测试）
├── test_workflow_integration.py    # 工作流集成测试（7 个测试）
└── README.md                       # 详细文档
```

## 测试统计

- **总测试数**: 47+
- **UI 测试**: 25+
- **API 测试**: 15+
- **集成测试**: 7+
- **覆盖率**: 目标 80%+

## 调试

### 显示浏览器窗口

```bash
PWDEBUG=1 uv run pytest tests/e2e/test_ui_deep_analysis.py -v
```

### 慢速执行

```bash
uv run pytest tests/e2e/ -v --slowmo=1000
```

### 保存失败截图

```bash
uv run pytest tests/e2e/ -v --screenshot=only-on-failure
```

## CI/CD 集成

项目包含 GitHub Actions 工作流（`.github/workflows/e2e-tests.yml`），会在以下情况自动运行测试：

- Push 到 main/develop 分支
- 创建 Pull Request
- 修改 jira-analysis 目录下的文件

测试结果会自动上传为 artifacts，失败时会保存截图和视频。

## 最佳实践

1. **独立性**: 每个测试独立运行，不依赖其他测试
2. **清理**: 使用 fixtures 自动清理资源
3. **等待**: 使用 Playwright 的 `expect` 而不是 `time.sleep()`
4. **选择器**: 优先使用 `data-testid` 属性
5. **超时**: 为长时间操作设置合理的超时时间

## 性能优化

### 并行执行

```bash
# 安装 pytest-xdist
uv add --dev pytest-xdist

# 并行运行测试
uv run pytest tests/e2e/ -n auto
```

### 复用浏览器

测试已配置为在会话级别复用浏览器实例，提升性能。

## 报告

### HTML 报告

```bash
uv run pytest tests/e2e/ --html=report.html --self-contained-html
```

### 覆盖率报告

```bash
uv run pytest tests/e2e/ --cov=src --cov-report=html
```

## 故障排查

### 服务未启动

```bash
# 检查服务状态
curl http://localhost:4501/docs
```

### 浏览器未安装

```bash
uv run playwright install chromium
```

### 端口冲突

修改 `llama_deploy.yml` 中的端口配置。

## 更多信息

详细文档请参见 `tests/e2e/README.md`。
