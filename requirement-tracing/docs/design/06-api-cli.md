# API和CLI设计

## 1. 概述

系统提供两种交互方式：
- **CLI（命令行界面）**：适合本地使用和脚本自动化
- **Web API（REST API）**：适合团队协作和系统集成

---

## 2. CLI设计

### 2.1 命令结构

```bash
req-trace <command> [options]
```

### 2.2 核心命令

#### 2.2.1 索引管理

```bash
# 构建索引
req-trace index build \
  --req-docs ./docs \
  --testcases ./TestCase \
  --version v1.0

# 列出所有索引版本
req-trace index list

# 删除索引
req-trace index delete --version v1.0
```

#### 2.2.2 需求覆盖率查询

```bash
# 基本查询
req-trace coverage "用户登录功能"

# 带过滤条件
req-trace coverage "性能测试" \
  --platform Windows \
  --category Common

# 启用LLM判断
req-trace coverage "REQ-001" --llm-judge

# 输出到文件
req-trace coverage "用户登录" --output result.json
```

#### 2.2.3 代码追溯查询

```bash
# 基本查询
req-trace trace "Windows/Common/01_Performance/test_boot.py"

# 启用LLM判断
req-trace trace "test_login.py" --llm-judge

# 输出到文件
req-trace trace "test_login.py" --output result.json
```

#### 2.2.4 差距分析

```bash
# 生成差距分析报告
req-trace gap --output gap_report.xlsx

# 指定版本
req-trace gap --version v1.0 --output report.xlsx

# 设置置信度阈值
req-trace gap --min-confidence high --output report.xlsx
```

#### 2.2.5 版本对比

```bash
# 对比两个版本
req-trace diff v1.0 v1.1

# 输出到文件
req-trace diff v1.0 v1.1 --output diff_report.json
```

### 2.3 全局选项

```bash
--config <path>     # 配置文件路径
--verbose           # 详细输出
--quiet             # 静默模式
--help              # 帮助信息
```

### 2.4 CLI实现

