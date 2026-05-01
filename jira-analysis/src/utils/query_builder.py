"""查询构建工具"""
from typing import Dict, Any


def build_retrieval_query(issue_data: Dict[str, Any]) -> str:
    """构建检索查询字符串

    Args:
        issue_data: Issue 数据字典

    Returns:
        格式化的查询字符串
    """
    parts = []

    if summary := issue_data.get("summary"):
        parts.append(summary)

    if description := issue_data.get("description"):
        parts.append(description)

    return " ".join(parts)
