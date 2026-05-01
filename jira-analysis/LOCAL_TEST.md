# 本地测试指南

本指南介绍如何使用 **LM Studio + 真实数据** 在本地测试 jira-analysis 系统。

## 测试方案

- **LLM**: LM Studio（本地运行，无需 API key）
- **数据源**: 真实的 Jira Server + PDF/Excel 规格文档
- **索引**: 使用 datasource 构建的向量索引

## 前置准备

### 1. 安装 LM Studio

1. 下载 LM Studio: https://lmstudio.ai/
2. 安装并启动 LM Studio
3. 下载推荐模型（选择其一）：
   - **Qwen2.5 14B Instruct** (推荐，中英文支持好)
   - **Llama 3.1 8B Instruct** (英文，速度快)
   - **Mistral 7B Instruct** (英文，质量高)

4. 启动本地服务器：
   - 在 LM Studio 中点击 "Local Server"
   - 加载你下载的模型
   - 点击 "Start Server"
   - 默认地址: `http://localhost:1234/v1`

5. 验证服务器运行：
   ```bash
   curl http://localhost:1234/v1/models
   ```

### 2. 准备 Jira 凭证

1. 登录你的 Jira Server
2. 生成 API Token:
   - 访问: https://id.atlassian.com/manage-profile/security/api-tokens
   - 点击 "Create API token"
   - 复制生成的 token

### 3. 准备文档索引

使用 `datasource` 项目构建索引：

```bash
# 进入 datasource 目录
cd ../datasource

# 索引 Jira issues
uv run datasource index jira \
  --server https://your-company.atlassian.net \
  --email your-email@company.com \
  --token YOUR_API_TOKEN

# 索引本地文档（PDF/Excel/Word）
uv run datasource index local \
  --path /path/to/your/specs \
  --name specs

# 查看索引状态
uv run datasource list
```

索引将保存在 `datasource/data/indexes/` 目录。

## 配置

### 1. 创建配置文件

```bash
cd jira-analysis
cp config.example.yaml config.yaml
```

### 2. 编辑 `config.yaml`

```yaml
# Jira 配置（填入你的真实凭证）
jira:
  server: "https://your-company.atlassian.net"
  email: "your-email@company.com"
  token: "your-api-token-here"

# LLM 配置（LM Studio）
llm:
  base_url: "http://localhost:1234/v1"
  model: "qwen2.5-14b-instruct"  # 你在 LM Studio 中加载的模型名称
  temperature: 0.1
  max_tokens: 4096
  api_key: "lm-studio"

# 索引配置
index:
  base_path: "../datasource/data/indexes"
  sources:
    - jira      # Jira issues 索引
    - specs     # 规格文档索引

# 本地测试模式（使用真实数据时设为 false）
local_test:
  enabled: false
  use_mock_data: false

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/jira-analysis.log"
```

## 运行测试

### 1. 测试连接

```bash
# 测试 Jira 连接
python test_real_data.py --test-jira

# 测试 LM Studio 连接
python test_real_data.py --test-llm

# 测试文档检索
python test_real_data.py --test-docs

# 运行所有连接测试
python test_real_data.py --test-all
```

### 2. 分析真实 Issue

```bash
# 分析指定的 issue
python test_real_data.py --issue PROJ-123

# 示例输出：
# ============================================================
# 测试真实 Issue: PROJ-123
# ============================================================
#
# 📥 步骤 1: 从 Jira Server 加载 issue
#    Server: https://your-company.atlassian.net
# ✅ Issue 加载成功
#    Key: PROJ-123
#    标题: 用户登录失败
#    类型: Bug
#    状态: Open
#
# 🔀 步骤 2: 路由分析 profile
# ✅ 路由到 profile: bug
#    描述: Bug 分析 profile
#    分析模式: balanced
#
# 🔍 步骤 3: 从索引检索相关证据
#    索引路径: ../datasource/data/indexes
# ✅ 检索到 8 条证据:
#    📋 相似 issues: 3 个
#       - PROJ-100: 登录超时问题
#       - PROJ-89: 认证失败
#    📚 规格文档: 5 个
#       - 用户认证设计文档.pdf
#       - API接口规范.xlsx
#
# 📝 步骤 4: 构建 LLM prompt
# ✅ Prompt 构建完成
#    长度: 2345 字符
#
# 🤖 步骤 5: 调用 LLM 分析
#    LLM: qwen2.5-14b-instruct
#    Base URL: http://localhost:1234/v1
#    正在生成分析结果...
#
# ============================================================
# 分析结果:
# ============================================================
# [LLM 生成的分析报告]
# ============================================================
```

### 3. 完整工作流测试

```bash
# 使用 pytest 运行完整测试
pytest tests/local_test.py -v

# 测试包括：
# - 路由测试（验证 issue type 到 profile 的映射）
# - Prompt 构建测试（验证 prompt 模板渲染）
# - LLM 客户端测试（验证 LM Studio 调用）
# - 完整流程测试（端到端验证）
```

## 测试场景

### 场景 1: Bug 分析