```python
# src/cli/main.py

import click
from pathlib import Path
from ..config import Config
from ..workflows import (
    CoverageQueryWorkflow,
    TraceabilityQueryWorkflow,
    GapAnalysisWorkflow,
    VersionDiffWorkflow
)

@click.group()
@click.option('--config', type=click.Path(exists=True), help='配置文件路径')
@click.option('--verbose', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config, verbose):
    """需求追溯系统 CLI"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config.load(config) if config else Config.load_default()
    ctx.obj['verbose'] = verbose

@cli.command()
@click.argument('requirement_query')
@click.option('--platform', type=click.Choice(['Windows', 'Linux']))
@click.option('--category', type=click.Choice(['Common', 'Customer']))
@click.option('--llm-judge', is_flag=True)
@click.option('--output', type=click.Path())
@click.pass_context
def coverage(ctx, requirement_query, platform, category, llm_judge, output):
    """查询需求覆盖率"""
    config = ctx.obj['config']
    
    # 初始化工作流
    workflow = CoverageQueryWorkflow(config)
    
    # 执行查询
    result = workflow.query(
        requirement_query=requirement_query,
        platform=platform,
        category=category,
        use_llm_judge=llm_judge
    )
    
    # 输出结果
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        click.echo(f"结果已保存到: {output}")
    else:
        _print_coverage_result(result)

@cli.command()
@click.argument('testcase_path')
@click.option('--llm-judge', is_flag=True)
@click.option('--output', type=click.Path())
@click.pass_context
def trace(ctx, testcase_path, llm_judge, output):
    """查询Test Case对应的需求"""
    config = ctx.obj['config']
    
    workflow = TraceabilityQueryWorkflow(config)
    result = workflow.query(testcase_path, use_llm_judge=llm_judge)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        click.echo(f"结果已保存到: {output}")
    else:
        _print_trace_result(result)

@cli.command()
@click.option('--version', help='需求文档版本')
@click.option('--min-confidence', type=click.Choice(['high', 'medium', 'low']), default='medium')
@click.option('--output', type=click.Path(), required=True)
@click.pass_context
def gap(ctx, version, min_confidence, output):
    """生成差距分析报告"""
    config = ctx.obj['config']
    
    workflow = GapAnalysisWorkflow(config)
    report = workflow.analyze(version=version, min_confidence=min_confidence)
    workflow.export_to_excel(report, output)
    
    click.echo(f"报告已保存到: {output}")
    click.echo(f"覆盖率: {report.coverage_rate*100:.1f}%")

@cli.command()
@click.argument('v1')
@click.argument('v2')
@click.option('--output', type=click.Path())
@click.pass_context
def diff(ctx, v1, v2, output):
    """对比两个版本"""
    config = ctx.obj['config']
    
    workflow = VersionDiffWorkflow(config)
    result = workflow.diff(v1, v2)
    
    if output:
        import json
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        click.echo(f"结果已保存到: {output}")
    else:
        _print_diff_result(result)

@cli.group()
def index():
    """索引管理命令"""
    pass

@index.command('build')
@click.option('--req-docs', type=click.Path(exists=True), required=True)
@click.option('--testcases', type=click.Path(exists=True), required=True)
@click.option('--version', required=True)
@click.pass_context
def build_index(ctx, req_docs, testcases, version):
    """构建索引"""
    config = ctx.obj['config']
    
    from ..preprocessing import DocumentPreprocessor
    from ..indexing import RequirementIndex, TestCaseIndex
    
    click.echo("开始构建索引...")
    
    # 预处理
    preprocessor = DocumentPreprocessor(config)
    req_documents = preprocessor.process_requirements(req_docs, version)
    tc_documents = preprocessor.process_testcases(testcases)
    
    # 构建索引
    req_index = RequirementIndex(config.index_dir, version, config.embed_model)
    req_index.build(req_documents)
    req_index.save()
    
    tc_index = TestCaseIndex(config.index_dir, config.embed_model)
    tc_index.build(tc_documents)
    tc_index.save()
    
    click.echo("索引构建完成！")

@index.command('list')
@click.pass_context
def list_index(ctx):
    """列出所有索引版本"""
    config = ctx.obj['config']
    
    from ..indexing import VersionManager
    version_mgr = VersionManager(config.index_dir)
    versions = version_mgr.get_all_versions()
    
    if not versions:
        click.echo("没有找到索引")
        return
    
    click.echo("可用的索引版本：")
    for v in versions:
        info = version_mgr.get_version_info(v)
        click.echo(f"  - {v} (创建时间: {info['created_at']})")

if __name__ == '__main__':
    cli()
```

---

## 3. Web API设计

### 3.1 API架构

```
FastAPI Server
├── /api/coverage          # 需求覆盖率查询
├── /api/trace             # 代码追溯查询
├── /api/gap               # 差距分析
├── /api/diff              # 版本对比
├── /api/versions          # 版本列表
└── /api/health            # 健康检查
```

### 3.2 API端点

#### 3.2.1 需求覆盖率查询

**请求**
```http
POST /api/coverage
Content-Type: application/json

{
  "requirement_query": "用户登录功能",
  "platform": "Windows",
  "category": "Common",
  "use_llm_judge": false,
  "top_k": 10
}
```

**响应**
```json
{
  "query": "用户登录功能",
  "total_matches": 5,
  "high_confidence": [
    {
      "file_path": "Windows/Common/test_login.py",
      "summary": "测试用户登录功能...",
      "confidence": "high",
      "score": 0.85,
      "match_reason": "关键词匹配：用户登录、密码验证"
    }
  ],
  "medium_confidence": [...],
  "low_confidence": [...]
}
```

#### 3.2.2 代码追溯查询

**请求**
```http
POST /api/trace
Content-Type: application/json

{
  "testcase_path": "Windows/Common/test_login.py",
  "use_llm_judge": false,
  "top_k": 5
}
```

**响应**
```json
{
  "testcase": {
    "file_path": "Windows/Common/test_login.py",
    "platform": "Windows",
    "category": "Common",
    "summary": "测试用户登录功能..."
  },
  "requirements": [
    {
      "title": "用户登录功能",
      "description": "系统应支持用户名密码登录...",
      "type": "功能需求",
      "confidence": "high",
      "score": 0.85
    }
  ]
}
```

