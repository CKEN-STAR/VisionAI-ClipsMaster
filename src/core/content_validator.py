"""内容验证模块

此模块提供内容验证功能，包括：
1. 版权合规检测
2. 水印检测
3. 敏感内容检测
4. 内容分类和过滤
"""

import os
import re
import json
from typing import Dict, List, Optional, Set, Any, Union
import logging
from loguru import logger

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV (cv2) 未安装，水印检测功能将受限")

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    logger.warning("ffmpeg-python 未安装，视频处理功能将受限")


class ContentValidator:
    """内容验证器，用于检测内容合规性"""
    
    def __init__(self, config_path: str = "configs/security_policy.json"):
        """初始化内容验证器
        
        Args:
            config_path: 安全配置文件路径
        """
        self.config = self._load_config(config_path)
        
        # 版权关键词
        self.copyright_keywords = [
            "版权所有", "©", "著作权", "All Rights Reserved", "Copyright", 
            "保留所有权利", "知识产权", "未经许可", "授权使用"
        ]
        
        # 敏感内容关键词
        self.sensitive_keywords = [
            "暴力", "色情", "政治", "歧视", "侮辱", "犯罪", "恐怖", 
            "毒品", "赌博", "自杀", "血腥"
        ]
        
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
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
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
    
    def check_copyright(self, content: str) -> bool:
        """检查内容是否包含版权声明
        
        Args:
            content: 要检查的文本内容
            
        Returns:
            是否包含版权声明
        """
        if not content:
            return False
        
        # 检查是否包含版权关键词
        for keyword in self.copyright_keywords:
            if keyword in content:
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
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def check_watermark(self, media_path: str) -> bool:
        """检查媒体文件是否包含水印
        
        Args:
            media_path: 媒体文件路径
            
        Returns:
            是否包含水印
        """
        if not os.path.exists(media_path):
            logger.warning(f"媒体文件不存在: {media_path}")
            return False
        
        # 获取文件扩展名
        _, ext = os.path.splitext(media_path)
        ext = ext.lower()
        
        # 根据文件类型选择检测方法
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
            return self._check_image_watermark(media_path)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            return self._check_video_watermark(media_path)
        else:
            logger.warning(f"不支持的媒体文件类型: {ext}")
            return False
    
    def _check_image_watermark(self, image_path: str) -> bool:
        """检查图片是否含有水印
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            是否检测到水印
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未安装，无法进行图片水印检测")
            return False
        
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return False
            
            # 转为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用阈值分割
            thresh = cv2.threshold(
                gray, 
                self.watermark_params.get("threshold", 240), 
                255, 
                cv2.THRESH_BINARY
            )[1]
            
            # 查找轮廓
            contours = cv2.findContours(
                thresh, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )[0]
            
            # 分析轮廓特征判断是否存在水印
            min_area = self.watermark_params.get("min_area", 100)
            max_area = self.watermark_params.get("max_area", 10000)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if min_area < area < max_area:
                    # 水印通常在这个面积范围
                    return True
            
            # 频域检测 (DCT/DFT)
            # 这里可以添加更复杂的频域检测算法
            
            return False
        except Exception as e:
            logger.error(f"图片水印检测失败: {e}")
            return False
    
    def _check_video_watermark(self, video_path: str) -> bool:
        """检查视频是否含有水印
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            是否检测到水印
        """
        if not CV2_AVAILABLE:
            logger.warning("OpenCV未安装，无法进行视频水印检测")
            return False
        
        try:
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                return False
            
            # 获取视频帧数
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 计算采样间隔
            scan_depth = self.config.get("watermark_check", {}).get("scan_depth", 3)
            sample_interval = max(1, frame_count // scan_depth)
            
            # 检查采样帧
            for i in range(scan_depth):
                # 设置位置
                pos = i * sample_interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                
                # 读取帧
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # 创建临时图像文件
                temp_path = os.path.join(os.path.dirname(video_path), f"_temp_frame_{i}.jpg")
                cv2.imwrite(temp_path, frame)
                
                # 检查帧中的水印
                has_watermark = self._check_image_watermark(temp_path)
                
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                # 如果检测到水印，立即返回
                if has_watermark:
                    return True
            
            # 释放视频
            cap.release()
            return False
        except Exception as e:
            logger.error(f"视频水印检测失败: {e}")
            return False
    
    def check_sensitive_content(self, content: str) -> bool:
        """检查内容是否包含敏感词
        
        Args:
            content: 要检查的文本内容
            
        Returns:
            是否包含敏感内容
        """
        if not content:
            return False
        
        # 检查是否包含敏感关键词
        for keyword in self.sensitive_keywords:
            if keyword in content:
                return True
        
        return False
    
    def classify_content(self, content: str) -> str:
        """对内容进行分类
        
        Args:
            content: 要分类的文本内容
            
        Returns:
            内容分类（normal, sensitive, copyright_violation等）
        """
        if not content:
            return "empty"
        
        if self.check_sensitive_content(content):
            return "sensitive"
        
        if self.check_copyright(content):
            return "copyright"
        
        return "normal"
    
    def filter_content(self, content: str) -> str:
        """过滤敏感内容
        
        Args:
            content: 要过滤的文本内容
            
        Returns:
            过滤后的内容
        """
        if not content:
            return ""
        
        filtered_content = content
        
        # 替换敏感关键词
        for keyword in self.sensitive_keywords:
            replacement = "*" * len(keyword)
            filtered_content = filtered_content.replace(keyword, replacement)
        
        return filtered_content 