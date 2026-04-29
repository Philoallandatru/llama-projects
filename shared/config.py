"""
共享数据层配置

定义数据源、加载器和治理策略
"""
from typing import Dict, Any, List


class DataSourceConfig:
    """数据源配置"""

    # 文件系统配置
    FILESYSTEM = {
        'paths': [
            './chat/data',
            './deep-serach/data',
            './data-explore/data',
        ],
        'file_types': [
            '.xlsx', '.xls',      # Excel
            '.docx', '.doc',      # Word
            '.pptx', '.ppt',      # PowerPoint
            '.md',                # Markdown
            '.pdf',               # PDF
            '.txt',               # Text
            '.png', '.jpg',       # Image
        ],
        'recursive': True,
        'watch': False,
    }

    # Jira 配置（示例）
    JIRA = {
        'url': 'https://your-domain.atlassian.net',
        'auth': {
            'email': '${JIRA_EMAIL}',
            'api_token': '${JIRA_API_TOKEN}',
        },
        'projects': ['PROJ1', 'PROJ2'],
        'jql': 'project in (PROJ1, PROJ2) AND updated >= -7d',
        'sync_interval': 3600,  # 秒
    }

    # Confluence 配置（示例）
    CONFLUENCE = {
        'url': 'https://your-domain.atlassian.net/wiki',
        'auth': {
            'email': '${CONFLUENCE_EMAIL}',
            'api_token': '${CONFLUENCE_API_TOKEN}',
        },
        'spaces': ['SPACE1', 'SPACE2'],
        'sync_interval': 3600,
    }


class GovernanceConfig:
    """数据治理配置"""

    # 数据质量配置
    QUALITY = {
        'min_content_length': 10,
        'check_encoding': True,
        'validate_metadata': True,
        'remove_duplicates': True,
    }

    # 数据安全配置
    SECURITY = {
        'filter_pii': True,  # 过滤个人身份信息
        'redact_patterns': [
            'email',
            'phone',
            'ssn',
            'credit_card',
        ],
        'access_control': True,
        'default_access_level': 'internal',
    }

    # 数据血缘配置
    LINEAGE = {
        'track_transformations': True,
        'store_raw_data': False,
        'track_access': True,
    }

    # 元数据配置
    METADATA = {
        'auto_extract': True,
        'extract_entities': True,  # 提取实体（人名、地名等）
        'extract_keywords': True,  # 提取关键词
        'extract_summary': True,   # 生成摘要
    }


class IndexConfig:
    """索引配置"""

    # 向量索引配置
    VECTOR_INDEX = {
        'chunk_size': 512,
        'chunk_overlap': 50,
        'embedding_model': 'text-embedding-3-large',
        'similarity_top_k': 10,
    }

    # 存储配置
    STORAGE = {
        'persist_dir': './storage',
        'vector_store': 'simple',  # 或 'chroma', 'pinecone' 等
    }


# 完整配置
CONFIG: Dict[str, Any] = {
    'data_sources': {
        'filesystem': DataSourceConfig.FILESYSTEM,
        # 'jira': DataSourceConfig.JIRA,
        # 'confluence': DataSourceConfig.CONFLUENCE,
    },
    'governance': {
        'quality': GovernanceConfig.QUALITY,
        'security': GovernanceConfig.SECURITY,
        'lineage': GovernanceConfig.LINEAGE,
        'metadata': GovernanceConfig.METADATA,
    },
    'index': {
        'vector': IndexConfig.VECTOR_INDEX,
        'storage': IndexConfig.STORAGE,
    },
}
