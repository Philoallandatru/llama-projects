# 需求文档

**项目:** 统一数据源层 (DataSource Layer)  
**版本:** v1  
**创建日期:** 2025-01-XX

---

## v1 需求

### 数据源连接 (SOURCE)

- [ ] **SOURCE-01**: 支持 Jira API 连接
  - 用户可以配置 Jira 服务器地址、项目 key、JQL 查询
  - 支持基础认证和 Token 认证
  - 验证：成功连接 Jira 并获取 issue 列表

- [ ] **SOURCE-02**: 支持 Confluence API 连接
  - 用户可以配置 Confluence 服务器地址、Space key、CQL 查询
  - 支持基础认证和 Token 认证
  - 验证：成功连接 Confluence 并获取 page 列表

- [ ] **SOURCE-03**: 支持本地文件系统数据源
  - 用户可以指定本地目录路径
  - 支持递归扫描子目录
  - 支持文件类型过滤（PDF/Word/Excel/PPT/Markdown/TXT）
  - 验证：成功扫描目录并列出所有匹配文件

- [ ] **SOURCE-04**: 配置文件管理
  - 每个数据源有独立的 source.yaml 配置文件
  - 配置包含：类型、名称、连接参数、字段选项、附件选项
  - 验证：读取配置文件并正确解析所有参数

- [ ] **SOURCE-05**: 环境变量支持
  - 敏感信息（Token、密码）可通过环境变量配置
  - 配置文件中使用 ${VAR_NAME} 语法引用环境变量
  - 验证：环境变量正确替换到配置中

### 数据抓取 (SNAPSHOT)

- [ ] **SNAPSHOT-01**: Jira 全量抓取
  - 抓取所有匹配 JQL 的 issues
  - 包含全部字段：基础、关系、扩展、changelog
  - 保存为 JSON 格式到 raw/ 目录
  - 验证：所有 issues 成功保存，字段完整

- [ ] **SNAPSHOT-02**: Confluence 全量抓取
  - 抓取所有匹配 CQL 的 pages
  - 包含基础字段和关系字段（不含 version history/comments）
  - 保存为 JSON 格式到 raw/ 目录
  - 验证：所有 pages 成功保存，字段完整

- [ ] **SNAPSHOT-03**: 本地文档扫描
  - 扫描指定目录下的所有文档
  - 支持格式：PDF、Word、Excel、PowerPoint、Markdown、TXT
  - 复制文件到 raw/ 目录（保持目录结构）
  - 验证：所有文档成功复制

- [ ] **SNAPSHOT-04**: 图片附件下载
  - 下载 Jira/Confluence 中的图片附件
  - 支持格式：PNG、JPG、JPEG、GIF、SVG、WebP
  - 无大小限制
  - 下载失败时跳过并标记
  - 验证：图片保存到 assets/ 目录，失败记录到日志

- [ ] **SNAPSHOT-05**: 快照版本管理
  - 快照按日期时间命名（YYYY-MM-DD_HHMMSS）
  - 每个快照包含：raw/、documents/、assets/、manifest.json
  - 支持列出历史快照
  - 验证：快照目录结构正确，manifest.json 包含元数据

- [ ] **SNAPSHOT-06**: 增量抓取检测
  - 检测数据源是否有变更（比较时间戳）
  - v1 仍视为死文档，不做增量更新
  - 仅用于提示用户是否需要重新抓取
  - 验证：正确检测变更并提示

- [ ] **SNAPSHOT-07**: 失败重试机制
  - API 调用失败时自动重试
  - 最多重试 3 次，每次间隔 5 秒
  - 3 次后仍失败则记录到 failed_items.json
  - 验证：模拟失败场景，确认重试逻辑正确

- [ ] **SNAPSHOT-08**: 并发控制
  - 初始并发数：10 个请求
  - 检测到 429 rate limit 时动态降速（减半）
  - 最低并发数：1
  - 验证：触发 rate limit 时正确降速

- [ ] **SNAPSHOT-09**: 进度显示
  - 终端实时显示抓取进度（使用 tqdm）
  - 显示：当前进度、总数、速度、预计剩余时间
  - 验证：进度条正确显示并更新

### 文档构建 (DOCUMENT)

