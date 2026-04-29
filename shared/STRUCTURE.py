"""
共享数据层 - 项目结构

这是一个统一的、可复用的、可迁移的数据源处理和数据治理层
"""

# 项目结构
"""
shared/
├── README.md                           # 架构设计文档
├── INTEGRATION.md                      # 集成指南
├── requirements.txt                    # 依赖列表
├── config.py                          # 配置文件
├── quick_start.py                     # 快速开始示例
├── example_usage.py                   # 完整使用示例
│
├── data-source/                       # 数据源处理层
│   ├── __init__.py
│   ├── manager.py                     # 数据源管理器（核心）
│   │
│   ├── schemas/                       # 数据模型
│   │   ├── __init__.py
│   │   └── models.py                  # UnifiedDocument, RawDocument 等
│   │
│   ├── connectors/                    # 数据源连接器
│   │   ├── __init__.py
│   │   ├── base.py                    # 基类：BaseConnector, FileSystemConnector, APIConnector
│   │   ├── filesystem.py              # 本地文件系统连接器
│   │   ├── jira.py                    # Jira 连接器（待实现）
│   │   └── confluence.py              # Confluence 连接器（待实现）
│   │
│   ├── loaders/                       # 数据加载器
│   │   ├── __init__.py
│   │   ├── base.py                    # 基类：BaseLoader, TextLoader, MarkdownLoader
│   │   └── documents.py               # 文档加载器：Excel, Word, PPT, PDF, Image
│   │
│   └── transformers/                  # 数据转换器（待实现）
│       └── __init__.py
│
├── data-governance/                   # 数据治理层（待实现）
│   ├── __init__.py
│   ├── quality/                       # 数据质量检查
│   ├── lineage/                       # 数据血缘追踪
│   ├── security/                      # 数据安全和权限
│   └── metadata/                      # 元数据管理
│
└── common/                            # 通用工具
    └── __init__.py
"""

# 核心组件说明

## 1. 数据模型 (schemas/models.py)
"""
- UnifiedDocument: 统一的文档模型，所有数据源转换为此格式
- RawDocument: 原始文档模型，从数据源获取的原始数据
- SourceType: 数据源类型枚举
- DocumentStatus: 文档状态枚举
- SyncResult: 同步结果模型
"""

## 2. 连接器 (connectors/)
"""
- BaseConnector: 所有连接器的基类
- FileSystemConnector: 文件系统连接器基类
- APIConnector: API 连接器基类（Jira, Confluence 等）
- LocalFileSystemConnector: 本地文件系统实现

支持的文件格式：
- Office: .xlsx, .xls, .docx, .doc, .pptx, .ppt
- 文档: .md, .pdf, .txt
- 图像: .png, .jpg, .jpeg
"""

## 3. 加载器 (loaders/)
"""
- BaseLoader: 所有加载器的基类
- TextLoader: 纯文本加载器
- MarkdownLoader: Markdown 加载器
- ExcelLoader: Excel 加载器（使用 pandas + openpyxl）
- WordLoader: Word 加载器（使用 python-docx）
- PowerPointLoader: PowerPoint 加载器（使用 python-pptx）
- PDFLoader: PDF 加载器（使用 pypdf）
- ImageLoader: 图像加载器（使用 pytesseract OCR）
"""

## 4. 数据源管理器 (manager.py)
"""
核心类：DataSourceManager

主要功能：
- register_connector(): 注册数据源连接器
- register_loader(): 注册数据加载器
- connect_all(): 连接所有数据源
- sync_source(): 同步单个数据源
- sync_all(): 同步所有数据源（支持并行）
- load_documents(): 加载原始文档为统一文档
- fetch_and_load(): 从数据源获取并加载文档
- get_sync_history(): 获取同步历史
- disconnect_all(): 断开所有连接
"""

# 使用流程

## 基本流程
"""
1. 创建 DataSourceManager
2. 注册加载器（TextLoader, ExcelLoader 等）
3. 注册连接器（LocalFileSystemConnector 等）
4. 连接数据源
5. 同步/获取数据
6. 加载为统一文档
7. 集成到 LlamaIndex 工作流
"""

## 示例代码
"""python
# 1. 创建管理器
manager = DataSourceManager()

# 2. 注册加载器
manager.register_loader(SourceType.EXCEL, ExcelLoader())
manager.register_loader(SourceType.PDF, PDFLoader())

# 3. 注册连接器
config = {'paths': ['./data'], 'file_types': ['.xlsx', '.pdf']}
connector = LocalFileSystemConnector(config)
manager.register_connector('docs', connector)

# 4. 连接并加载
await manager.connect_all()
documents = await manager.fetch_and_load('docs')

# 5. 转换为 LlamaIndex Document
from llama_index.core import Document
llama_docs = [
    Document(text=doc.content, metadata=doc.metadata)
    for doc in documents
]
"""

# 集成到现有项目

## 修改 src/index.py
"""
添加共享数据层的文档加载逻辑，替代 SimpleDirectoryReader
详见 INTEGRATION.md
"""

## 修改 src/generate.py
"""
使用共享数据层的 create_index() 函数
详见 INTEGRATION.md
"""

# 扩展指南

## 添加新的数据源连接器
"""
1. 继承 BaseConnector 或 APIConnector
2. 实现必需的抽象方法：
   - _get_source_type()
   - connect()
   - disconnect()
   - fetch()
   - sync()
3. 注册到 DataSourceManager
"""

## 添加新的加载器
"""
1. 继承 BaseLoader
2. 实现 load() 方法
3. 使用 _create_base_document() 创建统一文档
4. 注册到 DataSourceManager
"""

# 依赖安装

## 核心依赖
"""
pip install pydantic openpyxl pandas python-docx python-pptx pypdf
"""

## 可选依赖
"""
# OCR (图像文字识别)
pip install pytesseract Pillow

# Jira & Confluence
pip install atlassian-python-api

# 数据治理
pip install presidio-analyzer presidio-anonymizer
"""

# 配置

## 环境变量
"""
# Jira
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Confluence
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
"""

## 配置文件
"""
参见 config.py 中的配置示例
"""

# 下一步开发计划

## 短期
"""
1. 实现 Jira 连接器
2. 实现 Confluence 连接器
3. 添加数据质量检查
4. 添加数据安全过滤（PII）
"""

## 中期
"""
1. 实现数据血缘追踪
2. 实现元数据自动提取
3. 添加增量同步优化
4. 添加缓存机制
"""

## 长期
"""
1. 支持更多数据源（Notion, Google Drive 等）
2. 实现分布式索引
3. 添加数据版本控制
4. 构建数据治理仪表板
"""
