#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg工具模块
提供FFmpeg路径检测和配置功能
"""

import os
import subprocess
import json
from pathlib import Path

class FFmpegUtils:
    """FFmpeg工具类"""
    
    def __init__(self):
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self.load_config()
    
    def load_config(self):
        """加载FFmpeg配置"""
        config_files = [
            "configs/ffmpeg_config.json",
            "src/utils/ffmpeg_config.json", 
            "ffmpeg_config.json"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    self.ffmpeg_path = config.get("ffmpeg_path")
                    self.ffprobe_path = config.get("ffprobe_path")
                    return True
                except Exception:
                    continue
        
        # 如果没有配置文件，尝试默认路径
        self.ffmpeg_path = r"D:\zancun\VisionAI-ClipsMaster\tools\ffmpeg\bin\ffmpeg.exe"
        self.ffprobe_path = r"D:\zancun\VisionAI-ClipsMaster\tools\ffmpeg\bin\ffprobe.exe"
        return False
    
    def is_available(self):
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run([self.ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_ffmpeg_path(self):
        """获取FFmpeg路径"""
        return self.ffmpeg_path
    
    def get_ffprobe_path(self):
        """获取FFprobe路径"""
        return self.ffprobe_path

# 全局实例
ffmpeg_utils = FFmpegUtils()
