# Jira Analysis System - 部署指南

## 部署架构

由于 LlamaDeploy 已被废弃，我们采用标准的 FastAPI 生产部署方案：

```
┌─────────────────────────────────────────────┐
│              Nginx (反向代理)                │
│         SSL终止 + 负载均衡 + 静态文件         │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐  ┌───────▼────────┐
│  Uvicorn #1    │  │  Uvicorn #2    │
│  (Worker 1)    │  │  (Worker 2)    │
│  Port 8001     │  │  Port 8002     │
└────────────────┘  └────────────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │   Supervisor      │
        │   (进程管理)       │
        └───────────────────┘
```

## 部署选项

### 选项 1: Docker 部署（推荐）

**优点**：
- 环境隔离，依赖管理简单
- 易于扩展和迁移
- 支持 Docker Compose 多容器编排

**适用场景**：
- 云环境部署（AWS ECS, Azure Container Instances, GCP Cloud Run）
- Kubernetes 集群
- 本地开发和测试环境

### 选项 2: 传统服务器部署

**优点**：
- 直接控制系统资源
- 无容器开销
- 适合现有基础设施

**适用场景**：
- 物理服务器或 VM
- 已有 Python 环境的服务器
- 需要直接访问本地资源

### 选项 3: Serverless 部署

**优点**：
- 按需付费，成本优化
- 自动扩展
- 无需管理服务器

**限制**：
- 冷启动延迟（首次请求慢）
- 执行时间限制（通常 15-30 分钟）
- 不适合长时间运行的 workflow

**适用场景**：
- AWS Lambda + API Gateway
- Azure Functions
- Google Cloud Functions

**注意**：由于 LLM 分析可能需要 15-20 秒，需要配置足够的超时时间。

## 推荐部署方案

### 生产环境：Docker + Nginx + Supervisor

```yaml
# docker-compose.yml
version: '3.8'

services:
  jira-analysis-api:
    build: .
    ports:
      - "8001:8000"
    environment:
      - JIRA_URL=${JIRA_URL}
      - JIRA_USERNAME=${JIRA_USERNAME}
      - JIRA_PASSWORD=${JIRA_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_BASE=${OPENAI_API_BASE}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - jira-analysis-api
    restart: unless-stopped
```

### 开发环境：直接运行

```bash
# 使用 uvicorn 开发服务器
uv run uvicorn src.api_server:app --reload --port 4501

# 或使用 Python 直接运行
uv run python src/api_server.py
```

## 配置管理

### 环境变量

创建 `.env` 文件：

```bash
# Jira 配置
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_PASSWORD=your-api-token

# OpenAI 配置（或兼容的 API）
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=http://localhost:1234/v1

# 应用配置
LOG_LEVEL=INFO
MAX_CONCURRENT_ANALYSES=5
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4

# 数据源路径
DATASOURCE_PATH=../datasource/data
```

### 配置文件

`config.yaml` 包含：
- Jira 连接配置
- 数据源索引路径
- Profile 配置
- LLM 参数

## 进程管理

### Supervisor 配置

```ini
[program:jira-analysis-api]
command=/path/to/venv/bin/uvicorn src.api_server:app --host 0.0.0.0 --port 8001 --workers 2
directory=/path/to/jira-analysis
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/jira-analysis/api.log
environment=PATH="/path/to/venv/bin"
```

### Systemd 配置

```ini
[Unit]
Description=Jira Analysis API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/jira-analysis
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn src.api_server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

## 反向代理配置

### Nginx 配置

```nginx
upstream jira_analysis {
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # API 端点
    location /api/ {
        proxy_pass http://jira_analysis;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding on;
    }

    # 健康检查
    location /health {
        proxy_pass http://jira_analysis;
        access_log off;
    }

    # 静态文件（前端）
    location / {
        root /var/www/jira-analysis/ui/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## 日志和监控

### 日志配置

```python
# src/api_server.py
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
handler = RotatingFileHandler(
    'logs/api_server.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(handler)
```

### 监控指标

建议监控：
- API 响应时间
- 错误率
- 并发请求数
- LLM 调用延迟
- 证据检索性能
- 内存和 CPU 使用率

可以使用：
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- CloudWatch (AWS)
- Application Insights (Azure)

## 扩展策略

### 水平扩展

1. **多 Worker 部署**
   ```bash
   uvicorn src.api_server:app --workers 4
   ```

2. **负载均衡**
   - Nginx upstream 配置多个后端
   - 使用 least_conn 或 ip_hash 策略

3. **容器编排**
   - Docker Swarm
   - Kubernetes (HPA 自动扩展)

### 垂直扩展

- 增加 CPU 核心数（提高并发处理能力）
- 增加内存（支持更大的 embedding 模型和索引）
- 使用 GPU（加速 embedding 计算）

## 安全建议

1. **API 认证**
   - 添加 API Key 验证
   - 使用 OAuth 2.0 / JWT

2. **网络安全**
   - 启用 HTTPS
   - 配置 CORS 白名单
   - 使用防火墙限制访问

3. **密钥管理**
   - 使用环境变量或密钥管理服务（AWS Secrets Manager, Azure Key Vault）
   - 不要在代码中硬编码密钥

4. **输入验证**
   - 验证 issue_key 格式
   - 限制批量分析的 issue 数量
   - 防止 SQL 注入和 XSS

## 性能优化

1. **缓存策略**
   - Redis 缓存 issue 数据
   - 缓存 embedding 结果
   - 缓存分析结果（可选）

2. **异步处理**
   - 使用消息队列（Celery + Redis/RabbitMQ）
   - 长时间运行的分析任务异步执行

3. **数据库优化**
   - 使用连接池
   - 索引优化
   - 查询优化

## 故障排查

### 常见问题

1. **API 响应慢**
   - 检查 LLM 服务是否正常
   - 检查证据检索性能
   - 查看日志中的性能指标

2. **内存不足**
   - 减少 max_concurrent_analyses
   - 增加服务器内存
   - 优化 embedding 模型大小

3. **连接超时**
   - 检查 Jira API 连接
   - 检查 OpenAI API 连接
   - 增加超时配置

### 日志位置

- API 日志：`logs/api_server.log`
- Nginx 日志：`/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- Supervisor 日志：`/var/log/supervisor/jira-analysis-api.log`

## 下一步

1. 创建 Dockerfile 和 docker-compose.yml
2. 编写部署脚本
3. 配置 CI/CD 流水线
4. 设置监控和告警
5. 编写运维文档