- [ ] **DOCUMENT-01**: Jira Issue 转 Document
  - 一个 Issue = 一个 LlamaIndex Document
  - 内容格式：Markdown（包含所有字段）
  - 元数据：issue_key、status、priority、assignee 等
  - 验证：Document 内容完整，元数据正确

- [ ] **DOCUMENT-02**: Confluence Page 转 Document
  - 一个 Page = 一个 LlamaIndex Document
  - 内容格式：Markdown（从 HTML 转换）
  - 元数据：page_id、space、title、labels 等
  - 验证：Document 内容完整，元数据正确

- [ ] **DOCUMENT-03**: 本地文档转 Document
  - 支持多格式解析：PDF、Word、Excel、PPT、Markdown、TXT
  - 每个文件 = 一个 Document
  - 元数据：file_path、file_type、file_size 等
  - 验证：各种格式正确解析

- [ ] **DOCUMENT-04**: 文档元数据提取
  - 统一元数据结构：source_name、source_type、snapshot_name、item_id
  - 包含解析信息：parser、parsed_at
  - 包含附件信息：has_attachments、attachment_count、attachment_paths
  - 验证：元数据字段完整且格式正确

- [ ] **DOCUMENT-05**: 图片引用本地化
  - 替换 Markdown 中的图片 URL 为本地路径
  - 图片缺失时标记 "Image Missing"
  - 验证：图片路径正确，缺失图片有标记

- [ ] **DOCUMENT-06**: PDF 解析策略
  - 优先使用 MinerU 解析（更好的布局理解）
  - MinerU 失败时降级到 PyMuPDF
  - 记录使用的解析器到元数据
  - 验证：两种解析器都能正常工作，降级逻辑正确

### 索引构建 (INDEX)

- [ ] **INDEX-01**: Vector 索引构建
  - 使用 LlamaIndex VectorStoreIndex
  - 支持配置 embedding 模型
  - 索引保存到 indexes/vector/ 目录
  - 验证：索引构建成功，可以加载和查询

- [ ] **INDEX-02**: BM25 索引构建
  - 使用 LlamaIndex BM25Retriever
  - 配置 k1 和 b 参数
  - 索引保存到 indexes/bm25/ 目录
  - 验证：索引构建成功，可以加载和查询

- [ ] **INDEX-03**: 混合检索支持
  - 同时构建 Vector 和 BM25 索引
  - 默认权重：Vector 60% + BM25 40%
  - 支持运行时覆盖权重
  - 验证：混合检索返回正确的加权结果

- [ ] **INDEX-04**: IngestionPipeline 集成
  - 使用 LlamaIndex IngestionPipeline
  - 自动切分 Documents 为 Nodes（SentenceSplitter）
  - 配置 chunk_size 和 chunk_overlap
  - 验证：Nodes 正确切分，保留元数据

- [ ] **INDEX-05**: 索引持久化
  - 索引保存到本地文件系统
  - 支持重新加载已有索引
  - 记录索引元数据（创建时间、文档数、节点数）
  - 验证：索引保存和加载正确

- [ ] **INDEX-06**: 索引增量更新
  - 检测 Snapshot 变更
  - 只更新变更的 Documents
  - v1 简化实现：重建整个索引
  - 验证：新快照触发索引重建

### 检索接口 (RETRIEVAL)

- [ ] **RETRIEVAL-01**: 统一 Retriever 接口
  - 封装混合检索逻辑
  - 提供简单的 query() 方法
  - 返回标准的 NodeWithScore 列表
  - 验证：接口调用简单，返回结果正确

- [ ] **RETRIEVAL-02**: 查询参数配置
  - 支持 top_k 参数（返回结果数量）
  - 支持权重覆盖（vector_weight、bm25_weight）
  - 支持过滤条件（metadata filters）
  - 验证：参数正确影响查询结果

- [ ] **RETRIEVAL-03**: 结果排序和去重
  - 按分数降序排序
  - 去除重复的 Nodes（按 node_id）
  - 保留高分结果
  - 验证：结果无重复，排序正确

- [ ] **RETRIEVAL-04**: Source 过滤
  - 支持按 source_name 过滤
  - 支持按 source_type 过滤
  - 支持多个 source 组合查询
  - 验证：过滤条件正确应用

