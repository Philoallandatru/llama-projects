"""HTML 内容清理工具"""

import re
from typing import Dict, Optional
from bs4 import BeautifulSoup


class HTMLCleaner:
    """HTML 内容清理器

    使用 BeautifulSoup 彻底清理 HTML 标签，提取纯文本内容。
    """

    @staticmethod
    def clean(
        html: str,
        preserve_links: bool = True,
        preserve_formatting: bool = False
    ) -> str:
        """清理 HTML 标签，提取纯文本

        Args:
            html: HTML 内容
            preserve_links: 是否保留链接文本（格式：text (url)）
            preserve_formatting: 是否保留基本格式（换行、列表等）

        Returns:
            清理后的纯文本

        Examples:
            >>> html = '<p>Hello <a href="http://example.com">World</a></p>'
            >>> HTMLCleaner.clean(html, preserve_links=True)
            'Hello World (http://example.com)'

            >>> HTMLCleaner.clean(html, preserve_links=False)
            'Hello World'
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 移除不需要的标签
            for tag in soup(['script', 'style', 'meta', 'link', 'noscript']):
                tag.decompose()

            # 处理链接
            if preserve_links:
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    text = a.get_text(strip=True)
                    if href and text and href != text:
                        # 替换为 "text (url)" 格式
                        a.replace_with(f"{text} ({href})")
                    elif href and not text:
                        # 只有 URL 没有文本
                        a.replace_with(href)

            # 处理列表（保留格式）
            if preserve_formatting:
                for li in soup.find_all('li'):
                    # 在 li 前添加项目符号，并在后面添加换行
                    li_text = li.get_text(separator=' ', strip=True)
                    li.string = f"• {li_text}"

            # 提取文本
            if preserve_formatting:
                # 为块级元素添加换行
                for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br']):
                    tag.append('\n')
                text = soup.get_text(separator='')
            else:
                text = soup.get_text(separator=' ')

            # 清理多余空白
            text = HTMLCleaner._clean_whitespace(text)

            return text

        except Exception as e:
            # 如果解析失败，回退到简单的正则清理
            return HTMLCleaner._fallback_clean(html)

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """清理多余的空白字符

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        # 替换多个空格为单个空格
        text = re.sub(r' +', ' ', text)

        # 清理每行的首尾空白
        lines = [line.strip() for line in text.split('\n')]

        # 移除空行
        lines = [line for line in lines if line]

        return '\n'.join(lines)

    @staticmethod
    def _fallback_clean(html: str) -> str:
        """回退的简单清理方法（当 BeautifulSoup 失败时）

        Args:
            html: HTML 内容

        Returns:
            清理后的文本
        """
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', html)

        # 解码 HTML 实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')

        # 清理空白
        return HTMLCleaner._clean_whitespace(text)

    @staticmethod
    def extract_metadata(html: str) -> Dict[str, str]:
        """从 HTML 中提取元数据

        Args:
            html: HTML 内容

        Returns:
            元数据字典（title, description, keywords 等）

        Examples:
            >>> html = '<html><head><title>Test</title></head></html>'
            >>> HTMLCleaner.extract_metadata(html)
            {'title': 'Test'}
        """
        if not html:
            return {}

        try:
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

            # 提取 h1 标签（作为备用标题）
            if 'title' not in metadata:
                h1 = soup.find('h1')
                if h1:
                    metadata['title'] = h1.get_text(strip=True)

            return metadata

        except Exception:
            return {}

    @staticmethod
    def extract_links(html: str) -> list[Dict[str, str]]:
        """从 HTML 中提取所有链接

        Args:
            html: HTML 内容

        Returns:
            链接列表，每个链接包含 text 和 href

        Examples:
            >>> html = '<a href="http://example.com">Example</a>'
            >>> HTMLCleaner.extract_links(html)
            [{'text': 'Example', 'href': 'http://example.com'}]
        """
        if not html:
            return []

        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []

            for a in soup.find_all('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if href:
                    links.append({
                        'text': text or href,
                        'href': href
                    })

            return links

        except Exception:
            return []

    @staticmethod
    def has_html_tags(text: str) -> bool:
        """检查文本是否包含 HTML 标签

        Args:
            text: 输入文本

        Returns:
            是否包含 HTML 标签

        Examples:
            >>> HTMLCleaner.has_html_tags('<p>Hello</p>')
            True

            >>> HTMLCleaner.has_html_tags('Hello World')
            False
        """
        if not text:
            return False

        # 简单的 HTML 标签检测
        return bool(re.search(r'<[^>]+>', text))
