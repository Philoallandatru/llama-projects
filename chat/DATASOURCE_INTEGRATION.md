# Datasource 集成指南

## 概述

chat 项目现已集成 datasource 系统，支持从多个数据源（本地文件、Jira、Confluence）构建统一的 RAG 索引。

## 配置方式

### 1. LLM 配置

#### 使用本地 LM Studio（推荐用于测试）

在 `src/.env` 文件中配置：

```bash
# 启用本地 LM Studio
USE_LOCAL_LLM=true

# LM Studio 配置
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=local-model
LM_STUDIO_EMBED_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_EMBED_MODEL=text-embedding-3-large
REQUEST_TIMEOUT=300  # 本地模型响应较慢，设置 5 分钟超时
```

**注意事项**:
- 确保 LM Studio 已启动并监听在 http://127.0.0.1:1234
- 本地模型响应速度较慢，需要设置较长的超时时间（300 秒）
- 如果遇到超时错误，可以进一步增加 REQUEST_TIMEOUT 值

#### 使用 OpenAI API

```bash
USE_LOCAL_LLM=false
OPENAI_API_KEY=your-api-key-here
MODEL=gpt-4.1
EMBEDDING_MODEL=text-embedding-3-large
```

### 2. 数据源配置

在 `src/.env` 文件中配置数据源（参考 `src/.env.example`）：

```bash
# 数据源 1: 本地文件
DATASOURCE_1_NAME=local_docs
DATASOURCE_1_TYPE=local
DATASOURCE_1_PATH=./data
DATASOURCE_1_DESCRIPTION=本地文档数据源

# 数据源 2: Jira (可选)
DATASOURCE_2_NAME=jira_issues
DATASOURCE_2_TYPE=jira
DATASOURCE_2_ENABLED=false
DATASOURCE_2_SERVER=https://your-jira.atlassian.net
DATASOURCE_2_USERNAME=your-email@example.com
DATASOURCE_2_API_TOKEN=your-api-token
DATASOURCE_2_PROJECT_KEY=PROJ

# 数据源 3: Confluence (可选)
DATASOURCE_3_NAME=confluence_docs
DATASOURCE_3_TYPE=confluence
DATASOURCE_3_ENABLED=false
DATASOURCE_3_SERVER=https://your-confluence.atlassian.net
DATASOURCE_3_USERNAME=your-email@example.com
DATASOURCE_3_API_TOKEN=your-api-token
DATASOURCE_3_SPACE_KEY=SPACE
```

### 3. 代码配置（可选）

在 `src/datasource_config.py` 中直接配置：

```python
DATASOURCES = [
    {
        "name": "local_docs",
        "type": "local",
        "path": "./data",
        "enabled": True,
        "description": "本地文档数据源"
    },
    # 添加更多数据源...
]
```

## 使用方式

### 1. 启动 LM Studio（如果使用本地模型）

```bash
# 1. 打开 LM Studio 应用
# 2. 加载一个模型（例如 Llama 3 或其他兼容模型）
# 3. 启动本地服务器，确保监听在 http://127.0.0.1:1234
# 4. 验证服务是否正常：
curl http://127.0.0.1:1234/v1/models
```

### 2. 生成索引

```bash
# 使用默认配置生成索引
python src/generate.py

# 索引将包含所有已启用数据源的文档
```

### 3. 查询索引

```bash
# 启动 chat 服务
npm run dev

# 或直接使用 Python API
python src/index.py
```

### 4. 查看数据源状态

```bash
cd src
python datasource_config.py
```

输出示例：
```
=== 数据源配置状态 ===

local_docs:
  类型: local
  状态: [OK] 已启用
  描述: 本地文档数据源

jira_issues:
  类型: jira
  状态: [--] 未启用
  描述: Jira 工单数据源

已启用的数据源数量: 1
  - local_docs (local)
```

## 数据源类型

### Local Files (本地文件)

支持的文件格式：
- Markdown (.md)
- PDF (.pdf)
- Word (.docx)
- PowerPoint (.pptx)
- Excel (.xlsx)
- 纯文本 (.txt)

