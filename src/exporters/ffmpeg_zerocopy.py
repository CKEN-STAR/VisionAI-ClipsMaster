#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FFmpeg零拷贝集成模块

提供FFmpeg与零拷贝处理管道的集成，通过内存映射和共享内存实现高效视频处理。
使用零拷贝机制减少内存使用并提高大型视频文件处理性能。
"""

import os
import sys
import tempfile
import subprocess
import time
import logging
import json
import shutil
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union, Callable, Iterable, BinaryIO
from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path

from src.utils.log_handler import get_logger
from src.utils.exceptions import ProcessingError
from src.exporters.memmap_engine import get_memmap_engine
from src.exporters.stream_pipe import (
    ZeroCopyPipeline, 
    StreamingPipeline,
    Processor, 
    VideoProcessor,
    FunctionProcessor,
    ProcessingMode,
    PipelineContext
)

# 配置日志记录器
logger = get_logger("ffmpeg_zerocopy")

# 检查是否安装了ffmpeg-python
try:
    import ffmpeg
    FFMPEG_PYTHON_AVAILABLE = True
    logger.info("检测到ffmpeg-python库")
except ImportError:
    FFMPEG_PYTHON_AVAILABLE = False
    logger.warning("未检测到ffmpeg-python库，将使用subprocess调用FFmpeg命令行")


class FFmpegError(ProcessingError):
    """FFmpeg处理错误异常"""
    
    def __init__(self, message=None, command=None, output=None):
        """初始化FFmpeg错误异常
        
        Args:
            message: 错误消息
            command: 执行的命令
            output: 命令输出
        """
        self.command = command
        self.output = output
        
        if message is None:
            message = "FFmpeg处理错误"
            if command:
                message += f": {' '.join(command) if isinstance(command, list) else command}"
                
        details = {
            "command": command,
            "output": output
        }
        
        super().__init__(message, processor_name="FFmpeg", details=details)


class FFmpegCodec(Enum):
    """FFmpeg编解码器枚举"""
    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"
    AV1 = "libaom-av1"
    AAC = "aac"
    OPUS = "libopus"
    COPY = "copy"  # 不进行重新编码


class FFmpegPreset(Enum):
    """FFmpeg预设枚举"""
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"


@dataclass
class FFmpegSettings:
    """FFmpeg设置数据类"""
    video_codec: FFmpegCodec = FFmpegCodec.H264     # 视频编码器
    audio_codec: FFmpegCodec = FFmpegCodec.AAC      # 音频编码器
    preset: FFmpegPreset = FFmpegPreset.MEDIUM      # 预设
    crf: int = 23                                   # 恒定质量因子(0-51，越低质量越好)
    width: Optional[int] = None                     # 宽度，None表示保持原始尺寸
    height: Optional[int] = None                    # 高度，None表示保持原始尺寸
    fps: Optional[float] = None                     # 帧率，None表示保持原始帧率
    audio_bitrate: str = "128k"                     # 音频比特率
    threads: int = 0                                # 线程数，0表示自动
    extra_args: Dict[str, Any] = None               # 额外参数
    
    def __post_init__(self):
        """初始化后处理"""
        if self.extra_args is None:
            self.extra_args = {}


class FFmpegMemHandler:
    """FFmpeg内存管理处理器"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """初始化FFmpeg内存管理处理器
        
        Args:
            temp_dir: 临时目录路径，如果为None则使用系统临时目录
        """
        self.memmap_engine = get_memmap_engine()
        
        # 设置临时目录
        if temp_dir:
            self.temp_dir = temp_dir
        else:
            self.temp_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_zerocopy")
            
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 记录创建的临时文件
        self.temp_files: List[str] = []
    
    def create_temp_file(self, prefix: str = "ffmpeg_", suffix: str = ".bin") -> str:
        """创建临时文件
        
        Args:
            prefix: 文件名前缀
            suffix: 文件名后缀
            
        Returns:
            临时文件路径
        """
        temp_file = os.path.join(self.temp_dir, f"{prefix}{int(time.time()*1000)}{suffix}")
        self.temp_files.append(temp_file)
        return temp_file
    
    def cleanup(self):
        """清理创建的所有临时文件"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"清除临时文件失败: {file_path}, 错误: {e}")
        
        # 清空列表
        self.temp_files = []


