# 本地测试指南

本指南帮助你使用本地 LLM（Ollama）和 mock 数据测试 jira-analysis 功能。

## 前置条件

### 1. 安装 Ollama

```bash
# Windows: 从官网下载安装
# https://ollama.ai/download

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. 下载模型

```bash
# 推荐使用 qwen2.5:14b（中文支持好）
ollama pull qwen2.5:14b

# 或者使用其他模型
ollama pull llama3.1:8b
ollama pull mistral:7b
```

### 3. 启动 Ollama 服务

```bash
ollama serve
```

## 配置

### 1. 复制配置文件

```bash
cd jira-analysis
cp config.example.yaml config.yaml
```

### 2. 编辑 config.yaml

```yaml
# LLM 配置
llm:
  base_url: "http://localhost:11434/v1"  # Ollama 默认地址
  model: "qwen2.5:14b"                   # 你下载的模型名称
  temperature: 0.1
  max_tokens: 4096
  api_key: "ollama"

# Jira 配置（本地测试可以使用假数据）
jira:
  server: "https://jira.example.com"
  email: "test@example.com"
  token: "fake-token-for-local-test"

# 本地测试模式
local_test:
  enabled: true
  use_mock_data: true
  mock_data_path: "./tests/fixtures"
```

## 运行测试

### 方法 1: 使用测试脚本（推荐）

```bash
# 安装依赖
cd jira-analysis
uv sync

# 运行本地测试
uv run python tests/local_test.py
```

测试脚本会依次测试：
1. ✅ 路由功能（根据 issue 类型选择分析 profile）
2. ✅ Prompt 构建（生成 LLM 输入）
3. ✅ LLM 客户端（调用本地 Ollama）
4. ✅ 完整分析流程（端到端测试）

### 方法 2: 交互式测试

```python
# 启动 Python REPL
cd jira-analysis
uv run python

# 导入模块
from pathlib import Path
from core.router import Router
from core.prompt_builder import PromptBuilder
from core.llm_client import LLMClient
from settings import settings
import json

# 加载 mock issue
with open("tests/fixtures/mock_issue_bug.json") as f:
    issue = json.load(f)

# 测试路由
router = Router(profiles_dir=Path("./src/profiles"))
profile = router.route(issue)
print(f"Profile: {profile.name}")

# 测试 LLM
llm = LLMClient(llm_config=settings.get_llm_config())
response = llm.generate("你好，请介绍一下你自己。")
print(response)
```

### 方法 3: 使用 CLI（需要真实索引）

如果你已经有了索引数据：

```bash
# 深度分析单个 issue
uv run jira-analysis deep TEST-123

# 批量分析
uv run jira-analysis batch TEST-100 TEST-101 TEST-102
```

## Mock 数据说明

测试使用的 mock 数据位于 `tests/fixtures/`：

- `mock_issue_bug.json` - Bug 类型的 issue
- `mock_issue_story.json` - Story 类型的 issue

你可以根据需要添加更多 mock 数据文件。

## 测试输出示例

```
============================================================
Jira Analysis 本地测试
============================================================
配置文件: config.yaml
Mock 数据: tests/fixtures/
LLM: qwen2.5:14b @ http://localhost:11434/v1

============================================================
测试 1: 路由功能
============================================================
✅ Bug issue 路由到 profile: rca
   - 描述: Root Cause Analysis for bugs

✅ Story issue 路由到 profile: traceability
   - 描述: Traceability analysis for features

============================================================
测试 2: Prompt 构建
============================================================
✅ Prompt 构建成功
   - 长度: 1234 字符
   - 前 200 字符预览:
   你是一个专业的软件工程师，负责分析 Jira issue...

============================================================
测试 3: LLM 客户端
============================================================
📝 LLM 配置:
   - Base URL: http://localhost:11434/v1
   - Model: qwen2.5:14b
   - Temperature: 0.1

🤖 测试 prompt: 请用一句话介绍你自己。
✅ LLM 响应成功:
   我是一个基于大语言模型的 AI 助手...

============================================================
测试 4: 完整分析流程（无索引）
============================================================
📋 分析 Issue: TEST-123
   标题: 用户登录失败 - 密码错误提示不明确
✅ 路由到 profile: rca
✅ Prompt 构建完成 (1456 字符)
🤖 正在调用 LLM 分析...

============================================================
分析结果:
============================================================
根据提供的信息，这个 Bug 的根本原因分析如下：

1. **问题定位**：错误提示不够明确
2. **影响范围**：用户体验
3. **建议修复**：在 AuthService.login() 中增加详细的错误分类...

============================================================

============================================================
测试完成！
============================================================
```

## 常见问题

### Q: Ollama 连接失败

**A:** 确保 Ollama 服务正在运行：
```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 如果失败，启动服务
ollama serve
```

### Q: 模型响应很慢

**A:** 
- 使用更小的模型（如 llama3.1:8b）
- 减少 `max_tokens` 配置
- 确保有足够的 GPU/CPU 资源

### Q: 想使用其他 LLM 服务

**A:** 修改 `config.yaml` 中的 LLM 配置：

```yaml
# 使用 OpenAI
llm:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"
  api_key: "your-openai-api-key"

# 使用本地 vLLM
llm:
  base_url: "http://localhost:8000/v1"
  model: "Qwen/Qwen2.5-14B-Instruct"
  api_key: "dummy"
```

### Q: 想测试真实的 Jira 数据

**A:** 
1. 在 `config.yaml` 中填入真实的 Jira 配置
2. 设置 `local_test.enabled: false`
3. 使用 CLI 命令分析真实 issue

## 下一步

- 📚 查看 [USAGE.md](./USAGE.md) 了解完整功能
- 🔧 查看 [IMPLEMENTATION.md](./IMPLEMENTATION.md) 了解架构设计
- 🧪 查看 [tests/e2e/README.md](./tests/e2e/README.md) 了解 E2E 测试
