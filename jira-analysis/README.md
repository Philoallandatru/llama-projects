# Jira Analysis System

基于 LlamaIndex Workflows 的 Jira issue 深度分析系统。

## 功能特性

- **实时交互分析**: 输入 issue key，实时生成深度分析报告
- **批量报告生成**: 支持批量分析多个 issues
- **智能路由**: 根据 issue type 自动选择分析 profile（RCA、需求追溯、变更影响等）
- **跨源证据检索**: 从 Jira/Confluence/规格文档索引中检索相关证据
- **多模式分析**: strict/balanced/exploratory 三种分析模式
- **本地 LLM**: 支持 Ollama/LM Studio 本地模型

## 快速开始

### 1. 安装依赖

```bash
cd jira-analysis
uv sync
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# Jira 配置
JIRA_SERVER=https://jira.example.com
JIRA_EMAIL=user@example.com
JIRA_TOKEN=your_token_here

# LLM 配置
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b

# 索引路径（指向已有的索引）
INDEX_BASE_PATH=../datasource/data/indexes
```

### 3. 启动服务

**启动 LlamaDeploy API 服务器**（终端 1）：

```bash
uv run -m llama_deploy.apiserver
```

**部署工作流**（终端 2）：

```bash
uv run llamactl deploy llama_deploy.yml
```

### 4. 访问 UI

打开浏览器访问：
- Deep Analysis: `http://localhost:4501/deployments/jira-analysis/ui`
- API 文档: `http://localhost:4501/docs`

## 使用示例

### 单个 Issue 分析

```bash
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_key\":\"NVME-777\",\"mode\":\"strict\"}",
    "service_id": "deep-analysis"
  }'
```

### 批量分析

```bash
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_keys\":[\"NVME-777\",\"NVME-778\"],\"mode\":\"balanced\"}",
    "service_id": "batch-analysis"
  }'
```

## 分析 Profiles

系统根据 issue type 自动选择分析 profile：

- **RCA (Root Cause Analysis)**: FW Bug, HW Bug, Test Bug
- **Traceability**: DAS/PRD, MRD
- **Change Impact**: Requirement Change, Component Change
- **General**: 其他类型

## 分析模式

- **strict**: 严格模式，只基于明确证据
- **balanced**: 平衡模式，允许合理推断
- **exploratory**: 探索模式，提出假设和可能性

## 项目结构

```
jira-analysis/
├── src/
│   ├── workflows/          # Workflow 定义
│   ├── core/              # 核心组件
│   ├── profiles/          # 分析 profiles 配置
│   └── settings.py        # 配置管理
├── ui/                    # TypeScript UI
├── tests/                 # 测试
└── llama_deploy.yml       # 部署配置
```

## 测试

### 单元测试

```bash
# 运行单元测试
uv run pytest tests/ -v

# 排除 E2E 测试
uv run pytest tests/ -v --ignore=tests/e2e/
```

### E2E 测试

项目包含完整的端到端测试套件，使用 Playwright 进行 UI 测试。

```bash
# 安装 E2E 测试依赖
uv sync --extra e2e
uv run playwright install chromium

# 运行所有 E2E 测试
uv run pytest tests/e2e/ -v

# 使用快速启动脚本（推荐）
bash scripts/run-e2e-tests.sh  # Linux/Mac
scripts\run-e2e-tests.bat      # Windows
```

详细信息请参见 [E2E 测试文档](docs/E2E_TESTING.md)。

## 开发

```bash
# 类型检查
uv run mypy src/

# 运行测试
uv run pytest

# 代码格式化
uv run ruff format src/
```

## License

MIT