class FFmpegCommandBuilder:
    """FFmpeg命令构建器"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """初始化FFmpeg命令构建器
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        
        # 验证FFmpeg可用性
        self._validate_ffmpeg()
    
    def _validate_ffmpeg(self):
        """验证FFmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                logger.warning(f"FFmpeg命令返回非零值: {result.returncode}")
                logger.warning(f"FFmpeg输出: {result.stderr}")
            else:
                version_line = result.stdout.split('\n')[0]
                logger.info(f"FFmpeg可用: {version_line}")
        except Exception as e:
            logger.error(f"验证FFmpeg失败: {e}")
            logger.warning("FFmpeg可能未安装，请确保FFmpeg已添加到系统PATH中")
    
    def build_cut_command(self, 
                         input_path: str, 
                         output_path: str, 
                         start_time: float,
                         duration: Optional[float] = None,
                         settings: Optional[FFmpegSettings] = None) -> List[str]:
        """构建剪切命令
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            start_time: 开始时间(秒)
            duration: 持续时间(秒)，None表示剪到结尾
            settings: FFmpeg设置
            
        Returns:
            命令行参数列表
        """
        if settings is None:
            settings = FFmpegSettings()
        
        # 基本命令
        cmd = [
            self.ffmpeg_path,
            "-y",  # 覆盖输出文件
            "-ss", str(start_time),  # 开始时间
            "-i", input_path  # 输入文件
        ]
        
        # 添加持续时间参数
        if duration is not None:
            cmd.extend(["-t", str(duration)])
        
        # 添加视频编码参数
        cmd.extend([
            "-c:v", settings.video_codec.value,
            "-preset", settings.preset.value,
            "-crf", str(settings.crf)
        ])
        
        # 添加分辨率参数
        if settings.width and settings.height:
            cmd.extend(["-s", f"{settings.width}x{settings.height}"])
        
        # 添加帧率参数
        if settings.fps:
            cmd.extend(["-r", str(settings.fps)])
        
        # 添加音频编码参数
        cmd.extend([
            "-c:a", settings.audio_codec.value,
            "-b:a", settings.audio_bitrate
        ])
        
        # 添加线程数参数
        if settings.threads > 0:
            cmd.extend(["-threads", str(settings.threads)])
        
        # 添加额外参数
        for key, value in settings.extra_args.items():
            if value is not None:
                cmd.extend([f"-{key}", str(value)])
        
        # 添加输出文件
        cmd.append(output_path)
        
        return cmd
    
    def build_concat_command(self,
                            input_list_file: str,
                            output_path: str,
                            settings: Optional[FFmpegSettings] = None) -> List[str]:
        """构建视频合并命令
        
        Args:
            input_list_file: 包含输入文件的列表文件路径
            output_path: 输出文件路径
            settings: FFmpeg设置
            
        Returns:
            命令行参数列表
        """
        if settings is None:
            settings = FFmpegSettings()
        
        # 基本命令
        cmd = [
            self.ffmpeg_path,
            "-y",  # 覆盖输出文件
            "-f", "concat",  # 使用concat分离器
            "-safe", "0",  # 允许不安全的文件路径
            "-i", input_list_file  # 输入文件列表
        ]
        
        # 添加视频编码参数
        cmd.extend([
            "-c:v", settings.video_codec.value,
            "-preset", settings.preset.value,
            "-crf", str(settings.crf)
        ])
        
        # 添加分辨率参数
        if settings.width and settings.height:
            cmd.extend(["-s", f"{settings.width}x{settings.height}"])
        
        # 添加音频编码参数
        cmd.extend([
            "-c:a", settings.audio_codec.value,
            "-b:a", settings.audio_bitrate
        ])
        
        # 添加线程数参数
        if settings.threads > 0:
            cmd.extend(["-threads", str(settings.threads)])
        
        # 添加额外参数
        for key, value in settings.extra_args.items():
            if value is not None:
                cmd.extend([f"-{key}", str(value)])
        
        # 添加输出文件
        cmd.append(output_path)
        
        return cmd
    
    def build_command(self,
                     operation: str,
                     **kwargs) -> List[str]:
        """通用命令构建器
        
        Args:
            operation: 操作类型("cut", "concat", ...)
            **kwargs: 操作特定参数
            
        Returns:
            命令行参数列表
        """
        # 根据操作类型调用相应的构建函数
        if operation == "cut":
            return self.build_cut_command(**kwargs)
        elif operation == "concat":
            return self.build_concat_command(**kwargs)
        else:
            raise ValueError(f"不支持的操作类型: {operation}")


class FFmpegExecutor:
    """FFmpeg执行器"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """初始化FFmpeg执行器
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
        """
        self.ffmpeg_path = ffmpeg_path
        self.command_builder = FFmpegCommandBuilder(ffmpeg_path)
        self.mem_handler = FFmpegMemHandler()
    
    def execute_command(self, 
                       command: List[str], 
                       show_output: bool = False) -> Tuple[int, str, str]:
        """执行FFmpeg命令
        
        Args:
            command: 命令行参数列表
            show_output: 是否显示输出
            
        Returns:
            (返回码, 标准输出, 标准错误)
        """
        logger.info(f"执行FFmpeg命令: {' '.join(command)}")
        start_time = time.time()
        
        try:
            # 执行命令
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE if not show_output else None,
                stderr=subprocess.PIPE if not show_output else None,
                text=True
            )
            
            # 获取输出
            stdout, stderr = process.communicate()
            
            # 获取返回码
            return_code = process.returncode
            
            # 计算执行时间
            execution_time = time.time() - start_time
            logger.info(f"FFmpeg命令执行完成，耗时: {execution_time:.2f}秒，返回码: {return_code}")
            
            # 如果命令失败，记录错误信息
            if return_code != 0:
                logger.error(f"FFmpeg命令失败: {stderr}")
            
            return return_code, stdout or "", stderr or ""
            
        except Exception as e:
            logger.error(f"执行FFmpeg命令时发生异常: {e}")
            return 1, "", str(e)
    
    def cut_video(self,
                input_path: str,
                output_path: str,
                start_time: float,
                duration: Optional[float] = None,
                settings: Optional[FFmpegSettings] = None) -> bool:
        """剪切视频
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            start_time: 开始时间(秒)
            duration: 持续时间(秒)
            settings: FFmpeg设置
            
        Returns:
            是否成功
        """
        # 构建命令
        command = self.command_builder.build_cut_command(
            input_path=input_path,
            output_path=output_path,
            start_time=start_time,
            duration=duration,
            settings=settings
        )
        
        # 执行命令
        return_code, _, stderr = self.execute_command(command)
        
        # 检查命令是否成功
        if return_code != 0:
            logger.error(f"剪切视频失败: {stderr}")
            return False
        
        return True
    
    def concat_videos(self,
                     input_files: List[str],
                     output_path: str,
                     settings: Optional[FFmpegSettings] = None) -> bool:
        """连接多个视频
        
        Args:
            input_files: 输入文件路径列表
            output_path: 输出文件路径
            settings: FFmpeg设置
            
        Returns:
            是否成功
        """
        # 创建临时文件列表
        list_file_path = self.mem_handler.create_temp_file(suffix=".txt")
        
        # 写入文件列表
        with open(list_file_path, 'w', encoding='utf-8') as f:
            for file_path in input_files:
                # 路径需要使用反斜杠，否则FFmpeg会报错
                file_path = file_path.replace('\\', '/')
                f.write(f"file '{file_path}'\n")
        
        # 构建命令
        command = self.command_builder.build_concat_command(
            input_list_file=list_file_path,
            output_path=output_path,
            settings=settings
        )
        
        # 执行命令
        return_code, _, stderr = self.execute_command(command)
        
        # 检查命令是否成功
        if return_code != 0:
            logger.error(f"连接视频失败: {stderr}")
            return False
        
        return True
    
    def cleanup(self):
        """清理临时文件"""
        self.mem_handler.cleanup()
    
    def __del__(self):
        """析构函数，确保清理临时文件"""
        self.cleanup()


class FFmpegProcessor(Processor):
    """FFmpeg处理器基类"""
    
    def __init__(self, name: str = None, ffmpeg_path: str = "ffmpeg"):
        """初始化FFmpeg处理器
        
        Args:
            name: 处理器名称
            ffmpeg_path: FFmpeg可执行文件路径
        """
        super().__init__(name or "FFmpegProcessor")
        self.ffmpeg_executor = FFmpegExecutor(ffmpeg_path)
    
    def process(self, data: Any) -> Any:
        """处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
        """
        # 基类不实现具体处理逻辑
        raise NotImplementedError("子类必须实现process方法")


class VideoCutProcessor(FFmpegProcessor):
    """视频剪切处理器"""
    
    def __init__(self, 
                start_time: float, 
                duration: Optional[float] = None,
                settings: Optional[FFmpegSettings] = None,
                ffmpeg_path: str = "ffmpeg"):
        """初始化视频剪切处理器
        
        Args:
            start_time: 开始时间(秒)
            duration: 持续时间(秒)
            settings: FFmpeg设置
            ffmpeg_path: FFmpeg可执行文件路径
        """
        super().__init__("VideoCutProcessor", ffmpeg_path)
        self.start_time = start_time
        self.duration = duration
        self.settings = settings or FFmpegSettings()
    
    def process(self, data: Tuple[str, str]) -> str:
        """处理视频剪切
        
        Args:
            data: (输入文件路径, 输出文件路径)
            
        Returns:
            输出文件路径
        """
        input_path, output_path = data
        
        # 执行剪切
        success = self.ffmpeg_executor.cut_video(
            input_path=input_path,
            output_path=output_path,
            start_time=self.start_time,
            duration=self.duration,
            settings=self.settings
        )
        
        if not success:
            raise FFmpegError(f"视频剪切失败: {input_path} -> {output_path}")
        
        return output_path


class VideoConcatProcessor(FFmpegProcessor):
    """视频连接处理器"""
    
    def __init__(self,
                settings: Optional[FFmpegSettings] = None,
                ffmpeg_path: str = "ffmpeg"):
        """初始化视频连接处理器
        
        Args:
            settings: FFmpeg设置
            ffmpeg_path: FFmpeg可执行文件路径
        """
        super().__init__("VideoConcatProcessor", ffmpeg_path)
        self.settings = settings or FFmpegSettings()
    
    def process(self, data: Tuple[List[str], str]) -> str:
        """处理视频连接
        
        Args:
            data: (输入文件路径列表, 输出文件路径)
            
        Returns:
            输出文件路径
        """
        input_files, output_path = data
        
        # 执行连接
        success = self.ffmpeg_executor.concat_videos(
            input_files=input_files,
            output_path=output_path,
            settings=self.settings
        )
        
        if not success:
            raise FFmpegError(f"视频连接失败: {len(input_files)}个文件 -> {output_path}")
        
        return output_path


class ZeroCopyFFmpegPipeline(ZeroCopyPipeline):
    """零拷贝FFmpeg处理管道"""
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        """初始化零拷贝FFmpeg处理管道
        
        Args:
            ffmpeg_path: FFmpeg可执行文件路径
        """
        super().__init__()
        self.ffmpeg_path = ffmpeg_path
        self.executor = FFmpegExecutor(ffmpeg_path)
        self.mem_handler = self.executor.mem_handler
        self.settings = FFmpegSettings()
    
    def cut_video(self, 
                 input_path: str, 
                 output_path: str, 
                 start_time: float, 
                 duration: Optional[float] = None) -> str:
        """剪切视频
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            start_time: 开始时间(秒)
            duration: 持续时间(秒)
            
        Returns:
            输出文件路径
        """
        processor = VideoCutProcessor(
            start_time=start_time,
            duration=duration,
            settings=self.settings,
            ffmpeg_path=self.ffmpeg_path
        )
        
        return self.add_stage(processor).execute((input_path, output_path))
    
    def concat_videos(self,
                     input_files: List[str],
                     output_path: str) -> str:
        """连接多个视频
        
        Args:
            input_files: 输入文件路径列表
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        processor = VideoConcatProcessor(
            settings=self.settings,
            ffmpeg_path=self.ffmpeg_path
        )
        
        return self.add_stage(processor).execute((input_files, output_path))
    
    def set_settings(self, settings: FFmpegSettings) -> 'ZeroCopyFFmpegPipeline':
        """设置FFmpeg处理参数
        
        Args:
            settings: FFmpeg设置
            
        Returns:
            自身，支持链式调用
        """
        self.settings = settings
        return self
    
    def cleanup(self):
        """清理临时文件"""
        self.executor.cleanup()
    
    def __del__(self):
        """析构函数，确保清理临时文件"""
        self.cleanup()


