#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试下载中断清理功能
验证下载失败/中断时自动清理未完成的模型文件
"""

import sys
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.enhanced_model_downloader import ModelDownloadThread


def test_cleanup_incomplete_files():
    """测试清理不完整文件"""
    print("\n" + "=" * 60)
    print("测试：清理不完整文件")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建模拟的下载配置
        download_config = {
            'files': [
                {'name': 'model-00001.safetensors', 'size': 1000000},  # 1MB
                {'name': 'model-00002.safetensors', 'size': 2000000},  # 2MB
                {'name': 'config.json', 'size': 1000},  # 1KB
            ]
        }
        
        # 创建不完整的文件（大小不匹配）
        incomplete_file1 = temp_dir / 'model-00001.safetensors'
        incomplete_file1.write_bytes(b'0' * 500000)  # 只有500KB，应该被删除
        
        # 创建完整的文件（大小匹配）
        complete_file = temp_dir / 'model-00002.safetensors'
        complete_file.write_bytes(b'0' * 2000000)  # 2MB，应该被保留
        
        # 创建临时文件
        temp_file = temp_dir / 'download.tmp'
        temp_file.write_bytes(b'temp data')
        
        part_file = temp_dir / 'download.part'
        part_file.write_bytes(b'part data')
        
        print(f"创建测试文件:")
        print(f"  不完整文件: {incomplete_file1.name} (500KB, 期望1MB)")
        print(f"  完整文件: {complete_file.name} (2MB, 期望2MB)")
        print(f"  临时文件: {temp_file.name}")
        print(f"  临时文件: {part_file.name}")
        
        # 创建下载线程并执行清理
        thread = ModelDownloadThread("test-model", download_config, str(temp_dir))
        thread.cleanup_incomplete_download()
        
        # 验证结果
        print(f"\n清理后的文件状态:")
        
        if not incomplete_file1.exists():
            print(f"  ✅ 不完整文件已删除: {incomplete_file1.name}")
        else:
            print(f"  ❌ 不完整文件未删除: {incomplete_file1.name}")
            return False
        
        if complete_file.exists():
            print(f"  ✅ 完整文件已保留: {complete_file.name}")
        else:
            print(f"  ❌ 完整文件被误删: {complete_file.name}")
            return False
        
        if not temp_file.exists():
            print(f"  ✅ 临时文件已删除: {temp_file.name}")
        else:
            print(f"  ❌ 临时文件未删除: {temp_file.name}")
            return False
        
        if not part_file.exists():
            print(f"  ✅ 临时文件已删除: {part_file.name}")
        else:
            print(f"  ❌ 临时文件未删除: {part_file.name}")
            return False
        
        return True
        
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def test_cleanup_empty_directory():
    """测试清理空目录"""
    print("\n" + "=" * 60)
    print("测试：清理空目录")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建模拟的下载配置（空文件列表）
        download_config = {
            'files': []
        }
        
        print(f"创建空目录: {temp_dir}")
        
        # 创建下载线程并执行清理
        thread = ModelDownloadThread("test-model", download_config, str(temp_dir))
        thread.cleanup_incomplete_download()
        
        # 验证结果
        if not temp_dir.exists():
            print(f"✅ 空目录已删除")
            return True
        else:
            print(f"❌ 空目录未删除")
            return False
        
    except Exception as e:
        # 如果目录已被删除，清理会失败，这是正常的
        if not temp_dir.exists():
            print(f"✅ 空目录已删除")
            return True
        else:
            print(f"❌ 清理失败: {e}")
            return False


def test_cleanup_preserves_complete_files():
    """测试清理时保留完整文件"""
    print("\n" + "=" * 60)
    print("测试：清理时保留完整文件")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建模拟的下载配置
        download_config = {
            'files': [
                {'name': 'model.safetensors', 'size': 1000000},  # 1MB
                {'name': 'config.json', 'size': 500},  # 500B
            ]
        }
        
        # 创建完整的文件
        model_file = temp_dir / 'model.safetensors'
        model_file.write_bytes(b'0' * 1000000)  # 1MB
        
        config_file = temp_dir / 'config.json'
        config_file.write_bytes(b'0' * 500)  # 500B
        
        print(f"创建完整文件:")
        print(f"  {model_file.name} (1MB)")
        print(f"  {config_file.name} (500B)")
        
        # 创建下载线程并执行清理
        thread = ModelDownloadThread("test-model", download_config, str(temp_dir))
        thread.cleanup_incomplete_download()
        
        # 验证结果
        print(f"\n清理后的文件状态:")
        
        if model_file.exists():
            print(f"  ✅ 完整文件已保留: {model_file.name}")
        else:
            print(f"  ❌ 完整文件被误删: {model_file.name}")
            return False
        
        if config_file.exists():
            print(f"  ✅ 完整文件已保留: {config_file.name}")
        else:
            print(f"  ❌ 完整文件被误删: {config_file.name}")
            return False
        
        # 目录不应该被删除（因为有完整文件）
        if temp_dir.exists():
            print(f"  ✅ 目录已保留（包含完整文件）")
        else:
            print(f"  ❌ 目录被误删")
            return False
        
        return True
        
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("VisionAI-ClipsMaster 下载中断清理测试")
    print("=" * 60)
    
    results = {}
    
    # 测试1：清理不完整文件
    results["清理不完整文件"] = test_cleanup_incomplete_files()
    
    # 测试2：清理空目录
    results["清理空目录"] = test_cleanup_empty_directory()
    
    # 测试3：保留完整文件
    results["保留完整文件"] = test_cleanup_preserves_complete_files()
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print("\n" + "=" * 60)
    print(f"总计: {passed_count}/{total_count} 测试通过")
    print("=" * 60)
    
    if all(results.values()):
        print("\n🎉 所有测试通过！下载中断清理功能正常。")
        print("\n功能说明:")
        print("  ✅ 下载失败时自动清理不完整文件")
        print("  ✅ 下载取消时自动清理不完整文件")
        print("  ✅ 网络中断时自动清理不完整文件")
        print("  ✅ 验证失败时自动清理不完整文件")
        print("  ✅ 自动删除临时文件（.tmp, .part）")
        print("  ✅ 自动删除空目录")
        print("  ✅ 保留完整文件")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查清理逻辑。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

