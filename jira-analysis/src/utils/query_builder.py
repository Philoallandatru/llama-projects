"""查询构建工具"""
from typing import Dict, Any


def build_retrieval_query(issue_data: Dict[str, Any]) -> str:
    """构建检索查询字符串

    Args:
        issue_data: Issue 数据字典（Jira API 响应格式）

    Returns:
        格式化的查询字符串
    """
    parts = []

    # Jira API 返回的数据结构：fields.summary 和 fields.description
    fields = issue_data.get("fields", {})

    if summary := fields.get("summary"):
        parts.append(summary)

    if description := fields.get("description"):
        # Description 可能是字符串或 Atlassian Document Format (ADF)
        if isinstance(description, str):
            parts.append(description)
        elif isinstance(description, dict):
            # 简单提取 ADF 中的文本内容
            parts.append(_extract_text_from_adf(description))

    return " ".join(parts)


def _extract_text_from_adf(adf: Dict[str, Any]) -> str:
    """从 Atlassian Document Format 中提取纯文本

    Args:
        adf: ADF 格式的文档

    Returns:
        提取的纯文本
    """
    texts = []

    def extract_recursive(node: Dict[str, Any]):
        if isinstance(node, dict):
            # 提取文本节点
            if node.get("type") == "text":
                if text := node.get("text"):
                    texts.append(text)

            # 递归处理 content
            if content := node.get("content"):
                if isinstance(content, list):
                    for item in content:
                        extract_recursive(item)

    extract_recursive(adf)
    return " ".join(texts)