class StreamingFFmpegPipeline(StreamingPipeline):
    """流式FFmpeg处理管道"""
    
    def __init__(self, chunk_size: int = 30, ffmpeg_path: str = "ffmpeg"):
        """初始化流式FFmpeg处理管道
        
        Args:
            chunk_size: 分块大小
            ffmpeg_path: FFmpeg可执行文件路径
        """
        super().__init__(chunk_size)
        self.ffmpeg_path = ffmpeg_path
        self.executor = FFmpegExecutor(ffmpeg_path)
        self.mem_handler = self.executor.mem_handler
        self.settings = FFmpegSettings()
    
    def set_settings(self, settings: FFmpegSettings) -> 'StreamingFFmpegPipeline':
        """设置FFmpeg处理参数
        
        Args:
            settings: FFmpeg设置
            
        Returns:
            自身，支持链式调用
        """
        self.settings = settings
        return self
    
    def cleanup(self):
        """清理临时文件"""
        self.executor.cleanup()
    
    def __del__(self):
        """析构函数，确保清理临时文件"""
        self.cleanup()


def create_ffmpeg_pipeline(ffmpeg_path: str = "ffmpeg") -> ZeroCopyFFmpegPipeline:
    """创建FFmpeg零拷贝管道
    
    Args:
        ffmpeg_path: FFmpeg可执行文件路径
        
    Returns:
        ZeroCopyFFmpegPipeline实例
    """
    return ZeroCopyFFmpegPipeline(ffmpeg_path)