### CLI 工具 (CLI)

- [ ] **CLI-01**: `ds source add` 命令
  - 交互式创建数据源配置
  - 支持三种类型：jira、confluence、local
  - 生成 source.yaml 文件
  - 验证：配置文件正确生成

- [ ] **CLI-02**: `ds source list` 命令
  - 列出所有数据源
  - 显示：名称、类型、创建时间、快照数
  - 验证：列表显示正确

- [ ] **CLI-03**: `ds snapshot create` 命令
  - 为指定数据源创建快照
  - 显示实时进度
  - 生成 manifest.json 和 import_report.md
  - 验证：快照创建成功，报告完整

- [ ] **CLI-04**: `ds snapshot list` 命令
  - 列出数据源的所有快照
  - 显示：名称、状态、条目数、大小、创建时间
  - 验证：列表显示正确

- [ ] **CLI-05**: `ds index build` 命令
  - 为指定数据源构建索引
  - 支持指定快照版本
  - 显示构建进度
  - 验证：索引构建成功

- [ ] **CLI-06**: `ds index list` 命令
  - 列出数据源的索引状态
  - 显示：类型、快照、节点数、大小、创建时间
  - 验证：列表显示正确

- [ ] **CLI-07**: `ds query` 命令
  - 测试检索功能
  - 显示查询结果（标题、分数、摘要）
  - 支持参数：top_k、type（vector/bm25/hybrid）
  - 验证：查询返回正确结果

- [ ] **CLI-08**: 支持 `ds` 简写
  - `datasource` 命令可简写为 `ds`
  - 子命令也支持简写（如 `s` = `source`）
  - 验证：简写命令正常工作

- [ ] **CLI-09**: 配置文件支持
  - 全局配置文件：datasource/config.yaml
  - 配置项：存储路径、embedding 模型、检索权重等
  - 支持环境变量覆盖
  - 验证：配置正确加载和应用

- [ ] **CLI-10**: 日志输出
  - 终端输出：INFO 级别（简洁）
  - 文件输出：DEBUG 级别（详细）
  - 日志文件：data/logs/datasource.log
  - 验证：日志正确输出到终端和文件

### 错误处理 (ERROR)

- [ ] **ERROR-01**: API 错误处理
  - 401/403: 认证失败，提示检查凭证
  - 404: 资源不存在，跳过并记录
  - 429: Rate limit，触发降速
  - 500/502/503: 服务器错误，重试
  - 验证：各种错误正确处理

- [ ] **ERROR-02**: 网络超时处理
  - 设置合理的超时时间（30 秒）
  - 超时后重试
  - 验证：超时场景正确处理

- [ ] **ERROR-03**: 文件解析失败处理
  - 解析失败时跳过该文件
  - 记录到 failed_items.json
  - 继续处理其他文件
  - 验证：解析失败不影响整体流程

- [ ] **ERROR-04**: 磁盘空间检查
  - 抓取前检查可用空间
  - 空间不足时提前警告
  - 验证：空间不足时正确提示

- [ ] **ERROR-05**: 错误日志记录
  - 记录详细的错误信息和堆栈
  - 包含上下文信息（source、item_id 等）
  - 便于问题排查
  - 验证：错误日志包含足够信息

---

## v2 需求（已推迟）

- 增量更新支持（检测变更，只更新修改的内容）
- 数据治理功能（PII 过滤、内容质量检查）
- Web UI 界面
- 更多数据源支持（GitHub、Notion、Google Drive）
- 分布式部署支持

---

## 超出范围

- **实时同步** - v1 采用快照模式
- **多租户支持** - v1 单用户单机
- **权限管理** - v1 不实现细粒度权限
- **审计日志** - v1 只记录操作日志

---

## 需求追溯

| 需求 ID | 阶段 | 状态 |
|---------|------|------|
| SOURCE-01 | Phase 1 | 待规划 |
| SOURCE-02 | Phase 1 | 待规划 |
| SOURCE-03 | Phase 1 | 待规划 |
| SOURCE-04 | Phase 1 | 待规划 |
| SOURCE-05 | Phase 1 | 待规划 |
| ... | ... | ... |

（此表将在创建 ROADMAP 后自动填充）

---

*最后更新: 2025-01-XX*
