# 匹配层详细设计

## 1. 概述

匹配层负责在需求和Test Case之间建立关联关系，采用多阶段混合检索策略，结合关键词召回、语义相似度和LLM判断。

## 2. 模块结构

```
src/matching/
├── __init__.py
├── retriever.py        # 多阶段检索器
└── llm_judge.py        # LLM相关性判断器
```

## 3. 数据模型

### 3.1 匹配结果

```python
from dataclasses import dataclass
from typing import Dict, Any, Literal

@dataclass
class MatchResult:
    """匹配结果"""
    doc_id: str                                    # 文档ID
    text: str                                      # 文档文本
    metadata: Dict[str, Any]                       # 文档元数据
    score: float                                   # 匹配分数（0-1）
    confidence: Literal['high', 'medium', 'low']   # 置信度
    match_reason: str                              # 匹配原因说明
```

## 4. 多阶段检索器

### 4.1 设计思路

采用三阶段漏斗式检索策略：
1. **阶段1 - BM25快速召回**：使用关键词快速召回候选集（top 20）
2. **阶段2 - 向量精确匹配**：使用语义相似度重排序，混合BM25和向量分数
3. **阶段3 - LLM精确判断**（可选）：对高分候选使用LLM进行最终判断

### 4.2 接口设计

```python
from typing import List, Optional, Dict, Any
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.schema import NodeWithScore

class MultiStageRetriever:
    """多阶段混合检索器"""
    
    def __init__(
        self,
        vector_retriever: VectorIndexRetriever,
        bm25_retriever: BM25Retriever,
        llm_judge: Optional['LLMJudge'] = None,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.5,
        path_weight: float = 0.2,
        high_threshold: float = 0.8,
        medium_threshold: float = 0.6,
        use_llm_judge: bool = False
    ):
        """
        Args:
            vector_retriever: 向量检索器
            bm25_retriever: BM25检索器
            llm_judge: LLM判断器（可选）
            bm25_weight: BM25分数权重
            vector_weight: 向量分数权重
            path_weight: 路径匹配权重
            high_threshold: 高置信度阈值
            medium_threshold: 中等置信度阈值
            use_llm_judge: 是否启用LLM判断
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.llm_judge = llm_judge
        
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.path_weight = path_weight
        
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self.use_llm_judge = use_llm_judge
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MatchResult]:
        """
        多阶段检索
        
        Args:
            query: 查询文本
            top_k: 返回的top k结果数
            filters: 元数据过滤条件（如platform、category等）
            
        Returns:
            匹配结果列表（按分数降序）
        """
        # 阶段1：BM25快速召回
        stage1_results = self._stage1_keyword_recall(query, filters)
        
        if not stage1_results:
            return []
        
        # 阶段2：向量语义重排序
        stage2_results = self._stage2_semantic_rerank(query, stage1_results, filters)
        
        # 阶段3：LLM精确判断（可选）
        if self.use_llm_judge and self.llm_judge:
            stage3_results = self._stage3_llm_judge(query, stage2_results[:top_k])
        else:
            stage3_results = stage2_results[:top_k]
        
        # 转换为MatchResult
        match_results = []
        for node, score in stage3_results:
            confidence = self._determine_confidence(score)
            match_reason = self._generate_match_reason(query, node, score)
            
            match_results.append(MatchResult(
                doc_id=node.node.id_,
                text=node.node.text,
                metadata=node.node.metadata,
                score=score,
                confidence=confidence,
                match_reason=match_reason
            ))
        
        return match_results
    
    def _stage1_keyword_recall(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[NodeWithScore]:
        """
        阶段1：BM25关键词召回
        
        Args:
            query: 查询文本
            filters: 元数据过滤条件
            
        Returns:
            召回的节点列表（top 20）
        """
        # BM25检索
        nodes = self.bm25_retriever.retrieve(query)
        
        # 应用过滤器
        if filters:
            filtered_nodes = []
            for node in nodes:
                if self._match_filters(node.node.metadata, filters):
                    filtered_nodes.append(node)
            nodes = filtered_nodes
        
        # 返回top 20
        return nodes[:20]
    
    def _stage2_semantic_rerank(
        self,
        query: str,
        stage1_results: List[NodeWithScore],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[tuple[NodeWithScore, float]]:
        """
        阶段2：向量语义重排序
        
        Args:
            query: 查询文本
            stage1_results: 阶段1召回的节点
            filters: 元数据过滤条件
            
        Returns:
            重排序后的节点列表（节点，混合分数）
        """
        # 获取向量检索结果
        vector_nodes = self.vector_retriever.retrieve(query)
        
        # 构建向量分数映射
        vector_scores = {node.node.id_: node.score for node in vector_nodes}
        
        # 计算混合分数
        reranked = []
        for node in stage1_results:
            bm25_score = node.score if node.score else 0.0
            vector_score = vector_scores.get(node.node.id_, 0.0)
            
            # 路径匹配加权
            path_bonus = 0.0
            if filters:
                path_bonus = self._check_path_match(node.node.metadata, filters)
            
            # 混合分数
            hybrid_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score +
                self.path_weight * path_bonus
            )
            
            reranked.append((node, hybrid_score))
        
        # 按混合分数降序排序
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        return reranked
    
    def _stage3_llm_judge(
        self,
        query: str,
        stage2_results: List[tuple[NodeWithScore, float]]
    ) -> List[tuple[NodeWithScore, float]]:
        """
        阶段3：LLM精确判断
        
        Args:
            query: 查询文本
            stage2_results: 阶段2重排序的节点
            
        Returns:
            LLM判断后的节点列表
        """
        if not self.llm_judge:
            return stage2_results
        
        refined = []
        for node, score in stage2_results:
            # 使用LLM判断相关性
            llm_score = self.llm_judge.judge_relevance(
                query=query,
                candidate_text=node.node.text,
                candidate_metadata=node.node.metadata
            )
            
            # 混合LLM分数和阶段2分数
            final_score = 0.7 * llm_score + 0.3 * score
            refined.append((node, final_score))
        
        # 重新排序
        refined.sort(key=lambda x: x[1], reverse=True)
        
        return refined
    
    def _match_filters(
        self,
        metadata: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """检查元数据是否匹配过滤条件"""
        for key, value in filters.items():
            if metadata.get(key) != value:
                return False
        return True
    
    def _check_path_match(
        self,
        metadata: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> float:
        """
        检查路径匹配度
        
        例如：查询"Windows性能测试"，如果metadata中platform=Windows且subcategory=Performance，
        则返回1.0；部分匹配返回0.5；不匹配返回0.0
        """
        match_count = 0
        total_filters = len(filters)
        
        if total_filters == 0:
            return 0.0
        
        for key, value in filters.items():
            if metadata.get(key) == value:
                match_count += 1
        
        return match_count / total_filters
    
    def _determine_confidence(self, score: float) -> str:
        """根据分数确定置信度"""
        if score >= self.high_threshold:
            return 'high'
        elif score >= self.medium_threshold:
            return 'medium'
        else:
            return 'low'
    
    def _generate_match_reason(
        self,
        query: str,
        node: NodeWithScore,
        score: float
    ) -> str:
        """
        生成匹配原因说明
        
        Args:
            query: 查询文本
            node: 匹配的节点
            score: 匹配分数
            
        Returns:
            匹配原因说明
        """
        reasons = []
        
        # 1. 关键词匹配
        query_keywords = set(query.lower().split())
        text_keywords = set(node.node.text.lower().split())
        common_keywords = query_keywords & text_keywords
        
        if common_keywords:
            reasons.append(f"关键词匹配: {', '.join(list(common_keywords)[:3])}")
        
        # 2. 语义相似度
        if score >= self.high_threshold:
            reasons.append("高语义相似度")
        elif score >= self.medium_threshold:
            reasons.append("中等语义相似度")
        
        # 3. 元数据匹配
        metadata = node.node.metadata
        if metadata.get('platform'):
            reasons.append(f"平台: {metadata['platform']}")
        if metadata.get('subcategory'):
            reasons.append(f"类别: {metadata['subcategory']}")
        
        return " | ".join(reasons) if reasons else "基于语义相似度"
```

