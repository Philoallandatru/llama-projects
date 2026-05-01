# 索引层详细设计

## 1. 概述

索引层负责将预处理后的Document对象构建为可检索的索引，支持向量检索和BM25关键词检索的混合模式。

## 2. 模块结构

```
src/indexing/
├── __init__.py
├── base_index.py           # 索引基类
├── requirement_index.py    # 需求索引管理器
├── testcase_index.py       # Test Case索引管理器
└── version_manager.py      # 版本管理器
```

## 3. 索引基类

### 3.1 功能
- 定义索引的通用接口
- 提供持久化和加载功能
- 支持向量和BM25混合检索

### 3.2 接口设计

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any
from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever

class BaseIndex(ABC):
    """索引基类"""
    
    def __init__(
        self,
        index_dir: Path,
        embed_model,
        similarity_top_k: int = 10
    ):
        """
        Args:
            index_dir: 索引存储目录
            embed_model: 嵌入模型
            similarity_top_k: 检索返回的top k结果数
        """
        self.index_dir = index_dir
        self.embed_model = embed_model
        self.similarity_top_k = similarity_top_k
        
        self.vector_index: Optional[VectorStoreIndex] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.documents: List[Document] = []
    
    def build(self, documents: List[Document]) -> None:
        """
        构建索引
        
        Args:
            documents: Document列表
        """
        self.documents = documents
        
        # 1. 构建向量索引
        self.vector_index = VectorStoreIndex.from_documents(
            documents,
            embed_model=self.embed_model,
            show_progress=True
        )
        
        # 2. 构建BM25索引
        self.bm25_retriever = BM25Retriever.from_defaults(
            documents=documents,
            similarity_top_k=self.similarity_top_k
        )
        
        print(f"索引构建完成：{len(documents)} 个文档")
    
    def save(self) -> None:
        """持久化索引到磁盘"""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 保存向量索引
        if self.vector_index:
            self.vector_index.storage_context.persist(
                persist_dir=str(self.index_dir / "vector")
            )
        
        # 2. 保存BM25索引（保存documents即可，加载时重建）
        import pickle
        with open(self.index_dir / "documents.pkl", "wb") as f:
            pickle.dump(self.documents, f)
        
        print(f"索引已保存到：{self.index_dir}")
    
    def load(self) -> None:
        """从磁盘加载索引"""
        if not self.index_dir.exists():
            raise FileNotFoundError(f"索引目录不存在：{self.index_dir}")
        
        # 1. 加载向量索引
        from llama_index.core import load_index_from_storage
        storage_context = StorageContext.from_defaults(
            persist_dir=str(self.index_dir / "vector")
        )
        self.vector_index = load_index_from_storage(
            storage_context,
            embed_model=self.embed_model
        )
        
        # 2. 加载documents并重建BM25索引
        import pickle
        with open(self.index_dir / "documents.pkl", "rb") as f:
            self.documents = pickle.load(f)
        
        self.bm25_retriever = BM25Retriever.from_defaults(
            documents=self.documents,
            similarity_top_k=self.similarity_top_k
        )
        
        print(f"索引已加载：{len(self.documents)} 个文档")
    
    def get_vector_retriever(self, top_k: Optional[int] = None) -> VectorIndexRetriever:
        """获取向量检索器"""
        if not self.vector_index:
            raise ValueError("索引未构建或加载")
        
        return self.vector_index.as_retriever(
            similarity_top_k=top_k or self.similarity_top_k
        )
    
    def get_bm25_retriever(self) -> BM25Retriever:
        """获取BM25检索器"""
        if not self.bm25_retriever:
            raise ValueError("索引未构建或加载")
        
        return self.bm25_retriever
    
    @abstractmethod
    def filter_by_metadata(self, **filters) -> List[Document]:
        """
        根据metadata过滤文档
        
        Args:
            **filters: 过滤条件（key-value对）
            
        Returns:
            过滤后的文档列表
        """
        pass
