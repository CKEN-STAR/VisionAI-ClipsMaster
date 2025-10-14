#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解压FFmpeg 7z文件的脚本
"""

import os
import sys
from pathlib import Path

def extract_ffmpeg():
    """解压FFmpeg文件"""
    try:
        import py7zr
        
        ffmpeg_7z = Path("ffmpeg.7z")
        extract_dir = Path("tools/ffmpeg")
        
        if not ffmpeg_7z.exists():
            print("❌ ffmpeg.7z 文件不存在")
            return False
            
        print(f"📦 开始解压 {ffmpeg_7z} 到 {extract_dir}")
        
        # 确保目标目录存在
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # 解压文件
        with py7zr.SevenZipFile(ffmpeg_7z, mode='r') as archive:
            archive.extractall(path=extract_dir)
            
        print("✅ FFmpeg解压完成")
        
        # 检查是否有bin目录和ffmpeg.exe
        bin_dir = extract_dir / "bin"
        ffmpeg_exe = bin_dir / "ffmpeg.exe"
        
        if ffmpeg_exe.exists():
            print(f"✅ 找到FFmpeg可执行文件: {ffmpeg_exe}")
            return True
        else:
            # 可能解压后的结构不同，查找ffmpeg.exe
            for root, dirs, files in os.walk(extract_dir):
                if "ffmpeg.exe" in files:
                    found_path = Path(root) / "ffmpeg.exe"
                    print(f"✅ 找到FFmpeg可执行文件: {found_path}")
                    return True
            
            print("❌ 解压后未找到ffmpeg.exe")
            return False
            
    except Exception as e:
        print(f"❌ 解压失败: {e}")
        return False

if __name__ == "__main__":
    if extract_ffmpeg():
        print("🎉 FFmpeg安装成功！")
    else:
        print("❌ FFmpeg安装失败")
