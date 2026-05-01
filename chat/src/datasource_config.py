"""
数据源配置文件

定义 chat 项目使用的多个数据源配置。
支持 Local、Jira、Confluence 三种数据源类型。
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


# 数据源配置列表
DATASOURCES: List[Dict[str, Any]] = [
    # 本地文件数据源
    {
        "name": "local_docs",
        "type": "local",
        "enabled": True,
        "config": {
            "directory": os.getenv("LOCAL_DATA_DIR", "./data"),
            "recursive": True,
        },
        "description": "本地文档数据源（Markdown, PDF, TXT 等）"
    },

    # Jira 数据源（可选）
    {
        "name": "jira_issues",
        "type": "jira",
        "enabled": os.getenv("JIRA_ENABLED", "false").lower() == "true",
        "config": {
            "server_url": os.getenv("JIRA_SERVER_URL", ""),
            "email": os.getenv("JIRA_EMAIL", ""),
            "token": os.getenv("JIRA_TOKEN", ""),
            "jql": os.getenv("JIRA_JQL", "project = PROJ ORDER BY updated DESC"),
        },
        "description": "Jira 问题跟踪数据源"
    },

    # Confluence 数据源（可选）
    {
        "name": "confluence_docs",
        "type": "confluence",
        "enabled": os.getenv("CONFLUENCE_ENABLED", "false").lower() == "true",
        "config": {
            "base_url": os.getenv("CONFLUENCE_BASE_URL", ""),
            "email": os.getenv("CONFLUENCE_EMAIL", ""),
            "token": os.getenv("CONFLUENCE_TOKEN", ""),
            "space_key": os.getenv("CONFLUENCE_SPACE_KEY", ""),
            "cql": os.getenv("CONFLUENCE_CQL", ""),
        },
        "description": "Confluence 文档数据源"
    },
]


def get_enabled_datasources() -> List[Dict[str, Any]]:
    """获取启用的数据源列表"""
    return [ds for ds in DATASOURCES if ds.get("enabled", True)]


def get_datasource_by_name(name: str) -> Dict[str, Any] | None:
    """根据名称获取数据源配置"""
    for ds in DATASOURCES:
        if ds["name"] == name:
            return ds
    return None


def validate_datasource_config(datasource: Dict[str, Any]) -> bool:
    """验证数据源配置是否完整"""
    if not datasource.get("enabled", True):
        return True  # 未启用的数据源不需要验证

    ds_type = datasource.get("type")
    config = datasource.get("config", {})

    if ds_type == "local":
        return bool(config.get("directory"))

    elif ds_type == "jira":
        required = ["server_url", "email", "token", "jql"]
        return all(config.get(key) for key in required)

    elif ds_type == "confluence":
        required = ["base_url", "email", "token"]
        has_required = all(config.get(key) for key in required)
        has_query = bool(config.get("space_key") or config.get("cql"))
        return has_required and has_query

    return False


def print_datasource_status():
    """打印数据源状态"""
    print("\n=== 数据源配置状态 ===\n")

    for ds in DATASOURCES:
        name = ds["name"]
        enabled = ds.get("enabled", True)
        valid = validate_datasource_config(ds)

        if enabled and valid:
            status = "[OK] 已启用"
        elif not enabled:
            status = "[--] 未启用"
        else:
            status = "[!!] 配置不完整"

        print(f"{name}:")
        print(f"  类型: {ds['type']}")
        print(f"  状态: {status}")
        print(f"  描述: {ds.get('description', 'N/A')}")
        print()


if __name__ == "__main__":
    # 测试配置
    print_datasource_status()

    enabled = get_enabled_datasources()
    print(f"\n启用的数据源数量: {len(enabled)}")
    for ds in enabled:
        print(f"  - {ds['name']} ({ds['type']})")
