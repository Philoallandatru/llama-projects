# Phase 7 Plan: Chat 集成

**目标**: 将 datasource 系统集成到 chat 项目，实现端到端的多数据源 RAG  
**预计工作量**: 8-10 小时  
**优先级**: 高（验收关键阶段）

## 📋 任务列表

### Task 7.1: 添加 datasource 依赖 ⏱️ 1h

**目标**: 在 chat 项目中添加 datasource 作为本地依赖

**实现步骤**:
1. 修改 `chat/pyproject.toml`，添加本地路径依赖
2. 运行 `uv sync` 安装依赖
3. 验证导入成功

**验收标准**:
- [ ] `pyproject.toml` 包含 datasource 依赖
- [ ] `uv sync` 成功执行
- [ ] 可以导入 `datasource.core.manager.SourceManager`

**文件修改**:
- `chat/pyproject.toml`

---

### Task 7.2: 实现多数据源配置 ⏱️ 2h

**目标**: 创建配置文件支持 Local + Jira + Confluence 多数据源

**实现步骤**:
1. 在 `chat/src/` 创建 `datasource_config.py`
2. 定义数据源配置结构
3. 支持从环境变量读取配置
4. 创建示例配置文件

**配置示例**:
```python
DATASOURCES = [
    {
        "name": "local_docs",
        "type": "local",
        "config": {
            "directory": "./data"
        }
    },
    {
        "name": "jira_issues",
        "type": "jira",
        "config": {
            "server_url": os.getenv("JIRA_SERVER_URL"),
            "email": os.getenv("JIRA_EMAIL"),
            "token": os.getenv("JIRA_TOKEN"),
            "jql": "project = PROJ"
        }
    },
    {
        "name": "confluence_docs",
        "type": "confluence",
        "config": {
            "base_url": os.getenv("CONFLUENCE_BASE_URL"),
            "email": os.getenv("CONFLUENCE_EMAIL"),
            "token": os.getenv("CONFLUENCE_TOKEN"),
            "space_key": "SPACE"
        }
    }
]
```

**验收标准**:
- [ ] 配置文件支持多数据源
- [ ] 支持从环境变量读取敏感信息
- [ ] 配置结构清晰易懂

**文件修改**:
- 新增 `chat/src/datasource_config.py`
- 更新 `chat/src/.env.example`

---

### Task 7.3: 修改索引生成逻辑 ⏱️ 3h

**目标**: 修改 chat 的索引生成，使用 datasource 的 SourceManager

**实现步骤**:

#### 3.1 修改 `chat/src/index.py`
```python
from datasource.core.manager import SourceManager
from datasource.core.paths import PathManager

STORAGE_DIR = "src/storage"
DATA_DIR = "src/datasource_data"  # datasource 数据目录

def get_source_manager():
    """获取 SourceManager 实例"""
    path_manager = PathManager(base_dir=DATA_DIR)
    return SourceManager(path_manager)

def get_index():
    """从 datasource 加载索引"""
    # 检查是否有索引
    if not os.path.exists(STORAGE_DIR):
        return None
    
    # 加载索引
    storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
    index = load_index_from_storage(storage_context)
    return index
```

#### 3.2 修改 `chat/src/generate.py`
```python
from src.datasource_config import DATASOURCES
from src.index import get_source_manager, STORAGE_DIR

def generate_index():
    """从多数据源生成索引"""
    init_settings()
    
    # 1. 初始化 SourceManager
    manager = get_source_manager()
    
    # 2. 添加所有数据源
    for ds_config in DATASOURCES:
        if ds_config.get("enabled", True):
            manager.add_source(
                name=ds_config["name"],
                source_type=ds_config["type"],
                config=ds_config["config"]
            )
    
    # 3. 同步所有数据源
    all_documents = []
    for source in manager.list_sources():
        logger.info(f"Syncing source: {source.name}")
        manager.sync_source(source.name)
        
        # 加载文档
        docs = manager.load_documents(source.name)
        all_documents.extend(docs)
    
    # 4. 创建索引
    logger.info(f"Creating index from {len(all_documents)} documents")
    index = VectorStoreIndex.from_documents(
        all_documents,
        show_progress=True
    )
    
    # 5. 持久化
    index.storage_context.persist(STORAGE_DIR)
    logger.info(f"Index created and stored in {STORAGE_DIR}")
```