### 4.3 使用示例

```python
# 1. 初始化检索器
retriever = MultiStageRetriever(
    vector_retriever=req_index.get_vector_retriever(top_k=20),
    bm25_retriever=req_index.get_bm25_retriever(),
    llm_judge=llm_judge,
    use_llm_judge=False  # 默认不启用LLM判断
)

# 2. 查询需求覆盖的Test Case
query = "用户登录功能应支持多种认证方式"
results = retriever.retrieve(
    query=query,
    top_k=5,
    filters={"platform": "Windows"}
)

# 3. 输出结果
for result in results:
    print(f"文件: {result.metadata['file_path']}")
    print(f"置信度: {result.confidence} ({result.score:.2f})")
    print(f"匹配原因: {result.match_reason}")
    print(f"摘要: {result.text[:100]}...")
    print("-" * 80)
```

## 5. LLM相关性判断器

### 5.1 设计思路

使用LLM对候选匹配进行精确判断，评估需求和Test Case之间的相关性。

### 5.2 接口设计

```python
import re
from typing import Dict, Any
from llama_index.llms.ollama import Ollama

class LLMJudge:
    """LLM相关性判断器"""
    
    def __init__(
        self,
        llm: Ollama,
        score_threshold: float = 0.7
    ):
        """
        Args:
            llm: LLM实例
            score_threshold: 相关性分数阈值（0-1）
        """
        self.llm = llm
        self.score_threshold = score_threshold
    
    def judge_relevance(
        self,
        query: str,
        candidate_text: str,
        candidate_metadata: Dict[str, Any]
    ) -> float:
        """
        判断候选文档与查询的相关性
        
        Args:
            query: 查询文本（需求描述或Test Case摘要）
            candidate_text: 候选文档文本
            candidate_metadata: 候选文档元数据
            
        Returns:
            相关性分数（0-1）
        """
        # 构建prompt
        prompt = self._build_prompt(query, candidate_text, candidate_metadata)
        
        # 调用LLM
        response = self.llm.complete(prompt)
        
        # 解析分数
        score = self._parse_score(response.text)
        
        return score
    
    def _build_prompt(
        self,
        query: str,
        candidate_text: str,
        candidate_metadata: Dict[str, Any]
    ) -> str:
        """构建LLM判断prompt"""
        # 格式化元数据
        metadata_str = "\n".join([
            f"- {key}: {value}"
            for key, value in candidate_metadata.items()
            if key in ['platform', 'category', 'subcategory', 'type', 'source_file']
        ])
        
        prompt = f"""你是一个需求追溯专家，需要判断一个Test Case是否覆盖了某个需求。

**需求描述：**
{query}

**Test Case信息：**
{candidate_text}

**元数据：**
{metadata_str}

**任务：**
请评估这个Test Case与需求的相关性，给出0-10分的评分：
- 0-3分：不相关或几乎不相关
- 4-6分：部分相关，有一定关联但不完全覆盖
- 7-10分：高度相关，Test Case明确测试了需求中的功能

**评分标准：**
1. Test Case是否测试了需求中描述的核心功能？
2. Test Case的测试场景是否与需求一致？
3. Test Case是否覆盖了需求的关键验收条件？

请直接给出评分（0-10的整数），然后简要说明理由。

格式：
评分：X
理由：...
"""
        return prompt
    
    def _parse_score(self, response: str) -> float:
        """
        解析LLM返回的评分
        
        Args:
            response: LLM返回的文本
            
        Returns:
            归一化的分数（0-1）
        """
        # 尝试匹配"评分：X"格式
        match = re.search(r'评分[：:]\s*(\d+)', response)
        if match:
            score = int(match.group(1))
            # 归一化到0-1
            return min(max(score / 10.0, 0.0), 1.0)
        
        # 尝试匹配纯数字
        match = re.search(r'\b(\d+)\b', response)
        if match:
            score = int(match.group(1))
            if score <= 10:
                return min(max(score / 10.0, 0.0), 1.0)
        
        # 默认返回中等分数
        print(f"警告：无法解析LLM评分，返回默认值0.5。响应：{response[:100]}")
        return 0.5
    
    def batch_judge(
        self,
        query: str,
        candidates: List[tuple[str, Dict[str, Any]]]
    ) -> List[float]:
        """
        批量判断相关性
        
        Args:
            query: 查询文本
            candidates: 候选列表（文本，元数据）
            
        Returns:
            相关性分数列表
        """
        scores = []
        for text, metadata in candidates:
            score = self.judge_relevance(query, text, metadata)
            scores.append(score)
        return scores
```