#### 3.2.3 差距分析

**请求**
```http
POST /api/gap
Content-Type: application/json

{
  "version": "v1.0",
  "min_confidence": "medium"
}
```

**响应**
```json
{
  "summary": {
    "total_requirements": 50,
    "total_testcases": 120,
    "coverage_rate": 0.85,
    "uncovered_count": 8
  },
  "uncovered_requirements": [...],
  "orphan_testcases": [...],
  "over_tested_requirements": [...]
}
```

#### 3.2.4 版本对比

**请求**
```http
POST /api/diff
Content-Type: application/json

{
  "v1": "v1.0",
  "v2": "v1.1"
}
```

**响应**
```json
{
  "version_old": "v1.0",
  "version_new": "v1.1",
  "summary": {
    "added_count": 5,
    "removed_count": 2,
    "modified_count": 8
  },
  "added_requirements": [...],
  "removed_requirements": [...],
  "coverage_changes": [...]
}
```

#### 3.2.5 版本列表

**请求**
```http
GET /api/versions
```

**响应**
```json
{
  "versions": [
    {
      "version": "v1.0",
      "created_at": "2024-01-01T10:00:00",
      "description": "初始版本"
    },
    {
      "version": "v1.1",
      "created_at": "2024-02-01T10:00:00",
      "description": "新增性能需求"
    }
  ]
}
```

#### 3.2.6 健康检查

**请求**
```http
GET /api/health
```

**响应**
```json
{
  "status": "healthy",
  "indexes_loaded": true,
  "version": "0.1.0"
}
```

### 3.3 API实现

```python
# src/api/server.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Requirement Tracing API", version="0.1.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class CoverageQueryRequest(BaseModel):
    requirement_query: str
    platform: Optional[str] = None
    category: Optional[str] = None
    use_llm_judge: bool = False
    top_k: int = 10

class TraceabilityQueryRequest(BaseModel):
    testcase_path: str
    use_llm_judge: bool = False
    top_k: int = 5

class GapAnalysisRequest(BaseModel):
    version: Optional[str] = None
    min_confidence: str = "medium"

class VersionDiffRequest(BaseModel):
    v1: str
    v2: str

# 全局组件（启动时初始化）
config = None
workflows = {}

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化组件"""
    global config, workflows
    
    from ..config import Config
    from ..workflows import (
        CoverageQueryWorkflow,
        TraceabilityQueryWorkflow,
        GapAnalysisWorkflow,
        VersionDiffWorkflow
    )
    
    config = Config.load_default()
    
    workflows['coverage'] = CoverageQueryWorkflow(config)
    workflows['trace'] = TraceabilityQueryWorkflow(config)
    workflows['gap'] = GapAnalysisWorkflow(config)
    workflows['diff'] = VersionDiffWorkflow(config)

@app.post("/api/coverage")
async def query_coverage(request: CoverageQueryRequest):
    """查询需求覆盖率"""
    try:
        result = workflows['coverage'].query(
            requirement_query=request.requirement_query,
            platform=request.platform,
            category=request.category,
            use_llm_judge=request.use_llm_judge,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trace")
async def query_traceability(request: TraceabilityQueryRequest):
    """查询Test Case对应的需求"""
    try:
        result = workflows['trace'].query(
            testcase_path=request.testcase_path,
            use_llm_judge=request.use_llm_judge,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gap")
async def analyze_gap(request: GapAnalysisRequest):
    """生成差距分析报告"""
    try:
        result = workflows['gap'].analyze(
            version=request.version,
            min_confidence=request.min_confidence
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/diff")
async def compare_versions(request: VersionDiffRequest):
    """对比两个版本"""
    try:
        result = workflows['diff'].diff(request.v1, request.v2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/versions")
async def list_versions():
    """列出所有索引版本"""
    try:
        from ..indexing import VersionManager
        version_mgr = VersionManager(config.index_dir)
        versions = version_mgr.get_all_versions()
        
        return {
            "versions": [
                {
                    "version": v,
                    **version_mgr.get_version_info(v)
                }
                for v in versions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "indexes_loaded": workflows is not None,
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 4. 配置管理

### 4.1 配置文件格式

```yaml
# config.yaml