def create_streaming_ffmpeg_pipeline(chunk_size: int = 30, 
                                    ffmpeg_path: str = "ffmpeg") -> StreamingFFmpegPipeline:
    """创建流式FFmpeg处理管道
    
    Args:
        chunk_size: 分块大小
        ffmpeg_path: FFmpeg可执行文件路径
        
    Returns:
        StreamingFFmpegPipeline实例
    """
    return StreamingFFmpegPipeline(chunk_size, ffmpeg_path)


# 工厂函数
def cut_video(input_path: str, 
             output_path: str, 
             start_time: float, 
             duration: Optional[float] = None,
             settings: Optional[FFmpegSettings] = None,
             ffmpeg_path: str = "ffmpeg") -> str:
    """剪切视频工厂函数
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        start_time: 开始时间(秒)
        duration: 持续时间(秒)
        settings: FFmpeg设置
        ffmpeg_path: FFmpeg可执行文件路径
        
    Returns:
        输出文件路径
    """
    pipeline = ZeroCopyFFmpegPipeline(ffmpeg_path)
    
    if settings:
        pipeline.set_settings(settings)
        
    return pipeline.cut_video(input_path, output_path, start_time, duration)


def concat_videos(input_files: List[str],
                output_path: str,
                settings: Optional[FFmpegSettings] = None,
                ffmpeg_path: str = "ffmpeg") -> str:
    """连接多个视频工厂函数
    
    Args:
        input_files: 输入文件路径列表
        output_path: 输出文件路径
        settings: FFmpeg设置
        ffmpeg_path: FFmpeg可执行文件路径
        
    Returns:
        输出文件路径
    """
    pipeline = ZeroCopyFFmpegPipeline(ffmpeg_path)
    
    if settings:
        pipeline.set_settings(settings)
        
    return pipeline.concat_videos(input_files, output_path)


# 简单使用示例
if __name__ == "__main__":
    # 示例1：剪切视频
    input_file = "input.mp4"
    output_file = "output.mp4"
    
    # 创建管道
    pipeline = create_ffmpeg_pipeline()
    
    # 设置参数
    settings = FFmpegSettings(
        video_codec=FFmpegCodec.H264,
        preset=FFmpegPreset.VERYFAST,
        crf=23
    )
    pipeline.set_settings(settings)
    
    # 执行剪切
    try:
        result = pipeline.cut_video(
            input_path=input_file,
            output_path=output_file,
            start_time=10.5,
            duration=30.0
        )
        print(f"视频剪切完成: {result}")
    except FFmpegError as e:
        print(f"处理错误: {e}")
    finally:
        # 清理临时文件
        pipeline.cleanup() 