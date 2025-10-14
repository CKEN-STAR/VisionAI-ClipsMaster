#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测系统中的FFmpeg安装位置并配置项目
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

def find_ffmpeg_locations():
    """查找所有可能的FFmpeg位置"""
    locations = []
    
    # 1. 检查系统PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        locations.append({
            'type': 'system_path',
            'ffmpeg': ffmpeg_path,
            'ffprobe': shutil.which('ffprobe') or ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
        })
    
    # 2. 检查常见安装位置
    common_paths = [
        "C:/ffmpeg/bin",
        "C:/Program Files/ffmpeg/bin",
        "C:/Program Files (x86)/ffmpeg/bin",
        "D:/ffmpeg/bin",
        "E:/ffmpeg/bin",
        os.path.expanduser("~/ffmpeg/bin"),
        os.path.expanduser("~/AppData/Local/ffmpeg/bin"),
    ]
    
    for path in common_paths:
        ffmpeg_exe = Path(path) / "ffmpeg.exe"
        ffprobe_exe = Path(path) / "ffprobe.exe"
        
        if ffmpeg_exe.exists():
            locations.append({
                'type': 'manual_install',
                'ffmpeg': str(ffmpeg_exe),
                'ffprobe': str(ffprobe_exe) if ffprobe_exe.exists() else str(ffmpeg_exe)
            })
    
    # 3. 检查项目本地
    project_root = Path(__file__).parent
    local_ffmpeg = project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    local_ffprobe = project_root / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"
    
    if local_ffmpeg.exists():
        locations.append({
            'type': 'project_local',
            'ffmpeg': str(local_ffmpeg),
            'ffprobe': str(local_ffprobe) if local_ffprobe.exists() else str(local_ffmpeg)
        })
    
    return locations

def test_ffmpeg(ffmpeg_path):
    """测试FFmpeg是否工作正常"""
    try:
        result = subprocess.run([ffmpeg_path, '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 提取版本信息
            version_line = result.stdout.split('\n')[0]
            return True, version_line
        else:
            return False, f"返回码: {result.returncode}"
    except Exception as e:
        return False, str(e)

def configure_ffmpeg(ffmpeg_info):
    """配置FFmpeg路径"""
    config = {
        "ffmpeg_path": ffmpeg_info['ffmpeg'],
        "ffprobe_path": ffmpeg_info['ffprobe'],
        "version_info": ffmpeg_info.get('version', 'Unknown'),
        "system": "windows",
        "configured_at": str(Path(__file__).parent),
        "status": "configured",
        "type": ffmpeg_info['type']
    }
    
    # 保存配置
    config_file = Path(__file__).parent / "configs" / "ffmpeg_config.json"
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ FFmpeg配置已保存到: {config_file}")
    return True

def main():
    """主函数"""
    print("🔍 正在检测FFmpeg安装...")
    
    locations = find_ffmpeg_locations()
    
    if not locations:
        print("❌ 未找到FFmpeg安装")
        print("\n请确保FFmpeg已安装并在系统PATH中，或者:")
        print("1. 下载FFmpeg到 C:/ffmpeg/bin/")
        print("2. 或者将FFmpeg添加到系统环境变量PATH中")
        return False
    
    print(f"✅ 找到 {len(locations)} 个FFmpeg安装位置:")
    
    working_ffmpeg = None
    for i, location in enumerate(locations):
        print(f"\n{i+1}. 类型: {location['type']}")
        print(f"   路径: {location['ffmpeg']}")
        
        # 测试这个FFmpeg
        is_working, info = test_ffmpeg(location['ffmpeg'])
        if is_working:
            print(f"   状态: ✅ 工作正常")
            print(f"   版本: {info}")
            if not working_ffmpeg:
                working_ffmpeg = location
                working_ffmpeg['version'] = info
        else:
            print(f"   状态: ❌ 无法使用 ({info})")
    
    if working_ffmpeg:
        print(f"\n🎯 选择使用: {working_ffmpeg['type']} - {working_ffmpeg['ffmpeg']}")
        configure_ffmpeg(working_ffmpeg)
        print("✅ FFmpeg配置完成！")
        return True
    else:
        print("\n❌ 所有FFmpeg安装都无法正常工作")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 现在可以正常启动VisionAI-ClipsMaster了！")
    else:
        print("\n⚠️ 需要先正确安装FFmpeg")
