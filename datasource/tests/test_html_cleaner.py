"""测试 HTML 清理工具"""

import pytest
from datasource.core.utils.html_cleaner import HTMLCleaner


class TestHTMLCleanerBasic:
    """测试基本 HTML 清理功能"""

    def test_clean_simple_html(self):
        """测试清理简单 HTML"""
        html = "<p>Hello World</p>"
        result = HTMLCleaner.clean(html)
        assert result == "Hello World"

    def test_clean_nested_html(self):
        """测试清理嵌套 HTML"""
        html = "<div><p>Hello <strong>World</strong></p></div>"
        result = HTMLCleaner.clean(html)
        assert result == "Hello World"

    def test_clean_with_links_preserved(self):
        """测试保留链接"""
        html = '<p>Visit <a href="http://example.com">Example</a></p>'
        result = HTMLCleaner.clean(html, preserve_links=True)
        assert "Example (http://example.com)" in result

    def test_clean_with_links_not_preserved(self):
        """测试不保留链接"""
        html = '<p>Visit <a href="http://example.com">Example</a></p>'
        result = HTMLCleaner.clean(html, preserve_links=False)
        assert result == "Visit Example"
        assert "http://example.com" not in result

    def test_clean_empty_string(self):
        """测试空字符串"""
        result = HTMLCleaner.clean("")
        assert result == ""

    def test_clean_none(self):
        """测试 None"""
        result = HTMLCleaner.clean(None)
        assert result == ""

    def test_clean_removes_script_tags(self):
        """测试移除 script 标签"""
        html = "<p>Hello</p><script>alert('xss')</script>"
        result = HTMLCleaner.clean(html)
        assert result == "Hello"
        assert "alert" not in result

    def test_clean_removes_style_tags(self):
        """测试移除 style 标签"""
        html = "<p>Hello</p><style>.test { color: red; }</style>"
        result = HTMLCleaner.clean(html)
        assert result == "Hello"
        assert "color" not in result


class TestHTMLCleanerFormatting:
    """测试格式保留功能"""

    def test_clean_with_formatting(self):
        """测试保留格式"""
        html = "<p>Line 1</p><p>Line 2</p>"
        result = HTMLCleaner.clean(html, preserve_formatting=True)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "\n" in result

    def test_clean_list_with_formatting(self):
        """测试列表格式"""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = HTMLCleaner.clean(html, preserve_formatting=True)
        assert "• Item 1" in result
        assert "• Item 2" in result

    def test_clean_whitespace(self):
        """测试清理多余空白"""
        html = "<p>Hello    World</p>"
        result = HTMLCleaner.clean(html)
        assert result == "Hello World"

    def test_clean_multiple_newlines(self):
        """测试清理多余换行"""
        html = "<p>Line 1</p>\n\n\n<p>Line 2</p>"
        result = HTMLCleaner.clean(html, preserve_formatting=True)
        lines = result.split('\n')
        # 应该只有两行，没有空行
        assert len([l for l in lines if l.strip()]) == 2


class TestHTMLCleanerMetadata:
    """测试元数据提取"""

    def test_extract_title(self):
        """测试提取标题"""
        html = "<html><head><title>Test Title</title></head></html>"
        metadata = HTMLCleaner.extract_metadata(html)
        assert metadata['title'] == "Test Title"

    def test_extract_meta_tags(self):
        """测试提取 meta 标签"""
        html = '''
        <html>
        <head>
            <meta name="description" content="Test Description">
            <meta name="keywords" content="test, html">
        </head>
        </html>
        '''
        metadata = HTMLCleaner.extract_metadata(html)
        assert metadata['description'] == "Test Description"
        assert metadata['keywords'] == "test, html"

    def test_extract_h1_as_title(self):
        """测试使用 h1 作为备用标题"""
        html = "<html><body><h1>Main Title</h1></body></html>"
        metadata = HTMLCleaner.extract_metadata(html)
        assert metadata['title'] == "Main Title"

    def test_extract_empty_html(self):
        """测试空 HTML"""
        metadata = HTMLCleaner.extract_metadata("")
        assert metadata == {}