**验收标准**:
- [ ] 可以从多个数据源加载文档
- [ ] 索引生成成功
- [ ] 索引包含所有数据源的文档

**文件修改**:
- `chat/src/index.py`
- `chat/src/generate.py`

---

### Task 7.4: 添加 CLI 命令 ⏱️ 1h

**目标**: 在 chat 项目中添加数据源管理命令

**实现步骤**:
1. 创建 `chat/src/cli.py`
2. 添加数据源管理命令（add, list, sync, delete）
3. 在 `pyproject.toml` 中注册命令

**CLI 命令**:
```bash
# 添加数据源
uv run datasource add local_docs --type local --directory ./data

# 列出数据源
uv run datasource list

# 同步数据源
uv run datasource sync local_docs

# 删除数据源
uv run datasource delete local_docs
```

**验收标准**:
- [ ] CLI 命令可以正常执行
- [ ] 可以管理数据源
- [ ] 命令输出清晰

**文件修改**:
- 新增 `chat/src/cli.py`
- 更新 `chat/pyproject.toml`

---

### Task 7.5: 端到端集成测试 ⏱️ 2h

**目标**: 测试完整流程，确保所有功能正常工作

**测试场景**:

#### 场景 1: 本地文件数据源
```bash
# 1. 添加本地数据源
uv run datasource add local_docs --type local --directory ./data

# 2. 生成索引
uv run generate

# 3. 启动服务
uv run -m llama_deploy.apiserver

# 4. 部署工作流
uv run llamactl deploy llama_deploy.yml

# 5. 测试查询
curl -X POST 'http://localhost:4501/deployments/chat/tasks/create' \
  -H 'Content-Type: application/json' \
  -d '{"input": "{\"user_msg\":\"What is LlamaIndex?\",\"chat_history\":[]}", "service_id": "workflow"}'
```

#### 场景 2: Jira 数据源
```bash
# 1. 添加 Jira 数据源
uv run datasource add jira_issues --type jira \
  --server-url https://jira.example.com \
  --email user@example.com \
  --token xxx \
  --jql "project = PROJ"

# 2. 同步数据
uv run datasource sync jira_issues

# 3. 重新生成索引
uv run generate

# 4. 测试查询
# 查询 Jira issue 相关问题
```

#### 场景 3: 多数据源混合查询
```bash
# 1. 添加多个数据源
uv run datasource add local_docs --type local --directory ./data
uv run datasource add jira_issues --type jira --jql "project = PROJ"
uv run datasource add confluence_docs --type confluence --space-key SPACE

# 2. 同步所有数据源
uv run datasource sync --all

# 3. 生成索引
uv run generate

# 4. 测试混合查询
# 查询跨数据源的问题
```

**验收标准**:
- [ ] 本地文件数据源正常工作
- [ ] Jira 数据源正常工作
- [ ] Confluence 数据源正常工作
- [ ] 多数据源混合查询正常
- [ ] 查询结果包含正确的引用信息

**测试文件**:
- 新增 `chat/tests/test_integration.py`

---

### Task 7.6: 更新文档 ⏱️ 1h

**目标**: 更新 chat 项目文档，添加多数据源使用示例

**文档更新**:

#### 更新 `chat/README.md`
- 添加多数据源配置说明
- 添加 CLI 命令使用示例
- 添加常见问题解答

#### 创建 `chat/DATASOURCE_GUIDE.md`
- 详细的数据源配置指南
- 各种数据源的配置示例
- 故障排查指南

**验收标准**:
- [ ] README.md 包含多数据源使用说明
- [ ] 创建详细的数据源配置指南
- [ ] 文档清晰易懂

**文件修改**:
- 更新 `chat/README.md`
- 新增 `chat/DATASOURCE_GUIDE.md`

---

## 🎯 验收标准

### 功能验收
- [ ] 可以添加和管理多个数据源（Local, Jira, Confluence）
- [ ] 可以从多个数据源生成统一索引
- [ ] 查询可以检索所有数据源的内容
- [ ] 查询结果包含正确的引用信息
- [ ] 支持增量同步

