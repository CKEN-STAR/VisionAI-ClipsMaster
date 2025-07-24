#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU视频处理组件
包含GPU加速的视频解码、编码、帧处理和字幕对齐组件
"""

import os
import sys
import time
import logging
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# GPU相关导入
try:
    import torch
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPUVideoDecoder:
    """GPU视频解码器"""
    
    def __init__(self, device: torch.device, config):
        self.device = device
        self.config = config
        self.temp_dir = tempfile.mkdtemp()
        
        # 检查GPU硬件加速支持
        self.hw_accel_available = self._check_hw_acceleration()
        
        logger.info(f"GPU视频解码器初始化 - 硬件加速: {self.hw_accel_available}")
    
    def _check_hw_acceleration(self) -> bool:
        """检查硬件加速支持"""
        try:
            # 检查NVIDIA GPU编码器
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                return 'h264_nvenc' in output or 'hevc_nvenc' in output
            
            return False
            
        except Exception as e:
            logger.debug(f"硬件加速检查失败: {e}")
            return False
    
    def extract_segment(self, video_path: str, start_time: float, end_time: float) -> str:
        """提取视频片段"""
        try:
            # 生成临时文件名
            segment_file = os.path.join(
                self.temp_dir, 
                f"segment_{int(start_time*1000)}_{int(end_time*1000)}.mp4"
            )
            
            if self.hw_accel_available:
                return self._extract_segment_gpu(video_path, start_time, end_time, segment_file)
            else:
                return self._extract_segment_cpu(video_path, start_time, end_time, segment_file)
                
        except Exception as e:
            logger.error(f"视频片段提取失败: {e}")
            raise
    
    def _extract_segment_gpu(self, video_path: str, start_time: float, 
                           end_time: float, segment_file: str) -> str:
        """GPU加速提取片段"""
        try:
            # 使用NVIDIA GPU硬件加速
            cmd = [
                'ffmpeg', '-y',
                '-hwaccel', 'cuda',
                '-hwaccel_output_format', 'cuda',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-c:v', 'h264_nvenc',
                '-preset', 'fast',
                '-c:a', 'copy',
                '-avoid_negative_ts', 'make_zero',
                segment_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(segment_file):
                logger.debug(f"GPU提取片段成功: {segment_file}")
                return segment_file
            else:
                logger.warning(f"GPU提取失败，回退到CPU: {result.stderr}")
                return self._extract_segment_cpu(video_path, start_time, end_time, segment_file)
                
        except Exception as e:
            logger.error(f"GPU片段提取异常: {e}")
            return self._extract_segment_cpu(video_path, start_time, end_time, segment_file)
    
    def _extract_segment_cpu(self, video_path: str, start_time: float, 
                           end_time: float, segment_file: str) -> str:
        """CPU模式提取片段"""
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'copy',
            '-avoid_negative_ts', 'make_zero',
            segment_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(segment_file):
            logger.debug(f"CPU提取片段成功: {segment_file}")
            return segment_file
        else:
            raise RuntimeError(f"视频片段提取失败: {result.stderr}")
    
    def __del__(self):
        """清理临时目录"""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass


class CPUVideoDecoder:
    """CPU视频解码器"""
    
    def __init__(self, config):
        self.config = config
        self.temp_dir = tempfile.mkdtemp()
        
        logger.info("CPU视频解码器初始化")
    
    def extract_segment(self, video_path: str, start_time: float, end_time: float) -> str:
        """提取视频片段"""
        segment_file = os.path.join(
            self.temp_dir, 
            f"segment_{int(start_time*1000)}_{int(end_time*1000)}.mp4"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(end_time - start_time),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-avoid_negative_ts', 'make_zero',
            segment_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(segment_file):
            logger.debug(f"CPU提取片段成功: {segment_file}")
            return segment_file
        else:
            raise RuntimeError(f"视频片段提取失败: {result.stderr}")
    
    def __del__(self):
        """清理临时目录"""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass


class GPUVideoEncoder:
    """GPU视频编码器"""
    
    def __init__(self, device: torch.device, config):
        self.device = device
        self.config = config
        
        # 检查GPU编码器支持
        self.hw_encode_available = self._check_hw_encoding()
        
        logger.info(f"GPU视频编码器初始化 - 硬件编码: {self.hw_encode_available}")
    
    def _check_hw_encoding(self) -> bool:
        """检查硬件编码支持"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                return 'h264_nvenc' in output
            
            return False
            
        except Exception as e:
            logger.debug(f"硬件编码检查失败: {e}")
            return False
    
    def concatenate_segments(self, segment_files: List[str], output_path: str) -> str:
        """拼接视频片段"""
        try:
            if not segment_files:
                raise ValueError("没有视频片段可拼接")
            
            # 创建文件列表
            list_file = output_path + '.list'
            with open(list_file, 'w', encoding='utf-8') as f:
                for segment_file in segment_files:
                    # 确保路径格式正确
                    normalized_path = os.path.normpath(segment_file).replace('\\', '/')
                    f.write(f"file '{normalized_path}'\n")
            
            try:
                if self.hw_encode_available:
                    return self._concatenate_gpu(list_file, output_path)
                else:
                    return self._concatenate_cpu(list_file, output_path)
            finally:
                # 清理临时文件
                try:
                    os.remove(list_file)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"视频拼接失败: {e}")
            raise
    
    def _concatenate_gpu(self, list_file: str, output_path: str) -> str:
        """GPU加速拼接"""
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c:v', 'h264_nvenc',
            '-preset', 'fast',
            '-c:a', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"GPU拼接成功: {output_path}")
            return output_path
        else:
            logger.warning(f"GPU拼接失败，回退到CPU: {result.stderr}")
            return self._concatenate_cpu(list_file, output_path)
    
    def _concatenate_cpu(self, list_file: str, output_path: str) -> str:
        """CPU模式拼接"""
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(output_path):
            logger.info(f"CPU拼接成功: {output_path}")
            return output_path
        else:
            raise RuntimeError(f"视频拼接失败: {result.stderr}")


