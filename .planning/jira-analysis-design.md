# Jira 深度分析系统 - 设计文档

## 1. 项目概述

**项目名称**: jira-analysis

**目标**: 构建一个独立的 LlamaIndex Workflow 项目，提供 Jira issue 深度分析服务

**核心功能**:
- 实时交互分析（用户输入 issue key）
- 批量报告生成（分析一批 issues）
- Issue 类型路由（根据 issue type 选择分析 profile）
- 跨源证据检索（从 Confluence 和规格文档索引中检索）
- 多模式分析（strict/balanced/exploratory）
- 结构化输出（markdown 报告）

**技术栈**:
- LlamaIndex Workflows（事件驱动编排）
- LlamaDeploy（部署和 API 服务）
- 本地 LLM（Ollama/LM Studio）
- TypeScript UI

**使用规模**: 中等规模（10-50 用户，几千个 issues，响应时间 5-10 秒）

---

## 2. 架构设计

**目录结构**:
```
jira-analysis/
├── src/
│   ├── workflows/
│   │   ├── deep_analysis.py          # 深度分析 workflow
│   │   ├── batch_analysis.py         # 批量分析 workflow
│   │   ├── verification.py           # 验证 workflow（预留）
│   │   └── knowledge_extraction.py   # 知识提取 workflow（预留）
│   ├── core/
│   │   ├── issue_loader.py           # 实时加载 Jira issue
│   │   ├── router.py                 # Issue type 路由
│   │   ├── retriever.py              # 跨源证据检索
│   │   ├── prompt_builder.py         # Prompt 构建
│   │   └── llm_client.py             # LLM 调用封装
│   ├── profiles/
│   │   ├── config.json               # Issue type → profile 映射
│   │   └── prompts/                  # Prompt 模板
│   │       ├── rca.txt               # 根因分析
│   │       ├── traceability.txt      # 需求追溯
│   │       ├── change_impact.txt     # 变更影响
│   │       └── general.txt           # 通用分析
│   ├── settings.py                   # 配置管理
│   └── .env                          # 环境变量
├── ui/                               # TypeScript UI
├── llama_deploy.yml                  # 部署配置
└── README.md
```

**设计原则**:
- 共享组件 + 独立 Workflows（便于扩展）
- 核心逻辑可复用，新增 workflow 只需组合现有组件
- 配置驱动（issue type 路由、prompt 模板）

---

## 3. 核心组件设计

### 3.1 IssueLoader（issue_loader.py）

**职责**: 实时从 Jira API 拉取目标 issue 的最新数据

```python
class IssueLoader:
    def __init__(self, jira_config: Dict[str, Any]):
        """复用 datasource 的 JiraDataSource"""
        
    async def load_issue_realtime(self, issue_key: str) -> Dict[str, Any]:
        """实时拉取单个 issue（包含 comments）"""
        
    async def load_issues_batch(self, issue_keys: List[str]) -> List[Dict[str, Any]]:
        """批量实时拉取（异步并发）"""
```

**关键点**:
- 复用现有的 `JiraDataSource` 类
- 使用异步方法提升性能
- 返回原始 JSON 数据

---

### 3.2 Router（router.py）

**职责**: 根据 issue type 路由到对应的分析 profile

**配置文件**（profiles/config.json）:
```json
{
  "profiles": {
    "rca": {
      "issue_types": ["FW Bug", "HW Bug", "Test Bug"],
      "prompt_template": "prompts/rca.txt",
      "output_sections": ["概述", "跨源证据", "根因分析", "差距", "建议"]
    },
    "traceability": {
      "issue_types": ["DAS/PRD", "MRD"],
      "prompt_template": "prompts/traceability.txt",
      "output_sections": ["概述", "跨源证据", "追溯分析", "差距", "建议"]
    },
    "change_impact": {
      "issue_types": ["Requirement Change", "Component Change"],
      "prompt_template": "prompts/change_impact.txt",
      "output_sections": ["概述", "跨源证据", "影响分析", "差距", "建议"]
    }
  },
  "default_profile": "general"
}
```

**代码接口**:
```python
class Router:
    def __init__(self, config_path: Path):
        """加载配置文件"""
        
    def route(self, issue_type: str) -> ProfileConfig:
        """返回对应的 profile 配置"""
```

