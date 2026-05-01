# 预处理层详细设计

## 1. 概述

预处理层负责将原始文档（需求文档、Test Case）转换为结构化的LlamaIndex Document对象，为后续索引和检索做准备。

## 2. 模块结构

```
src/preprocessing/
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py          # 解析器基类
│   └── mineru_parser.py        # MinerU解析器
├── extractors/
│   ├── __init__.py
│   ├── requirement_extractor.py  # 需求提取器
│   └── testcase_extractor.py     # Test Case提取器
├── document_builder.py         # Document构建器
└── __init__.py
```

## 3. MinerU解析器

### 3.1 功能
- 将PDF/Excel文档转换为Markdown格式
- 从文件名提取版本号
- 保留文档结构信息（章节、页码）

### 3.2 接口设计

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

class BaseParser(ABC):
    """文档解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """
        解析文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            {
                "content": str,      # Markdown内容
                "metadata": {
                    "file_name": str,
                    "version": str,  # 从文件名提取
                    "format": str,   # pdf/excel
                    "pages": int     # 页数（PDF）
                }
            }
        """
        pass

class MinerUParser(BaseParser):
    """MinerU文档解析器"""
    
    def __init__(self, output_format: str = "markdown", parse_images: bool = False):
        """
        Args:
            output_format: 输出格式（markdown/json）
            parse_images: 是否解析图片
        """
        self.output_format = output_format
        self.parse_images = parse_images
    
    def parse(self, file_path: Path) -> Dict[str, Any]:
        """解析PDF/Excel文档"""
        # 1. 调用MinerU解析
        # 2. 提取版本号（正则匹配 _v数字.数字）
        # 3. 返回结构化结果
        pass
    
    def _extract_version(self, file_name: str) -> str:
        """
        从文件名提取版本号
        
        Examples:
            "用户需求规格说明书_v1.2.pdf" -> "1.2"
            "系统设计文档_v2.0.1.xlsx" -> "2.0.1"
            "需求文档.pdf" -> "unknown"
        """
        import re
        match = re.search(r'_v([\d.]+)', file_name)
        return match.group(1) if match else "unknown"
```

### 3.3 MinerU配置

```python
# config.yaml
mineru:
  output_format: markdown
  parse_images: false
  parse_tables: true
  ocr_enabled: true
```

### 3.4 输出示例

```python
{
    "content": """
# 第1章 系统概述
## 1.1 系统目标
本系统旨在...

## 1.2 功能需求
### 1.2.1 用户管理
- 用户注册：支持邮箱和手机号注册
- 用户登录：支持密码和验证码登录
...
""",
    "metadata": {
        "file_name": "用户需求规格说明书_v1.2.pdf",
        "version": "1.2",
        "format": "pdf",
        "pages": 45
    }
}
```

## 4. 需求提取器

### 4.1 功能
- 从Markdown文档中提取结构化需求
- 使用LLM识别需求标题、描述、类型、关键词
- 按章节分块处理，避免超context限制

### 4.2 接口设计

```python
from typing import List
from pydantic import BaseModel

class Requirement(BaseModel):
    """需求数据模型"""
    title: str                  # 需求标题/摘要
    description: str            # 详细描述
    type: str                   # 需求类型（功能/性能/兼容性/安全/可用性）
    keywords: List[str]         # 关键词
    source: Dict[str, Any]      # 来源信息

class RequirementExtractor:
    """需求提取器"""
    
    def __init__(self, llm, max_tokens: int = 3000):
        """
        Args:
            llm: LlamaIndex LLM实例
            max_tokens: 单次处理的最大token数
        """
        self.llm = llm
        self.max_tokens = max_tokens
    
    def extract(self, markdown_content: str, metadata: Dict[str, Any]) -> List[Requirement]:
        """
        从Markdown文档提取需求
        
        Args:
            markdown_content: Markdown内容
            metadata: 文档元数据（file_name, version等）
            
        Returns:
            需求列表
        """
        # 1. 按章节分块（基于Markdown标题）
        chunks = self._split_by_chapters(markdown_content)
        
        # 2. 对每个chunk调用LLM提取需求
        requirements = []
        for chunk in chunks:
            reqs = self._extract_from_chunk(chunk, metadata)
            requirements.extend(reqs)
        
        return requirements
    
    def _split_by_chapters(self, content: str) -> List[Dict[str, str]]:
        """
        按章节分块
        
        Returns:
            [
                {"chapter": "1.1 系统目标", "content": "..."},
                {"chapter": "1.2 功能需求", "content": "..."},
                ...
            ]
        """
        # 使用正则匹配Markdown标题（# ## ###）
        # 确保每个chunk不超过max_tokens
        pass
    
    def _extract_from_chunk(self, chunk: Dict[str, str], metadata: Dict[str, Any]) -> List[Requirement]:
        """
        从单个chunk提取需求
        
        使用LLM Prompt:
        """
        prompt = f"""
