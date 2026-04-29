# Phase 6: 高级功能 - 实施计划

## 概述

**目标**: 优化现有数据源的性能和功能，实现增量同步、异步抓取、HTML 清理和附件下载。

**预计时间**: 3-4 天

**优先级**: 高（性能优化和用户体验提升）

## 背景

Phase 5 审查发现的主要改进点：
1. **性能瓶颈**: 同步 I/O 导致大量数据抓取缓慢
2. **全量同步**: 每次都抓取所有数据，浪费时间和资源
3. **HTML 质量**: 简单的正则表达式清理不够彻底
4. **功能缺失**: 附件未下载和解析

## 任务分解

### Task 6.1: 增量同步 (优先级: 高)

**目标**: 实现基于时间戳的增量同步，只抓取更新的数据

**工作量**: 6-8 小时

#### 子任务
- [ ] 6.1.1 设计增量同步接口
- [ ] 6.1.2 在 manifest.json 中记录 last_sync_time
- [ ] 6.1.3 为 JiraDataSource 实现增量同步
- [ ] 6.1.4 为 ConfluenceDataSource 实现增量同步
- [ ] 6.1.5 更新 SourceManager.sync_source() 支持增量模式
- [ ] 6.1.6 添加 CLI 参数 --full/--incremental
- [ ] 6.1.7 编写单元测试
- [ ] 6.1.8 编写集成测试

#### 设计方案

**1. BaseDataSource 接口扩展**
```python
class BaseDataSource(ABC):
    @abstractmethod
    def fetch_raw(self, output_dir: Path, since: Optional[datetime] = None) -> int:
        """抓取原始数据
        
        Args:
            output_dir: 输出目录
            since: 只抓取此时间后更新的数据（None 表示全量）
        """
```

**2. Manifest 扩展**
```python
{
    "source_name": "my_jira",
    "source_type": "jira",
    "last_sync_time": "2026-04-29T10:30:00Z",  # 新增
    "last_full_sync_time": "2026-04-28T00:00:00Z",  # 新增
    "total_items": 150,
    "sync_history": [  # 新增
        {
            "timestamp": "2026-04-29T10:30:00Z",
            "mode": "incremental",
            "items_fetched": 5,
            "items_updated": 3,
            "items_deleted": 0
        }
    ]
}
```

**3. Jira 增量查询**
```python
def _build_jql_with_time(self, since: datetime) -> str:
    """构建带时间过滤的 JQL"""
    base_jql = self.jql or f"project={self.project}"
    time_filter = f"updated >= '{since.strftime('%Y-%m-%d %H:%M')}'"
    return f"{base_jql} AND {time_filter}"
```

**4. Confluence 增量查询**
```python
def _fetch_pages_since(self, since: datetime) -> List[Dict]:
    """抓取指定时间后更新的 Pages"""
    if self.space_key:
        cql = f"space={self.space_key} AND lastModified >= '{since.isoformat()}'"
    else:
        cql = f"{self.cql} AND lastModified >= '{since.isoformat()}'"
    return self._fetch_pages_by_cql(cql)
```

#### 验收标准
- [ ] 增量同步只抓取更新的数据
- [ ] manifest.json 正确记录同步时间
- [ ] 全量同步仍然正常工作
- [ ] CLI 支持 `--full` 和 `--incremental` 参数
- [ ] 测试覆盖率 > 90%

---

### Task 6.2: 异步抓取 (优先级: 高)

**目标**: 使用 asyncio + aiohttp 并发抓取，提升性能 5-10 倍

**工作量**: 10-12 小时

#### 子任务
- [ ] 6.2.1 设计异步接口
- [ ] 6.2.2 实现异步 HTTP 客户端（aiohttp）
- [ ] 6.2.3 为 JiraDataSource 实现异步抓取
- [ ] 6.2.4 为 ConfluenceDataSource 实现异步抓取
- [ ] 6.2.5 实现并发控制（Semaphore）
- [ ] 6.2.6 实现异步重试机制
- [ ] 6.2.7 更新 SourceManager 支持异步
- [ ] 6.2.8 编写单元测试
- [ ] 6.2.9 编写性能测试

#### 设计方案

**1. 异步基类**
```python
class AsyncDataSource(ABC):
    """异步数据源基类"""
    
    @abstractmethod
    async def fetch_raw_async(
        self, 
        output_dir: Path, 
        since: Optional[datetime] = None
    ) -> int:
        """异步抓取原始数据"""
    
    async def _make_request_async(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """异步 HTTP 请求（带重试）"""
```