---

### 3.3 EvidenceRetriever（retriever.py）

**职责**: 从 LlamaIndex 向量索引中检索相关证据

```python
class EvidenceRetriever:
    def __init__(self, index_path: Path):
        """加载三类索引：Jira/Confluence/规格文档"""
        self.jira_index = self._load_index(index_path / "jira")
        self.confluence_index = self._load_index(index_path / "confluence")
        self.spec_index = self._load_index(index_path / "specs")
    
    def retrieve_similar_issues(self, query: str, top_k: int = 5) -> List[Document]:
        """检索相似的历史 Jira issues"""
        
    def retrieve_confluence_docs(self, query: str, top_k: int = 3) -> List[Document]:
        """检索相关的 Confluence 文档"""
        
    def retrieve_spec_docs(self, query: str, top_k: int = 3) -> List[Document]:
        """检索相关的规格文档"""
```

**查询构建策略**:
- 基于目标 issue 的 `summary + description + key comments` 构建查询文本
- 可选：使用 LLM 提取关键词增强查询

---

### 3.4 PromptBuilder（prompt_builder.py）

**职责**: 根据 profile 和模式构建完整的 LLM prompt

```python
class PromptBuilder:
    def __init__(self, profiles_dir: Path):
        """加载 prompt 模板目录"""
        self.templates = self._load_templates(profiles_dir / "prompts")
        self.mode_instructions = self._load_mode_instructions()
    
    def build_prompt(
        self,
        profile: str,  # "rca", "traceability", etc.
        mode: str,     # "strict", "balanced", "exploratory"
        issue_data: Dict[str, Any],
        evidence: Dict[str, List[Document]]
    ) -> str:
        """构建完整 prompt"""
```

**Prompt 模板结构**（prompts/rca.txt）:
```
你是一位资深的固件工程师，专注于根因分析。

## 任务
分析以下 Jira issue，识别根本原因、失效机制和修复建议。

**重要**：请仔细阅读并分析每一条 comment，因为：
- Comments 中通常包含调查过程、测试结果、根因假设
- 工程师在 comments 中会讨论失效机制和解决方案
- 后续的 comments 可能推翻或修正早期的结论
- 需要追踪问题的演进过程（从发现 → 调查 → 定位 → 修复）

{MODE_INSTRUCTION}

## 输出格式
1. 概述：2-3 句话总结问题
2. 跨源证据：引用 Confluence 和规格证据
3. 根因分析：
   - 失效机制（基于 comments 中的调查过程）
   - 触发条件（引用具体的 comment）
   - 根本原因（综合所有 comments 的结论）
   - 证据链（引用关键 comments，格式：[作者 - 时间]: "内容摘要"）
4. 差距：缺失的证据或未解答的问题
5. 建议：具体的后续步骤

## Jira Issue 上下文
**Issue Key**: {ISSUE_KEY}
**Summary**: {SUMMARY}
**Description**: 
{DESCRIPTION}

**Comments**（按时间顺序，请逐条分析）:
{COMMENTS_DETAILED}

## 检索证据
{EVIDENCE}
```

**Comments 格式化**:
```python
def format_comments(comments: List[Dict]) -> str:
    """将 comments 格式化为易于分析的结构"""
    formatted = []
    for i, comment in enumerate(comments, 1):
        formatted.append(f"""
### Comment #{i}
- **作者**: {comment['author']}
- **时间**: {comment['created']}
- **内容**:
{comment['body']}
---
""")
    return "\n".join(formatted)
```

---

### 3.5 LLMClient（llm_client.py）

**职责**: 封装本地 LLM 调用，支持流式输出

```python
class LLMClient:
    def __init__(self, config: Dict[str, Any]):
        """
        初始化本地 LLM 客户端
        Args:
            config: {
                "base_url": "http://localhost:11434/v1",  # Ollama
                "model": "qwen2.5:14b",
                "temperature": 0.1,
                "max_tokens": 4096
            }
        """
        from llama_index.llms.openai_like import OpenAILike
        self.llm = OpenAILike(
            api_base=config["base_url"],
            model=config["model"],
            temperature=config.get("temperature", 0.1),
            max_tokens=config.get("max_tokens", 4096),
            is_chat_model=True
        )
    
    async def generate(self, prompt: str) -> str:
        """生成分析报告（非流式）"""
        response = await self.llm.acomplete(prompt)
        return response.text
    
    async def generate_stream(self, prompt: str) -> AsyncIterator[str]:
        """流式生成（用于实时 UI 反馈）"""
        response = await self.llm.astream_complete(prompt)
        async for chunk in response:
            yield chunk.delta
```

