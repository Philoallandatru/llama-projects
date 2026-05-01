"""使用真实数据测试 jira-analysis

测试流程：
1. 从 Jira Server 加载真实 issue
2. 从索引中检索相关证据（PDF/Excel 文档）
3. 使用 LM Studio 进行分析
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.issue_loader import IssueLoader
from core.router import Router
from core.retriever import EvidenceRetriever
from core.prompt_builder import PromptBuilder
from core.llm_client import LLMClient
from settings import settings
from utils.query_builder import build_retrieval_query


async def test_real_issue(issue_key: str):
    """测试真实 issue 分析"""
    print(f"\n{'='*60}")
    print(f"测试真实 Issue: {issue_key}")
    print(f"{'='*60}")

    # 1. 加载 issue
    print(f"\n📥 步骤 1: 从 Jira Server 加载 issue")
    print(f"   Server: {settings.jira_server}")

    jira_config = settings.get_jira_config()
    loader = IssueLoader(**jira_config)

    try:
        issue_data = await loader.load_issue_realtime(issue_key)
        print(f"✅ Issue 加载成功")
        print(f"   Key: {issue_data['key']}")
        print(f"   标题: {issue_data['fields']['summary']}")
        print(f"   类型: {issue_data['fields']['issuetype']['name']}")
        print(f"   状态: {issue_data['fields']['status']['name']}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return

    # 2. 路由
    print(f"\n🔀 步骤 2: 路由分析 profile")
    router = Router(profiles_dir=Path("./src/profiles"))
    profile = router.route(issue_data)
    print(f"✅ 路由到 profile: {profile.name}")
    print(f"   描述: {profile.description}")
    print(f"   分析模式: {profile.mode}")

    # 3. 检索证据
    print(f"\n🔍 步骤 3: 从索引检索相关证据")
    print(f"   索引路径: {settings.index_base_path}")

    try:
        retriever = EvidenceRetriever(index_base_path=Path(settings.index_base_path))

        # 构建查询
        query = build_retrieval_query(issue_data)
        print(f"   查询文本: {query[:100]}...")

        evidence = retriever.retrieve_all_evidence(
            query=query,
            similar_issues_top_k=5,
            confluence_top_k=3,
            spec_top_k=3,
            exclude_issue_key=issue_key
        )

        total_evidence = sum(len(docs) for docs in evidence.values())
        print(f"✅ 检索到 {total_evidence} 条证据:")

        if evidence['similar_issues']:
            print(f"   📋 相似 issues: {len(evidence['similar_issues'])} 个")
            for doc in evidence['similar_issues'][:3]:
                print(f"      - {doc.metadata.get('issue_key')}: {doc.metadata.get('summary', '')[:50]}...")

        if evidence['confluence']:
            print(f"   📄 Confluence 文档: {len(evidence['confluence'])} 个")
            for doc in evidence['confluence'][:3]:
                print(f"      - {doc.metadata.get('title', 'Unknown')[:50]}...")

        if evidence['specs']:
            print(f"   📚 规格文档: {len(evidence['specs'])} 个")
            for doc in evidence['specs'][:3]:
                print(f"      - {doc.metadata.get('file_name', 'Unknown')}")

    except Exception as e:
        print(f"⚠️  检索失败: {e}")
        print(f"   提示: 请先使用 datasource 构建索引")
        evidence = {"similar_issues": [], "confluence": [], "specs": []}

    # 4. 构建 prompt
    print(f"\n📝 步骤 4: 构建 LLM prompt")
    builder = PromptBuilder(profiles_dir=Path("./src/profiles"))
    prompt = builder.build_prompt(
        profile=profile.name,
        mode="balanced",
        issue_data=issue_data,
        evidence=evidence
    )
    print(f"✅ Prompt 构建完成")
    print(f"   长度: {len(prompt)} 字符")
    print(f"   前 200 字符预览:")
    print(f"   {prompt[:200]}...")

    # 5. LLM 分析
    print(f"\n🤖 步骤 5: 调用 LLM 分析")
    llm_config = settings.get_llm_config()
    print(f"   LLM: {llm_config['model']}")
    print(f"   Base URL: {llm_config['base_url']}")

    try:
        llm = LLMClient(llm_config=llm_config)
        print(f"   正在生成分析结果...")
        analysis = llm.generate(prompt)

        print(f"\n{'='*60}")
        print(f"分析结果:")
        print(f"{'='*60}")
        print(analysis)
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        print(f"   提示: 请确保 LM Studio 正在运行")
        print(f"   测试连接: curl {llm_config['base_url']}/models")


async def test_document_retrieval():
    """测试文档检索功能"""
    print(f"\n{'='*60}")
    print(f"测试文档检索")
    print(f"{'='*60}")

    print(f"\n📚 索引路径: {settings.index_base_path}")

    try:
        retriever = EvidenceRetriever(index_base_path=Path(settings.index_base_path))

        # 测试查询
        test_queries = [
            "用户认证流程",
            "数据库设计",
            "API 接口规范"
        ]

        for query in test_queries:
            print(f"\n🔍 查询: {query}")
            docs = retriever.retrieve("specs", query, top_k=3)

            if docs:
                print(f"✅ 检索到 {len(docs)} 个文档:")
                for i, doc in enumerate(docs, 1):
                    file_name = doc.metadata.get('file_name', 'Unknown')
                    print(f"   {i}. {file_name}")
                    print(f"      内容预览: {doc.text[:100]}...")
            else:
                print(f"⚠️  未检索到相关文档")

    except Exception as e:
        print(f"❌ 检索失败: {e}")
        print(f"   提示: 请先使用 datasource 构建索引")


async def test_jira_connection():
    """测试 Jira 连接"""
    print(f"\n{'='*60}")
    print(f"测试 Jira Server 连接")
    print(f"{'='*60}")

    print(f"\n📡 连接信息:")
    print(f"   Server: {settings.jira_server}")
    print(f"   Email: {settings.jira_email}")

    jira_config = settings.get_jira_config()
    loader = IssueLoader(**jira_config)

    try:
        # 使用 JQL 查询测试连接
        print(f"\n🔍 测试 JQL 查询...")
        issue_keys = await loader.search_issues_by_jql(
            jql="ORDER BY created DESC",
            max_results=5
        )

        print(f"✅ 连接成功！")
        print(f"   找到 {len(issue_keys)} 个最近的 issues:")
        for key in issue_keys:
            print(f"   - {key}")

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print(f"\n💡 排查建议:")
        print(f"   1. 检查 Jira Server URL 是否正确")
        print(f"   2. 检查 API Token 是否有效")
        print(f"   3. 测试命令:")
        print(f"      curl -u {settings.jira_email}:YOUR_TOKEN \\")
        print(f"        {settings.jira_server}/rest/api/2/myself")


async def test_lm_studio():
    """测试 LM Studio 连接"""
    print(f"\n{'='*60}")
    print(f"测试 LM Studio 连接")
    print(f"{'='*60}")

    llm_config = settings.get_llm_config()
    print(f"\n🤖 LLM 配置:")
    print(f"   Base URL: {llm_config['base_url']}")
    print(f"   Model: {llm_config['model']}")
    print(f"   Temperature: {llm_config['temperature']}")

    try:
        llm = LLMClient(llm_config=llm_config)

        print(f"\n📝 测试 prompt: 请用一句话介绍你自己。")
        response = llm.generate("请用一句话介绍你自己。")

        print(f"✅ LM Studio 响应成功:")
        print(f"   {response[:200]}...")

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print(f"\n💡 排查建议:")
        print(f"   1. 确认 LM Studio 正在运行")
        print(f"   2. 确认已加载模型")
        print(f"   3. 测试命令:")
        print(f"      curl {llm_config['base_url']}/models")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Jira Analysis 真实数据测试")
    parser.add_argument("--issue", type=str, help="测试指定的 issue key")
    parser.add_argument("--test-jira", action="store_true", help="测试 Jira 连接")
    parser.add_argument("--test-llm", action="store_true", help="测试 LM Studio 连接")
    parser.add_argument("--test-docs", action="store_true", help="测试文档检索")
    parser.add_argument("--test-all", action="store_true", help="运行所有测试")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Jira Analysis 真实数据测试")
    print("="*60)
    print(f"配置文件: config.yaml")
    print(f"Jira Server: {settings.jira_server}")
    print(f"LLM: {settings.llm_model} @ {settings.llm_base_url}")
    print(f"索引路径: {settings.index_base_path}")

    if args.test_all:
        asyncio.run(test_jira_connection())
        asyncio.run(test_lm_studio())
        asyncio.run(test_document_retrieval())

        # 如果提供了 issue key，也测试它
        if args.issue:
            asyncio.run(test_real_issue(args.issue))
    elif args.test_jira:
        asyncio.run(test_jira_connection())
    elif args.test_llm:
        asyncio.run(test_lm_studio())
    elif args.test_docs:
        asyncio.run(test_document_retrieval())
    elif args.issue:
        asyncio.run(test_real_issue(args.issue))
    else:
        parser.print_help()
        print("\n示例:")
        print("  python test_real_data.py --test-all              # 运行所有测试")
        print("  python test_real_data.py --test-jira             # 测试 Jira 连接")
        print("  python test_real_data.py --test-llm              # 测试 LM Studio")
        print("  python test_real_data.py --test-docs             # 测试文档检索")
        print("  python test_real_data.py --issue PROJ-123        # 分析指定 issue")


if __name__ == "__main__":
    main()
