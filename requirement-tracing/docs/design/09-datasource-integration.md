# 整合 DataSource 层的设计方案

## 1. 为什么要整合 DataSource？

### 1.1 DataSource 的核心能力

`datasource` 项目提供了：
- ✅ **统一的数据源管理**：配置持久化、目录结构管理
- ✅ **多种数据源支持**：Local、Jira、Confluence（可扩展）
- ✅ **完整的索引管理**：Vector + BM25 混合索引
- ✅ **增量同步机制**：支持增量更新，避免重复处理
- ✅ **标准化的文档模型**：基于 LlamaIndex Document
- ✅ **CLI 工具**：成熟的命令行接口

### 1.2 Requirement-Tracing 的需求

`requirement-tracing` 需要：
- 管理需求文档（PDF/Excel）
- 管理测试用例（Python代码）
- 构建和管理索引
- 支持版本管理
- 提供查询接口

### 1.3 整合的价值

**避免重复造轮**：
- 不需要重新实现索引管理（Vector + BM25）
- 不需要重新实现配置管理和持久化
- 不需要重新实现增量同步机制
- 不需要重新实现 CLI 框架

**获得额外能力**：
- 自动支持 Jira/Confluence 数据源（未来可能需要）
- 成熟的错误处理和日志系统
- 标准化的目录结构

---

## 2. 整合方案设计

### 2.1 架构调整

**原设计**（独立实现）：
```
requirement-tracing/
├── src/
│   ├── preprocessing/    # 文档解析和提取
│   ├── indexing/         # 索引管理（重复造轮）
│   ├── matching/         # 匹配层
│   └── workflows/        # 工作流层
```

**新设计**（基于 DataSource）：
```
requirement-tracing/
├── datasource/           # Git submodule 或依赖
├── src/
│   ├── sources/          # 扩展 DataSource（需求和测试用例）
│   │   ├── requirement.py   # RequirementDataSource
│   │   └── testcase.py      # TestCaseDataSource
│   ├── matching/         # 匹配层（保持不变）
│   ├── workflows/        # 工作流层（保持不变）
│   └── cli/              # CLI（扩展 datasource CLI）
```

### 2.2 数据源扩展

#### 2.2.1 RequirementDataSource

继承 `BaseDataSource`，实现需求文档的处理：

```python
# src/sources/requirement.py

from datasource.core.sources.base import BaseDataSource
from datasource.core.models import SourceConfig
from llama_index.core import Document
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any

class RequirementDataSource(BaseDataSource):
    """需求文档数据源
    
    支持：
    - PDF/Excel 需求文档解析（MinerU）
    - LLM 提取结构化需求
    - 版本管理
    """
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.version = config.options.get("version", "unknown")
        
        # 初始化 MinerU 解析器
        from ..preprocessing.parsers import MinerUParser
        self.parser = MinerUParser()
        
        # 初始化需求提取器
        from ..preprocessing.extractors import RequirementExtractor
        self.extractor = RequirementExtractor(llm=self._get_llm())
    
    def fetch_raw(
        self, 
        raw_dir: Path, 
        since: Optional[str] = None
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """抓取原始需求文档
        
        Args:
            raw_dir: 原始数据存储目录
            since: 增量同步起始时间（ISO格式）
        
        Yields:
            (文档ID, 原始数据) 元组
        """
        doc_path = Path(self.config.path)
        
        # 遍历所有需求文档
        for file_path in doc_path.glob("**/*"):
            if file_path.suffix.lower() not in ['.pdf', '.xlsx', '.xls']:
                continue
            
            # 增量同步：检查文件修改时间
            if since:
                from datetime import datetime
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                since_dt = datetime.fromisoformat(since)
                if file_mtime < since_dt:
                    continue
            
            # 使用 MinerU 解析文档
            try:
                parsed = self.parser.parse(file_path)
                
                # 生成文档ID（文件名 + 版本号）
                doc_id = f"{file_path.stem}_{self.version}"
                
                # 保存原始数据
                raw_file = raw_dir / f"{self._sanitize_filename(doc_id)}.json"
                import json
                raw_file.write_text(
                    json.dumps(parsed, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                
                yield doc_id, parsed
                
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path}: {e}")
                continue
    
    def build_document(
        self,
        item_id: str,
        raw_data: Dict[str, Any],
        assets_dir: Path
    ) -> Document:
        """构建 LlamaIndex Document
        
        Args:
            item_id: 文档ID
            raw_data: 原始数据（MinerU 解析结果）
            assets_dir: 资源文件目录
        
        Returns:
            LlamaIndex Document
        """
        # 使用 LLM 提取结构化需求
        requirements = self.extractor.extract(
            markdown_content=raw_data['content'],
            metadata=raw_data['metadata']
        )
        
        # 合并所有需求为一个 Document
        # （或者每个需求生成一个 Document，取决于粒度需求）
        all_text = "\n\n".join([
            f"# {req.title}\n{req.description}"
            for req in requirements
        ])
        
        # 构建元数据
        metadata = {
            "doc_type": "requirement",
            "source_file": raw_data['metadata']['file_name'],
            "version": self.version,
            "format": raw_data['metadata']['format'],
            "requirement_count": len(requirements),
            "requirements": [
                {
                    "title": req.title,
                    "type": req.type,
                    "keywords": req.keywords,
                    "chapter": req.source.get("chapter", "")
                }
                for req in requirements
            ]
        }
        
        return Document(
            text=all_text,
            metadata=metadata,
            id_=item_id
        )
```