你是一个需求分析专家。请从以下文档片段中提取所有需求，并以JSON格式返回。

文档信息：
- 文件名：{metadata['file_name']}
- 版本：{metadata['version']}
- 章节：{chunk['chapter']}

文档内容：
{chunk['content']}

请提取所有需求，每个需求包含：
1. title: 需求标题或摘要（简短，10-30字）
2. description: 详细描述（保留原文关键信息）
3. type: 需求类型（从以下选择：功能、性能、兼容性、安全、可用性、其他）
4. keywords: 关键词列表（3-10个，用于后续检索）

返回格式（JSON数组）：
[
  {{
    "title": "用户注册功能",
    "description": "系统应支持用户通过邮箱和手机号进行注册...",
    "type": "功能",
    "keywords": ["用户注册", "邮箱", "手机号", "验证码"]
  }},
  ...
]

注意：
- 只提取明确的需求，不要提取背景描述或说明性文字
- 如果某段文字不是需求，可以不提取
- 关键词应该是具体的技术术语或业务术语
"""
        
        # 调用LLM
        response = self.llm.complete(prompt)
        
        # 解析JSON
        import json
        try:
            reqs_data = json.loads(response.text)
        except json.JSONDecodeError:
            # 如果LLM返回的不是纯JSON，尝试提取JSON部分
            reqs_data = self._extract_json_from_text(response.text)
        
        # 构建Requirement对象
        requirements = []
        for req_data in reqs_data:
            req = Requirement(
                title=req_data['title'],
                description=req_data['description'],
                type=req_data['type'],
                keywords=req_data['keywords'],
                source={
                    "file": metadata['file_name'],
                    "version": metadata['version'],
                    "chapter": chunk['chapter'],
                    "format": metadata['format']
                }
            )
            requirements.append(req)
        
        return requirements
    
    def _extract_json_from_text(self, text: str) -> List[Dict]:
        """从LLM响应中提取JSON（处理LLM可能返回额外文字的情况）"""
        import re
        # 查找 [...] 或 {...}
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return []
```

### 4.3 提取示例

**输入（Markdown片段）：**
```markdown
## 1.2.1 用户管理
### 用户注册
系统应支持用户通过邮箱和手机号进行注册。注册时需要验证邮箱或手机号的有效性。

### 用户登录
系统应支持密码登录和验证码登录两种方式。
```

**输出（Requirement列表）：**
```python
[
    Requirement(
        title="用户注册功能",
        description="系统应支持用户通过邮箱和手机号进行注册。注册时需要验证邮箱或手机号的有效性。",
        type="功能",
        keywords=["用户注册", "邮箱", "手机号", "验证"],
        source={
            "file": "用户需求规格说明书_v1.2.pdf",
            "version": "1.2",
            "chapter": "1.2.1 用户管理",
            "format": "pdf"
        }
    ),
    Requirement(
        title="用户登录功能",
        description="系统应支持密码登录和验证码登录两种方式。",
        type="功能",
        keywords=["用户登录", "密码", "验证码"],
        source={
            "file": "用户需求规格说明书_v1.2.pdf",
            "version": "1.2",
            "chapter": "1.2.1 用户管理",
            "format": "pdf"
        }
    )
]
```

## 5. Test Case提取器

### 5.1 功能
- 使用AST解析Python Test Case文件
- 优先使用docstring，无docstring时用LLM生成摘要
- 从文件路径提取元数据（platform、category、subcategory）

### 5.2 接口设计

```python
import ast
from pathlib import Path

class TestCase(BaseModel):
    """Test Case数据模型"""
    file_path: str              # 文件路径
    file_name: str              # 文件名
    platform: str               # Windows/Linux
    category: str               # Common/Customer
    subcategory: str            # Performance/Compatibility等
    summary: str                # 摘要
    keywords: List[str]         # 关键词
    functions: List[str]        # 函数列表

class TestCaseExtractor:
    """Test Case提取器"""
    
    def __init__(self, llm, testcase_root: Path):
        """
        Args:
            llm: LlamaIndex LLM实例
            testcase_root: Test Case根目录
        """
        self.llm = llm
        self.testcase_root = testcase_root
    
    def extract(self, file_path: Path) -> TestCase:
        """
        从Python文件提取Test Case信息
        
        Args:
            file_path: Test Case文件路径
            
        Returns:
            TestCase对象
        """
        # 1. 解析文件路径，提取元数据
        metadata = self._extract_metadata_from_path(file_path)
        
        # 2. 使用AST解析代码
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        # 3. 提取函数列表和docstring
        functions = []
        docstring = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
                # 获取模块级docstring（第一个字符串）
                if docstring is None and isinstance(node, ast.Module):
                    docstring = ast.get_docstring(node)
        
        # 如果没有模块级docstring，尝试获取第一个函数的docstring
        if docstring is None:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        break
        
        # 4. 生成摘要
        if docstring:
            summary = docstring.strip()
            keywords = self._extract_keywords_from_text(summary)
        else:
            # 使用LLM生成摘要
            summary, keywords = self._generate_summary_with_llm(code, metadata)
        
        # 5. 构建TestCase对象
        return TestCase(
            file_path=str(file_path),
            file_name=file_path.name,
            platform=metadata['platform'],
            category=metadata['category'],
            subcategory=metadata['subcategory'],
            summary=summary,
            keywords=keywords,
            functions=functions
        )
    
    def _extract_metadata_from_path(self, file_path: Path) -> Dict[str, str]:
        """
        从文件路径提取元数据
        
        路径格式：TestCase/{platform}/{category}/{subcategory}/xxx.py
        
        Examples:
            TestCase/Windows/Common/01_Performance/test_boot_time.py
            -> {platform: "Windows", category: "Common", subcategory: "Performance"}
        """
        relative_path = file_path.relative_to(self.testcase_root)
        parts = relative_path.parts
        
        return {
            "platform": parts[0] if len(parts) > 0 else "Unknown",
            "category": parts[1] if len(parts) > 1 else "Unknown",
            "subcategory": parts[2].split('_', 1)[-1] if len(parts) > 2 else "Unknown"  # 去掉编号前缀
        }
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词（简单实现：提取名词和技术术语）"""
        # 简单实现：分词 + 过滤停用词
        # 可以使用jieba或其他NLP工具
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # 过滤常见停用词
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'test', 'case'}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return list(set(keywords))[:10]  # 最多10个关键词
    
    def _generate_summary_with_llm(self, code: str, metadata: Dict[str, str]) -> tuple[str, List[str]]:
        """
        使用LLM生成Test Case摘要
        
        Returns:
            (summary, keywords)
        """
        prompt = f"""
你是一个测试工程师。请分析以下Test Case代码，生成简短的摘要和关键词。

Test Case信息：
- 平台：{metadata['platform']}
- 类别：{metadata['category']}
- 子类别：{metadata['subcategory']}

代码：
```python
{code[:2000]}  # 只取前2000字符，避免超context
```

请返回JSON格式：
{{
  "summary": "简短描述这个Test Case测试什么功能（1-2句话）",
  "keywords": ["关键词1", "关键词2", ...]  // 3-10个关键词
}}
"""
        
        response = self.llm.complete(prompt)
        
        # 解析JSON
        import json
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            result = self._extract_json_from_text(response.text)
        
        return result.get('summary', ''), result.get('keywords', [])
    
    def _extract_json_from_text(self, text: str) -> Dict:
        """从LLM响应中提取JSON"""
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        return {}
```

### 5.3 提取示例

**输入（Test Case文件）：**
```python
# TestCase/Windows/Common/01_Performance/test_boot_time.py

