#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试FFmpeg配置管理
验证FFmpeg路径检测和配置功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.ffmpeg_utils import FFmpegUtils, ffmpeg_utils
from src.core.clip_generator import ClipGenerator


def test_ffmpeg_utils_initialization():
    """测试FFmpegUtils初始化"""
    print("=" * 60)
    print("测试1: FFmpegUtils初始化")
    print("=" * 60)
    
    utils = FFmpegUtils()
    
    print(f"✓ FFmpeg路径: {utils.get_ffmpeg_path()}")
    print(f"✓ FFprobe路径: {utils.get_ffprobe_path()}")
    print(f"✓ FFmpeg可用: {utils.is_available()}")
    
    if utils.is_available():
        version = utils.get_version()
        print(f"✓ FFmpeg版本: {version}")
    
    assert utils.ffmpeg_path is not None, "FFmpeg路径不应为None"
    assert utils.ffprobe_path is not None, "FFprobe路径不应为None"
    
    print("✓ 测试通过\n")


def test_global_instance():
    """测试全局实例"""
    print("=" * 60)
    print("测试2: 全局FFmpegUtils实例")
    print("=" * 60)
    
    print(f"✓ 全局实例FFmpeg路径: {ffmpeg_utils.get_ffmpeg_path()}")
    print(f"✓ 全局实例可用性: {ffmpeg_utils.is_available()}")
    
    assert ffmpeg_utils.ffmpeg_path is not None
    
    print("✓ 测试通过\n")


def test_clip_generator_integration():
    """测试ClipGenerator集成"""
    print("=" * 60)
    print("测试3: ClipGenerator集成FFmpegUtils")
    print("=" * 60)
    
    generator = ClipGenerator()
    
    print(f"✓ ClipGenerator FFmpeg路径: {generator.ffmpeg_path}")
    print(f"✓ ClipGenerator FFprobe路径: {generator.ffprobe_path}")
    print(f"✓ ClipGenerator FFmpeg可用: {generator.check_ffmpeg_availability()}")
    
    # 验证ClipGenerator使用的是FFmpegUtils提供的路径
    assert generator.ffmpeg_path == ffmpeg_utils.get_ffmpeg_path(), \
        "ClipGenerator应该使用FFmpegUtils提供的路径"
    
    print("✓ 测试通过\n")


def test_no_hardcoded_paths():
    """测试没有硬编码路径"""
    print("=" * 60)
    print("测试4: 验证没有硬编码路径")
    print("=" * 60)
    
    # 读取clip_generator.py源代码
    clip_gen_file = project_root / "src" / "core" / "clip_generator.py"
    with open(clip_gen_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含硬编码的绝对路径
    hardcoded_patterns = [
        r"D:\zancun",
        r"D:\\zancun",
        r"C:\Users",
        r"C:\\Users"
    ]
    
    found_hardcoded = []
    for pattern in hardcoded_patterns:
        if pattern in content:
            found_hardcoded.append(pattern)
    
    if found_hardcoded:
        print(f"✗ 发现硬编码路径: {found_hardcoded}")
        assert False, f"clip_generator.py中仍包含硬编码路径: {found_hardcoded}"
    else:
        print("✓ 未发现硬编码路径")
    
    print("✓ 测试通过\n")


def test_config_file_format():
    """测试配置文件格式"""
    print("=" * 60)
    print("测试5: 验证配置文件格式")
    print("=" * 60)
    
    import json
    
    config_file = project_root / "src" / "utils" / "ffmpeg_config.json"
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✓ 配置文件存在: {config_file}")
        print(f"✓ FFmpeg路径: {config.get('ffmpeg_path')}")
        print(f"✓ FFprobe路径: {config.get('ffprobe_path')}")
        
        # 检查是否使用相对路径
        ffmpeg_path = config.get('ffmpeg_path', '')
        if ffmpeg_path:
            is_relative = not os.path.isabs(ffmpeg_path)
            print(f"✓ 使用相对路径: {is_relative}")
            
            if not is_relative and ('D:\\' in ffmpeg_path or 'C:\\' in ffmpeg_path):
                print(f"⚠ 警告: 配置文件仍使用绝对路径，建议使用相对路径")
    else:
        print(f"⚠ 配置文件不存在: {config_file}")
    
    print("✓ 测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("FFmpeg配置管理测试套件")
    print("=" * 60 + "\n")
    
    try:
        test_ffmpeg_utils_initialization()
        test_global_instance()
        test_clip_generator_integration()
        test_no_hardcoded_paths()
        test_config_file_format()
        
        print("=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试失败: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