### 5.3 使用示例

```python
# 1. 初始化LLM判断器
from llama_index.llms.ollama import Ollama

llm = Ollama(model="qwen2.5:7b", base_url="http://localhost:11434")
llm_judge = LLMJudge(llm=llm, score_threshold=0.7)

# 2. 判断单个候选
query = "用户登录功能应支持多种认证方式"
candidate_text = "测试用户使用用户名密码登录系统"
candidate_metadata = {
    "platform": "Windows",
    "subcategory": "Authentication"
}

score = llm_judge.judge_relevance(query, candidate_text, candidate_metadata)
print(f"相关性分数：{score:.2f}")

# 3. 批量判断
candidates = [
    ("测试用户使用用户名密码登录", {"platform": "Windows"}),
    ("测试用户使用OAuth登录", {"platform": "Windows"}),
    ("测试系统性能", {"platform": "Linux"})
]

scores = llm_judge.batch_judge(query, candidates)
for (text, _), score in zip(candidates, scores):
    print(f"{text}: {score:.2f}")
```

## 6. 匹配策略对比

### 6.1 三种策略

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **纯BM25** | 速度快，可解释性强 | 无法理解语义，召回率低 | 关键词明确的查询 |
| **BM25 + 向量** | 平衡速度和准确性 | 需要调参，可能误判 | 大多数场景（推荐） |
| **BM25 + 向量 + LLM** | 准确性最高 | 速度慢，成本高 | 高精度要求的场景 |

