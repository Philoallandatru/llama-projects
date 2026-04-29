# 共享数据层 - 使用 LlamaIndex Readers

## 重构说明

本次重构将：
1. ✅ 使用 LlamaIndex 内置 Readers 替代自定义连接器和加载器
2. ✅ 保留数据治理功能（质量检查、安全过滤、元数据管理）
3. ✅ 简化架构，减少重复代码
4. ✅ 提供统一的配置和管理接口

## 新架构

```
shared/
├── readers/                    # LlamaIndex Readers 配置和管理
│   ├── __init__.py
│   ├── manager.py             # Reader 管理器
│   ├── config.py              # Reader 配置
│   └── factory.py             # Reader 工厂
│
├── governance/                 # 数据治理层（核心价值）
│   ├── __init__.py
│   ├── quality.py             # 数据质量检查
│   ├── security.py            # 安全过滤（PII）
│   ├── metadata.py            # 元数据管理
│   └── lineage.py             # 数据血缘追踪
│
├── config.py                   # 统一配置
├── quick_start.py             # 快速开始
└── example_usage.py           # 使用示例
```

## 优势

1. **减少维护成本** - 使用 LlamaIndex 社区维护的 Readers
2. **更多数据源** - 100+ 种现成的连接器
3. **原生集成** - 无需转换，直接使用
4. **专注价值** - 专注于数据治理，而非重复造轮子
