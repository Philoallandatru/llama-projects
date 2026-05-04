# Jira Analysis System

Jira issue 深度分析系统，基于 LlamaIndex Workflows。

## 项目状态

✅ **Phase 4 已完成** | **进度**: 80% (4/5)

- ✅ Phase 1: 核心组件
- ✅ Phase 2: Deep Analysis Workflow
- ✅ Phase 3: Batch Analysis Workflow
- ✅ Phase 4: E2E Testing and Validation
- ⏳ Phase 5: UI Optimization and Deployment

## 功能特性

1. **实时交互分析**：输入 issue key，实时拉取并分析
2. **批量报告生成**：分析多个 issues，生成汇总报告
3. **Issue 类型路由**：根据 issue type 选择分析 profile（RCA、需求追溯、变更影响等）
4. **跨源证据检索**：从 Jira、Confluence 和规格文档索引中检索证据
5. **多模式分析**：strict/balanced/exploratory 三种模式
6. **本地 LLM 支持**：支持 Ollama/LM Studio

## 快速开始

### 1. 安装依赖

```bash
cd jira-analysis/
uv sync
```

### 2. 配置环境变量

创建 `src/.env` 文件：

```bash
# Jira 配置
JIRA_SERVER=https://jira.example.com
JIRA_EMAIL=user@example.com
JIRA_TOKEN=your_token

# LLM 配置（本地模型）
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096

# 索引路径（指向 datasource 生成的索引）
INDEX_BASE_PATH=../datasource/data/indexes
```

### 3. 生成索引（依赖 datasource）

```bash
# 先在 datasource 项目中生成索引
cd ../datasource/
uv run datasource sync jira --project PROJ
uv run datasource index jira --strategy vector

# 索引会保存在 datasource/data/indexes/jira/
```

### 4. 启动服务

```bash
cd ../jira-analysis/

# 启动 LlamaDeploy API 服务器（终端 1）
# 默认端口: 8100 (如果被占用，可在 llama_deploy.yml 中修改)
uv run -m llama_deploy.apiserver

# 部署工作流（终端 2）
uv run llamactl deploy llama_deploy.yml

# 启动 UI（终端 3）
# 默认端口: 3000 (如果被占用，使用 npm run dev -- -p 3001)
cd ui-next/
npm run dev

# 访问 UI
# http://localhost:3000
```

## 使用示例

### 深度分析单个 issue

```bash
curl -X POST 'http://localhost:8100/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_key\":\"NVME-777\",\"mode\":\"balanced\"}",
    "service_id": "deep-analysis"
  }'
```

### 批量分析

```bash
# 使用 issue keys 列表
curl -X POST 'http://localhost:8100/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_keys\":[\"NVME-777\",\"NVME-778\"],\"mode\":\"balanced\",\"max_concurrent\":3}",
    "service_id": "batch-analysis"
  }'

# 使用 JQL 查询
curl -X POST 'http://localhost:8100/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"jql\":\"project=NVME AND created>=2024-01-01\",\"mode\":\"balanced\"}",
    "service_id": "batch-analysis"
  }'
```

## 分析 Profiles

系统根据 issue type 自动选择分析 profile：

- **RCA（根因分析）**：FW Bug, HW Bug, Test Bug → 失效机制、根本原因、证据链
- **Traceability（需求追溯）**：DAS/PRD, MRD → 需求覆盖、实现状态、差距分析
- **Change Impact（变更影响）**：变更类 → 影响范围、风险评估、依赖分析
- **General（通用分析）**：其他类型 → 问题概述、相关证据、分析结论

配置文件：`src/profiles/config.json`

## 分析模式

- **strict**: 严格模式，只基于明确证据
- **balanced**: 平衡模式，允许合理推断（默认）
- **exploratory**: 探索模式，提出假设和可能性

## 项目结构

```
jira-analysis/
├── src/
│   ├── workflows/
│   │   ├── deep_analysis.py          # ✅ 深度分析 workflow
│   │   └── batch_analysis.py         # ✅ 批量分析 workflow
│   ├── core/
│   │   ├── issue_loader.py           # ✅ 实时加载 Jira issue
│   │   ├── router.py                 # ✅ Issue type 路由
│   │   ├── retriever.py              # ✅ 跨源证据检索
│   │   ├── prompt_builder.py         # ✅ Prompt 构建
│   │   └── llm_client.py             # ✅ LLM 调用封装
│   ├── profiles/
│   │   ├── config.json               # ✅ Issue type → profile 映射
│   │   └── prompts/                  # ✅ Prompt 模板
│   │       ├── rca.txt
│   │       ├── traceability.txt
│   │       ├── change_impact.txt
│   │       └── general.txt
│   └── settings.py                   # ✅ 配置管理
├── ui-next/                          # ✅ Next.js UI (已完成)
├── tests/                            # ✅ 测试用例
├── llama_deploy.yml                  # ✅ 部署配置
└── README.md
```

## 工作流程

### DeepAnalysisWorkflow（深度分析）✅

1. **Load Issue**: 实时从 Jira API 拉取 issue 数据
2. **Route Profile**: 根据 issue type 选择分析 profile
3. **Retrieve Evidence**: 从索引中检索相似 issues 和相关文档
4. **Generate Analysis**: 调用 LLM 生成分析报告（支持流式输出）
5. **Format Output**: 格式化输出结果
6. **Save Knowledge**: 保存到知识库

### BatchAnalysisWorkflow（批量分析）⏳

1. **Start**: 接收 issue keys 列表或 JQL 查询
2. **Batch Analyze**: 并发分析多个 issues（控制并发数）
3. **Generate Summary**: 生成汇总报告

## 测试

### 单元测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_deep_analysis_workflow.py -v

# 排除 E2E 测试
uv run pytest tests/ -v --ignore=tests/e2e/
```

### E2E 测试

```bash
# 安装 E2E 测试依赖
uv sync --extra e2e
uv run playwright install chromium

# 运行 E2E 测试
uv run pytest tests/e2e/ -v
```

详细信息请参见 [E2E 测试文档](docs/E2E_TESTING.md)。

## 开发

```bash
# 类型检查
uv run mypy src/

# 代码格式化
uv run ruff format src/
```

## 技术特点

1. **实时数据拉取**：分析目标 issue 实时从 Jira API 拉取，确保数据最新
2. **索引检索证据**：相似 issues 和文档从预建索引中检索，提升性能
3. **配置驱动**：通过 `profiles/config.json` 配置 issue type 路由规则
4. **流式输出**：支持流式生成，实时 UI 反馈
5. **事件驱动**：基于 LlamaIndex Workflow 的事件驱动架构

## 文档

- [PHASE2_COMPLETE.md](PHASE2_COMPLETE.md) - Phase 2 完成总结
- [PHASE3_COMPLETE.md](PHASE3_COMPLETE.md) - Phase 3 完成总结
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - 项目总体概述
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - 实现细节
- [USAGE.md](USAGE.md) - 使用指南
- [LOCAL_TEST.md](LOCAL_TEST.md) - 本地测试指南

## 许可证

MIT
