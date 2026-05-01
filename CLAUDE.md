# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个包含多个 LlamaIndex 工作流项目的 monorepo，展示了使用 LlamaDeploy 的不同 AI 应用模式：

### 核心项目

- **chat/**: 带引用支持的智能体 RAG 聊天应用
- **deep-serach/**: 多视角深度研究工作流，支持并行问答
- **data-explore/**: 多智能体财务报告生成器，集成代码解释器和文档生成
- **jira-analysis/**: Jira issue 深度分析系统，支持实时分析和批量报告生成（🚧 开发中）

### 基础设施项目

- **datasource/**: 统一数据源管理系统，支持 Jira、Confluence 和本地文件（✅ Phase 6 已完成）

所有项目使用：
- **uv** 进行 Python 包管理
- **LlamaIndex Workflows** 编排 AI 智能体
- **LlamaDeploy** 进行部署和服务
- **TypeScript UI**（在各项目的 `ui/` 目录中）作为前端

## 开发命令

### 初始设置

每个项目需要独立设置。首先进入项目目录：

```bash
cd chat/          # 或 deep-serach/ 或 data-explore/
uv sync           # 安装依赖
```

### 环境配置

每个项目的 `src/.env` 包含必需的 API 密钥：
- `OPENAI_API_KEY`: 所有项目必需
- `E2B_API_KEY`: 仅 data-explore 需要（代码解释器）
- `MODEL`: LLM 模型（默认: gpt-4.1）
- `EMBEDDING_MODEL`: 嵌入模型（默认: text-embedding-3-large）

在 `src/settings.py` 中配置 LLM 和嵌入模型。

### 生成索引

运行任何项目前，需要从 `./data` 中的文档生成嵌入：

```bash
uv run generate
```

这会创建 RAG 查询所需的向量索引。

### 运行项目

**启动 LlamaDeploy API 服务器**（在一个终端中）：

```bash
uv run -m llama_deploy.apiserver
# 运行在 http://0.0.0.0:4501
```

**部署工作流**（在另一个终端中）：

```bash
uv run llamactl deploy llama_deploy.yml
# 部署名称与项目匹配（chat、deep-serach 或 data-explore）
```

**访问 UI**：
- 导航到 `http://localhost:4501/deployments/<deployment-name>/ui`
- 示例：`http://localhost:4501/deployments/chat/ui`

**API 文档**：`http://localhost:4501/docs`

### 测试 API 端点

创建任务：

```bash
curl -X POST 'http://localhost:4501/deployments/chat/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"user_msg\":\"你好\",\"chat_history\":[]}",
    "service_id": "workflow"
  }'
```

流式事件（使用任务创建响应中的 task_id 和 session_id）：

```bash
curl 'http://localhost:4501/deployments/chat/tasks/<task_id>/events?session_id=<session_id>&raw_event=true' \
  -H 'Content-Type: application/json'
```

### 开发工具

```bash
# 类型检查
uv run mypy src/

# 运行测试
uv run pytest
```

## 架构

### 工作流模式

所有项目遵循 LlamaIndex Workflow 的事件驱动步骤模式：

1. **Workflow 类**继承 `Workflow` 并使用 `@step` 装饰器定义步骤
2. **Events**（继承 `Event`）触发步骤间的转换
3. **Context**（`ctx`）管理状态并向 UI 流式传输事件
4. **Memory** 在交互过程中维护聊天历史

### 项目特定架构

**chat/** - 简单智能体 RAG：
- 使用 `AgentWorkflow.from_tools_or_functions()` 的单智能体工作流
- 引用系统为查询响应包装源引用
- 文件：`workflow.py`、`citation.py`、`query.py`、`index.py`

**deep-serach/** - 多阶段研究工作流：
- **Retrieve（检索）**：从索引中获取相关文档
- **Analyze（分析）**：LLM 基于上下文生成研究问题
- **Answer（回答）**：并行工作器（num_workers=2）并发回答问题
- **Report（报告）**：将答案综合为全面的 markdown 报告
- 自定义 UI 事件（`UIEventData`）跟踪各阶段进度
- 文件：`workflow.py`（主逻辑）、`utils.py`（流式辅助函数）

**data-explore/** - 多智能体财务分析：
- **三个专业智能体**：
  - Researcher（研究员）：查询索引的财务文档
  - Analyst（分析师）：分析数据，可调用 E2B 代码解释器生成图表
  - Reporter（报告员）：生成 PDF/DOCX 报告
- **智能体协调**：工作流 LLM 通过函数调用决定调用哪个智能体
- **共享内存**：所有智能体访问 `ChatMemoryBuffer` 获取上下文
- 文件：`workflow.py`（编排）、`agent_tool.py`（工具调用）、`interpreter.py`（E2B 集成）、`document_generator.py`（报告生成）、`events.py`（自定义事件）

### 关键模式

**索引管理**：所有项目使用 `src/index.py` 中的 `get_index()` 加载向量存储。运行工作流前必须生成索引。

**设置初始化**：`src/settings.py` 中的 `init_settings()` 从环境变量配置 LLM 和嵌入模型。

**流式传输**：工作流通过 `ctx.write_event_to_stream()` 支持流式响应，实现实时 UI 更新。

**工具集成**：
- `QueryEngineTool`：包装向量索引检索器
- `FunctionTool`：包装自定义 Python 函数（代码解释器、文档生成器）
- 工具传递给 LLM 进行函数调用

### UI 自定义

每个项目的 `ui/index.ts` 用于 UI 配置：
- `starterQuestions`：预定义提示
- `componentsDir`：自定义事件组件
- `layoutDir`：自定义布局组件
- `llamaDeploy`：来自 `llama_deploy.yml` 的部署和工作流名称
- `llamaCloud`：可选的 LlamaCloud 集成

## 常见工作流程

**向 data-explore 添加新工具**：
1. 在新文件中创建工具函数（例如 `src/my_tool.py`）
2. 使用 `.to_tool()` 转换为 `FunctionTool`
3. 添加到 `FinancialReportWorkflow.__init__` 中的 `self.tools` 列表
4. 在 `handle_llm_input()` 的 match 语句中添加 case
5. 创建相应的事件类和步骤方法

**修改 deep-serach 中的研究问题**：
- 编辑 `src/workflow.py` 中的 `plan_research()` 函数
- 调整 `analyze_prompt` 模板以改变问题生成行为
- 修改 `total_questions` 阈值以控制研究深度

**更改 chat 中的引用格式**：
- 编辑 `src/citation.py` 中的 `CITATION_SYSTEM_PROMPT`
- 修改 `enable_citation()` 包装器以改变引用提取逻辑

## DataSource 项目（数据源管理系统）

### 概述

`datasource/` 是一个独立的 Python 包，提供统一的数据源管理和索引生成能力。

**当前状态**: Phase 6 已完成（增量同步、异步抓取、代码重构）  
**进度**: 75% (6/8 phases)  
**分支**: feature/phase6-refactoring

### 核心功能

1. **多数据源支持**
   - Local: 本地文件系统（Markdown, PDF, Office 文档等）
   - Jira Server: Issues, Comments, Projects
   - Confluence Server: Pages, Spaces, Attachments

2. **高级特性**（Phase 6）
   - ✅ 增量同步：基于 `lastModified` 时间戳
   - ✅ 异步抓取：5-10x 性能提升（基于 aiohttp）
   - ✅ HTML 清理：智能清理 Confluence/Jira HTML 内容
   - ✅ 通用工具层：Paginator, RetryHandler, AsyncHTTPClient

3. **数据治理**
   - 质量检查：长度验证、编码检测、去重
   - PII 过滤：邮箱、电话、身份证等敏感信息
   - 内容过滤：不安全内容检测

### 项目结构

```
datasource/
├── datasource/              # 主包（重构后）
│   ├── core/
│   │   ├── sources/        # 数据源实现
│   │   │   ├── base.py
│   │   │   ├── local.py
│   │   │   ├── jira.py
│   │   │   └── confluence.py
│   │   ├── indexing/       # 索引策略
│   │   │   ├── vector.py
│   │   │   ├── bm25.py
│   │   │   └── hybrid.py
│   │   ├── utils/          # 工具层（Phase 6 新增）
│   │   │   ├── async_http.py    # 异步 HTTP 客户端
│   │   │   ├── pagination.py    # 通用分页
│   │   │   ├── retry.py         # 重试和限流
│   │   │   └── html_cleaner.py  # HTML 清理
│   │   ├── manager.py      # 数据源管理器
│   │   ├── models.py       # 数据模型
│   │   └── paths.py        # 路径管理
│   └── cli.py              # 命令行接口
├── tests/                  # 180+ 测试用例
├── benchmarks/             # 性能基准测试
└── pyproject.toml
```

### 使用方式

**安装依赖**：
```bash
cd datasource/
uv sync
```

**配置环境变量**（`.env`）：
```bash
# Jira 配置
JIRA_SERVER=https://jira.example.com
JIRA_EMAIL=user@example.com
JIRA_TOKEN=your_token

# Confluence 配置
CONFLUENCE_SERVER=https://confluence.example.com
CONFLUENCE_EMAIL=user@example.com
CONFLUENCE_TOKEN=your_token
```

**命令行使用**：
```bash
# 同步数据源
uv run datasource sync local ./data
uv run datasource sync jira --project PROJ
uv run datasource sync confluence --space SPACE

# 生成索引
uv run datasource index local --strategy vector
uv run datasource index jira --strategy hybrid

# 查询索引
uv run datasource query "your question" --source local
```

**Python API 使用**：
```python
from datasource.core.manager import DataSourceManager
from datasource.core.indexing.vector import VectorIndexStrategy

# 创建管理器
manager = DataSourceManager(base_path="./data")

# 同步数据源
await manager.sync_source("jira", project="PROJ")

# 生成索引
strategy = VectorIndexStrategy()
index = await manager.create_index("jira", strategy)

# 查询
results = index.query("your question", top_k=5)
```

### 技术亮点

1. **增量同步**：只抓取更新的数据，速度提升 80-90%
2. **异步并发**：使用 aiohttp + Semaphore，100 个 issues 从 20s 降至 3-4s
3. **智能重试**：指数退避 + 429 限流处理
4. **通用抽象**：Paginator 和 RetryHandler 减少代码重复 30%

### 下一步计划

- **Phase 7**: 集成到 chat 项目
- **Phase 8**: 文档完善和性能优化

---

## 旧版共享数据层（已废弃）

`shared/` 目录包含早期的数据治理层原型，已被 `datasource/` 项目取代。

### 支持的数据源（旧版）

**文档格式**：
- Office: Excel (.xlsx, .xls), Word (.docx, .doc), PowerPoint (.pptx, .ppt)
- 文档: Markdown (.md), PDF (.pdf), 纯文本 (.txt)
- 图像: PNG (.png), JPEG (.jpg, .jpeg) - 使用 OCR 提取文本

**协作平台**（已在 datasource 中实现）：
- Jira: 问题、项目、评论
- Confluence: 页面、空间、附件

### 核心组件（旧版 - 已废弃）

**Reader 管理器** (`shared/readers/manager.py`)：
- `ReaderManager`: 管理 LlamaIndex Readers
- `load_from_directory()`: 从目录加载文档
- `load_with_reader()`: 使用指定 Reader 加载
- `setup_jira_reader()`, `setup_confluence_reader()`: 配置 API Readers

**数据治理** (`shared/governance/`)：
- `DataQualityChecker`: 质量检查（长度、编码、去重）
- `PIIFilter`: PII 过滤（邮箱、电话、身份证等）
- `ContentFilter`: 内容过滤（不安全内容）

**注意**: 新项目应使用 `datasource/` 包，而不是 `shared/` 目录。

---

## Jira Analysis 项目（Jira 深度分析系统）

### 概述

`jira-analysis/` 是一个独立的 LlamaIndex Workflow 项目，提供 Jira issue 深度分析服务。

**当前状态**: 🚧 开发中（Phase 1 核心组件实现）  
**设计文档**: `.planning/jira-analysis-design.md`

### 核心功能

1. **实时交互分析**：用户输入 issue key，实时拉取并分析
2. **批量报告生成**：分析一批 issues，生成汇总报告
3. **Issue 类型路由**：根据 issue type 选择分析 profile（RCA、需求追溯、变更影响等）
4. **跨源证据检索**：从 Jira、Confluence 和规格文档索引中检索相关证据
5. **多模式分析**：strict/balanced/exploratory 三种分析模式
6. **结构化输出**：生成 markdown 格式的分析报告

### 项目结构

```
jira-analysis/
├── src/
│   ├── workflows/
│   │   ├── deep_analysis.py          # 深度分析 workflow
│   │   └── batch_analysis.py         # 批量分析 workflow
│   ├── core/
│   │   ├── issue_loader.py           # 实时加载 Jira issue
│   │   ├── router.py                 # Issue type 路由
│   │   ├── retriever.py              # 跨源证据检索
│   │   ├── prompt_builder.py         # Prompt 构建
│   │   └── llm_client.py             # LLM 调用封装
│   ├── profiles/
│   │   ├── config.json               # Issue type → profile 映射
│   │   └── prompts/                  # Prompt 模板
│   │       ├── rca.txt               # 根因分析
│   │       ├── traceability.txt      # 需求追溯
│   │       ├── change_impact.txt     # 变更影响
│   │       └── general.txt           # 通用分析
│   ├── settings.py                   # 配置管理
│   └── .env                          # 环境变量
├── ui/                               # TypeScript UI
├── tests/                            # 测试用例
├── llama_deploy.yml                  # 部署配置
└── README.md
```

### 技术特点

1. **实时数据拉取**：分析目标 issue 实时从 Jira API 拉取，确保数据最新
2. **索引检索证据**：相似 issues 和文档从预建索引中检索，提升性能
3. **配置驱动**：通过 `profiles/config.json` 配置 issue type 路由规则
4. **本地 LLM**：支持 Ollama/LM Studio，成本可控
5. **流式输出**：支持流式生成，实时 UI 反馈

### 使用方式

**安装依赖**：
```bash
cd jira-analysis/
uv sync
```

**配置环境变量**（`.env`）：
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

**生成索引**（依赖 datasource）：
```bash
# 先在 datasource 项目中生成索引
cd ../datasource/
uv run datasource sync jira --project PROJ
uv run datasource index jira --strategy vector

# 索引会保存在 datasource/data/indexes/jira/
```

**启动服务**：
```bash
# 启动 LlamaDeploy API 服务器
uv run -m llama_deploy.apiserver

# 部署工作流
uv run llamactl deploy llama_deploy.yml

# 访问 UI
# http://localhost:4501/deployments/jira-analysis/ui
```

**API 使用**：
```bash
# 深度分析单个 issue
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_key\":\"NVME-777\",\"mode\":\"strict\"}",
    "service_id": "deep-analysis"
  }'

# 批量分析
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_keys\":[\"NVME-777\",\"NVME-778\"],\"mode\":\"strict\"}",
    "service_id": "batch-analysis"
  }'
```

### 分析 Profiles

**RCA（根因分析）**：
- 适用于：FW Bug, HW Bug, Test Bug
- 输出：失效机制、触发条件、根本原因、证据链、建议

**Traceability（需求追溯）**：
- 适用于：DAS/PRD, MRD
- 输出：需求覆盖、实现状态、差距分析、建议

**Change Impact（变更影响）**：
- 适用于：Requirement Change, Component Change
- 输出：影响范围、风险评估、依赖分析、建议

**General（通用分析）**：
- 适用于：其他所有 issue types
- 输出：问题概述、相关证据、分析结论、建议

### 工作流程

**DeepAnalysisWorkflow**（深度分析）：
1. **Load Issue**: 实时从 Jira API 拉取 issue 数据
2. **Route Profile**: 根据 issue type 选择分析 profile
3. **Retrieve Evidence**: 从索引中检索相似 issues 和相关文档
4. **Generate Analysis**: 调用 LLM 生成分析报告（支持流式输出）
5. **Format Output**: 格式化输出结果

**BatchAnalysisWorkflow**（批量分析）：
1. **Start**: 接收 issue keys 列表或 JQL 查询
2. **Batch Analyze**: 并发分析多个 issues（控制并发数）
3. **Generate Summary**: 生成汇总报告

### 实现计划

- ✅ **Phase 1**: 核心组件（IssueLoader, Router, Retriever, PromptBuilder, LLMClient）
- 🚧 **Phase 2**: Deep Analysis Workflow
- ⏳ **Phase 3**: Batch Analysis Workflow
- ⏳ **Phase 4**: 配置和部署
- ⏳ **Phase 5**: UI 和测试

---

## 旧版共享数据层（已废弃）

`shared/` 目录包含早期的数据治理层原型，已被 `datasource/` 项目取代。

### 使用示例（旧版 - 已废弃）

```python
from llama_index.core import VectorStoreIndex
from readers.manager import ReaderManager
from governance.quality import DataQualityChecker
from governance.security import PIIFilter

# 1. 创建 Reader 管理器
manager = ReaderManager()

# 2. 加载文档（自动识别格式）
documents = manager.load_from_directory(
    directory="./data",
    recursive=True
)

# 3. 应用数据治理
# 质量检查
quality_checker = DataQualityChecker()
validated_docs, metrics = quality_checker.validate(documents)

# PII 过滤
pii_filter = PIIFilter()
safe_docs = pii_filter.filter(validated_docs)

# 4. 创建索引
index = VectorStoreIndex.from_documents(safe_docs)
```

**注意**: 新项目应使用 `datasource/` 包的 API，参见上面的 DataSource 项目章节。

---

## 开发指南

### 项目间依赖关系

```
datasource/  (基础设施)
    ↓
jira-analysis/  (依赖 datasource 生成的索引)
    ↓
chat/  (未来将集成 datasource 和 jira-analysis)
```

### 添加新项目

1. 在根目录创建项目文件夹
2. 使用 `uv init` 初始化项目
3. 添加 `llama_deploy.yml` 配置
4. 实现 Workflow 类
5. 添加 UI（可选）
6. 更新本文档

### 代码规范

- 使用 `uv` 管理依赖
- 使用 `mypy` 进行类型检查
- 使用 `pytest` 编写测试
- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写文档字符串

### 测试策略

- 单元测试：测试独立组件
- 集成测试：测试 Workflow 流程
- 端到端测试：测试完整的 API 调用
- 性能测试：使用 `benchmarks/` 目录

### Git 工作流

- 主分支：`main`
- 功能分支：`feature/<feature-name>`
- 修复分支：`fix/<bug-name>`
- 提交前运行测试：`uv run pytest`
- 提交信息格式：`<type>: <description>`
  - `feat`: 新功能
  - `fix`: 修复
  - `docs`: 文档
  - `refactor`: 重构
  - `test`: 测试
  - `chore`: 构建/工具

---

## 常见问题

### Q: 如何选择使用哪个项目？

- **需要数据源管理**：使用 `datasource/`
- **需要 Jira 分析**：使用 `jira-analysis/`（依赖 datasource）
- **需要通用 RAG 聊天**：使用 `chat/`
- **需要深度研究**：使用 `deep-serach/`
- **需要财务分析**：使用 `data-explore/`

### Q: datasource 和 shared 有什么区别？

- `datasource/`：新的、完整的数据源管理系统，支持增量同步、异步抓取等高级特性
- `shared/`：早期原型，已废弃，新项目不应使用

### Q: jira-analysis 和 datasource 的关系？

- `datasource/`：负责数据同步和索引生成
- `jira-analysis/`：负责分析逻辑，使用 datasource 生成的索引

### Q: 如何使用本地 LLM？

在项目的 `.env` 文件中配置：
```bash
LLM_BASE_URL=http://localhost:11434/v1  # Ollama
LLM_MODEL=qwen2.5:14b
```

支持的本地 LLM 服务：
- Ollama: `http://localhost:11434/v1`
- LM Studio: `http://localhost:1234/v1`

### Q: 如何调试 Workflow？

1. 查看日志：Workflow 会输出详细日志
2. 使用 `ctx.write_event_to_stream()` 输出调试信息
3. 在 UI 中查看事件流
4. 使用 `pytest` 运行单元测试

### Q: 如何提升性能？

1. **使用增量同步**：只同步更新的数据
2. **启用异步抓取**：并发处理多个请求
3. **调整索引策略**：根据数据规模选择合适的索引类型
4. **控制并发数**：避免压垮 API 服务器
5. **使用缓存**：缓存频繁访问的数据

---

## 更新日志

### 2026-04-30
- ✅ 完成 datasource Phase 6（增量同步、异步抓取、代码重构）
- 🚧 开始 jira-analysis Phase 1（核心组件实现）
- 📝 更新 CLAUDE.md，反映当前项目状态

### 2026-04-29
- ✅ 实现 datasource HTML 清理功能
- ✅ 添加 180+ 测试用例

### 2026-04-28
- ✅ 实现 datasource 增量同步
- ✅ 提取通用工具层（Paginator, RetryHandler）

---

## 联系和支持

- **文档**: 各项目的 README.md 和 docs/ 目录
- **问题跟踪**: 使用 Git issues
- **设计文档**: `.planning/` 目录
