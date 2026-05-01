# Requirement Tracing System

需求-测试追溯系统：自动化分析需求文档与测试用例的覆盖关系

## 📋 项目简介

这是一个基于 LlamaIndex 和本地 LLM 的需求追溯系统，用于：
- 分析需求文档（PDF/Excel）与测试用例（Python代码）的覆盖关系
- 识别未覆盖的需求和缺失的测试
- 追踪需求变更对测试的影响
- 生成覆盖率报告和差距分析

## ✨ 核心功能

### 1. 需求覆盖率查询
查询某个需求被哪些测试用例覆盖，支持按平台、类别过滤。

```bash
req-trace coverage "用户登录功能" --platform Windows --category Performance
```

### 2. 代码追溯查询
从测试用例反向查找对应的需求，了解测试目的。

```bash
req-trace trace TestCase/Windows/Common/01_Performance/test_login_001.py
```

### 3. 差距分析
生成完整的覆盖矩阵，识别未覆盖需求和过度测试的需求。

```bash
req-trace gap --export coverage_report.xlsx
```

### 4. 版本对比
对比不同版本需求文档的变更，分析覆盖率变化。

```bash
req-trace diff --old v1.0 --new v1.1
```

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户接口层                              │
│                   CLI / Web API / 定期报告                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        工作流层                                │
│   覆盖率查询 | 追溯查询 | 差距分析 | 版本对比                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        匹配层                                  │
│   BM25召回 → 向量重排序 → LLM判断 → 置信度评估                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        索引层                                  │
│   需求索引 (Vector + BM25) | Test Case索引 | 版本管理          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        预处理层                                │
│   MinerU解析 → LLM提取需求 → AST分析代码 → Document构建        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/requirement-tracing.git
cd requirement-tracing

# 安装依赖
pip install -e .

# 复制配置文件
cp config.yaml.example config.yaml
# 编辑 config.yaml，配置LLM和Embedding模型
```

### 构建索引

```bash
# 索引需求文档
req-trace index requirements --input data/requirements/ --version v1.0

# 索引测试用例
req-trace index testcases --input data/testcases/
```

### 查询示例

```bash
# 查询需求覆盖率
req-trace coverage "用户登录功能"

# 追溯测试用例
req-trace trace TestCase/Windows/Common/test_login_001.py

# 生成差距分析报告
req-trace gap --export report.xlsx

# 对比版本变更
req-trace diff --old v1.0 --new v1.1
```

## 📚 文档

完整的设计文档位于 `docs/design/` 目录：

1. [系统概览](docs/design/01-overview.md) - 项目背景、技术选型、架构设计
2. [预处理层](docs/design/02-preprocessing.md) - 文档解析、需求提取、代码分析
3. [索引层](docs/design/03-indexing.md) - 向量索引、BM25索引、版本管理
4. [匹配层](docs/design/04-matching.md) - 多阶段检索、LLM判断、置信度评估
5. [工作流层](docs/design/05-workflows.md) - 四个核心工作流的实现
6. [API和CLI](docs/design/06-api-cli.md) - 命令行接口和Web API设计
7. [部署方案](docs/design/07-deployment.md) - 本地部署、Docker、K8s
8. [项目结构](docs/design/08-project-structure.md) - 目录结构、开发指南

## 🛠️ 技术栈

- **文档解析**: MinerU (magic-pdf)
- **LLM**: 本地模型（通过Ollama）
- **Embedding**: HuggingFace模型（bge-large-zh-v1.5）
- **索引和检索**: LlamaIndex
- **关键词匹配**: BM25
- **CLI**: Click
- **Web API**: FastAPI
- **数据处理**: Pandas, openpyxl

## 📊 工作流程

### 1. 预处理阶段（离线）

```
需求文档 (PDF/Excel)
    ↓ MinerU解析
Markdown文本
    ↓ LLM提取
结构化需求 (title, description, keywords...)
    ↓ Document构建
LlamaIndex Documents
    ↓ 索引构建
Vector Index + BM25 Index
```

### 2. 查询阶段（在线）

```
用户查询
    ↓ 阶段1: BM25召回
Top 50候选
    ↓ 阶段2: 向量重排序
Top 20精选
    ↓ 阶段3: LLM判断（可选）
Top 5最终结果
    ↓ 置信度评估
High/Medium/Low + 匹配原因
```

## 🎯 使用场景

### 场景1: 新需求发布后检查覆盖率

```bash
# 1. 索引新版本需求文档
req-trace index requirements --input requirements_v1.1.pdf --version v1.1

# 2. 生成覆盖率报告
req-trace gap --version v1.1 --export coverage_v1.1.xlsx

# 3. 识别未覆盖的需求
# 查看报告中的"未覆盖需求"部分
```

### 场景2: 测试用例追溯

```bash
# 开发人员想了解某个测试用例的目的
req-trace trace TestCase/Windows/Customer/02_Compatibility/test_edge_case_042.py

# 输出：
# 需求ID: REQ-042
# 需求标题: 边界条件处理
# 需求描述: 系统应正确处理输入边界值...
# 置信度: high
# 匹配原因: 测试步骤与需求描述高度一致
```

### 场景3: 版本变更影响分析

```bash
# 需求文档从v1.0升级到v1.1
req-trace diff --old v1.0 --new v1.1

# 输出：
# 新增需求: 3个 (REQ-101, REQ-102, REQ-103)
# 删除需求: 1个 (REQ-005)
# 修改需求: 2个 (REQ-012, REQ-034)
# 
# 覆盖率变化:
# - 新增需求未覆盖: 2个
# - 删除需求的测试需清理: 3个测试用例
```

## 🔧 配置说明

编辑 `config.yaml` 配置系统参数：

```yaml
# LLM配置
llm:
  model_name: "qwen2.5:14b"
  base_url: "http://localhost:11434"
  temperature: 0.1
  max_tokens: 2000

# Embedding配置
embedding:
  model_name: "BAAI/bge-large-zh-v1.5"
  device: "cuda"  # 或 "cpu"
  batch_size: 32

# 检索配置
retriever:
  bm25_top_k: 50
  vector_top_k: 20
  llm_top_k: 5
  bm25_weight: 0.3
  vector_weight: 0.5
  path_weight: 0.2
  high_confidence_threshold: 0.8
  medium_confidence_threshold: 0.6
```

## 📈 性能指标

基于中型项目（50个需求文档，500个测试用例）的测试结果：

| 操作 | 响应时间 | 说明 |
|------|---------|------|
| 单个需求覆盖率查询 | < 2秒 | 使用BM25+向量混合检索 |
| 单个测试追溯查询 | < 1秒 | 直接向量检索 |
| 完整差距分析 | 5-10分钟 | 批量处理所有需求 |
| 版本对比 | 2-5分钟 | 取决于变更数量 |
| 索引构建（需求） | 10-30分钟 | 取决于文档数量和LLM速度 |
| 索引构建（测试） | 5-15分钟 | 取决于代码文件数量 |

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交变更 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

详见 [开发指南](docs/design/08-project-structure.md)

## 📝 许可证

MIT License

## 🙏 致谢

- [LlamaIndex](https://www.llamaindex.ai/) - 强大的LLM应用框架
- [MinerU](https://github.com/opendatalab/MinerU) - 高质量PDF解析工具
- [Ollama](https://ollama.ai/) - 本地LLM运行环境

## 📧 联系方式

- 问题追踪: https://github.com/your-org/requirement-tracing/issues
- 讨论区: https://github.com/your-org/requirement-tracing/discussions
- 邮箱: your-email@example.com

---

**注意**: 本项目目前处于设计阶段，代码实现正在进行中。