#### 2.2.2 TestCaseDataSource

```python
# src/sources/testcase.py

from datasource.core.sources.base import BaseDataSource
from datasource.core.models import SourceConfig
from llama_index.core import Document
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any

class TestCaseDataSource(BaseDataSource):
    """测试用例数据源
    
    支持：
    - Python 测试用例解析（AST）
    - LLM 生成摘要
    - 路径元数据提取
    """
    
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        
        # 初始化测试用例提取器
        from ..preprocessing.extractors import TestCaseExtractor
        self.extractor = TestCaseExtractor(
            llm=self._get_llm(),
            testcase_root=Path(config.path)
        )
    
    def fetch_raw(
        self, 
        raw_dir: Path, 
        since: Optional[str] = None
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """抓取原始测试用例
        
        Args:
            raw_dir: 原始数据存储目录
            since: 增量同步起始时间
        
        Yields:
            (测试用例ID, 原始数据) 元组
        """
        testcase_root = Path(self.config.path)
        
        # 遍历所有 Python 文件
        for file_path in testcase_root.rglob("*.py"):
            # 增量同步：检查文件修改时间
            if since:
                from datetime import datetime
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                since_dt = datetime.fromisoformat(since)
                if file_mtime < since_dt:
                    continue
            
            # 读取代码
            try:
                code = file_path.read_text(encoding="utf-8")
                
                # 生成测试用例ID（相对路径）
                relative_path = file_path.relative_to(testcase_root)
                tc_id = str(relative_path).replace("\\", "/")
                
                # 保存原始数据
                raw_data = {
                    "file_path": str(file_path),
                    "relative_path": tc_id,
                    "code": code
                }
                
                raw_file = raw_dir / f"{self._sanitize_filename(tc_id)}.json"
                import json
                raw_file.write_text(
                    json.dumps(raw_data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
                
                yield tc_id, raw_data
                
            except Exception as e:
                self.logger.error(f"Failed to read {file_path}: {e}")
                continue
    
    def build_document(
        self,
        item_id: str,
        raw_data: Dict[str, Any],
        assets_dir: Path
    ) -> Document:
        """构建 LlamaIndex Document
        
        Args:
            item_id: 测试用例ID
            raw_data: 原始数据（代码）
            assets_dir: 资源文件目录
        
        Returns:
            LlamaIndex Document
        """
        # 使用提取器分析测试用例
        testcase = self.extractor.extract(Path(raw_data['file_path']))
        
        # 构建文本（文件名 + 摘要）
        text = f"{testcase.file_name}\n\n{testcase.summary}"
        
        # 构建元数据
        metadata = {
            "doc_type": "testcase",
            "file_path": testcase.file_path,
            "file_name": testcase.file_name,
            "platform": testcase.platform,
            "category": testcase.category,
            "subcategory": testcase.subcategory,
            "keywords": testcase.keywords,
            "functions": testcase.functions
        }
        
        return Document(
            text=text,
            metadata=metadata,
            id_=item_id
        )
```

### 2.3 CLI 整合

扩展 `datasource` 的 CLI，添加 requirement-tracing 特定命令：