class CPUVideoEncoder:
    """CPU视频编码器"""
    
    def __init__(self, config):
        self.config = config
        
        logger.info("CPU视频编码器初始化")
    
    def concatenate_segments(self, segment_files: List[str], output_path: str) -> str:
        """拼接视频片段"""
        if not segment_files:
            raise ValueError("没有视频片段可拼接")
        
        # 创建文件列表
        list_file = output_path + '.list'
        with open(list_file, 'w', encoding='utf-8') as f:
            for segment_file in segment_files:
                normalized_path = os.path.normpath(segment_file).replace('\\', '/')
                f.write(f"file '{normalized_path}'\n")
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"CPU拼接成功: {output_path}")
                return output_path
            else:
                raise RuntimeError(f"视频拼接失败: {result.stderr}")
                
        finally:
            try:
                os.remove(list_file)
            except:
                pass


class GPUFrameProcessor:
    """GPU帧处理器"""

    def __init__(self, device: torch.device, config):
        self.device = device
        self.config = config

        # 初始化GPU处理管道
        if TORCH_AVAILABLE:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.ToTensor()
            ])

        logger.info(f"GPU帧处理器初始化 - 设备: {device}")

    def process_frames(self, frames: torch.Tensor) -> torch.Tensor:
        """处理视频帧"""
        try:
            if not TORCH_AVAILABLE:
                return frames

            # 将帧数据移动到GPU
            frames = frames.to(self.device)

            # GPU加速的帧处理操作
            with torch.no_grad():
                # 色彩空间转换
                if frames.dim() == 4:  # [batch, channels, height, width]
                    processed_frames = self._apply_gpu_filters(frames)
                else:
                    processed_frames = frames

            return processed_frames

        except Exception as e:
            logger.error(f"GPU帧处理失败: {e}")
            return frames.cpu()

    def _apply_gpu_filters(self, frames: torch.Tensor) -> torch.Tensor:
        """应用GPU滤镜"""
        try:
            # 亮度调整
            frames = torch.clamp(frames * 1.1, 0, 1)

            # 对比度调整
            mean = torch.mean(frames, dim=[2, 3], keepdim=True)
            frames = torch.clamp((frames - mean) * 1.2 + mean, 0, 1)

            return frames

        except Exception as e:
            logger.error(f"GPU滤镜应用失败: {e}")
            return frames

    def resize_frames(self, frames: torch.Tensor, target_size: Tuple[int, int]) -> torch.Tensor:
        """GPU加速帧缩放"""
        try:
            if not TORCH_AVAILABLE:
                return frames

            frames = frames.to(self.device)

            # 使用双线性插值进行缩放
            resized = torch.nn.functional.interpolate(
                frames, size=target_size, mode='bilinear', align_corners=False
            )

            return resized

        except Exception as e:
            logger.error(f"GPU帧缩放失败: {e}")
            return frames


