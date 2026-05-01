# 项目结构和开发指南

## 1. 项目目录结构

```
requirement-tracing/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── models.py                 # 数据模型定义
│   ├── config.py                 # 配置管理
│   │
│   ├── preprocessing/            # 预处理层
│   │   ├── __init__.py
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   └── mineru_parser.py  # MinerU文档解析器
│   │   ├── extractors/
│   │   │   ├── __init__.py
│   │   │   ├── requirement_extractor.py  # 需求提取器
│   │   │   └── testcase_extractor.py     # Test Case提取器
│   │   └── document_builder.py   # Document构建器
│   │
│   ├── indexing/                 # 索引层
│   │   ├── __init__.py
│   │   ├── requirement_index.py  # 需求索引管理器
│   │   ├── testcase_index.py     # Test Case索引管理器
│   │   └── version_manager.py    # 版本管理器
│   │
│   ├── matching/                 # 匹配层
│   │   ├── __init__.py
│   │   ├── retriever.py          # 多阶段检索器
│   │   ├── keyword_matcher.py    # 关键词匹配器
│   │   ├── semantic_ranker.py    # 语义排序器
│   │   └── llm_judge.py          # LLM判断器
│   │
│   ├── workflows/                # 工作流层
│   │   ├── __init__.py
│   │   ├── coverage_query.py     # 需求覆盖率查询
│   │   ├── traceability_query.py # 代码追溯查询
│   │   ├── gap_analysis.py       # 差距分析
│   │   └── version_diff.py       # 版本对比
│   │
│   ├── cli/                      # CLI接口
│   │   ├── __init__.py
│   │   └── main.py               # CLI主程序
│   │
│   ├── api/                      # Web API
│   │   ├── __init__.py
│   │   ├── server.py             # FastAPI服务器
│   │   ├── auth.py               # 认证模块
│   │   └── models.py             # API数据模型
│   │
│   └── utils/                    # 工具模块
│       ├── __init__.py
│       ├── logger.py             # 日志工具
│       ├── cache.py              # 缓存工具
│       └── text_utils.py         # 文本处理工具
│
├── prompts/                      # LLM提示词模板
│   ├── requirement_extraction.txt
│   ├── testcase_summary.txt
│   └── llm_judge.txt
│
├── tests/                        # 测试代码
│   ├── __init__.py
│   ├── conftest.py               # pytest配置
│   ├── test_preprocessing/
│   │   ├── test_mineru_parser.py
│   │   ├── test_requirement_extractor.py
│   │   └── test_testcase_extractor.py
│   ├── test_indexing/
│   │   ├── test_requirement_index.py
│   │   ├── test_testcase_index.py
│   │   └── test_version_manager.py
│   ├── test_matching/
│   │   ├── test_retriever.py
│   │   └── test_llm_judge.py
│   └── test_workflows/
│       ├── test_coverage_query.py
│       ├── test_traceability_query.py
│       ├── test_gap_analysis.py
│       └── test_version_diff.py
│
├── examples/                     # 示例代码
│   ├── basic_usage.py
│   ├── custom_workflow.py
│   └── api_client.py
│
├── docs/                         # 文档
│   ├── design/                   # 设计文档
│   │   ├── 01-overview.md
│   │   ├── 02-preprocessing.md
│   │   ├── 03-indexing.md
│   │   ├── 04-matching.md
│   │   ├── 05-workflows.md
│   │   ├── 06-api-cli.md
│   │   └── 07-deployment.md
│   ├── user-guide.md             # 用户指南
│   ├── api-reference.md          # API参考
│   └── development.md            # 开发指南
│
├── scripts/                      # 脚本工具
│   ├── build_index.sh
│   ├── backup.sh
│   ├── restore.sh
│   └── migrate.py
│
├── data/                         # 数据目录（不提交到Git）
│   ├── requirements/             # 原始需求文档
│   ├── testcases/                # 原始Test Case
│   └── indexes/                  # 生成的索引
│       ├── requirements_v1.0/
│       │   ├── vector/
│       │   ├── bm25.pkl
│       │   └── metadata.json
│       └── testcases/
│           ├── vector/
│           ├── bm25.pkl
│           └── metadata.json
│
├── .github/                      # GitHub配置
│   └── workflows/
│       ├── ci.yml                # CI/CD配置
│       └── weekly-report.yml     # 定期报告
│
├── docker/                       # Docker配置
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── k8s/                          # Kubernetes配置
│   ├── deployment.yaml
│   ├── service.yaml
│   └── configmap.yaml
│
├── .gitignore
├── .env.example                  # 环境变量示例
├── config.yaml.example           # 配置文件示例
├── requirements.txt              # Python依赖
├── setup.py                      # 安装配置
├── pyproject.toml                # 项目元数据
├── README.md                     # 项目说明
└── LICENSE                       # 许可证
```

