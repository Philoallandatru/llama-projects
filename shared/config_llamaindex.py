"""
共享层配置 - 使用 LlamaIndex Readers
"""
from typing import Dict, Any


class ReaderConfig:
    """Reader 配置"""

    # 文件系统配置
    FILESYSTEM = {
        "directories": [
            "../chat/data",
            "../deep-serach/data",
            "../data-explore/data",
        ],
        "recursive": True,
        "required_exts": [".md", ".txt", ".pdf", ".docx", ".xlsx", ".pptx"],
        "exclude": ["__pycache__", ".git", "node_modules"],
    }

    # Jira 配置
    JIRA = {
        "email": "${JIRA_EMAIL}",
        "api_token": "${JIRA_API_TOKEN}",
        "server_url": "https://your-domain.atlassian.net",
        "query": "project in (PROJ1, PROJ2) AND updated >= -7d",
    }

    # Confluence 配置
    CONFLUENCE = {
        "base_url": "https://your-domain.atlassian.net/wiki",
        "api_token": "${CONFLUENCE_API_TOKEN}",
        "space_keys": ["SPACE1", "SPACE2"],
    }

    # Notion 配置
    NOTION = {
        "integration_token": "${NOTION_TOKEN}",
        "page_ids": [],  # 要加载的页面 ID
    }

    # Google Drive 配置
    GOOGLE_DRIVE = {
        "credentials_path": "./credentials.json",
        "folder_ids": [],  # 要加载的文件夹 ID
    }


class GovernanceConfig:
    """数据治理配置"""

    # 质量检查配置
    QUALITY = {
        "min_content_length": 50,
        "check_encoding": True,
        "remove_duplicates": True,
    }

    # 安全配置
    SECURITY = {
        # PII 过滤
        "pii_filter": {
            "enabled_filters": ["email", "phone", "id_card", "credit_card"],
            "redact_mode": "mask",  # "mask" 或 "remove"
        },
        # 内容过滤
        "content_filter": {
            "blocked_keywords": [],  # 阻止的关键词
        },
    }

    # 元数据配置
    METADATA = {
        "auto_enrich": True,  # 自动丰富元数据
        "extract_keywords": True,  # 提取关键词
        "extract_summary": False,  # 生成摘要（需要 LLM）
    }


class IndexConfig:
    """索引配置"""

    # 向量索引配置
    VECTOR_INDEX = {
        "chunk_size": 512,
        "chunk_overlap": 50,
        "similarity_top_k": 10,
    }

    # 存储配置
    STORAGE = {
        "persist_dir": "./storage",
    }


# 完整配置
CONFIG: Dict[str, Any] = {
    "readers": {
        "filesystem": ReaderConfig.FILESYSTEM,
        "jira": ReaderConfig.JIRA,
        "confluence": ReaderConfig.CONFLUENCE,
        "notion": ReaderConfig.NOTION,
        "google_drive": ReaderConfig.GOOGLE_DRIVE,
    },
    "governance": {
        "quality": GovernanceConfig.QUALITY,
        "security": GovernanceConfig.SECURITY,
        "metadata": GovernanceConfig.METADATA,
    },
    "index": {
        "vector": IndexConfig.VECTOR_INDEX,
        "storage": IndexConfig.STORAGE,
    },
}
