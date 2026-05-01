"""本地测试脚本

使用本地 LLM 和 mock 数据测试 jira-analysis 功能。
"""

import json
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.issue_loader import IssueLoader
from core.router import Router
from core.prompt_builder import PromptBuilder
from core.llm_client import LLMClient
from settings import settings


def load_mock_issue(issue_type: str = "bug"):
    """加载 mock issue 数据"""
    fixture_path = Path(__file__).parent / "fixtures" / f"mock_issue_{issue_type}.json"

    if not fixture_path.exists():
        print(f"❌ Mock 数据文件不存在: {fixture_path}")
        return None

    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_router():
    """测试路由功能"""
    print("\n" + "="*60)
    print("测试 1: 路由功能")
    print("="*60)

    router = Router(profiles_dir=Path("./src/profiles"))

    # 测试 Bug
    bug_issue = load_mock_issue("bug")
    if bug_issue:
        profile = router.route(bug_issue)
        print(f"✅ Bug issue 路由到 profile: {profile.name}")
        print(f"   - 描述: {profile.description}")

    # 测试 Story
    story_issue = load_mock_issue("story")
    if story_issue:
        profile = router.route(story_issue)
        print(f"✅ Story issue 路由到 profile: {profile.name}")
        print(f"   - 描述: {profile.description}")


def test_prompt_builder():
    """测试 Prompt 构建"""
    print("\n" + "="*60)
    print("测试 2: Prompt 构建")
    print("="*60)

    builder = PromptBuilder(profiles_dir=Path("./src/profiles"))
    bug_issue = load_mock_issue("bug")

    if bug_issue:
        # 构建 prompt（不使用证据）
        prompt = builder.build_prompt(
            profile="rca",
            mode="balanced",
            issue_data=bug_issue,
            evidence={"similar_issues": [], "confluence": [], "specs": []}
        )

        print(f"✅ Prompt 构建成功")
        print(f"   - 长度: {len(prompt)} 字符")
        print(f"   - 前 200 字符预览:")
        print(f"   {prompt[:200]}...")


def test_llm_client():
    """测试 LLM 客户端"""
    print("\n" + "="*60)
    print("测试 3: LLM 客户端")
    print("="*60)

    llm_config = settings.get_llm_config()
    print(f"📝 LLM 配置:")
    print(f"   - Base URL: {llm_config['base_url']}")
    print(f"   - Model: {llm_config['model']}")
    print(f"   - Temperature: {llm_config['temperature']}")

    client = LLMClient(llm_config=llm_config)

    # 简单测试
    test_prompt = "请用一句话介绍你自己。"
    print(f"\n🤖 测试 prompt: {test_prompt}")

    try:
        response = client.generate(test_prompt)
        print(f"✅ LLM 响应成功:")
        print(f"   {response[:200]}...")
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        print(f"   请确保 Ollama 正在运行: ollama serve")
        print(f"   并且已下载模型: ollama pull {llm_config['model']}")


def test_full_analysis():
    """测试完整分析流程（不使用索引）"""
    print("\n" + "="*60)
    print("测试 4: 完整分析流程（无索引）")
    print("="*60)

    # 加载组件
    router = Router(profiles_dir=Path("./src/profiles"))
    builder = PromptBuilder(profiles_dir=Path("./src/profiles"))
    llm_config = settings.get_llm_config()
    client = LLMClient(llm_config=llm_config)

    # 加载 issue
    bug_issue = load_mock_issue("bug")
    if not bug_issue:
        return

    print(f"📋 分析 Issue: {bug_issue['key']}")
    print(f"   标题: {bug_issue['fields']['summary']}")

    # 路由
    profile = router.route(bug_issue)
    print(f"✅ 路由到 profile: {profile.name}")

    # 构建 prompt
    prompt = builder.build_prompt(
        profile=profile.name,
        mode="balanced",
        issue_data=bug_issue,
        evidence={"similar_issues": [], "confluence": [], "specs": []}
    )
    print(f"✅ Prompt 构建完成 ({len(prompt)} 字符)")

    # LLM 分析
    print(f"🤖 正在调用 LLM 分析...")
    try:
        analysis = client.generate(prompt)
        print(f"\n{'='*60}")
        print(f"分析结果:")
        print(f"{'='*60}")
        print(analysis)
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Jira Analysis 本地测试")
    print("="*60)
    print(f"配置文件: config.yaml")
    print(f"Mock 数据: tests/fixtures/")
    print(f"LLM: {settings.llm_model} @ {settings.llm_base_url}")

    # 运行测试
    test_router()
    test_prompt_builder()
    test_llm_client()
    test_full_analysis()

    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
