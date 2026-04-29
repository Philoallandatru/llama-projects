# 统一数据源层 (DataSource Layer)

## 这是什么

一个基于 LlamaIndex 的企业级数据源管理系统，专注于从 Jira、Confluence 和本地文档中一次性全量抓取数据，构建混合检索索引，为下游 LlamaIndex Workflow 提供统一的检索接口。

**核心价值：** 将分散的企业知识（Jira issues、Confluence pages、本地文档）转换为可检索的统一数据层，支持高质量的 RAG 应用。

## 上下文

### 为什么构建这个

- 现有三个 LlamaIndex 项目（chat、deep-search、data-explore）各自处理数据源，代码重复
- 需要统一的数据获取和索引构建层，让上层 Workflow 专注于业务逻辑
- Jira 和 Confluence 包含大量企业知识，但数据分散、格式不统一
- 需要支持离线快照模式，不依赖实时 API 调用

### 目标用户

- 企业内部开发者：需要构建基于企业知识的 RAG 应用
- 数据工程师：需要管理和维护企业知识库
- AI 应用开发者：需要高质量的检索层支持

### 技术背景

- 使用 LlamaIndex 作为核心框架
- Python 3.10+
- 数据规模：中等（1000-5000 issues，500-2000 pages）
- 部署环境：本地开发机或内部服务器

## 需求

### 已验证

（无 - 这是新项目）

### 活跃需求

#### 数据源连接 (SOURCE)
- [ ] **SOURCE-01**: 支持 Jira API 连接（基础认证 + Token）
- [ ] **SOURCE-02**: 支持 Confluence API 连接（基础认证 + Token）
- [ ] **SOURCE-03**: 支持本地文件系统数据源（递归扫描目录）
- [ ] **SOURCE-04**: 配置文件管理（source.yaml 定义数据源）
- [ ] **SOURCE-05**: 环境变量支持（敏感信息不写入配置文件）

#### 数据抓取 (SNAPSHOT)
- [ ] **SNAPSHOT-01**: Jira 全量抓取（所有 issues，包含全部字段）
- [ ] **SNAPSHOT-02**: Confluence 全量抓取（所有 pages，包含基础+关系字段）
- [ ] **SNAPSHOT-03**: 本地文档扫描（支持 PDF/Word/Excel/PPT/Markdown/TXT）
- [ ] **SNAPSHOT-04**: 图片附件下载（PNG/JPG/GIF/SVG/WebP，失败跳过）
- [ ] **SNAPSHOT-05**: 快照版本管理（按日期组织，支持多版本）
- [ ] **SNAPSHOT-06**: 增量抓取检测（检测变更，但 v1 视为死文档）
- [ ] **SNAPSHOT-07**: 失败重试机制（3 次重试，间隔 5 秒）
- [ ] **SNAPSHOT-08**: 并发控制（初始 10 并发，遇到 429 动态降速）
- [ ] **SNAPSHOT-09**: 进度显示（终端实时显示抓取进度）

#### 文档构建 (DOCUMENT)
- [ ] **DOCUMENT-01**: Jira Issue 转 LlamaIndex Document（一对一映射）
- [ ] **DOCUMENT-02**: Confluence Page 转 LlamaIndex Document（一对一映射）
- [ ] **DOCUMENT-03**: 本地文档转 LlamaIndex Document（支持多格式解析）
- [ ] **DOCUMENT-04**: 文档元数据提取（source_type、source_id、timestamp 等）
- [ ] **DOCUMENT-05**: 图片引用本地化（替换为本地路径）
- [ ] **DOCUMENT-06**: PDF 解析（MinerU 为主，PyMuPDF 为 fallback）

#### 索引构建 (INDEX)
- [ ] **INDEX-01**: Vector 索引构建（使用 LlamaIndex VectorStoreIndex）
- [ ] **INDEX-02**: BM25 索引构建（使用 LlamaIndex BM25Retriever）
- [ ] **INDEX-03**: 混合检索支持（Vector 60% + BM25 40%，权重可配置）
- [ ] **INDEX-04**: IngestionPipeline 集成（自动切分 Nodes）
- [ ] **INDEX-05**: 索引持久化（保存到本地文件系统）
- [ ] **INDEX-06**: 索引增量更新（基于 Snapshot 变更）