配置参数：
- `path`: 文件目录路径（相对或绝对路径）
- `recursive`: 是否递归扫描子目录（默认 true）

### Jira

从 Jira 项目同步工单。

必需参数：
- `server`: Jira 服务器地址
- `username`: 用户名（邮箱）
- `api_token`: API Token
- `project_key`: 项目 Key

可选参数：
- `jql`: 自定义 JQL 查询（默认查询项目所有工单）
- `max_results`: 最大结果数（默认 1000）

### Confluence

从 Confluence 空间同步文档。

必需参数：
- `server`: Confluence 服务器地址
- `username`: 用户名（邮箱）
- `api_token`: API Token
- `space_key`: 空间 Key

可选参数：
- `max_results`: 最大结果数（默认 1000）

## 架构说明

### 核心组件

1. **datasource_config.py**: 数据源配置管理
   - 从环境变量或代码加载配置
   - 验证配置完整性
   - 提供配置查询接口

2. **generate.py**: 索引生成
   - 使用 `DataSourceManager` 统一管理多个数据源
   - 从所有已启用数据源加载文档
   - 构建统一的向量索引

3. **index.py**: 索引加载
   - 加载预生成的索引
   - 支持本地索引和 LlamaCloud

### 数据流

```
配置文件 (.env)
    ↓
datasource_config.py (加载配置)
    ↓
generate.py (生成索引)
    ↓
DataSourceManager (统一管理)
    ↓
各数据源 Reader (LocalReader, JiraReader, ConfluenceReader)
    ↓
LlamaIndex (构建向量索引)
    ↓
index.py (加载索引)
    ↓
RAG 查询
```

## 性能优化

### 增量同步

datasource 系统支持增量同步，只同步变更的文档：

```python
# 首次同步：全量
reader.load_data()  # 同步所有文档

# 后续同步：增量
reader.load_data()  # 只同步变更的文档（基于 lastModified）
```

性能提升：
- 首次同步后，增量同步速度提升 80-90%
- 100 个文档的增量同步通常在 1-2 秒内完成

### 异步抓取

对于 Jira 和 Confluence，支持异步并发抓取：

```python
# 同步抓取（默认）
reader.load_data()

# 异步抓取（推荐）
reader.load_data(use_async=True, max_concurrent=10)
```

性能提升：
- 10 个文档：2s → 0.5s (4倍)
- 100 个文档：20s → 3-4s (5-7倍)
- 500 个文档：100s → 15-20s (5-7倍)

## 故障排查

### 问题 1: 数据源配置无效

**症状**: 运行 `python src/datasource_config.py` 显示 `[!!] 配置不完整`

**解决方案**:
1. 检查 `.env` 文件中的配置是否完整
2. 对于 Jira/Confluence，确保提供了所有必需参数（server, username, api_token, project_key/space_key）
3. 运行 `python src/datasource_config.py` 查看详细错误信息

### 问题 2: 索引生成失败

**症状**: `python src/generate.py` 报错

**解决方案**:
1. 确保至少有一个数据源已启用且配置正确
2. 检查数据源路径是否存在（对于本地文件）
3. 检查网络连接和认证信息（对于 Jira/Confluence）
4. 查看详细错误日志

### 问题 3: 查询结果为空

**症状**: 查询返回空结果或不相关结果

**解决方案**:
1. 确认索引已生成（检查 `storage` 目录）
2. 重新生成索引：`python src/generate.py`
3. 检查数据源是否包含相关文档
4. 调整查询参数（top_k, similarity_threshold）

## 下一步

- [ ] 添加更多数据源类型（GitHub, Notion, Google Drive 等）
- [ ] 实现数据源权限控制
- [ ] 添加数据源同步调度器
- [ ] 优化索引更新策略（部分更新而非全量重建）
- [ ] 添加数据源监控和告警

## 参考资料

- [datasource 项目文档](../datasource/README.md)
- [LlamaIndex 文档](https://docs.llamaindex.ai/)
- [Phase 7 实施计划](../datasource/PHASE7_PLAN.md)
