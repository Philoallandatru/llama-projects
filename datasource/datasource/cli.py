"""命令行接口

提供数据源管理的命令行工具。
"""

import click
import logging
import os
from pathlib import Path
from typing import Optional

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding

from .core.manager import SourceManager
from .core.models import SourceConfig, SourceType


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def init_llm_settings():
    """初始化 LLM 设置"""
    # 从环境变量读取配置
    api_key = os.getenv("OPENAI_API_KEY", "lm-studio")
    api_base = os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1234/v1")

    # 配置 embedding 模型
    # 使用 text-embedding-3-small 作为模型名称，实际会被 LM Studio 重定向到加载的模型
    Settings.embed_model = OpenAIEmbedding(
        api_key=api_key,
        api_base=api_base,
        model="text-embedding-3-small"
    )


@click.group()
@click.option('--data-dir', type=click.Path(), default='data', help='数据目录路径')
@click.pass_context
def cli(ctx, data_dir):
    """数据源管理工具

    支持本地文件、Jira、Confluence 等多种数据源。
    """
    # 初始化 LLM 设置
    init_llm_settings()

    ctx.ensure_object(dict)
    ctx.obj['manager'] = SourceManager(Path(data_dir))


@cli.command()
@click.argument('name')
@click.option('--type', 'source_type', type=click.Choice(['local', 'jira', 'confluence']), required=True, help='数据源类型')
@click.option('--path', type=str, help='本地路径（local 类型必需）')
@click.option('--server', type=str, help='服务器地址（jira/confluence 类型必需）')
@click.option('--email', type=str, help='用户邮箱（jira/confluence 认证）')
@click.option('--token', type=str, help='API Token（jira/confluence 认证）')
@click.option('--project', type=str, help='项目 key（jira）')
@click.option('--jql', type=str, help='JQL 查询语句（jira）')
@click.option('--space', type=str, help='Space key（confluence）')
@click.option('--description', type=str, help='数据源描述')
@click.pass_context
def add(ctx, name: str, source_type: str, path: Optional[str], server: Optional[str],
        email: Optional[str], token: Optional[str], project: Optional[str],
        jql: Optional[str], space: Optional[str], description: Optional[str]):
    """添加数据源

    示例：

    \b
    # 添加本地文件数据源
    datasource add my_docs --type local --path /path/to/docs

    \b
    # 添加 Jira 数据源
    datasource add my_jira --type jira --server https://jira.example.com --email user@example.com --token YOUR_TOKEN --project PROJ

    \b
    # 添加 Confluence 数据源
    datasource add my_confluence --type confluence --server https://confluence.example.com --email user@example.com --token YOUR_TOKEN --space SPACE
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        # 验证参数
        if source_type == 'local' and not path:
            raise click.UsageError("本地文件数据源必须指定 --path")

        if source_type in ['jira', 'confluence']:
            if not server:
                raise click.UsageError(f"{source_type} 数据源必须指定 --server")
            if not email or not token:
                raise click.UsageError(f"{source_type} 数据源必须指定 --email 和 --token")

        # 构建配置
        options = {}
        if email:
            options['email'] = email
        if token:
            options['token'] = token

        config = SourceConfig(
            name=name,
            type=SourceType(source_type),
            path=path,
            server=server,
            project=project,
            jql=jql,
            space=space,
            description=description,
            options=options
        )

        # 添加数据源
        info = manager.add_source(config)

        click.echo(f"✓ 数据源 '{name}' 添加成功")
        click.echo(f"  类型: {info.type.value}")
        if path:
            click.echo(f"  路径: {path}")
        if server:
            click.echo(f"  服务器: {server}")
        if project:
            click.echo(f"  项目: {project}")

    except Exception as e:
        click.echo(f"✗ 添加失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.pass_context
def list(ctx):
    """列出所有数据源

    显示数据源的基本信息和统计数据。
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        sources = manager.list_sources()

        if not sources:
            click.echo("没有数据源")
            return

        click.echo(f"\n共 {len(sources)} 个数据源:\n")

        for info in sources:
            click.echo(f"📁 {info.name}")
            click.echo(f"   类型: {info.type.value}")
            if info.config.path:
                click.echo(f"   路径: {info.config.path}")
            if info.config.server:
                click.echo(f"   服务器: {info.config.server}")
            click.echo(f"   状态: {info.status}")
            click.echo(f"   原始数据: {info.raw_count} 条")
            click.echo(f"   文档: {info.document_count} 个")
            click.echo(f"   大小: {info.total_size:.2f} MB")
            if info.last_sync:
                click.echo(f"   最后同步: {info.last_sync}")
            click.echo()

    except Exception as e:
        click.echo(f"✗ 列表失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('name')
@click.pass_context
def show(ctx, name: str):
    """显示数据源详情

    显示指定数据源的完整信息。
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        info = manager.get_source_info(name)

        click.echo(f"\n数据源: {info.name}\n")
        click.echo(f"类型: {info.type.value}")

        if info.config.path:
            click.echo(f"路径: {info.config.path}")
        if info.config.server:
            click.echo(f"服务器: {info.config.server}")
        if info.config.description:
            click.echo(f"描述: {info.config.description}")

        click.echo(f"\n统计信息:")
        click.echo(f"  原始数据: {info.raw_count} 条")
        click.echo(f"  文档: {info.document_count} 个")
        click.echo(f"  总大小: {info.total_size:.2f} MB")

        click.echo(f"\n状态:")
        click.echo(f"  当前状态: {info.status}")
        if info.last_sync:
            click.echo(f"  最后同步: {info.last_sync}")
        else:
            click.echo(f"  最后同步: 从未同步")

    except Exception as e:
        click.echo(f"✗ 查询失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('name')
@click.option('--yes', '-y', is_flag=True, help='跳过确认')
@click.pass_context
def delete(ctx, name: str, yes: bool):
    """删除数据源

    删除数据源及其所有数据（不可恢复）。
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        # 确认删除
        if not yes:
            if not click.confirm(f"确定要删除数据源 '{name}' 吗？此操作不可恢复。"):
                click.echo("已取消")
                return

        manager.delete_source(name)
        click.echo(f"✓ 数据源 '{name}' 已删除")

    except Exception as e:
        click.echo(f"✗ 删除失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('name')
@click.option('--full', is_flag=True, help='强制全量同步（默认使用增量同步）')
@click.pass_context
def sync(ctx, name: str, full: bool):
    """同步数据源

    从数据源抓取数据并构建索引。

    默认使用增量同步（只抓取上次同步后更新的数据）。
    使用 --full 参数强制全量同步。

    示例：
        datasource sync my_source          # 增量同步
        datasource sync my_source --full   # 全量同步
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        sync_mode = "全量" if full else "增量"
        click.echo(f"开始{sync_mode}同步数据源 '{name}'...")

        result = manager.sync_source(name, full=full)

        click.echo(f"\n同步完成:")
        click.echo(f"  原始数据: {result.raw_count} 条")
        click.echo(f"  文档: {result.document_count} 个")

        if result.error_count > 0:
            click.echo(f"  错误: {result.error_count} 个", err=True)
            if result.errors:
                click.echo(f"\n错误详情:")
                for error in result.errors[:5]:  # 只显示前5个
                    click.echo(f"  - {error}", err=True)
                if len(result.errors) > 5:
                    click.echo(f"  ... 还有 {len(result.errors) - 5} 个错误", err=True)

        if result.success:
            click.echo(f"\n✓ 同步成功")
        else:
            click.echo(f"\n⚠ 同步完成，但有错误", err=True)

    except Exception as e:
        click.echo(f"✗ 同步失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('name')
@click.argument('query')
@click.option('--mode', type=click.Choice(['hybrid', 'vector', 'bm25']), default='hybrid', help='检索模式')
@click.option('--top-k', type=int, default=5, help='返回结果数量')
@click.pass_context
def query(ctx, name: str, query: str, mode: str, top_k: int):
    """查询数据源

    使用混合检索（向量 + BM25）查询数据源。

    示例：

    \b
    # 混合检索
    datasource query my_docs "如何使用 Python"

    \b
    # 仅向量检索
    datasource query my_docs "如何使用 Python" --mode vector

    \b
    # 返回更多结果
    datasource query my_docs "如何使用 Python" --top-k 10
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        click.echo(f"正在查询数据源 '{name}'...")
        click.echo(f"查询: {query}")
        click.echo(f"模式: {mode}")
        click.echo()

        results = manager.query(name, query, mode=mode, top_k=top_k)

        if not results:
            click.echo("没有找到相关结果")
            return

        click.echo(f"找到 {len(results)} 个结果:\n")

        for result in results:
            click.echo(f"#{result['rank']} (分数: {result['score']})")
            click.echo(f"  {result['text']}")

            # 显示元数据
            metadata = result['metadata']
            if 'source_name' in metadata:
                click.echo(f"  来源: {metadata['source_name']}")
            if 'item_id' in metadata:
                click.echo(f"  ID: {metadata['item_id']}")

            click.echo()

    except Exception as e:
        click.echo(f"✗ 查询失败: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
