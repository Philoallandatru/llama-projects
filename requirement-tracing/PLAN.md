# Requirement Tracing System - 实施计划（基于 DataSource）

## 项目概述

**目标**: 构建需求文档（PDF/Excel）与测试用例（Python代码）的自动化追溯系统

**技术栈**: DataSource + MinerU + 本地LLM + LlamaIndex + BM25

**项目规模**: 中型（50个需求文档，500个测试用例）

**当前状态**: ✅ 设计阶段完成，准备进入实现阶段

---

## 架构设计（基于 DataSource）

### 为什么整合 DataSource？

本项目将基于现有的 `datasource` 项目构建，通过继承和扩展的方式实现需求追溯功能。

**DataSource 提供的能力**：
- ✅ 统一的数据源管理（配置、目录结构）
- ✅ 完整的索引管理（Vector + BM25 混合索引）
- ✅ 增量同步机制
- ✅ 标准化的 Document 模型
- ✅ 成熟的 CLI 框架

**整合的价值**：
- 减少约 40% 代码量（~2000 行）
- 节省 2-3 周开发时间（15周 → 12-13周）
- 避免重复实现索引管理
- 统一维护，bug 修复惠及所有项目

### 架构图

```
requirement-tracing/
├── datasource/           # Git submodule（datasource 项目）
├── src/
│   ├── sources/          # 自定义数据源
│   │   ├── requirement.py   # RequirementDataSource
│   │   └── testcase.py      # TestCaseDataSource
│   ├── preprocessing/    # 预处理工具（被 sources 使用）
│   │   ├── parsers/         # MinerU Parser
│   │   └── extractors/      # Requirement/TestCase Extractor
│   ├── matching/         # 匹配层（多阶段检索）
│   ├── workflows/        # 工作流层（使用 SourceManager）
│   └── cli/              # CLI（扩展 datasource CLI）
```

详见：[DataSource 整合方案](docs/design/09-datasource-integration.md)

---

## 阶段划分

### Phase 0: DataSource 整合 (3-5天)

**目标**: 添加 DataSource 依赖并验证基础功能

#### 0.1 添加 DataSource 依赖
- [ ] 添加 datasource 为 Git submodule
- [ ] 配置 Python 路径（PYTHONPATH）
- [ ] 验证 datasource CLI 可用
- [ ] 阅读 datasource 源码和文档

#### 0.2 验证基础功能
- [ ] 测试 Local 数据源（添加、同步、查询）
- [ ] 测试索引构建和加载
- [ ] 测试混合检索（Vector + BM25）
- [ ] 理解 BaseDataSource 接口

**验收标准**:
- datasource CLI 正常工作
- 能够创建和查询测试数据源
- 理解如何扩展 BaseDataSource

---

### Phase 1: 预处理工具实现 (1-2周)

**目标**: 实现文档解析和信息提取工具（被自定义数据源使用）

#### 1.1 MinerU解析器
- [ ] 实现 MinerUParser（PDF/Excel → Markdown）
- [ ] 实现版本号提取逻辑
- [ ] 单元测试（测试PDF、Excel解析）
- [ ] 集成测试（端到端解析流程）

#### 1.2 需求提取器
- [ ] 实现 RequirementExtractor
- [ ] 实现章节分块逻辑（避免超context限制）
- [ ] 设计并测试LLM提取prompt
- [ ] 实现JSON解析和错误处理
- [ ] 单元测试（测试提取准确性）
- [ ] 性能测试（测试LLM调用速度）

#### 1.3 Test Case提取器
- [ ] 实现 TestCaseExtractor
- [ ] 实现AST代码解析
- [ ] 实现路径元数据提取
- [ ] 实现docstring优先策略
- [ ] 实现LLM摘要生成（fallback）
- [ ] 单元测试（测试AST解析和摘要生成）

**验收标准**:
- 能够解析PDF/Excel需求文档并提取结构化需求
- 能够解析Python测试用例并生成摘要
- 单元测试覆盖率 > 80%
- 端到端测试通过

---

### Phase 2: 自定义数据源实现 (1-2周)

**目标**: 实现 RequirementDataSource 和 TestCaseDataSource

#### 2.1 RequirementDataSource
- [ ] 继承 BaseDataSource
- [ ] 实现 fetch_raw()（调用 MinerU Parser）
- [ ] 实现 build_document()（调用 Requirement Extractor）
- [ ] 实现版本管理逻辑
- [ ] 单元测试（测试数据源功能）
- [ ] 集成测试（端到端同步流程）

