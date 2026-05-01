# Jira Analysis System - 使用指南

## 目录

1. [快速开始](#快速开始)
2. [配置说明](#配置说明)
3. [使用方式](#使用方式)
4. [分析模式](#分析模式)
5. [故障排查](#故障排查)

---

## 快速开始

### 1. 安装依赖

```bash
cd jira-analysis
uv sync
```

### 2. 配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必需的配置：

```bash
# Jira 配置
JIRA_SERVER=https://jira.example.com
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your_jira_api_token

# LLM 配置（Ollama）
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=qwen2.5:14b
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096

# 索引路径（指向已有的索引）
INDEX_BASE_PATH=../datasource/data/indexes
```

### 3. 生成索引（首次使用）

如果还没有索引，需要先生成：

```bash
# 生成 Confluence 和规格文档索引
uv run jira-index generate \
  --confluence-dir ./data/confluence \
  --spec-dir ./data/specs \
  --persist-dir ./data/indexes
```

### 4. 启动服务

**方式 1：使用 LlamaDeploy（推荐）**

终端 1 - 启动 API 服务器：
```bash
uv run -m llama_deploy.apiserver
```

终端 2 - 部署工作流：
```bash
uv run llamactl deploy llama_deploy.yml
```

访问 UI：`http://localhost:4501/deployments/jira-analysis/ui`

**方式 2：使用 CLI 工具**

```bash
# 分析单个 issue
uv run jira-analysis analyze NVME-777 --mode balanced

# 批量分析
uv run jira-analysis batch NVME-777 NVME-778 NVME-779 --summary
```

---

## 配置说明

### Jira 配置

获取 Jira API Token：
1. 登录 Jira
2. 进入 Account Settings → Security → API Tokens
3. 创建新的 API Token
4. 复制 token 到 `.env` 文件

### LLM 配置

**使用 Ollama（推荐）**：

```bash
# 安装 Ollama
# 下载地址：https://ollama.ai

# 拉取模型
ollama pull qwen2.5:14b

# 启动 Ollama（默认监听 11434 端口）
ollama serve
```

**使用 LM Studio**：

```bash
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=your-model-name
```

### 索引配置

索引路径结构：

```
data/indexes/
├── jira/              # Jira issues 索引
├── confluence/        # Confluence 文档索引
└── specs/            # 规格文档索引
```

---

## 使用方式

### 1. CLI 命令

#### 分析单个 Issue

```bash
# 基本用法
uv run jira-analysis analyze PROJ-123

# 指定分析模式
uv run jira-analysis analyze PROJ-123 --mode strict

# 保存到文件
uv run jira-analysis analyze PROJ-123 --output report.md

# JSON 格式输出
uv run jira-analysis analyze PROJ-123 --format json --output report.json
```

#### 批量分析

```bash
# 分析多个 issues
uv run jira-analysis batch PROJ-123 PROJ-124 PROJ-125

# 生成汇总报告
uv run jira-analysis batch PROJ-123 PROJ-124 --summary

# 指定输出目录
uv run jira-analysis batch PROJ-123 PROJ-124 --output ./reports
```

#### 其他命令

```bash
# 查看可用的分析 profiles
uv run jira-analysis profiles

# 可视化工作流
uv run jira-analysis visualize --workflow deep --output workflow.html

# 运行诊断检查
uv run jira-analysis doctor --check-llm --check-jira --check-index
```

### 2. API 调用

#### 单个 Issue 分析

```bash
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_key\":\"NVME-777\",\"mode\":\"strict\"}",
    "service_id": "deep-analysis"
  }'
```

响应：
```json
{
  "task_id": "task-123",
  "session_id": "session-456"
}
```

#### 获取流式事件

```bash
curl 'http://localhost:4501/deployments/jira-analysis/tasks/task-123/events?session_id=session-456&raw_event=true'
```

#### 批量分析

```bash
curl -X POST 'http://localhost:4501/deployments/jira-analysis/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "{\"issue_keys\":[\"NVME-777\",\"NVME-778\"],\"mode\":\"balanced\"}",
    "service_id": "batch-analysis"
  }'
```

### 3. Web UI

访问 `http://localhost:4501/deployments/jira-analysis/ui`

**功能**：
- 输入 issue key 进行分析
- 实时查看分析进度
- 查看流式生成的分析报告
- 使用预设问题快速开始

**示例输入**：
- "分析 issue NVME-777"
- "批量分析 NVME-777, NVME-778, NVME-779"
- "使用严格模式分析 PROJ-123"

---

## 分析模式

### Strict（严格模式）

- **特点**：只基于明确的证据进行分析
- **适用场景**：需要高度准确性的场景，如正式报告
- **输出**：保守的结论，明确标注不确定的部分

```bash
uv run jira-analysis analyze PROJ-123 --mode strict
```

### Balanced（平衡模式，默认）

- **特点**：基于证据进行分析，允许合理推断
- **适用场景**：日常分析，平衡准确性和洞察力
- **输出**：区分确定的结论和可能的推测

```bash
uv run jira-analysis analyze PROJ-123 --mode balanced
```

### Exploratory（探索模式）

- **特点**：鼓励提出假设和可能性
- **适用场景**：复杂问题的初步调查，头脑风暴
- **输出**：多种可能的解释和调查方向

```bash
uv run jira-analysis analyze PROJ-123 --mode exploratory
```

---

## 分析 Profiles

系统根据 issue type 自动选择分析 profile：

### RCA (Root Cause Analysis) - 根因分析

**适用 Issue Types**：
- FW Bug
- HW Bug
- Test Bug
- Bug

**分析重点**：
- 失效机制
- 触发条件
- 根本原因
- 证据链

### Traceability - 需求追溯

**适用 Issue Types**：
- DAS/PRD
- MRD
- Requirement

**分析重点**：
- 需求来源
- 实现状态
- 验证情况
- 依赖关系

### Change Impact - 变更影响分析

**适用 Issue Types**：
- Requirement Change
- Component Change
- Change Request

**分析重点**：
- 直接影响
- 间接影响
- 风险评估
- 缓解措施

### General - 通用分析

**适用 Issue Types**：
- 其他所有类型（默认）

**分析重点**：
- 关键发现
- 技术细节
- 讨论要点

---

## 索引管理

### 生成索引

```bash
# 生成所有索引
uv run jira-index generate \
  --confluence-dir ./data/confluence \
  --spec-dir ./data/specs \
  --persist-dir ./data/indexes

# 自定义分块参数
uv run jira-index generate \
  --confluence-dir ./data/confluence \
  --spec-dir ./data/specs \
  --chunk-size 1024 \
  --chunk-overlap 100
```

### 更新索引

```bash
# 增量更新 Confluence 索引
uv run jira-index update \
  --index-name confluence \
  --new-docs-dir ./data/confluence/new

# 增量更新规格文档索引
uv run jira-index update \
  --index-name specifications \
  --new-docs-dir ./data/specs/new
```

### 测试索引

```bash
# 查询索引
uv run jira-index query \
  --index-name confluence \
  --query "authentication flow" \
  --top-k 5
```

---

## 故障排查

### 问题 1：LLM 连接失败

**症状**：
```
Failed to generate: Connection refused
```

**解决方案**：
1. 检查 Ollama 是否运行：`ollama list`
2. 检查端口：`curl http://localhost:11434/api/tags`
3. 验证 `.env` 中的 `LLM_BASE_URL` 配置

### 问题 2：Jira 认证失败

**症状**：
```
Failed to load issue: HTTP 401
```

**解决方案**：
1. 验证 API Token 是否有效
2. 检查 email 和 server URL 是否正确
3. 测试连接：
   ```bash
   uv run jira-analysis doctor --check-jira
   ```

### 问题 3：索引不存在

**症状**：
```
Index not found: ./data/indexes/confluence
```

**解决方案**：
1. 生成索引：
   ```bash
   uv run jira-index generate \
     --confluence-dir ./data/confluence \
     --spec-dir ./data/specs
   ```
2. 或者在 `.env` 中设置正确的索引路径

### 问题 4：分析超时

**症状**：
```
Timeout waiting for LLM response
```

**解决方案**：
1. 增加超时时间（`.env`）：
   ```bash
   LLM_MAX_TOKENS=8192
   ```
2. 使用更快的模型
3. 减少检索的证据数量（`settings.py`）

### 问题 5：内存不足

**症状**：
```
Out of memory
```

**解决方案**：
1. 减少批量分析的并发数：
   ```bash
   BATCH_MAX_CONCURRENT=3
   ```
2. 使用更小的模型
3. 减少索引的 chunk_size

---

## 高级配置

### 自定义 Profile

编辑 `src/profiles/config.json`：

```json
{
  "profiles": {
    "custom": {
      "name": "custom",
      "description": "Custom Analysis",
      "issue_types": ["Custom Type"],
      "prompt_template": "prompts/custom.txt",
      "output_sections": ["概述", "分析", "建议"]
    }
  }
}
```

创建 `src/profiles/prompts/custom.txt`。

### 调整检索参数

编辑 `src/settings.py`：

```python
# 检索配置
retrieve_similar_issues_top_k: int = 10  # 增加相似 issues 数量
retrieve_confluence_top_k: int = 5       # 增加 Confluence 文档数量
retrieve_spec_top_k: int = 5             # 增加规格文档数量
```

### 自定义 LLM 参数

编辑 `.env`：

```bash
LLM_TEMPERATURE=0.2      # 增加创造性
LLM_MAX_TOKENS=8192      # 增加输出长度
```

---

## 性能优化

### 1. 使用异步批量分析

```bash
# 增加并发数（默认 5）
BATCH_MAX_CONCURRENT=10
```

### 2. 缓存索引

索引会自动持久化到磁盘，无需每次重新生成。

### 3. 使用更快的模型

```bash
# 使用较小的模型
LLM_MODEL=qwen2.5:7b
```

### 4. 减少证据检索

```python
# 在 settings.py 中
retrieve_similar_issues_top_k: int = 3
retrieve_confluence_top_k: int = 2
retrieve_spec_top_k: int = 2
```

---

## 最佳实践

1. **首次使用**：先用 `doctor` 命令检查配置
2. **测试连接**：使用单个 issue 测试分析流程
3. **选择模式**：根据场景选择合适的分析模式
4. **批量分析**：控制并发数，避免过载
5. **定期更新**：定期更新索引以包含最新文档
6. **监控日志**：查看 `logs/jira-analysis.log` 了解详细信息

---

## 相关文档

- [README.md](README.md) - 项目概述
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - 实现细节
- [.planning/jira-analysis-design.md](.planning/jira-analysis-design.md) - 设计文档
- [ui/README.md](ui/README.md) - UI 文档
