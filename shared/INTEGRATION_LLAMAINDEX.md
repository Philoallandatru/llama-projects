# 集成指南 - 使用 LlamaIndex Readers

## 概述

本指南展示如何将共享层（使用 LlamaIndex Readers + 数据治理）集成到现有项目中。

## 架构

```
shared/
├── readers/                    # LlamaIndex Readers 管理
│   └── manager.py             # Reader 管理器
├── governance/                 # 数据治理（核心价值）
│   ├── quality.py             # 质量检查
│   └── security.py            # PII 过滤
├── config_llamaindex.py       # 配置
├── quick_start_llamaindex.py  # 快速开始
└── example_llamaindex.py      # 完整示例
```

## 步骤 1: 安装依赖

```bash
pip install -r shared/requirements_llamaindex.txt
```

## 步骤 2: 修改现有项目

### 修改 `src/index.py`

**原来的代码**：
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

def get_index():
    # ...

def create_index():
    documents = SimpleDirectoryReader("./data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index
```

**修改后的代码**（使用共享层）：
```python
import sys
from pathlib import Path

# 添加共享层到路径
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from readers.manager import ReaderManager
from governance.quality import DataQualityChecker
from governance.security import PIIFilter


def get_index():
    """获取已存在的索引"""
    index_path = Path(__file__).parent.parent / "storage"
    if index_path.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
        return load_index_from_storage(storage_context)
    return None


def create_index():
    """创建新索引（使用共享层）"""
    from llama_index.core.settings import Settings
    
    # 1. 使用 LlamaIndex Readers 加载文档
    manager = ReaderManager()
    data_path = Path(__file__).parent.parent / "data"
    documents = manager.load_from_directory(
        directory=str(data_path),
        recursive=True,
        required_exts=[".md", ".txt", ".pdf", ".docx", ".xlsx"]
    )
    
    # 2. 应用数据治理
    # 质量检查
    quality_checker = DataQualityChecker({
        "min_content_length": 50,
        "remove_duplicates": True
    })
    validated_docs, metrics = quality_checker.validate(documents)
    print(f"质量检查: {metrics.passed_docs}/{metrics.total_docs} 通过")
    
    # PII 过滤
    pii_filter = PIIFilter({
        "enabled_filters": ["email", "phone"],
        "redact_mode": "mask"
    })
    safe_docs = pii_filter.filter(validated_docs)
    
    # 丰富元数据
    enriched_docs = quality_checker.enrich_metadata(safe_docs)
    
    # 3. 创建索引
    index = VectorStoreIndex.from_documents(
        enriched_docs,
        embed_model=Settings.embed_model
    )
    
    # 4. 持久化
    index_path = Path(__file__).parent.parent / "storage"
    index.storage_context.persist(persist_dir=str(index_path))
    
    return index
```

### 修改 `src/generate.py`

**原来的代码**：
```python
from src.index import get_index
from src.settings import init_settings
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

def generate_index():
    init_settings()
    index = get_index()
    if index is None:
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir="./storage")
```

**修改后的代码**：
```python
from src.index import get_index, create_index
from src.settings import init_settings

def generate_index():
    """生成索引（使用共享层）"""
    init_settings()
    index = get_index()
    if index is None:
        print("创建新索引（使用 LlamaIndex Readers + 数据治理）...")
        index = create_index()
        print("索引创建完成！")
    else:
        print("索引已存在")
```

## 步骤 3: 测试

```bash
cd chat  # 或 deep-serach, data-explore
uv run generate
```

## 步骤 4: 添加 Jira/Confluence（可选）

### 修改 `src/index.py` 添加 Jira 支持

```python
def create_index_with_jira():
    """创建索引（包含 Jira 数据）"""
    import os
    from llama_index.core.settings import Settings
    
    manager = ReaderManager()
    all_documents = []
    
    # 1. 加载本地文件
    data_path = Path(__file__).parent.parent / "data"
    local_docs = manager.load_from_directory(str(data_path))
    all_documents.extend(local_docs)
    
    # 2. 加载 Jira（如果配置了）
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    if jira_email and jira_token:
        manager.setup_jira_reader(
            email=jira_email,
            api_token=jira_token,
            server_url="https://your-domain.atlassian.net"
        )
        jira_docs = manager.load_with_reader(
            "jira",
            query="project=PROJ AND updated >= -7d"
        )
        all_documents.extend(jira_docs)
        print(f"加载了 {len(jira_docs)} 个 Jira 问题")
    
    # 3. 应用数据治理
    quality_checker = DataQualityChecker()
    validated_docs, _ = quality_checker.validate(all_documents)
    
    pii_filter = PIIFilter()
    safe_docs = pii_filter.filter(validated_docs)
    
    # 4. 创建索引
    index = VectorStoreIndex.from_documents(
        safe_docs,
        embed_model=Settings.embed_model
    )
    
    index_path = Path(__file__).parent.parent / "storage"
    index.storage_context.persist(persist_dir=str(index_path))
    
    return index
```

### 配置环境变量

在 `src/.env` 中添加：
```bash
# Jira
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Confluence
CONFLUENCE_API_TOKEN=your-api-token
```

## 优势

使用 LlamaIndex Readers + 共享数据治理层后：

1. ✅ **减少维护** - 使用 LlamaIndex 社区维护的 Readers
2. ✅ **更多数据源** - 100+ 种现成的连接器
3. ✅ **数据治理** - 统一的质量检查和 PII 过滤
4. ✅ **易于扩展** - 轻松添加新数据源
5. ✅ **配置驱动** - 统一的配置管理

## 示例：完整的工作流

```python
# 1. 创建管理器
manager = ReaderManager()

# 2. 加载多个数据源
local_docs = manager.load_from_directory("./data")
jira_docs = manager.load_with_reader("jira", query="project=PROJ")
confluence_docs = manager.load_with_reader("confluence", space_key="SPACE")

all_docs = local_docs + jira_docs + confluence_docs

# 3. 应用数据治理
quality_checker = DataQualityChecker()
validated_docs, metrics = quality_checker.validate(all_docs)

pii_filter = PIIFilter()
safe_docs = pii_filter.filter(validated_docs)

# 4. 创建索引
index = VectorStoreIndex.from_documents(safe_docs)

# 5. 查询
query_engine = index.as_query_engine()
response = query_engine.query("你的问题")
```

## 下一步

1. 为其他两个项目（deep-serach, data-explore）应用相同的集成
2. 配置 Jira 和 Confluence 连接
3. 根据需要调整数据治理策略
4. 添加更多数据源（Notion, Google Drive 等）
