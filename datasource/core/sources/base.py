"""数据源基类

本模块定义了所有数据源实现必须遵循的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Iterator, Tuple, Dict, Any, Optional
from pathlib import Path
from llama_index.core import Document


class BaseDataSource(ABC):
    """数据源基类

    所有数据源实现（Jira、Confluence、Local）都必须继承此类。

    职责分离：
    - fetch_raw(): 抓取原始数据并保存为 JSON
    - build_document(): 将原始数据转换为 LlamaIndex Document

    这种设计的优点：
    1. 可追溯性：保留原始数据用于调试和审计
    2. 可重新处理：修改 build_document 逻辑后可重新处理已有数据
    3. 增量更新：对比新旧原始数据，只处理变化的部分
    """

    def __init__(self, config: "SourceConfig"):
        """初始化数据源

        Args:
            config: 数据源配置
        """
        self.config = config

    @abstractmethod
    def fetch_raw(
        self,
        output_dir: Path
    ) -> Iterator[Tuple[str, Dict[str, Any]]]:
        """抓取原始数据并保存

        实现要求：
        1. 从数据源抓取原始数据（API 调用、文件扫描等）
        2. 将每个条目保存为 JSON 文件：output_dir / f"{item_id}.json"
        3. yield (item_id, raw_data) 供后续处理

        Args:
            output_dir: 原始数据保存目录

        Yields:
            (item_id, raw_data) 元组
            - item_id: 条目唯一标识（如 "SSD-1234" 或 "doc1.pdf"）
            - raw_data: 原始数据字典

        示例：
            >>> for item_id, raw_data in source.fetch_raw(output_dir):
            ...     print(f"Fetched {item_id}")
            ...     # raw_data 已自动保存到 output_dir/{item_id}.json
        """
        pass

    @abstractmethod
    def build_document(
        self,
        item_id: str,
        raw_data: Dict[str, Any],
        assets_dir: Path
    ) -> Document:
        """将原始数据转换为 LlamaIndex Document

        实现要求：
        1. 从 raw_data 中提取文本内容
        2. 构建 Markdown 格式的文档文本
        3. 下载附件到 assets_dir（如果有）
        4. 设置 metadata（至少包含 source_name, source_type, item_id）

        Args:
            item_id: 条目唯一标识
            raw_data: 原始数据字典
            assets_dir: 附件保存目录

        Returns:
            LlamaIndex Document 实例

        示例：
            >>> doc = source.build_document("SSD-1234", raw_data, assets_dir)
            >>> print(doc.text)  # Markdown 格式的文本
            >>> print(doc.metadata)  # 包含 source_name, item_id 等
        """
        pass

    # ============ 通用工具方法 ============

    def _download_attachment(
        self,
        url: str,
        output_path: Path,
        max_size: Optional[int] = None,
        timeout: int = 30
    ) -> Optional[Path]:
        """下载附件（通用实现）

        提供了重试、超时、大小限制等功能。

        Args:
            url: 附件 URL
            output_path: 保存路径
            max_size: 最大文件大小（字节），None 表示不限制
            timeout: 超时时间（秒）

        Returns:
            保存路径（成功）或 None（失败）
        """
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        try:
            # 配置重试策略
            session = requests.Session()
            retry = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET"]
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # 流式下载
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            # 检查文件大小
            content_length = response.headers.get("Content-Length")
            if max_size and content_length:
                if int(content_length) > max_size:
                    print(f"Skipping {url}: file too large ({content_length} bytes)")
                    return None

            # 保存文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # 检查已下载大小
                        if max_size and downloaded > max_size:
                            print(f"Skipping {url}: file too large (>{max_size} bytes)")
                            output_path.unlink()  # 删除部分下载的文件
                            return None

            return output_path

        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error downloading {url}: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        import re
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        return filename

    def _format_markdown_text(
        self,
        title: str,
        fields: Dict[str, Any],
        sections: Optional[Dict[str, str]] = None
    ) -> str:
        """格式化为 Markdown 文本（通用模板）

        Args:
            title: 文档标题
            fields: 字段字典（key: 字段名, value: 字段值）
            sections: 章节字典（key: 章节标题, value: 章节内容）

        Returns:
            Markdown 格式的文本
        """
        lines = [f"# {title}", ""]

        # 添加字段
        for key, value in fields.items():
            if value:
                lines.append(f"**{key}**: {value}")
        lines.append("")

        # 添加章节
        if sections:
            for section_title, section_content in sections.items():
                if section_content:
                    lines.append(f"## {section_title}")
                    lines.append("")
                    lines.append(section_content)
                    lines.append("")

        return "\n".join(lines)
