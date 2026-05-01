# CLAUDE.md

本文件为 Claude Code 在此代码库中工作时提供指导。

## 项目概述

LlamaIndex 工作流项目 monorepo，使用 LlamaDeploy 部署 AI 应用。

### 项目列表

**核心应用**：
- **chat/**: RAG 聊天应用（带引用支持）
- **deep-serach/**: 多视角深度研究工作流
- **data-explore/**: 多智能体财务报告生成器
- **jira-analysis/**: Jira issue 深度分析系统（🚧 开发中）

**基础设施**：
- **datasource/**: 统一数据源管理系统（✅ Phase 6 已完成）

**技术栈**：uv + LlamaIndex Workflows + LlamaDeploy + TypeScript UI

## 快速开始

### 初始设置

```bash
cd <project>/        # 进入项目目录
uv sync              # 安装依赖
```

### 环境配置

在 `src/.env` 中配置：
- `OPENAI_API_KEY`: 必需
- `E2B_API_KEY`: data-explore 需要
- `MODEL`: LLM 模型（默认: gpt-4.1）
- `EMBEDDING_MODEL`: 嵌入模型（默认: text-embedding-3-large）

### 运行项目

```bash
# 1. 生成索引
uv run generate

# 2. 启动 API 服务器（终端 1）
uv run -m llama_deploy.apiserver

# 3. 部署工作流（终端 2）
uv run llamactl deploy llama_deploy.yml

# 4. 访问 UI
# http://localhost:4501/deployments/<project-name>/ui
```

## 架构概览

### 工作流模式

LlamaIndex Workflow 事件驱动架构：
- **Workflow 类**：继承 `Workflow`，使用 `@step` 装饰器
- **Events**：继承 `Event`，触发步骤转换
- **Context**：管理状态，流式传输到 UI
- **Memory**：维护聊天历史

### 关键组件

- **索引管理**：`src/index.py` 中的 `get_index()` 加载向量存储
- **设置初始化**：`src/settings.py` 中的 `init_settings()` 配置 LLM
- **流式传输**：`ctx.write_event_to_stream()` 实现实时 UI 更新
- **工具集成**：`QueryEngineTool`（索引检索）、`FunctionTool`（自定义函数）

## DataSource 项目

统一数据源管理和索引生成系统。

**状态**: Phase 6 已完成 | **进度**: 75% (6/8)

### 核心功能

1. **多数据源**：Local（文件系统）、Jira Server、Confluence Server
2. **高级特性**：增量同步、异步抓取（5-10x 性能提升）、HTML 清理
3. **数据治理**：质量检查、PII 过滤、内容过滤

### 使用方式

```bash
cd datasource/
uv sync

# 同步数据源
uv run datasource sync local ./data
uv run datasource sync jira --project PROJ

# 生成索引
uv run datasource index local --strategy vector

# 查询
uv run datasource query "your question" --source local
```

### Python API

```python
from datasource.core.manager import DataSourceManager
from datasource.core.indexing.vector import VectorIndexStrategy

manager = DataSourceManager(base_path="./data")
await manager.sync_source("jira", project="PROJ")

strategy = VectorIndexStrategy()
index = await manager.create_index("jira", strategy)
results = index.query("your question", top_k=5)
```

### 技术亮点

- 增量同步：速度提升 80-90%
- 异步并发：100 个 issues 从 20s 降至 3-4s
- 智能重试：指数退避 + 429 限流处理

---

## Jira Analysis 项目

Jira issue 深度分析系统。

**状态**: 🚧 Phase 1 开发中 | **设计文档**: `.planning/jira-analysis-design.md`

### 核心功能

1. **实时交互分析**：输入 issue key，实时拉取并分析
2. **批量报告生成**：分析多个 issues，生成汇总报告
3. **Issue 类型路由**：根据 issue type 选择分析 profile（RCA、需求追溯、变更影响等）
4. **跨源证据检索**：从 Jira、Confluence 和规格文档索引中检索证据
5. **多模式分析**：strict/balanced/exploratory 三种模式

### 使用方式

```bash
cd jira-analysis/
uv sync

# 配置 .env（Jira 配置 + LLM 配置 + 索引路径）

# 生成索引（依赖 datasource）
cd ../datasource/
uv run datasource sync jira --project PROJ
uv run datasource index jira --strategy vector

# 启动服务
cd ../jira-analysis/
uv run -m llama_deploy.apiserver
uv run llamactl deploy llama_deploy.yml
```

### 分析 Profiles

- **RCA**：FW/HW/Test Bug → 失效机制、根本原因、证据链
- **Traceability**：DAS/PRD/MRD → 需求覆盖、实现状态、差距分析
- **Change Impact**：变更类 → 影响范围、风险评估、依赖分析
- **General**：其他类型 → 问题概述、相关证据、分析结论

### 实现计划

- ✅ Phase 1: 核心组件
- 🚧 Phase 2: Deep Analysis Workflow
- ⏳ Phase 3: Batch Analysis Workflow
- ⏳ Phase 4: 配置和部署
- ⏳ Phase 5: UI 和测试

---

## 开发指南

### 项目依赖关系

```
datasource/ → jira-analysis/ → chat/
```

### 代码规范

- 使用 `uv` 管理依赖
- 使用 `mypy` 类型检查
- 使用 `pytest` 编写测试
- 遵循 PEP 8 代码风格

### Git 工作流

- 主分支：`main`
- 功能分支：`feature/<name>`
- 修复分支：`fix/<name>`
- 提交格式：`<type>: <description>`（feat/fix/docs/refactor/test/chore）

---

## 常见问题

**Q: 如何选择项目？**
- 数据源管理 → `datasource/`
- Jira 分析 → `jira-analysis/`
- RAG 聊天 → `chat/`
- 深度研究 → `deep-serach/`
- 财务分析 → `data-explore/`

**Q: jira-analysis 和 datasource 的关系？**
- `datasource/`：数据同步和索引生成
- `jira-analysis/`：分析逻辑，使用 datasource 生成的索引

**Q: 如何使用本地 LLM？**
```bash
# .env 配置
LLM_BASE_URL=http://localhost:11434/v1  # Ollama
LLM_MODEL=qwen2.5:14b
```

**Q: 如何提升性能？**
- 使用增量同步
- 启用异步抓取
- 调整索引策略
- 控制并发数
- 使用缓存

---

## 更新日志

### 2026-05-01
- 📝 精简 CLAUDE.md，删除废弃内容

### 2026-04-30
- ✅ 完成 datasource Phase 6
- 🚧 开始 jira-analysis Phase 1

---

## 联系和支持

- **文档**: 各项目 README.md 和 docs/
- **设计文档**: `.planning/` 目录