**2. 并发控制**
```python
class JiraDataSource(BaseDataSource):
    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.max_concurrent = 10  # 最大并发数
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def _fetch_issue_async(
        self, 
        session: aiohttp.ClientSession, 
        issue_key: str
    ) -> Dict:
        """异步抓取单个 Issue"""
        async with self.semaphore:
            url = f"{self.server}/rest/api/2/issue/{issue_key}"
            async with session.get(url) as response:
                return await response.json()
```

**3. 批量并发抓取**
```python
async def _fetch_issues_batch_async(
    self, 
    issue_keys: List[str]
) -> List[Dict]:
    """批量异步抓取 Issues"""
    async with aiohttp.ClientSession() as session:
        tasks = [
            self._fetch_issue_async(session, key) 
            for key in issue_keys
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

**4. 兼容同步接口**
```python
def fetch_raw(self, output_dir: Path, since: Optional[datetime] = None) -> int:
    """同步接口（内部调用异步）"""
    return asyncio.run(self.fetch_raw_async(output_dir, since))
```

#### 验收标准
- [ ] 异步抓取速度提升 5-10 倍
- [ ] 并发控制正确（不超过限制）
- [ ] 异步重试机制正常工作
- [ ] 兼容现有同步接口
- [ ] 测试覆盖率 > 85%

---

### Task 6.3: HTML 清理 (优先级: 中)

**目标**: 使用 BeautifulSoup 彻底清理 HTML，提升文档质量

**工作量**: 3-4 小时

#### 子任务
- [ ] 6.3.1 添加 beautifulsoup4 依赖
- [ ] 6.3.2 实现 HTML 清理工具类
- [ ] 6.3.3 更新 ConfluenceDataSource 使用新清理器
- [ ] 6.3.4 更新 JiraDataSource 使用新清理器
- [ ] 6.3.5 编写单元测试
- [ ] 6.3.6 对比清理前后质量

#### 设计方案

**1. HTML 清理工具**
```python
# datasource/core/utils/html_cleaner.py

from bs4 import BeautifulSoup
from typing import Optional

