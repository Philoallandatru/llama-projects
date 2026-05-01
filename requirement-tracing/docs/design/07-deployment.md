# 部署方案详细设计

## 1. 概述

系统支持三种部署方式：
- **本地CLI部署**：适合个人使用和脚本自动化
- **Web服务部署**：适合团队协作和系统集成
- **定期报告部署**：适合自动化场景

---

## 2. 本地CLI部署

### 2.1 系统要求

- **操作系统**：Windows 10+, Linux, macOS
- **Python版本**：3.9+
- **硬件要求**：
  - CPU：4核以上
  - 内存：8GB以上（推荐16GB）
  - 磁盘：10GB以上可用空间
  - GPU：可选（用于加速向量化）

### 2.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/requirement-tracing.git
cd requirement-tracing

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -e .

# 4. 安装开发依赖（可选）
pip install -e ".[dev]"

# 5. 配置
mkdir -p ~/.req-trace
cp config.yaml.example ~/.req-trace/config.yaml
# 编辑配置文件

# 6. 启动Ollama（如果使用本地LLM）
ollama serve
ollama pull qwen2.5:14b

# 7. 验证安装
req-trace --help
```

### 2.3 快速开始

```bash
# 1. 构建索引
req-trace index build \
  --req-docs ./data/requirements \
  --testcases ./data/TestCase \
  --version v1.0

# 2. 查询
req-trace coverage "性能测试需求"
req-trace trace "Windows/Common/01_Performance/test_perf_01.py"

# 3. 生成报告
req-trace gap --output gap_report.xlsx
```

### 2.4 优点和缺点

**优点：**
- 部署简单，无需服务器
- 数据完全本地，安全性高
- 适合按需查询场景
- 无网络依赖

**缺点：**
- 每次查询需要加载索引（首次较慢）
- 不支持多用户并发
- 无Web界面
- 需要手动管理索引

---

## 3. Web服务部署

### 3.1 架构图

```
┌─────────────┐
│   Browser   │
│  (Web UI)   │
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│   FastAPI   │  ← Web服务层
│   Server    │
└──────┬──────┘
       │
┌──────▼──────┐
│  Workflows  │  ← 工作流层
└──────┬──────┘
       │
┌──────▼──────┐
│   Indexes   │  ← 索引层（持久化）
└─────────────┘
```

### 3.2 Docker部署

#### 3.2.1 Dockerfile

```dockerfile
# Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

# 创建数据目录
RUN mkdir -p /data/indexes /data/cache

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["python", "-m", "src.api.server"]
```

#### 3.2.2 docker-compose.yml

```yaml
# docker-compose.yml

version: '3.8'

services:
  req-trace-api:
    build: .
    container_name: req-trace-api
    ports:
      - "8000:8000"
    volumes:
      - ./data/indexes:/data/indexes
      - ./data/cache:/data/cache
      - ./config.yaml:/root/.req-trace/config.yaml
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - PYTHONUNBUFFERED=1
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - req-trace-network
  
  ollama:
    image: ollama/ollama:latest
    container_name: req-trace-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    networks:
      - req-trace-network
    # GPU支持（可选）
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]
  
  # Nginx反向代理（可选）
  nginx:
    image: nginx:alpine
    container_name: req-trace-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - req-trace-api
    restart: unless-stopped
    networks:
      - req-trace-network

volumes:
  ollama_data:

networks:
  req-trace-network:
    driver: bridge
```

#### 3.2.3 启动服务

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f req-trace-api

# 4. 初始化Ollama模型
docker exec -it req-trace-ollama ollama pull qwen2.5:14b

# 5. 构建索引（在容器内）
docker exec -it req-trace-api req-trace index build \
  --req-docs /data/requirements \
  --testcases /data/TestCase \
  --version v1.0

# 6. 访问API文档
# http://localhost:8000/docs

# 7. 停止服务
docker-compose down
```

### 3.3 Kubernetes部署（可选）

#### 3.3.1 deployment.yaml

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: req-trace-api
  labels:
    app: req-trace
