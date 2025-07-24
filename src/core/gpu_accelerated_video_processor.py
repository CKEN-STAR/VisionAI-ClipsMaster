#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU加速视频处理器
实现GPU/CPU自动检测和切换机制，优化视频处理工作流程
"""

import os
import sys
import time
import json
import logging
import subprocess
import tempfile
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# GPU相关导入
try:
    import torch
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """处理配置"""
    use_gpu: bool = True
    gpu_device_id: int = 0
    batch_size: int = 4
    memory_limit_gb: float = 3.8
    precision: str = "fp16"  # fp16, fp32
    enable_tensorrt: bool = False
    fallback_to_cpu: bool = True

@dataclass
class PerformanceMetrics:
    """性能指标"""
    processing_time: float = 0.0
    gpu_utilization: float = 0.0
    memory_usage: float = 0.0
    frames_per_second: float = 0.0
    gpu_memory_used: float = 0.0
    cpu_usage: float = 0.0

class GPUAcceleratedVideoProcessor:
    """GPU加速视频处理器"""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        初始化GPU加速视频处理器
        
        Args:
            config: 处理配置
        """
        self.config = config or ProcessingConfig()
        self.device = None
        self.gpu_available = False
        self.performance_metrics = PerformanceMetrics()
        
        # 初始化设备
        self._initialize_device()
        
        # 初始化处理器
        self._initialize_processors()
        
        # 性能监控
        self.monitoring_active = False
        self.monitor_thread = None
        
        logger.info(f"GPU加速视频处理器初始化完成 - 设备: {self.device}")
    
    def _initialize_device(self):
        """初始化计算设备"""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch不可用，使用CPU模式")
            self.device = torch.device("cpu")
            self.gpu_available = False
            self.config.use_gpu = False
            return
        
        # 检查GPU可用性
        if self.config.use_gpu and torch.cuda.is_available():
            try:
                # 检查指定的GPU设备
                if self.config.gpu_device_id < torch.cuda.device_count():
                    self.device = torch.device(f"cuda:{self.config.gpu_device_id}")
                    
                    # 检查GPU内存
                    gpu_memory = torch.cuda.get_device_properties(self.config.gpu_device_id).total_memory
                    gpu_memory_gb = gpu_memory / (1024**3)
                    
                    if gpu_memory_gb >= self.config.memory_limit_gb:
                        self.gpu_available = True
                        logger.info(f"使用GPU设备: {torch.cuda.get_device_name(self.config.gpu_device_id)}")
                        logger.info(f"GPU内存: {gpu_memory_gb:.1f}GB")
                    else:
                        logger.warning(f"GPU内存不足: {gpu_memory_gb:.1f}GB < {self.config.memory_limit_gb}GB")
                        self._fallback_to_cpu()
                else:
                    logger.warning(f"GPU设备ID {self.config.gpu_device_id} 不存在")
                    self._fallback_to_cpu()
                    
            except Exception as e:
                logger.error(f"GPU初始化失败: {e}")
                self._fallback_to_cpu()
        else:
            self._fallback_to_cpu()
    
    def _fallback_to_cpu(self):
        """回退到CPU模式"""
        if self.config.fallback_to_cpu:
            self.device = torch.device("cpu")
            self.gpu_available = False
            self.config.use_gpu = False
            logger.info("回退到CPU模式")
        else:
            raise RuntimeError("GPU不可用且未启用CPU回退")
    
    def _initialize_processors(self):
        """初始化处理器"""
        # 视频解码器
        self.video_decoder = self._create_video_decoder()
        
        # 视频编码器
        self.video_encoder = self._create_video_encoder()
        
        # 帧处理器
        self.frame_processor = self._create_frame_processor()
        
        # 字幕对齐器
        self.subtitle_aligner = self._create_subtitle_aligner()
    
    def _create_video_decoder(self):
        """创建视频解码器"""
        if self.gpu_available and OPENCV_AVAILABLE:
            return GPUVideoDecoder(self.device, self.config)
        else:
            return CPUVideoDecoder(self.config)
    
    def _create_video_encoder(self):
        """创建视频编码器"""
        if self.gpu_available:
            return GPUVideoEncoder(self.device, self.config)
        else:
            return CPUVideoEncoder(self.config)
    
    def _create_frame_processor(self):
        """创建帧处理器"""
        if self.gpu_available:
            return GPUFrameProcessor(self.device, self.config)
        else:
            return CPUFrameProcessor(self.config)
    
    def _create_subtitle_aligner(self):
        """创建字幕对齐器"""
        if self.gpu_available:
            return GPUSubtitleAligner(self.device, self.config)
        else:
            return CPUSubtitleAligner(self.config)
    
    def process_video_workflow(self, 
                              video_path: str, 
                              srt_path: str, 
                              output_path: str,
                              progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        处理完整的视频工作流程
        
        Args:
            video_path: 原视频路径
            srt_path: 新字幕文件路径
            output_path: 输出视频路径
            progress_callback: 进度回调函数
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        
        try:
            # 启动性能监控
            self.start_performance_monitoring()
            
            # 1. 解析字幕文件
            if progress_callback:
                progress_callback(10, "解析字幕文件...")
            
            subtitle_segments = self._parse_subtitle_file(srt_path)
            
            # 2. 视频解码和分析
            if progress_callback:
                progress_callback(20, "分析视频文件...")
            
            video_info = self._analyze_video(video_path)
            
            # 3. 字幕时间轴对齐
            if progress_callback:
                progress_callback(30, "对齐字幕时间轴...")
            
            aligned_segments = self.subtitle_aligner.align_subtitles(
                subtitle_segments, video_info
            )
            
            # 4. 视频片段切割
            if progress_callback:
                progress_callback(50, "切割视频片段...")
            
            video_segments = self._extract_video_segments(
                video_path, aligned_segments, progress_callback
            )
            
            # 5. 视频片段拼接
            if progress_callback:
                progress_callback(80, "拼接视频片段...")
            
            final_video = self._concatenate_video_segments(
                video_segments, output_path, progress_callback
            )
            
            # 6. 后处理和优化
            if progress_callback:
                progress_callback(95, "后处理优化...")
            
            self._post_process_video(final_video, output_path)
            
            # 停止性能监控
            self.stop_performance_monitoring()
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "output_path": output_path,
                "processing_time": processing_time,
                "performance_metrics": self.get_performance_metrics(),
                "segments_processed": len(video_segments),
                "device_used": str(self.device),
                "gpu_accelerated": self.gpu_available
            }
            
            if progress_callback:
                progress_callback(100, "处理完成")
            
            logger.info(f"视频处理完成: {processing_time:.2f}秒")
            return result
            
        except Exception as e:
            self.stop_performance_monitoring()
            logger.error(f"视频处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "device_used": str(self.device)
            }
    
    def _parse_subtitle_file(self, srt_path: str) -> List[Dict[str, Any]]:
        """解析字幕文件"""
        segments = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的SRT解析
            blocks = content.strip().split('\n\n')
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 解析时间码
                    time_line = lines[1]
                    if ' --> ' in time_line:
                        start_time, end_time = time_line.split(' --> ')
                        
                        # 解析文本
                        text = '\n'.join(lines[2:])
                        
                        segments.append({
                            'start_time': self._parse_time_code(start_time),
                            'end_time': self._parse_time_code(end_time),
                            'text': text
                        })
            
            logger.info(f"解析字幕文件: {len(segments)}个片段")
            return segments
            
        except Exception as e:
            logger.error(f"解析字幕文件失败: {e}")
            raise
    
    def _parse_time_code(self, time_str: str) -> float:
        """解析时间码为秒数"""
        try:
            # 格式: HH:MM:SS,mmm
            time_str = time_str.strip().replace(',', '.')
            parts = time_str.split(':')
            
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception as e:
            logger.error(f"解析时间码失败: {time_str} - {e}")
            return 0.0
    
    def _analyze_video(self, video_path: str) -> Dict[str, Any]:
        """分析视频文件"""
        try:
            if OPENCV_AVAILABLE:
                cap = cv2.VideoCapture(video_path)
                
                video_info = {
                    'fps': cap.get(cv2.CAP_PROP_FPS),
                    'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
                }
                
                cap.release()
                
                logger.info(f"视频信息: {video_info}")
                return video_info
            else:
                # 使用FFprobe作为备选
                return self._analyze_video_with_ffprobe(video_path)
                
        except Exception as e:
            logger.error(f"视频分析失败: {e}")
            raise
    
    def _analyze_video_with_ffprobe(self, video_path: str) -> Dict[str, Any]:
        """使用FFprobe分析视频"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # 查找视频流
                video_stream = None
                for stream in data['streams']:
                    if stream['codec_type'] == 'video':
                        video_stream = stream
                        break
                
                if video_stream:
                    return {
                        'fps': eval(video_stream.get('r_frame_rate', '25/1')),
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'duration': float(data['format'].get('duration', 0))
                    }
            
            raise RuntimeError("无法获取视频信息")
            
        except Exception as e:
            logger.error(f"FFprobe分析失败: {e}")
            raise

    def _extract_video_segments(self, video_path: str, segments: List[Dict],
                               progress_callback: Optional[callable] = None) -> List[str]:
        """提取视频片段"""
        segment_files = []
        total_segments = len(segments)

        for i, segment in enumerate(segments):
            try:
                # 更新进度
                if progress_callback:
                    progress = 50 + int((i / total_segments) * 25)
                    progress_callback(progress, f"处理片段 {i+1}/{total_segments}")

                # 提取片段
                segment_file = self.video_decoder.extract_segment(
                    video_path, segment['start_time'], segment['end_time']
                )

                if segment_file:
                    segment_files.append(segment_file)

            except Exception as e:
                logger.error(f"提取片段失败: {e}")
                continue

        logger.info(f"成功提取 {len(segment_files)} 个视频片段")
        return segment_files

    def _concatenate_video_segments(self, segment_files: List[str], output_path: str,
                                   progress_callback: Optional[callable] = None) -> str:
        """拼接视频片段"""
        try:
            if progress_callback:
                progress_callback(85, "拼接视频片段...")

            result = self.video_encoder.concatenate_segments(segment_files, output_path)

            # 清理临时文件
            for segment_file in segment_files:
                try:
                    os.remove(segment_file)
                except:
                    pass

            return result

        except Exception as e:
            logger.error(f"拼接视频失败: {e}")
            raise

    def _post_process_video(self, video_path: str, output_path: str):
        """后处理视频"""
        try:
            # 如果需要，可以在这里添加后处理逻辑
            # 例如：视频优化、格式转换等
            pass

        except Exception as e:
            logger.error(f"后处理失败: {e}")

    def start_performance_monitoring(self):
        """启动性能监控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
            self.monitor_thread.start()

    def stop_performance_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _monitor_performance(self):
        """性能监控循环"""
        import psutil

        while self.monitoring_active:
            try:
                # CPU使用率
                self.performance_metrics.cpu_usage = psutil.cpu_percent(interval=0.1)

                # 内存使用
                memory = psutil.virtual_memory()
                self.performance_metrics.memory_usage = memory.percent

                # GPU监控
                if self.gpu_available and TORCH_AVAILABLE:
                    try:
                        # GPU内存使用
                        gpu_memory = torch.cuda.memory_allocated(self.device) / (1024**3)
                        self.performance_metrics.gpu_memory_used = gpu_memory

                        # GPU利用率（简化版本）
                        self.performance_metrics.gpu_utilization = min(gpu_memory / 4.0 * 100, 100)

                    except Exception as e:
                        logger.debug(f"GPU监控失败: {e}")

                time.sleep(1)

            except Exception as e:
                logger.debug(f"性能监控错误: {e}")
                time.sleep(5)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "processing_time": self.performance_metrics.processing_time,
            "gpu_utilization": self.performance_metrics.gpu_utilization,
            "memory_usage": self.performance_metrics.memory_usage,
            "frames_per_second": self.performance_metrics.frames_per_second,
            "gpu_memory_used": self.performance_metrics.gpu_memory_used,
            "cpu_usage": self.performance_metrics.cpu_usage,
            "device_used": str(self.device),
            "gpu_available": self.gpu_available
        }

    def get_device_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        status = {
            "device": str(self.device),
            "gpu_available": self.gpu_available,
            "torch_available": TORCH_AVAILABLE,
            "opencv_available": OPENCV_AVAILABLE,
            "cupy_available": CUPY_AVAILABLE
        }

        if self.gpu_available and TORCH_AVAILABLE:
            try:
                status.update({
                    "gpu_name": torch.cuda.get_device_name(self.config.gpu_device_id),
                    "gpu_memory_total": torch.cuda.get_device_properties(self.config.gpu_device_id).total_memory / (1024**3),
                    "gpu_memory_allocated": torch.cuda.memory_allocated(self.device) / (1024**3),
                    "gpu_memory_cached": torch.cuda.memory_reserved(self.device) / (1024**3)
                })
            except Exception as e:
                logger.debug(f"获取GPU状态失败: {e}")

        return status