**设计要点**:
- 使用 LlamaIndex 的 `OpenAILike` 适配器，兼容 Ollama/LM Studio
- 支持流式和非流式两种模式
- 温度设置较低（0.1）以保证输出稳定性

---

## 4. Workflow 设计

### 4.1 DeepAnalysisWorkflow（workflows/deep_analysis.py）

**工作流步骤**:

```python
class DeepAnalysisWorkflow(Workflow):
    """Jira 深度分析工作流"""
    
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> LoadIssueEvent:
        """接收输入"""
        ctx.data["issue_key"] = ev.issue_key
        ctx.data["mode"] = ev.mode
        return LoadIssueEvent(issue_key=ev.issue_key)
    
    @step
    async def load_issue(self, ctx: Context, ev: LoadIssueEvent) -> RouteEvent:
        """实时拉取 Jira issue"""
        loader = IssueLoader(self.jira_config)
        issue_data = await loader.load_issue_realtime(ev.issue_key)
        ctx.data["issue_data"] = issue_data
        
        ctx.write_event_to_stream(ProgressEvent(
            stage="load_issue",
            message=f"已加载 issue: {issue_data['key']}"
        ))
        
        return RouteEvent(issue_type=issue_data['fields']['issuetype']['name'])
    
    @step
    async def route_profile(self, ctx: Context, ev: RouteEvent) -> RetrieveEvent:
        """根据 issue type 路由到分析 profile"""
        router = Router(self.profiles_config)
        profile = router.route(ev.issue_type)
        ctx.data["profile"] = profile
        
        ctx.write_event_to_stream(ProgressEvent(
            stage="route",
            message=f"选择分析 profile: {profile.name}"
        ))
        
        return RetrieveEvent()
    
    @step
    async def retrieve_evidence(self, ctx: Context, ev: RetrieveEvent) -> AnalyzeEvent:
        """检索跨源证据"""
        issue_data = ctx.data["issue_data"]
        query = self._build_query(issue_data)
        
        retriever = EvidenceRetriever(self.index_path)
        
        similar_issues = retriever.retrieve_similar_issues(query, top_k=5)
        confluence_docs = retriever.retrieve_confluence_docs(query, top_k=3)
        spec_docs = retriever.retrieve_spec_docs(query, top_k=3)
        
        evidence = {
            "similar_issues": similar_issues,
            "confluence": confluence_docs,
            "specs": spec_docs
        }
        ctx.data["evidence"] = evidence
        
        ctx.write_event_to_stream(ProgressEvent(
            stage="retrieve",
            message=f"检索到 {len(similar_issues)} 个相似 issues, "
                    f"{len(confluence_docs)} 个 Confluence 文档, "
                    f"{len(spec_docs)} 个规格文档"
        ))
        
        return AnalyzeEvent()
    
    @step
    async def generate_analysis(self, ctx: Context, ev: AnalyzeEvent) -> FormatEvent:
        """调用 LLM 生成分析"""
        profile = ctx.data["profile"]
        mode = ctx.data["mode"]
        issue_data = ctx.data["issue_data"]
        evidence = ctx.data["evidence"]
        
        prompt_builder = PromptBuilder(self.profiles_dir)
        prompt = prompt_builder.build_prompt(
            profile=profile.name,
            mode=mode,
            issue_data=issue_data,
            evidence=evidence
        )
        
        llm_client = LLMClient(self.llm_config)
        
        analysis_text = ""
        async for chunk in llm_client.generate_stream(prompt):
            analysis_text += chunk
            ctx.write_event_to_stream(StreamEvent(content=chunk))
        
        ctx.data["analysis"] = analysis_text
        return FormatEvent()
    
    @step
    async def format_output(self, ctx: Context, ev: FormatEvent) -> StopEvent:
        """格式化输出"""
        analysis = ctx.data["analysis"]
        issue_key = ctx.data["issue_key"]
        
        result = {
            "issue_key": issue_key,
            "profile": ctx.data["profile"].name,
            "mode": ctx.data["mode"],
            "analysis": analysis,
            "evidence_count": {
                "similar_issues": len(ctx.data["evidence"]["similar_issues"]),
                "confluence": len(ctx.data["evidence"]["confluence"]),
                "specs": len(ctx.data["evidence"]["specs"])
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return StopEvent(result=result)
```

