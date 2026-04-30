# JIRA 和 Confluence 集成完整指南

## 文档概述

本文档整合了 JIRA 和 Confluence 连接器的实现细节、深度分析框架、示例数据和最佳实践。

---

## 目录

1. [JIRA 连接器实现](#jira-连接器实现)
2. [Confluence 连接器实现](#confluence-连接器实现)
3. [JIRA 深度分析框架](#jira-深度分析框架)
4. [示例数据](#示例数据)
5. [集成使用指南](#集成使用指南)

---

## JIRA 连接器实现

### 核心功能

#### 1. 连接测试
```python
result = await connector.test_connection()
# 返回 ConnectionTestResult(success, message, details)
```

#### 2. 初始同步（游标分页）
```python
result = await connector.fetch_initial(cursor=None)
# 返回 FetchResult(success, items_fetched, cursor, has_more, raw_data)
```

**特点**:
- 每次获取 50 条记录
- 返回下一个游标（最大 updated 时间）
- 支持断点续传

#### 3. 增量同步（时间过滤）
```python
since = datetime.now() - timedelta(days=7)
result = await connector.fetch_incremental(since)
# 返回 FetchResult(success, items_fetched, raw_data)
```

**特点**:
- 基于 `updated >= since` 过滤
- 每次获取 100 条记录
- 一次性获取所有更新

### Scope 支持

#### Single Issue
```python
config = JiraSourceConfig(
    scope_type=JiraScopeType.SINGLE_ISSUE,
    issue_key="NVME-777"
)
# JQL: issuekey = "NVME-777" order by updated asc
```

#### Project
```python
config = JiraSourceConfig(
    scope_type=JiraScopeType.PROJECT,
    project="NVME"
)
# JQL: project = "NVME" order by updated asc
```

#### Custom JQL
```python
config = JiraSourceConfig(
    scope_type=JiraScopeType.JQL,
    jql="project = NVME AND status = 'In Progress'"
)
# JQL: project = NVME AND status = 'In Progress' ORDER BY updated ASC
```

### 集成示例

```python
from packages.source_models import JiraSourceConfig, JiraScopeType
from services.connectors.jira import JiraConnector

# 创建配置
config = JiraSourceConfig(
    base_url="https://jira.example.com",
    credential_ref="jira_token",
    scope_type=JiraScopeType.PROJECT,
    project="NVME"
)

# 加载凭证
credential = load_credential(config.credential_ref)

# 初始化连接器
connector = JiraConnector(config, credential)

# 测试连接
result = await connector.test_connection()

# 初始同步
result = await connector.fetch_initial()

# 增量同步
result = await connector.fetch_incremental(since=last_sync_time)

# 转换为 Canonical Document
for raw_issue in result.raw_data:
    doc = connector.to_canonical(raw_issue)
```

---

## Confluence 连接器实现

### 核心功能

#### 1. 连接测试
```python
result = await connector.test_connection()
# 返回 ConnectionTestResult(success, message, details)
```

#### 2. 初始同步（游标分页）
```python
result = await connector.fetch_initial(cursor=None)
# 返回 FetchResult(success, items_fetched, cursor, has_more, raw_data)
```

**特点**:
- 每次获取 50 条记录
- 返回下一个游标（最大 modified 时间）
- 支持断点续传

#### 3. 增量同步（时间过滤）
```python
since = datetime.now() - timedelta(days=7)
result = await connector.fetch_incremental(since)
# 返回 FetchResult(success, items_fetched, raw_data)
```

**特点**:
- 基于 `lastmodified >= since` 过滤
- 每次获取 100 条记录
- 一次性获取所有更新

### Scope 支持

#### Single Page
```python
config = ConfluenceSourceConfig(
    scope_type=ConfluenceScopeType.SINGLE_PAGE,
    page_id="123456"
)
```

#### Space
```python
config = ConfluenceSourceConfig(
    scope_type=ConfluenceScopeType.SPACE,
    space_key="ENG"
)
```

### 集成示例

```python
from packages.source_models import ConfluenceSourceConfig, ConfluenceScopeType
from services.connectors.confluence import ConfluenceConnector

# 创建配置
config = ConfluenceSourceConfig(
    base_url="https://confluence.example.com",
    credential_ref="confluence_token",
    scope_type=ConfluenceScopeType.SPACE,
    space_key="ENG"
)

# 加载凭证
credential = load_credential(config.credential_ref)

# 初始化连接器
connector = ConfluenceConnector(config, credential)

# 测试连接
result = await connector.test_connection()

# 初始同步
result = await connector.fetch_initial()

# 增量同步
result = await connector.fetch_incremental(since=last_sync_time)

# 转换为 Canonical Document
for raw_page in result.raw_data:
    doc = connector.to_canonical(raw_page)
```

---

## JIRA 深度分析框架

### 问题类型路由（Issue Type Routing）

系统根据 Jira Issue Type 自动路由到不同的分析 profile：

| Issue Type | Issue Family | 分析路由 | 分析重点 |
|------------|--------------|----------|----------|
| FW Bug / HW Bug / Test Bug | `defect` | 根因分析 (RCA) | 失效机制、根因识别、修复方案 |
| DAS/PRD / MRD | `requirement` | 需求追溯分析 | 规格覆盖、实现状态、差距分析 |
| Requirement Change | `requirement_change` | 需求变更影响分析 | 变更范围、规格影响、兼容性 |
| Component Change | `change_control` | 变更影响分析 | 受影响组件、接口影响、验证策略 |
| Epic / Story / Task | `delivery` | 交付总结 | 进度、依赖、风险 |
| Release | `release` | 发布总结 | 发布范围、质量评估 |

### 分析维度

#### 1. 缺陷根因分析 (Defect RCA)

**分析要点**:
1. **根因识别** - 代码逻辑错误、配置错误、时序问题、资源竞争、边界条件处理
2. **失效机制** - 问题触发条件、错误传播路径、失效模式分类
3. **影响评估** - 严重程度、影响范围、用户可见性
4. **证据链** - 引用规格条款、设计文档、测试结果、代码片段
5. **修复建议** - 具体代码修改点、配置调整方案、测试验证方法
6. **预防措施** - 代码审查要点、测试用例增强、设计模式改进

#### 2. 需求追溯分析 (Requirement Traceability)

**分析要点**:
1. **规格覆盖** - 对应的规格条款、标准版本、强制性 vs 可选性要求
2. **实现状态** - 完全实现 / 部分实现 / 未实现、实现完整性评估
3. **差距分析** - 缺失的功能点、不符合规格的实现、性能指标差距
4. **依赖关系** - 硬件依赖、固件模块依赖、上下游需求依赖
5. **测试覆盖** - 单元测试覆盖率、集成测试场景、合规性测试
6. **风险评估** - 技术风险、进度风险、合规性风险

#### 3. 变更影响分析 (Change Impact Analysis)

**分析要点**:
1. **变更范围** - 涉及的功能模块、接口变更、配置参数变更
2. **规格影响** - 新增的合规性要求、受影响的规格条款、标准版本升级影响
3. **架构影响** - 系统架构变更、模块交互变更、性能影响
4. **兼容性** - 向后兼容性、与其他功能的兼容性、Host 兼容性
5. **测试影响** - 新增测试用例、修改的测试用例、回归测试范围
6. **风险评估** - 回归风险、性能风险、稳定性风险
7. **实施建议** - 分阶段实施方案、验证策略、回滚方案

### Prompt 设计模式

#### Prompt 结构

标准 Prompt 包含以下部分：

```
1. 角色定义 (Assistant Intro)
2. 任务指令 (Task Instruction)
3. 模式指令 (Mode Instructions)
4. 输出格式 (Output Format)
5. 上下文 (Context)
   - Jira 问题上下文
   - Confluence 证据
   - 规格说明证据
   - 图像证据状态
```

#### 三种 Prompt 模式

##### Strict Mode（严格模式）- 默认

**适用场景**: 合规性报告、正式文档、高风险决策

**核心原则**:
- 如果证据不能直接支持结论，明确说明证据不足
- 不推断未在检索证据中明确体现的事实
- 不超出 Jira 字段和评论的范围推断发布风险
- 当 Jira 提到验证、复测或未解决状态时，不说"无需后续跟进"

**Prompt 指令**:
```
模式：严格证据审查
如果证据不能直接支持结论，请明确说明证据不足。
不要推断未在检索证据中明确体现的事实。
```

##### Balanced Mode（平衡模式）

**适用场景**: 日常工程分析、技术讨论、问题诊断

**核心原则**:
- 区分直接证据和合理推断
- 指出不确定性
- 说明需要哪些额外证据来加强结论

**Prompt 指令**:
```
模式：平衡证据审查
区分直接证据和合理推断。
指出不确定性以及需要哪些额外证据来加强结论。
```

##### Exploratory Mode（探索模式）

**适用场景**: 早期问题探索、头脑风暴、假设验证

**核心原则**:
- 明确标注假设，不作为既定事实呈现
- 仅使用假设来建议后续检查
- 不声称最终结论

**Prompt 指令**:
```
模式：探索性证据审查
明确标注假设，不要将其作为既定事实呈现。
仅使用假设来建议后续检查，而非声称最终结论。
```

### 输出格式规范

标准输出包含 5 个部分：

```markdown
1. 概述：简明的问题概览（2-3 句话）

2. 跨源证据：引用 Confluence 和规格证据，标注文档 ID
   - Confluence: [文档ID] v[版本]: [证据片段]
   - 规格: [文档ID] v[版本]: [证据片段]

3. 分析：根据问题类型进行根因/追溯/影响分析
   - 根因分析: 失效机制、触发条件、根本原因
   - 追溯分析: 规格覆盖、实现状态、差距
   - 影响分析: 变更范围、受影响组件、风险

4. 差距：缺失的证据或未解答的问题
   - 列出需要补充的证据
   - 指出不确定的技术点

5. 建议：建议的后续步骤
   - 具体的行动项
   - 优先级排序
```

---

## 示例数据

### JIRA Issue 示例

```json
{
  "key": "NVME-777",
  "fields": {
    "summary": "FTL Mapping Table Overflow in Sequential Write Workload",
    "description": "When running sequential write workload with 4KB block size, FTL mapping table overflows after 2 hours of continuous operation. System becomes unresponsive and requires power cycle to recover.",
    "issuetype": {
      "name": "FW Bug"
    },
    "priority": {
      "name": "Critical"
    },
    "status": {
      "name": "In Progress"
    },
    "assignee": {
      "displayName": "Zhang Wei"
    },
    "created": "2024-04-10T08:30:00.000+0000",
    "updated": "2024-04-15T10:30:00.000+0000",
    "components": [
      {
        "name": "FTL"
      },
      {
        "name": "Memory Management"
      }
    ]
  },
  "comment": {
    "comments": [
      {
        "author": {
          "displayName": "Zhang Wei"
        },
        "body": "Initial investigation shows mapping table size calculation doesn't account for worst-case fragmentation scenario.",
        "created": "2024-04-12T14:20:00.000+0000"
      },
      {
        "author": {
          "displayName": "Li Ming"
        },
        "body": "Reviewed NVMe 1.4 spec section 5.3.2 - our implementation violates the error handling requirements.",
        "created": "2024-04-14T09:15:00.000+0000"
      }
    ]
  }
}
```

### Confluence 证据示例

```markdown
# FTL Mapping Table Design

**Document ID**: CONF-001
**Version**: 2024-04-10T12:00:00Z
**Space**: ENG

## Memory Allocation

The FTL mapping table is allocated 256MB of DRAM at system initialization. This allocation is based on:

- Maximum logical address space: 2TB
- Page size: 4KB
- Mapping granularity: 4KB (page-level mapping)
- Entry size: 8 bytes (physical address + metadata)

**Calculation**:
- Total pages: 2TB / 4KB = 536,870,912 pages
- Required memory: 536,870,912 × 8 bytes = 4GB

**Issue**: Current 256MB allocation only supports 33,554,432 pages (128GB logical space).

## Error Handling

Current implementation does not include overflow detection. When mapping table is full, new write requests overwrite existing entries, causing data corruption.

**Reference**: See NVMe 1.4 Specification Section 5.3.2 for required error handling behavior.
```

### 规格文档示例

```markdown
# NVMe 1.4 Specification Extract

**Document ID**: NVME-1.4
**Version**: 2021-06-01
**Section**: 5.3.2 Error Handling

## 5.3.2 Error Handling Requirements

When a controller encounters a resource exhaustion condition (e.g., mapping table overflow), it SHALL:

1. Return an appropriate status code to the host (Status Code 0x05: Capacity Exceeded)
2. Maintain data integrity for all previously committed writes
3. NOT silently drop or corrupt data
4. Log the error condition in the controller's error log

**Compliance Level**: MANDATORY

Controllers that fail to implement proper error handling for resource exhaustion conditions are NOT compliant with this specification.
```

### 深度分析输出示例

```markdown
# 深度分析报告：NVME-777

## 1. 概述

NVME-777 是一个关键的固件缺陷，涉及 FTL 映射表在顺序写入工作负载下发生溢出。问题导致系统无响应，需要断电重启才能恢复。根因是映射表内存分配不足，且缺少溢出检测机制。

## 2. 跨源证据

### Confluence 证据
- **CONF-001** v2024-04-10: "FTL mapping table is allocated 256MB of DRAM... Current 256MB allocation only supports 33,554,432 pages (128GB logical space)."
- **CONF-001** v2024-04-10: "Current implementation does not include overflow detection. When mapping table is full, new write requests overwrite existing entries, causing data corruption."

### 规格证据
- **NVME-1.4** v2021-06-01 Section 5.3.2: "When a controller encounters a resource exhaustion condition (e.g., mapping table overflow), it SHALL: 1. Return an appropriate status code to the host (Status Code 0x05: Capacity Exceeded)..."

## 3. 根因分析

### 失效机制
1. **触发条件**: 顺序写入工作负载，4KB 块大小，持续运行 2 小时
2. **传播路径**: 
   - 映射表条目逐渐填满 256MB 分配空间
   - 达到容量上限后，新写入请求覆盖现有条目
   - 数据完整性被破坏，系统进入不一致状态
   - 系统无响应，需要断电重启

### 根本原因
1. **内存分配不足**: 256MB 仅支持 128GB 逻辑空间，而系统声称支持 2TB
2. **缺少溢出检测**: 没有实现边界检查和错误处理
3. **违反规格要求**: 未按 NVMe 1.4 Section 5.3.2 要求返回错误状态码

### 影响评估
- **严重程度**: Critical（数据损坏，系统不可用）
- **影响范围**: FTL 模块、内存管理、数据完整性
- **用户可见性**: 高（系统挂起，需要断电重启）

## 4. 差距

### 缺失的证据
1. 实际测试日志和错误堆栈跟踪
2. 内存分配决策的历史背景（为什么选择 256MB？）
3. 是否有其他工作负载也会触发此问题
4. 修复方案的性能影响评估

### 未解答的问题
1. 为什么初始设计时没有考虑 2TB 的完整映射表需求？
2. 是否有其他模块也存在类似的资源分配不足问题？
3. 修复后如何确保不会影响正常工作负载的性能？

## 5. 建议

### 立即行动（P0）
1. **增加映射表内存分配**
   - 将 DRAM 分配从 256MB 增加到 4GB
   - 或实现两级映射表（L1 缓存 + L2 NAND）以减少 DRAM 需求
   
2. **实现溢出检测和错误处理**
   - 在映射表写入前检查容量
   - 返回 NVMe Status Code 0x05 (Capacity Exceeded)
   - 记录错误到控制器日志

### 验证测试（P0）
1. 使用相同工作负载（顺序写入，4KB，2+ 小时）验证修复
2. 测试边界条件（接近容量上限时的行为）
3. 验证错误处理路径（模拟资源耗尽场景）
4. 回归测试其他工作负载（随机读写、混合负载）

### 预防措施（P1）
1. **代码审查要点**: 所有资源分配必须包含容量规划和溢出检测
2. **测试用例增强**: 添加长时间运行测试和资源耗尽测试
3. **设计模式改进**: 实施资源配额管理和优雅降级机制

### 后续跟进（P2）
1. 审查其他固件模块的资源分配策略
2. 建立资源容量规划的设计检查清单
3. 更新设计文档，明确资源限制和错误处理要求
```

---

## 集成使用指南

### 完整工作流程

#### 1. 配置连接器

```python
# JIRA 配置
jira_config = JiraSourceConfig(
    base_url="https://jira.example.com",
    credential_ref="jira_token",
    scope_type=JiraScopeType.PROJECT,
    project="NVME"
)

# Confluence 配置
confluence_config = ConfluenceSourceConfig(
    base_url="https://confluence.example.com",
    credential_ref="confluence_token",
    scope_type=ConfluenceScopeType.SPACE,
    space_key="ENG"
)
```

#### 2. 同步数据

```python
# 初始化连接器
jira_connector = JiraConnector(jira_config, jira_credential)
confluence_connector = ConfluenceConnector(confluence_config, confluence_credential)

# 初始同步
jira_result = await jira_connector.fetch_initial()
confluence_result = await confluence_connector.fetch_initial()

# 增量同步（每日）
since = datetime.now() - timedelta(days=1)
jira_updates = await jira_connector.fetch_incremental(since)
confluence_updates = await confluence_connector.fetch_incremental(since)
```

#### 3. 执行深度分析

```python
from services.analysis.deep_analysis import build_deep_analysis_payload
from services.analysis.jira_issue_analysis import build_jira_batch_spec_report

# 单个 Issue 分析
payload = build_deep_analysis_payload(
    jira_document=jira_doc,
    confluence_documents=conf_docs,
    spec_documents=spec_docs,
    allowed_policies={"public"},
    prompt_mode="strict",  # strict | balanced | exploratory
    llm_backend=llm_backend  # 可选
)

# 批量分析
report = build_jira_batch_spec_report(
    workspace_id="nvme-project",
    updated_from_iso="2024-04-01T00:00:00Z",
    updated_to_iso="2024-04-30T23:59:59Z",
    prompt_mode="strict"
)
```

#### 4. 生成报告

```python
# 提取式答案（无需 LLM）
if not llm_backend:
    print(f"找到跨源证据：{len(conf_docs)}条Confluence证据 和{len(spec_docs)}条规格证据")
    for doc in conf_docs:
        print(f"- {doc.document_id} v{doc.version}: {doc.content[:100]}...")

# LLM 增强答案
else:
    response = await llm_backend.generate(payload["prompt"])
    print(response)
```

### 最佳实践

#### 1. 选择合适的 Prompt 模式

| 场景 | 推荐模式 | 原因 |
|------|---------|------|
| 合规性报告 | Strict | 需要严格的证据支持，避免推断 |
| 日常工程分析 | Balanced | 平衡证据和推理，指出不确定性 |
| 早期问题探索 | Exploratory | 允许假设，帮助发现调查方向 |
| 正式文档 | Strict | 确保准确性和可追溯性 |
| 技术讨论 | Balanced | 促进深入讨论和知识共享 |

#### 2. 优化检索质量

```python
# 增加检索范围
top_k = 5  # 默认 3

# 使用检索增强
from services.analysis.search_enhancer import build_enhanced_search_query

enhanced_query = build_enhanced_search_query(
    base_query="FTL mapping table overflow",
    section_name="rca",  # rca | spec_impact | decision_brief | general_summary
    issue_type="FW Bug"
)
```

#### 3. 处理缺失证据

```python
# 检查证据质量
if len(conf_docs) == 0:
    print("警告：未找到 Confluence 证据，建议使用 exploratory 模式")
    prompt_mode = "exploratory"

if len(spec_docs) == 0:
    print("警告：未找到规格证据，分析可能不完整")
```

#### 4. 批量分析优化

```python
# 使用时间窗口过滤
updated_from = datetime.now() - timedelta(days=7)
updated_to = datetime.now()

# 分批处理
batch_size = 10
for i in range(0, len(issues), batch_size):
    batch = issues[i:i+batch_size]
    results = await analyze_batch(batch)
    save_results(results)
```

### 故障排查

#### 常见问题

**Q1: 连接测试失败**
```python
# 检查配置
print(f"Base URL: {config.base_url}")
print(f"Credential: {credential}")

# 测试网络连接
import requests
response = requests.get(config.base_url)
print(f"Status: {response.status_code}")
```

**Q2: 检索不到相关证据**
```python
# 检查 ACL Policy
print(f"Allowed policies: {allowed_policies}")

# 扩大检索范围
top_k = 10  # 增加到 10

# 调整搜索关键词
keywords = extract_keywords(jira_doc, min_length=3, max_keywords=10)
```

**Q3: LLM 生成超时**
```python
# 增加超时时间
llm_backend = LLMBackend(
    name="openai-compatible",
    base_url="http://localhost:1234/v1",
    model="qwen2.5-14b-instruct",
    timeout_seconds=120  # 增加到 120 秒
)
```

---

## 附录

### A. 核心代码文件

| 文件路径 | 功能 |
|---------|------|
| `services/connectors/jira/unified_connector.py` | JIRA 连接器实现 |
| `services/connectors/confluence/unified_connector.py` | Confluence 连接器实现 |
| `services/analysis/deep_analysis.py` | 深度分析核心逻辑 |
| `services/analysis/jira_issue_analysis.py` | JIRA 问题分析 |
| `services/analysis/jira_profiles.py` | Prompt 构建 |
| `services/connectors/jira/issue_type_profiles.py` | 问题类型路由 |
| `packages/schema/jira-issue-type-profiles.json` | 路由配置 |

### B. 相关文档

- `docs/jira-connector-implementation.md` - JIRA 连接器实现总结
- `docs/confluence-connector-implementation.md` - Confluence 连接器实现总结
- `docs/jira-deep-analysis-guide.md` - JIRA 深度分析指南
- `docs/modules/jira-analysis-reporting.md` - 模块契约
- `docs/ENHANCED_RETRIEVAL.md` - 增强检索策略

### C. 测试文件

- `services/connectors/jira/test_unified_connector.py` - JIRA 连接器测试
- `services/connectors/confluence/test_unified_connector.py` - Confluence 连接器测试
- `tests/analysis/test_jira_issue_analysis.py` - 分析功能测试
- `tests/phase3_integration_test.py` - 集成测试
- `test_deep_analysis_e2e.py` - 端到端测试

---

**文档版本**: v1.0  
**创建日期**: 2026-04-30  
**维护者**: Codex Team
