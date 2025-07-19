#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频质量评估模块

提供视频质量评估功能，包括PSNR计算、帧比对等功能。
支持GPU加速计算，确保高精度低误判。
"""

import os
import sys
import logging
import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path

# 项目内部导入
from src.utils.log_handler import get_logger

# 配置日志
quality_logger = get_logger("video_quality")

class VideoQualityEvaluator:
    """视频质量评估器
    
    提供视频质量评估功能，包括PSNR计算、帧比对等。
    支持GPU加速以提高性能。
    """
    
    def __init__(self, use_gpu: bool = True):
        """初始化视频质量评估器
        
        Args:
            use_gpu: 是否使用GPU加速
        """
        self.use_gpu = False
        if use_gpu:
            self.enable_gpu_acceleration()
        quality_logger.info(f"视频质量评估器初始化完成，GPU加速: {self.use_gpu}")
    
    def enable_gpu_acceleration(self) -> bool:
        """启用GPU加速
        
        Returns:
            bool: 是否成功启用GPU加速
        """
        try:
            # 检查是否有可用GPU
            gpu_count = cv2.cuda.getCudaEnabledDeviceCount()
            if gpu_count > 0:
                # 设置OpenCV使用GPU
                cv2.setUseOptimized(True)
                self.use_gpu = True
                quality_logger.info(f"GPU加速已启用，可用设备数: {gpu_count}")
                return True
            else:
                quality_logger.warning("未检测到可用GPU设备，使用CPU处理")
                self.use_gpu = False
                return False
        except Exception as e:
            quality_logger.error(f"GPU加速初始化失败: {str(e)}")
            self.use_gpu = False
            return False
    
    def calculate_psnr(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """计算两图像间的PSNR值
        
        Args:
            img1: 第一张图像
            img2: 第二张图像
            
        Returns:
            float: PSNR值，值越高表示图像越相似
        """
        # 确保图像尺寸相同
        if img1.shape != img2.shape:
            quality_logger.warning(f"图像尺寸不匹配: {img1.shape} vs {img2.shape}")
            # 调整尺寸
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        
        # 确保数据类型一致
        img1 = img1.astype(np.float32)
        img2 = img2.astype(np.float32)
        
        if self.use_gpu:
            try:
                # 将图像转移到GPU
                gpu_img1 = cv2.cuda_GpuMat(img1)
                gpu_img2 = cv2.cuda_GpuMat(img2)
                
                # 计算差异
                gpu_diff = cv2.cuda.absdiff(gpu_img1, gpu_img2)
                diff = gpu_diff.download()
                
                # 计算MSE
                mse = np.mean(diff ** 2)
            except Exception as e:
                quality_logger.error(f"GPU计算PSNR失败，回退到CPU: {str(e)}")
                # 回退到CPU计算
                mse = np.mean((img1 - img2) ** 2)
        else:
            # CPU计算
            mse = np.mean((img1 - img2) ** 2)
        
        # 避免除零错误
        if mse == 0:
            return float('inf')
        
        # 计算PSNR
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
        
        return psnr
    
    def compare_frames(self, frame1: np.ndarray, frame2: np.ndarray, threshold: float = 28.0) -> Dict[str, Any]:
        """比较两帧之间的差异
        
        Args:
            frame1: 第一帧
            frame2: 第二帧
            threshold: PSNR阈值，高于此值视为相似
            
        Returns:
            Dict[str, Any]: 比对结果
        """
        # 计算PSNR
        psnr_value = self.calculate_psnr(frame1, frame2)
        
        # 判断是否相似
        is_similar = psnr_value >= threshold
        
        # 返回结果
        return {
            "psnr": psnr_value,
            "is_similar": is_similar,
            "threshold": threshold
        }
    
    def compare_video_segments(
        self, 
        video_path1: str, 
        video_path2: str, 
        start_time: float = 0.0,
        duration: float = 5.0,
        threshold: float = 28.0,
        sample_rate: int = 5  # 每秒采样帧数
    ) -> Dict[str, Any]:
        """比较两个视频片段的相似度
        
        Args:
            video_path1: 第一个视频路径
            video_path2: 第二个视频路径
            start_time: 开始时间（秒）
            duration: 比较时长（秒）
            threshold: PSNR阈值
            sample_rate: 每秒采样帧数
            
        Returns:
            Dict[str, Any]: 比对结果
        """
        quality_logger.info(f"比较视频片段: {video_path1} vs {video_path2}")
        
        # 打开视频
        cap1 = cv2.VideoCapture(video_path1)
        cap2 = cv2.VideoCapture(video_path2)
        
        # 检查视频是否成功打开
        if not cap1.isOpened() or not cap2.isOpened():
            quality_logger.error("无法打开视频文件")
            if cap1.isOpened():
                cap1.release()
            if cap2.isOpened():
                cap2.release()
            return {
                "success": False,
                "error": "无法打开视频文件"
            }
        
        # 获取视频帧率
        fps1 = cap1.get(cv2.CAP_PROP_FPS)
        fps2 = cap2.get(cv2.CAP_PROP_FPS)
        
        # 设置开始帧
        start_frame1 = int(start_time * fps1)
        start_frame2 = int(start_time * fps2)
        
        cap1.set(cv2.CAP_PROP_POS_FRAMES, start_frame1)
        cap2.set(cv2.CAP_PROP_POS_FRAMES, start_frame2)
        
        # 计算总采样帧数
        total_frames = int(duration * sample_rate)
        
        # 采样间隔
        frame_interval1 = int(fps1 / sample_rate)
        frame_interval2 = int(fps2 / sample_rate)
        
        # 记录结果
        psnr_values = []
        frame_pairs = []
        similar_count = 0
        total_compared = 0
        
        # 逐帧比较
        for i in range(total_frames):
            # 读取视频1的帧
            for _ in range(frame_interval1):
                ret1, frame1 = cap1.read()
                if not ret1:
                    break
            
            # 读取视频2的帧
            for _ in range(frame_interval2):
                ret2, frame2 = cap2.read()
                if not ret2:
                    break
            
            # 如果任一视频结束，停止比较
            if not ret1 or not ret2:
                break
            
            # 比较帧
            result = self.compare_frames(frame1, frame2, threshold)
            psnr_values.append(result["psnr"])
            frame_pairs.append((i * frame_interval1 + start_frame1, i * frame_interval2 + start_frame2))
            
            if result["is_similar"]:
                similar_count += 1
            
            total_compared += 1
        
        # 释放视频资源
        cap1.release()
        cap2.release()
        
        # 计算相似度和误判率
        similarity_ratio = similar_count / total_compared if total_compared > 0 else 0
        error_rate = 1.0 - similarity_ratio
        
        if np.min(psnr_values) > threshold:
            mistaken_judgement_rate = 0.0
        else:
            # 计算误判率：PSNR>28但判断为不相似的比例
            high_psnr_count = sum(1 for psnr in psnr_values if psnr >= threshold)
            mistaken_judgement_rate = 1.0 - (similar_count / high_psnr_count if high_psnr_count > 0 else 0)
        
        # 加入更详细的统计信息 
        result = {
            "success": True,
            "total_frames_compared": total_compared,
            "similar_frames": similar_count,
            "similarity_ratio": similarity_ratio,
            "error_rate": error_rate,
            "mistaken_judgement_rate": mistaken_judgement_rate,
            "threshold": threshold,
            "avg_psnr": np.mean(psnr_values) if psnr_values else 0,
            "min_psnr": np.min(psnr_values) if psnr_values else 0,
            "max_psnr": np.max(psnr_values) if psnr_values else 0,
            "std_psnr": np.std(psnr_values) if psnr_values else 0,
            "frame_count": len(psnr_values)
        }
        
        quality_logger.info(
            f"视频片段比较完成: 相似度={similarity_ratio:.2%}, "
            f"误差率={error_rate:.4%}, 平均PSNR={result['avg_psnr']:.2f}"
        )
        
        return result
    
    def verify_output_quality(self, original_video: str, output_video: str) -> bool:
        """验证输出视频的质量
        
        确保输出视频达到质量要求，PSNR>28且误判率<0.1%
        
        Args:
            original_video: 原始视频路径
            output_video: 输出视频路径
            
        Returns:
            bool: 是否达到质量要求
        """
        quality_logger.info(f"验证输出视频质量: {output_video}")
        
        # 获取视频时长
        def get_duration(video_path):
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return 0
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            return frame_count / fps if fps else 0
        
        # 获取视频时长
        original_duration = get_duration(original_video)
        output_duration = get_duration(output_video)
        
        # 计算对比的起始时间和持续时间
        start_time = 0.0
        duration = min(original_duration, output_duration)
        
        if duration <= 0:
            quality_logger.error("无法获取视频时长")
            return False
        
        # 比较视频段，采用更高的采样率和严格的阈值
        result = self.compare_video_segments(
            original_video,
            output_video,
            start_time=start_time,
            duration=duration,
            threshold=28.0,  # 确保PSNR>28
            sample_rate=10   # 增加采样率提高精度
        )
        
        if not result.get("success", False):
            quality_logger.error(f"视频对比失败: {result.get('error', '未知错误')}")
            return False
        
        # 检查PSNR最小值
        min_psnr = result.get("min_psnr", 0)
        avg_psnr = result.get("avg_psnr", 0)
        error_rate = result.get("error_rate", 1.0)
        
        quality_logger.info(f"视频质量评估结果: 最小PSNR={min_psnr:.2f}, 平均PSNR={avg_psnr:.2f}, 误差率={error_rate:.4%}")
        
        # 确保PSNR>28且误判率<0.1%
        quality_meets_standard = min_psnr > 28.0 and error_rate < 0.001
        
        if quality_meets_standard:
            quality_logger.info("✓ 视频质量达到要求")
        else:
            quality_logger.warning("✗ 视频质量未达到要求")
            if min_psnr <= 28.0:
                quality_logger.warning(f"PSNR值过低: {min_psnr:.2f} <= 28.0")
            if error_rate >= 0.001:
                quality_logger.warning(f"误差率过高: {error_rate:.4%} >= 0.1%")
        
        return quality_meets_standard

# 单例实例
_quality_evaluator_instance = None

def get_quality_evaluator(use_gpu: bool = True) -> VideoQualityEvaluator:
    """获取视频质量评估器实例
    
    Args:
        use_gpu: 是否使用GPU加速
        
    Returns:
        VideoQualityEvaluator: 视频质量评估器实例
    """
    global _quality_evaluator_instance
    if _quality_evaluator_instance is None:
        _quality_evaluator_instance = VideoQualityEvaluator(use_gpu)
    return _quality_evaluator_instance 