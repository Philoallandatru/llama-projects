# 集成指南

## 如何将共享数据层集成到现有项目

### 步骤 1: 安装依赖

在项目根目录运行：

```bash
pip install -r shared/requirements.txt
```

### 步骤 2: 修改现有项目的 `src/index.py`

**原来的代码**（以 chat 项目为例）：

```python
# chat/src/index.py
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from pathlib import Path

def get_index():
    index_path = Path(__file__).parent.parent / "storage"
    if index_path.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
        return load_index_from_storage(storage_context)
    return None
```

**修改后的代码**（使用共享数据层）：

```python
# chat/src/index.py
import sys
from pathlib import Path

# 添加共享层到 Python 路径
shared_path = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from llama_index.core import VectorStoreIndex, Document, StorageContext, load_index_from_storage
from shared.data_source.manager import DataSourceManager
from shared.data_source.connectors.filesystem import LocalFileSystemConnector
from shared.data_source.loaders.base import TextLoader, MarkdownLoader
from shared.data_source.loaders.documents import ExcelLoader, WordLoader, PDFLoader
from shared.data_source.schemas.models import SourceType
import asyncio

async def load_documents_from_shared():
    """使用共享数据层加载文档"""
    manager = DataSourceManager()
    
    # 注册加载器
    manager.register_loader(SourceType.TEXT, TextLoader())
    manager.register_loader(SourceType.MARKDOWN, MarkdownLoader())
    manager.register_loader(SourceType.EXCEL, ExcelLoader())
    manager.register_loader(SourceType.WORD, WordLoader())
    manager.register_loader(SourceType.PDF, PDFLoader())
    
    # 配置文件系统连接器
    config = {
        'paths': [str(Path(__file__).parent.parent / "data")],
        'file_types': ['.md', '.txt', '.pdf', '.docx', '.xlsx'],
        'recursive': True,
    }
    
    connector = LocalFileSystemConnector(config)
    manager.register_connector('docs', connector)
    
    # 连接并加载
    await manager.connect_all()
    unified_docs = await manager.fetch_and_load('docs')
    
    # 转换为 LlamaIndex Document
    llama_docs = [
        Document(
            text=doc.content,
            metadata={
                'title': doc.title,
                'source_type': doc.source_type.value,
                'source_id': doc.source_id,
                **doc.metadata
            }
        )
        for doc in unified_docs
    ]
    
    return llama_docs

def get_index():
    """获取或创建索引"""
    index_path = Path(__file__).parent.parent / "storage"
    
    # 如果索引已存在，直接加载
    if index_path.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
        return load_index_from_storage(storage_context)
    
    return None

def create_index():
    """创建新索引（使用共享数据层）"""
    from llama_index.core.settings import Settings
    
    # 使用共享数据层加载文档
    documents = asyncio.run(load_documents_from_shared())
    
    # 创建索引
    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=Settings.embed_model
    )
    
    # 持久化
    index_path = Path(__file__).parent.parent / "storage"
    index.storage_context.persist(persist_dir=str(index_path))
    
    return index
```

### 步骤 3: 修改 `src/generate.py`

**原来的代码**：

```python
# chat/src/generate.py
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
# chat/src/generate.py
from src.index import get_index, create_index
from src.settings import init_settings

def generate_index():
    """生成索引（使用共享数据层）"""
    init_settings()
    index = get_index()
    if index is None:
        print("创建新索引...")
        index = create_index()
        print("索引创建完成！")
    else:
        print("索引已存在")
```

### 步骤 4: 测试集成

```bash
cd chat
uv run generate
```

## 优势

使用共享数据层后，你将获得：

1. **统一的数据接入** - 所有项目使用相同的数据加载逻辑
2. **支持更多格式** - Excel, Word, PowerPoint, PDF, 图像等
3. **可扩展性** - 轻松添加新的数据源（Jira, Confluence 等）
4. **数据治理** - 内置数据质量检查、安全控制、血缘追踪
5. **可迁移性** - 配置驱动，易于在不同环境间迁移

## 下一步

1. 为其他两个项目（deep-serach, data-explore）应用相同的集成
2. 实现 Jira 和 Confluence 连接器
3. 添加数据治理功能
4. 配置统一的索引管理
