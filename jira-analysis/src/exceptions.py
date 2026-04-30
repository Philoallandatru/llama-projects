"""自定义异常类"""


class JiraAnalysisError(Exception):
    """基础异常类"""
    pass


class IssueLoadError(JiraAnalysisError):
    """Issue 加载失败"""
    pass


class EvidenceRetrievalError(JiraAnalysisError):
    """证据检索失败"""
    pass


class LLMGenerationError(JiraAnalysisError):
    """LLM 生成失败"""
    pass


class ConfigurationError(JiraAnalysisError):
    """配置错误"""
    pass


class IndexNotFoundError(JiraAnalysisError):
    """索引不存在"""
    pass