class TestHTMLCleanerLinks:
    """测试链接提取"""

    def test_extract_links(self):
        """测试提取链接"""
        html = '<a href="http://example.com">Example</a>'
        links = HTMLCleaner.extract_links(html)
        assert len(links) == 1
        assert links[0]['text'] == "Example"
        assert links[0]['href'] == "http://example.com"

    def test_extract_multiple_links(self):
        """测试提取多个链接"""
        html = '''
        <a href="http://example1.com">Link 1</a>
        <a href="http://example2.com">Link 2</a>
        '''
        links = HTMLCleaner.extract_links(html)
        assert len(links) == 2

    def test_extract_link_without_text(self):
        """测试提取无文本的链接"""
        html = '<a href="http://example.com"></a>'
        links = HTMLCleaner.extract_links(html)
        assert len(links) == 1
        assert links[0]['text'] == "http://example.com"

    def test_extract_empty_html(self):
        """测试空 HTML"""
        links = HTMLCleaner.extract_links("")
        assert links == []


class TestHTMLCleanerUtilities:
    """测试工具方法"""

    def test_has_html_tags_true(self):
        """测试检测 HTML 标签（有）"""
        assert HTMLCleaner.has_html_tags("<p>Hello</p>") is True
        assert HTMLCleaner.has_html_tags("<div>Test</div>") is True

    def test_has_html_tags_false(self):
        """测试检测 HTML 标签（无）"""
        assert HTMLCleaner.has_html_tags("Hello World") is False
        assert HTMLCleaner.has_html_tags("") is False

    def test_has_html_tags_none(self):
        """测试检测 HTML 标签（None）"""
        assert HTMLCleaner.has_html_tags(None) is False


class TestHTMLCleanerFallback:
    """测试回退清理方法"""

    def test_fallback_clean_basic(self):
        """测试回退清理基本功能"""
        html = "<p>Hello &nbsp; World</p>"
        result = HTMLCleaner._fallback_clean(html)
        assert "Hello" in result
        assert "World" in result
        assert "<p>" not in result

    def test_fallback_clean_entities(self):
        """测试回退清理 HTML 实体"""
        html = "&lt;div&gt; &amp; &quot;test&quot;"
        result = HTMLCleaner._fallback_clean(html)
        assert "<div>" in result
        assert "&" in result
        assert '"test"' in result


class TestHTMLCleanerRealWorld:
    """测试真实场景"""

    def test_confluence_page_body(self):
        """测试 Confluence 页面内容"""
        html = '''
        <div class="wiki-content">
            <h1>Project Overview</h1>
            <p>This is a <strong>test</strong> project.</p>
            <ul>
                <li>Feature 1</li>
                <li>Feature 2</li>
            </ul>
            <p>Visit <a href="https://docs.example.com">documentation</a> for more info.</p>
        </div>
        '''
        result = HTMLCleaner.clean(html, preserve_links=True, preserve_formatting=True)

        assert "Project Overview" in result
        assert "test project" in result
        assert "• Feature 1" in result
        assert "• Feature 2" in result
        assert "documentation (https://docs.example.com)" in result

    def test_jira_issue_description(self):
        """测试 Jira Issue 描述"""
        html = '''
        <p>Bug found in <a href="/browse/PROJ-123">PROJ-123</a></p>
        <p>Steps to reproduce:</p>
        <ol>
            <li>Step 1</li>
            <li>Step 2</li>
        </ol>
        <p>Expected: <code>result</code></p>
        '''
        result = HTMLCleaner.clean(html, preserve_links=True, preserve_formatting=True)

        assert "Bug found in" in result
        assert "PROJ-123" in result
        assert "Steps to reproduce" in result
        assert "Step 1" in result
        assert "Step 2" in result
        assert "Expected: result" in result

    def test_complex_nested_structure(self):
        """测试复杂嵌套结构"""
        html = '''
        <div class="content">
            <div class="section">
                <h2>Section 1</h2>
                <div class="subsection">
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                </div>
            </div>
            <div class="section">
                <h2>Section 2</h2>
                <p>Content</p>
            </div>
        </div>
        '''
        result = HTMLCleaner.clean(html, preserve_formatting=True)

        assert "Section 1" in result
        assert "Paragraph 1" in result
        assert "Paragraph 2" in result
        assert "Section 2" in result
        assert "Content" in result
