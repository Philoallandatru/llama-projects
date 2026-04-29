# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个包含三个 LlamaIndex 工作流项目的 monorepo，展示了使用 LlamaDeploy 的不同 AI 应用模式：

- **chat/**: 带引用支持的智能体 RAG 聊天应用
- **deep-serach/**: 多视角深度研究工作流，支持并行问答
- **data-explore/**: 多智能体财务报告生成器，集成代码解释器和文档生成

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

## 共享数据层

### 概述

`shared/` 目录包含统一的数据源处理和数据治理层，为所有项目提供可复用的数据接入能力。

### 支持的数据源

**文档格式**：
- Office: Excel (.xlsx, .xls), Word (.docx, .doc), PowerPoint (.pptx, .ppt)
- 文档: Markdown (.md), PDF (.pdf), 纯文本 (.txt)
- 图像: PNG (.png), JPEG (.jpg, .jpeg) - 使用 OCR 提取文本

**协作平台**（待实现）：
- Jira: 问题、项目、评论
- Confluence: 页面、空间、附件

### 核心组件

**Reader 管理器** (`shared/readers/manager.py`)：
- `ReaderManager`: 管理 LlamaIndex Readers
- `load_from_directory()`: 从目录加载文档
- `load_with_reader()`: 使用指定 Reader 加载
- `setup_jira_reader()`, `setup_confluence_reader()`: 配置 API Readers

**数据治理** (`shared/governance/`)：
- `DataQualityChecker`: 质量检查（长度、编码、去重）
- `PIIFilter`: PII 过滤（邮箱、电话、身份证等）
- `ContentFilter`: 内容过滤（不安全内容）

### 使用示例

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

### 集成到现有项目

详见 `shared/INTEGRATION_LLAMAINDEX.md`，主要步骤：

1. 安装依赖：`pip install -r shared/requirements_llamaindex.txt`
2. 修改 `src/index.py` 使用 `ReaderManager` 和数据治理
3. 修改 `src/generate.py` 使用新的索引创建逻辑
4. 运行 `uv run generate` 测试

### 依赖安装

**核心依赖**：
```bash
pip install llama-index-core llama-index-readers-file
```

**可选 Readers**：
```bash
# Jira & Confluence
pip install llama-index-readers-jira llama-index-readers-confluence

# Notion
pip install llama-index-readers-notion

# Google Drive
pip install llama-index-readers-google
```

### 添加新数据源

**添加 Jira**：
```python
manager = ReaderManager()
manager.setup_jira_reader(
    email="your-email@example.com",
    api_token="your-api-token",
    server_url="https://your-domain.atlassian.net"
)
jira_docs = manager.load_with_reader("jira", query="project=PROJ")
```

**添加 Confluence**：
```python
manager.setup_confluence_reader(
    base_url="https://your-domain.atlassian.net/wiki",
    api_token="your-api-token"
)
confluence_docs = manager.load_with_reader("confluence", space_key="SPACE")
```

### 配置

参见 `shared/config_llamaindex.py` 中的配置示例，包括：
- Reader 配置（文件系统、Jira、Confluence、Notion、Google Drive）
- 数据治理配置（质量检查、PII 过滤）
- 索引配置（向量索引、存储）
