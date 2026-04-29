"""
数据治理 - 质量检查

检查文档质量，确保数据符合标准
"""
from typing import List, Dict, Any
from llama_index.core import Document


class QualityMetrics:
    """质量指标"""

    def __init__(self):
        self.total_docs = 0
        self.passed_docs = 0
        self.failed_docs = 0
        self.issues: List[Dict[str, Any]] = []

    def add_issue(self, doc_id: str, issue_type: str, message: str):
        """添加质量问题"""
        self.issues.append({
            "doc_id": doc_id,
            "type": issue_type,
            "message": message
        })
        self.failed_docs += 1

    def mark_passed(self):
        """标记通过"""
        self.passed_docs += 1

    def get_summary(self) -> Dict[str, Any]:
        """获取质量摘要"""
        return {
            "total": self.total_docs,
            "passed": self.passed_docs,
            "failed": self.failed_docs,
            "pass_rate": self.passed_docs / self.total_docs if self.total_docs > 0 else 0,
            "issues": self.issues
        }


class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化质量检查器

        Args:
            config: 配置，包含：
                - min_content_length: 最小内容长度（默认 10）
                - check_encoding: 是否检查编码（默认 True）
                - remove_duplicates: 是否去重（默认 True）
        """
        self.config = config or {}
        self.min_content_length = self.config.get("min_content_length", 10)
        self.check_encoding = self.config.get("check_encoding", True)
        self.remove_duplicates = self.config.get("remove_duplicates", True)

    def validate(self, documents: List[Document]) -> tuple[List[Document], QualityMetrics]:
        """
        验证文档质量

        Args:
            documents: 文档列表

        Returns:
            tuple[List[Document], QualityMetrics]: 验证通过的文档和质量指标
        """
        metrics = QualityMetrics()
        metrics.total_docs = len(documents)

        validated_docs = []
        seen_content = set()

        for doc in documents:
            doc_id = doc.doc_id or doc.id_

            # 检查内容长度
            if len(doc.text.strip()) < self.min_content_length:
                metrics.add_issue(
                    doc_id,
                    "content_too_short",
                    f"内容长度 {len(doc.text)} 小于最小长度 {self.min_content_length}"
                )
                continue

            # 检查编码
            if self.check_encoding:
                try:
                    doc.text.encode('utf-8')
                except UnicodeEncodeError:
                    metrics.add_issue(
                        doc_id,
                        "encoding_error",
                        "文档包含无效的 UTF-8 字符"
                    )
                    continue

            # 去重
            if self.remove_duplicates:
                content_hash = hash(doc.text)
                if content_hash in seen_content:
                    metrics.add_issue(
                        doc_id,
                        "duplicate",
                        "文档内容重复"
                    )
                    continue
                seen_content.add(content_hash)

            # 通过验证
            metrics.mark_passed()
            validated_docs.append(doc)

        print(f"质量检查完成: {metrics.passed_docs}/{metrics.total_docs} 通过")
        if metrics.failed_docs > 0:
            print(f"  发现 {metrics.failed_docs} 个问题")

        return validated_docs, metrics

    def enrich_metadata(self, documents: List[Document]) -> List[Document]:
        """
        丰富文档元数据

        Args:
            documents: 文档列表

        Returns:
            List[Document]: 丰富后的文档列表
        """
        for doc in documents:
            # 添加质量指标
            doc.metadata["content_length"] = len(doc.text)
            doc.metadata["word_count"] = len(doc.text.split())
            doc.metadata["quality_checked"] = True

        return documents
