# 工作流层设计

## 1. 概述

工作流层是系统的业务逻辑层，封装了四个核心功能：
- **需求覆盖率查询**：查询某个需求被哪些Test Case覆盖
- **代码追溯查询**：查询某个Test Case覆盖了哪些需求
- **差距分析**：生成需求-测试覆盖矩阵，识别未覆盖需求
- **版本对比**：对比两个版本的需求变更和覆盖率变化

---

## 2. 需求覆盖率查询 (Coverage Query)

### 2.1 功能描述
输入需求ID或关键词，返回匹配的Test Case列表，支持按平台/类别过滤。

### 2.2 实现逻辑
```python
class CoverageQueryWorkflow:
    def __init__(self, req_index, tc_index, retriever):
        self.req_index = req_index
        self.tc_index = tc_index
        self.retriever = retriever
    
    def query(self, requirement_id: str, filters: dict = None, top_k: int = 10):
        """
        查询需求覆盖率
        
        Args:
            requirement_id: 需求ID或关键词
            filters: 过滤条件 {"platform": "Windows", "category": "Performance"}
            top_k: 返回Top K个结果
        
        Returns:
            List[MatchResult]: 匹配的Test Case列表
        """
        # 1. 从需求索引中查找需求文档
        req_doc = self.req_index.get_by_id(requirement_id)
        if not req_doc:
            # 如果没有精确匹配，尝试关键词搜索
            req_results = self.req_index.search(requirement_id, top_k=1)
            if not req_results:
                return []
            req_doc = req_results[0]
        
        # 2. 使用多阶段检索器匹配Test Case
        matches = self.retriever.retrieve(
            query_doc=req_doc,
            target_index=self.tc_index,
            filters=filters,
            top_k=top_k,
            use_llm_judge=True  # 可选启用LLM判断
        )
        
        return matches
```

### 2.3 输出格式
```json
{
  "requirement": {
    "id": "REQ-001",
    "title": "用户登录功能",
    "description": "系统应支持用户名密码登录..."
  },
  "coverage": [
    {
      "test_case": "test_user_login.py",
      "platform": "Windows",
      "category": "Common",
      "subcategory": "01_Performance",
      "summary": "测试用户登录性能...",
      "confidence": "high",
      "score": 0.85,
      "match_reason": "关键词匹配：用户登录、密码验证；语义相似度高"
    }
  ],
  "total_matches": 3,
  "coverage_rate": "75%"
}
```

---

## 3. 代码追溯查询 (Traceability Query)

### 3.1 功能描述
输入Test Case文件路径，返回该Test Case覆盖的需求列表，以需求卡片形式展示。

### 3.2 实现逻辑
```python
class TraceabilityQueryWorkflow:
    def __init__(self, req_index, tc_index, retriever):
        self.req_index = req_index
        self.tc_index = tc_index
        self.retriever = retriever
    
    def query(self, testcase_path: str, top_k: int = 5):
        """
        查询Test Case追溯的需求
        
        Args:
            testcase_path: Test Case文件路径
            top_k: 返回Top K个需求
        
        Returns:
            List[MatchResult]: 匹配的需求列表
        """
        # 1. 从Test Case索引中查找文档
        tc_doc = self.tc_index.get_by_path(testcase_path)
        if not tc_doc:
            raise ValueError(f"Test Case not found: {testcase_path}")
        
        # 2. 使用多阶段检索器匹配需求
        matches = self.retriever.retrieve(
            query_doc=tc_doc,
            target_index=self.req_index,
            top_k=top_k,
            use_llm_judge=True
        )
        
        return matches
    
    def format_as_cards(self, matches: List[MatchResult]) -> str:
        """格式化为需求卡片"""
        cards = []
        for match in matches:
            card = f"""
┌─────────────────────────────────────────┐
│ 需求ID: {match.metadata.get('title', 'N/A')}
│ 类型: {match.metadata.get('type', 'N/A')}
│ 置信度: {match.confidence.upper()} ({match.score:.2f})
├─────────────────────────────────────────┤
│ 描述:
│ {match.text[:100]}...
├─────────────────────────────────────────┤
│ 匹配原因: {match.match_reason}
└─────────────────────────────────────────┘
"""
            cards.append(card)
        return "\n".join(cards)
```

### 3.3 输出格式
```
┌─────────────────────────────────────────┐
│ 需求ID: REQ-001 用户登录功能
│ 类型: 功能需求
│ 置信度: HIGH (0.85)
├─────────────────────────────────────────┤
│ 描述:
│ 系统应支持用户名密码登录，登录成功后跳转到主页...
├─────────────────────────────────────────┤
│ 匹配原因: 关键词匹配：用户登录、密码验证；语义相似度高
└─────────────────────────────────────────┘
```

---

## 4. 差距分析 (Gap Analysis)

### 4.1 功能描述
生成需求-测试覆盖矩阵，识别未覆盖需求、过度测试需求、孤立Test Case。

