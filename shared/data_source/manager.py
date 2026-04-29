"""
数据源管理器

统一管理所有数据源的连接、同步和加载
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from .connectors.base import BaseConnector
from .loaders.base import BaseLoader
from .schemas.models import (
    UnifiedDocument,
    SyncResult,
    SourceType,
    RawDocument
)


class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.loaders: Dict[SourceType, BaseLoader] = {}
        self._sync_history: List[SyncResult] = []

    def register_connector(self, name: str, connector: BaseConnector):
        """
        注册数据源连接器

        Args:
            name: 连接器名称
            connector: 连接器实例
        """
        self.connectors[name] = connector
        print(f"已注册连接器: {name} ({connector.source_type.value})")

    def register_loader(self, source_type: SourceType, loader: BaseLoader):
        """
        注册数据加载器

        Args:
            source_type: 数据源类型
            loader: 加载器实例
        """
        self.loaders[source_type] = loader
        print(f"已注册加载器: {source_type.value}")

    async def connect_all(self) -> Dict[str, bool]:
        """
        连接所有数据源

        Returns:
            Dict[str, bool]: 连接结果 {连接器名称: 是否成功}
        """
        results = {}
        for name, connector in self.connectors.items():
            try:
                success = await connector.connect()
                results[name] = success
                status = "成功" if success else "失败"
                print(f"连接 {name}: {status}")
            except Exception as e:
                results[name] = False
                print(f"连接 {name} 失败: {e}")
        return results

    async def sync_source(
        self,
        name: str,
        incremental: bool = True
    ) -> Optional[SyncResult]:
        """
        同步单个数据源

        Args:
            name: 连接器名称
            incremental: 是否增量同步

        Returns:
            Optional[SyncResult]: 同步结果
        """
        connector = self.connectors.get(name)
        if not connector:
            print(f"连接器 {name} 不存在")
            return None

        try:
            print(f"开始同步 {name}...")
            result = await connector.sync(incremental=incremental)
            self._sync_history.append(result)
            print(f"同步 {name} 完成: 获取 {result.total_fetched} 条，"
                  f"处理 {result.total_processed} 条，"
                  f"错误 {result.total_errors} 条")
            return result
        except Exception as e:
            print(f"同步 {name} 失败: {e}")
            return None

    async def sync_all(
        self,
        incremental: bool = True,
        parallel: bool = True
    ) -> List[SyncResult]:
        """
        同步所有数据源

        Args:
            incremental: 是否增量同步
            parallel: 是否并行同步

        Returns:
            List[SyncResult]: 同步结果列表
        """
        if parallel:
            tasks = [
                self.sync_source(name, incremental)
                for name in self.connectors.keys()
            ]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]
        else:
            results = []
            for name in self.connectors.keys():
                result = await self.sync_source(name, incremental)
                if result:
                    results.append(result)
            return results

    async def load_documents(
        self,
        raw_docs: List[RawDocument]
    ) -> List[UnifiedDocument]:
        """
        加载原始文档为统一文档

        Args:
            raw_docs: 原始文档列表

        Returns:
            List[UnifiedDocument]: 统一文档列表
        """
        results = []
        for raw_doc in raw_docs:
            loader = self.loaders.get(raw_doc.source_type)
            if not loader:
                print(f"未找到 {raw_doc.source_type.value} 的加载器")
                continue

            try:
                doc = await loader.load(raw_doc)
                if doc:
                    results.append(doc)
            except Exception as e:
                print(f"加载文档 {raw_doc.source_id} 失败: {e}")

        return results

    async def fetch_and_load(
        self,
        connector_name: str,
        **fetch_kwargs
    ) -> List[UnifiedDocument]:
        """
        从指定数据源获取并加载文档

        Args:
            connector_name: 连接器名称
            **fetch_kwargs: 获取参数

        Returns:
            List[UnifiedDocument]: 统一文档列表
        """
        connector = self.connectors.get(connector_name)
        if not connector:
            print(f"连接器 {connector_name} 不存在")
            return []

        # 获取原始文档
        raw_docs = await connector.fetch(**fetch_kwargs)
        print(f"从 {connector_name} 获取了 {len(raw_docs)} 个文档")

        # 加载为统一文档
        unified_docs = await self.load_documents(raw_docs)
        print(f"成功加载 {len(unified_docs)} 个文档")

        return unified_docs

    def get_sync_history(
        self,
        source_type: Optional[SourceType] = None
    ) -> List[SyncResult]:
        """
        获取同步历史

        Args:
            source_type: 数据源类型（可选，不指定则返回所有）

        Returns:
            List[SyncResult]: 同步历史
        """
        if source_type:
            return [
                r for r in self._sync_history
                if r.source_type == source_type
            ]
        return self._sync_history

    async def disconnect_all(self):
        """断开所有连接"""
        for name, connector in self.connectors.items():
            try:
                await connector.disconnect()
                print(f"已断开 {name}")
            except Exception as e:
                print(f"断开 {name} 失败: {e}")
