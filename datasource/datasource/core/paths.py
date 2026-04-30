"""路径管理工具

本模块提供统一的路径管理功能，确保所有文件和目录的路径一致性。
"""

from pathlib import Path
from typing import Optional


class Paths:
    """路径管理工具类

    管理 DataSource 系统中所有文件和目录的路径。
    默认使用项目根目录下的 data/ 目录作为基础目录。

    目录结构：
        data/
        ├── sources/
        │   └── {source_name}/
        │       ├── source.yaml          # 数据源配置
        │       ├── raw/                 # 原始数据
        │       ├── documents/           # LlamaIndex Documents
        │       ├── assets/              # 附件资源
        │       ├── indexes/             # 索引文件
        │       │   ├── vector/          # 向量索引
        │       │   └── bm25.pkl         # BM25 索引
        │       ├── manifest.json        # 同步清单
        │       └── sync.log             # 同步日志
        └── logs/                        # 全局日志
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """初始化路径管理器

        Args:
            base_dir: 基础目录路径。如果为 None，使用默认路径（项目根目录的 data/）
        """
        if base_dir is None:
            # 默认使用项目根目录的 data/
            # datasource/core/paths.py -> datasource/ -> llama-projects/ -> data/
            base_dir = Path(__file__).parent.parent.parent / "data"

        self.base_dir = Path(base_dir)
        self.sources_dir = self.base_dir / "sources"
        self.logs_dir = self.base_dir / "logs"

    # ============ 数据源根目录 ============

    def source(self, name: str) -> Path:
        """获取数据源根目录

        Args:
            name: 数据源名称

        Returns:
            数据源根目录路径
        """
        return self.sources_dir / name

    def source_config(self, name: str) -> Path:
        """获取数据源配置文件路径

        Args:
            name: 数据源名称

        Returns:
            source.yaml 文件路径
        """
        return self.source(name) / "source.yaml"

    # ============ 数据目录 ============

    def raw(self, name: str) -> Path:
        """获取原始数据目录

        Args:
            name: 数据源名称

        Returns:
            raw/ 目录路径
        """
        return self.source(name) / "raw"

    def documents(self, name: str) -> Path:
        """获取文档目录

        Args:
            name: 数据源名称

        Returns:
            documents/ 目录路径
        """
        return self.source(name) / "documents"

    def assets(self, name: str) -> Path:
        """获取资源目录（附件）

        Args:
            name: 数据源名称

        Returns:
            assets/ 目录路径
        """
        return self.source(name) / "assets"

    # ============ 索引目录 ============

    def indexes(self, name: str) -> Path:
        """获取索引根目录

        Args:
            name: 数据源名称

        Returns:
            indexes/ 目录路径
        """
        return self.source(name) / "indexes"

    def vector_index(self, name: str) -> Path:
        """获取向量索引目录

        Args:
            name: 数据源名称

        Returns:
            indexes/vector/ 目录路径
        """
        return self.indexes(name) / "vector"

    def bm25_index(self, name: str) -> Path:
        """获取 BM25 索引文件路径

        Args:
            name: 数据源名称

        Returns:
            indexes/bm25.pkl 文件路径
        """
        return self.indexes(name) / "bm25.pkl"

    # ============ 元数据文件 ============

    def manifest(self, name: str) -> Path:
        """获取清单文件路径

        Args:
            name: 数据源名称

        Returns:
            manifest.json 文件路径
        """
        return self.source(name) / "manifest.json"

    def sync_log(self, name: str) -> Path:
        """获取同步日志文件路径

        Args:
            name: 数据源名称

        Returns:
            sync.log 文件路径
        """
        return self.source(name) / "sync.log"

    def sync_report(self, name: str) -> Path:
        """获取同步报告文件路径

        Args:
            name: 数据源名称

        Returns:
            sync_report.md 文件路径
        """
        return self.source(name) / "sync_report.md"

    # ============ 工具方法 ============

    def ensure_dirs(self, name: str) -> None:
        """确保数据源的所有必要目录存在

        Args:
            name: 数据源名称
        """
        directories = [
            self.source(name),
            self.raw(name),
            self.documents(name),
            self.assets(name),
            self.indexes(name),
            self.vector_index(name),
            self.logs_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def exists(self, name: str) -> bool:
        """检查数据源目录是否存在

        Args:
            name: 数据源名称

        Returns:
            如果数据源目录存在返回 True，否则返回 False
        """
        return self.source(name).exists()

    def list_sources(self) -> list[str]:
        """列出所有数据源名称

        Returns:
            数据源名称列表
        """
        if not self.sources_dir.exists():
            return []

        sources = []
        for source_dir in self.sources_dir.iterdir():
            if source_dir.is_dir() and self.source_config(source_dir.name).exists():
                sources.append(source_dir.name)

        return sorted(sources)

    def get_size_mb(self, name: str) -> float:
        """计算数据源目录的总大小

        Args:
            name: 数据源名称

        Returns:
            目录大小（MB）
        """
        source_dir = self.source(name)
        if not source_dir.exists():
            return 0.0

        total_size = 0
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size / (1024 * 1024)

    def get_index_size_mb(self, name: str) -> float:
        """计算索引目录的大小

        Args:
            name: 数据源名称

        Returns:
            索引大小（MB）
        """
        indexes_dir = self.indexes(name)
        if not indexes_dir.exists():
            return 0.0

        total_size = 0
        for file_path in indexes_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size / (1024 * 1024)
