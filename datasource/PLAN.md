# DataSource 项目实施计划

## 项目概述

构建统一的数据源管理系统，支持 Jira、Confluence、本地文件的抓取、索引和检索，并集成到 chat 项目中。

## 设计原则

- **简化优先**：移除 Snapshot 概念，扁平化配置
- **统一接口**：单一 Manager 类作为入口
- **混合检索**：Vector + BM25 混合索引
- **可验收**：每个阶段都有明确的验收标准

## 项目里程碑

| 阶段 | 目标 | 预计时间 | 状态 |
|------|------|---------|------|
| Phase 1 | 基础设施 | 1 天 | ⬜ 未开始 |
| Phase 2 | 本地文件支持 | 2 天 | ⬜ 未开始 |
| Phase 3 | 索引和检索 | 2 天 | ⬜ 未开始 |
| Phase 4 | Jira 支持 | 2 天 | ⬜ 未开始 |
| Phase 5 | chat 集成 | 1 天 | ⬜ 未开始 |
| Phase 6 | 文档和优化 | 1 天 | ⬜ 未开始 |

**总计**：9 天

---

## Phase 1: 基础设施

### 目标

搭建项目骨架，实现数据模型、路径管理、配置系统。

### 任务清单

- [ ] 1.1 创建项目目录结构
- [ ] 1.2 实现数据模型（models.py）
- [ ] 1.3 实现路径管理（paths.py）
- [ ] 1.4 实现配置管理（config.py）
- [ ] 1.5 实现基类（BaseDataSource）
- [ ] 1.6 编写单元测试
- [ ] 1.7 代码审查

### 验收标准

#### 功能验收

- [ ] `SourceConfig` 可以序列化为 YAML 并反序列化
- [ ] `Paths` 类能正确生成所有路径
- [ ] `BaseDataSource` 定义了清晰的抽象接口
- [ ] 所有单元测试通过

#### 代码质量

- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 无 mypy 错误
- [ ] 无 pylint 警告

#### 交付物

- [ ] `datasource/core/models.py`
- [ ] `datasource/core/paths.py`
- [ ] `datasource/core/sources/base.py`
- [ ] `tests/test_models.py`
- [ ] `tests/test_paths.py`
- [ ] `PHASE1_REVIEW.md`（代码审查报告）

### 验收测试

```bash
# 运行测试
pytest tests/test_models.py tests/test_paths.py -v

# 类型检查
mypy datasource/core/models.py datasource/core/paths.py

# 代码质量检查
pylint datasource/core/models.py datasource/core/paths.py
```

---

## Phase 2: 本地文件支持

### 目标

实现本地文件数据源，支持 PDF、Word、Markdown 等格式的解析。

### 任务清单

- [ ] 2.1 实现 LocalDataSource
- [ ] 2.2 实现文件解析器（PDF/Word/Markdown）
- [ ] 2.3 实现 SourceManager（add/list/get/show/delete）
- [ ] 2.4 实现 CLI 基础命令（add/list/show/delete）
- [ ] 2.5 编写单元测试
- [ ] 2.6 编写集成测试
- [ ] 2.7 代码审查

### 验收标准

#### 功能验收

- [ ] 能添加本地文件数据源
- [ ] 能扫描目录并识别支持的文件类型
- [ ] 能解析 PDF、Word、Markdown 文件
- [ ] CLI 命令正常工作
- [ ] 所有测试通过

#### 性能验收

- [ ] 扫描 100 个文件 < 10 秒
- [ ] 解析单个 PDF（10 页）< 5 秒

#### 代码质量

- [ ] 类型注解完整
- [ ] 错误处理完善
- [ ] 日志记录清晰
- [ ] 无代码重复

#### 交付物

- [ ] `datasource/core/sources/local.py`
- [ ] `datasource/core/manager.py`（部分实现）
- [ ] `datasource/cli.py`（部分实现）
- [ ] `tests/test_local_source.py`
- [ ] `tests/test_manager.py`
- [ ] `tests/integration/test_local_workflow.py`
- [ ] `PHASE2_REVIEW.md`