### 性能验收
- [ ] 索引生成时间合理（< 5 分钟，100 个文档）
- [ ] 查询响应时间 < 3 秒
- [ ] 支持大规模数据源（1000+ 文档）

### 质量验收
- [ ] 所有测试通过
- [ ] 代码符合项目规范
- [ ] 文档完整清晰
- [ ] 错误处理完善

---

## 📊 项目结构

### 修改后的 chat 项目结构
```
chat/
├── src/
│   ├── __init__.py
│   ├── .env                      # 环境变量
│   ├── settings.py               # LLM 设置
│   ├── datasource_config.py      # 数据源配置（新增）
│   ├── cli.py                    # CLI 命令（新增）
│   ├── index.py                  # 索引管理（修改）
│   ├── generate.py               # 索引生成（修改）
│   ├── workflow.py               # 工作流
│   ├── query.py                  # 查询引擎
│   ├── citation.py               # 引用系统
│   ├── storage/                  # 索引存储
│   └── datasource_data/          # datasource 数据目录（新增）
│       ├── sources/              # 数据源配置
│       ├── raw/                  # 原始数据
│       └── processed/            # 处理后的文档
├── tests/
│   └── test_integration.py       # 集成测试（新增）
├── pyproject.toml                # 依赖配置（修改）
├── README.md                     # 项目文档（修改）
└── DATASOURCE_GUIDE.md           # 数据源指南（新增）
```

---

## 🔧 技术决策

### 1. 依赖管理
**决策**: 使用本地路径依赖  
**原因**: datasource 和 chat 在同一个 monorepo 中，使用本地依赖更方便开发和调试

```toml
[project]
dependencies = [
    "datasource @ file:///${PROJECT_ROOT}/../datasource"
]
```

### 2. 数据目录
**决策**: 使用独立的 `datasource_data/` 目录  
**原因**: 与原有的 `data/` 目录分离，避免冲突

### 3. 配置方式
**决策**: 使用 Python 配置文件 + 环境变量  
**原因**: 灵活性高，支持动态配置，敏感信息通过环境变量管理

### 4. CLI 命令
**决策**: 在 chat 项目中添加独立的 CLI 命令  
**原因**: 用户可以在 chat 项目中直接管理数据源，无需切换到 datasource 目录

---

## 🚀 实施计划

### Day 1 (4h)
- ✅ Task 7.1: 添加 datasource 依赖 (1h)
- ✅ Task 7.2: 实现多数据源配置 (2h)
- ✅ Task 7.3: 修改索引生成逻辑 (3h) - 开始

### Day 2 (4h)
- ✅ Task 7.3: 修改索引生成逻辑 (3h) - 完成
- ✅ Task 7.4: 添加 CLI 命令 (1h)

### Day 3 (2h)
- ✅ Task 7.5: 端到端集成测试 (2h)
- ✅ Task 7.6: 更新文档 (1h)

---

## 📝 风险和缓解

### 风险 1: 依赖冲突
**描述**: datasource 和 chat 可能有不同版本的依赖  
**缓解**: 统一依赖版本，使用 uv 的依赖解析

### 风险 2: 索引生成时间过长
**描述**: 多数据源可能导致索引生成时间过长  
**缓解**: 使用异步抓取，支持增量同步

### 风险 3: 查询性能下降
**描述**: 多数据源可能导致查询性能下降  
**缓解**: 优化索引结构，使用混合检索

---

## 🎓 学习目标

通过 Phase 7，我们将学习：
1. 如何在 monorepo 中管理本地依赖
2. 如何集成多个数据源到 RAG 系统
3. 如何设计灵活的配置系统
4. 如何进行端到端集成测试

---

## 📚 参考资料

- [LlamaIndex Documentation](https://docs.llamaindex.ai)
- [LlamaDeploy GitHub](https://github.com/run-llama/llama_deploy)
- [uv Documentation](https://docs.astral.sh/uv/)
- datasource PHASE6_REVIEW.md
- datasource PLAN.md

---

## ✅ 完成标准

Phase 7 完成的标志：
1. ✅ chat 项目可以使用 datasource 管理多数据源
2. ✅ 可以从多个数据源生成统一索引
3. ✅ 查询可以检索所有数据源的内容
4. ✅ 所有集成测试通过
5. ✅ 文档完整清晰

完成后，进入 Phase 8 (文档和优化)。