#### 2.2 TestCaseDataSource
- [ ] 继承 BaseDataSource
- [ ] 实现 fetch_raw()（读取 Python 文件）
- [ ] 实现 build_document()（调用 TestCase Extractor）
- [ ] 实现路径元数据提取
- [ ] 单元测试（测试数据源功能）
- [ ] 集成测试（端到端同步流程）

#### 2.3 数据源注册
- [ ] 在 SourceManager 中注册自定义数据源
- [ ] 或实现插件机制
- [ ] 测试数据源创建和同步

**验收标准**:
- 能够通过 datasource CLI 添加需求和测试用例数据源
- 能够同步数据并构建索引
- 索引加载速度 < 5秒
- 单元测试覆盖率 > 80%

---

### Phase 3: 匹配层实现 (2-3周)

**目标**: 实现多阶段检索和匹配

#### 3.1 多阶段检索器
- [ ] 实现 MultiStageRetriever 框架
- [ ] 实现阶段1：BM25快速召回（使用 datasource 的 BM25Indexer）
- [ ] 实现阶段2：向量语义重排序（使用 datasource 的 VectorIndexer）
- [ ] 实现混合评分算法
- [ ] 实现路径匹配加权
- [ ] 实现置信度判断
- [ ] 实现匹配原因生成
- [ ] 单元测试（测试各阶段逻辑）
- [ ] 集成测试（测试端到端检索）

#### 3.2 LLM判断器
- [ ] 实现 LLMJudge
- [ ] 设计并测试LLM判断prompt
- [ ] 实现评分解析（0-10分）
- [ ] 实现批量判断
- [ ] 单元测试（测试评分准确性）
- [ ] 性能测试（测试LLM调用速度）

#### 3.3 参数调优
- [ ] 调优混合评分权重（BM25/向量/路径）
- [ ] 调优置信度阈值（high/medium/low）
- [ ] 调优各阶段返回数量（top k）
- [ ] 准备人工标注数据集（100-200对）
- [ ] 计算Precision、Recall、F1
- [ ] 对比不同策略效果

**验收标准**:
- 三阶段检索流程完整实现
- Precision > 0.8, Recall > 0.6（高置信度结果）
- 单次查询响应时间 < 2秒（不启用LLM判断）
- 单元测试覆盖率 > 80%

---

### Phase 4: 工作流层实现 (1-2周)

**目标**: 实现四个核心工作流（使用 SourceManager）

#### 4.1 需求覆盖率查询
- [ ] 实现 CoverageQueryWorkflow
- [ ] 使用 SourceManager 查询需求
- [ ] 使用 MultiStageRetriever 匹配测试用例
- [ ] 实现结果格式化
- [ ] 实现按平台/类别过滤
- [ ] 单元测试
- [ ] 集成测试

#### 4.2 代码追溯查询
- [ ] 实现 TraceabilityQueryWorkflow
- [ ] 使用 SourceManager 查询测试用例
- [ ] 使用 MultiStageRetriever 匹配需求
- [ ] 实现需求卡片格式化
- [ ] 单元测试
- [ ] 集成测试

#### 4.3 差距分析
- [ ] 实现 GapAnalysisWorkflow
- [ ] 实现覆盖矩阵构建
- [ ] 实现未覆盖需求识别
- [ ] 实现孤立Test Case识别
- [ ] 实现Excel导出
- [ ] 单元测试
- [ ] 集成测试

#### 4.4 版本对比
- [ ] 实现 VersionDiffWorkflow
- [ ] 使用 VersionManager 对比版本
- [ ] 实现需求变更识别（新增/删除/修改）
- [ ] 实现覆盖率变化分析
- [ ] 实现结果格式化
- [ ] 单元测试
- [ ] 集成测试

**验收标准**:
- 四个工作流全部实现并通过测试
- 差距分析能生成完整的Excel报告
- 版本对比能识别所有变更类型
- 单元测试覆盖率 > 80%

---

### Phase 5: CLI扩展 (3-5天)

**目标**: 扩展 datasource CLI，添加需求追溯命令

#### 5.1 CLI扩展
- [ ] 扩展 datasource CLI（添加 req-trace 命令组）
- [ ] 实现 add-requirements 命令
- [ ] 实现 add-testcases 命令
- [ ] 实现 coverage 命令
- [ ] 实现 trace 命令
- [ ] 实现 gap 命令
- [ ] 实现 diff 命令
- [ ] 实现结果格式化输出
- [ ] 单元测试

#### 5.2 配置管理
- [ ] 扩展 datasource 配置
- [ ] 添加需求追溯特定配置
- [ ] 创建 config.yaml.example
- [ ] 文档说明