### 4.2 实现逻辑
```python
class GapAnalysisWorkflow:
    def __init__(self, req_index, tc_index, retriever):
        self.req_index = req_index
        self.tc_index = tc_index
        self.retriever = retriever
    
    def analyze(self, confidence_threshold: str = "medium"):
        """
        执行差距分析
        
        Args:
            confidence_threshold: 置信度阈值 (high/medium/low)
        
        Returns:
            GapAnalysisReport: 分析报告
        """
        # 1. 获取所有需求和Test Case
        all_requirements = self.req_index.get_all_documents()
        all_testcases = self.tc_index.get_all_documents()
        
        # 2. 构建覆盖矩阵
        coverage_matrix = []
        uncovered_requirements = []
        orphan_testcases = set(tc.doc_id for tc in all_testcases)
        
        for req in all_requirements:
            matches = self.retriever.retrieve(
                query_doc=req,
                target_index=self.tc_index,
                top_k=20,
                use_llm_judge=False  # 差距分析不使用LLM判断（性能考虑）
            )
            
            # 过滤低置信度匹配
            filtered_matches = [
                m for m in matches 
                if self._meets_threshold(m.confidence, confidence_threshold)
            ]
            
            if not filtered_matches:
                uncovered_requirements.append(req)
            else:
                for match in filtered_matches:
                    orphan_testcases.discard(match.doc_id)
            
            coverage_matrix.append({
                "requirement": req,
                "matches": filtered_matches,
                "coverage_count": len(filtered_matches)
            })
        
        # 3. 识别过度测试需求（覆盖数 > 阈值）
        over_tested = [
            row for row in coverage_matrix 
            if row["coverage_count"] > 10
        ]
        
        return GapAnalysisReport(
            coverage_matrix=coverage_matrix,
            uncovered_requirements=uncovered_requirements,
            orphan_testcases=list(orphan_testcases),
            over_tested_requirements=over_tested,
            total_requirements=len(all_requirements),
            total_testcases=len(all_testcases),
            coverage_rate=1 - len(uncovered_requirements) / len(all_requirements)
        )
    
    def export_to_excel(self, report: GapAnalysisReport, output_path: str):
        """导出为Excel报告"""
        import pandas as pd
        
        # Sheet 1: 覆盖矩阵
        matrix_data = []
        for row in report.coverage_matrix:
            req = row["requirement"]
            for match in row["matches"]:
                matrix_data.append({
                    "需求ID": req.metadata.get("title"),
                    "需求类型": req.metadata.get("type"),
                    "Test Case": match.metadata.get("file_path"),
                    "平台": match.metadata.get("platform"),
                    "类别": match.metadata.get("category"),
                    "置信度": match.confidence,
                    "评分": match.score
                })
        
        # Sheet 2: 未覆盖需求
        uncovered_data = [
            {
                "需求ID": req.metadata.get("title"),
                "需求类型": req.metadata.get("type"),
                "描述": req.text[:100]
            }
            for req in report.uncovered_requirements
        ]
        
        # Sheet 3: 孤立Test Case
        orphan_data = [
            {"Test Case": tc_id}
            for tc_id in report.orphan_testcases
        ]
        
        with pd.ExcelWriter(output_path) as writer:
            pd.DataFrame(matrix_data).to_excel(writer, sheet_name="覆盖矩阵", index=False)
            pd.DataFrame(uncovered_data).to_excel(writer, sheet_name="未覆盖需求", index=False)
            pd.DataFrame(orphan_data).to_excel(writer, sheet_name="孤立TestCase", index=False)
```

### 4.3 输出格式
```json
{
  "summary": {
    "total_requirements": 50,
    "total_testcases": 120,
    "coverage_rate": 0.85,
    "uncovered_count": 8,
    "orphan_count": 15,
    "over_tested_count": 3
  },
  "uncovered_requirements": [
    {
      "id": "REQ-042",
      "title": "数据导出功能",
      "type": "功能需求"
    }
  ],
  "orphan_testcases": [
    "test_legacy_feature.py",
    "test_deprecated_api.py"
  ],
  "over_tested_requirements": [
    {
      "id": "REQ-001",
      "title": "用户登录功能",
      "coverage_count": 15
    }
  ]
}
```

---

## 5. 版本对比 (Version Diff)

### 5.1 功能描述
对比两个版本的需求文档，识别新增/删除/修改的需求，以及覆盖率变化。