### 6.2 性能对比

假设索引规模：1000个需求，5000个Test Case

| 策略 | 平均响应时间 | 准确率（估计） | 成本 |
|------|-------------|---------------|------|
| 纯BM25 | ~50ms | 60-70% | 低 |
| BM25 + 向量 | ~200ms | 75-85% | 中 |
| BM25 + 向量 + LLM | ~2s | 85-95% | 高 |

### 6.3 推荐配置

```python
# 默认配置（平衡模式）
retriever = MultiStageRetriever(
    vector_retriever=vector_retriever,
    bm25_retriever=bm25_retriever,
    bm25_weight=0.3,
    vector_weight=0.5,
    path_weight=0.2,
    high_threshold=0.8,
    medium_threshold=0.6,
    use_llm_judge=False
)

# 高精度配置（启用LLM）
retriever_high_precision = MultiStageRetriever(
    vector_retriever=vector_retriever,
    bm25_retriever=bm25_retriever,
    llm_judge=llm_judge,
    bm25_weight=0.2,
    vector_weight=0.5,
    path_weight=0.3,
    high_threshold=0.85,
    medium_threshold=0.7,
    use_llm_judge=True
)

# 快速模式（仅BM25）
retriever_fast = MultiStageRetriever(
    vector_retriever=vector_retriever,
    bm25_retriever=bm25_retriever,
    bm25_weight=0.7,
    vector_weight=0.3,
    path_weight=0.0,
    high_threshold=0.75,
    medium_threshold=0.55,
    use_llm_judge=False
)
```

## 7. 置信度标注

### 7.1 置信度定义

- **high（高置信度）**：分数 ≥ 0.8，强烈推荐，可直接使用
- **medium（中等置信度）**：分数 0.6-0.8，建议人工审核
- **low（低置信度）**：分数 < 0.6，仅供参考

### 7.2 置信度应用

```python
def filter_by_confidence(
    results: List[MatchResult],
    min_confidence: str = 'medium'
) -> List[MatchResult]:
    """按置信度过滤结果"""
    confidence_order = {'low': 0, 'medium': 1, 'high': 2}
    min_level = confidence_order[min_confidence]
    
    return [
        r for r in results
        if confidence_order[r.confidence] >= min_level
    ]

# 使用示例
high_confidence_results = filter_by_confidence(results, min_confidence='high')
print(f"高置信度结果数量：{len(high_confidence_results)}")
```

## 8. 错误处理

### 8.1 检索失败
- 捕获检索异常
- 记录失败查询
- 返回空结果或降级策略

### 8.2 LLM调用失败
- 设置超时时间
- 重试机制（最多3次）
- 降级到阶段2结果

### 8.3 分数异常
- 检查分数范围（0-1）
- 处理NaN和Inf
- 使用默认分数

## 9. 性能优化

### 9.1 缓存策略
- 缓存热门查询结果（LRU缓存）
- 缓存LLM判断结果
- 设置缓存过期时间

### 9.2 批量处理
- 批量调用LLM（减少网络开销）
- 批量计算向量相似度
- 并行处理多个查询

### 9.3 索引优化
- 预过滤文档（减少检索范围）
- 使用近似最近邻搜索
- 分片索引（大规模场景）

## 10. 测试策略

### 10.1 单元测试
- 测试各阶段检索逻辑
- 测试分数计算
- 测试置信度判断

### 10.2 集成测试
- 测试端到端检索流程
- 测试LLM判断
- 测试过滤器

### 10.3 准确性测试
- 使用人工标注数据集
- 计算Precision、Recall、F1
- 对比不同策略的效果