```

## 4. 需求索引管理器

### 4.1 功能
- 管理需求文档的索引
- 支持按版本号组织索引
- 提供版本切换功能

### 4.2 接口设计

```python
class RequirementIndex(BaseIndex):
    """需求索引管理器"""
    
    def __init__(
        self,
        base_dir: Path,
        version: str,
        embed_model,
        similarity_top_k: int = 10
    ):
        """
        Args:
            base_dir: 索引基础目录
            version: 需求文档版本号
            embed_model: 嵌入模型
            similarity_top_k: 检索返回的top k结果数
        """
        # 索引目录：base_dir/requirements_v{version}/
        index_dir = base_dir / f"requirements_v{version}"
        super().__init__(index_dir, embed_model, similarity_top_k)
        self.version = version
    
    def filter_by_metadata(
        self,
        req_type: Optional[str] = None,
        source_file: Optional[str] = None,
        chapter: Optional[str] = None
    ) -> List[Document]:
        """
        根据metadata过滤需求文档
        
        Args:
            req_type: 需求类型（功能/性能/兼容性等）
            source_file: 来源文件名
            chapter: 章节
            
        Returns:
            过滤后的文档列表
        """
        filtered = self.documents
        
        if req_type:
            filtered = [
                doc for doc in filtered
                if doc.metadata.get('type') == req_type
            ]
        
        if source_file:
            filtered = [
                doc for doc in filtered
                if doc.metadata.get('source_file') == source_file
            ]
        
        if chapter:
            filtered = [
                doc for doc in filtered
                if chapter in doc.metadata.get('chapter', '')
            ]
        
        return filtered
    
    def get_all_types(self) -> List[str]:
        """获取所有需求类型"""
        types = set()
        for doc in self.documents:
            req_type = doc.metadata.get('type')
            if req_type:
                types.add(req_type)
        return sorted(list(types))
    
    def get_all_source_files(self) -> List[str]:
        """获取所有来源文件"""
        files = set()
        for doc in self.documents:
            source_file = doc.metadata.get('source_file')
            if source_file:
                files.add(source_file)
        return sorted(list(files))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        stats = {
            "version": self.version,
            "total_requirements": len(self.documents),
            "types": {},
            "source_files": {}
        }
        
        # 统计各类型需求数量
        for doc in self.documents:
            req_type = doc.metadata.get('type', 'Unknown')
            stats['types'][req_type] = stats['types'].get(req_type, 0) + 1
            
            source_file = doc.metadata.get('source_file', 'Unknown')
            stats['source_files'][source_file] = stats['source_files'].get(source_file, 0) + 1
        
        return stats
```

### 4.3 使用示例

```python
# 1. 构建索引
req_index = RequirementIndex(
    base_dir=Path("data/indexes"),
    version="1.2",
    embed_model=embed_model
)

req_index.build(req_documents)
req_index.save()

# 2. 加载索引
req_index = RequirementIndex(
    base_dir=Path("data/indexes"),
    version="1.2",
    embed_model=embed_model
)
req_index.load()

# 3. 过滤查询
performance_reqs = req_index.filter_by_metadata(req_type="性能")
print(f"性能需求数量：{len(performance_reqs)}")

