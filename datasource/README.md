# DataSource - 统一数据源管理系统

> 为 LlamaIndex 项目提供统一的数据源管理、索引和检索能力

## 项目状态

🚧 **开发中** - Phase 1: 基础设施

## 功能特性

- ✅ 统一的数据源管理接口
- ✅ 支持多种数据源类型
  - 📁 本地文件（PDF、Word、Excel、Markdown）
  - 🎫 Jira Issues
  - 📚 Confluence Pages
- ✅ 混合检索（Vector + BM25）
- ✅ 简洁的 CLI 工具
- ✅ 与 LlamaIndex chat 项目无缝集成

## 快速开始

### 安装

```bash
cd datasource
pip install -r requirements.txt
```

### 基本使用

```bash
# 1. 添加数据源
ds add my_docs --type local --path ./data/documents

# 2. 同步数据（抓取 + 索引）
ds sync my_docs

# 3. 查询
ds query my_docs "如何解决 S4 黑屏问题？"

# 4. 查看所有数据源
ds list

# 5. 查看详情
ds show my_docs
```

## 项目结构

```
datasource/
├── core/                       # 核心模块
│   ├── models.py              # 数据模型
│   ├── paths.py               # 路径管理
│   ├── manager.py             # 数据源管理器
│   └── sources/               # 数据源实现
│       ├── base.py            # 基类
│       ├── local.py           # 本地文件
│       ├── jira.py            # Jira
│       └── confluence.py      # Confluence
├── cli.py                     # CLI 入口
├── requirements.txt           # 依赖
├── PLAN.md                    # 项目计划
├── PROGRESS.md                # 进度跟踪
└── tests/                     # 测试
    ├── test_models.py
    ├── test_paths.py
    └── integration/
```

## 开发指南

### 开发流程

1. 查看 `PLAN.md` 了解项目计划
2. 查看 `PROGRESS.md` 了解当前进度
3. 按 Phase 顺序开发
4. 每个 Phase 完成后进行代码审查
5. 更新 `PROGRESS.md`

### 代码审查

每个 Phase 完成后：

1. 使用 `REVIEW_TEMPLATE.md` 创建审查报告
2. 修复发现的问题
3. 重新运行测试
4. 提交代码

### 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_models.py -v

# 查看覆盖率
pytest tests/ --cov=datasource --cov-report=html
```

## 文档

- [项目计划](PLAN.md) - 详细的实施计划和验收标准
- [进度跟踪](PROGRESS.md) - 每日进度更新
- [问题跟踪](ISSUES.md) - 问题和 bug 跟踪
- [审查模板](REVIEW_TEMPLATE.md) - 代码审查模板

## 集成到 chat 项目

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

## 许可证

MIT

## 贡献

欢迎贡献！请先阅读 `PLAN.md` 了解项目结构。
