"""跨源证据检索器

从 LlamaIndex 向量索引中检索相关证据。
"""

import logging
from pathlib import Path
from typing import List, Optional

from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.schema import Document

logger = logging.getLogger(__name__)


class EvidenceRetriever:
    """跨源证据检索器

    职责：
    - 加载三类索引：Jira/Confluence/规格文档
    - 从索引中检索相关证据
    - 支持相似度搜索
    """

    def __init__(self, index_base_path: Path):
        """初始化证据检索器

        Args:
            index_base_path: 索引基础路径（包含 jira/confluence/specs 子目录）
        """
        self.index_base_path = Path(index_base_path)

        # 索引路径
        self.jira_index_path = self.index_base_path / "jira"
        self.confluence_index_path = self.index_base_path / "confluence"
        self.spec_index_path = self.index_base_path / "specs"

        # 加载索引
        self.jira_index = self._load_index(self.jira_index_path, "Jira")
        self.confluence_index = self._load_index(self.confluence_index_path, "Confluence")
        self.spec_index = self._load_index(self.spec_index_path, "Specs")

        logger.info("EvidenceRetriever initialized")

    def _load_index(self, index_path: Path, name: str) -> Optional[VectorStoreIndex]:
        """加载索引

        Args:
            index_path: 索引路径
            name: 索引名称（用于日志）

        Returns:
            VectorStoreIndex 或 None（如果索引不存在）
        """
        if not index_path.exists():
            logger.warning(f"{name} index not found at {index_path}")
            return None

        try:
            storage_context = StorageContext.from_defaults(persist_dir=str(index_path))
            index = load_index_from_storage(storage_context)
            logger.info(f"Loaded {name} index from {index_path}")
            return index
        except Exception as e:
            logger.error(f"Failed to load {name} index: {e}")
            return None

    def retrieve_similar_issues(
        self,
        query: str,
        top_k: int = 5,
        exclude_issue_key: Optional[str] = None
    ) -> List[Document]:
        """检索相似的历史 Jira issues

        Args:
            query: 查询文本
            top_k: 返回结果数量
            exclude_issue_key: 排除的 issue key（通常是目标 issue 本身）

        Returns:
            Document 列表
        """
        if not self.jira_index:
            logger.warning("Jira index not available")
            return []

        try:
            retriever = self.jira_index.as_retriever(similarity_top_k=top_k * 2)
            nodes = retriever.retrieve(query)

            # 过滤掉目标 issue 本身
            filtered_docs = []
            for node in nodes:
                issue_key = node.metadata.get("issue_key", "")
                if exclude_issue_key and issue_key == exclude_issue_key:
                    continue

                # 转换为 Document
                doc = Document(
                    text=node.text,
                    metadata=node.metadata
                )
                filtered_docs.append(doc)

                if len(filtered_docs) >= top_k:
                    break

            logger.info(f"Retrieved {len(filtered_docs)} similar issues")
            return filtered_docs

        except Exception as e:
            logger.error(f"Failed to retrieve similar issues: {e}")
            return []

    def retrieve_confluence_docs(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Document]:
        """检索相关的 Confluence 文档

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            Document 列表
        """
        if not self.confluence_index:
            logger.warning("Confluence index not available")
            return []

        try:
            retriever = self.confluence_index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)

            # 转换为 Document
            docs = [
                Document(text=node.text, metadata=node.metadata)
                for node in nodes
            ]

            logger.info(f"Retrieved {len(docs)} Confluence documents")
            return docs

        except Exception as e:
            logger.error(f"Failed to retrieve Confluence docs: {e}")
            return []

    def retrieve_spec_docs(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Document]:
        """检索相关的规格文档

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            Document 列表
        """
        if not self.spec_index:
            logger.warning("Specs index not available")
            return []

        try:
            retriever = self.spec_index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)

            # 转换为 Document
            docs = [
                Document(text=node.text, metadata=node.metadata)
                for node in nodes
            ]

            logger.info(f"Retrieved {len(docs)} spec documents")
            return docs

        except Exception as e:
            logger.error(f"Failed to retrieve spec docs: {e}")
            return []

    def retrieve_all_evidence(
        self,
        query: str,
        similar_issues_top_k: int = 5,
        confluence_top_k: int = 3,
        spec_top_k: int = 3,
        exclude_issue_key: Optional[str] = None
    ) -> dict[str, List[Document]]:
        """一次性检索所有类型的证据

        Args:
            query: 查询文本
            similar_issues_top_k: 相似 issues 数量
            confluence_top_k: Confluence 文档数量
            spec_top_k: 规格文档数量
            exclude_issue_key: 排除的 issue key

        Returns:
            包含三类证据的字典
        """
        evidence = {
            "similar_issues": self.retrieve_similar_issues(
                query, similar_issues_top_k, exclude_issue_key
            ),
            "confluence": self.retrieve_confluence_docs(query, confluence_top_k),
            "specs": self.retrieve_spec_docs(query, spec_top_k)
        }

        total_count = sum(len(docs) for docs in evidence.values())
        logger.info(f"Retrieved total {total_count} evidence documents")

        return evidence