class HTMLCleaner:
    """HTML 内容清理器"""
    
    @staticmethod
    def clean(html: str, preserve_links: bool = True) -> str:
        """清理 HTML 标签
        
        Args:
            html: HTML 内容
            preserve_links: 是否保留链接文本
        
        Returns:
            清理后的纯文本
        """
        if not html:
            return ""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除 script 和 style 标签
        for tag in soup(['script', 'style', 'meta', 'link']):
            tag.decompose()
        
        # 处理链接
        if preserve_links:
            for a in soup.find_all('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if href and text:
                    a.replace_with(f"{text} ({href})")
        
        # 提取文本
        text = soup.get_text(separator='\n', strip=True)
        
        # 清理多余空行
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        return '\n'.join(lines)
    
    @staticmethod
    def extract_metadata(html: str) -> dict:
        """提取 HTML 元数据"""
        soup = BeautifulSoup(html, 'html.parser')
        
        metadata = {}
        
        # 提取标题
        title = soup.find('title')
        if title:
            metadata['title'] = title.get_text(strip=True)
        
        # 提取 meta 标签
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata
```

**2. 集成到数据源**
```python
from datasource.core.utils.html_cleaner import HTMLCleaner

class ConfluenceDataSource(BaseDataSource):
    def build_document(self, item_id: str, raw_data: Dict[str, Any]) -> Document:
        body = raw_data.get("body", {}).get("storage", {}).get("value", "")
        
        # 使用新的清理器
        clean_body = HTMLCleaner.clean(body, preserve_links=True)
        
        # 提取元数据
        html_metadata = HTMLCleaner.extract_metadata(body)
        
        # ...
```

#### 验收标准
- [ ] HTML 标签完全移除
- [ ] 链接文本保留（可选）
- [ ] 多余空行清理
- [ ] 文档质量提升（人工抽查）
- [ ] 测试覆盖率 > 90%

---

### Task 6.4: 附件下载 (优先级: 低)

**目标**: 下载并解析文本附件（PDF、Word、图片 OCR）

**工作量**: 8-10 小时

#### 子任务
- [ ] 6.4.1 设计附件存储结构
- [ ] 6.4.2 实现附件下载器
- [ ] 6.4.3 实现 PDF 解析
- [ ] 6.4.4 实现 Word 解析
- [ ] 6.4.5 实现图片 OCR（可选）
- [ ] 6.4.6 集成到 JiraDataSource
- [ ] 6.4.7 集成到 ConfluenceDataSource
- [ ] 6.4.8 编写单元测试
- [ ] 6.4.9 编写集成测试

#### 设计方案

**1. 附件存储结构**
```
data/sources/{source_name}/
├── raw/
│   ├── ISSUE-123.json
│   └── attachments/
│       ├── ISSUE-123_attachment1.pdf
│       └── ISSUE-123_attachment2.png
├── documents/
│   ├── ISSUE-123.json
│   └── ISSUE-123_attachment1.json  # 附件解析后的文档
```

**2. 附件下载器**
```python
# datasource/core/utils/attachment_downloader.py

import aiohttp
from pathlib import Path
from typing import Optional

class AttachmentDownloader:
    """附件下载器"""
    
    def __init__(self, max_size_mb: int = 10):
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    async def download_async(
        self,
        session: aiohttp.ClientSession,
        url: str,
        output_path: Path,
        auth: Optional[tuple] = None
    ) -> bool:
        """异步下载附件
        
        Returns:
            是否下载成功
        """
        try:
            async with session.get(url, auth=auth) as response:
                # 检查大小
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.max_size_bytes:
                    logger.warning(f"Attachment too large: {url}")
                    return False
                
                # 下载
                content = await response.read()
                output_path.write_bytes(content)
                return True
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
```

**3. 附件解析器**
```python
# datasource/core/utils/attachment_parser.py

from pathlib import Path
from typing import Optional
from llama_index.core import Document
from llama_index.readers.file import PDFReader, DocxReader

class AttachmentParser:
    """附件解析器"""
    
    def __init__(self):
        self.pdf_reader = PDFReader()
        self.docx_reader = DocxReader()
    
    def parse(self, file_path: Path) -> Optional[Document]:
        """解析附件为 Document"""
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.pdf':
                docs = self.pdf_reader.load_data(file_path)
                return docs[0] if docs else None
            elif suffix in ['.docx', '.doc']:
                docs = self.docx_reader.load_data(file_path)
                return docs[0] if docs else None
            elif suffix in ['.png', '.jpg', '.jpeg']:
                # TODO: 实现 OCR
                return None
            else:
                logger.warning(f"Unsupported attachment type: {suffix}")
                return None
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None
```

**4. 集成到数据源**
```python
class JiraDataSource(BaseDataSource):
    async def _fetch_and_parse_attachments_async(
        self,
        session: aiohttp.ClientSession,
        issue_key: str,
        attachments: List[Dict]
    ) -> List[Document]:
        """异步下载并解析附件"""
        downloader = AttachmentDownloader(max_size_mb=10)
        parser = AttachmentParser()
        
        docs = []
        for att in attachments:
            # 只处理文本附件
            if not self._is_text_attachment(att):
                continue
            
            # 下载
            output_path = self.paths.raw_dir / "attachments" / f"{issue_key}_{att['filename']}"
            success = await downloader.download_async(
                session, att['content'], output_path, auth=self.auth
            )
            
            if success:
                # 解析
                doc = parser.parse(output_path)
                if doc:
                    doc.metadata['source_issue'] = issue_key
                    doc.metadata['attachment_name'] = att['filename']
                    docs.append(doc)
        
        return docs
```

#### 验收标准
- [ ] 能下载 PDF、Word 附件
- [ ] 能解析附件内容
- [ ] 附件大小限制正常工作
- [ ] 附件正确关联到原始 Issue/Page
- [ ] 测试覆盖率 > 80%

---

### Task 6.5: 代码重构 (优先级: 中)

**目标**: 减少代码重复，提高可维护性

**工作量**: 4-6 小时

#### 子任务
- [ ] 6.5.1 提取通用分页逻辑
- [ ] 6.5.2 提取通用重试逻辑
- [ ] 6.5.3 提取通用限流逻辑
- [ ] 6.5.4 添加缺失的类型注解
- [ ] 6.5.5 运行 mypy 检查
- [ ] 6.5.6 运行 pylint 检查

#### 设计方案

**1. 通用分页器**
```python
# datasource/core/utils/pagination.py

from typing import Callable, Dict, Any, List, TypeVar

T = TypeVar('T')

class Paginator:
    """通用分页器"""
    
    @staticmethod
    def paginate(
        fetch_func: Callable[[int, int], Dict[str, Any]],
        page_size: int = 50,
        max_results: Optional[int] = None
    ) -> List[T]:
        """通用分页逻辑
        
        Args:
            fetch_func: 抓取函数，接受 (start, limit) 返回 {"results": [...], "size": N}
            page_size: 每页大小
            max_results: 最大结果数
        
        Returns:
            所有结果列表
        """
        results = []
        start = 0
        
        while True:
            # 计算本次抓取数量
            limit = page_size
            if max_results:
                remaining = max_results - len(results)
                if remaining <= 0:
                    break
                limit = min(limit, remaining)
            
            # 抓取
            response = fetch_func(start, limit)
            batch = response.get("results", [])
            
            if not batch:
                break
            
            results.extend(batch)
            
            # 检查是否还有更多
            if response.get("size", 0) < limit:
                break
            
            start += limit
        
        return results
```

**2. 使用分页器**
```python
class ConfluenceDataSource(BaseDataSource):
    def _fetch_pages_by_space(self, space_key: str) -> List[Dict]:
        """使用通用分页器"""
        def fetch_func(start: int, limit: int) -> Dict:
            url = f"{self.server}/rest/api/content"
            params = {
                "spaceKey": space_key,
                "start": start,
                "limit": limit,
                "expand": "body.storage,version,space"
            }
            response = self._make_request("GET", url, params=params)
            return response.json()
        
        return Paginator.paginate(fetch_func, page_size=50)
```

#### 验收标准
- [ ] 代码重复率 < 3%
- [ ] mypy 无错误
- [ ] pylint 评分 > 9.0
- [ ] 所有测试通过

---

## 实施顺序

### Week 1 (Day 1-2)
1. Task 6.3: HTML 清理（快速见效）
2. Task 6.1: 增量同步（高优先级）

### Week 1 (Day 3-4)
3. Task 6.2: 异步抓取（高优先级，耗时）

### Week 2 (Day 1)
4. Task 6.5: 代码重构（提高质量）

### Week 2 (Day 2) - 可选
5. Task 6.4: 附件下载（低优先级）

## 验收标准

### 功能验收
- [ ] 增量同步正常工作
- [ ] 异步抓取速度提升 5-10 倍
- [ ] HTML 清理质量提升
- [ ] 附件下载和解析正常（如实现）

### 性能验收
- [ ] 1000 个 Jira Issues 同步 < 2 分钟（异步）
- [ ] 增量同步 100 个更新 < 30 秒
- [ ] HTML 清理不影响性能

### 质量验收
- [ ] 所有测试通过
- [ ] 测试覆盖率 > 85%
- [ ] 代码重复率 < 3%
- [ ] mypy 无错误
- [ ] pylint 评分 > 9.0

### 文档验收
- [ ] 更新 README.md
- [ ] 更新 API 文档
- [ ] 添加性能对比数据

## 交付物

- [ ] `datasource/core/utils/html_cleaner.py`
- [ ] `datasource/core/utils/attachment_downloader.py`
- [ ] `datasource/core/utils/attachment_parser.py`
- [ ] `datasource/core/utils/pagination.py`
- [ ] 更新的 `datasource/core/sources/jira.py`
- [ ] 更新的 `datasource/core/sources/confluence.py`
- [ ] 更新的 `datasource/core/manager.py`
- [ ] `tests/test_html_cleaner.py`
- [ ] `tests/test_attachment_downloader.py`
- [ ] `tests/test_pagination.py`
- [ ] `tests/performance/test_async_performance.py`
- [ ] `PHASE6_REVIEW.md`
- [ ] `PERFORMANCE_COMPARISON.md`

## 风险和缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 异步改造破坏现有功能 | 高 | 中 | 保留同步接口，充分测试 |
| aiohttp 依赖冲突 | 中 | 低 | 使用虚拟环境隔离 |
| 增量同步逻辑复杂 | 中 | 中 | 详细设计，分步实现 |
| 附件解析失败率高 | 低 | 中 | 设置大小限制，记录失败 |

## 成功指标

- ✅ 同步速度提升 5-10 倍
- ✅ 增量同步减少 80% 数据传输
- ✅ HTML 清理质量提升（人工抽查）
- ✅ 代码质量评分 > 9.0
- ✅ 测试覆盖率 > 85%

## 下一步

完成 Phase 6 后：
- Phase 7: chat 集成
- Phase 8: 文档和优化
