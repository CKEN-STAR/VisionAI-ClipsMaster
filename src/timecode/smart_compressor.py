#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能压缩算法模块

此模块实现视频内容的智能压缩功能，包括：
1. 基于场景重要性的动态压缩率调整
2. 保护关键场景免受过度压缩
3. 自适应视频码率控制
4. 多级压缩质量策略
5. 维持情感重点场景的质量
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass
import math

# 导入关键场景保护器
from .key_scene_protector import KeySceneGuard, ProtectionLevel
from .base_analyzer import BaseAnalyzer

# 配置日志
logger = logging.getLogger(__name__)


class CompressionLevel(Enum):
    """压缩级别枚举"""
    NONE = 0        # 无压缩
    MINIMAL = 1     # 最小压缩
    LOW = 2         # 低压缩
    MEDIUM = 3      # 中等压缩
    HIGH = 4        # 高压缩
    EXTREME = 5     # 极限压缩


@dataclass
class CompressionProfile:
    """压缩配置文件"""
    name: str                           # 配置名称
    crf: int                            # 恒定速率因子（0-51，越低质量越高）
    preset: str                         # 编码预设（ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow）
    tune: Optional[str] = None          # 优化参数 (film, animation, grain, stillimage, psnr, ssim, fastdecode, zerolatency)
    pixel_format: str = "yuv420p"       # 像素格式
    max_bitrate: Optional[str] = None   # 最大比特率
    description: str = ""               # 配置描述