### 验收测试

```bash
# 单元测试
pytest tests/test_local_source.py tests/test_manager.py -v

# 集成测试
pytest tests/integration/test_local_workflow.py -v

# 手动测试
python -m datasource.cli add test_local --type local --path ./test_data
python -m datasource.cli list
python -m datasource.cli show test_local
python -m datasource.cli delete test_local
```

---

## Phase 3: 索引和检索

### 目标

实现混合索引（Vector + BM25）和统一检索接口。

### 任务清单

- [ ] 3.1 实现同步逻辑（fetch + build + index）
- [ ] 3.2 实现向量索引构建
- [ ] 3.3 实现 BM25 索引构建
- [ ] 3.4 实现混合检索
- [ ] 3.5 实现 CLI sync 和 query 命令
- [ ] 3.6 编写单元测试
- [ ] 3.7 编写集成测试
- [ ] 3.8 代码审查

### 验收标准

#### 功能验收

- [ ] `sync` 命令能完整执行（抓取 + 索引）
- [ ] 向量索引能正确持久化和加载
- [ ] BM25 索引能正确持久化和加载
- [ ] 混合检索返回相关结果
- [ ] 查询结果按 score 排序
- [ ] 所有测试通过

#### 性能验收

- [ ] 100 个文档索引构建 < 30 秒
- [ ] 查询响应时间 < 2 秒
- [ ] 索引大小 < 原始数据的 50%

#### 质量验收

- [ ] 查询准确率（Top 5）> 80%
- [ ] 混合检索优于单一检索

#### 代码质量

- [ ] 索引构建逻辑清晰
- [ ] 错误处理完善（部分失败不影响整体）
- [ ] 进度提示友好

#### 交付物

- [ ] `datasource/core/manager.py`（完整实现）
- [ ] `datasource/cli.py`（完整实现）
- [ ] `tests/test_indexing.py`
- [ ] `tests/test_retrieval.py`
- [ ] `tests/integration/test_sync_workflow.py`
- [ ] `tests/integration/test_query_workflow.py`
- [ ] `PHASE3_REVIEW.md`

### 验收测试

```bash
# 单元测试
pytest tests/test_indexing.py tests/test_retrieval.py -v

# 集成测试
pytest tests/integration/test_sync_workflow.py -v
pytest tests/integration/test_query_workflow.py -v

# 手动测试
python -m datasource.cli add test_local --type local --path ./test_data
python -m datasource.cli sync test_local
python -m datasource.cli query test_local "测试查询"

# 性能测试
python tests/benchmark/test_performance.py
```

---

## Phase 4: Jira 支持

### 目标

实现 Jira 数据源，支持 issue 抓取、附件下载、评论提取。

### 任务清单

- [ ] 4.1 实现 JiraDataSource
- [ ] 4.2 实现 issue 抓取（分页、字段提取）
- [ ] 4.3 实现附件下载（图片过滤、大小限制）
- [ ] 4.4 实现评论提取
- [ ] 4.5 实现重试和限流
- [ ] 4.6 编写单元测试（mock Jira API）
- [ ] 4.7 编写集成测试（真实 Jira）
- [ ] 4.8 代码审查

### 验收标准

#### 功能验收

- [ ] 能连接 Jira 并认证
- [ ] 能根据 JQL 查询 issues
- [ ] 能提取所有必要字段
- [ ] 能下载图片附件
- [ ] 能提取评论
- [ ] 失败的 issue 记录在 errors 中
- [ ] 所有测试通过

#### 性能验收

- [ ] 1000 个 issues 同步 < 5 分钟
- [ ] 附件下载成功率 > 95%
- [ ] 并发请求不超过 Jira 限制

#### 质量验收

- [ ] 查询 Jira 数据准确率 > 90%
- [ ] 附件正确关联到 issue

#### 代码质量

