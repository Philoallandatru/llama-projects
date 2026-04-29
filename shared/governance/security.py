"""
数据治理 - 安全过滤

过滤敏感信息（PII）和不安全内容
"""
from typing import List, Dict, Any, Pattern
import re
from llama_index.core import Document


class PIIFilter:
    """个人身份信息（PII）过滤器"""

    # 常见 PII 模式
    PATTERNS = {
        "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "phone": re.compile(r'\b(?:\+?86)?1[3-9]\d{9}\b'),
        "id_card": re.compile(r'\b\d{17}[\dXx]\b'),
        "credit_card": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
        "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    }

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化 PII 过滤器

        Args:
            config: 配置，包含：
                - enabled_filters: 启用的过滤器列表（默认全部）
                - redact_mode: 替换模式 "mask" 或 "remove"（默认 "mask"）
                - custom_patterns: 自定义正则模式
        """
        self.config = config or {}
        self.enabled_filters = self.config.get(
            "enabled_filters",
            list(self.PATTERNS.keys())
        )
        self.redact_mode = self.config.get("redact_mode", "mask")

        # 添加自定义模式
        custom_patterns = self.config.get("custom_patterns", {})
        for name, pattern in custom_patterns.items():
            self.PATTERNS[name] = re.compile(pattern)

    def filter(self, documents: List[Document]) -> List[Document]:
        """
        过滤文档中的 PII

        Args:
            documents: 文档列表

        Returns:
            List[Document]: 过滤后的文档列表
        """
        filtered_docs = []
        total_redactions = 0

        for doc in documents:
            filtered_text, redactions = self._filter_text(doc.text)

            # 创建新文档
            filtered_doc = Document(
                text=filtered_text,
                metadata={
                    **doc.metadata,
                    "pii_filtered": True,
                    "pii_redactions": redactions,
                }
            )

            filtered_docs.append(filtered_doc)
            total_redactions += sum(redactions.values())

        if total_redactions > 0:
            print(f"PII 过滤完成: 替换了 {total_redactions} 处敏感信息")

        return filtered_docs

    def _filter_text(self, text: str) -> tuple[str, Dict[str, int]]:
        """
        过滤文本中的 PII

        Args:
            text: 原始文本

        Returns:
            tuple[str, Dict[str, int]]: 过滤后的文本和替换统计
        """
        filtered_text = text
        redactions = {}

        for filter_name in self.enabled_filters:
            pattern = self.PATTERNS.get(filter_name)
            if not pattern:
                continue

            matches = pattern.findall(filtered_text)
            if matches:
                redactions[filter_name] = len(matches)

                if self.redact_mode == "mask":
                    # 替换为掩码
                    replacement = f"[{filter_name.upper()}_REDACTED]"
                    filtered_text = pattern.sub(replacement, filtered_text)
                elif self.redact_mode == "remove":
                    # 完全移除
                    filtered_text = pattern.sub("", filtered_text)

        return filtered_text, redactions

    def scan(self, documents: List[Document]) -> Dict[str, Any]:
        """
        扫描文档中的 PII（不修改）

        Args:
            documents: 文档列表

        Returns:
            Dict[str, Any]: 扫描报告
        """
        report = {
            "total_docs": len(documents),
            "docs_with_pii": 0,
            "pii_types": {},
            "details": []
        }

        for doc in documents:
            doc_pii = {}
            has_pii = False

            for filter_name in self.enabled_filters:
                pattern = self.PATTERNS.get(filter_name)
                if not pattern:
                    continue

                matches = pattern.findall(doc.text)
                if matches:
                    has_pii = True
                    doc_pii[filter_name] = len(matches)
                    report["pii_types"][filter_name] = \
                        report["pii_types"].get(filter_name, 0) + len(matches)

            if has_pii:
                report["docs_with_pii"] += 1
                report["details"].append({
                    "doc_id": doc.doc_id or doc.id_,
                    "pii_found": doc_pii
                })

        return report


class ContentFilter:
    """内容过滤器（过滤不安全或不适当的内容）"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化内容过滤器

        Args:
            config: 配置，包含：
                - blocked_keywords: 阻止的关键词列表
                - min_quality_score: 最小质量分数
        """
        self.config = config or {}
        self.blocked_keywords = self.config.get("blocked_keywords", [])

    def filter(self, documents: List[Document]) -> List[Document]:
        """
        过滤不安全的内容

        Args:
            documents: 文档列表

        Returns:
            List[Document]: 过滤后的文档列表
        """
        filtered_docs = []
        blocked_count = 0

        for doc in documents:
            if self._is_safe(doc.text):
                filtered_docs.append(doc)
            else:
                blocked_count += 1

        if blocked_count > 0:
            print(f"内容过滤: 阻止了 {blocked_count} 个不安全的文档")

        return filtered_docs

    def _is_safe(self, text: str) -> bool:
        """检查文本是否安全"""
        text_lower = text.lower()

        for keyword in self.blocked_keywords:
            if keyword.lower() in text_lower:
                return False

        return True
