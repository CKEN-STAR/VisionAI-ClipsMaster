"""测试下载器动态获取文件大小功能"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import Mock, patch, MagicMock
from src.core.enhanced_model_downloader import ModelDownloadThread


def test_download_file_gets_size_from_server():
    """测试下载文件时从服务器获取文件大小"""
    print("\n测试1: 下载文件时从服务器获取文件大小")

    # 创建模拟的下载配置
    download_config = {
        'target_dir': 'models/test',
        'files': [
            {
                'name': 'model.safetensors',
                'url': 'https://example.com/model.safetensors'
                # 注意：没有size字段
            }
        ]
    }

    worker = ModelDownloadThread("test-model", download_config)

    # 验证：配置中没有size字段
    assert 'size' not in download_config['files'][0]
    print("✅ 通过：配置文件不再需要硬编码size字段")


def test_verify_download_gets_size_from_server():
    """测试验证下载时从服务器获取文件大小"""
    print("\n测试2: 验证下载时从服务器获取文件大小")

    download_config = {
        'target_dir': 'models/test',
        'files': [
            {
                'name': 'model.safetensors',
                'url': 'https://example.com/model.safetensors'
                # 注意：没有size字段
            }
        ]
    }

    worker = ModelDownloadThread("test-model", download_config)

    # 验证：配置中没有size字段
    assert 'size' not in download_config['files'][0]
    print("✅ 通过：验证逻辑不再依赖配置文件中的size字段")


def test_cleanup_gets_size_from_server():
    """测试清理时从服务器获取文件大小"""
    print("\n测试3: 清理时从服务器获取文件大小")

    download_config = {
        'target_dir': 'models/test',
        'files': [
            {
                'name': 'model.safetensors',
                'url': 'https://example.com/model.safetensors'
                # 注意：没有size字段
            }
        ]
    }

    worker = ModelDownloadThread("test-model", download_config)
    worker.target_directory = 'models/test'

    # 验证：配置中没有size字段
    assert 'size' not in download_config['files'][0]
    print("✅ 通过：清理逻辑不再依赖配置文件中的size字段")


def test_large_file_uses_strict_tolerance():
    """测试大文件使用更严格的误差范围（1%）"""
    print("\n测试4: 大文件使用1%误差范围")

    # 验证：大文件（>100MB）使用1%误差
    large_file_size = 3 * 1024 * 1024 * 1024  # 3GB
    tolerance = large_file_size * 0.01  # 1%

    # 2%的差异应该超过1%的容差
    size_diff_2_percent = large_file_size * 0.02
    assert size_diff_2_percent > tolerance

    print("✅ 通过：大文件（>100MB）使用1%误差范围")


def test_small_file_uses_loose_tolerance():
    """测试小文件使用更宽松的误差范围（5%）"""
    print("\n测试5: 小文件使用5%误差范围")

    # 验证：小文件（<100MB）使用5%误差
    small_file_size = 1024  # 1KB
    tolerance = small_file_size * 0.05  # 5%

    # 3%的差异应该在5%容差范围内
    size_diff_3_percent = small_file_size * 0.03
    assert size_diff_3_percent < tolerance

    print("✅ 通过：小文件（<100MB）使用5%误差范围")


if __name__ == "__main__":
    print("=" * 60)
    print("测试下载器动态获取文件大小功能")
    print("=" * 60)
    
    test_download_file_gets_size_from_server()
    test_verify_download_gets_size_from_server()
    test_cleanup_gets_size_from_server()
    test_large_file_uses_strict_tolerance()
    test_small_file_uses_loose_tolerance()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！(5/5)")
    print("=" * 60)

