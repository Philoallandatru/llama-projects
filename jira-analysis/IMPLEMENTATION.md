# Jira Analysis System - 实现总结

## 已完成的工作

### Phase 1: 核心组件（已完成）

1. **IssueLoader** (`src/core/issue_loader.py`)
   - 实时从 Jira API 拉取 issue 数据
   - 支持单个和批量加载
   - 使用异步方式提升性能
   - 支持通过 JQL 查询获取 issue keys

2. **Router** (`src/core/router.py`)
   - 根据 issue type 路由到对应的分析 profile
   - 支持配置文件驱动（`src/profiles/config.json`）
   - 提供默认 profile 机制
   - 大小写不敏感的路由匹配

3. **EvidenceRetriever** (`src/core/retriever.py`)
   - 从 LlamaIndex 向量索引中检索证据
   - 支持三类索引：Jira/Confluence/规格文档
   - 提供相似度搜索功能
   - 支持排除目标 issue 本身

4. **PromptBuilder** (`src/core/prompt_builder.py`)
   - 根据 profile 和 mode 构建完整 prompt
   - 支持三种分析模式：strict/balanced/exploratory
   - 格式化 issue 数据和证据
   - 加载和管理 prompt 模板

5. **LLMClient** (`src/core/llm_client.py`)
   - 封装本地 LLM 调用（Ollama/LM Studio）
   - 支持流式和非流式输出
   - 使用 LlamaIndex 的 OpenAILike 适配器

### Phase 2: Workflows（已完成）

1. **DeepAnalysisWorkflow** (`src/workflows/deep_analysis.py`)
   - 完整的单个 issue 深度分析流程
   - 6 个步骤：start → load_issue → route_profile → retrieve_evidence → generate_analysis → format_output
   - 支持流式输出和进度事件
   - 可配置是否检索证据

2. **BatchAnalysisWorkflow** (`src/workflows/batch_analysis.py`)
   - 批量分析多个 issues
   - 并发控制（使用 asyncio.Semaphore）
   - 自动生成汇总报告
   - 详细的进度跟踪

### Phase 3: 配置和部署（已完成）

1. **配置管理** (`src/settings.py`)
   - 使用 pydantic-settings 管理配置
   - 支持环境变量
   - 提供配置访问方法

2. **Profiles 配置** (`src/profiles/config.json`)
   - 定义了 4 个分析 profiles：
     - rca: 根因分析（Bug 类型）
     - traceability: 需求追溯（需求类型）
     - change_impact: 变更影响分析（变更类型）
     - general: 通用分析（默认）

3. **Prompt 模板** (`src/profiles/prompts/`)
   - rca.txt: 根因分析模板
   - traceability.txt: 需求追溯模板
   - change_impact.txt: 变更影响分析模板
   - general.txt: 通用分析模板

4. **部署配置** (`llama_deploy.yml`)
   - 配置了两个服务：deep-analysis 和 batch-analysis
   - 设置了控制平面端口和路由

5. **项目配置**
   - `pyproject.toml`: Python 项目配置
   - `.env.example`: 环境变量示例
   - `.gitignore`: Git 忽略规则
   - `README.md`: 项目文档

### Phase 4: 测试（已完成）

创建了基础测试文件：
- `tests/test_issue_loader.py`
- `tests/test_router.py`
- `tests/test_prompt_builder.py`

## 项目结构

```
jira-analysis/
├── src/
│   ├── workflows/
│   │   ├── __init__.py
│   │   ├── deep_analysis.py       # 深度分析 workflow
│   │   └── batch_analysis.py      # 批量分析 workflow
│   ├── core/
│   │   ├── __init__.py
│   │   ├── issue_loader.py        # Issue 加载器
│   │   ├── router.py              # 路由器
│   │   ├── retriever.py           # 证据检索器
│   │   ├── prompt_builder.py      # Prompt 构建器
│   │   └── llm_client.py          # LLM 客户端
│   ├── profiles/
│   │   ├── __init__.py
│   │   ├── config.json            # Profile 配置
│   │   └── prompts/               # Prompt 模板
│   │       ├── rca.txt
│   │       ├── traceability.txt
│   │       ├── change_impact.txt
│   │       └── general.txt
│   ├── __init__.py
│   └── settings.py                # 配置管理
├── tests/
│   ├── __init__.py
│   ├── test_issue_loader.py
│   ├── test_router.py
│   └── test_prompt_builder.py
├── ui/                            # TypeScript UI (待实现)
├── .env.example                   # 环境变量示例
├── .gitignore
├── llama_deploy.yml               # 部署配置
├── pyproject.toml                 # Python 项目配置
└── README.md                      # 项目文档
```

## 下一步工作

### Phase 5: UI 和集成（待实现）

1. **TypeScript UI**
   - 基于现有项目模板创建 UI
   - 实现单个 issue 分析界面
   - 实现批量分析界面
   - 显示进度和流式输出

2. **端到端测试**
   - 测试完整的分析流程
   - 测试批量分析
   - 测试错误处理

3. **文档完善**
   - API 使用文档
   - 部署指南
   - 故障排查指南

### 可选的增强功能

1. **Verification Workflow**（验证工作流）
   - 验证分析结果的准确性
   - 交叉验证证据

2. **Knowledge Extraction Workflow**（知识提取工作流）
   - 从历史 issues 中提取知识
   - 构建知识库

3. **增强的证据检索**
   - 使用 LLM 提取关键词增强查询
   - 支持更多证据源

4. **分析结果缓存**
   - 缓存已分析的 issues
   - 支持增量更新

## 使用示例

### 启动服务

```bash
# 1. 安装依赖
cd jira-analysis
uv sync

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写配置

# 3. 启动 LlamaDeploy API 服务器
uv run -m llama_deploy.apiserver

# 4. 部署工作流（新终端）
uv run llamactl deploy llama_deploy.yml
```

### API 调用

**单个 issue 分析**：

```bash
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_key\":\"NVME-777\",\"mode\":\"strict\"}",
    "service_id": "deep-analysis"
  }'
```

**批量分析**：

```bash
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_keys\":[\"NVME-777\",\"NVME-778\"],\"mode\":\"balanced\"}",
    "service_id": "batch-analysis"
  }'
```

## 技术亮点

1. **事件驱动架构**：使用 LlamaIndex Workflows 的事件驱动模式，清晰的步骤划分
2. **异步并发**：IssueLoader 和 BatchAnalysisWorkflow 使用异步方式提升性能
3. **配置驱动**：Profile 和 Prompt 模板通过配置文件管理，易于扩展
4. **流式输出**：支持流式生成，提供实时反馈
5. **模块化设计**：核心组件独立，易于测试和复用
6. **本地 LLM**：支持 Ollama/LM Studio，成本可控

## 总结

Jira Analysis System 的核心功能已经完整实现，包括：
- ✅ 5 个核心组件
- ✅ 2 个完整的 Workflows
- ✅ 4 个分析 Profiles 和 Prompt 模板
- ✅ 完整的配置和部署文件
- ✅ 基础测试框架

项目已经可以运行和使用，剩余的主要工作是 UI 开发和端到端测试。
