# 共享数据层 - 重构完成（使用 LlamaIndex Readers）

## ✅ 重构完成

已成功重构为使用 **LlamaIndex 内置 Readers** + **自定义数据治理层**。

## 新架构

```
shared/
├── readers/                           # LlamaIndex Readers 管理
│   ├── __init__.py
│   └── manager.py                    # Reader 管理器
│
├── governance/                        # 数据治理（核心价值）
│   ├── __init__.py
│   ├── quality.py                    # 质量检查
│   └── security.py                   # PII 过滤
│
├── config_llamaindex.py              # 配置
├── quick_start_llamaindex.py         # 快速开始
├── example_llamaindex.py             # 完整示例
├── requirements_llamaindex.txt       # 依赖
└── INTEGRATION_LLAMAINDEX.md         # 集成指南
```

## 核心组件

### 1. Reader 管理器 (`readers/manager.py`)

```python
from readers.manager import ReaderManager

manager = ReaderManager()

# 加载本地文件（自动识别格式）
documents = manager.load_from_directory("./data")

# 配置 Jira
manager.setup_jira_reader(
    email="your-email@example.com",
    api_token="your-token",
    server_url="https://your-domain.atlassian.net"
)
jira_docs = manager.load_with_reader("jira", query="project=PROJ")

# 配置 Confluence
manager.setup_confluence_reader(
    base_url="https://your-domain.atlassian.net/wiki",
    api_token="your-token"
)
confluence_docs = manager.load_with_reader("confluence", space_key="SPACE")
```

### 2. 数据治理 (`governance/`)

**质量检查**：
```python
from governance.quality import DataQualityChecker

checker = DataQualityChecker({
    "min_content_length": 50,
    "remove_duplicates": True
})

validated_docs, metrics = checker.validate(documents)
print(f"通过率: {metrics.get_summary()['pass_rate']:.1%}")
```

**PII 过滤**：
```python
from governance.security import PIIFilter

pii_filter = PIIFilter({
    "enabled_filters": ["email", "phone", "id_card"],
    "redact_mode": "mask"
})

# 扫描
report = pii_filter.scan(documents)
print(f"包含 PII: {report['docs_with_pii']}/{report['total_docs']}")

# 过滤
safe_docs = pii_filter.filter(documents)
```

## 支持的数据源

### 文件格式（通过 LlamaIndex Readers）
- ✅ PDF, Word, Excel, PowerPoint
- ✅ Markdown, 纯文本
- ✅ 100+ 种其他格式

### API 数据源（通过 LlamaIndex Readers）
- ✅ Jira - 问题、项目、评论
- ✅ Confluence - 页面、空间、附件
- ✅ Notion - 页面、数据库
- ✅ Google Drive - 文档、表格
- ✅ 数据库 - PostgreSQL, MySQL 等

## 快速开始

### 1. 安装依赖

```bash
pip install -r shared/requirements_llamaindex.txt
```

### 2. 基础使用

```python
from llama_index.core import VectorStoreIndex
from readers.manager import ReaderManager
from governance.quality import DataQualityChecker
from governance.security import PIIFilter

# 加载文档
manager = ReaderManager()
documents = manager.load_from_directory("./data")

# 数据治理
quality_checker = DataQualityChecker()
validated_docs, _ = quality_checker.validate(documents)

pii_filter = PIIFilter()
safe_docs = pii_filter.filter(validated_docs)

# 创建索引
index = VectorStoreIndex.from_documents(safe_docs)
```

### 3. 集成到现有项目

详见 `INTEGRATION_LLAMAINDEX.md`

## 优势对比

| 特性 | 旧方案（自定义） | 新方案（LlamaIndex） |
|------|----------------|---------------------|
| 开发工作量 | 高 | 低 |
| 维护成本 | 高 | 低（社区维护） |
| 支持的数据源 | 7 种 | 100+ 种 |
| 与 LlamaIndex 集成 | 需要转换 | 原生支持 |
| 数据治理 | ✅ 自定义 | ✅ 保留 |
| 文档和社区 | 自己维护 | 官方文档 |

## 保留的价值

虽然使用 LlamaIndex Readers，但我们保留了：

1. ✅ **统一的 Reader 管理** - `ReaderManager` 简化配置
2. ✅ **数据质量检查** - 确保数据符合标准
3. ✅ **PII 过滤** - 保护敏感信息
4. ✅ **统一配置** - 跨项目的配置管理
5. ✅ **元数据丰富** - 自动添加质量指标

## 文件清单

### 核心代码
- ✅ `readers/manager.py` - Reader 管理器
- ✅ `governance/quality.py` - 质量检查
- ✅ `governance/security.py` - PII 过滤

### 配置和示例
- ✅ `config_llamaindex.py` - 配置示例
- ✅ `quick_start_llamaindex.py` - 快速开始
- ✅ `example_llamaindex.py` - 完整示例
- ✅ `requirements_llamaindex.txt` - 依赖

### 文档
- ✅ `INTEGRATION_LLAMAINDEX.md` - 集成指南
- ✅ `REFACTOR.md` - 重构说明
- ✅ `LLAMAINDEX_READERS.md` - LlamaIndex Readers 说明
- ✅ `CLAUDE.md` - 已更新

## 安装 LlamaIndex Readers

### 核心
```bash
pip install llama-index-core llama-index-readers-file
```

### Jira & Confluence
```bash
pip install llama-index-readers-jira llama-index-readers-confluence
```

### 其他
```bash
pip install llama-index-readers-notion      # Notion
pip install llama-index-readers-google      # Google Drive
pip install llama-index-readers-database    # 数据库
```

## 下一步

1. ✅ 重构完成
2. ⏳ 集成到 chat 项目
3. ⏳ 集成到 deep-serach 项目
4. ⏳ 集成到 data-explore 项目
5. ⏳ 配置 Jira 和 Confluence

## 总结

重构后的共享数据层：

- **更简单** - 使用 LlamaIndex 现成的 Readers
- **更强大** - 支持 100+ 种数据源
- **更易维护** - 社区维护，官方文档
- **保留价值** - 数据治理功能完整保留

**准备就绪，可以开始集成！** 🎉
