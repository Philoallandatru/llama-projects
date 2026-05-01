# Chat 项目配置

## 项目概述

这是一个基于 LlamaIndex 的多数据源 RAG (Retrieval-Augmented Generation) 系统，支持从本地文件、Jira 和 Confluence 等多个数据源加载文档并进行智能问答。

## LLM 配置

### 使用本地 LM Studio

项目配置为使用本地 LM Studio 模型进行测试：

- **LM Studio 地址**: http://127.0.0.1:1234
- **超时时间**: 300 秒（5 分钟）- 本地模型响应较慢，需要较长的超时时间
- **配置方式**: 在 `.env` 文件中设置 `USE_LOCAL_LLM=true`

### 环境变量配置

创建 `src/.env` 文件（参考 `src/.env.example`）：

```bash
# 启用本地 LM Studio
USE_LOCAL_LLM=true

# LM Studio 配置
LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_MODEL=local-model
LM_STUDIO_EMBED_BASE_URL=http://127.0.0.1:1234/v1
LM_STUDIO_EMBED_MODEL=text-embedding-3-large
REQUEST_TIMEOUT=300

# 本地数据源
LOCAL_DATA_DIR=./data
```

### 切换到 OpenAI

如需切换回 OpenAI API：

```bash
USE_LOCAL_LLM=false
OPENAI_API_KEY=your-api-key-here
MODEL=gpt-4.1
EMBEDDING_MODEL=text-embedding-3-large
```

## 数据源配置

支持三种数据源类型：

1. **Local**: 本地文件系统（默认启用）
2. **Jira**: Jira Server/Cloud（可选）
3. **Confluence**: Confluence Server/Cloud（可选）

数据源配置在 `src/datasource_config.py` 中定义。

## 开发要求

### 超时时间

- 所有 LLM 请求必须设置足够长的超时时间（至少 300 秒）
- 本地模型响应速度较慢，避免过早超时

### 测试

运行集成测试：

```bash
cd tests
python test_datasource_integration.py
```

### 代码风格

- 使用 Python 3.11+
- 遵循 PEP 8 代码规范
- 添加类型注解
- 编写单元测试

## 项目结构

```
chat/
├── src/
│   ├── settings.py          # LLM 配置（支持本地/OpenAI）
│   ├── datasource_config.py # 数据源配置
│   ├── index.py             # 索引加载
│   ├── generate.py          # 索引生成
│   ├── workflow.py          # AgentWorkflow
│   ├── query.py             # 查询引擎
│   └── citation.py          # 引用系统
├── tests/
│   └── test_datasource_integration.py
├── pyproject.toml           # 项目依赖
└── CLAUDE.md                # 本文件
```

## 依赖项目

- **datasource**: 位于 `../datasource`，提供多数据源读取功能
- 通过 `pyproject.toml` 中的本地路径依赖引入

## 注意事项

1. **Windows 编码问题**: 避免在控制台输出中使用 emoji，使用 ASCII 字符代替
2. **网络问题**: 如果 `uv sync` 失败，可以直接通过 Python 路径导入 datasource
3. **LM Studio**: 确保 LM Studio 服务已启动并监听在 http://127.0.0.1:1234
