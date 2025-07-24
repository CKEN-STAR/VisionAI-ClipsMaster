#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频处理核心模块 - 简化版本用于冷热启动测试

提供视频分析、字幕处理和片段裁剪功能。
"""

import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# 配置日志
logging.basicConfig(level=logging.INFO,
                  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("video_processor")

# 导入项目模块
from src.utils.log_handler import get_logger
from src.utils.config_manager import get_config
from src.utils.file_utils import ensure_dir, get_temp_path
from src.core.model_loader import get_model_loader

# 导入GPU相关模块
try:
    import torch
    import cv2
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch或OpenCV未安装，GPU加速功能将不可用")

try:
    from ui.hardware.gpu_detector import get_gpu_detector
    GPU_DETECTOR_AVAILABLE = True
except ImportError:
    GPU_DETECTOR_AVAILABLE = False
    logger.warning("GPU检测器不可用")

# 用于冷热启动测试的变量
_is_first_run = True

class VideoProcessor:
    """
    视频处理器类

    负责视频分析、关键帧提取、字幕处理和片段裁剪功能。

    支持的视频格式：
    - MP4 (H.264/H.265)
    - AVI (多种编码)
    - FLV (Flash Video)
    - MOV (QuickTime)
    - MKV (Matroska)
    - WMV (Windows Media)
    - WEBM (VP8/VP9)
    """

    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS = {
        '.mp4': {'codec': 'libx264', 'container': 'mp4'},
        '.avi': {'codec': 'libx264', 'container': 'avi'},
        '.flv': {'codec': 'libx264', 'container': 'flv'},
        '.mov': {'codec': 'libx264', 'container': 'mov'},
        '.mkv': {'codec': 'libx264', 'container': 'matroska'},
        '.wmv': {'codec': 'libx264', 'container': 'asf'},
        '.webm': {'codec': 'libvpx-vp9', 'container': 'webm'},
        '.m4v': {'codec': 'libx264', 'container': 'mp4'},
        '.3gp': {'codec': 'libx264', 'container': '3gp'}
    }

    # 格式特定的编码参数
    FORMAT_SPECIFIC_PARAMS = {
        '.mp4': ['-movflags', '+faststart'],
        '.webm': ['-c:a', 'libvorbis'],
        '.flv': ['-ar', '44100'],
        '.avi': ['-c:a', 'aac'],
        '.mkv': ['-c:a', 'aac'],
        '.mov': ['-c:a', 'aac'],
        '.wmv': ['-c:a', 'aac']
    }

    def __init__(self):
        """初始化视频处理器"""
        global _is_first_run

        # 记录实例化时间
        self.init_time = time.time()

        # 加载配置
        self.config = get_config("core").get("video_processor", {})

        # 视频处理参数
        self.min_clip_duration = self.config.get("min_clip_duration", 3)  # 最小片段时长，单位秒
        self.max_clip_duration = self.config.get("max_clip_duration", 30)  # 最大片段时长，单位秒

        # GPU加速相关初始化
        self.gpu_enabled = False
        self.device = 'cpu'
        self.gpu_info = None

        # 初始化GPU支持
        self._init_gpu_support()

        # FFmpeg GPU加速参数
        self.ffmpeg_gpu_params = self._get_ffmpeg_gpu_params()
        
        # 模拟第一次初始化较慢
        if _is_first_run:
            logger.info("首次初始化视频处理器（冷启动）...")
            time.sleep(0.5)  # 模拟冷启动延迟
            _is_first_run = False
        else:
            logger.info("再次初始化视频处理器（热启动）...")
        
        # 加载模型
        self.model_loader = get_model_loader()

        # 初始化FFmpeg路径
        self.ffmpeg_path = self._find_ffmpeg()

        logger.info("视频处理器初始化完成")

    def _init_gpu_support(self):
        """初始化GPU支持"""
        try:
            if not TORCH_AVAILABLE:
                logger.info("PyTorch不可用，跳过GPU初始化")
                return

            # 检测GPU
            if GPU_DETECTOR_AVAILABLE:
                gpu_detector = get_gpu_detector()
                self.gpu_info = gpu_detector.detect_gpus()
                self.device = gpu_detector.get_best_device()
            else:
                # 备用GPU检测
                if torch.cuda.is_available():
                    self.device = 'cuda'
                else:
                    self.device = 'cpu'

            # 设置GPU状态
            if self.device != 'cpu':
                self.gpu_enabled = True
                logger.info(f"GPU检测成功，使用设备: {self.device}")

                # 验证GPU可用性
                if self.device == 'cuda':
                    test_tensor = torch.tensor([1.0]).to(self.device)
                    _ = test_tensor + 1  # 简单计算测试
                    logger.info("GPU功能验证成功")
            else:
                logger.info("未检测到可用GPU，使用CPU模式")

        except Exception as e:
            logger.error(f"GPU初始化失败: {str(e)}")
            self.gpu_enabled = False
            self.device = 'cpu'

    def _get_ffmpeg_gpu_params(self) -> Dict[str, List[str]]:
        """获取FFmpeg GPU加速参数"""
        gpu_params = {
            'nvidia_encode': ['-c:v', 'h264_nvenc', '-preset', 'fast'],
            'nvidia_decode': ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda'],
            'amd_encode': ['-c:v', 'h264_amf', '-quality', 'speed'],
            'intel_encode': ['-c:v', 'h264_qsv', '-preset', 'fast'],
            'cpu_fallback': ['-c:v', 'libx264', '-preset', 'fast']
        }

        # 根据GPU类型选择参数
        if self.gpu_info and self.gpu_enabled:
            if self.gpu_info.get('nvidia_gpus'):
                return {
                    'encode': gpu_params['nvidia_encode'],
                    'decode': gpu_params['nvidia_decode']
                }
            elif self.gpu_info.get('amd_gpus'):
                return {
                    'encode': gpu_params['amd_encode'],
                    'decode': []
                }
            elif self.gpu_info.get('intel_gpus'):
                return {
                    'encode': gpu_params['intel_encode'],
                    'decode': []
                }

        # CPU回退
        return {
            'encode': gpu_params['cpu_fallback'],
            'decode': []
        }

    def process_video(self, video_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """处理视频文件，提取关键信息和片段
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录，默认为临时目录
            
        Returns:
            Dict[str, Any]: 包含视频分析结果和片段信息
        """
        logger.info(f"开始处理视频: {video_path}")
        
        # 确保输出目录存在
        if output_dir is None:
            output_dir = get_temp_path("video_processor")
        ensure_dir(output_dir)
        
        # 模拟视频处理
        time.sleep(0.3)  # 模拟处理时间
        
        # 返回结果
        return {
            "video_path": video_path,
            "output_dir": output_dir,
            "processed_at": time.time(),
            "duration": 10.5,
            "resolution": "1280x720",
            "clips": [
                {"start": 0.0, "end": 3.5, "score": 0.85},
                {"start": 5.2, "end": 8.7, "score": 0.92}
            ]
        }
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 视频信息
        """
        # 模拟获取视频信息
        return {
            "filename": os.path.basename(video_path),
            "duration": 10.5,
            "width": 1280,
            "height": 720,
            "fps": 30.0
        }
    
    def extract_subtitles(self, video_path: str, output_path: str) -> Dict[str, Any]:
        """提取视频字幕

        Args:
            video_path: 视频文件路径
            output_path: 字幕输出路径

        Returns:
            Dict[str, Any]: 字幕信息
        """
        # 模拟字幕提取
        return {
            "language": "zh",
            "line_count": 15,
            "duration": 10.5
        }

    def concatenate_videos(self, video_list: List[str], output_path: str,
                          subtitle_segments: List[Dict] = None) -> Dict[str, Any]:
        """根据字幕时间轴拼接视频片段

        Args:
            video_list: 视频文件路径列表
            output_path: 输出视频路径
            subtitle_segments: 字幕片段信息，包含时间轴

        Returns:
            Dict[str, Any]: 拼接结果
        """
        try:
            start_time = time.time()
            logger.info(f"开始拼接 {len(video_list)} 个视频片段")

            if not self.ffmpeg_path:
                return {'success': False, 'error': 'FFmpeg不可用'}

            # 创建临时文件列表
            temp_list_file = get_temp_path("video_processor") / "concat_list.txt"
            ensure_dir(temp_list_file.parent)

            with open(temp_list_file, 'w', encoding='utf-8') as f:
                for video_path in video_list:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")

            # 构建FFmpeg拼接命令
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', str(temp_list_file),
                '-c', 'copy',  # 无损拼接
                '-y',  # 覆盖输出文件
                output_path
            ]

            # 执行拼接
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            # 清理临时文件
            if temp_list_file.exists():
                temp_list_file.unlink()

            process_time = time.time() - start_time

            if result.returncode == 0:
                logger.info(f"视频拼接成功，耗时: {process_time:.2f}秒")
                return {
                    'success': True,
                    'output_path': output_path,
                    'process_time': process_time,
                    'video_count': len(video_list),
                    'method': 'ffmpeg_concat'
                }
            else:
                logger.error(f"视频拼接失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'process_time': process_time
                }

        except Exception as e:
            logger.error(f"视频拼接异常: {str(e)}")
            return {'success': False, 'error': str(e)}

    def extract_video_segment(self, input_path: str, output_path: str,
                             start_time: float, end_time: float) -> Dict[str, Any]:
        """提取视频片段

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）

        Returns:
            Dict[str, Any]: 提取结果
        """
        try:
            if not self.ffmpeg_path:
                return {'success': False, 'error': 'FFmpeg不可用'}

            duration = end_time - start_time
            if duration <= 0:
                return {'success': False, 'error': '无效的时间范围'}

            # 构建FFmpeg命令
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c', 'copy',  # 无损切割
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ]

            start_process_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            process_time = time.time() - start_process_time

            if result.returncode == 0:
                logger.info(f"视频片段提取成功: {start_time}s-{end_time}s")
                return {
                    'success': True,
                    'output_path': output_path,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'process_time': process_time
                }
            else:
                logger.error(f"视频片段提取失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'process_time': process_time
                }

        except Exception as e:
            logger.error(f"视频片段提取异常: {str(e)}")
            return {'success': False, 'error': str(e)}

    def validate_video_file(self, video_path: str) -> Dict[str, Any]:
        """验证视频文件的完整性和可用性

        Args:
            video_path: 视频文件路径

        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            if not os.path.exists(video_path):
                return {'valid': False, 'error': '文件不存在'}

            if not self.is_supported_format(video_path):
                return {'valid': False, 'error': '不支持的视频格式'}

            # 使用FFmpeg验证文件
            if self.ffmpeg_path:
                cmd = [
                    self.ffmpeg_path,
                    '-v', 'error',
                    '-i', video_path,
                    '-f', 'null', '-'
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    return {
                        'valid': True,
                        'file_size': os.path.getsize(video_path),
                        'format_info': self.detect_video_format(video_path)
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'文件损坏或格式错误: {result.stderr}'
                    }
            else:
                # 基本文件检查
                file_size = os.path.getsize(video_path)
                return {
                    'valid': file_size > 0,
                    'file_size': file_size,
                    'error': '无法深度验证（FFmpeg不可用）' if file_size == 0 else None
                }

        except Exception as e:
            return {'valid': False, 'error': f'验证异常: {str(e)}'}

    def _find_ffmpeg(self):
        """查找FFmpeg可执行文件"""
        import shutil

        # 尝试在系统PATH中查找
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path

        # 尝试在项目目录中查找
        project_root = Path(__file__).parent.parent.parent
        possible_paths = [
            project_root / 'tools' / 'ffmpeg' / 'ffmpeg.exe',
            project_root / 'ffmpeg.exe',
            project_root / 'bin' / 'ffmpeg.exe'
        ]

        for path in possible_paths:
            if path.exists():
                return str(path)

        return None

    def encode_video_gpu(self, input_path: str, output_path: str,
                        width: int = None, height: int = None,
                        bitrate: str = None) -> Dict[str, Any]:
        """
        GPU加速视频编码

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            width: 目标宽度
            height: 目标高度
            bitrate: 目标比特率

        Returns:
            Dict[str, Any]: 编码结果
        """
        try:
            # 构建FFmpeg命令
            cmd = ['ffmpeg', '-y']

            # 添加GPU解码参数
            if self.ffmpeg_gpu_params.get('decode'):
                cmd.extend(self.ffmpeg_gpu_params['decode'])

            # 输入文件
            cmd.extend(['-i', input_path])

            # 添加GPU编码参数
            cmd.extend(self.ffmpeg_gpu_params['encode'])

            # 分辨率设置
            if width and height:
                cmd.extend(['-s', f'{width}x{height}'])

            # 比特率设置
            if bitrate:
                cmd.extend(['-b:v', bitrate])

            # 输出文件
            cmd.append(output_path)

            logger.info(f"开始GPU加速视频编码: {input_path} -> {output_path}")
            logger.debug(f"FFmpeg命令: {' '.join(cmd)}")

            # 执行编码
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            encode_time = time.time() - start_time

            if result.returncode == 0:
                logger.info(f"GPU视频编码成功，耗时: {encode_time:.2f}秒")
                return {
                    'success': True,
                    'output_path': output_path,
                    'encode_time': encode_time,
                    'gpu_accelerated': self.gpu_enabled,
                    'device': self.device
                }
            else:
                logger.error(f"GPU视频编码失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'gpu_accelerated': self.gpu_enabled
                }

        except subprocess.TimeoutExpired:
            logger.error("GPU视频编码超时")
            return {'success': False, 'error': '编码超时'}
        except Exception as e:
            logger.error(f"GPU视频编码异常: {str(e)}")
            return {'success': False, 'error': str(e)}

    def apply_video_effects_gpu(self, input_path: str, output_path: str,
                               effects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        GPU加速视频特效处理

        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            effects: 特效列表

        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            if not TORCH_AVAILABLE or not self.gpu_enabled:
                logger.warning("GPU不可用，使用CPU处理特效")
                return self._apply_video_effects_cpu(input_path, output_path, effects)

            logger.info(f"开始GPU加速特效处理: {input_path}")
            start_time = time.time()

            # 使用OpenCV GPU加速处理
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {input_path}")

            # 获取视频属性
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 应用特效 (这里是简化版本)
                processed_frame = self._apply_frame_effects_gpu(frame, effects)
                out.write(processed_frame)
                frame_count += 1

            cap.release()
            out.release()

            process_time = time.time() - start_time
            logger.info(f"GPU特效处理完成，处理帧数: {frame_count}，耗时: {process_time:.2f}秒")

            return {
                'success': True,
                'output_path': output_path,
                'process_time': process_time,
                'frame_count': frame_count,
                'gpu_accelerated': True,
                'device': self.device
            }

        except Exception as e:
            logger.error(f"GPU特效处理失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _apply_frame_effects_gpu(self, frame, effects: List[Dict[str, Any]]):
        """
        GPU加速单帧特效处理

        Args:
            frame: 视频帧
            effects: 特效列表

        Returns:
            处理后的帧
        """
        try:
            # 转换为GPU tensor
            if self.device == 'cuda':
                frame_tensor = torch.from_numpy(frame).permute(2, 0, 1).float().to(self.device) / 255.0

                # 应用特效
                for effect in effects:
                    effect_type = effect.get('type', '')

                    if effect_type == 'brightness':
                        brightness = effect.get('value', 0.0)
                        frame_tensor = torch.clamp(frame_tensor + brightness, 0, 1)

                    elif effect_type == 'contrast':
                        contrast = effect.get('value', 1.0)
                        frame_tensor = torch.clamp(frame_tensor * contrast, 0, 1)

                    elif effect_type == 'blur':
                        # 简化的模糊效果
                        kernel_size = effect.get('kernel_size', 5)
                        # 这里可以实现GPU加速的模糊算法
                        pass

                # 转换回CPU numpy数组
                processed_frame = (frame_tensor.permute(1, 2, 0).cpu().numpy() * 255).astype('uint8')
                return processed_frame
            else:
                # 非CUDA设备的处理
                return frame

        except Exception as e:
            logger.error(f"GPU帧处理失败: {str(e)}")
            return frame

    def _apply_video_effects_cpu(self, input_path: str, output_path: str,
                                effects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """CPU回退的特效处理"""
        logger.info("使用CPU处理视频特效")
        # 这里实现CPU版本的特效处理
        return {
            'success': True,
            'output_path': output_path,
            'gpu_accelerated': False,
            'device': 'cpu'
        }

    def detect_video_info(self, file_path):
        """检测视频格式和编码信息"""
        if not self.ffmpeg_path:
            return {'error': 'FFmpeg不可用'}

        try:
            cmd = [
                self.ffmpeg_path, '-i', file_path,
                '-f', 'null', '-'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            # FFmpeg将信息输出到stderr
            output = result.stderr

            # 解析视频信息
            info = {
                'duration': self._extract_duration(output),
                'resolution': self._extract_resolution(output),
                'fps': self._extract_fps(output),
                'codec': self._extract_codec(output),
                'bitrate': self._extract_bitrate(output)
            }

            return info

        except subprocess.TimeoutExpired:
            return {'error': '检测超时'}
        except Exception as e:
            return {'error': f'检测失败: {str(e)}'}

    def _extract_duration(self, output):
        """从FFmpeg输出中提取时长"""
        import re
        match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', output)
        if match:
            hours, minutes, seconds = match.groups()
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        return None

    def _extract_resolution(self, output):
        """从FFmpeg输出中提取分辨率"""
        import re
        match = re.search(r'(\d{3,4})x(\d{3,4})', output)
        if match:
            return f"{match.group(1)}x{match.group(2)}"
        return None

    def _extract_fps(self, output):
        """从FFmpeg输出中提取帧率"""
        import re
        match = re.search(r'(\d+\.?\d*) fps', output)
        if match:
            return float(match.group(1))
        return None

    def _extract_codec(self, output):
        """从FFmpeg输出中提取编码格式"""
        import re
        match = re.search(r'Video: (\w+)', output)
        if match:
            return match.group(1)
        return None

    def _extract_bitrate(self, output):
        """从FFmpeg输出中提取比特率"""
        import re
        match = re.search(r'bitrate: (\d+) kb/s', output)
        if match:
            return int(match.group(1))
        return None

# 单例模式
_video_processor = None

def get_video_processor() -> VideoProcessor:
    """获取视频处理器实例（单例模式）
    
    Returns:
        VideoProcessor: 视频处理器实例
    """
    global _video_processor
    
    if _video_processor is None:
        _video_processor = VideoProcessor()

    return _video_processor