def test_system_boot_time():
    """测试系统启动时间是否在30秒内"""
    start_time = time.time()
    # ... 测试代码 ...
    boot_time = time.time() - start_time
    assert boot_time < 30

def test_application_launch_time():
    """测试应用启动时间"""
    # ... 测试代码 ...
    pass
```

**输出（TestCase对象）：**
```python
TestCase(
    file_path="TestCase/Windows/Common/01_Performance/test_boot_time.py",
    file_name="test_boot_time.py",
    platform="Windows",
    category="Common",
    subcategory="Performance",
    summary="测试系统启动时间是否在30秒内",
    keywords=["系统", "启动", "时间", "性能"],
    functions=["test_system_boot_time", "test_application_launch_time"]
)
```

## 6. Document构建器

### 6.1 功能
- 将Requirement和TestCase转换为LlamaIndex Document对象
- 设计合理的text和metadata字段，优化检索效果

### 6.2 接口设计

```python
from llama_index.core import Document

class DocumentBuilder:
    """Document构建器"""
    
    @staticmethod
    def build_requirement_document(requirement: Requirement) -> Document:
        """
        构建需求Document
        
        设计原则：
        - text字段：用于向量化和BM25检索，应包含最重要的信息
        - metadata字段：用于过滤和展示，应包含结构化信息
        """
        # text字段：标题 + 描述（用于检索）
        text = f"{requirement.title}\n\n{requirement.description}"
        
        # metadata字段
        metadata = {
            "doc_type": "requirement",
            "title": requirement.title,
            "type": requirement.type,
            "keywords": requirement.keywords,
            "source_file": requirement.source['file'],
            "version": requirement.source['version'],
            "chapter": requirement.source.get('chapter', ''),
            "format": requirement.source.get('format', '')
        }
        
        return Document(
            text=text,
            metadata=metadata,
            id_=f"req_{hash(text)}"  # 生成唯一ID
        )
    
    @staticmethod
    def build_testcase_document(testcase: TestCase) -> Document:
        """
        构建Test Case Document
        
        设计原则：
        - text字段：文件名 + 摘要（用于检索）
        - metadata字段：路径、平台、类别等（用于过滤）
        """
        # text字段：文件名 + 摘要
        text = f"{testcase.file_name}\n\n{testcase.summary}"
        
        # metadata字段
        metadata = {
            "doc_type": "testcase",
            "file_path": testcase.file_path,
            "file_name": testcase.file_name,
            "platform": testcase.platform,
            "category": testcase.category,
            "subcategory": testcase.subcategory,
            "keywords": testcase.keywords,
            "functions": testcase.functions
        }
        
        return Document(
            text=text,
            metadata=metadata,
            id_=f"tc_{hash(testcase.file_path)}"
        )
