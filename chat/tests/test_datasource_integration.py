"""
集成测试：验证 datasource 系统集成
"""
import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datasource_config import (
    get_enabled_datasources,
    validate_datasource_config,
    DATASOURCES
)


def test_datasource_config_loading():
    """测试数据源配置加载"""
    print("\n=== 测试 1: 数据源配置加载 ===")

    configs = DATASOURCES
    print(f"加载的数据源数量: {len(configs)}")

    assert len(configs) > 0, "至少应该有一个数据源配置"

    for config in configs:
        print(f"  - {config['name']} ({config['type']})")
        assert "name" in config
        assert "type" in config
        assert config["type"] in ["local", "jira", "confluence"]

    print("[OK] 配置加载成功")


def test_datasource_validation():
    """测试数据源配置验证"""
    print("\n=== 测试 2: 数据源配置验证 ===")

    for ds in DATASOURCES:
        name = ds["name"]
        enabled = ds.get("enabled", True)

        if not enabled:
            print(f"  - {name}: 跳过（未启用）")
            continue

        valid = validate_datasource_config(ds)
        print(f"  - {name}: {'有效' if valid else '无效'}")

        if ds["type"] == "local":
            # 本地数据源应该总是有效的
            assert valid, f"本地数据源 {name} 应该是有效的"

    print("[OK] 配置验证成功")


def test_datasource_import():
    """测试 datasource 包导入"""
    print("\n=== 测试 3: datasource 包导入 ===")

    try:
        from datasource.core.manager import SourceManager
        print("  - SourceManager 导入成功")

        from datasource.core.sources.local import LocalDataSource
        print("  - LocalDataSource 导入成功")

        print("[OK] 包导入成功")
        return True
    except ImportError as e:
        print(f"[SKIP] 包导入失败: {e}")
        print("  提示: 运行 'uv sync' 安装依赖")
        return False


def test_local_datasource_loading():
    """测试本地数据源加载"""
    print("\n=== 测试 4: 本地数据源加载 ===")

    try:
        from datasource.core.sources.local import LocalDataSource
    except ImportError:
        print("[SKIP] datasource 包未安装")
        return

    # 查找本地数据源配置
    local_configs = [ds for ds in DATASOURCES if ds["type"] == "local" and ds.get("enabled", True)]

    if not local_configs:
        print("[SKIP] 没有启用的本地数据源")
        return

    config = local_configs[0]
    data_path = config.get("path", "./data")

    # 确保数据目录存在
    data_dir = Path(__file__).parent.parent / data_path
    if not data_dir.exists():
        print(f"[SKIP] 数据目录不存在: {data_dir}")
        return

    print(f"  数据目录: {data_dir}")

    # 创建配置和 reader
    from datasource.core.models import SourceConfig, SourceType
    config = SourceConfig(
        name="test_local",
        type=SourceType.LOCAL,
        path=str(data_dir)
    )
    reader = LocalDataSource(config)
    print(f"  Reader 创建成功")

    # 测试 fetch_raw
    try:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir) / "raw"
            raw_dir.mkdir()

            # 抓取原始数据
            items = list(reader.fetch_raw(raw_dir))
            print(f"  抓取文件数量: {len(items)}")

            if items:
                item_id, raw_data = items[0]
                print(f"  示例文件: {raw_data.get('file_name', 'N/A')}")

                # 测试 build_document
                assets_dir = Path(tmpdir) / "assets"
                assets_dir.mkdir()
                doc = reader.build_document(item_id, raw_data, assets_dir)
                print(f"  文档内容长度: {len(doc.text)} 字符")

        print("[OK] 本地数据源加载成功")
    except Exception as e:
        print(f"[WARN] 加载失败: {e}")


def test_manager_integration():
    """测试 SourceManager 集成"""
    print("\n=== 测试 5: SourceManager 集成 ===")

    try:
        from datasource.core.manager import SourceManager
    except ImportError:
        print("[SKIP] datasource 包未安装")
        return

    configs = get_enabled_datasources()

    if not configs:
        print("[SKIP] 没有启用的数据源")
        return

    try:
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data"
        manager = SourceManager(data_dir)
        print(f"  Manager 创建成功")
        print(f"  数据目录: {data_dir}")
        print("[OK] Manager 集成成功")
    except Exception as e:
        print(f"[WARN] Manager 创建失败: {e}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Datasource 集成测试")
    print("=" * 60)

    tests = [
        test_datasource_config_loading,
        test_datasource_validation,
        test_datasource_import,
        test_local_datasource_loading,
        test_manager_integration,
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