# 4. 统计信息
stats = req_index.get_statistics()
print(f"需求统计：{stats}")
```

## 5. Test Case索引管理器

### 5.1 功能
- 管理Test Case的索引
- 支持按平台、类别、子类别过滤
- 提供Test Case统计功能

### 5.2 接口设计

```python
class TestCaseIndex(BaseIndex):
    """Test Case索引管理器"""
    
    def __init__(
        self,
        index_dir: Path,
        embed_model,
        similarity_top_k: int = 10
    ):
        """
        Args:
            index_dir: 索引存储目录
            embed_model: 嵌入模型
            similarity_top_k: 检索返回的top k结果数
        """
        super().__init__(index_dir, embed_model, similarity_top_k)
    
    def filter_by_metadata(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> List[Document]:
        """
        根据metadata过滤Test Case文档
        
        Args:
            platform: 平台（Windows/Linux）
            category: 类别（Common/Customer）
            subcategory: 子类别（Performance/Compatibility等）
            file_name: 文件名（支持模糊匹配）
            
        Returns:
            过滤后的文档列表
        """
        filtered = self.documents
        
        if platform:
            filtered = [
                doc for doc in filtered
                if doc.metadata.get('platform') == platform
            ]
        
        if category:
            filtered = [
                doc for doc in filtered
                if doc.metadata.get('category') == category
            ]
        
        if subcategory:
            filtered = [
                doc for doc in filtered
                if doc.metadata.get('subcategory') == subcategory
            ]
        
        if file_name:
            filtered = [
                doc for doc in filtered
                if file_name.lower() in doc.metadata.get('file_name', '').lower()
            ]
        
        return filtered
    
    def get_all_platforms(self) -> List[str]:
        """获取所有平台"""
        platforms = set()
        for doc in self.documents:
            platform = doc.metadata.get('platform')
            if platform:
                platforms.add(platform)
        return sorted(list(platforms))
    
    def get_all_categories(self, platform: Optional[str] = None) -> List[str]:
        """获取所有类别（可按平台过滤）"""
        categories = set()
        for doc in self.documents:
            if platform and doc.metadata.get('platform') != platform:
                continue
            category = doc.metadata.get('category')
            if category:
                categories.add(category)
        return sorted(list(categories))
    
    def get_all_subcategories(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """获取所有子类别（可按平台和类别过滤）"""
        subcategories = set()
        for doc in self.documents:
            if platform and doc.metadata.get('platform') != platform:
                continue
            if category and doc.metadata.get('category') != category:
                continue
            subcategory = doc.metadata.get('subcategory')
            if subcategory:
                subcategories.add(subcategory)
        return sorted(list(subcategories))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        stats = {
            "total_testcases": len(self.documents),
            "platforms": {},
            "categories": {},
            "subcategories": {}
        }
        
        # 统计各维度数量
        for doc in self.documents:
            platform = doc.metadata.get('platform', 'Unknown')
            category = doc.metadata.get('category', 'Unknown')
            subcategory = doc.metadata.get('subcategory', 'Unknown')
            
            stats['platforms'][platform] = stats['platforms'].get(platform, 0) + 1
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            stats['subcategories'][subcategory] = stats['subcategories'].get(subcategory, 0) + 1
        
        return stats
    
    def get_hierarchy_tree(self) -> Dict[str, Any]:
        """
        获取层级树结构
        
        Returns:
            {
                "Windows": {
                    "Common": ["Performance", "Compatibility"],
                    "Customer": ["Feature1", "Feature2"]
                },
                "Linux": {...}
            }
        """
        tree = {}
        
        for doc in self.documents:
            platform = doc.metadata.get('platform', 'Unknown')
            category = doc.metadata.get('category', 'Unknown')
            subcategory = doc.metadata.get('subcategory', 'Unknown')
            
            if platform not in tree:
                tree[platform] = {}
            if category not in tree[platform]:
                tree[platform][category] = set()
            tree[platform][category].add(subcategory)
        
        # 转换set为sorted list
        for platform in tree:
            for category in tree[platform]:
                tree[platform][category] = sorted(list(tree[platform][category]))
        
        return tree
```

### 5.3 使用示例

```python
# 1. 构建索引
tc_index = TestCaseIndex(
    index_dir=Path("data/indexes/testcases"),
    embed_model=embed_model
)

tc_index.build(tc_documents)
tc_index.save()

# 2. 加载索引
tc_index = TestCaseIndex(
    index_dir=Path("data/indexes/testcases"),
    embed_model=embed_model
)
tc_index.load()

# 3. 过滤查询
windows_perf_tests = tc_index.filter_by_metadata(
    platform="Windows",
    subcategory="Performance"
)
print(f"Windows性能测试数量：{len(windows_perf_tests)}")

# 4. 层级树
tree = tc_index.get_hierarchy_tree()
print(f"Test Case层级结构：{tree}")

# 5. 统计信息
stats = tc_index.get_statistics()
print(f"Test Case统计：{stats}")
```

## 6. 版本管理器

### 6.1 功能
- 管理需求文档的多个版本
- 记录版本元数据（源文件列表、创建时间）
- 提供版本对比功能

### 6.2 接口设计

```python
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple

class VersionManager:
    """版本管理器"""
    
    def __init__(self, base_dir: Path):
        """
        Args:
            base_dir: 索引基础目录
        """
        self.base_dir = base_dir
        self.metadata_file = base_dir / "versions.json"
        self.metadata: Dict[str, Any] = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载版本元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self) -> None:
        """保存版本元数据"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def register_version(
        self,
        version: str,
        source_files: List[str],
        description: str = ""
    ) -> None:
        """
        注册新版本
        
        Args:
            version: 版本号
            source_files: 源文件列表
            description: 版本描述
        """
        self.metadata[version] = {
            "source_files": source_files,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "index_dir": f"requirements_v{version}"
        }
        self._save_metadata()
        print(f"版本 {version} 已注册")
    
    def get_all_versions(self) -> List[str]:
        """获取所有版本号（按时间排序）"""
        versions = list(self.metadata.keys())
        versions.sort(key=lambda v: self.metadata[v]['created_at'])
        return versions
    
    def get_version_info(self, version: str) -> Dict[str, Any]:
        """获取版本信息"""
        if version not in self.metadata:
            raise ValueError(f"版本 {version} 不存在")
        return self.metadata[version]
    
    def compare_versions(
        self,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        对比两个版本
        
        Args:
            version1: 旧版本
            version2: 新版本
            
        Returns:
            {
                "added_files": [...],      # 新增的文件
                "removed_files": [...],    # 删除的文件
                "common_files": [...]      # 共同的文件
            }
        """
        if version1 not in self.metadata:
            raise ValueError(f"版本 {version1} 不存在")
        if version2 not in self.metadata:
            raise ValueError(f"版本 {version2} 不存在")
        
        files1 = set(self.metadata[version1]['source_files'])
        files2 = set(self.metadata[version2]['source_files'])
        
        return {
            "added_files": sorted(list(files2 - files1)),
            "removed_files": sorted(list(files1 - files2)),
            "common_files": sorted(list(files1 & files2))
        }
    
    def get_latest_version(self) -> Optional[str]:
        """获取最新版本"""
        versions = self.get_all_versions()
        return versions[-1] if versions else None
```

### 6.3 使用示例

```python
# 1. 初始化版本管理器
version_mgr = VersionManager(base_dir=Path("data/indexes"))

# 2. 注册版本
version_mgr.register_version(
    version="1.2",
    source_files=["用户需求规格说明书_v1.2.pdf", "系统设计文档_v1.2.xlsx"],
    description="初始版本"
)

version_mgr.register_version(
    version="1.3",
    source_files=["用户需求规格说明书_v1.3.pdf", "系统设计文档_v1.3.xlsx"],
    description="新增性能需求"
)

# 3. 查询版本
all_versions = version_mgr.get_all_versions()
print(f"所有版本：{all_versions}")

latest_version = version_mgr.get_latest_version()
print(f"最新版本：{latest_version}")

# 4. 版本对比
diff = version_mgr.compare_versions("1.2", "1.3")
print(f"版本差异：{diff}")
```

## 7. 索引构建流程

### 7.1 完整流程

```python
from pathlib import Path
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. 初始化组件
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5")
version_mgr = VersionManager(base_dir=Path("data/indexes"))

# 2. 预处理（见上一章节）
# req_documents = [...]  # 需求Document列表
# tc_documents = [...]   # Test Case Document列表

# 3. 构建需求索引
req_index = RequirementIndex(
    base_dir=Path("data/indexes"),
    version="1.2",
    embed_model=embed_model
)
req_index.build(req_documents)
req_index.save()

# 4. 注册版本
source_files = list(set([doc.metadata['source_file'] for doc in req_documents]))
version_mgr.register_version(
    version="1.2",
    source_files=source_files,
    description="初始版本"
)

# 5. 构建Test Case索引
tc_index = TestCaseIndex(
    index_dir=Path("data/indexes/testcases"),
    embed_model=embed_model
)
tc_index.build(tc_documents)
tc_index.save()

print("索引构建完成！")
```

### 7.2 增量更新流程

```python
# 1. 加载现有索引
req_index = RequirementIndex(
    base_dir=Path("data/indexes"),
    version="1.2",
    embed_model=embed_model
)
req_index.load()

# 2. 处理新文档
new_req_documents = [...]  # 新增的需求Document

# 3. 合并文档
all_documents = req_index.documents + new_req_documents

# 4. 重建索引
req_index.build(all_documents)
req_index.save()

print(f"索引已更新：新增 {len(new_req_documents)} 个需求")
```

## 8. 性能优化

### 8.1 索引构建优化
- 使用GPU加速向量化（如果可用）
- 批量处理文档（避免逐个处理）
- 使用更小的嵌入模型（如bge-small而非bge-large）

### 8.2 索引存储优化
- 使用向量数据库（如Qdrant、Milvus）替代内存索引
- 压缩向量（使用量化技术）
- 分片存储大规模索引

### 8.3 检索优化
- 缓存热门查询结果
- 使用近似最近邻搜索（ANN）
- 预过滤文档（先用metadata过滤，再检索）

## 9. 索引目录结构

```
data/indexes/
├── versions.json                    # 版本元数据
├── requirements_v1.0/               # 需求索引（版本1.0）
│   ├── vector/                      # 向量索引
│   │   ├── docstore.json
│   │   ├── index_store.json
│   │   └── vector_store.json
│   └── documents.pkl                # 原始文档（用于BM25）
├── requirements_v1.2/               # 需求索引（版本1.2）
│   ├── vector/
│   └── documents.pkl
└── testcases/                       # Test Case索引
    ├── vector/
    └── documents.pkl
```

## 10. 错误处理

### 10.1 索引构建失败
- 记录失败的文档
- 跳过失败文档，继续构建
- 提供重试机制

### 10.2 索引加载失败
- 检查索引目录是否存在
- 检查索引文件是否完整
- 提供索引修复功能

### 10.3 版本冲突
- 检查版本号是否已存在
- 提供版本覆盖选项

## 11. 测试策略

### 11.1 单元测试
- 测试索引构建和加载
- 测试metadata过滤
- 测试版本管理功能

### 11.2 集成测试
- 测试端到端索引流程
- 测试检索准确性
- 测试增量更新

### 11.3 性能测试
- 测试索引构建时间
- 测试检索响应时间
- 测试内存占用