- [ ] API 调用有重试机制
- [ ] 限流控制合理
- [ ] 错误处理完善
- [ ] 日志记录详细

#### 交付物

- [ ] `datasource/core/sources/jira.py`
- [ ] `tests/test_jira_source.py`
- [ ] `tests/integration/test_jira_workflow.py`
- [ ] `.env.example`（Jira 配置示例）
- [ ] `PHASE4_REVIEW.md`

### 验收测试

```bash
# 单元测试（mock）
pytest tests/test_jira_source.py -v

# 集成测试（需要真实 Jira）
export JIRA_EMAIL="test@example.com"
export JIRA_API_TOKEN="xxx"
pytest tests/integration/test_jira_workflow.py -v

# 手动测试
python -m datasource.cli add jira_test \
  --type jira \
  --server https://jira.company.com \
  --project TEST

python -m datasource.cli sync jira_test
python -m datasource.cli query jira_test "bug"
```

---

## Phase 5: chat 集成

### 目标

将 DataSource 集成到 chat 项目，实现 Agent 自动调用数据源工具。

### 任务清单

- [ ] 5.1 实现 `get_query_engine()` 方法
- [ ] 5.2 修改 chat/src/workflow.py 集成 DataSource
- [ ] 5.3 测试 Agent 工具调用
- [ ] 5.4 测试引用系统
- [ ] 5.5 编写集成测试
- [ ] 5.6 编写端到端测试
- [ ] 5.7 代码审查

### 验收标准

#### 功能验收

- [ ] chat Agent 能列出所有数据源工具
- [ ] Agent 能根据查询自动选择工具
- [ ] 查询结果包含正确的引用
- [ ] UI 能显示数据源来源
- [ ] 所有测试通过

#### 用户体验验收

- [ ] 查询响应时间 < 5 秒
- [ ] 引用链接可点击
- [ ] 错误提示友好

#### 质量验收

- [ ] Agent 工具选择准确率 > 90%
- [ ] 引用提取准确率 > 95%

#### 代码质量

- [ ] 集成代码简洁
- [ ] 不破坏原有功能
- [ ] 错误处理完善

#### 交付物

- [ ] `datasource/core/manager.py`（添加 get_query_engine）
- [ ] `chat/src/workflow.py`（集成修改）
- [ ] `tests/integration/test_chat_integration.py`
- [ ] `tests/e2e/test_chat_workflow.py`
- [ ] `INTEGRATION_GUIDE.md`
- [ ] `PHASE5_REVIEW.md`

### 验收测试

```bash
# 集成测试
pytest tests/integration/test_chat_integration.py -v

# 端到端测试
cd ../chat
uv run -m llama_deploy.apiserver &
uv run llamactl deploy llama_deploy.yml

# 手动测试（通过 UI）
# 1. 访问 http://localhost:4501/deployments/chat/ui
# 2. 输入: "查询 test_local 中关于 S4 的问题"
# 3. 验证: Agent 调用 query_test_local 工具
# 4. 验证: 返回结果包含引用链接
```

---

## Phase 6: 文档和优化

### 目标

完善文档、优化性能、修复 bug。

### 任务清单

- [ ] 6.1 编写 README.md
- [ ] 6.2 编写 API 文档
- [ ] 6.3 更新 CLAUDE.md
- [ ] 6.4 性能优化（如有必要）
- [ ] 6.5 修复已知 bug
- [ ] 6.6 代码重构（如有必要）
- [ ] 6.7 最终代码审查

### 验收标准

#### 文档验收

- [ ] README 包含安装、使用、示例
- [ ] API 文档完整
- [ ] CLAUDE.md 包含集成指南
- [ ] 所有命令有使用示例

#### 质量验收

- [ ] 所有测试通过
- [ ] 代码覆盖率 > 80%
- [ ] 无已知严重 bug
- [ ] 性能满足目标

#### 交付物