---

## 2. 核心模块说明

### 2.1 数据模型 (models.py)

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Requirement:
    """需求数据模型"""
    id: str
    title: str
    description: str
    type: str  # "功能需求" | "性能需求" | "安全需求"
    keywords: List[str]
    source_file: str
    version: str
    chapter: Optional[str] = None
    created_at: datetime = None

@dataclass
class TestCase:
    """Test Case数据模型"""
    file_path: str
    file_name: str
    platform: str  # "Windows" | "Linux"
    category: str  # "Common" | "Customer"
    subcategory: str  # "01_Performance" | "02_Compatibility"
    summary: str
    keywords: List[str]
    functions: List[str]
    created_at: datetime = None

@dataclass
class MatchResult:
    """匹配结果数据模型"""
    doc_id: str
    text: str
    metadata: dict
    score: float
    confidence: str  # "high" | "medium" | "low"
    match_reason: str
```

### 2.2 配置管理 (config.py)

```python
from pathlib import Path
from dataclasses import dataclass
import yaml

@dataclass
class LLMConfig:
    model_name: str
    base_url: str
    temperature: float
    max_tokens: int
    timeout: int = 60

@dataclass
class EmbeddingConfig:
    model_name: str
    device: str
    batch_size: int

@dataclass
class RetrieverConfig:
    bm25_top_k: int
    vector_top_k: int
    llm_top_k: int
    bm25_weight: float
    vector_weight: float
    path_weight: float
    high_confidence_threshold: float
    medium_confidence_threshold: float