```python
# src/cli/main.py

import click
from datasource.cli import cli as ds_cli
from datasource.core.manager import SourceManager
from datasource.core.models import SourceConfig, SourceType

# 扩展 datasource CLI
@ds_cli.group()
def req_trace():
    """需求追溯相关命令"""
    pass

@req_trace.command()
@click.option('--req-docs', required=True, help='需求文档目录')
@click.option('--version', required=True, help='版本号')
def add_requirements(req_docs, version):
    """添加需求文档数据源"""
    manager = SourceManager()
    
    config = SourceConfig(
        name=f"requirements_{version}",
        type=SourceType.LOCAL,  # 注册为自定义类型
        path=req_docs,
        options={"version": version, "source_class": "RequirementDataSource"}
    )
    
    info = manager.add_source(config)
    click.echo(f"✓ 需求文档数据源已添加: {info.name}")

@req_trace.command()
@click.option('--testcases', required=True, help='测试用例目录')
def add_testcases(testcases):
    """添加测试用例数据源"""
    manager = SourceManager()
    
    config = SourceConfig(
        name="testcases",
        type=SourceType.LOCAL,
        path=testcases,
        options={"source_class": "TestCaseDataSource"}
    )
    
    info = manager.add_source(config)
    click.echo(f"✓ 测试用例数据源已添加: {info.name}")

@req_trace.command()
@click.argument('requirement_query')
@click.option('--version', help='需求版本')
@click.option('--platform', help='平台过滤')
def coverage(requirement_query, version, platform):
    """查询需求覆盖率"""
    from ..workflows import CoverageQueryWorkflow
    
    workflow = CoverageQueryWorkflow()
    result = workflow.query(
        requirement_query=requirement_query,
        version=version,
        platform=platform
    )
    
    # 输出结果
    click.echo(f"\n找到 {len(result.matches)} 个匹配的测试用例：\n")
    for match in result.matches:
        click.echo(f"  [{match.confidence.upper()}] {match.metadata['file_path']}")
        click.echo(f"    评分: {match.score:.2f}")
        click.echo(f"    原因: {match.match_reason}\n")

if __name__ == '__main__':
    ds_cli()
```

### 2.4 工作流层调整

工作流层使用 `SourceManager` 访问索引：

```python
# src/workflows/coverage_query.py

from datasource.core.manager import SourceManager
from ..matching.retriever import MultiStageRetriever

class CoverageQueryWorkflow:
    def __init__(self):
        self.manager = SourceManager()
    
    def query(
        self,
        requirement_query: str,
        version: str = None,
        platform: str = None
    ):
        """查询需求覆盖率
        
        Args:
            requirement_query: 需求查询（ID或关键词）
            version: 需求版本
            platform: 平台过滤
        
        Returns:
            匹配结果
        """
        # 1. 从需求数据源查询
        req_source_name = f"requirements_{version}" if version else "requirements_latest"
        req_results = self.manager.query(
            name=req_source_name,
            query=requirement_query,
            mode="hybrid",
            top_k=1
        )
        
        if not req_results:
            return {"error": "需求未找到"}
        
        req_doc = req_results[0]
        
        # 2. 使用多阶段检索器匹配测试用例
        retriever = MultiStageRetriever(
            vector_retriever=self._get_vector_retriever("testcases"),
            bm25_retriever=self._get_bm25_retriever("testcases")
        )
        
        matches = retriever.retrieve(
            query=req_doc['text'],
            top_k=10,
            filters={"platform": platform} if platform else None
        )
        
        return {
            "requirement": req_doc,
            "matches": matches
        }
    
    def _get_vector_retriever(self, source_name: str):
        """获取向量检索器"""
        # 从 datasource 加载索引
        from datasource.core.indexing.vector import VectorIndexer
        from datasource.core.paths import Paths
        
        paths = Paths()
        vector_dir = paths.indexes(source_name) / "vector"
        
        indexer = VectorIndexer()
        return indexer.load_index(vector_dir).as_retriever()
    
    def _get_bm25_retriever(self, source_name: str):
        """获取 BM25 检索器"""
        from datasource.core.indexing.bm25 import BM25Indexer
        from datasource.core.paths import Paths
        
        paths = Paths()
        bm25_dir = paths.indexes(source_name) / "bm25"
        
        indexer = BM25Indexer()
        return indexer.load_index(bm25_dir)
```

---

## 3. 目录结构调整