spec:
  replicas: 2
  selector:
    matchLabels:
      app: req-trace
  template:
    metadata:
      labels:
        app: req-trace
    spec:
      containers:
      - name: api
        image: your-registry/req-trace:latest
        ports:
        - containerPort: 8000
        env:
        - name: OLLAMA_BASE_URL
          value: "http://ollama-service:11434"
        volumeMounts:
        - name: indexes
          mountPath: /data/indexes
        - name: config
          mountPath: /root/.req-trace
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: indexes
        persistentVolumeClaim:
          claimName: req-trace-indexes-pvc
      - name: config
        configMap:
          name: req-trace-config
---
apiVersion: v1
kind: Service
metadata:
  name: req-trace-service
spec:
  selector:
    app: req-trace
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3.4 优点和缺点

**优点：**
- 支持多用户并发访问
- 索引常驻内存，查询速度快
- 可以提供Web UI界面
- 易于集成到其他系统
- 支持水平扩展

**缺点：**
- 部署复杂度较高
- 需要服务器资源
- 需要维护和监控

---

## 4. 定期报告部署

### 4.1 使用Cron定期生成报告

```bash
# crontab -e

# 每周一早上8点生成差距分析报告
0 8 * * 1 cd /path/to/requirement-tracing && \
  source venv/bin/activate && \
  req-trace gap --output /reports/gap_$(date +\%Y\%m\%d).xlsx && \
  echo "差距分析报告已生成" | mail -s "Weekly Gap Report" team@example.com

# 每天凌晨2点更新索引
0 2 * * * cd /path/to/requirement-tracing && \
  source venv/bin/activate && \
  req-trace index build \
    --req-docs /data/requirements \
    --testcases /data/TestCase \
    --version latest
```

### 4.2 使用GitHub Actions自动化

```yaml
# .github/workflows/weekly-report.yml

name: Weekly Gap Analysis Report

on:
  schedule:
    - cron: '0 8 * * 1'  # 每周一早上8点
  workflow_dispatch:  # 支持手动触发

jobs:
  generate-report:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -e .
    
    - name: Download requirements and testcases
      run: |
        # 从S3/Git等下载最新数据
        aws s3 sync s3://your-bucket/requirements ./data/requirements
        aws s3 sync s3://your-bucket/TestCase ./data/TestCase
    
    - name: Build index
      run: |
        req-trace index build \
          --req-docs ./data/requirements \
          --testcases ./data/TestCase \
          --version $(date +%Y%m%d)
    
    - name: Generate gap report
      run: |
        req-trace gap --output gap_report_$(date +%Y%m%d).xlsx
    
    - name: Upload report
      uses: actions/upload-artifact@v3
      with:
        name: gap-report
        path: gap_report_*.xlsx
    
    - name: Send notification
      uses: dawidd6/action-send-mail@v3
      with:
        server_address: smtp.gmail.com
        server_port: 465
        username: ${{ secrets.EMAIL_USERNAME }}
        password: ${{ secrets.EMAIL_PASSWORD }}
        subject: Weekly Gap Analysis Report
        to: team@example.com
        from: noreply@example.com
        body: 差距分析报告已生成，请查看附件。
        attachments: gap_report_*.xlsx
```

---

## 5. 性能优化

### 5.1 索引优化

```python
# 使用更小的嵌入模型
embedding_config:
  model_name: BAAI/bge-small-zh-v1.5  # small而非large
  device: cuda
  batch_size: 64  # 增大批量大小

# 使用量化模型
embedding_config:
  model_name: BAAI/bge-small-zh-v1.5
  model_kwargs:
    quantization_config: "int8"
```

### 5.2 缓存策略

```python
# src/utils/cache.py

from functools import lru_cache
import hashlib

class QueryCache:
    """查询结果缓存"""
    
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, query: str, filters: dict = None):
        key = self._make_key(query, filters)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
        return None
    
    def set(self, query: str, filters: dict, result):
        key = self._make_key(query, filters)
        self.cache[key] = (result, time.time())
        
        # LRU淘汰
        if len(self.cache) > self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def _make_key(self, query: str, filters: dict):
        data = f"{query}_{filters}"
        return hashlib.md5(data.encode()).hexdigest()
```

### 5.3 并行处理

