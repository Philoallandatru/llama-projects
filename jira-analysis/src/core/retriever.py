"""跨源证据检索器 - 简化版

从 LlamaIndex 向量索引中检索相关证据。
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict

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

    # 索引配置 - 匹配 datasource 的目录结构
    INDEX_CONFIGS = {
        "similar_issues": {"subdir": "jira_kan/indexes/vector", "name": "Jira"},
        "confluence": {"subdir": "confluence/indexes/vector", "name": "Confluence"},
        "specs": {"subdir": "specs/indexes/vector", "name": "Specs"}
    }

    def __init__(self, index_base_path: Path):
        """初始化证据检索器

        Args:
            index_base_path: 索引基础路径（包含 jira/confluence/specs 子目录）
        """
        self.index_base_path = Path(index_base_path)
        self.indexes = {}

        print(f"[RETRIEVER INIT] base_path: {self.index_base_path.absolute()}")
        logger.info(f"[RETRIEVER] Initializing with base_path: {self.index_base_path.absolute()}")

        # 加载所有索引
        for key, config in self.INDEX_CONFIGS.items():
            index_path = self.index_base_path / config["subdir"]
            print(f"[RETRIEVER INIT] Loading {key} from: {index_path.absolute()}")
            self.indexes[key] = self._load_index(index_path, config["name"])

        logger.info("EvidenceRetriever initialized")
        print(f"[RETRIEVER INIT] Loaded indexes: {[k for k, v in self.indexes.items() if v is not None]}")

    def _load_index(self, index_path: Path, name: str) -> Optional[VectorStoreIndex]:
        """加载索引

        Args:
            index_path: 索引路径
            name: 索引名称（用于日志）

        Returns:
            VectorStoreIndex 或 None（如果索引不存在）
        """
        print(f"[RETRIEVER LOAD] Checking {name} at: {index_path.absolute()}")
        print(f"[RETRIEVER LOAD] Path exists: {index_path.exists()}")
        logger.info(f"[RETRIEVER] Checking {name} index at: {index_path.absolute()}")
        if not index_path.exists():
            logger.warning(f"{name} index not found at {index_path}")
            print(f"[RETRIEVER LOAD] {name} NOT FOUND")
            return None

        try:
            print(f"[RETRIEVER LOAD] Loading {name} from storage...")
            storage_context = StorageContext.from_defaults(persist_dir=str(index_path))

            # Load index with current Settings (including embed_model)
            from llama_index.core import Settings
            index = load_index_from_storage(
                storage_context,
                embed_model=Settings.embed_model  # Use current embedding model
            )
            logger.info(f"Loaded {name} index from {index_path}")
            print(f"[RETRIEVER LOAD] {name} loaded successfully")
            return index
        except Exception as e:
            logger.error(f"Failed to load {name} index: {e}")
            print(f"[RETRIEVER LOAD] {name} FAILED: {e}")
            return None

    def retrieve(
        self,
        index_key: str,
        query: str,
        top_k: int = 5,
        exclude_issue_key: Optional[str] = None
    ) -> List[Document]:
        """通用检索方法

        Args:
            index_key: 索引键（similar_issues/confluence/specs）
            query: 查询文本
            top_k: 返回结果数量
            exclude_issue_key: 排除的 issue key（仅对 similar_issues 有效）

        Returns:
            Document 列表
        """
        index = self.indexes.get(index_key)
        if not index:
            logger.warning(f"{index_key} index not available")
            return []

        try:
            # 对于 similar_issues，获取更多结果以便过滤
            fetch_k = top_k * 2 if index_key == "similar_issues" and exclude_issue_key else top_k

            # Debug: Check embedding model state
            from llama_index.core import Settings
            logger.info(f"[RETRIEVE DEBUG] Embedding model type: {type(Settings.embed_model)}")
            logger.info(f"[RETRIEVE DEBUG] Embedding model: {Settings.embed_model}")

            # Test embedding directly before retrieval
            logger.info(f"[RETRIEVE DEBUG] Testing direct embedding call...")
            try:
                test_embedding = Settings.embed_model.get_query_embedding(query)
                logger.info(f"[RETRIEVE DEBUG] Direct embedding result: {test_embedding is not None}, dim: {len(test_embedding) if test_embedding else 'None'}")
            except Exception as e:
                logger.error(f"[RETRIEVE DEBUG] Direct embedding failed: {e}")
                import traceback
                logger.error(f"[RETRIEVE DEBUG] Traceback: {traceback.format_exc()}")

            # Create retriever with explicit embed_model
            retriever = index.as_retriever(
                similarity_top_k=fetch_k,
                embed_model=Settings.embed_model
            )
            logger.info(f"[RETRIEVE DEBUG] Retriever created, attempting to retrieve with query: {query[:100]}")
            nodes = retriever.retrieve(query)
            logger.info(f"[RETRIEVE DEBUG] Retrieved {len(nodes)} nodes from {index_key}")

            # 转换为 Document 并过滤
            docs = []
            for node in nodes:
                # 过滤目标 issue 本身
                if exclude_issue_key and node.metadata.get("issue_key") == exclude_issue_key:
                    continue

                docs.append(Document(text=node.text, metadata=node.metadata))

                if len(docs) >= top_k:
                    break

            logger.info(f"[RETRIEVE DEBUG] Retrieved {len(docs)} documents from {index_key}")
            return docs

        except Exception as e:
            logger.error(f"[RETRIEVE ERROR] Failed to retrieve from {index_key}: {e}")
            import traceback
            logger.error(f"[RETRIEVE ERROR] Full traceback:\n{traceback.format_exc()}")
            return []

    def retrieve_all_evidence(
        self,
        query: str,
        similar_issues_top_k: int = 5,
        confluence_top_k: int = 3,
        spec_top_k: int = 3,
        exclude_issue_key: Optional[str] = None
    ) -> Dict[str, List[Document]]:
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
            "similar_issues": self.retrieve("similar_issues", query, similar_issues_top_k, exclude_issue_key),
            "confluence": self.retrieve("confluence", query, confluence_top_k),
            "specs": self.retrieve("specs", query, spec_top_k)
        }

        total_count = sum(len(docs) for docs in evidence.values())
        logger.info(f"Retrieved total {total_count} evidence documents")

        return evidence
