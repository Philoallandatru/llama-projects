# LlamaIndex 内置数据连接方案

## 为什么应该使用 LlamaIndex 内置 Readers

LlamaIndex 提供了 **LlamaHub**，包含 100+ 种数据连接器：

### 1. 文件 Readers（已内置）
```python
from llama_index.core import SimpleDirectoryReader

# 自动识别多种格式
documents = SimpleDirectoryReader(
    "./data",
    file_extractor={
        ".pdf": PDFReader(),
        ".docx": DocxReader(),
        ".xlsx": PandasExcelReader(),
    }
).load_data()
```

### 2. 数据库 Readers
```python
from llama_index.readers.database import DatabaseReader

# 连接数据库
reader = DatabaseReader(
    sql_database=sql_database,
    query="SELECT * FROM users"
)
documents = reader.load_data()
```

### 3. API Readers
```python
# Jira
from llama_index.readers.jira import JiraReader
jira_reader = JiraReader(
    email="your-email@example.com",
    api_token="your-api-token",
    server_url="https://your-domain.atlassian.net"
)
documents = jira_reader.load_data(query="project=PROJ")

# Confluence
from llama_index.readers.confluence import ConfluenceReader
confluence_reader = ConfluenceReader(
    base_url="https://your-domain.atlassian.net/wiki",
    oauth2={"access_token": "your-token"}
)
documents = confluence_reader.load_data(space_key="SPACE")

# Notion
from llama_index.readers.notion import NotionPageReader
notion_reader = NotionPageReader(integration_token="your-token")
documents = notion_reader.load_data(page_ids=["page-id"])
```

### 4. 云存储 Readers
```python
# Google Drive
from llama_index.readers.google import GoogleDriveReader
drive_reader = GoogleDriveReader()
documents = drive_reader.load_data(folder_id="folder-id")

# AWS S3
from llama_index.readers.s3 import S3Reader
s3_reader = S3Reader(bucket="my-bucket")
documents = s3_reader.load_data(key="path/to/file")
```

## 推荐的实施方案

### 方案 A：完全使用 LlamaIndex Readers（推荐）

```python
# src/index.py
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.file import PDFReader, DocxReader, PandasExcelReader
from pathlib import Path

def get_documents():
    """使用 LlamaIndex 内置 Readers 加载文档"""
    
    # 配置文件提取器
    file_extractor = {
        ".pdf": PDFReader(),
        ".docx": DocxReader(),
        ".xlsx": PandasExcelReader(),
        ".pptx": PptxReader(),
    }
    
    # 加载文档
    data_path = Path(__file__).parent.parent / "data"
    documents = SimpleDirectoryReader(
        str(data_path),
        file_extractor=file_extractor,
        recursive=True
    ).load_data()
    
    return documents

def create_index():
    """创建索引"""
    from llama_index.core.settings import Settings
    
    documents = get_documents()
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=Settings.embed_model
    )
    
    # 持久化
    index.storage_context.persist(persist_dir="./storage")
    return index
```

### 方案 B：混合方案（自定义 + LlamaIndex）

如果你需要自定义的数据治理功能，可以：

```python
# 使用 LlamaIndex Readers 加载
from llama_index.core import SimpleDirectoryReader

# 加载为 LlamaIndex Documents
documents = SimpleDirectoryReader("./data").load_data()

# 应用自定义的数据治理
from shared.data_governance.quality import DataQualityChecker
from shared.data_governance.security import PIIFilter

quality_checker = DataQualityChecker()
pii_filter = PIIFilter()

# 过滤和验证
validated_docs = quality_checker.validate(documents)
safe_docs = pii_filter.filter(validated_docs)

# 创建索引
index = VectorStoreIndex.from_documents(safe_docs)
```

## 安装 LlamaIndex Readers

```bash
# 核心包（已安装）
pip install llama-index-core

# 文件 Readers
pip install llama-index-readers-file

# Jira & Confluence
pip install llama-index-readers-jira
pip install llama-index-readers-confluence

# Notion
pip install llama-index-readers-notion

# Google Drive
pip install llama-index-readers-google

# 数据库
pip install llama-index-readers-database
```

## 对比总结

| 特性 | 自定义方案 | LlamaIndex Readers |
|------|-----------|-------------------|
| 开发工作量 | 高（需要自己实现） | 低（开箱即用） |
| 维护成本 | 高 | 低（社区维护） |
| 功能完整性 | 需要自己实现 | 100+ 连接器 |
| 与 LlamaIndex 集成 | 需要转换 | 原生支持 |
| 数据治理 | 可自定义 | 需要额外实现 |
| 文档和社区 | 自己维护 | 官方文档完善 |

## 建议

1. **优先使用 LlamaIndex Readers** - 覆盖 90% 的场景
2. **保留自定义的数据治理层** - 用于质量检查、PII 过滤等
3. **简化共享层** - 只保留治理功能，不重复实现连接器

## 下一步

要不要我帮你：
1. 重构为使用 LlamaIndex Readers？
2. 保留数据治理层，删除重复的连接器和加载器？
3. 创建一个混合方案的示例？
