"""Prompt 构建器

根据 profile 和模式构建完整的 LLM prompt。
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from llama_index.core.schema import Document

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Prompt 构建器

    职责：
    - 加载 prompt 模板
    - 根据 profile 和 mode 构建完整 prompt
    - 格式化 issue 数据和证据
    """

    # 分析模式指令
    MODE_INSTRUCTIONS = {
        "strict": """
**分析模式：严格模式**
- 只基于明确的证据进行分析
- 避免推测和假设
- 明确标注不确定的部分
- 引用具体的证据来源
""",
        "balanced": """
**分析模式：平衡模式**
- 基于证据进行分析，允许合理推断
- 推断时需要说明依据
- 区分确定的结论和可能的推测
- 提供多种可能的解释
""",
        "exploratory": """
**分析模式：探索模式**
- 鼓励提出假设和可能性
- 探索多种潜在的原因和解决方案
- 提出需要进一步调查的方向
- 识别知识盲区和不确定性
"""
    }

    def __init__(self, profiles_dir: Path):
        """初始化 Prompt 构建器

        Args:
            profiles_dir: profiles 目录路径
        """
        self.profiles_dir = Path(profiles_dir)
        self.prompts_dir = self.profiles_dir / "prompts"
        self.templates: Dict[str, str] = {}

        self._load_templates()

    def _load_templates(self) -> None:
        """加载所有 prompt 模板"""
        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")
            return

        for template_file in self.prompts_dir.glob("*.txt"):
            template_name = template_file.stem
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates[template_name] = f.read()
                logger.info(f"Loaded template: {template_name}")
            except Exception as e:
                logger.error(f"Failed to load template {template_name}: {e}")

    def build_prompt(
        self,
        profile: str,
        mode: str,
        issue_data: Dict[str, Any],
        evidence: Dict[str, List[Document]]
    ) -> str:
        """构建完整 prompt

        Args:
            profile: Profile 名称（如 "rca", "traceability"）
            mode: 分析模式（"strict", "balanced", "exploratory"）
            issue_data: Issue 原始数据
            evidence: 检索到的证据

        Returns:
            完整的 prompt 字符串
        """
        # 获取模板
        template = self.templates.get(profile)
        if not template:
            logger.warning(f"Template not found for profile '{profile}', using general")
            template = self.templates.get("general", "")

        # 获取模式指令
        mode_instruction = self.MODE_INSTRUCTIONS.get(mode, self.MODE_INSTRUCTIONS["balanced"])

        # 提取 issue 字段
        fields = issue_data.get("fields", {})
        issue_key = issue_data.get("key", "Unknown")
        summary = fields.get("summary", "No Summary")
        description = fields.get("description", "No description")
        status = fields.get("status", {}).get("name", "Unknown")
        priority = fields.get("priority", {}).get("name", "Unknown")
        created = fields.get("created", "Unknown")
        updated = fields.get("updated", "Unknown")

        # 格式化 comments
        comments_text = self._format_comments(fields.get("comment", {}).get("comments", []))

        # 格式化证据
        evidence_text = self._format_evidence(evidence)

        # 替换模板变量
        prompt = template.format(
            MODE_INSTRUCTION=mode_instruction,
            ISSUE_KEY=issue_key,
            SUMMARY=summary,
            STATUS=status,
            PRIORITY=priority,
            CREATED=created,
            UPDATED=updated,
            DESCRIPTION=description,
            COMMENTS=comments_text,
            EVIDENCE=evidence_text
        )

        return prompt

    def _format_comments(self, comments: List[Dict[str, Any]]) -> str:
        """格式化 comments

        Args:
            comments: Comment 列表

        Returns:
            格式化的 comments 文本
        """
        if not comments:
            return "（无 comments）"

        formatted = []
        for i, comment in enumerate(comments, 1):
            author = self._get_user_name(comment.get("author"))
            created = comment.get("created", "Unknown")
            body = comment.get("body", "")

            formatted.append(f"""
### Comment #{i}
- **作者**: {author}
- **时间**: {created}
- **内容**:
{body}
---
""")

        return "\n".join(formatted)

    def _format_evidence(self, evidence: Dict[str, List[Document]]) -> str:
        """格式化证据

        Args:
            evidence: 证据字典

        Returns:
            格式化的证据文本
        """
        sections = []

        # 相似 issues
        similar_issues = evidence.get("similar_issues", [])
        if similar_issues:
            sections.append("### 相似的历史 Issues")
            for i, doc in enumerate(similar_issues, 1):
                issue_key = doc.metadata.get("issue_key", "Unknown")
                summary = doc.metadata.get("summary", "")
                sections.append(f"\n**{i}. {issue_key}**: {summary}")
                sections.append(f"```\n{doc.text[:500]}...\n```")

        # Confluence 文档
        confluence_docs = evidence.get("confluence", [])
        if confluence_docs:
            sections.append("\n### Confluence 文档")
            for i, doc in enumerate(confluence_docs, 1):
                title = doc.metadata.get("title", "Unknown")
                sections.append(f"\n**{i}. {title}**")
                sections.append(f"```\n{doc.text[:500]}...\n```")

        # 规格文档
        spec_docs = evidence.get("specs", [])
        if spec_docs:
            sections.append("\n### 规格文档")
            for i, doc in enumerate(spec_docs, 1):
                filename = doc.metadata.get("file_name", "Unknown")
                sections.append(f"\n**{i}. {filename}**")
                sections.append(f"```\n{doc.text[:500]}...\n```")

        if not sections:
            return "（未检索到相关证据）"

        return "\n".join(sections)

    def _get_user_name(self, user: Any) -> str:
        """获取用户名

        Args:
            user: 用户对象

        Returns:
            用户名或 "Unknown"
        """
        if not user:
            return "Unknown"
        if isinstance(user, dict):
            return user.get("displayName", user.get("name", "Unknown"))
        return str(user)