```

### 6.3 Document示例

**需求Document：**
```python
Document(
    text="用户注册功能\n\n系统应支持用户通过邮箱和手机号进行注册。注册时需要验证邮箱或手机号的有效性。",
    metadata={
        "doc_type": "requirement",
        "title": "用户注册功能",
        "type": "功能",
        "keywords": ["用户注册", "邮箱", "手机号", "验证"],
        "source_file": "用户需求规格说明书_v1.2.pdf",
        "version": "1.2",
        "chapter": "1.2.1 用户管理",
        "format": "pdf"
    },
    id_="req_1234567890"
)
```

**Test Case Document：**
```python
Document(
    text="test_boot_time.py\n\n测试系统启动时间是否在30秒内",
    metadata={
        "doc_type": "testcase",
        "file_path": "TestCase/Windows/Common/01_Performance/test_boot_time.py",
        "file_name": "test_boot_time.py",
        "platform": "Windows",
        "category": "Common",
        "subcategory": "Performance",
        "keywords": ["系统", "启动", "时间", "性能"],
        "functions": ["test_system_boot_time", "test_application_launch_time"]
    },
    id_="tc_9876543210"
)
```

## 7. 完整流程示例

```python
# 1. 初始化组件
parser = MinerUParser()
req_extractor = RequirementExtractor(llm)
tc_extractor = TestCaseExtractor(llm, testcase_root=Path("TestCase"))
doc_builder = DocumentBuilder()

# 2. 处理需求文档
parsed_doc = parser.parse(Path("需求文档_v1.2.pdf"))
requirements = req_extractor.extract(parsed_doc['content'], parsed_doc['metadata'])
req_documents = [doc_builder.build_requirement_document(req) for req in requirements]

# 3. 处理Test Case
testcase_files = Path("TestCase").rglob("*.py")
tc_documents = []
for tc_file in testcase_files:
    testcase = tc_extractor.extract(tc_file)
    tc_doc = doc_builder.build_testcase_document(testcase)
    tc_documents.append(tc_doc)

# 4. 传递给索引层
# (见下一章节)
```

## 8. 性能优化

### 8.1 批量处理
- Test Case提取可以并行处理（使用multiprocessing）
- LLM调用可以批量处理（如果LLM支持）

### 8.2 缓存机制
- 缓存已解析的文档（基于文件hash）
- 缓存LLM生成的摘要（避免重复调用）

### 8.3 增量更新
- 只处理新增或修改的文件
- 使用文件修改时间或hash判断是否需要重新处理

## 9. 错误处理

### 9.1 文档解析失败
- 记录错误日志
- 跳过该文档，继续处理其他文档

### 9.2 LLM调用失败
- 重试机制（最多3次）
- 降级策略：使用简单的规则提取（如提取前N个句子作为摘要）

### 9.3 代码解析失败
- 记录错误日志
- 跳过该文件，继续处理其他文件

## 10. 测试策略

### 10.1 单元测试
- 测试版本号提取
- 测试章节分块
- 测试AST解析
- 测试JSON解析

### 10.2 集成测试
- 准备测试数据集（包含各种格式的文档）
- 验证端到端流程
- 检查输出Document的质量

### 10.3 LLM输出质量测试
- 人工评估LLM提取的需求是否准确
- 检查关键词是否合理
- 验证摘要是否简洁明了
