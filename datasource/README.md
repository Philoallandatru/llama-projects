# DataSource - 统一数据源管理系统

统一数据源管理和索引生成系统，为 LlamaIndex 项目提供数据基础设施。

## 项目状态

✅ **Phase 6 已完成** - 增量同步、异步抓取、代码重构  
**进度**: 75% (6/8 phases)

## 功能特性

### 多数据源支持
- 📁 **Local**: 本地文件系统（Markdown, PDF, Office 文档等）
- 🎫 **Jira Server**: Issues, Comments, Projects
- 📚 **Confluence Server**: Pages, Spaces, Attachments

### 高级特性（Phase 6）
- ✅ **增量同步**：基于 `lastModified` 时间戳，速度提升 80-90%
- ✅ **异步抓取**：5-10x 性能提升（基于 aiohttp）
- ✅ **HTML 清理**：智能清理 Confluence/Jira HTML 内容
- ✅ **通用工具层**：Paginator, RetryHandler, AsyncHTTPClient

### 数据治理
- 质量检查：长度验证、编码检测、去重
- PII 过滤：邮箱、电话、身份证等敏感信息
- 内容过滤：不安全内容检测

## 快速开始

### 安装

```bash
cd datasource/
uv sync
```

### 配置环境变量

创建 `.env` 文件：

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

### 命令行使用

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

### Python API 使用

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

## 项目结构

```
datasource/
├── datasource/              # 主包
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
│   │   ├── utils/          # 工具层（Phase 6）
│   │   │   ├── async_http.py
│   │   │   ├── pagination.py
│   │   │   ├── retry.py
│   │   │   └── html_cleaner.py
│   │   ├── manager.py
│   │   ├── models.py
│   │   └── paths.py
│   └── cli.py
├── tests/                  # 180+ 测试用例
├── benchmarks/             # 性能基准测试
└── pyproject.toml
```

## 技术亮点

1. **增量同步**：只抓取更新的数据，速度提升 80-90%
2. **异步并发**：使用 aiohttp + Semaphore，100 个 issues 从 20s 降至 3-4s
3. **智能重试**：指数退避 + 429 限流处理
4. **通用抽象**：Paginator 和 RetryHandler 减少代码重复 30%

## 集成到其他项目

### 在 jira-analysis 中使用

```bash
# 1. 在 datasource 中生成索引
cd datasource/
uv run datasource sync jira --project PROJ
uv run datasource index jira --strategy vector

# 2. 在 jira-analysis 中配置索引路径
# .env: INDEX_BASE_PATH=../datasource/data/indexes
```

### 在 chat 中使用

```python
from datasource.core.manager import DataSourceManager

# 初始化
manager = DataSourceManager()

# 获取 QueryEngine
query_engine = manager.get_query_engine("my_docs")

# 在 Agent 中使用
from llama_index.core.tools import QueryEngineTool

tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="query_my_docs",
    description="查询我的文档"
)
```

## 开发指南

### 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定测试
uv run pytest tests/test_models.py -v

# 查看覆盖率
uv run pytest --cov=datasource --cov-report=html
```

### 性能基准测试

```bash
cd benchmarks/
uv run python benchmark_sync.py
uv run python benchmark_async.py
```

## 下一步计划

- **Phase 7**: 集成到 chat 项目
- **Phase 8**: 文档完善和性能优化

## 文档

- [项目计划](PLAN.md) - 详细的实施计划
- [进度跟踪](PROGRESS.md) - 开发进度
- [问题跟踪](ISSUES.md) - 问题和 bug 跟踪

## 许可证

MIT
