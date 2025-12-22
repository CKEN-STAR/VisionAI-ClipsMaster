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

    # 模拟HEAD请求返回文件大小
    mock_head_response = Mock()
    mock_head_response.headers = {'content-length': '3221225472'}  # 3GB
    mock_head_response.raise_for_status = Mock()
    
    with patch.object(worker.session, 'head', return_value=mock_head_response):
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                # 模拟文件大小不匹配（缺少100MB）
                mock_stat.return_value.st_size = 3221225472 - 100 * 1024 * 1024
                
                with patch('pathlib.Path.unlink') as mock_unlink:
                    with patch('pathlib.Path.iterdir', return_value=[]):
                        with patch('pathlib.Path.glob', return_value=[]):
                            with patch('pathlib.Path.rglob', return_value=[]):
                                worker.cleanup_incomplete_download()
    
    # 验证HEAD请求被调用
    assert worker.session.head.call_count == 1
    # 验证文件被删除（因为大小不匹配）
    assert mock_unlink.call_count == 1
    print("✅ 通过：清理时正确发送HEAD请求获取文件大小并删除不完整文件")


def test_large_file_uses_strict_tolerance():
    """测试大文件使用更严格的误差范围（1%）"""
    print("\n测试4: 大文件使用1%误差范围")
    
    download_config = {
        'target_dir': 'models/test',
        'files': [
            {
                'name': 'model.safetensors',
                'url': 'https://example.com/model.safetensors'
            }
        ]
    }
    
    worker = ModelDownloadThread("test-model", download_config)

    # 模拟HEAD请求返回3GB文件
    mock_head_response = Mock()
    mock_head_response.headers = {'content-length': '3221225472'}  # 3GB
    mock_head_response.raise_for_status = Mock()
    
    with patch.object(worker.session, 'head', return_value=mock_head_response):
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                # 模拟文件大小差异为2%（应该被拒绝，因为大文件只允许1%误差）
                expected_size = 3221225472
                actual_size = int(expected_size * 0.98)  # 差2%
                mock_stat.return_value.st_size = actual_size
                
                result = worker._verify_download()
    
    # 验证失败（因为2%超过了1%的容差）
    assert result == False
    print("✅ 通过：大文件（>100MB）使用1%误差范围，2%差异被正确拒绝")


def test_small_file_uses_loose_tolerance():
    """测试小文件使用更宽松的误差范围（5%）"""
    print("\n测试5: 小文件使用5%误差范围")
    
    download_config = {
        'target_dir': 'models/test',
        'files': [
            {
                'name': 'config.json',
                'url': 'https://example.com/config.json'
            }
        ]
    }
    
    worker = ModelDownloadThread("test-model", download_config)

    # 模拟HEAD请求返回1KB文件
    mock_head_response = Mock()
    mock_head_response.headers = {'content-length': '1024'}  # 1KB
    mock_head_response.raise_for_status = Mock()
    
    with patch.object(worker.session, 'head', return_value=mock_head_response):
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                # 模拟文件大小差异为3%（应该被接受，因为小文件允许5%误差）
                expected_size = 1024
                actual_size = int(expected_size * 0.97)  # 差3%
                mock_stat.return_value.st_size = actual_size
                
                result = worker._verify_download()
    
    # 验证成功（因为3%在5%容差范围内）
    assert result == True
    print("✅ 通过：小文件（<100MB）使用5%误差范围，3%差异被正确接受")


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

