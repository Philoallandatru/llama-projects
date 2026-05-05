"""Deep Analysis Workflow

Jira issue 深度分析工作流。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from ..core.issue_loader import IssueLoader
from ..core.router import Router, ProfileConfig
from ..core.retriever import EvidenceRetriever
from ..core.prompt_builder import PromptBuilder
from ..core.llm_client import LLMClient
from ..settings import settings
from ..utils.query_builder import build_retrieval_query

logger = logging.getLogger(__name__)


# ==================== Events ====================

class LoadIssueEvent(Event):
    """加载 Issue 事件"""
    issue_key: str


class RouteEvent(Event):
    """路由事件"""
    issue_type: str


class RetrieveEvent(Event):
    """检索证据事件"""
    pass


class AnalyzeEvent(Event):
    """分析事件"""
    pass


class FormatEvent(Event):
    """格式化输出事件"""
    pass


class ProgressEvent(Event):
    """进度事件（用于 UI 显示）"""
    stage: str
    message: str


class StreamEvent(Event):
    """流式输出事件"""
    content: str


# ==================== Workflow ====================

class DeepAnalysisWorkflow(Workflow):
    """Jira 深度分析工作流

    工作流步骤：
    1. start: 接收输入
    2. load_issue: 实时拉取 Jira issue
    3. route_profile: 根据 issue type 路由到分析 profile
    4. retrieve_evidence: 检索跨源证据
    5. generate_analysis: 调用 LLM 生成分析
    6. format_output: 格式化输出
    """

    def __init__(
        self,
        jira_config: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        index_base_path: Optional[Path] = None,
        profiles_dir: Optional[Path] = None,
        **kwargs: Any
    ):
        """初始化工作流

        Args:
            jira_config: Jira 配置（如果为 None，使用 settings）
            llm_config: LLM 配置（如果为 None，使用 settings）
            index_base_path: 索引基础路径（如果为 None，使用 settings）
            profiles_dir: Profiles 目录（如果为 None，使用 settings）
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        # 使用配置或默认值
        self.jira_config = jira_config or settings.get_jira_config()
        self.llm_config = llm_config or settings.get_llm_config()
        self.index_base_path = index_base_path or Path(settings.index_base_path)
        self.profiles_dir = profiles_dir or Path(settings.profiles_dir)

        logger.info("DeepAnalysisWorkflow initialized")

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> LoadIssueEvent:
        """接收输入

        Args:
            ctx: 上下文
            ev: 启动事件，包含：
                - issue_key: Issue key
                - mode: 分析模式（strict/balanced/exploratory，默认 balanced）
                - retrieve_evidence: 是否检索证据（默认 True）

        Returns:
            LoadIssueEvent
        """
        issue_key = ev.get("issue_key")
        if not issue_key:
            raise ValueError("issue_key is required")

        mode = ev.get("mode", "balanced")
        retrieve_evidence = ev.get("retrieve_evidence", True)

        await ctx.set("issue_key", issue_key)
        await ctx.set("mode", mode)
        await ctx.set("retrieve_evidence", retrieve_evidence)

        logger.info(f"Starting analysis for {issue_key} in {mode} mode")

        return LoadIssueEvent(issue_key=issue_key)

    @step
    async def load_issue(self, ctx: Context, ev: LoadIssueEvent) -> RouteEvent:
        """实时拉取 Jira issue

        Args:
            ctx: 上下文
            ev: LoadIssueEvent

        Returns:
            RouteEvent
        """
        loader = IssueLoader(
            server=self.jira_config["server"],
            email=self.jira_config["email"],
            token=self.jira_config["token"]
        )

        issue_data = await loader.load_issue_realtime(ev.issue_key)
        await ctx.set("issue_data", issue_data)

        issue_type = issue_data.get("fields", {}).get("issuetype", {}).get("name", "Unknown")

        ctx.write_event_to_stream(
            ProgressEvent(
                stage="load_issue",
                message=f"已加载 issue: {ev.issue_key} (类型: {issue_type})"
            )
        )

        return RouteEvent(issue_type=issue_type)

    @step
    async def route_profile(self, ctx: Context, ev: RouteEvent) -> RetrieveEvent:
        """根据 issue type 路由到分析 profile

        Args:
            ctx: 上下文
            ev: RouteEvent

        Returns:
            RetrieveEvent
        """
        router = Router(self.profiles_dir / "config.json")
        profile = router.route(ev.issue_type)
        await ctx.set("profile", profile)

        ctx.write_event_to_stream(
            ProgressEvent(
                stage="route",
                message=f"选择分析 profile: {profile.name} ({profile.description})"
            )
        )

        return RetrieveEvent()

    @step
    async def retrieve_evidence(self, ctx: Context, ev: RetrieveEvent) -> AnalyzeEvent:
        """检索跨源证据

        Args:
            ctx: 上下文
            ev: RetrieveEvent

        Returns:
            AnalyzeEvent
        """
        retrieve_evidence = await ctx.get("retrieve_evidence", default=True)
        if not retrieve_evidence:
            await ctx.set("evidence", {
                "similar_issues": [],
                "confluence": [],
                "specs": []
            })
            ctx.write_event_to_stream(
                ProgressEvent(
                    stage="retrieve",
                    message="跳过证据检索"
                )
            )
            return AnalyzeEvent()

        issue_data = await ctx.get("issue_data")
        issue_key = await ctx.get("issue_key")

        # 构建查询文本
        query = build_retrieval_query(issue_data)

        # 检索证据
        retriever = EvidenceRetriever(self.index_base_path)
        evidence = retriever.retrieve_all_evidence(
            query=query,
            similar_issues_top_k=settings.retrieve_similar_issues_top_k,
            confluence_top_k=settings.retrieve_confluence_top_k,
            spec_top_k=settings.retrieve_spec_top_k,
            exclude_issue_key=issue_key
        )

        await ctx.set("evidence", evidence)

        total_count = sum(len(docs) for docs in evidence.values())
        ctx.write_event_to_stream(
            ProgressEvent(
                stage="retrieve",
                message=f"检索到 {total_count} 个证据文档 "
                        f"(相似 issues: {len(evidence['similar_issues'])}, "
                        f"Confluence: {len(evidence['confluence'])}, "
                        f"规格: {len(evidence['specs'])})"
            )
        )

        return AnalyzeEvent()

    @step
    async def generate_analysis(self, ctx: Context, ev: AnalyzeEvent) -> FormatEvent:
        """调用 LLM 生成分析

        Args:
            ctx: 上下文
            ev: AnalyzeEvent

        Returns:
            FormatEvent
        """
        profile: ProfileConfig = await ctx.get("profile")
        mode = await ctx.get("mode")
        issue_data = await ctx.get("issue_data")
        evidence = await ctx.get("evidence")

        # 构建 prompt
        prompt_builder = PromptBuilder(self.profiles_dir)
        prompt = prompt_builder.build_prompt(
            profile=profile.name,
            mode=mode,
            issue_data=issue_data,
            evidence=evidence
        )

        ctx.write_event_to_stream(
            ProgressEvent(
                stage="analyze",
                message="开始生成分析报告..."
            )
        )

        # 调用 LLM（流式）
        llm_client = LLMClient(self.llm_config)

        analysis_text = ""
        async for chunk in llm_client.generate_stream(prompt):
            analysis_text += chunk
            ctx.write_event_to_stream(StreamEvent(content=chunk))

        await ctx.set("analysis", analysis_text)

        ctx.write_event_to_stream(
            ProgressEvent(
                stage="analyze",
                message=f"分析完成，生成了 {len(analysis_text)} 字符"
            )
        )

        return FormatEvent()

    @step
    async def format_output(self, ctx: Context, ev: FormatEvent) -> StopEvent:
        """格式化输出

        Args:
            ctx: 上下文
            ev: FormatEvent

        Returns:
            StopEvent
        """
        analysis = await ctx.get("analysis")
        issue_key = await ctx.get("issue_key")
        profile: ProfileConfig = await ctx.get("profile")
        mode = await ctx.get("mode")
        evidence = await ctx.get("evidence")

        result = {
            "issue_key": issue_key,
            "profile": profile.name,
            "mode": mode,
            "analysis": analysis,
            "evidence_count": {
                "similar_issues": len(evidence["similar_issues"]),
                "confluence": len(evidence["confluence"]),
                "specs": len(evidence["specs"])
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Analysis completed for {issue_key}")

        return StopEvent(result=result)