#### 检索接口 (RETRIEVAL)
- [ ] **RETRIEVAL-01**: 统一 Retriever 接口（封装混合检索逻辑）
- [ ] **RETRIEVAL-02**: 查询参数配置（top_k、权重、过滤条件）
- [ ] **RETRIEVAL-03**: 结果排序和去重
- [ ] **RETRIEVAL-04**: Source 过滤（按数据源类型或名称过滤）

#### CLI 工具 (CLI)
- [ ] **CLI-01**: `ds source add` - 添加数据源
- [ ] **CLI-02**: `ds source list` - 列出所有数据源
- [ ] **CLI-03**: `ds snapshot create` - 创建快照
- [ ] **CLI-04**: `ds snapshot list` - 列出快照历史
- [ ] **CLI-05**: `ds index build` - 构建索引
- [ ] **CLI-06**: `ds index list` - 列出索引状态
- [ ] **CLI-07**: `ds query` - 测试检索
- [ ] **CLI-08**: 支持 `ds` 简写
- [ ] **CLI-09**: 配置文件支持（config.yaml）
- [ ] **CLI-10**: 日志输出（终端 + 文件）

#### 错误处理 (ERROR)
- [ ] **ERROR-01**: API 错误处理（401/403/404/429/500）
- [ ] **ERROR-02**: 网络超时处理
- [ ] **ERROR-03**: 文件解析失败处理（跳过并记录）
- [ ] **ERROR-04**: 磁盘空间检查
- [ ] **ERROR-05**: 错误日志记录（详细堆栈信息）

### 超出范围

- **实时同步** - v1 采用快照模式，不做实时增量同步
- **数据治理** - v1 不实现 PII 过滤、内容过滤等功能
- **Web UI** - v1 只提供 CLI，不提供 Web 界面
- **多租户支持** - v1 单用户单机部署
- **分布式部署** - v1 单机运行
- **数据库存储** - v1 使用文件系统，不使用数据库
- **权限管理** - v1 不实现细粒度权限控制
- **审计日志** - v1 只记录操作日志，不做审计追踪

## 关键决策

| 决策 | 理由 | 结果 |
|------|------|------|
| 采用快照模式而非实时同步 | 中等数据规模，离线处理更稳定可靠 | 简化架构，降低复杂度 |
| 使用 LlamaIndex 原生组件 | 避免重复造轮子，利用成熟生态 | 开发效率高，维护成本低 |
| 混合检索（Vector + BM25） | 结合语义和关键词匹配，提高召回率 | 检索质量更高 |
| 扁平化架构（只有 Source） | 去除 Workspace/Project 抽象 | 架构简单，易于理解 |
| 数据存储在 data/ 目录 | 代码和数据分离 | 便于备份和迁移 |
| MinerU + PyMuPDF | MinerU 解析质量高，PyMuPDF 作为 fallback | 兼顾质量和稳定性 |
| 一对一 Document 策略 | 一个 Issue/Page = 一个 Document | 元数据管理清晰 |
| 并发控制 + 动态降速 | 避免触发 API 限流 | 提高抓取成功率 |

## 演进

本文档在阶段转换和里程碑边界时演进。

**每次阶段转换后** (通过 `/gsd-transition`):
1. 需求失效？→ 移至超出范围并说明原因
2. 需求验证？→ 移至已验证并标注阶段
3. 新需求出现？→ 添加到活跃需求
4. 需要记录决策？→ 添加到关键决策
5. "这是什么"仍然准确？→ 如有偏差则更新

**每次里程碑后** (通过 `/gsd-complete-milestone`):
1. 全面审查所有部分
2. 核心价值检查 - 仍然是正确的优先级？
3. 审计超出范围 - 原因仍然有效？
4. 用当前状态更新上下文

---
*最后更新: 2025-01-XX 初始化后*