- [ ] `README.md`
- [ ] `API.md`
- [ ] `CLAUDE.md`（更新）
- [ ] `CHANGELOG.md`
- [ ] `PHASE6_REVIEW.md`
- [ ] `PROJECT_SUMMARY.md`

### 验收测试

```bash
# 运行所有测试
pytest tests/ -v --cov=datasource --cov-report=html

# 检查文档
# 1. 按照 README 从头安装
# 2. 运行所有示例代码
# 3. 验证所有链接有效
```

---

## 代码审查流程

### 每个 Phase 完成后

1. **自我审查**
   - 检查代码是否符合设计
   - 检查是否有明显 bug
   - 检查是否有代码重复
   - 检查是否有性能问题

2. **创建审查报告**
   - 文件名：`PHASE{N}_REVIEW.md`
   - 内容：见下方模板

3. **修复问题**
   - 根据审查报告修复问题
   - 重新运行测试
   - 更新审查报告

4. **提交代码**
   - 提交信息格式：`[Phase {N}] {简短描述}`
   - 包含审查报告

### 代码审查报告模板

```markdown
# Phase {N} 代码审查报告

## 审查日期
{YYYY-MM-DD}

## 审查范围
- 文件列表
- 功能列表

## 设计一致性
- [ ] 代码实现符合设计文档
- [ ] 接口定义清晰
- [ ] 职责划分合理

## 代码质量
- [ ] 类型注解完整
- [ ] 文档字符串完整
- [ ] 变量命名清晰
- [ ] 函数长度合理（< 50 行）
- [ ] 无代码重复
- [ ] 无魔法数字

## 错误处理
- [ ] 异常处理完善
- [ ] 错误信息清晰
- [ ] 日志记录合理

## 测试覆盖
- [ ] 单元测试覆盖核心逻辑
- [ ] 集成测试覆盖主要流程
- [ ] 边界条件有测试
- [ ] 错误场景有测试

## 性能
- [ ] 无明显性能问题
- [ ] 资源使用合理
- [ ] 并发控制正确

## 安全
- [ ] 无 SQL 注入风险
- [ ] 无路径遍历风险
- [ ] 敏感信息不泄露
- [ ] 输入验证完善

## 发现的问题
### 严重问题（必须修复）
1. {问题描述}
   - 位置：{文件}:{行号}
   - 影响：{影响说明}
   - 建议：{修复建议}

### 一般问题（建议修复）
1. {问题描述}

### 优化建议
1. {建议描述}

## 修复记录
- [ ] 问题 1：{修复说明}
- [ ] 问题 2：{修复说明}

## 审查结论
- [ ] ✅ 通过审查，可以进入下一阶段
- [ ] ⚠️ 有问题需要修复
- [ ] ❌ 有严重问题，需要重新设计

## 审查人
{姓名}
```

---

## 风险管理

### 已识别风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| Jira API 限流 | 同步速度慢 | 高 | 实现限流控制和重试 |
| 大文件解析失败 | 部分文档丢失 | 中 | 设置大小限制，记录失败 |
| 索引构建内存溢出 | 同步失败 | 低 | 分批处理，流式构建 |
| chat 集成破坏原有功能 | 功能回归 | 低 | 充分测试，保持接口简洁 |

---

## 项目跟踪

### 每日更新

在 `PROGRESS.md` 中记录每日进度：

```markdown
# 项目进度

## 2026-04-29
- [x] 创建项目规划文档
- [x] 设计数据模型
- [ ] 实现 models.py

## 2026-04-30
- [ ] ...
```

### 问题跟踪

在 `ISSUES.md` 中记录问题：

```markdown
# 问题跟踪

## #1 - Jira API 认证失败
- 状态：Open
- 优先级：High
- 描述：...
- 解决方案：...

## #2 - PDF 解析中文乱码
- 状态：Closed
- 解决方案：...
```

---

## 下一步

1. 创建项目目录结构
2. 开始 Phase 1 实施
3. 每完成一个任务更新 PROGRESS.md
4. 每完成一个 Phase 创建审查报告

准备好开始了吗？
