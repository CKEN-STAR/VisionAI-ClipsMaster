#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster - 版权声明自动嵌入模块

该模块用于在视频末尾自动添加版权声明，包括：
1. 添加一个持续至少5秒的文本声明
2. 在声明中包含版权符号和生成工具标识
3. 支持自定义文本和样式

使用FFmpeg实现视频处理，确保跨平台兼容性。
"""

import os
import sys
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# 获取项目根目录
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    sys.path.append(str(PROJECT_ROOT))
except Exception:
    PROJECT_ROOT = Path.cwd()

# 尝试导入项目模块
try:
    from src.utils.log_handler import get_logger
    from src.utils.config_manager import get_config
    from src.utils.file_utils import ensure_dir, get_temp_path
except ImportError:
    # 基本日志设置（当无法导入项目模块时）
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def get_config(module):
        return {}
    
    def ensure_dir(path):
        os.makedirs(path, exist_ok=True)
        return path
    
    def get_temp_path():
        return tempfile.gettempdir()

# 配置日志
logger = get_logger("copyright_embedder")

class CopyrightEngine:
    """版权信息嵌入引擎，负责在视频中添加法律声明和版权信息"""
    
    def __init__(self):
        """初始化版权引擎"""
        # 加载配置
        self.config = get_config("exporters").get("copyright", {})
        
        # 默认配置
        self.default_text = "本视频由AI生成\n© 2024 ClipsMaster.All rights reserved"
        self.default_fontsize = 24
        self.default_color = "white"
        self.default_bg_color = "#333333"
        self.default_duration = 5  # 秒
        self.default_size = (1920, 1080)  # 默认分辨率
        
        # 临时目录
        self.temp_dir = Path(get_temp_path()) / "visionai_copyright"
        ensure_dir(self.temp_dir)
        
        # 检查FFmpeg是否可用
        self._check_ffmpeg()
        
        logger.info("版权引擎初始化完成")
    
    def _check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            logger.info("FFmpeg检测成功")
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("FFmpeg不可用，版权嵌入功能可能受限")
    
    def _create_text_clip(self, text: str, duration: int, size: Tuple[int, int],
                          fontsize: int, color: str, bg_color: str) -> str:
        """
        创建带有文本的视频片段
        
        Args:
            text: 显示的文本
            duration: 持续时间（秒）
            size: 视频尺寸 (宽, 高)
            fontsize: 字体大小
            color: 文本颜色
            bg_color: 背景颜色
            
        Returns:
            临时文本视频的路径
        """
        # 创建临时文件
        temp_text_video = self.temp_dir / f"disclaimer_{os.urandom(4).hex()}.mp4"
        
        # 准备FFmpeg命令
        width, height = size
        
        # 替换换行符为适合drawtext的格式
        text_for_ffmpeg = text.replace('\n', '\\n')
        
        # 构建FFmpeg命令 - 创建一个带有文本的视频片段
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖现有文件
            "-f", "lavfi",  # 使用lavfi输入格式
            "-i", f"color=c={bg_color}:s={width}x{height}:d={duration}",  # 创建纯色背景
            "-vf", f"drawtext=text='{text_for_ffmpeg}':fontsize={fontsize}:fontcolor={color}:x=(w-text_w)/2:y=(h-text_h)/2:line_spacing=10",  # 添加文本
            "-c:v", "libx264",  # 视频编码器
            "-preset", "fast",  # 编码速度
            "-crf", "22",  # 质量
            "-shortest",  # 输出最短的流
            str(temp_text_video)  # 输出文件
        ]
        
        try:
            # 执行命令
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"文本片段创建成功: {temp_text_video}")
            return str(temp_text_video)
        except subprocess.CalledProcessError as e:
            logger.error(f"创建文本片段失败: {e.stderr}")
            return ""
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            包含视频信息的字典
        """
        try:
            # 使用FFprobe获取视频信息
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration",
                "-of", "json",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            import json
            info = json.loads(result.stdout)
            
            # 提取宽度、高度和时长
            width = int(info.get("streams", [{}])[0].get("width", 1920))
            height = int(info.get("streams", [{}])[0].get("height", 1080))
            
            # 获取视频时长
            duration_str = info.get("streams", [{}])[0].get("duration", "0")
            try:
                duration = float(duration_str)
            except (ValueError, TypeError):
                duration = 0
            
            return {
                "width": width,
                "height": height,
                "duration": duration
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            # 返回默认值
            return {
                "width": 1920,
                "height": 1080,
                "duration": 0
            }
    
    def add_legal_disclaimer(self, video_path: str, output_path: Optional[str] = None):
        """
        在视频末尾添加法律声明
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径，如果为None则自动生成
            
        Returns:
            输出视频路径
        """
        logger.info(f"在视频 {video_path} 添加法律声明")
        
        # 获取视频信息
        video_info = self._get_video_info(video_path)
        width, height = video_info["width"], video_info["height"]
        
        # 如果未指定输出路径，创建一个
        if output_path is None:
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(video_dir, f"{video_name}_copyright.mp4")
        
        # 获取配置的值（或使用默认值）
        text = self.config.get("text", self.default_text)
        fontsize = self.config.get("fontsize", self.default_fontsize)
        color = self.config.get("color", self.default_color)
        bg_color = self.config.get("bg_color", self.default_bg_color)
        duration = self.config.get("duration", self.default_duration)
        
        # 确保声明至少持续5秒（符合需求）
        duration = max(duration, 5)
        
        # 创建文本视频片段
        text_video = self._create_text_clip(
            text=text,
            duration=duration,
            size=(width, height),
            fontsize=fontsize,
            color=color,
            bg_color=bg_color
        )
        
        if not text_video:
            logger.error("创建文本视频失败，无法添加法律声明")
            return video_path
        
        # 创建临时文件以存储要连接的文件列表
        list_file = self.temp_dir / "concat_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            video_path_normalized = video_path.replace('\\', '/')
            f.write(f"file '{video_path_normalized}'\n")
            text_video_normalized = text_video.replace('\\', '/')
            f.write(f"file '{text_video_normalized}'\n")
        
        try:
            # 使用FFmpeg的concat demuxer将视频和声明连接起来
            cmd = [
                "ffmpeg",
                "-y",  # 覆盖现有文件
                "-f", "concat",  # 使用concat格式
                "-safe", "0",  # 允许不安全的文件名
                "-i", str(list_file),  # 输入文件列表
                "-c", "copy",  # 直接复制编解码器（不重新编码）
                output_path  # 输出文件
            ]
            
            # 执行命令
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logger.info(f"法律声明添加成功: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"添加法律声明失败: {e.stderr}")
            return video_path
        finally:
            # 清理临时文件
            try:
                if os.path.exists(text_video):
                    os.unlink(text_video)
                if os.path.exists(list_file):
                    os.unlink(list_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")

def main():
    """主函数，用于命令行调用"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="视频版权声明嵌入工具")
    parser.add_argument("video_path", help="输入视频路径")
    parser.add_argument("--output", "-o", help="输出视频路径")
    parser.add_argument("--text", "-t", help="自定义声明文本")
    parser.add_argument("--fontsize", "-s", type=int, help="字体大小")
    parser.add_argument("--color", "-c", help="文本颜色")
    parser.add_argument("--bg-color", "-b", help="背景颜色")
    parser.add_argument("--duration", "-d", type=int, help="声明持续时间（秒）")
    
    args = parser.parse_args()
    
    # 创建版权引擎
    engine = CopyrightEngine()
    
    # 设置自定义参数（如果提供）
    if args.text:
        engine.config["text"] = args.text
    if args.fontsize:
        engine.config["fontsize"] = args.fontsize
    if args.color:
        engine.config["color"] = args.color
    if args.bg_color:
        engine.config["bg_color"] = args.bg_color
    if args.duration:
        engine.config["duration"] = max(args.duration, 5)  # 确保至少5秒
    
    # 添加版权声明
    output_path = engine.add_legal_disclaimer(args.video_path, args.output)
    
    print(f"处理完成: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 