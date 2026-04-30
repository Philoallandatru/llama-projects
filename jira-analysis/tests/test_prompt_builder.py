"""测试 PromptBuilder"""

import pytest
from pathlib import Path
from src.core.prompt_builder import PromptBuilder
from src.core.models import AnalysisProfile


def test_build_prompt():
    """测试构建 prompt"""
    builder = PromptBuilder(Path("src/profiles/prompts"))

    profile = AnalysisProfile(
        name="bug",
        prompt_template="rca.txt",
        focus_areas=["root_cause", "impact", "fix"],
        analysis_depth="deep",
        evidence_sources=["jira", "confluence"],
        retrieval_top_k=5
    )

    issue_data = {
        "key": "PROJ-123",
        "fields": {
            "summary": "Login fails with 500 error",
            "description": "Users cannot login",
            "issuetype": {"name": "Bug"}
        }
    }

    evidence = []

    prompt = builder.build(profile, issue_data, evidence)

    assert "PROJ-123" in prompt
    assert "Login fails with 500 error" in prompt
    assert len(prompt) > 100


def test_build_prompt_with_evidence():
    """测试包含证据的 prompt"""
    builder = PromptBuilder(Path("src/profiles/prompts"))

    profile = AnalysisProfile(
        name="bug",
        prompt_template="rca.txt",
        focus_areas=["root_cause"],
        analysis_depth="deep",
        evidence_sources=["confluence"],
        retrieval_top_k=3
    )

    issue_data = {
        "key": "PROJ-456",
        "fields": {
            "summary": "API timeout",
            "description": "API calls timing out",
            "issuetype": {"name": "Bug"}
        }
    }

    # Mock evidence
    class MockDoc:
        def __init__(self, text):
            self.text = text

    evidence = [
        MockDoc("Authentication service documentation"),
        MockDoc("API rate limiting policy")
    ]

    prompt = builder.build(profile, issue_data, evidence)

    assert "Authentication service documentation" in prompt
    assert "API rate limiting policy" in prompt
