"""自定义异常类"""


class JiraAnalysisError(Exception):
    """基础异常类"""
    pass


class IssueLoadError(JiraAnalysisError):
    """Issue 加载失败"""
    pass