### 5.2 实现逻辑
```python
class VersionDiffWorkflow:
    def __init__(self, version_manager, req_index, tc_index, retriever):
        self.version_manager = version_manager
        self.req_index = req_index
        self.tc_index = tc_index
        self.retriever = retriever
    
    def diff(self, version_old: str, version_new: str):
        """
        对比两个版本
        
        Args:
            version_old: 旧版本号 (如 "v1.0")
            version_new: 新版本号 (如 "v1.1")
        
        Returns:
            VersionDiffReport: 版本对比报告
        """
        # 1. 获取版本元数据
        old_meta = self.version_manager.get_version_metadata(version_old)
        new_meta = self.version_manager.get_version_metadata(version_new)
        
        # 2. 识别文件变更
        added_files, removed_files, common_files = self.version_manager.compare_versions(
            version_old, version_new
        )
        
        # 3. 加载两个版本的需求索引
        old_index = self.req_index.load(version_old)
        new_index = self.req_index.load(version_new)
        
        # 4. 分析需求变更
        added_requirements = [
            new_index.get_by_source(f) for f in added_files
        ]
        removed_requirements = [
            old_index.get_by_source(f) for f in removed_files
        ]
        
        # 5. 分析覆盖率变化
        coverage_changes = []
        for req_new in new_index.get_all_documents():
            # 查找新版本覆盖率
            matches_new = self.retriever.retrieve(
                query_doc=req_new,
                target_index=self.tc_index,
                top_k=10
            )
            
            # 查找旧版本中的对应需求
            req_old = old_index.find_similar(req_new, threshold=0.9)
            if req_old:
                matches_old = self.retriever.retrieve(
                    query_doc=req_old,
                    target_index=self.tc_index,
                    top_k=10
                )
                
                # 对比覆盖率变化
                if len(matches_new) != len(matches_old):
                    coverage_changes.append({
                        "requirement": req_new,
                        "old_coverage": len(matches_old),
                        "new_coverage": len(matches_new),
                        "change": len(matches_new) - len(matches_old)
                    })
        
        return VersionDiffReport(
            version_old=version_old,
            version_new=version_new,
            added_requirements=added_requirements,
            removed_requirements=removed_requirements,
            coverage_changes=coverage_changes
        )
```

### 5.3 输出格式
```json
{
  "version_old": "v1.0",
  "version_new": "v1.1",
  "summary": {
    "added_count": 5,
    "removed_count": 2,
    "modified_count": 8
  },
  "added_requirements": [
    {
      "id": "REQ-051",
      "title": "数据导出功能",
      "coverage": 0
    }
  ],
  "removed_requirements": [
    {
      "id": "REQ-012",
      "title": "旧版登录接口"
    }
  ],
  "coverage_changes": [
    {
      "requirement": "REQ-001",
      "old_coverage": 10,
      "new_coverage": 12,
      "change": +2
    }
  ]
}
```

---

## 6. 数据模型

### 6.1 MatchResult
```python
@dataclass
class MatchResult:
    doc_id: str
    text: str
    metadata: dict
    score: float
    confidence: str  # "high" | "medium" | "low"
    match_reason: str
```

### 6.2 GapAnalysisReport
```python
@dataclass
class GapAnalysisReport:
    coverage_matrix: List[dict]
    uncovered_requirements: List[Document]
    orphan_testcases: List[str]
    over_tested_requirements: List[dict]
    total_requirements: int
    total_testcases: int
    coverage_rate: float
```

### 6.3 VersionDiffReport
```python
@dataclass
class VersionDiffReport:
    version_old: str
    version_new: str
    added_requirements: List[Document]
    removed_requirements: List[Document]
    coverage_changes: List[dict]
```

---

## 7. 性能优化

### 7.1 批量查询优化
- 差距分析时，批量查询所有需求的覆盖情况，避免逐个查询
- 使用缓存机制，避免重复计算

### 7.2 LLM判断策略
- 需求覆盖率查询：启用LLM判断（精确度优先）
- 代码追溯查询：启用LLM判断（精确度优先）
- 差距分析：禁用LLM判断（性能优先）
- 版本对比：禁用LLM判断（性能优先）

### 7.3 并行处理
- 差距分析时，使用多线程并行查询需求覆盖率
- 版本对比时，并行加载两个版本的索引

---

## 8. 错误处理

### 8.1 需求不存在
```python
if not req_doc:
    raise ValueError(f"Requirement not found: {requirement_id}")
```

### 8.2 Test Case不存在
```python
if not tc_doc:
    raise ValueError(f"Test Case not found: {testcase_path}")
```

### 8.3 版本不存在
```python
if not old_meta or not new_meta:
    raise ValueError(f"Version not found: {version_old} or {version_new}")
```

---

## 9. 扩展性

### 9.1 自定义过滤器
支持用户自定义过滤逻辑：
```python
def custom_filter(match: MatchResult) -> bool:
    # 自定义过滤逻辑
    return match.metadata.get("platform") == "Windows"

matches = workflow.query(
    requirement_id="REQ-001",
    custom_filter=custom_filter
)
```

### 9.2 自定义输出格式
支持用户自定义输出格式化器：
```python
class CustomFormatter:
    def format(self, matches: List[MatchResult]) -> str:
        # 自定义格式化逻辑
        pass

workflow.set_formatter(CustomFormatter())
```
