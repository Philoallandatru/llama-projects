"""Batch Analysis Workflow

批量 Jira issue 分析工作流。
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

logger = logging.getLogger(__name__)


# ==================== Events ====================

class LoadBatchEvent(Event):
    """批量加载事件"""
    issue_keys: List[str]


class AnalyzeBatchEvent(Event):
    """批量分析事件"""
    pass


class GenerateReportEvent(Event):
    """生成报告事件"""
    pass


class BatchProgressEvent(Event):
    """批量进度事件"""
    stage: str
    message: str
    current: int
    total: int


# ==================== Workflow ====================

class BatchAnalysisWorkflow(Workflow):
    """批量 Jira 分析工作流

    工作流步骤：
    1. start: 接收输入
    2. load_batch: 批量加载 issues
    3. analyze_batch: 并发分析所有 issues
    4. generate_report: 生成汇总报告
    """

    def __init__(
        self,
        jira_config: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        index_base_path: Optional[Path] = None,
        profiles_dir: Optional[Path] = None,
        max_concurrent: int = 5,
        **kwargs: Any
    ):
        """初始化工作流

        Args:
            jira_config: Jira 配置
            llm_config: LLM 配置
            index_base_path: 索引基础路径
            profiles_dir: Profiles 目录
            max_concurrent: 最大并发数
            **kwargs: 其他参数
        """
        super().__init__(**kwargs)

        self.jira_config = jira_config or settings.get_jira_config()
        self.llm_config = llm_config or settings.get_llm_config()
        self.index_base_path = index_base_path or Path(settings.index_base_path)
        self.profiles_dir = profiles_dir or Path(settings.profiles_dir)
        self.max_concurrent = max_concurrent

        logger.info(f"BatchAnalysisWorkflow initialized (max_concurrent={max_concurrent})")

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> LoadBatchEvent:
        """接收输入

        Args:
            ctx: 上下文
            ev: 启动事件，包含：
                - issue_keys: Issue keys 列表
                - mode: 分析模式（默认 balanced）
                - retrieve_evidence: 是否检索证据（默认 True）
                - generate_summary: 是否生成汇总报告（默认 True）

        Returns:
            LoadBatchEvent
        """
        issue_keys = ev.get("issue_keys")
        if not issue_keys:
            raise ValueError("issue_keys is required")

        mode = ev.get("mode", "balanced")
        retrieve_evidence = ev.get("retrieve_evidence", True)
        generate_summary = ev.get("generate_summary", True)

        ctx.data["issue_keys"] = issue_keys
        ctx.data["mode"] = mode
        ctx.data["retrieve_evidence"] = retrieve_evidence
        ctx.data["generate_summary"] = generate_summary

        logger.info(f"Starting batch analysis for {len(issue_keys)} issues in {mode} mode")

        return LoadBatchEvent(issue_keys=issue_keys)

    @step
    async def load_batch(self, ctx: Context, ev: LoadBatchEvent) -> AnalyzeBatchEvent:
        """批量加载 issues

        Args:
            ctx: 上下文
            ev: LoadBatchEvent

        Returns:
            AnalyzeBatchEvent
        """
        loader = IssueLoader(
            server=self.jira_config["server"],
            email=self.jira_config["email"],
            token=self.jira_config["token"]
        )

        ctx.write_event_to_stream(
            BatchProgressEvent(
                stage="load",
                message="开始批量加载 issues...",
                current=0,
                total=len(ev.issue_keys)
            )
        )

        # 批量加载
        issues_data = await loader.load_issues_batch(ev.issue_keys)
        ctx.data["issues_data"] = issues_data

        ctx.write_event_to_stream(
            BatchProgressEvent(
                stage="load",
                message=f"已加载 {len(issues_data)} 个 issues",
                current=len(issues_data),
                total=len(ev.issue_keys)
            )
        )

        return AnalyzeBatchEvent()

    @step
    async def analyze_batch(self, ctx: Context, ev: AnalyzeBatchEvent) -> GenerateReportEvent:
        """并发分析所有 issues

        Args:
            ctx: 上下文
            ev: AnalyzeBatchEvent

        Returns:
            GenerateReportEvent
        """
        issues_data = ctx.data["issues_data"]
        mode = ctx.data["mode"]
        retrieve_evidence = ctx.data["retrieve_evidence"]

        # 初始化组件
        router = Router(self.profiles_dir / "config.json")
        retriever = EvidenceRetriever(self.index_base_path) if retrieve_evidence else None
        prompt_builder = PromptBuilder(self.profiles_dir)
        llm_client = LLMClient(self.llm_config)

        # 并发分析
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []

        async def analyze_one(issue_data: Dict[str, Any], index: int) -> Dict[str, Any]:
            """分析单个 issue"""
            async with semaphore:
                issue_key = issue_data["key"]

                try:
                    # 路由 profile
                    issue_type = issue_data.get("fields", {}).get("issuetype", {}).get("name", "Unknown")
                    profile = router.route(issue_type)

                    # 检索证据
                    evidence = {"similar_issues": [], "confluence": [], "specs": []}
                    if retrieve_evidence and retriever:
                        query = self._build_query(issue_data)
                        evidence = retriever.retrieve_all_evidence(
                            query=query,
                            similar_issues_top_k=settings.retrieve_similar_issues_top_k,
                            confluence_top_k=settings.retrieve_confluence_top_k,
                            spec_top_k=settings.retrieve_spec_top_k,
                            exclude_issue_key=issue_key
                        )

                    # 构建 prompt
                    prompt = prompt_builder.build_prompt(
                        profile=profile.name,
                        mode=mode,
                        issue_data=issue_data,
                        evidence=evidence
                    )

                    # 生成分析（非流式）
                    analysis = await llm_client.generate(prompt)

                    ctx.write_event_to_stream(
                        BatchProgressEvent(
                            stage="analyze",
                            message=f"已完成 {issue_key}",
                            current=index + 1,
                            total=len(issues_data)
                        )
                    )

                    return {
                        "issue_key": issue_key,
                        "profile": profile.name,
                        "analysis": analysis,
                        "evidence_count": {
                            "similar_issues": len(evidence["similar_issues"]),
                            "confluence": len(evidence["confluence"]),
                            "specs": len(evidence["specs"])
                        },
                        "status": "success"
                    }

                except Exception as e:
                    logger.error(f"Failed to analyze {issue_key}: {e}")
                    ctx.write_event_to_stream(
                        BatchProgressEvent(
                            stage="analyze",
                            message=f"分析 {issue_key} 失败: {str(e)}",
                            current=index + 1,
                            total=len(issues_data)
                        )
                    )
                    return {
                        "issue_key": issue_key,
                        "status": "error",
                        "error": str(e)
                    }

        # 并发执行
        tasks = [analyze_one(issue_data, i) for i, issue_data in enumerate(issues_data)]
        results = await asyncio.gather(*tasks)

        ctx.data["results"] = results

        success_count = sum(1 for r in results if r["status"] == "success")
        ctx.write_event_to_stream(
            BatchProgressEvent(
                stage="analyze",
                message=f"批量分析完成: {success_count}/{len(results)} 成功",
                current=len(results),
                total=len(results)
            )
        )

        return GenerateReportEvent()

    @step
    async def generate_report(self, ctx: Context, ev: GenerateReportEvent) -> StopEvent:
        """生成汇总报告

        Args:
            ctx: 上下文
            ev: GenerateReportEvent

        Returns:
            StopEvent
        """
        results = ctx.data["results"]
        generate_summary = ctx.data.get("generate_summary", True)

        # 统计信息
        total = len(results)
        success = sum(1 for r in results if r["status"] == "success")
        failed = total - success

        summary = None
        if generate_summary and success > 0:
            ctx.write_event_to_stream(
                BatchProgressEvent(
                    stage="report",
                    message="生成汇总报告...",
                    current=0,
                    total=1
                )
            )

            # 生成汇总
            summary = await self._generate_summary(results)

            ctx.write_event_to_stream(
                BatchProgressEvent(
                    stage="report",
                    message="汇总报告生成完成",
                    current=1,
                    total=1
                )
            )

        report = {
            "total": total,
            "success": success,
            "failed": failed,
            "results": results,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Batch analysis completed: {success}/{total} succeeded")

        return StopEvent(result=report)

    async def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """生成汇总报告

        Args:
            results: 分析结果列表

        Returns:
            汇总报告文本
        """
        # 提取成功的分析
        successful = [r for r in results if r["status"] == "success"]
        if not successful:
            return "没有成功的分析结果"

        # 按 profile 分组
        by_profile = {}
        for result in successful:
            profile = result["profile"]
            if profile not in by_profile:
                by_profile[profile] = []
            by_profile[profile].append(result)

        # 构建汇总 prompt
        prompt_parts = [
            "请根据以下批量分析结果生成一份汇总报告。",
            "",
            f"总共分析了 {len(successful)} 个 issues，分布如下：",
        ]

        for profile, items in by_profile.items():
            prompt_parts.append(f"- {profile}: {len(items)} 个")

        prompt_parts.extend([
            "",
            "各 issue 的分析结果：",
            ""
        ])

        for result in successful:
            prompt_parts.append(f"## {result['issue_key']} ({result['profile']})")
            prompt_parts.append(result["analysis"][:500])  # 每个最多 500 字符
            prompt_parts.append("")

        prompt_parts.extend([
            "",
            "请生成一份简洁的汇总报告，包括：",
            "1. 主要发现和趋势",
            "2. 共性问题",
            "3. 建议的行动项",
            "",
            "报告应该简洁明了，不超过 500 字。"
        ])

        prompt = "\n".join(prompt_parts)

        # 调用 LLM
        llm_client = LLMClient(self.llm_config)
        summary = await llm_client.generate(prompt)

        return summary

    def _build_query(self, issue_data: Dict[str, Any]) -> str:
        """构建检索查询文本

        Args:
            issue_data: Issue 数据

        Returns:
            查询文本
        """
        fields = issue_data.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description", "")

        query_parts = [summary]
        if description:
            query_parts.append(description[:500])

        return " ".join(query_parts)