**验收标准**:
- CLI所有命令可用且输出友好
- 配置文件易于理解和修改
- 与 datasource CLI 无缝集成

---

### Phase 6: 部署和优化 (1周)

**目标**: 完成部署方案和性能优化

#### 6.1 Docker部署
- [ ] 编写Dockerfile（基于 datasource）
- [ ] 编写docker-compose.yml
- [ ] 配置Ollama服务
- [ ] 测试Docker部署
- [ ] 编写部署文档

#### 6.2 性能优化
- [ ] 实现查询结果缓存
- [ ] 实现批量处理优化
- [ ] 实现并行处理（差距分析）
- [ ] 性能测试和基准测试
- [ ] 性能优化文档

#### 6.3 监控和日志
- [ ] 复用 datasource 日志系统
- [ ] 添加需求追溯特定日志
- [ ] 编写监控文档

**验收标准**:
- Docker一键部署成功
- 查询响应时间满足性能指标
- 日志完整且易于分析

---

### Phase 7: 文档和发布 (3-5天)

**目标**: 完善文档并发布v0.1.0

#### 7.1 用户文档
- [ ] 编写用户指南（安装、配置、使用）
- [ ] 编写常见问题FAQ
- [ ] 编写故障排查指南
- [ ] 录制演示视频（可选）

#### 7.2 开发文档
- [ ] 完善开发指南
- [ ] 编写贡献指南
- [ ] 编写代码规范

#### 7.3 发布准备
- [ ] 代码审查
- [ ] 完整测试（单元+集成+端到端）
- [ ] 性能测试
- [ ] 更新CHANGELOG
- [ ] 创建Git tag v0.1.0
- [ ] 发布公告

**验收标准**:
- 文档完整且易于理解
- 所有测试通过
- 代码覆盖率 > 80%
- 性能满足指标
- 成功发布v0.1.0

---

## 里程碑（调整后）

| 里程碑 | 预计完成时间 | 交付物 |
|--------|------------|--------|
| M0: DataSource整合 | Week 1 | DataSource依赖配置完成 |
| M1: 预处理工具完成 | Week 3 | MinerU Parser、Extractors |
| M2: 自定义数据源完成 | Week 5 | RequirementDataSource、TestCaseDataSource |
| M3: 匹配层完成 | Week 8 | 多阶段检索、LLM判断 |
| M4: 工作流层完成 | Week 10 | 四个核心工作流 |
| M5: CLI扩展完成 | Week 11 | 扩展的CLI命令 |
| M6: 部署优化完成 | Week 12 | Docker部署、性能优化 |
| M7: v0.1.0发布 | Week 13 | 完整系统发布 |

**总时间**: 12-13周（相比原计划节省 2-3周）

---

## 风险和应对

### 风险1: DataSource API 变更
**影响**: 自定义数据源可能需要调整
**应对**: 
- 使用 Git submodule 锁定版本
- 定期同步 datasource 更新
- 保持与 datasource 团队沟通

### 风险2: LLM提取准确性不足
**影响**: 需求提取质量差，影响后续匹配准确性
**应对**: 
- 迭代优化prompt设计
- 增加人工审核环节
- 提供手动修正接口

### 风险3: 检索准确率达不到目标
**影响**: 匹配结果不可信，用户体验差
**应对**:
- 准备充足的标注数据集
- 调优混合评分权重
- 引入人工反馈机制

### 风险4: 性能不满足要求
**影响**: 查询响应慢，用户体验差
**应对**:
- 利用 datasource 的缓存机制
- 优化索引结构
- 使用更小的模型

---

## 资源需求

### 人力资源
- 后端开发: 1人（全职）
- 测试: 0.5人（兼职）
- 文档: 0.5人（兼职）

### 硬件资源
- 开发机: 16GB内存，GPU（可选）
- 服务器: 32GB内存，4核CPU，GPU（推荐）

### 软件资源
- DataSource 项目（Git submodule）
- Ollama + Qwen2.5:14b
- HuggingFace模型（bge-large-zh-v1.5）
- MinerU

---

## 下一步行动

**立即开始**: Phase 0 - DataSource 整合

**第一个任务**: 添加 DataSource 依赖
1. 添加 datasource 为 Git submodule
2. 配置 Python 路径
3. 验证 datasource CLI 可用
4. 阅读 datasource 源码

**预计完成时间**: 1-2天

---

**计划创建时间**: 2024-01-XX
**最后更新时间**: 2024-01-XX（整合 DataSource）
**计划状态**: ✅ 设计完成，准备实施
