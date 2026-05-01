# LlamaIndex Workflows Projects

LlamaIndex 工作流项目 monorepo，使用 LlamaDeploy 部署 AI 应用。

## 项目列表

### 核心应用

- **[chat/](./chat/)** - RAG 聊天应用（带引用支持）
- **[deep-serach/](./deep-serach/)** - 多视角深度研究工作流
- **[data-explore/](./data-explore/)** - 多智能体财务报告生成器
- **[jira-analysis/](./jira-analysis/)** - Jira issue 深度分析系统（🚧 开发中）

### 基础设施

- **[datasource/](./datasource/)** - 统一数据源管理系统（✅ Phase 6 已完成）

## 技术栈

- **uv** - Python 包管理
- **LlamaIndex Workflows** - AI 智能体编排
- **LlamaDeploy** - 部署和服务
- **TypeScript** - UI 前端

## 快速开始

```bash
# 1. 进入项目目录
cd <project>/

# 2. 安装依赖
uv sync

# 3. 配置环境变量（src/.env）
# OPENAI_API_KEY=your_key

# 4. 生成索引
uv run generate

# 5. 启动服务（终端 1）
uv run -m llama_deploy.apiserver

# 6. 部署工作流（终端 2）
uv run llamactl deploy llama_deploy.yml

# 7. 访问 UI
# http://localhost:4501/deployments/<project-name>/ui
```

## 项目依赖关系

```
datasource/ → jira-analysis/ → chat/
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

## 开发指南

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

## 文档

- **项目指南**：[CLAUDE.md](./CLAUDE.md)
- **设计文档**：[.planning/](./.planning/)
- **各项目文档**：查看各子目录的 README.md

## 许可证

MIT
