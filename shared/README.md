# 共享数据层架构

统一的数据源处理和数据治理层，为所有 LlamaIndex 项目提供可复用的数据接入能力。

## 架构概述

```
shared/
├── data-source/           # 数据源处理层
│   ├── connectors/       # 数据源连接器（Jira、Confluence、文件系统等）
│   ├── loaders/          # 数据加载器（统一的加载接口）
│   ├── transformers/     # 数据转换器（格式标准化）
│   └── schemas/          # 数据模型定义
├── data-governance/      # 数据治理层
│   ├── quality/          # 数据质量检查
│   ├── lineage/          # 数据血缘追踪
│   ├── security/         # 数据安全和权限控制
│   └── metadata/         # 元数据管理
└── common/               # 通用工具
    ├── index.py          # 统一索引管理
    ├── settings.py       # 统一配置
    └── utils.py          # 工具函数
```

## 支持的数据源

### 协作平台
- **Jira**: 问题、项目、评论
- **Confluence**: 页面、空间、附件

### 文档格式
- **Office**: Excel (.xlsx, .xls), Word (.docx, .doc), PowerPoint (.pptx, .ppt)
- **文本**: Markdown (.md), PDF (.pdf), 纯文本 (.txt)
- **图像**: PNG (.png), JPEG (.jpg, .jpeg)

## 核心设计原则

### 1. 统一数据模型
所有数据源转换为统一的 `Document` 模型：
```python
Document(
    id: str,              # 唯一标识
    content: str,         # 文本内容
    metadata: dict,       # 元数据（来源、作者、时间等）
    source_type: str,     # 数据源类型
    source_id: str,       # 原始数据源ID
    embeddings: Optional[List[float]]  # 向量嵌入
)
```

### 2. 可插拔连接器
每个数据源实现统一的 `Connector` 接口：
```python
class Connector(ABC):
    @abstractmethod
    async def connect(self) -> bool
    
    @abstractmethod
    async def fetch(self, **kwargs) -> List[RawDocument]
    
    @abstractmethod
    async def sync(self) -> SyncResult
```

### 3. 数据治理
- **质量检查**: 内容完整性、格式验证
- **血缘追踪**: 记录数据来源和转换过程
- **安全控制**: 权限管理、敏感信息过滤
- **元数据管理**: 自动提取和索引元数据

### 4. 可迁移性
- 配置驱动：所有连接器通过配置文件管理
- 版本控制：数据模型版本化
- 导出/导入：支持数据迁移和备份

## 使用示例

```python
from shared.data_source import DataSourceManager
from shared.data_governance import GovernanceEngine

# 初始化数据源管理器
manager = DataSourceManager()

# 注册数据源
manager.register_source('jira', JiraConnector(config))
manager.register_source('confluence', ConfluenceConnector(config))
manager.register_source('documents', FileSystemConnector(config))

# 同步数据
documents = await manager.sync_all()

# 应用数据治理
governance = GovernanceEngine()
validated_docs = governance.validate(documents)
governed_docs = governance.apply_policies(validated_docs)

# 创建索引
from shared.common import create_unified_index
index = create_unified_index(governed_docs)
```

## 配置文件示例

```yaml
# config/data_sources.yaml
sources:
  jira:
    type: jira
    url: https://your-domain.atlassian.net
    auth:
      email: ${JIRA_EMAIL}
      api_token: ${JIRA_API_TOKEN}
    projects: [PROJ1, PROJ2]
    sync_interval: 3600  # 秒
    
  confluence:
    type: confluence
    url: https://your-domain.atlassian.net/wiki
    auth:
      email: ${CONFLUENCE_EMAIL}
      api_token: ${CONFLUENCE_API_TOKEN}
    spaces: [SPACE1, SPACE2]
    sync_interval: 3600
    
  documents:
    type: filesystem
    paths:
      - ./data/documents
      - ./data/reports
    file_types: [.xlsx, .docx, .pptx, .md, .pdf, .txt, .png, .jpg]
    watch: true  # 监控文件变化
    
governance:
  quality:
    min_content_length: 10
    check_encoding: true
    validate_metadata: true
    
  security:
    filter_pii: true  # 过滤个人身份信息
    redact_patterns:
      - email
      - phone
      - ssn
    access_control: true
    
  lineage:
    track_transformations: true
    store_raw_data: false
```

## 下一步

1. 实现核心数据模型和接口
2. 开发各个数据源连接器
3. 构建数据治理引擎
4. 集成到现有项目（chat、deep-serach、data-explore）
