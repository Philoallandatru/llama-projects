"""测试 Jira 和 LLM 连接"""

import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from settings import settings
import aiohttp

# Windows 控制台编码问题，使用 ASCII 字符
OK = "[OK]"
FAIL = "[FAIL]"


async def test_jira_connection():
    """测试 Jira 连接"""
    print("=" * 60)
    print("测试 Jira 连接")
    print("=" * 60)

    print(f"服务器: {settings.jira_server}")
    print(f"邮箱: {settings.jira_email}")

    try:
        # 测试基本连接
        auth = aiohttp.BasicAuth(settings.jira_email, settings.jira_token)
        async with aiohttp.ClientSession(auth=auth) as session:
            # 获取当前用户信息
            url = f"{settings.jira_server}/rest/api/2/myself"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[OK] Jira 连接成功")
                    print(f"  用户: {data.get('displayName')}")
                    print(f"  邮箱: {data.get('emailAddress')}")
                else:
                    print(f"[FAIL] Jira 连接失败: HTTP {response.status}")
                    return False

            # 搜索最近的 issues
            search_url = f"{settings.jira_server}/rest/api/2/search"
            params = {
                "jql": "ORDER BY created DESC",
                "maxResults": 5,
                "fields": "key,summary,status,issuetype,project"
            }
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    total = data.get('total', 0)
                    issues = data.get('issues', [])
                    print(f"[OK] 可访问 {total} 个 issues")
                    if issues:
                        print(f"  最近的 issues:")
                        for issue in issues[:5]:
                            key = issue['key']
                            summary = issue['fields']['summary']
                            status = issue['fields']['status']['name']
                            project = issue['fields']['project']['key']
                            print(f"    - {key} ({project}): {summary} [{status}]")
                else:
                    print(f"[FAIL] 搜索 issues 失败: HTTP {response.status}")

        return True
    except Exception as e:
        print(f"[FAIL] Jira 连接失败: {e}")
        return False


async def test_llm_connection():
    """测试 LLM 连接"""
    print("\n" + "=" * 60)
    print("测试 LLM 连接")
    print("=" * 60)

    print(f"服务器: {settings.llm_base_url}")
    print(f"模型: {settings.llm_model}")

    try:
        async with aiohttp.ClientSession() as session:
            # 测试模型列表
            url = f"{settings.llm_base_url}/models"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m['id'] for m in data.get('data', [])]
                    print(f"[OK] LLM 服务连接成功")
                    print(f"  可用模型: {', '.join(models)}")

                    if settings.llm_model in models:
                        print(f"  [OK] 配置的模型 '{settings.llm_model}' 可用")
                    else:
                        print(f"  [FAIL] 配置的模型 '{settings.llm_model}' 不在可用列表中")
                        return False
                else:
                    print(f"[FAIL] LLM 连接失败: HTTP {response.status}")
                    return False

            # 测试简单的 completion
            completion_url = f"{settings.llm_base_url}/chat/completions"
            payload = {
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            async with session.post(completion_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    print(f"[OK] LLM 推理测试成功")
                    print(f"  响应: {content[:50]}...")
                else:
                    print(f"[FAIL] LLM 推理失败: HTTP {response.status}")
                    return False

        return True
    except Exception as e:
        print(f"[FAIL] LLM 连接失败: {e}")
        return False


async def main():
    """主测试函数"""
    jira_ok = await test_jira_connection()
    llm_ok = await test_llm_connection()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"Jira 连接: {'[OK] 成功' if jira_ok else '[FAIL] 失败'}")
    print(f"LLM 连接: {'[OK] 成功' if llm_ok else '[FAIL] 失败'}")

    if jira_ok and llm_ok:
        print("\n[OK] 所有连接测试通过，可以开始使用系统")
        return 0
    else:
        print("\n[FAIL] 部分连接测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
