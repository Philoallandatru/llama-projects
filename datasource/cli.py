"""命令行接口

提供数据源管理的命令行工具。
"""

import click
import logging
from pathlib import Path
from typing import Optional

from .core.manager import SourceManager
from .core.models import SourceConfig, SourceType


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
@click.option('--data-dir', type=click.Path(), default='data', help='数据目录路径')
@click.pass_context
def cli(ctx, data_dir):
    """数据源管理工具

    支持本地文件、Jira、Confluence 等多种数据源。
    """
    ctx.ensure_object(dict)
    ctx.obj['manager'] = SourceManager(Path(data_dir))


@cli.command()
@click.argument('name')
@click.option('--type', 'source_type', type=click.Choice(['local', 'jira', 'confluence']), required=True, help='数据源类型')
@click.option('--path', type=str, help='本地路径（local 类型必需）')
@click.option('--server', type=str, help='服务器地址（jira/confluence 类型必需）')
@click.option('--username', type=str, help='用户名')
@click.option('--password', type=str, help='密码或 API Token')
@click.option('--description', type=str, help='数据源描述')
@click.pass_context
def add(ctx, name: str, source_type: str, path: Optional[str], server: Optional[str],
        username: Optional[str], password: Optional[str], description: Optional[str]):
    """添加数据源

    示例：

    \b
    # 添加本地文件数据源
    datasource add my_docs --type local --path /path/to/docs

    \b
    # 添加 Jira 数据源
    datasource add my_jira --type jira --server https://jira.example.com --username user --password token
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        # 验证参数
        if source_type == 'local' and not path:
            raise click.UsageError("本地文件数据源必须指定 --path")

        if source_type in ['jira', 'confluence'] and not server:
            raise click.UsageError(f"{source_type} 数据源必须指定 --server")

        # 构建配置
        credentials = None
        if username and password:
            credentials = {
                'username': username,
                'password': password
            }

        config = SourceConfig(
            name=name,
            type=SourceType(source_type.upper()),
            path=path,
            server=server,
            credentials=credentials,
            description=description
        )

        # 添加数据源
        info = manager.add_source(config)

        click.echo(f"✓ 数据源 '{name}' 添加成功")
        click.echo(f"  类型: {info.type.value}")
        if path:
            click.echo(f"  路径: {path}")
        if server:
            click.echo(f"  服务器: {server}")

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
@click.pass_context
def sync(ctx, name: str):
    """同步数据源

    从数据源抓取数据并构建文档。
    """
    manager: SourceManager = ctx.obj['manager']

    try:
        click.echo(f"开始同步数据源 '{name}'...")

        result = manager.sync_source(name)

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


if __name__ == '__main__':
    cli()
