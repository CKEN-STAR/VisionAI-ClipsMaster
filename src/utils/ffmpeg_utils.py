#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FFmpeg工具类
提供视频处理相关的FFmpeg功能
"""

import os
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FFmpegUtils:
    """FFmpeg工具类"""
    
    def __init__(self):
        """初始化FFmpeg工具"""
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        
    def _find_ffmpeg(self) -> str:
        """查找FFmpeg可执行文件"""
        try:
            # 首先检查项目内的FFmpeg
            project_root = Path(__file__).resolve().parent.parent.parent
            ffmpeg_paths = [
                project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
                project_root / "tools" / "ffmpeg" / "ffmpeg.exe",
                "ffmpeg.exe",
                "ffmpeg"
            ]
            
            for path in ffmpeg_paths:
                try:
                    if isinstance(path, Path) and path.exists():
                        return str(path)
                    elif isinstance(path, str):
                        result = subprocess.run([path, "-version"], 
                                              capture_output=True, 
                                              timeout=5)
                        if result.returncode == 0:
                            return path
                except Exception:
                    continue
            
            logger.warning("FFmpeg未找到，某些功能可能不可用")
            return "ffmpeg"
            
        except Exception as e:
            logger.error(f"查找FFmpeg失败: {e}")
            return "ffmpeg"
    
    def _find_ffprobe(self) -> str:
        """查找FFprobe可执行文件"""
        try:
            # 首先检查项目内的FFprobe
            project_root = Path(__file__).resolve().parent.parent.parent
            ffprobe_paths = [
                project_root / "tools" / "ffmpeg" / "bin" / "ffprobe.exe",
                project_root / "tools" / "ffmpeg" / "ffprobe.exe",
                "ffprobe.exe",
                "ffprobe"
            ]
            
            for path in ffprobe_paths:
                try:
                    if isinstance(path, Path) and path.exists():
                        return str(path)
                    elif isinstance(path, str):
                        result = subprocess.run([path, "-version"], 
                                              capture_output=True, 
                                              timeout=5)
                        if result.returncode == 0:
                            return path
                except Exception:
                    continue
            
            return "ffprobe"
            
        except Exception as e:
            logger.error(f"查找FFprobe失败: {e}")
            return "ffprobe"
    
    def check_ffmpeg_availability(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run([self.ffmpeg_path, "-version"], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """获取处理能力信息"""
        try:
            capabilities = {
                "ffmpeg_available": self.check_ffmpeg_availability(),
                "ffprobe_available": self.check_ffprobe_availability(),
                "supported_formats": [],
                "supported_codecs": []
            }
            
            if capabilities["ffmpeg_available"]:
                # 获取支持的格式
                try:
                    result = subprocess.run([self.ffmpeg_path, "-formats"], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=10)
                    if result.returncode == 0:
                        # 解析格式信息
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'mp4' in line.lower():
                                capabilities["supported_formats"].append("mp4")
                            elif 'avi' in line.lower():
                                capabilities["supported_formats"].append("avi")
                            elif 'mov' in line.lower():
                                capabilities["supported_formats"].append("mov")
                except Exception:
                    pass
                
                # 获取支持的编解码器
                try:
                    result = subprocess.run([self.ffmpeg_path, "-codecs"], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=10)
                    if result.returncode == 0:
                        # 解析编解码器信息
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'h264' in line.lower():
                                capabilities["supported_codecs"].append("h264")
                            elif 'h265' in line.lower():
                                capabilities["supported_codecs"].append("h265")
                            elif 'aac' in line.lower():
                                capabilities["supported_codecs"].append("aac")
                except Exception:
                    pass
            
            return capabilities
            
        except Exception as e:
            logger.error(f"获取处理能力失败: {e}")
            return {
                "ffmpeg_available": False,
                "ffprobe_available": False,
                "supported_formats": [],
                "supported_codecs": [],
                "error": str(e)
            }
    
    def check_ffprobe_availability(self) -> bool:
        """检查FFprobe是否可用"""
        try:
            result = subprocess.run([self.ffprobe_path, "-version"], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            if not self.check_ffprobe_availability():
                return {"error": "FFprobe不可用"}
            
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                import json
                info = json.loads(result.stdout)
                
                # 提取关键信息
                video_info = {
                    "duration": 0.0,
                    "width": 0,
                    "height": 0,
                    "fps": 0.0,
                    "bitrate": 0,
                    "format": "",
                    "codec": ""
                }
                
                if "format" in info:
                    video_info["duration"] = float(info["format"].get("duration", 0))
                    video_info["bitrate"] = int(info["format"].get("bit_rate", 0))
                    video_info["format"] = info["format"].get("format_name", "")
                
                if "streams" in info:
                    for stream in info["streams"]:
                        if stream.get("codec_type") == "video":
                            video_info["width"] = stream.get("width", 0)
                            video_info["height"] = stream.get("height", 0)
                            video_info["codec"] = stream.get("codec_name", "")
                            
                            # 计算帧率
                            fps_str = stream.get("r_frame_rate", "0/1")
                            if "/" in fps_str:
                                num, den = fps_str.split("/")
                                if int(den) != 0:
                                    video_info["fps"] = float(num) / float(den)
                            break
                
                return video_info
            else:
                return {"error": f"FFprobe执行失败: {result.stderr}"}
                
        except Exception as e:
            logger.error(f"获取视频信息失败: {e}")
            return {"error": str(e)}
    
    def cut_video_segment(self, input_path: str, output_path: str, 
                         start_time: float, duration: float) -> bool:
        """切割视频片段"""
        try:
            if not self.check_ffmpeg_availability():
                logger.error("FFmpeg不可用")
                return False
            
            cmd = [
                self.ffmpeg_path,
                "-i", input_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                "-y",  # 覆盖输出文件
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"切割视频失败: {e}")
            return False
    
    def concatenate_videos(self, input_files: List[str], output_path: str) -> bool:
        """拼接视频文件"""
        try:
            if not self.check_ffmpeg_availability():
                logger.error("FFmpeg不可用")
                return False
            
            if not input_files:
                return False
            
            # 创建文件列表
            list_file = output_path + ".txt"
            with open(list_file, 'w', encoding='utf-8') as f:
                for file_path in input_files:
                    f.write(f"file '{file_path}'\n")
            
            try:
                cmd = [
                    self.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c", "copy",
                    "-y",
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=300)
                return result.returncode == 0
                
            finally:
                # 清理临时文件
                if os.path.exists(list_file):
                    os.remove(list_file)
                    
        except Exception as e:
            logger.error(f"拼接视频失败: {e}")
            return False

# 全局实例
ffmpeg_utils = FFmpegUtils()

def get_ffmpeg_utils() -> FFmpegUtils:
    """获取FFmpeg工具实例"""
    return ffmpeg_utils