@dataclass
class Config:
    project_root: Path
    index_dir: Path
    cache_dir: Path
    llm: LLMConfig
    embedding: EmbeddingConfig
    retriever: RetrieverConfig
    
    @classmethod
    def load(cls, config_path: str):
        """从YAML文件加载配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(
            project_root=Path(data['project_root']),
            index_dir=Path(data['index_dir']),
            cache_dir=Path(data['cache_dir']),
            llm=LLMConfig(**data['llm']),
            embedding=EmbeddingConfig(**data['embedding']),
            retriever=RetrieverConfig(**data['retriever'])
        )
```

---

## 3. 开发环境设置

### 3.1 安装开发依赖

```bash
# 克隆项目
git clone https://github.com/your-org/requirement-tracing.git
cd requirement-tracing

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"

# 安装pre-commit hooks
pre-commit install
```

### 3.2 依赖管理

```python
# setup.py

from setuptools import setup, find_packages

setup(
    name="requirement-tracing",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "llama-index>=0.9.0",
        "llama-index-embeddings-huggingface>=0.1.0",
        "llama-index-llms-ollama>=0.1.0",
        "magic-pdf>=0.6.0",  # MinerU
        "click>=8.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "rank-bm25>=0.2.2",
        "torch>=2.0.0",
        "transformers>=4.30.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "req-trace=src.cli.main:cli",
        ],
    },
)
```

### 3.3 代码风格

```python
# .flake8
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,build,dist
ignore = E203,W503

# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 4. 测试策略

### 4.1 单元测试

```python
# tests/test_preprocessing/test_requirement_extractor.py

import pytest
from src.preprocessing.extractors import RequirementExtractor

@pytest.fixture
def extractor():
    return RequirementExtractor(llm_config)

def test_extract_requirements(extractor):
    """测试需求提取"""
    markdown_text = """
    # 1. 用户登录功能
    系统应支持用户名密码登录...
    """
    
    requirements = extractor.extract(markdown_text, "test.pdf", "v1.0")
    
    assert len(requirements) > 0
    assert requirements[0].title == "用户登录功能"
    assert "登录" in requirements[0].keywords

def test_extract_with_empty_input(extractor):
    """测试空输入"""
    requirements = extractor.extract("", "test.pdf", "v1.0")
    assert len(requirements) == 0
```

### 4.2 集成测试

```python
# tests/test_workflows/test_coverage_query.py

import pytest
from src.workflows import CoverageQueryWorkflow

@pytest.fixture
def workflow(config):
    return CoverageQueryWorkflow(config)

def test_coverage_query_e2e(workflow):
    """端到端测试：需求覆盖率查询"""
    # 1. 构建测试索引
    workflow.build_test_index()
    
    # 2. 执行查询
    result = workflow.query("用户登录功能")
    
    # 3. 验证结果
    assert result is not None
    assert len(result.matches) > 0
    assert result.matches[0].confidence in ["high", "medium", "low"]
```

### 4.3 性能测试

```python
# tests/test_performance.py

import pytest
import time

def test_query_performance(workflow):
    """测试查询性能"""
    start = time.time()
    result = workflow.query("性能测试需求")
    duration = time.time() - start
    
    # 查询应在2秒内完成
    assert duration < 2.0

def test_batch_query_performance(workflow):
    """测试批量查询性能"""
    queries = ["需求1", "需求2", "需求3", "需求4", "需求5"]
    
    start = time.time()
    results = [workflow.query(q) for q in queries]
    duration = time.time() - start
    
    # 平均每个查询应在1秒内完成
    assert duration / len(queries) < 1.0
```

### 4.4 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_preprocessing/test_requirement_extractor.py

# 运行带覆盖率报告
pytest --cov=src --cov-report=html

# 运行性能测试
pytest tests/test_performance.py -v
```

---

## 5. 开发工作流

### 5.1 分支策略

```
main          # 主分支，稳定版本
├── develop   # 开发分支
│   ├── feature/preprocessing  # 功能分支
│   ├── feature/indexing
│   └── bugfix/issue-123       # 修复分支
```

### 5.2 提交规范

```bash
# 提交格式
<type>(<scope>): <subject>

# 类型
feat:     新功能
fix:      修复bug
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构
test:     测试相关
chore:    构建/工具相关

# 示例
feat(preprocessing): add MinerU parser
fix(indexing): fix version comparison bug
docs(api): update API documentation
```

### 5.3 Pull Request流程

```markdown
## PR标题
feat(matching): implement multi-stage retriever

## 描述
实现了三阶段检索器：
1. BM25关键词召回
2. 向量语义重排序
3. LLM精确判断

## 测试
- [x] 单元测试通过
- [x] 集成测试通过
- [x] 性能测试通过

## 相关Issue
Closes #42
```

---

## 6. 调试技巧

### 6.1 日志调试

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 在代码中添加日志
logger = logging.getLogger(__name__)
logger.debug(f"Query: {query}")
logger.info(f"Found {len(results)} matches")
logger.warning(f"Low confidence: {score}")
logger.error(f"Failed to load index: {e}")
```

### 6.2 交互式调试

```python
# 使用pdb调试
import pdb; pdb.set_trace()

# 使用ipdb（更友好）
import ipdb; ipdb.set_trace()

# 在pytest中使用
pytest --pdb  # 失败时进入调试器
pytest -s     # 显示print输出
```

### 6.3 性能分析

```python
# 使用cProfile
python -m cProfile -o profile.stats src/cli/main.py coverage "需求1"

# 分析结果
python -m pstats profile.stats
>>> sort time
>>> stats 10

# 使用line_profiler
@profile
def slow_function():
    # ...

kernprof -l -v script.py
```

---

## 7. 常见开发任务

### 7.1 添加新的提取器

```python
# 1. 创建新文件
# src/preprocessing/extractors/custom_extractor.py

from .base import BaseExtractor

class CustomExtractor(BaseExtractor):
    def extract(self, text: str) -> List[Document]:
        # 实现提取逻辑
        pass

# 2. 添加测试
# tests/test_preprocessing/test_custom_extractor.py

def test_custom_extractor():
    extractor = CustomExtractor()
    result = extractor.extract("test")
    assert result is not None

# 3. 更新文档
# docs/design/02-preprocessing.md
```

### 7.2 添加新的工作流

```python
# 1. 创建新文件
# src/workflows/custom_workflow.py

class CustomWorkflow:
    def __init__(self, config):
        self.config = config
    
    def execute(self, **kwargs):
        # 实现工作流逻辑
        pass

# 2. 添加CLI命令
# src/cli/main.py

@cli.command()
def custom(**kwargs):
    """自定义工作流"""
    workflow = CustomWorkflow(config)
    result = workflow.execute(**kwargs)
    print(result)

# 3. 添加API端点
# src/api/server.py

@app.post("/api/custom")
async def custom_endpoint(request: CustomRequest):
    workflow = workflows['custom']
    return workflow.execute(**request.dict())
```

### 7.3 优化检索性能

```python
# 1. 添加缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def retrieve_cached(query: str, filters: str):
    return self.retrieve(query, json.loads(filters))

# 2. 批量处理
def retrieve_batch(queries: List[str]):
    # 批量向量化
    embeddings = self.embed_model.get_text_embedding_batch(queries)
    
    # 批量查询
    results = [self._search(emb) for emb in embeddings]
    return results

# 3. 并行处理
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(self.retrieve, queries))
```

---

## 8. 发布流程

### 8.1 版本号规范

遵循语义化版本（Semantic Versioning）：
- **主版本号**：不兼容的API变更
- **次版本号**：向后兼容的功能新增
- **修订号**：向后兼容的问题修正

```
v0.1.0 -> v0.2.0 (新增功能)
v0.2.0 -> v0.2.1 (修复bug)
v0.2.1 -> v1.0.0 (重大变更)
```

### 8.2 发布检查清单

```markdown
- [ ] 所有测试通过
- [ ] 代码覆盖率 > 80%
- [ ] 文档已更新
- [ ] CHANGELOG已更新
- [ ] 版本号已更新
- [ ] 创建Git tag
- [ ] 构建Docker镜像
- [ ] 发布到PyPI（可选）
```

### 8.3 发布命令

```bash
# 1. 更新版本号
# 编辑 setup.py 和 pyproject.toml

# 2. 更新CHANGELOG
# 编辑 CHANGELOG.md

# 3. 提交变更
git add .
git commit -m "chore: bump version to v0.2.0"

# 4. 创建tag
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# 5. 构建Docker镜像
docker build -t req-trace:v0.2.0 .
docker push your-registry/req-trace:v0.2.0

# 6. 发布到PyPI（可选）
python setup.py sdist bdist_wheel
twine upload dist/*
```

---

## 9. 贡献指南

### 9.1 如何贡献

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 9.2 代码审查标准

- 代码风格符合规范（black + flake8）
- 所有测试通过
- 代码覆盖率不降低
- 有清晰的注释和文档
- 性能无明显下降

---

## 10. 资源链接

- **项目仓库**: https://github.com/your-org/requirement-tracing
- **文档**: https://req-trace.readthedocs.io
- **问题追踪**: https://github.com/your-org/requirement-tracing/issues
- **讨论区**: https://github.com/your-org/requirement-tracing/discussions
- **LlamaIndex文档**: https://docs.llamaindex.ai
- **MinerU文档**: https://github.com/opendatalab/MinerU
