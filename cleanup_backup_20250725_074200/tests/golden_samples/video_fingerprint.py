#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
视频指纹提取引擎

此模块用于从视频中提取稳定的视觉特征指纹，可用于视频内容比对、重复检测和相似度分析。
无论视频编码、分辨率或轻微剪辑如何变化，相同内容的视频应产生相似的指纹。
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Union, Optional
from scipy.spatial.distance import cosine

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

class VideoFingerprint:
    """视频指纹处理类"""
    
    def __init__(self, sample_frames: int = 16, hist_bins: int = 256):
        """
        初始化视频指纹提取器
        
        Args:
            sample_frames: 采样帧数量
            hist_bins: 直方图柱数
        """
        self.sample_frames = sample_frames
        self.hist_bins = hist_bins
    
    def extract_signature(self, video_path: str) -> np.ndarray:
        """
        提取视频关键帧特征指纹
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            np.ndarray: 视频特征指纹向量
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"无法打开视频文件: {video_path}")
        
        # 获取视频基本信息
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps if fps > 0 else 0
        
        # 准备采样帧索引
        if frame_count <= 0:
            raise ValueError(f"视频没有可用帧: {video_path}")
        
        # 计算采样间隔，确保覆盖整个视频
        if frame_count <= self.sample_frames:
            # 如果视频帧数少于采样数，则使用所有帧
            sample_indices = list(range(frame_count))
        else:
            # 均匀采样
            sample_indices = [int(i * frame_count / self.sample_frames) for i in range(self.sample_frames)]
        
        signatures = []
        current_frame = 0
        
        for frame_idx in sample_indices:
            # 定位到目标帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                # 如果无法读取某一帧，尝试下一帧
                continue
            
            # 处理帧: 转灰度 -> 计算直方图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 提取多种特征
            # 1. 灰度直方图特征
            hist = cv2.calcHist([gray], [0], None, [self.hist_bins], [0, 256])
            hist = cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            
            # 2. 添加边缘特征 (可选)
            edges = cv2.Canny(gray, 100, 200)
            edge_hist = cv2.calcHist([edges], [0], None, [2], [0, 256])
            edge_hist = cv2.normalize(edge_hist, edge_hist, 0, 1, cv2.NORM_MINMAX)
            
            # 组合特征
            combined_features = np.concatenate([hist.flatten(), edge_hist.flatten()])
            signatures.append(combined_features)
        
        # 释放视频流
        cap.release()
        
        if not signatures:
            raise ValueError(f"无法从视频中提取特征: {video_path}")
        
        # 返回所有特征的平均值作为最终指纹
        return np.mean(signatures, axis=0)
    
    def compare_signatures(self, sig1: np.ndarray, sig2: np.ndarray) -> float:
        """
        比较两个视频指纹的相似度
        
        Args:
            sig1: 第一个视频指纹
            sig2: 第二个视频指纹
            
        Returns:
            float: 相似度分数 (0-1，1表示完全相同)
        """
        if sig1.shape != sig2.shape:
            raise ValueError(f"指纹维度不匹配: {sig1.shape} vs {sig2.shape}")
        
        # 使用余弦相似度
        similarity = 1 - cosine(sig1, sig2)
        return similarity
    
    def compare_videos(self, video_path1: str, video_path2: str) -> float:
        """
        直接比较两个视频的相似度
        
        Args:
            video_path1: 第一个视频路径
            video_path2: 第二个视频路径
            
        Returns:
            float: 相似度分数 (0-1，1表示完全相同)
        """
        sig1 = self.extract_signature(video_path1)
        sig2 = self.extract_signature(video_path2)
        return self.compare_signatures(sig1, sig2)
    
    def batch_extract_signatures(self, video_paths: List[str]) -> Dict[str, np.ndarray]:
        """
        批量提取多个视频的指纹
        
        Args:
            video_paths: 视频文件路径列表
            
        Returns:
            Dict[str, np.ndarray]: 视频路径到指纹的映射
        """
        signatures = {}
        for video_path in video_paths:
            try:
                signatures[video_path] = self.extract_signature(video_path)
            except Exception as e:
                print(f"处理视频 {video_path} 时出错: {str(e)}")
        return signatures
    
    def find_similar_videos(self, target_video: str, video_collection: List[str], 
                           threshold: float = 0.95) -> List[Tuple[str, float]]:
        """
        在视频集合中查找与目标视频相似的视频
        
        Args:
            target_video: 目标视频路径
            video_collection: 视频集合路径列表
            threshold: 相似度阈值
            
        Returns:
            List[Tuple[str, float]]: 相似视频列表，每项包含视频路径和相似度
        """
        # 提取目标视频指纹
        target_sig = self.extract_signature(target_video)
        
        # 比对所有视频
        similar_videos = []
        for video_path in video_collection:
            try:
                # 跳过自身比对
                if os.path.abspath(video_path) == os.path.abspath(target_video):
                    continue
                
                # 提取并比对
                sig = self.extract_signature(video_path)
                similarity = self.compare_signatures(target_sig, sig)
                
                # 如果相似度高于阈值，加入结果
                if similarity >= threshold:
                    similar_videos.append((video_path, similarity))
            except Exception as e:
                print(f"处理视频 {video_path} 时出错: {str(e)}")
        
        # 按相似度降序排序
        similar_videos.sort(key=lambda x: x[1], reverse=True)
        return similar_videos

def extract_video_signature(video_path: str) -> np.ndarray:
    """
    提取视频关键帧特征指纹
    
    此函数是VideoFingerprint类的简化接口，用于直接从视频提取指纹。
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        np.ndarray: 视频特征指纹向量
    """
    fingerprinter = VideoFingerprint()
    return fingerprinter.extract_signature(video_path)

def compare_videos(video_path1: str, video_path2: str) -> float:
    """
    比较两个视频的相似度
    
    Args:
        video_path1: 第一个视频路径
        video_path2: 第二个视频路径
        
    Returns:
        float: 相似度分数 (0-1，1表示完全相同)
    """
    fingerprinter = VideoFingerprint()
    return fingerprinter.compare_videos(video_path1, video_path2)

if __name__ == "__main__":
    # 简单测试代码
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print(f"提取视频指纹: {video_path}")
        try:
            signature = extract_video_signature(video_path)
            print(f"指纹维度: {signature.shape}")
            print(f"指纹前10个值: {signature[:10]}")
        except Exception as e:
            print(f"处理出错: {str(e)}")
    elif len(sys.argv) > 2:
        video_path1 = sys.argv[1]
        video_path2 = sys.argv[2]
        print(f"比较视频相似度:")
        print(f"视频1: {video_path1}")
        print(f"视频2: {video_path2}")
        try:
            similarity = compare_videos(video_path1, video_path2)
            print(f"相似度: {similarity:.4f}")
            if similarity > 0.99:
                print("判定: 相同视频的不同版本")
            elif similarity > 0.7:
                print("判定: 高度相似的视频")
            else:
                print("判定: 不同的视频")
        except Exception as e:
            print(f"处理出错: {str(e)}")
    else:
        print("使用方法:")
        print("  单个视频: python video_fingerprint.py <视频路径>")
        print("  视频比较: python video_fingerprint.py <视频路径1> <视频路径2>") 