```bash
# 1. 在 Jira 中找一个 Bug issue
# 2. 运行分析
python test_real_data.py --issue BUG-123

# 预期结果：
# - 路由到 bug profile
# - 检索相似的 bug issues
# - 检索相关的技术文档
# - 生成根因分析和修复建议
```

### 场景 2: Story 分析

```bash
# 1. 在 Jira 中找一个 Story issue
# 2. 运行分析
python test_real_data.py --issue STORY-456

# 预期结果：
# - 路由到 story profile
# - 检索相关的需求文档
# - 检索类似的 story
# - 生成实现建议和验收标准
```

### 场景 3: 批量分析

```bash
# 使用 CLI 进行批量分析
uv run jira-analysis batch \
  --jql "project = PROJ AND status = Open" \
  --output ./reports/batch_analysis.json

# 预期结果：
# - 批量加载多个 issues
# - 并发分析（默认 5 个并发）
# - 生成 JSON 报告
```

## 验证清单

### ✅ 基础功能

- [ ] Jira 连接成功
- [ ] LM Studio 连接成功
- [ ] 文档索引可访问
- [ ] 路由逻辑正确（Bug → bug profile, Story → story profile）
- [ ] Prompt 构建成功

### ✅ 检索功能

- [ ] 可以检索相似的 Jira issues
- [ ] 可以检索相关的 PDF 文档
- [ ] 可以检索相关的 Excel 文档
- [ ] 检索结果相关性高

### ✅ LLM 分析

- [ ] LM Studio 响应正常
- [ ] 分析结果质量高
- [ ] 响应时间可接受（< 30 秒）
- [ ] 支持中英文分析

### ✅ 端到端流程

- [ ] 单个 issue 分析成功
- [ ] 批量分析成功
- [ ] 错误处理正确
- [ ] 日志记录完整

## 常见问题

### Q1: LM Studio 连接失败

**错误**: `Connection refused to http://localhost:1234`

**解决**:
1. 确认 LM Studio 正在运行
2. 确认已加载模型
3. 确认服务器已启动（Local Server 标签页）
4. 测试连接: `curl http://localhost:1234/v1/models`

### Q2: Jira 认证失败

**错误**: `401 Unauthorized`

**解决**:
1. 检查 Jira Server URL 是否正确
2. 检查 email 是否正确
3. 重新生成 API Token
4. 测试连接:
   ```bash
   curl -u your-email@company.com:YOUR_TOKEN \
     https://your-company.atlassian.net/rest/api/2/myself
   ```

### Q3: 索引不存在

**错误**: `Index not found: specs`

**解决**:
1. 使用 datasource 构建索引:
   ```bash
   cd ../datasource
   uv run datasource index local --path /path/to/docs --name specs
   ```
2. 检查索引路径配置是否正确
3. 运行 `uv run datasource list` 查看可用索引

### Q4: 检索结果为空

**可能原因**:
1. 索引中没有相关文档
2. 查询文本太短或太模糊
3. 相似度阈值太高

**解决**:
1. 检查索引内容: `uv run datasource list --verbose`
2. 调整 `config.yaml` 中的 `similarity_threshold`
3. 使用更具体的查询文本

### Q5: LLM 响应太慢

**优化建议**:
1. 使用更小的模型（如 7B 而非 14B）
2. 减少 `max_tokens` 配置
3. 减少检索的证据数量（`max_evidence_items`）
4. 使用 GPU 加速（在 LM Studio 设置中启用）

### Q6: 分析结果质量不佳

**优化建议**:
1. 使用更大的模型（如 14B 或 70B）
2. 调整 `temperature` 参数（降低以获得更确定的结果）
3. 优化 prompt 模板（`src/prompts/*.txt`）
4. 增加检索的证据数量
5. 改进索引质量（添加更多相关文档）

## 性能基准

### 硬件配置

- CPU: Intel i7-12700K
- RAM: 32GB
- GPU: NVIDIA RTX 3080 (10GB)

### 性能指标

| 模型 | 参数量 | 加载时间 | 推理速度 | 内存占用 |
|------|--------|----------|----------|----------|
| Qwen2.5 Instruct | 14B | ~10s | ~20 tokens/s | ~8GB |
| Llama 3.1 Instruct | 8B | ~5s | ~35 tokens/s | ~5GB |
| Mistral Instruct | 7B | ~5s | ~40 tokens/s | ~4.5GB |

### 端到端延迟

| 操作 | 平均时间 |
|------|----------|
| 加载 issue | ~500ms |
| 检索证据 | ~1-2s |
| 构建 prompt | ~100ms |
| LLM 分析 | ~15-30s |
| **总计** | **~20-35s** |

## 下一步

完成本地测试后，你可以：

1. **部署到生产环境**:
   - 切换到 OpenAI API 或其他云端 LLM
   - 配置生产级索引
   - 启用 Web UI

2. **优化性能**:
   - 使用更快的模型
   - 启用缓存
   - 批量处理

3. **扩展功能**:
   - 添加更多分析 profiles
   - 自定义 prompt 模板
   - 集成更多数据源

## 参考资料

- [LM Studio 文档](https://lmstudio.ai/docs)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v2/)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)
- [项目 README](./README.md)