# 目录配置
project_root: .
index_dir: ./indexes
cache_dir: ./.cache

# LLM配置
llm:
  model_name: qwen2.5:14b
  base_url: http://localhost:11434
  temperature: 0.1
  max_tokens: 2048

# Embedding配置
embedding:
  model_name: BAAI/bge-large-zh-v1.5
  device: cuda
  batch_size: 32

# 检索器配置
retriever:
  bm25_top_k: 50
  vector_top_k: 20
  llm_top_k: 5
  bm25_weight: 0.3
  vector_weight: 0.5
  path_weight: 0.2
  high_confidence_threshold: 0.8
  medium_confidence_threshold: 0.6

# MinerU配置
mineru:
  output_format: markdown
  parse_images: false
```

### 4.2 配置加载

```python
# src/config.py

from pathlib import Path
from dataclasses import dataclass
import yaml

@dataclass
class Config:
    project_root: Path
    index_dir: Path
    cache_dir: Path
    llm_config: dict
    embedding_config: dict
    retriever_config: dict
    mineru_config: dict
    
    @classmethod
    def load(cls, config_path: str):
        """从YAML文件加载配置"""
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(
            project_root=Path(data['project_root']),
            index_dir=Path(data['index_dir']),
            cache_dir=Path(data['cache_dir']),
            llm_config=data['llm'],
            embedding_config=data['embedding'],
            retriever_config=data['retriever'],
            mineru_config=data['mineru']
        )
    
    @classmethod
    def load_default(cls):
        """加载默认配置"""
        default_path = Path.home() / '.req-trace' / 'config.yaml'
        if default_path.exists():
            return cls.load(str(default_path))
        else:
            return cls.create_default()
    
    @classmethod
    def create_default(cls):
        """创建默认配置"""
        return cls(
            project_root=Path.cwd(),
            index_dir=Path.cwd() / 'indexes',
            cache_dir=Path.cwd() / '.cache',
            llm_config={
                'model_name': 'qwen2.5:14b',
                'base_url': 'http://localhost:11434',
                'temperature': 0.1,
                'max_tokens': 2048
            },
            embedding_config={
                'model_name': 'BAAI/bge-large-zh-v1.5',
                'device': 'cuda',
                'batch_size': 32
            },
            retriever_config={
                'bm25_top_k': 50,
                'vector_top_k': 20,
                'llm_top_k': 5,
                'bm25_weight': 0.3,
                'vector_weight': 0.5,
                'path_weight': 0.2,
                'high_confidence_threshold': 0.8,
                'medium_confidence_threshold': 0.6
            },
            mineru_config={
                'output_format': 'markdown',
                'parse_images': False
            }
        )
```

---

## 5. 使用示例

### 5.1 CLI使用

```bash
# 1. 构建索引
req-trace index build \
  --req-docs ./docs/requirements \
  --testcases ./TestCase \
  --version v1.0

# 2. 查询需求覆盖率
req-trace coverage "用户登录功能" --platform Windows

# 3. 查询Test Case追溯
req-trace trace "Windows/Common/test_login.py"

# 4. 生成差距分析报告
req-trace gap --output gap_report.xlsx

# 5. 版本对比
req-trace diff v1.0 v1.1
```

### 5.2 API使用

```python
import requests

# 1. 查询需求覆盖率
response = requests.post('http://localhost:8000/api/coverage', json={
    "requirement_query": "用户登录功能",
    "platform": "Windows",
    "use_llm_judge": False
})
result = response.json()

# 2. 查询Test Case追溯
response = requests.post('http://localhost:8000/api/trace', json={
    "testcase_path": "Windows/Common/test_login.py"
})
result = response.json()

# 3. 差距分析
response = requests.post('http://localhost:8000/api/gap', json={
    "version": "v1.0",
    "min_confidence": "medium"
})
result = response.json()
```
