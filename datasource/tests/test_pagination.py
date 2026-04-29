"""测试分页工具"""

import pytest
from datasource.core.utils.pagination import Paginator


class TestPaginatorBasic:
    """测试基本分页功能"""

    def test_paginate_single_page(self):
        """测试单页数据"""
        def fetch_func(start: int, limit: int):
            return {
                "results": [1, 2, 3],
                "size": 3
            }

        results = Paginator.paginate(fetch_func, page_size=10)
        assert results == [1, 2, 3]

    def test_paginate_multiple_pages(self):
        """测试多页数据"""
        data = list(range(25))  # 25 个元素

        def fetch_func(start: int, limit: int):
            end = min(start + limit, len(data))
            batch = data[start:end]
            return {
                "results": batch,
                "size": len(batch)
            }

        results = Paginator.paginate(fetch_func, page_size=10)
        assert results == data
        assert len(results) == 25

    def test_paginate_empty_results(self):
        """测试空结果"""
        def fetch_func(start: int, limit: int):
            return {
                "results": [],
                "size": 0
            }

        results = Paginator.paginate(fetch_func, page_size=10)
        assert results == []

    def test_paginate_with_max_results(self):
        """测试最大结果数限制"""
        data = list(range(100))

        def fetch_func(start: int, limit: int):
            end = min(start + limit, len(data))
            batch = data[start:end]
            return {
                "results": batch,
                "size": len(batch)
            }

        results = Paginator.paginate(fetch_func, page_size=10, max_results=25)
        assert len(results) == 25
        assert results == data[:25]

    def test_paginate_custom_keys(self):
        """测试自定义键名"""
        def fetch_func(start: int, limit: int):
            return {
                "items": [1, 2, 3],
                "count": 3
            }

        results = Paginator.paginate(
            fetch_func,
            page_size=10,
            results_key="items",
            size_key="count"
        )
        assert results == [1, 2, 3]

    def test_paginate_stops_on_partial_page(self):
        """测试在不完整页面时停止"""
        call_count = 0

        def fetch_func(start: int, limit: int):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {"results": list(range(10)), "size": 10}
            else:
                # 第二页只有 5 个元素，应该停止
                return {"results": list(range(5)), "size": 5}

        results = Paginator.paginate(fetch_func, page_size=10)
        assert len(results) == 15
        assert call_count == 2  # 只调用了 2 次


class TestPaginatorWithNextLink:
    """测试基于 next 链接的分页"""

    def test_paginate_with_next_link_single_page(self):
        """测试单页数据"""
        def fetch_func(next_url):
            return {
                "results": [1, 2, 3],
                "next": None
            }

        results = Paginator.paginate_with_next_link(fetch_func)
        assert results == [1, 2, 3]

    def test_paginate_with_next_link_multiple_pages(self):
        """测试多页数据"""
        pages = [
            {"results": [1, 2, 3], "next": "page2"},
            {"results": [4, 5, 6], "next": "page3"},
            {"results": [7, 8, 9], "next": None}
        ]
        current_page = 0

        def fetch_func(next_url):
            nonlocal current_page
            page = pages[current_page]
            current_page += 1
            return page

        results = Paginator.paginate_with_next_link(fetch_func)
        assert results == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_paginate_with_next_link_empty(self):
        """测试空结果"""
        def fetch_func(next_url):
            return {
                "results": [],
                "next": None
            }

        results = Paginator.paginate_with_next_link(fetch_func)
        assert results == []


class TestPaginatorCursorBased:
    """测试基于游标的分页"""

    def test_paginate_cursor_single_page(self):
        """测试单页数据"""
        def fetch_func(cursor, limit):
            return {
                "results": [1, 2, 3],
                "cursor": None,
                "has_more": False
            }

        results = Paginator.paginate_cursor_based(fetch_func, page_size=10)
        assert results == [1, 2, 3]

    def test_paginate_cursor_multiple_pages(self):
        """测试多页数据"""
        pages = [
            {"results": [1, 2, 3], "cursor": "cursor2", "has_more": True},
            {"results": [4, 5, 6], "cursor": "cursor3", "has_more": True},
            {"results": [7, 8, 9], "cursor": None, "has_more": False}
        ]
        current_page = 0

        def fetch_func(cursor, limit):
            nonlocal current_page
            page = pages[current_page]
            current_page += 1
            return page

        results = Paginator.paginate_cursor_based(fetch_func, page_size=10)
        assert results == [1, 2, 3, 4, 5, 6, 7, 8, 9]

    def test_paginate_cursor_with_max_results(self):
        """测试最大结果数限制"""
        def fetch_func(cursor, limit):
            return {
                "results": list(range(10)),
                "cursor": "next_cursor",
                "has_more": True
            }

        results = Paginator.paginate_cursor_based(
            fetch_func,
            page_size=10,
            max_results=15
        )
        assert len(results) == 15

    def test_paginate_cursor_empty(self):
        """测试空结果"""
        def fetch_func(cursor, limit):
            return {
                "results": [],
                "cursor": None,
                "has_more": False
            }

        results = Paginator.paginate_cursor_based(fetch_func, page_size=10)
        assert results == []


class TestPaginatorErrorHandling:
    """测试错误处理"""

    def test_paginate_handles_exception(self):
        """测试处理异常"""
        call_count = 0

        def fetch_func(start: int, limit: int):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {"results": [1, 2, 3], "size": 3}
            else:
                raise Exception("Network error")

        results = Paginator.paginate(fetch_func, page_size=10)
        # 应该返回第一页的结果，然后停止
        assert results == [1, 2, 3]

    def test_paginate_with_next_link_handles_exception(self):
        """测试 next link 分页处理异常"""
        call_count = 0

        def fetch_func(next_url):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {"results": [1, 2, 3], "next": "page2"}
            else:
                raise Exception("Network error")

        results = Paginator.paginate_with_next_link(fetch_func)
        assert results == [1, 2, 3]

    def test_paginate_cursor_handles_exception(self):
        """测试游标分页处理异常"""
        call_count = 0

        def fetch_func(cursor, limit):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                return {"results": [1, 2, 3], "cursor": "cursor2", "has_more": True}
            else:
                raise Exception("Network error")

        results = Paginator.paginate_cursor_based(fetch_func, page_size=10)
        assert results == [1, 2, 3]