```
requirement-tracing/
├── datasource/                    # Git submodule（datasource 项目）
│   ├── datasource/
│   │   ├── core/
│   │   │   ├── models.py
│   │   │   ├── manager.py
│   │   │   ├── sources/
│   │   │   └── indexing/
│   │   └── cli.py
│   └── README.md
│
├── src/
│   ├── sources/                   # 扩展数据源
│   │   ├── __init__.py
│   │   ├── requirement.py         # RequirementDataSource
│   │   └── testcase.py            # TestCaseDataSource
│   │
│   ├── preprocessing/             # 预处理工具（被 sources 使用）
│   │   ├── parsers/
│   │   │   └── mineru_parser.py
│   │   └── extractors/
│   │       ├── requirement_extractor.py
│   │       └── testcase_extractor.py
│   │
│   ├── matching/                  # 匹配层（保持不变）
│   │   ├── retriever.py
│   │   └── llm_judge.py
│   │
│   ├── workflows/                 # 工作流层（使用 SourceManager）
│   │   ├── coverage_query.py
│   │   ├── traceability_query.py
│   │   ├── gap_analysis.py
│   │   └── version_diff.py
│   │
│   └── cli/                       # CLI（扩展 datasource CLI）
│       └── main.py
│
├── data/                          # 数据目录（datasource 标准结构）
│   ├── requirements_v1.0/
│   │   ├── config.yaml
│   │   ├── raw/
│   │   ├── documents/
│   │   ├── indexes/
│   │   │   ├── vector/
│   │   │   └── bm25/
│   │   └── manifest.json
│   └── testcases/
│       ├── config.yaml
│       ├── raw/
│       ├── documents/
│       ├── indexes/
│       └── manifest.json
│
├── docs/design/
├── README.md
└── PLAN.md
```

---

## 4. 优势分析

### 4.1 代码复用

**避免重复实现**：
- ✅ 索引管理（Vector + BM25）
- ✅ 配置持久化
- ✅ 目录结构管理
- ✅ 增量同步机制
- ✅ CLI 框架
- ✅ 错误处理和日志

**预计减少代码量**：~40%（约 2000 行代码）

### 4.2 功能增强

**自动获得**：
- ✅ 混合检索（Vector + BM25）
- ✅ 增量同步（避免重复处理）
- ✅ 统一的配置管理
- ✅ 标准化的目录结构
- ✅ 完善的错误处理

**未来扩展**：
- 支持 Jira 需求（如果需求存储在 Jira）
- 支持 Confluence 文档
- 支持其他数据源

### 4.3 维护性

**统一维护**：
- 索引相关的 bug 修复只需在 datasource 中进行
- 性能优化可以惠及所有项目
- 新功能（如新的检索算法）自动可用

---

## 5. 实施步骤

### Step 1: 添加 datasource 依赖

```bash
# 方式1: Git submodule
cd requirement-tracing
git submodule add ../datasource datasource

# 方式2: 作为 Python 包依赖
# 在 requirements.txt 中添加
# -e ../datasource
```

### Step 2: 实现自定义数据源

```bash
# 创建目录
mkdir -p src/sources

# 实现 RequirementDataSource
# 实现 TestCaseDataSource
```

### Step 3: 注册自定义数据源

```python
# 在 datasource/core/manager.py 中添加
from requirement_tracing.sources import RequirementDataSource, TestCaseDataSource

# 或者通过插件机制注册
```

### Step 4: 调整工作流层

```python
# 使用 SourceManager 替代自定义索引管理
from datasource.core.manager import SourceManager
```

### Step 5: 扩展 CLI

```python
# 扩展 datasource CLI
# 添加 req-trace 命令组
```

### Step 6: 更新文档

```markdown
# 更新 README.md
# 更新设计文档
# 更新 PLAN.md
```

---

## 6. 风险和应对

### 风险1: datasource 不支持某些特性

**应对**: 
- 优先在 datasource 中实现通用功能
- 特殊功能在 requirement-tracing 中实现

### 风险2: 版本管理复杂度

**应对**:
- 使用 Git submodule 或明确的版本依赖
- 定期同步 datasource 更新

### 风险3: 学习成本

**应对**:
- 提供清晰的集成文档
- 示例代码和最佳实践

---

## 7. 下一步行动

1. ✅ 确认整合方案
2. 添加 datasource 为 submodule
3. 实现 RequirementDataSource
4. 实现 TestCaseDataSource
5. 调整工作流层
6. 更新 CLI
7. 更新文档

**预计节省时间**: 2-3周（原计划 15周 → 12-13周）