class CPUFrameProcessor:
    """CPU帧处理器"""

    def __init__(self, config):
        self.config = config

        logger.info("CPU帧处理器初始化")

    def process_frames(self, frames: np.ndarray) -> np.ndarray:
        """处理视频帧"""
        try:
            if not OPENCV_AVAILABLE:
                return frames

            # CPU模式的帧处理
            processed_frames = self._apply_cpu_filters(frames)

            return processed_frames

        except Exception as e:
            logger.error(f"CPU帧处理失败: {e}")
            return frames

    def _apply_cpu_filters(self, frames: np.ndarray) -> np.ndarray:
        """应用CPU滤镜"""
        try:
            # 亮度和对比度调整
            alpha = 1.2  # 对比度
            beta = 10    # 亮度

            adjusted = cv2.convertScaleAbs(frames, alpha=alpha, beta=beta)

            return adjusted

        except Exception as e:
            logger.error(f"CPU滤镜应用失败: {e}")
            return frames

    def resize_frames(self, frames: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """CPU帧缩放"""
        try:
            if not OPENCV_AVAILABLE:
                return frames

            resized = cv2.resize(frames, target_size, interpolation=cv2.INTER_LINEAR)

            return resized

        except Exception as e:
            logger.error(f"CPU帧缩放失败: {e}")
            return frames


class GPUSubtitleAligner:
    """GPU字幕对齐器"""

    def __init__(self, device: torch.device, config):
        self.device = device
        self.config = config

        logger.info(f"GPU字幕对齐器初始化 - 设备: {device}")

    def align_subtitles(self, segments: List[Dict], video_info: Dict) -> List[Dict]:
        """对齐字幕时间轴"""
        try:
            if not segments:
                return segments

            # GPU加速的时间轴对齐算法
            aligned_segments = []

            # 提取时间信息
            start_times = [seg['start_time'] for seg in segments]
            end_times = [seg['end_time'] for seg in segments]

            if TORCH_AVAILABLE:
                # 使用GPU进行并行计算
                start_tensor = torch.tensor(start_times, device=self.device, dtype=torch.float32)
                end_tensor = torch.tensor(end_times, device=self.device, dtype=torch.float32)

                # 时间轴优化算法
                optimized_times = self._optimize_timeline_gpu(start_tensor, end_tensor, video_info)

                # 转换回CPU并构建结果
                optimized_starts = optimized_times[0].cpu().numpy()
                optimized_ends = optimized_times[1].cpu().numpy()

                for i, segment in enumerate(segments):
                    aligned_segment = {
                        'start_time': float(optimized_starts[i]),
                        'end_time': float(optimized_ends[i]),
                        'text': segment['text']
                    }
                    aligned_segments.append(aligned_segment)
            else:
                # 回退到CPU模式
                aligned_segments = self._align_subtitles_cpu(segments, video_info)

            logger.info(f"GPU字幕对齐完成: {len(aligned_segments)}个片段")
            return aligned_segments

        except Exception as e:
            logger.error(f"GPU字幕对齐失败: {e}")
            return self._align_subtitles_cpu(segments, video_info)

    def _optimize_timeline_gpu(self, start_times: torch.Tensor, end_times: torch.Tensor,
                              video_info: Dict) -> Tuple[torch.Tensor, torch.Tensor]:
        """GPU加速的时间轴优化"""
        try:
            # 计算片段持续时间
            durations = end_times - start_times

            # 最小间隔约束
            min_gap = 0.1  # 100ms最小间隔

            # 调整重叠片段
            for i in range(len(start_times) - 1):
                if start_times[i + 1] < end_times[i]:
                    # 有重叠，调整时间
                    overlap = end_times[i] - start_times[i + 1]
                    adjustment = overlap / 2 + min_gap / 2

                    end_times[i] = end_times[i] - adjustment
                    start_times[i + 1] = start_times[i + 1] + adjustment

            # 确保时间在视频范围内
            video_duration = video_info.get('duration', float('inf'))
            end_times = torch.clamp(end_times, 0, video_duration)
            start_times = torch.clamp(start_times, 0, video_duration)

            return start_times, end_times

        except Exception as e:
            logger.error(f"GPU时间轴优化失败: {e}")
            return start_times, end_times

    def _align_subtitles_cpu(self, segments: List[Dict], video_info: Dict) -> List[Dict]:
        """CPU模式字幕对齐"""
        # 简单的CPU对齐算法
        aligned_segments = []

        for segment in segments:
            aligned_segment = {
                'start_time': segment['start_time'],
                'end_time': segment['end_time'],
                'text': segment['text']
            }
            aligned_segments.append(aligned_segment)

        return aligned_segments


class CPUSubtitleAligner:
    """CPU字幕对齐器"""

    def __init__(self, config):
        self.config = config

        logger.info("CPU字幕对齐器初始化")

    def align_subtitles(self, segments: List[Dict], video_info: Dict) -> List[Dict]:
        """对齐字幕时间轴"""
        try:
            if not segments:
                return segments

            aligned_segments = []
            video_duration = video_info.get('duration', float('inf'))

            # CPU模式的时间轴对齐
            for i, segment in enumerate(segments):
                start_time = max(0, segment['start_time'])
                end_time = min(video_duration, segment['end_time'])

                # 确保时间有效性
                if end_time <= start_time:
                    end_time = start_time + 1.0  # 最少1秒

                aligned_segment = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': segment['text']
                }

                aligned_segments.append(aligned_segment)

            logger.info(f"CPU字幕对齐完成: {len(aligned_segments)}个片段")
            return aligned_segments

        except Exception as e:
            logger.error(f"CPU字幕对齐失败: {e}")
            return segments