**输入示例**:
```json
{
  "issue_key": "NVME-777",
  "mode": "strict",
  "retrieve_evidence": true
}
```

**输出示例**:
```json
{
  "issue_key": "NVME-777",
  "profile": "rca",
  "mode": "strict",
  "analysis": "# 深度分析报告：NVME-777\n\n## 1. 概述\n...",
  "evidence_count": {
    "similar_issues": 5,
    "confluence": 3,
    "specs": 2
  },
  "timestamp": "2026-04-30T10:30:00Z"
}
```

---

### 4.2 BatchAnalysisWorkflow（workflows/batch_analysis.py）

**工作流步骤**:

```python
class BatchAnalysisWorkflow(Workflow):
    """批量分析工作流"""
    
    @step
    async def start(self, ctx: Context, ev: StartEvent) -> BatchLoadEvent:
        """接收批量输入"""
        ctx.data["mode"] = ev.mode
        ctx.data["max_concurrent"] = ev.get("max_concurrent", 5)
        
        if ev.get("issue_keys"):
            issue_keys = ev.issue_keys
        elif ev.get("jql"):
            issue_keys = await self._fetch_issue_keys_by_jql(ev.jql)
        else:
            raise ValueError("必须提供 issue_keys 或 jql")
        
        ctx.data["issue_keys"] = issue_keys
        ctx.data["total"] = len(issue_keys)
        ctx.data["completed"] = 0
        
        return BatchLoadEvent(issue_keys=issue_keys)
    
    @step
    async def batch_analyze(self, ctx: Context, ev: BatchLoadEvent) -> GenerateReportEvent:
        """批量分析（控制并发）"""
        issue_keys = ev.issue_keys
        mode = ctx.data["mode"]
        max_concurrent = ctx.data["max_concurrent"]
        
        deep_workflow = DeepAnalysisWorkflow(
            jira_config=self.jira_config,
            index_path=self.index_path,
            profiles_dir=self.profiles_dir,
            llm_config=self.llm_config
        )
        
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def analyze_one(issue_key: str):
            async with semaphore:
                try:
                    result = await deep_workflow.run(
                        issue_key=issue_key,
                        mode=mode,
                        retrieve_evidence=True
                    )
                    ctx.data["completed"] += 1
                    
                    ctx.write_event_to_stream(ProgressEvent(
                        stage="batch_analyze",
                        message=f"完成 {ctx.data['completed']}/{ctx.data['total']}: {issue_key}"
                    ))
                    
                    return result
                except Exception as e:
                    logger.error(f"分析 {issue_key} 失败: {e}")
                    return {"issue_key": issue_key, "error": str(e)}
        
        tasks = [analyze_one(key) for key in issue_keys]
        results = await asyncio.gather(*tasks)
        
        ctx.data["results"] = results
        return GenerateReportEvent()
    
    @step
    async def generate_summary_report(self, ctx: Context, ev: GenerateReportEvent) -> StopEvent:
        """生成汇总报告"""
        results = ctx.data["results"]
        
        success_count = sum(1 for r in results if "error" not in r)
        error_count = len(results) - success_count
        
        by_profile = {}
        for r in results:
            if "error" not in r:
                profile = r.get("profile", "unknown")
                by_profile.setdefault(profile, []).append(r)
        
        summary = {
            "total": len(results),
            "success": success_count,
            "error": error_count,
            "by_profile": {k: len(v) for k, v in by_profile.items()},
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        return StopEvent(result=summary)
```

**输入示例**:
```json
{
  "issue_keys": ["NVME-777", "NVME-778", "NVME-779"],
  "mode": "strict",
  "max_concurrent": 5
}
```

