#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 视频处理性能优化器
实现FFmpeg参数优化、GPU硬件加速和多线程并行处理
"""

import os
import time
import threading
import multiprocessing
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)

@dataclass
class VideoProcessingTask:
    """视频处理任务"""
    id: str
    input_path: str
    output_path: str
    start_time: float
    end_time: float
    operation: str  # 'cut', 'merge', 'encode'
    params: Dict[str, Any]

@dataclass
class ProcessingResult:
    """处理结果"""
    task_id: str
    success: bool
    output_path: Optional[str]
    processing_time_ms: float
    file_size_mb: float
    error: Optional[str] = None

class FFmpegOptimizer:
    """FFmpeg参数优化器"""
    
    def __init__(self):
        self.gpu_encoders = {
            'nvidia': ['h264_nvenc', 'hevc_nvenc'],
            'amd': ['h264_amf', 'hevc_amf'],
            'intel': ['h264_qsv', 'hevc_qsv']
        }
        self.cpu_encoders = ['libx264', 'libx265']
        self.detected_gpu = None
        self.optimal_params = {}
        
        self._detect_hardware()
        self._initialize_optimal_params()
    
    def _detect_hardware(self):
        """检测硬件加速支持"""
        try:
            from ui.hardware.gpu_detector import get_gpu_detector
            gpu_detector = get_gpu_detector()
            
            if gpu_detector.nvidia_gpus:
                self.detected_gpu = 'nvidia'
            elif gpu_detector.amd_gpus:
                self.detected_gpu = 'amd'
            elif gpu_detector.intel_gpus:
                self.detected_gpu = 'intel'
            
            logger.info(f"检测到GPU类型: {self.detected_gpu}")
        except Exception as e:
            logger.warning(f"GPU检测失败: {e}")
            self.detected_gpu = None
    
    def _initialize_optimal_params(self):
        """初始化最优参数"""
        # 基础参数
        base_params = {
            'video_codec': 'libx264',
            'audio_codec': 'aac',
            'preset': 'medium',
            'crf': 23,
            'threads': min(multiprocessing.cpu_count(), 8)
        }
        
        # GPU加速参数
        if self.detected_gpu and self.detected_gpu in self.gpu_encoders:
            gpu_params = base_params.copy()
            gpu_params.update({
                'video_codec': self.gpu_encoders[self.detected_gpu][0],
                'preset': 'fast',
                'rc_mode': 'vbr',
                'qp': 23
            })
            self.optimal_params['gpu'] = gpu_params
        
        # CPU参数
        cpu_params = base_params.copy()
        cpu_params.update({
            'preset': 'faster',  # 更快的预设
            'tune': 'film'
        })
        self.optimal_params['cpu'] = cpu_params
        
        # 快速处理参数（用于预览）
        fast_params = base_params.copy()
        fast_params.update({
            'preset': 'ultrafast',
            'crf': 28,
            'scale': '720:-1'  # 降低分辨率
        })
        self.optimal_params['fast'] = fast_params
    
    def get_optimal_params(self, mode: str = 'auto') -> Dict[str, Any]:
        """获取最优参数"""
        if mode == 'auto':
            if self.detected_gpu and 'gpu' in self.optimal_params:
                return self.optimal_params['gpu']
            else:
                return self.optimal_params['cpu']
        elif mode in self.optimal_params:
            return self.optimal_params[mode]
        else:
            return self.optimal_params['cpu']
    
    def build_ffmpeg_command(self, task: VideoProcessingTask, mode: str = 'auto') -> List[str]:
        """构建FFmpeg命令"""
        params = self.get_optimal_params(mode)
        
        cmd = ['ffmpeg', '-y']  # -y 覆盖输出文件
        
        # 输入文件
        cmd.extend(['-i', task.input_path])
        
        # 时间范围（如果指定）
        if task.start_time > 0:
            cmd.extend(['-ss', str(task.start_time)])
        
        if task.end_time > task.start_time:
            duration = task.end_time - task.start_time
            cmd.extend(['-t', str(duration)])
        
        # 编码参数
        cmd.extend(['-c:v', params['video_codec']])
        cmd.extend(['-c:a', params['audio_codec']])
        
        if 'preset' in params:
            cmd.extend(['-preset', params['preset']])
        
        if 'crf' in params and params['video_codec'].startswith('lib'):
            cmd.extend(['-crf', str(params['crf'])])
        elif 'qp' in params:
            cmd.extend(['-qp', str(params['qp'])])
        
        if 'threads' in params:
            cmd.extend(['-threads', str(params['threads'])])
        
        if 'scale' in params:
            cmd.extend(['-vf', f"scale={params['scale']}"])
        
        # 任务特定参数
        if task.params:
            for key, value in task.params.items():
                cmd.extend([f'-{key}', str(value)])
        
        # 输出文件
        cmd.append(task.output_path)
        
        return cmd

class VideoProcessor:
    """视频处理器"""
    
    def __init__(self, max_workers: int = None):
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 4)
        
        self.max_workers = max_workers
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="VideoProcessor")
        self.ffmpeg_optimizer = FFmpegOptimizer()
        self.active_tasks = {}
        self.processing_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_processing_time_ms': 0,
            'total_output_size_mb': 0
        }
        
    def submit_task(self, task: VideoProcessingTask, mode: str = 'auto') -> ProcessingResult:
        """提交视频处理任务"""
        future = self.thread_executor.submit(self._process_video, task, mode)
        self.active_tasks[task.id] = future
        
        try:
            result = future.result()
            self._update_stats(result)
            return result
        finally:
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
    
    def submit_batch_tasks(self, tasks: List[VideoProcessingTask], mode: str = 'auto') -> List[ProcessingResult]:
        """提交批量视频处理任务"""
        futures = []
        
        for task in tasks:
            future = self.thread_executor.submit(self._process_video, task, mode)
            futures.append((task.id, future))
            self.active_tasks[task.id] = future
        
        results = []
        for task_id, future in futures:
            try:
                result = future.result()
                results.append(result)
                self._update_stats(result)
            except Exception as e:
                logger.error(f"批量任务执行失败: {task_id} - {e}")
                results.append(ProcessingResult(
                    task_id=task_id,
                    success=False,
                    output_path=None,
                    processing_time_ms=0,
                    file_size_mb=0,
                    error=str(e)
                ))
            finally:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
        
        return results
    
    def _process_video(self, task: VideoProcessingTask, mode: str) -> ProcessingResult:
        """处理单个视频任务"""
        start_time = time.time()
        
        try:
            # 构建FFmpeg命令
            cmd = self.ffmpeg_optimizer.build_ffmpeg_command(task, mode)
            
            logger.info(f"执行FFmpeg命令: {' '.join(cmd)}")
            
            # 执行命令
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                # 获取输出文件大小
                file_size_mb = 0
                if os.path.exists(task.output_path):
                    file_size_mb = os.path.getsize(task.output_path) / 1024 / 1024
                
                return ProcessingResult(
                    task_id=task.id,
                    success=True,
                    output_path=task.output_path,
                    processing_time_ms=processing_time,
                    file_size_mb=file_size_mb
                )
            else:
                logger.error(f"FFmpeg执行失败: {result.stderr}")
                return ProcessingResult(
                    task_id=task.id,
                    success=False,
                    output_path=None,
                    processing_time_ms=processing_time,
                    file_size_mb=0,
                    error=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"视频处理超时: {task.id}")
            return ProcessingResult(
                task_id=task.id,
                success=False,
                output_path=None,
                processing_time_ms=processing_time,
                file_size_mb=0,
                error="处理超时"
            )
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"视频处理异常: {task.id} - {e}")
            return ProcessingResult(
                task_id=task.id,
                success=False,
                output_path=None,
                processing_time_ms=processing_time,
                file_size_mb=0,
                error=str(e)
            )
    
    def _update_stats(self, result: ProcessingResult):
        """更新统计信息"""
        self.processing_stats['total_tasks'] += 1
        self.processing_stats['total_processing_time_ms'] += result.processing_time_ms
        
        if result.success:
            self.processing_stats['successful_tasks'] += 1
            self.processing_stats['total_output_size_mb'] += result.file_size_mb
        else:
            self.processing_stats['failed_tasks'] += 1
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        stats = self.processing_stats.copy()
        
        if stats['total_tasks'] > 0:
            stats['success_rate'] = stats['successful_tasks'] / stats['total_tasks']
            stats['avg_processing_time_ms'] = stats['total_processing_time_ms'] / stats['total_tasks']
        else:
            stats['success_rate'] = 0
            stats['avg_processing_time_ms'] = 0
        
        stats['active_tasks'] = len(self.active_tasks)
        stats['gpu_acceleration'] = self.ffmpeg_optimizer.detected_gpu is not None
        
        return stats
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            future = self.active_tasks[task_id]
            cancelled = future.cancel()
            if cancelled:
                del self.active_tasks[task_id]
            return cancelled
        return False
    
    def shutdown(self):
        """关闭处理器"""
        self.thread_executor.shutdown(wait=True)
        logger.info("视频处理器已关闭")

# 全局视频处理器实例
_video_processor = None

def get_video_processor() -> VideoProcessor:
    """获取全局视频处理器实例"""
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor
