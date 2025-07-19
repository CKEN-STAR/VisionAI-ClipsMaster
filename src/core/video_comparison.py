#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU加速视频比较模块

提供高性能的视频帧比较和分析功能，利用GPU加速实现更快的视频内容对比。
支持CUDA、OpenCL等多种GPU加速后端，并提供优雅的CPU回退机制。

主要功能:
1. 帧对比: 快速计算两个视频帧之间的相似度
2. 视频相似度计算: 整体分析两个视频的相似程度
3. 特征比较: 颜色分布、结构特征、动态内容比较
4. 视觉质量评估: PSNR, SSIM等质量指标的GPU加速计算
"""

import os
import sys
import logging
import numpy as np
import cv2
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path

# 导入GPU回退组件
from src.hardware.gpu_fallback import get_gpu_fallback_manager, try_gpu_accel

# 配置日志
logger = logging.getLogger("video_comparison")

class VideoCompare:
    """GPU加速的视频比较类"""
    
    def __init__(self, use_gpu: bool = True, min_vram_mb: int = 1024):
        """
        初始化视频比较器
        
        Args:
            use_gpu: 是否使用GPU加速
            min_vram_mb: 最小显存要求(MB)
        """
        self.use_gpu = use_gpu
        self.gpu_manager = get_gpu_fallback_manager(min_vram_mb=min_vram_mb, prefer_gpu=use_gpu)
        self.device = self.gpu_manager.current_device
        
        # 初始化CUDA组件(如果可用)
        self.stream = None
        self.hist_calculator = None
        
        if self.device == "cuda":
            try:
                self.stream = cv2.cuda.Stream()
                # 检查CUDA是否真正可用
                test_mat = cv2.cuda.GpuMat((10, 10), cv2.CV_8UC3)
                logger.info("成功初始化CUDA加速")
            except Exception as e:
                logger.warning(f"CUDA初始化失败，回退到CPU: {e}")
                self.device = "cpu"
    
    def compare_frames(self, frame1: np.ndarray, frame2: np.ndarray) -> Dict[str, float]:
        """
        比较两个视频帧的相似度
        
        使用多种指标进行比较，包括PSNR、直方图相似度等
        
        Args:
            frame1: 第一个视频帧
            frame2: 第二个视频帧
            
        Returns:
            Dict: 包含各种相似度指标的字典
        """
        # 确保两帧大小相同
        if frame1.shape != frame2.shape:
            frame2 = self._resize_frame(frame2, (frame1.shape[1], frame1.shape[0]))
        
        # 计算各种相似度指标
        result = {}
        
        # 1. 计算PSNR (峰值信噪比)
        result["psnr"] = self._calculate_psnr(frame1, frame2)
        
        # 2. 计算直方图相似度
        result["histogram_similarity"] = self._calculate_histogram_similarity(frame1, frame2)
        
        # 3. 计算结构相似度(SSIM) - 仅在CPU上实现
        if self.device == "cpu":
            result["ssim"] = self._calculate_ssim_cpu(frame1, frame2)
        else:
            # 在GPU上回退到CPU计算SSIM
            result["ssim"] = self._calculate_ssim_cpu(frame1, frame2)
        
        # 4. 计算平均相似度
        result["similarity"] = (
            0.4 * min(result["psnr"] / 50.0, 1.0) +  # PSNR贡献
            0.4 * result["histogram_similarity"] +   # 直方图贡献
            0.2 * result["ssim"]                     # SSIM贡献
        )
        
        return result
    
    def _resize_frame(self, frame: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """调整帧大小，使用GPU加速(如果可用)"""
        if self.device == "cuda":
            try:
                gpu_frame = cv2.cuda.GpuMat()
                gpu_frame.upload(frame)
                resized = cv2.cuda.resize(gpu_frame, size)
                return resized.download()
            except Exception as e:
                logger.warning(f"GPU调整大小失败，回退到CPU: {e}")
        
        # CPU回退
        return cv2.resize(frame, size)
    
    def _calculate_psnr(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """使用GPU加速计算PSNR(如果可用)"""
        if self.device == "cuda":
            try:
                # 上传到GPU
                gpu_frame1 = cv2.cuda.GpuMat()
                gpu_frame2 = cv2.cuda.GpuMat()
                gpu_frame1.upload(frame1)
                gpu_frame2.upload(frame2)
                
                # 计算差异的平方
                diff = cv2.cuda.absdiff(gpu_frame1, gpu_frame2)
                gpu_diff_squared = cv2.cuda.multiply(diff, diff)
                
                # 计算MSE
                mse = cv2.cuda.mean(gpu_diff_squared)[0]
                
                # 计算PSNR
                if mse < 1e-10:
                    return 100.0
                
                return 10.0 * np.log10((255.0 * 255.0) / mse)
            
            except Exception as e:
                logger.warning(f"GPU PSNR计算失败，回退到CPU: {e}")
        
        # CPU回退实现
        mse = np.mean((frame1.astype(np.float64) - frame2.astype(np.float64)) ** 2)
        if mse < 1e-10:
            return 100.0
        
        return 10.0 * np.log10((255.0 * 255.0) / mse)
    
    def _calculate_histogram_similarity(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算直方图相似度，使用GPU加速(如果可用)"""
        if self.device == "cuda":
            try:
                # 获取GPU直方图
                hist1 = self._gpu_histogram(frame1)
                hist2 = self._gpu_histogram(frame2)
                
                # 计算相似度 (使用相关性)
                correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                return max(0.0, correlation)  # 确保结果在0-1范围内
            
            except Exception as e:
                logger.warning(f"GPU直方图计算失败，回退到CPU: {e}")
        
        # CPU回退实现
        hist1 = self._cpu_histogram(frame1)
        hist2 = self._cpu_histogram(frame2)
        
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return max(0.0, correlation)
    
    def _gpu_histogram(self, frame: np.ndarray) -> np.ndarray:
        """GPU加速的直方图计算"""
        # 转换为HSV空间
        gpu_frame = cv2.cuda.GpuMat()
        gpu_frame.upload(frame)
        gpu_hsv = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2HSV)
        
        # 计算H和S通道的直方图
        h_bins, s_bins = 30, 32
        
        # 使用CUDA直方图计算
        h_hist = cv2.cuda.histEven(gpu_hsv, 0, 0, 180, h_bins)
        s_hist = cv2.cuda.histEven(gpu_hsv, 1, 0, 256, s_bins)
        
        # 下载到CPU并合并
        h_hist_cpu = h_hist.download()
        s_hist_cpu = s_hist.download()
        
        # 归一化
        cv2.normalize(h_hist_cpu, h_hist_cpu, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(s_hist_cpu, s_hist_cpu, 0, 1, cv2.NORM_MINMAX)
        
        # 返回扁平化直方图特征
        return np.concatenate([h_hist_cpu, s_hist_cpu])
    
    def _cpu_histogram(self, frame: np.ndarray) -> np.ndarray:
        """CPU实现的直方图计算"""
        # 转换为HSV空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算H和S通道的直方图
        h_bins, s_bins = 30, 32
        h_hist = cv2.calcHist([hsv], [0], None, [h_bins], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [s_bins], [0, 256])
        
        # 归一化
        cv2.normalize(h_hist, h_hist, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(s_hist, s_hist, 0, 1, cv2.NORM_MINMAX)
        
        # 返回扁平化直方图特征
        return np.concatenate([h_hist.flatten(), s_hist.flatten()])
    
    def _calculate_ssim_cpu(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """计算结构相似度(SSIM)的CPU实现"""
        # 转换为灰度图
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        # 计算均值
        mu1 = cv2.GaussianBlur(gray1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(gray2, (11, 11), 1.5)
        
        # 计算均值的平方
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        # 计算方差和协方差
        sigma1_sq = cv2.GaussianBlur(gray1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(gray2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(gray1 * gray2, (11, 11), 1.5) - mu1_mu2
        
        # SSIM公式
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        
        # 返回平均SSIM
        return float(np.mean(ssim_map))
    
    def compare_videos(self, video1_path: str, video2_path: str, 
                       max_frames: int = 300) -> Dict[str, Any]:
        """
        比较两个视频的相似度
        
        Args:
            video1_path: 第一个视频的路径
            video2_path: 第二个视频的路径
            max_frames: 最大比较帧数
            
        Returns:
            Dict: 视频比较结果
        """
        # 打开视频文件
        cap1 = cv2.VideoCapture(video1_path)
        cap2 = cv2.VideoCapture(video2_path)
        
        # 检查视频是否成功打开
        if not cap1.isOpened() or not cap2.isOpened():
            error_msg = "无法打开视频文件"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # 获取视频基本信息
        info1 = self._get_video_info(cap1)
        info2 = self._get_video_info(cap2)
        
        # 确定采样策略
        frame_count = min(info1["frame_count"], info2["frame_count"])
        sample_count = min(max_frames, frame_count)
        
        if sample_count <= 0:
            return {"error": "视频帧数不足"}
        
        # 计算采样间隔
        interval = max(1, frame_count // sample_count)
        
        # 初始化结果统计
        frame_similarities = []
        frame_positions = []
        
        # 逐帧比较
        for i in range(0, frame_count, interval):
            # 设置帧位置
            cap1.set(cv2.CAP_PROP_POS_FRAMES, i)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, i)
            
            # 读取帧
            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()
            
            # 检查是否成功读取
            if not ret1 or not ret2:
                continue
            
            # 比较帧
            comparison = self.compare_frames(frame1, frame2)
            
            # 记录结果
            frame_similarities.append(comparison)
            frame_positions.append(i)
            
            # 如果已达到采样数量上限，停止处理
            if len(frame_similarities) >= sample_count:
                break
        
        # 释放资源
        cap1.release()
        cap2.release()
        
        # 计算整体指标
        avg_psnr = np.mean([f["psnr"] for f in frame_similarities]) if frame_similarities else 0
        avg_hist_sim = np.mean([f["histogram_similarity"] for f in frame_similarities]) if frame_similarities else 0
        avg_ssim = np.mean([f["ssim"] for f in frame_similarities]) if frame_similarities else 0
        avg_similarity = np.mean([f["similarity"] for f in frame_similarities]) if frame_similarities else 0
        
        # 构建结果
        result = {
            "video_info": {
                "video1": info1,
                "video2": info2
            },
            "comparison": {
                "frames_compared": len(frame_similarities),
                "avg_psnr": float(avg_psnr),
                "avg_histogram_similarity": float(avg_hist_sim),
                "avg_ssim": float(avg_ssim),
                "avg_similarity": float(avg_similarity)
            },
            "device_info": {
                "device": self.device,
                "gpu_available": self.device == "cuda"
            }
        }
        
        return result
    
    def _get_video_info(self, cap) -> Dict[str, Any]:
        """获取视频基本信息"""
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": frame_count,
            "duration": duration
        }

# 创建全局视频比较器单例
_video_comparator = None

def get_video_comparator(use_gpu: bool = True, min_vram_mb: int = 1024) -> VideoCompare:
    """
    获取视频比较器全局实例
    
    Args:
        use_gpu: 是否使用GPU加速
        min_vram_mb: 最小显存要求(MB)
        
    Returns:
        VideoCompare: 视频比较器实例
    """
    global _video_comparator
    if _video_comparator is None:
        _video_comparator = VideoCompare(use_gpu=use_gpu, min_vram_mb=min_vram_mb)
    return _video_comparator

def compare_videos(video1_path: str, video2_path: str, use_gpu: bool = True) -> Dict[str, Any]:
    """
    比较两个视频的相似度(便捷函数)
    
    Args:
        video1_path: 第一个视频的路径
        video2_path: 第二个视频的路径
        use_gpu: 是否使用GPU加速
        
    Returns:
        Dict: 视频比较结果
    """
    comparator = get_video_comparator(use_gpu=use_gpu)
    return comparator.compare_videos(video1_path, video2_path) 