或

```json
{
  "jql": "project = NVME AND updated >= '2024-04-01'",
  "mode": "strict",
  "max_concurrent": 5
}
```

**并发控制**:
- 使用 `asyncio.Semaphore` 控制最大并发数
- 默认 5 个并发请求

---

## 5. 配置和部署

### 5.1 项目配置文件（src/settings.py）

```python
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """项目配置"""
    
    # Jira 配置
    jira_server: str
    jira_email: str
    jira_token: str
    
    # LLM 配置
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "qwen2.5:14b"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    
    # 索引路径
    index_base_path: Path = Path("./indexes")
    jira_index_path: Path = index_base_path / "jira"
    confluence_index_path: Path = index_base_path / "confluence"
    spec_index_path: Path = index_base_path / "specs"
    
    # Profiles 配置
    profiles_dir: Path = Path("./src/profiles")
    
    # 批量分析配置
    batch_max_concurrent: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 5.2 环境变量文件（.env）

```bash
# Jira 配置
JIRA_SERVER=https://jira.example.com
JIRA_EMAIL=user@example.com
JIRA_TOKEN=your_token_here

# LLM 配置
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096

# 索引路径（指向已有的索引）
INDEX_BASE_PATH=../datasource/data/indexes
```

### 5.3 LlamaDeploy 配置（llama_deploy.yml）

```yaml
name: jira-analysis

control-plane:
  port: 8000

default-service: deep-analysis

services:
  deep-analysis:
    name: deep-analysis
    source:
      type: local
      name: workflows.deep_analysis:DeepAnalysisWorkflow
    path: /deep-analysis
  
  batch-analysis:
    name: batch-analysis
    source:
      type: local
      name: workflows.batch_analysis:BatchAnalysisWorkflow
    path: /batch-analysis
```

---

## 6. Decision Log（决策日志）

### 决策 1：架构模式
- **决定**: 共享组件 + 独立 Workflows
- **备选方案**: 单 Workflow、完全独立 Workflows
- **选择原因**: 平衡代码复用和扩展性，便于后续添加 verification 和 knowledge extraction workflows

### 决策 2：Jira 数据获取
- **决定**: 分析目标实时拉取，检索证据使用索引
- **备选方案**: 完全依赖 datasource 同步数据
- **选择原因**: 确保分析的是最新状态，同时利用索引提升检索性能

### 决策 3：Comments 处理
- **决定**: 整体分析，在 prompt 中强调逐条分析
- **备选方案**: 逐条独立分析、分层分析
- **选择原因**: 保持上下文连贯性，控制成本，输出更有价值

### 决策 4：LLM 后端
- **决定**: 本地模型（Ollama/LM Studio）
- **备选方案**: OpenAI API、多后端支持
- **选择原因**: 用户明确需求，成本可控

### 决策 5：批量分析实现
- **决定**: 复用单个分析 workflow + 并发控制
- **备选方案**: 独立的批量处理逻辑
- **选择原因**: 避免重复代码，通过 semaphore 控制并发数

### 决策 6：证据检索
- **决定**: 基于现有 LlamaIndex 索引
- **备选方案**: 实时 API 查询、混合方式
- **选择原因**: 用户明确需求，性能最优

---

## 7. 实现计划

### Phase 1：核心组件（2-3 天）
1. `IssueLoader` - 实时拉取 Jira issue
2. `Router` - Issue type 路由
3. `EvidenceRetriever` - 跨源证据检索
4. `PromptBuilder` - Prompt 构建
5. `LLMClient` - LLM 调用封装

### Phase 2：Deep Analysis Workflow（2 天）
1. 实现完整的分析流程
2. 添加流式输出支持
3. 单元测试

### Phase 3：Batch Analysis Workflow（1 天）
1. 实现批量分析
2. 并发控制
3. 汇总报告生成

### Phase 4：配置和部署（1 天）
1. Profiles 配置文件
2. Prompt 模板
3. LlamaDeploy 配置
4. 环境配置

### Phase 5：UI 和测试（2 天）
1. TypeScript UI（基于现有项目模板）
2. 端到端测试
3. 文档编写

**总计：8-9 天**

---

**设计文档完成 - 2026-04-30**
