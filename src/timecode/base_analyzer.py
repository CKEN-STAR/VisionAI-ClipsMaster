#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
原片时长基准分析模块

精确计算和分析视频文件的时长信息，支持多种分析方法，并可进行方法间的结果对比。
主要功能：
1. 基于OpenCV的帧计数时长分析（高精度但速度较慢）
2. 基于FFprobe的元数据时长分析（快速但依赖媒体文件格式的完整性）
3. 多方法结果比对，确保时长计算的准确性
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, List, Tuple, Optional, Any, Union

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV (cv2) 未安装，仅使用FFprobe进行时长分析")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy 未安装，某些高级分析功能可能受限")

# 配置日志记录
logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """视频基础分析器
    
    提供视频文件基本属性的分析功能，包括时长、分辨率、帧率等。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化基础分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.ffprobe_path = self.config.get("ffprobe_path", "ffprobe")
        self.ffmpeg_path = self.config.get("ffmpeg_path", "ffmpeg")
        self.tolerance = self.config.get("duration_tolerance", 0.05)  # 默认允许0.05秒的误差
        
        # 确认FFprobe可用性
        self._check_ffprobe()
    
    def _check_ffprobe(self) -> None:
        """检查FFprobe是否可用"""
        try:
            result = subprocess.run(
                [self.ffprobe_path, "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                logger.info("FFprobe可用")
                # 提取版本信息
                version_line = result.stdout.split('\n')[0]
                logger.debug(f"FFprobe版本: {version_line}")
                self.ffprobe_available = True
            else:
                logger.warning("FFprobe命令返回非零状态，可能无法正常使用")
                self.ffprobe_available = False
        except Exception as e:
            logger.error(f"检测FFprobe失败: {str(e)}")
            logger.warning("FFprobe可能未安装，将依赖OpenCV进行分析")
            self.ffprobe_available = False
    
    def analyze_source_duration(self, video_path: str) -> float:
        """精确计算原片总时长
        
        使用OpenCV计算视频总帧数并根据帧率计算精确时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（毫秒）
            
        Raises:
            FileNotFoundError: 视频文件不存在
            ValueError: 无法打开视频或获取视频信息
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 优先使用OpenCV计算时长（更精确）
        if CV2_AVAILABLE:
            try:
                cv_duration = self._calculate_duration_cv2(video_path)
                logger.debug(f"OpenCV计算的视频时长: {cv_duration:.3f}秒")
                
                # 尝试使用FFprobe作为参照
                if self.ffprobe_available:
                    ff_duration = self._calculate_duration_ffprobe(video_path)
                    logger.debug(f"FFprobe计算的视频时长: {ff_duration:.3f}秒")
                    
                    # 比较两种方法的结果，如果差异较大则记录警告
                    if abs(cv_duration - ff_duration) > self.tolerance:
                        logger.warning(
                            f"视频时长计算结果存在差异: OpenCV={cv_duration:.3f}秒, "
                            f"FFprobe={ff_duration:.3f}秒"
                        )
                
                return cv_duration
            except Exception as e:
                logger.error(f"使用OpenCV分析视频时长失败: {str(e)}")
                # 如果OpenCV失败，尝试使用FFprobe
                if self.ffprobe_available:
                    logger.info("尝试使用FFprobe作为备选方法")
                    return self._calculate_duration_ffprobe(video_path)
                raise ValueError(f"无法分析视频时长: {str(e)}")
        
        # 如果OpenCV不可用，则使用FFprobe
        elif self.ffprobe_available:
            return self._calculate_duration_ffprobe(video_path)
        
        else:
            raise RuntimeError("无法分析视频时长: 缺少必要的工具库(OpenCV或FFprobe)")
    
    def _calculate_duration_cv2(self, video_path: str) -> float:
        """使用OpenCV计算视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（秒）
            
        Raises:
            ValueError: 无法打开视频或获取视频信息
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取帧率和总帧数
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 检查获取的值是否有效
        if fps <= 0:
            logger.warning(f"获取到无效的帧率({fps})，尝试手动计算")
            fps = self._manually_calculate_fps(cap)
        
        if frame_count <= 0:
            logger.warning(f"获取到无效的总帧数({frame_count})，尝试手动计数")
            frame_count = self._manually_count_frames(cap)
        
        # 释放视频对象
        cap.release()
        
        # 计算时长（秒）
        if fps > 0 and frame_count > 0:
            duration = frame_count / fps
            return duration
        else:
            raise ValueError("无法计算视频时长: 无效的帧率或总帧数")
    
    def _manually_calculate_fps(self, cap: cv2.VideoCapture) -> float:
        """手动计算视频帧率
        
        当无法从视频元数据直接获取帧率时，通过采样计算近似帧率
        
        Args:
            cap: OpenCV VideoCapture对象
            
        Returns:
            估算的帧率
        """
        # 默认返回标准帧率25fps
        default_fps = 25.0
        
        try:
            # 尝试读取最开始的100帧，记录时间戳
            timestamps = []
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            for i in range(100):
                ret = cap.grab()
                if not ret:
                    break
                # 获取当前帧的时间戳（毫秒）
                msec = cap.get(cv2.CAP_PROP_POS_MSEC)
                timestamps.append(msec)
            
            if len(timestamps) < 2:
                logger.warning("无法手动计算帧率: 读取帧不足")
                return default_fps
            
            # 计算时间差和帧数差
            time_diff = (timestamps[-1] - timestamps[0]) / 1000  # 转换为秒
            frame_diff = len(timestamps) - 1
            
            if time_diff > 0:
                fps = frame_diff / time_diff
                logger.info(f"手动计算的帧率: {fps:.3f} fps")
                return fps
            else:
                logger.warning("时间差异过小，无法准确计算帧率")
                return default_fps
                
        except Exception as e:
            logger.error(f"手动计算帧率时出错: {str(e)}")
            return default_fps
    
    def _manually_count_frames(self, cap: cv2.VideoCapture) -> int:
        """手动计数视频帧数
        
        当无法从视频元数据直接获取总帧数时，通过逐帧读取计数
        
        Args:
            cap: OpenCV VideoCapture对象
            
        Returns:
            总帧数
        """
        # 重置视频位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 尝试使用快速计数方法（OpenCV 3.x及以上版本）
        try:
            frame_count = 0
            # 使用grab()方法比read()更快，因为它不实际解码帧
            while cap.grab():
                frame_count += 1
            
            logger.info(f"手动计数的总帧数: {frame_count}")
            return frame_count
            
        except Exception as e:
            logger.error(f"手动计数帧数时出错: {str(e)}")
            return 0
    
    def _calculate_duration_ffprobe(self, video_path: str) -> float:
        """使用FFprobe计算视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频时长（秒）
            
        Raises:
            ValueError: 无法使用FFprobe获取视频信息
        """
        try:
            # 调用FFprobe获取视频时长
            result = subprocess.run([
                self.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise ValueError(f"FFprobe返回错误: {result.stderr}")
            
            duration = float(result.stdout.strip())
            return duration
            
        except Exception as e:
            logger.error(f"使用FFprobe获取视频时长失败: {str(e)}")
            raise ValueError(f"无法使用FFprobe分析视频时长: {str(e)}")
    
    def get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """获取视频的完整元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频元数据字典
        """
        metadata = {}
        
        # 使用FFprobe获取详细信息
        if self.ffprobe_available:
            try:
                result = subprocess.run([
                    self.ffprobe_path,
                    '-v', 'error',
                    '-show_format',
                    '-show_streams',
                    '-of', 'json',
                    video_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if result.returncode == 0:
                    ffprobe_data = json.loads(result.stdout)
                    metadata['ffprobe'] = ffprobe_data
                    
                    # 提取关键信息到顶层
                    if 'format' in ffprobe_data:
                        format_info = ffprobe_data['format']
                        metadata['duration'] = float(format_info.get('duration', 0))
                        metadata['size'] = int(format_info.get('size', 0))
                        metadata['bit_rate'] = int(format_info.get('bit_rate', 0))
                        metadata['format_name'] = format_info.get('format_name', '')
                    
                    # 提取视频流信息
                    if 'streams' in ffprobe_data:
                        for stream in ffprobe_data['streams']:
                            if stream.get('codec_type') == 'video':
                                metadata['width'] = stream.get('width', 0)
                                metadata['height'] = stream.get('height', 0)
                                metadata['codec'] = stream.get('codec_name', '')
                                
                                # 处理帧率，可能是分数形式如"30000/1001"
                                fps_str = stream.get('r_frame_rate', '')
                                if '/' in fps_str:
                                    num, den = map(int, fps_str.split('/'))
                                    if den != 0:
                                        metadata['fps'] = num / den
                                else:
                                    try:
                                        metadata['fps'] = float(fps_str)
                                    except (ValueError, TypeError):
                                        metadata['fps'] = 0
                                break
            except Exception as e:
                logger.error(f"获取FFprobe元数据失败: {str(e)}")
        
        # 使用OpenCV获取基本信息
        if CV2_AVAILABLE:
            try:
                cap = cv2.VideoCapture(video_path)
                if cap.isOpened():
                    metadata['cv2'] = {
                        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                        'fps': cap.get(cv2.CAP_PROP_FPS),
                        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                        'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC))
                    }
                    
                    # 如果顶层没有这些值，用OpenCV的填充
                    if 'width' not in metadata:
                        metadata['width'] = metadata['cv2']['width']
                    if 'height' not in metadata:
                        metadata['height'] = metadata['cv2']['height']
                    if 'fps' not in metadata or metadata['fps'] == 0:
                        metadata['fps'] = metadata['cv2']['fps']
                    
                    # 计算OpenCV估算的时长
                    if metadata['cv2']['fps'] > 0 and metadata['cv2']['frame_count'] > 0:
                        metadata['cv2']['duration'] = metadata['cv2']['frame_count'] / metadata['cv2']['fps']
                        # 如果没有FFprobe时长，用OpenCV的替代
                        if 'duration' not in metadata:
                            metadata['duration'] = metadata['cv2']['duration']
                    
                    cap.release()
            except Exception as e:
                logger.error(f"获取OpenCV元数据失败: {str(e)}")
        
        return metadata
    
    def verify_duration_with_ffprobe(self, video_path: str, calculated_duration: float) -> Tuple[bool, float]:
        """使用FFprobe验证已计算的视频时长
        
        将计算得到的时长与FFprobe报告的时长进行比较，验证结果的准确性。
        
        Args:
            video_path: 视频文件路径
            calculated_duration: 已计算的时长（秒）
            
        Returns:
            验证结果元组 (是否一致, 差异值)
        """
        if not self.ffprobe_available:
            logger.warning("FFprobe不可用，无法验证计算结果")
            return False, 0.0
        
        try:
            ffprobe_duration = self._calculate_duration_ffprobe(video_path)
            
            # 计算绝对差异
            diff = abs(calculated_duration - ffprobe_duration)
            
            # 判断是否在容差范围内
            is_verified = diff <= self.tolerance
            
            logger.info(
                f"FFprobe验证结果: {'✓' if is_verified else '✗'}, "
                f"计算时长={calculated_duration:.3f}秒, FFprobe={ffprobe_duration:.3f}秒, "
                f"差异={diff:.3f}秒"
            )
            
            return is_verified, diff
            
        except Exception as e:
            logger.error(f"验证时长失败: {str(e)}")
            return False, 0.0


# 便利函数
def analyze_source_duration(video_path: str) -> float:
    """精确计算原片总时长（毫秒级）
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频时长（秒）
    """
    analyzer = BaseAnalyzer()
    duration_sec = analyzer.analyze_source_duration(video_path)
    return round(duration_sec * 1000) / 1000  # 保留毫秒精度

def verify_duration(video_path: str, duration: float) -> bool:
    """验证视频时长计算结果
    
    使用FFprobe验证计算的视频时长是否准确
    
    Args:
        video_path: 视频文件路径
        duration: 计算的时长（秒）
        
    Returns:
        验证结果（布尔值）
    """
    analyzer = BaseAnalyzer()
    is_verified, _ = analyzer.verify_duration_with_ffprobe(video_path, duration)
    return is_verified 