class SmartCompressor:
    """智能压缩器
    
    基于视频内容特性和关键场景保护进行智能压缩
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化智能压缩器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()
        
        # 初始化场景保护器
        self.scene_guard = KeySceneGuard(self.config.get("protection_config"))
        
        # 初始化基础分析器
        self.analyzer = BaseAnalyzer(self.config.get("analyzer_config"))
        
        # 初始化压缩配置文件
        self.compression_profiles = self._initialize_profiles()
        
        # 设置FFmpeg路径
        self.ffmpeg_path = self.config.get("ffmpeg_path", "ffmpeg")
        
        logger.info("智能压缩器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "base_crf": 23,                      # 基础CRF值
            "protection_enabled": True,          # 是否启用保护机制
            "dynamic_adjustment_range": 10,      # 动态调整范围
            "bitrate_factor": 0.75,              # 码率系数（相对于原始码率）
            "min_segment_duration": 1.0,         # 最小片段时长（秒）
            "max_threads": 0,                    # 最大线程数（0表示自动）
            "temp_directory": None,              # 临时文件目录（None表示系统默认）
            "audio_quality": "medium",           # 音频质量
            "two_pass_encoding": False,          # 是否使用两次编码
            "fast_start": True,                  # 是否启用快速启动
            "hardware_acceleration": "auto",     # 硬件加速类型
            "adaptive_quantization": "auto",     # 自适应量化参数
            "ffmpeg_path": "ffmpeg",             # FFmpeg路径
            "ffprobe_path": "ffprobe",           # FFprobe路径
            "log_level": "info"                  # 日志级别
        }
    
    def _initialize_profiles(self) -> Dict[str, CompressionProfile]:
        """初始化压缩配置文件
        
        Returns:
            Dict[str, CompressionProfile]: 压缩配置文件字典
        """
        profiles = {
            "lossless": CompressionProfile(
                name="lossless",
                crf=0,
                preset="medium",
                tune="film",
                description="无损压缩"
            ),
            "high_quality": CompressionProfile(
                name="high_quality",
                crf=18,
                preset="slow",
                tune="film",
                max_bitrate="8M",
                description="高质量压缩"
            ),
            "balanced": CompressionProfile(
                name="balanced",
                crf=23,
                preset="medium",
                max_bitrate="4M",
                description="平衡压缩"
            ),
            "size_efficient": CompressionProfile(
                name="size_efficient",
                crf=28,
                preset="fast",
                max_bitrate="2M",
                description="体积优先压缩"
            ),
            "minimal": CompressionProfile(
                name="minimal",
                crf=35,
                preset="veryfast",
                max_bitrate="1M",
                description="最小体积压缩"
            )
        }
        
        return profiles
    
    def dynamic_compress(self, 
                        video_path: str, 
                        output_path: str, 
                        scene_data: List[Dict[str, Any]] = None,
                        target_size: Optional[Union[int, float, str]] = None,
                        quality_preference: float = 0.5) -> Dict[str, Any]:
        """动态压缩视频文件
        
        根据场景重要性动态调整压缩参数，保护关键场景
        
        Args:
            video_path: 源视频文件路径
            output_path: 输出文件路径
            scene_data: 场景数据列表
            target_size: 目标文件大小（字节，或表示百分比的字符串）
            quality_preference: 质量偏好系数（0.0-1.0，越大质量越高）
            
        Returns:
            Dict[str, Any]: 压缩结果统计
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 分析视频
        video_info = self._analyze_video(video_path)
        logger.info(f"视频分析完成: {video_info['duration']}秒, {video_info['bitrate']}kbps")
        
        # 如果未提供场景数据，尝试自动检测
        if scene_data is None:
            logger.info("未提供场景数据，尝试自动检测...")
            scene_data = self._detect_scenes(video_path)
        
        # 应用场景保护机制
        if self.config["protection_enabled"] and scene_data:
            scene_data = self.scene_guard.mark_protected(scene_data)
            
        # 计算目标比特率
        target_bitrate = self._calculate_target_bitrate(
            video_info, target_size, quality_preference
        )
        logger.info(f"计算的目标比特率: {target_bitrate}kbps")
        
        # 选择压缩策略
        if scene_data and len(scene_data) > 0:
            # 基于场景的动态压缩
            compression_result = self._segment_based_compression(
                video_path, output_path, scene_data, video_info, target_bitrate
            )
        else:
            # 全局压缩
            compression_result = self._global_compression(
                video_path, output_path, video_info, target_bitrate
            )
        
        # 验证压缩结果
        if os.path.exists(output_path):
            result_info = self._analyze_video(output_path)
            compression_ratio = result_info['size'] / video_info['size']
            
            logger.info(f"压缩完成: 压缩率 {compression_ratio:.2%}, "
                      f"新比特率 {result_info['bitrate']}kbps")
            
            compression_result.update({
                'source_size': video_info['size'],
                'compressed_size': result_info['size'],
                'compression_ratio': compression_ratio,
                'source_bitrate': video_info['bitrate'],
                'target_bitrate': target_bitrate,
                'result_bitrate': result_info['bitrate']
            })
        
        return compression_result
    
    def _analyze_video(self, video_path: str) -> Dict[str, Any]:
        """分析视频文件信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        # 使用BaseAnalyzer获取视频元数据
        metadata = self.analyzer.get_video_metadata(video_path)
        
        # 提取关键信息
        video_info = {
            'duration': float(metadata.get('duration', 0)),
            'bitrate': float(metadata.get('bit_rate', 0)) / 1000,  # 转换为kbps
            'size': os.path.getsize(video_path),
            'width': int(metadata.get('width', 0)),
            'height': int(metadata.get('height', 0)),
            'fps': float(metadata.get('fps', 0)),
            'codec': metadata.get('codec_name', ''),
            'format': metadata.get('format_name', '')
        }
        
        return video_info
    
    def _detect_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        """自动检测视频场景
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            List[Dict[str, Any]]: 场景数据列表
        """
        # 简单的基于时间的场景划分
        # 在实际生产环境中，应使用更复杂的场景检测算法
        video_info = self._analyze_video(video_path)
        duration = video_info['duration']
        
        # 每30秒或视频长度的十分之一（取较小值）为一个场景
        scene_duration = min(30.0, duration / 10.0)
        scene_count = math.ceil(duration / scene_duration)
        
        scenes = []
        for i in range(scene_count):
            start_time = i * scene_duration
            end_time = min(start_time + scene_duration, duration)
            
            scenes.append({
                'id': f'scene_{i}',
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'importance': 0.5  # 默认重要性
            })
        
        return scenes
    
    def _calculate_target_bitrate(self,
                                video_info: Dict[str, Any],
                                target_size: Optional[Union[int, float, str]] = None,
                                quality_preference: float = 0.5) -> float:
        """计算目标比特率
        
        Args:
            video_info: 视频信息
            target_size: 目标文件大小（字节，或表示百分比的字符串）
            quality_preference: 质量偏好系数
            
        Returns:
            float: 目标比特率（kbps）
        """
        original_bitrate = video_info['bitrate']
        duration = video_info['duration']
        
        # 根据质量偏好调整基础码率因子
        base_factor = self.config["bitrate_factor"]
        adjusted_factor = base_factor + (1 - base_factor) * quality_preference
        
        if target_size is None:
            # 使用调整后的系数计算目标码率
            target_bitrate = original_bitrate * adjusted_factor
        else:
            # 基于目标大小计算
            if isinstance(target_size, str) and target_size.endswith('%'):
                # 百分比格式
                percentage = float(target_size.rstrip('%')) / 100
                target_size_bytes = video_info['size'] * percentage
            else:
                # 字节格式
                target_size_bytes = float(target_size)
            
            # 计算目标码率（字节转比特并考虑时长）
            target_bitrate = (target_size_bytes * 8) / (duration * 1000)
        
        # 确保不低于合理的最低码率
        min_bitrate = 500.0  # 最低500kbps，确保基本质量
        target_bitrate = max(target_bitrate, min_bitrate)
        
        return target_bitrate
    
    def _select_compression_level(self, 
                                scene: Dict[str, Any], 
                                base_level: CompressionLevel) -> CompressionLevel:
        """为场景选择压缩级别
        
        Args:
            scene: 场景数据
            base_level: 基础压缩级别
            
        Returns:
            CompressionLevel: 压缩级别
        """
        # 默认使用基础级别
        level = base_level
        
        # 检查是否是受保护场景
        is_protected = False
        protection_info = scene.get('_protection_info', {})
        if protection_info:
            is_protected = True
            protection_level = protection_info.get('level', 'NONE')
            
            # 根据保护级别降低压缩强度
            if protection_level == 'CRITICAL':
                # 无压缩或最小压缩
                return CompressionLevel.NONE
            elif protection_level == 'HIGH':
                # 最多使用最小压缩
                return self._min_compression_level(CompressionLevel.MINIMAL, base_level)
            elif protection_level == 'MEDIUM':
                # 最多使用低压缩
                return self._min_compression_level(CompressionLevel.LOW, base_level)
        
        # 检查场景重要性
        importance = scene.get('importance', 0.5)
        if importance > 0.8:
            # 高重要性场景
            level = self._min_compression_level(level, CompressionLevel.LOW)
        elif importance > 0.6:
            # 中等重要性场景
            level = self._min_compression_level(level, CompressionLevel.MEDIUM)
        
        return level
    
    def _min_compression_level(self, 
                              level1: CompressionLevel, 
                              level2: CompressionLevel) -> CompressionLevel:
        """获取两个压缩级别中较小的一个
        
        Args:
            level1: 第一个压缩级别
            level2: 第二个压缩级别
            
        Returns:
            CompressionLevel: 较小的压缩级别
        """
        return level1 if level1.value < level2.value else level2
    
    def _get_profile_for_level(self, 
                              level: CompressionLevel, 
                              target_bitrate: float) -> Dict[str, Any]:
        """获取压缩级别对应的编码参数
        
        Args:
            level: 压缩级别
            target_bitrate: 目标比特率
            
        Returns:
            Dict[str, Any]: 编码参数
        """
        # 根据压缩级别选择配置文件
        if level == CompressionLevel.NONE:
            profile = self.compression_profiles["lossless"]
        elif level == CompressionLevel.MINIMAL:
            profile = self.compression_profiles["high_quality"]
        elif level == CompressionLevel.LOW:
            profile = self.compression_profiles["balanced"]
        elif level == CompressionLevel.MEDIUM:
            profile = self.compression_profiles["balanced"]
        elif level == CompressionLevel.HIGH:
            profile = self.compression_profiles["size_efficient"]
        else:  # EXTREME
            profile = self.compression_profiles["minimal"]
        
        # 构建编码参数
        encode_params = {
            "crf": profile.crf,
            "preset": profile.preset,
            "max_bitrate": f"{target_bitrate}k",
            "pixel_format": profile.pixel_format
        }
        
        # 添加可选参数
        if profile.tune:
            encode_params["tune"] = profile.tune
        
        return encode_params
    
    def _build_ffmpeg_command(self, 
                            input_path: str, 
                            output_path: str, 
                            encode_params: Dict[str, Any],
                            start_time: Optional[float] = None,
                            duration: Optional[float] = None) -> List[str]:
        """构建FFmpeg命令
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            encode_params: 编码参数
            start_time: 开始时间
            duration: 持续时间
            
        Returns:
            List[str]: FFmpeg命令
        """
        command = [self.ffmpeg_path, "-y"]  # 覆盖输出文件
        
        # 添加起始时间
        if start_time is not None:
            command.extend(["-ss", str(start_time)])
        
        # 输入文件
        command.extend(["-i", input_path])
        
        # 添加持续时间
        if duration is not None:
            command.extend(["-t", str(duration)])
        
        # 视频编码参数
        command.extend([
            "-c:v", "libx264",
            "-crf", str(encode_params["crf"]),
            "-preset", encode_params["preset"],
            "-maxrate", encode_params["max_bitrate"],
            "-bufsize", f"{int(float(encode_params['max_bitrate'].rstrip('k')) * 2)}k",
            "-pix_fmt", encode_params["pixel_format"]
        ])
        
        # 可选的调谐参数
        if "tune" in encode_params:
            command.extend(["-tune", encode_params["tune"]])
        
        # 音频参数（保持不变或轻度压缩）
        command.extend(["-c:a", "aac", "-b:a", "128k"])
        
        # 线程设置
        max_threads = self.config["max_threads"]
        if max_threads > 0:
            command.extend(["-threads", str(max_threads)])
        
        # 快速启动设置
        if self.config["fast_start"]:
            command.extend(["-movflags", "+faststart"])
        
        # 自适应量化
        adaptive_quant = self.config["adaptive_quantization"]
        if adaptive_quant != "off":
            command.extend(["-aq-mode", "2"])  # 使用方差AQ
        
        # 输出文件
        command.append(output_path)
        
        return command
    
    def _segment_based_compression(self,
                                 video_path: str,
                                 output_path: str,
                                 scenes: List[Dict[str, Any]],
                                 video_info: Dict[str, Any],
                                 target_bitrate: float) -> Dict[str, Any]:
        """基于场景的分段压缩
        
        为每个场景选择适当的压缩级别，并分别压缩
        
        Args:
            video_path: 源视频文件路径
            output_path: 输出文件路径
            scenes: 场景列表
            video_info: 视频信息
            target_bitrate: 目标比特率
            
        Returns:
            Dict[str, Any]: 压缩结果
        """
        # 基础压缩级别（根据目标比特率相对于原始比特率的比例确定）
        ratio = target_bitrate / video_info['bitrate']
        
        if ratio >= 0.9:
            base_level = CompressionLevel.MINIMAL
        elif ratio >= 0.7:
            base_level = CompressionLevel.LOW
        elif ratio >= 0.5:
            base_level = CompressionLevel.MEDIUM
        elif ratio >= 0.3:
            base_level = CompressionLevel.HIGH
        else:
            base_level = CompressionLevel.EXTREME
        
        logger.info(f"基础压缩级别: {base_level.name}")
        
        # 临时目录
        temp_dir = self.config["temp_directory"] or tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成分段压缩文件列表
        segment_files = []
        segment_file_list = os.path.join(temp_dir, "segments.txt")
        
        try:
            # 处理每个场景
            for i, scene in enumerate(scenes):
                # 选择压缩级别
                level = self._select_compression_level(scene, base_level)
                logger.debug(f"场景 {i}: {level.name} 压缩级别")
                
                # 获取编码参数
                encode_params = self._get_profile_for_level(level, target_bitrate)
                
                # 分段压缩
                segment_path = os.path.join(temp_dir, f"segment_{i:04d}.mp4")
                segment_files.append(segment_path)
                
                # 构建FFmpeg命令
                command = self._build_ffmpeg_command(
                    video_path, segment_path, encode_params,
                    start_time=scene.get("start_time"),
                    duration=scene.get("duration")
                )
                
                # 执行压缩
                logger.debug(f"压缩段 {i}: {' '.join(command)}")
                subprocess.run(command, check=True, capture_output=True)
                
                # 将段添加到文件列表
                with open(segment_file_list, "a", encoding="utf-8") as f:
                    f.write(f"file '{segment_path}'\n")
            
            # 合并所有段
            concat_command = [
                self.ffmpeg_path, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", segment_file_list,
                "-c", "copy",
                output_path
            ]
            
            logger.debug(f"合并段: {' '.join(concat_command)}")
            subprocess.run(concat_command, check=True, capture_output=True)
            
            return {
                'method': 'segment_based',
                'segments': len(scenes),
                'base_level': base_level.name
            }
            
        finally:
            # 清理临时文件
            for file in segment_files:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except:
                        pass
            
            if os.path.exists(segment_file_list):
                try:
                    os.remove(segment_file_list)
                except:
                    pass
    
    def _global_compression(self,
                          video_path: str,
                          output_path: str,
                          video_info: Dict[str, Any],
                          target_bitrate: float) -> Dict[str, Any]:
        """全局压缩处理
        
        使用统一的参数压缩整个视频
        
        Args:
            video_path: 源视频文件路径
            output_path: 输出文件路径
            video_info: 视频信息
            target_bitrate: 目标比特率
            
        Returns:
            Dict[str, Any]: 压缩结果
        """
        # 确定压缩级别
        ratio = target_bitrate / video_info['bitrate']
        
        if ratio >= 0.9:
            level = CompressionLevel.MINIMAL
        elif ratio >= 0.7:
            level = CompressionLevel.LOW
        elif ratio >= 0.5:
            level = CompressionLevel.MEDIUM
        elif ratio >= 0.3:
            level = CompressionLevel.HIGH
        else:
            level = CompressionLevel.EXTREME
        
        logger.info(f"全局压缩级别: {level.name}")
        
        # 获取编码参数
        encode_params = self._get_profile_for_level(level, target_bitrate)
        
        # 构建命令
        command = self._build_ffmpeg_command(video_path, output_path, encode_params)
        
        # 执行压缩
        logger.debug(f"全局压缩: {' '.join(command)}")
        subprocess.run(command, check=True, capture_output=True)
        
        return {
            'method': 'global',
            'level': level.name
        }


def compress_video(video_path: str, 
                 output_path: str, 
                 scene_data: Optional[List[Dict[str, Any]]] = None,
                 target_size: Optional[Union[int, float, str]] = None,
                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """压缩视频文件
    
    Args:
        video_path: 源视频文件路径
        output_path: 输出文件路径
        scene_data: 场景数据（可选）
        target_size: 目标大小
        config: 配置参数
        
    Returns:
        Dict[str, Any]: 压缩结果
    """
    compressor = SmartCompressor(config)
    return compressor.dynamic_compress(
        video_path, output_path, scene_data, target_size
    ) 