```python
# 差距分析时并行查询
from concurrent.futures import ThreadPoolExecutor

def analyze_parallel(self, requirements):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(self._query_coverage, req)
            for req in requirements
        ]
        results = [f.result() for f in futures]
    return results
```

---

## 6. 监控和日志

### 6.1 日志配置

```python
# src/utils/logger.py

import logging
from pathlib import Path

def setup_logger(name: str, log_file: Path, level=logging.INFO):
    """配置日志"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### 6.2 Prometheus监控（Web服务）

```python
# src/api/server.py

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# 定义指标
request_count = Counter('req_trace_requests_total', 'Total requests', ['endpoint'])
request_duration = Histogram('req_trace_request_duration_seconds', 'Request duration', ['endpoint'])

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.middleware("http")
async def add_metrics(request, call_next):
    """记录请求指标"""
    endpoint = request.url.path
    
    with request_duration.labels(endpoint=endpoint).time():
        response = await call_next(request)
    
    request_count.labels(endpoint=endpoint).inc()
    
    return response
```

---

## 7. 安全性

### 7.1 API认证

```python
# src/api/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证JWT token"""
    token = credentials.credentials
    
    # 验证token逻辑
    if not is_valid_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return token

# 在API端点中使用
@app.post("/api/coverage")
async def query_coverage(
    request: CoverageQueryRequest,
    token: str = Depends(verify_token)
):
    # ...
```

### 7.2 HTTPS配置

```nginx
# nginx.conf

server {
    listen 443 ssl http2;
    server_name req-trace.example.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://req-trace-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name req-trace.example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 8. 备份和恢复

### 8.1 索引备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/req-trace"
INDEX_DIR="/data/indexes"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份
tar -czf "$BACKUP_DIR/indexes_$DATE.tar.gz" "$INDEX_DIR"

# 保留最近7天的备份
find "$BACKUP_DIR" -name "indexes_*.tar.gz" -mtime +7 -delete

echo "备份完成: indexes_$DATE.tar.gz"
```

### 8.2 索引恢复

```bash
#!/bin/bash
# restore.sh

BACKUP_FILE=$1
INDEX_DIR="/data/indexes"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: ./restore.sh <backup_file>"
    exit 1
fi

# 备份当前索引
mv "$INDEX_DIR" "$INDEX_DIR.old"

# 恢复备份
tar -xzf "$BACKUP_FILE" -C /data

echo "恢复完成"
```

---

## 9. 故障排查

### 9.1 常见问题

**问题1：索引加载失败**
```bash
# 检查索引目录
ls -la /data/indexes

# 检查索引文件完整性
req-trace index list

# 重建索引
req-trace index build --req-docs ./docs --testcases ./TestCase --version v1.0
```

**问题2：LLM调用超时**
```yaml
# 增加超时时间
llm:
  timeout: 120  # 秒
  max_retries: 3
```

**问题3：内存不足**
```python
# 使用更小的批量大小
embedding_config:
  batch_size: 16  # 减小批量大小

# 使用更小的模型
embedding_config:
  model_name: BAAI/bge-small-zh-v1.5
```

### 9.2 日志分析

```bash
# 查看错误日志
grep ERROR /var/log/req-trace/app.log

# 查看慢查询
grep "duration > 5s" /var/log/req-trace/app.log

# 实时监控日志
tail -f /var/log/req-trace/app.log
```

---

## 10. 升级和迁移

### 10.1 版本升级

```bash
# 1. 备份数据
./backup.sh

# 2. 停止服务
docker-compose down

# 3. 更新代码
git pull origin main

# 4. 更新依赖
pip install -e . --upgrade

# 5. 迁移数据（如果需要）
python scripts/migrate.py

# 6. 启动服务
docker-compose up -d

# 7. 验证
curl http://localhost:8000/api/health
```

### 10.2 数据迁移

```python
# scripts/migrate.py

def migrate_v1_to_v2():
    """从v1.0迁移到v2.0"""
    # 1. 加载旧版本索引
    old_index = load_old_index()
    
    # 2. 转换数据格式
    new_documents = convert_documents(old_index.documents)
    
    # 3. 构建新版本索引
    new_index = build_new_index(new_documents)
    
    # 4. 保存
    new_index.save()
    
    print("迁移完成")
```
