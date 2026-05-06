"""
数据源配置文件

定义 chat 项目使用的多个数据源配置。
支持 Local、Jira、Confluence 三种数据源类型。
"""

from pathlib import Path
from typing import List, Dict, Any
import yaml


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        raise RuntimeError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_datasources() -> List[Dict[str, Any]]:
    """从配置文件获取数据源列表"""
    config = load_config()
    datasources_config = config.get('datasources', {})

    datasources = []

    # 本地文件数据源
    if datasources_config.get('local', {}).get('enabled', False):
        local_config = datasources_config['local']
        datasources.append({
            "name": "local_docs",
            "type": "local",
            "enabled": True,
            "config": {
                "directory": local_config.get('data_dir', './data'),
                "recursive": True,
            },
            "description": "本地文档数据源（Markdown, PDF, TXT 等）"
        })

    # Jira 数据源
    if datasources_config.get('jira', {}).get('enabled', False):
        jira_config = datasources_config['jira']
        datasources.append({
            "name": "jira_issues",
            "type": "jira",
            "enabled": True,
            "config": {
                "server_url": jira_config.get('server', ''),
                "email": jira_config.get('email', ''),
                "token": jira_config.get('token', ''),
                "jql": jira_config.get('jql', 'ORDER BY updated DESC'),
            },
            "description": "Jira 问题跟踪数据源"
        })

    # Confluence 数据源
    if datasources_config.get('confluence', {}).get('enabled', False):
        confluence_config = datasources_config['confluence']
        datasources.append({
            "name": "confluence_docs",
            "type": "confluence",
            "enabled": True,
            "config": {
                "base_url": confluence_config.get('url', ''),
                "email": confluence_config.get('username', ''),
                "token": confluence_config.get('token', ''),
                "space_key": confluence_config.get('space_key', ''),
                "cql": confluence_config.get('cql', ''),
            },
            "description": "Confluence 文档数据源"
        })

    return datasources


def get_enabled_datasources() -> List[Dict[str, Any]]:
    """获取启用的数据源列表"""
    datasources = get_datasources()
    return [ds for ds in datasources if ds.get("enabled", True) and validate_datasource_config(ds)]


def get_datasource_by_name(name: str) -> Dict[str, Any] | None:
    """根据名称获取数据源配置"""
    datasources = get_datasources()
    for ds in datasources:
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
        required = ["server_url", "email", "token"]
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

    datasources = get_datasources()
    for ds in datasources:
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
