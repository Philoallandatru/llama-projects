"""测试 Router"""

import pytest
from pathlib import Path
from src.core.router import Router


def test_route_bug():
    """测试 Bug 类型路由"""
    router = Router(Path("src/profiles/config.json"))

    profile = router.route("Bug")
    assert profile.name == "bug"
    assert "root_cause" in profile.focus_areas


def test_route_story():
    """测试 Story 类型路由"""
    router = Router(Path("src/profiles/config.json"))

    profile = router.route("Story")
    assert profile.name == "story"
    assert "requirements" in profile.focus_areas


def test_route_task():
    """测试 Task 类型路由"""
    router = Router(Path("src/profiles/config.json"))

    profile = router.route("Task")
    assert profile.name == "task"


def test_route_unknown():
    """测试未知类型路由到默认"""
    router = Router(Path("src/profiles/config.json"))

    profile = router.route("UnknownType")
    assert profile.name == "default"


def test_route_case_insensitive():
    """测试大小写不敏感"""
    router = Router(Path("src/profiles/config.json"))

    profile1 = router.route("bug")
    profile2 = router.route("Bug")
    profile3 = router.route("BUG")

    assert profile1.name == profile2.name == profile3.name == "bug"
