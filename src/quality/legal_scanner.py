#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
法律合规扫描器模块

提供版权水印检测、敏感内容筛查、合规审计等功能。
主要功能包括：
1. 视频水印检测
2. 图像水印检测
3. 版权合规检查
4. 隐私敏感信息检测
5. 违规内容筛查
"""

import os
import json
import re
import logging
import numpy as np
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from pathlib import Path

from loguru import logger
from src.utils.file_handler import ensure_dir_exists

# 尝试导入CV和视频处理库
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    logger.warning("未安装OpenCV，部分水印检测功能将受限")
    CV2_AVAILABLE = False

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    logger.warning("未安装ffmpeg-python，部分视频处理功能将受限")
    FFMPEG_AVAILABLE = False


class WatermarkDatabase:
    """
    水印数据库，用于存储和比对已知的水印特征
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化水印数据库
        
        Args:
            db_path: 水印特征数据库路径，如果不提供则使用默认路径
        """
        # 设置默认路径
        if db_path is None:
            db_path = os.path.join("data", "watermarks", "database.json")
        
        self.db_path = db_path
        self.watermarks: Dict[str, Any] = {}
        self.features: Dict[str, np.ndarray] = {}
        self.signatures: Set[str] = set()
        
        # 确保数据库目录存在
        ensure_dir_exists(os.path.dirname(db_path))
        
        # 加载数据库
        self._load_database()
        logger.debug(f"已加载 {len(self.watermarks)} 个水印特征")
    
    def _load_database(self) -> None:
        """加载水印数据库"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    db_data = json.load(f)
                
                # 加载水印数据
                self.watermarks = db_data.get("watermarks", {})
                
                # 处理特征向量
                for wm_id, wm_data in self.watermarks.items():
                    if "features" in wm_data and wm_data["features"]:
                        # 转换特征为numpy数组
                        self.features[wm_id] = np.array(wm_data["features"])
                    
                    # 加载签名
                    if "signature" in wm_data and wm_data["signature"]:
                        self.signatures.add(wm_data["signature"])
                
                logger.debug(f"从 {self.db_path} 加载了 {len(self.watermarks)} 个水印特征")
            except Exception as e:
                logger.error(f"加载水印数据库失败: {str(e)}")
                # 初始化空数据库
                self.watermarks = {}
                self.features = {}
                self.signatures = set()
        else:
            logger.warning(f"水印数据库文件不存在: {self.db_path}，将创建新数据库")
            # 初始化空数据库
            self.watermarks = {}
            self.features = {}
            self.signatures = set()
    
    def add_watermark(self, name: str, features: List[float], signature: str, 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加水印特征到数据库
        
        Args:
            name: 水印名称
            features: 水印特征向量
            signature: 水印签名
            metadata: 水印相关元数据
            
        Returns:
            str: 水印ID
        """
        # 生成唯一ID
        import uuid
        wm_id = str(uuid.uuid4())
        
        # 创建水印记录
        watermark_data = {
            "id": wm_id,
            "name": name,
            "features": features,
            "signature": signature,
            "metadata": metadata or {},
            "added_at": str(datetime.datetime.now())
        }
        
        # 保存到数据库
        self.watermarks[wm_id] = watermark_data
        self.features[wm_id] = np.array(features)
        self.signatures.add(signature)
        
        # 保存数据库
        self._save_database()
        
        return wm_id
    
    def _save_database(self) -> None:
        """保存水印数据库"""
        try:
            # 确保目录存在
            ensure_dir_exists(os.path.dirname(self.db_path))
            
            # 构建保存数据
            db_data = {
                "watermarks": self.watermarks,
                "updated_at": str(datetime.datetime.now())
            }
            
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(db_data, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"已保存 {len(self.watermarks)} 个水印特征到 {self.db_path}")
        except Exception as e:
            logger.error(f"保存水印数据库失败: {str(e)}")
    
    def match_features(self, features: List[float], threshold: float = 0.85) -> Optional[str]:
        """
        匹配水印特征
        
        Args:
            features: 待匹配的特征向量
            threshold: 匹配阈值，越高要求越严格
            
        Returns:
            Optional[str]: 匹配的水印ID，如果没有匹配则返回None
        """
        if not self.features:
            return None
        
        # 将输入特征转换为numpy数组
        input_features = np.array(features)
        
        # 计算相似度并找到最佳匹配
        best_match = None
        best_similarity = 0.0
        
        for wm_id, wm_features in self.features.items():
            # 计算余弦相似度
            similarity = self._cosine_similarity(input_features, wm_features)
            
            if similarity > threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = wm_id
        
        return best_match
    
    def match_signature(self, signature: str) -> bool:
        """
        匹配水印签名
        
        Args:
            signature: 待匹配的签名
            
        Returns:
            bool: 是否匹配成功
        """
        return signature in self.signatures
    
    def match_any(self, frame: np.ndarray) -> bool:
        """
        检查图像帧是否包含任何已知水印
        
        Args:
            frame: 图像帧
            
        Returns:
            bool: 是否包含水印
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未安装，无法进行水印特征提取")
            return False
        
        try:
            # 提取特征
            features = self._extract_features(frame)
            
            # 匹配特征
            match_id = self.match_features(features)
            
            return match_id is not None
        except Exception as e:
            logger.error(f"水印匹配失败: {str(e)}")
            return False
    
    def _extract_features(self, frame: np.ndarray) -> List[float]:
        """
        从图像帧提取水印特征
        
        Args:
            frame: 图像帧
            
        Returns:
            List[float]: 提取的特征向量
        """
        # 灰度化
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 提取HOG特征
        winSize = (64, 64)
        blockSize = (16, 16)
        blockStride = (8, 8)
        cellSize = (8, 8)
        nbins = 9
        
        hog = cv2.HOGDescriptor(winSize, blockSize, blockStride, cellSize, nbins)
        resized = cv2.resize(gray, winSize)
        hog_features = hog.compute(resized)
        
        # 转为列表
        return hog_features.flatten().tolist()
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        计算余弦相似度
        
        Args:
            a: 向量a
            b: 向量b
            
        Returns:
            float: 余弦相似度
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return np.dot(a, b) / (norm_a * norm_b)


class CopyrightValidator:
    """
    版权验证器，用于检测媒体内容的版权合规性
    """
    
    def __init__(self):
        """初始化版权验证器"""
        self.watermark_lib = WatermarkDatabase()
        
        # 版权关键词
        self.copyright_keywords = [
            "版权所有", "©", "著作权", "All Rights Reserved", "Copyright", 
            "保留所有权利", "知识产权", "未经许可", "授权使用"
        ]
        
        # 配置参数
        self.config = self._load_config()
        
        # 水印检测参数
        self.watermark_params = self.config.get("content_security", {}).get(
            "watermark_detection", 
            {
                "enabled": True,
                "min_area": 100,
                "max_area": 10000,
                "threshold": 240
            }
        )
        
        # 水印检测设置
        self.scan_depth = self.config.get("watermark_check", {}).get("scan_depth", 3)
        
        logger.debug("版权验证器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        config_path = "configs/security_policy.json"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def full_scan(self, video_path: str) -> bool:
        """
        全片版权水印检测
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            bool: 是否通过检测（无水印返回True）
        """
        if not os.path.exists(video_path):
            logger.warning(f"视频文件不存在: {video_path}")
            return False
        
        # 提取关键帧
        frames = extract_key_frames(video_path)
        
        # 检查每一帧
        for frame in frames:
            if self.watermark_lib.match_any(frame):
                return False  # 检测到水印，返回不通过
        
        # 未检测到水印，返回通过
        return True
    
    def check_text_copyright(self, text: str) -> bool:
        """
        检查文本中是否包含版权声明
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否包含版权声明
        """
        if not text:
            return False
        
        # 检查是否包含版权关键词
        for keyword in self.copyright_keywords:
            if keyword in text:
                return True
        
        # 使用正则表达式检查更复杂的版权模式
        copyright_patterns = [
            r'©\s*\d{4}',  # © 2023
            r'版权\s*[©]\s*\d{4}',  # 版权 © 2023
            r'Copyright\s*[©]\s*\d{4}',  # Copyright © 2023
            r'All\s*Rights\s*Reserved',  # All Rights Reserved
            r'保留\s*所有\s*权利'  # 保留所有权利
        ]
        
        for pattern in copyright_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def check_metadata_copyright(self, media_path: str) -> bool:
        """
        检查媒体文件元数据中的版权信息
        
        Args:
            media_path: 媒体文件路径
            
        Returns:
            bool: 是否包含版权信息
        """
        if not FFMPEG_AVAILABLE:
            logger.warning("ffmpeg-python未安装，无法提取元数据")
            return False
        
        try:
            # 使用ffprobe提取元数据
            probe = ffmpeg.probe(media_path)
            
            # 检查格式元数据
            format_tags = probe.get("format", {}).get("tags", {})
            
            # 检查常见版权字段
            copyright_fields = ["copyright", "Copyright", "COPYRIGHT", "版权"]
            
            for field in copyright_fields:
                if field in format_tags:
                    return True
            
            # 检查其他元数据
            for stream in probe.get("streams", []):
                stream_tags = stream.get("tags", {})
                for field in copyright_fields:
                    if field in stream_tags:
                        return True
            
            # 检查评论字段中的版权信息
            comment_fields = ["comment", "COMMENT", "Comment", "comments", "Comments"]
            for field in comment_fields:
                if field in format_tags:
                    comment = format_tags[field]
                    if self.check_text_copyright(comment):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"提取元数据失败: {str(e)}")
            return False


def extract_key_frames(video_path: str, max_frames: int = 10) -> List[np.ndarray]:
    """
    从视频中提取关键帧
    
    Args:
        video_path: 视频文件路径
        max_frames: 最大提取帧数
        
    Returns:
        List[np.ndarray]: 提取的关键帧列表
    """
    if not CV2_AVAILABLE:
        logger.warning("OpenCV未安装，无法提取关键帧")
        return []
    
    try:
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return []
        
        # 获取视频信息
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = frame_count / fps if fps > 0 else 0
        
        # 计算采样间隔
        interval = max(1, frame_count // max_frames)
        
        # 提取帧
        frames = []
        positions = list(range(0, frame_count, interval))[:max_frames]
        
        for pos in positions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        
        # 释放视频
        cap.release()
        
        # 如果没有提取到足够的帧，尝试场景变化检测
        if len(frames) < 3 and frame_count > 100:
            logger.info(f"采样关键帧数量不足，尝试场景变化检测")
            return detect_scene_changes(video_path, max_frames)
        
        return frames
    except Exception as e:
        logger.error(f"提取关键帧失败: {str(e)}")
        return []


def detect_scene_changes(video_path: str, max_scenes: int = 10) -> List[np.ndarray]:
    """
    检测视频场景变化并提取关键帧
    
    Args:
        video_path: 视频文件路径
        max_scenes: 最大场景数
        
    Returns:
        List[np.ndarray]: 场景关键帧列表
    """
    if not CV2_AVAILABLE:
        return []
    
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        # 读取第一帧
        ret, prev_frame = cap.read()
        if not ret:
            return []
        
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        frames = [prev_frame]  # 添加第一帧
        
        # 设置阈值
        threshold = 30.0
        
        while len(frames) < max_scenes:
            ret, curr_frame = cap.read()
            if not ret:
                break
            
            # 转换为灰度
            curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
            
            # 计算帧差异
            frame_diff = cv2.absdiff(curr_gray, prev_gray)
            mean_diff = np.mean(frame_diff)
            
            # 如果差异超过阈值，认为是场景变化
            if mean_diff > threshold:
                frames.append(curr_frame)
                
            # 更新前一帧
            prev_gray = curr_gray
        
        cap.release()
        return frames
    except Exception as e:
        logger.error(f"场景变化检测失败: {str(e)}")
        return [] 