#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练数据处理器
处理和预处理训练数据
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TrainingDataProcessor:
    """训练数据处理器"""
    
    def __init__(self):
        """初始化数据处理器"""
        logger.info("训练数据处理器初始化完成")
    
    def process_training_data(self, training_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理训练数据
        
        Args:
            training_data: 原始训练数据
            
        Returns:
            处理后的训练数据
        """
        try:
            processed_data = []
            
            for item in training_data:
                processed_item = {
                    "original_text": item.get("original_text", ""),
                    "viral_text": item.get("viral_text", ""),
                    "engagement_score": item.get("engagement_score", 0.0),
                    "category": item.get("category", "unknown"),
                    "features": self._extract_features(item)
                }
                processed_data.append(processed_item)
            
            logger.info(f"处理了 {len(processed_data)} 个训练样本")
            return processed_data
            
        except Exception as e:
            logger.error(f"训练数据处理失败: {e}")
            return []
    
    def _extract_features(self, item: Dict[str, Any]) -> List[float]:
        """提取特征"""
        try:
            # 简单的特征提取
            original_text = item.get("original_text", "")
            viral_text = item.get("viral_text", "")
            
            features = [
                len(original_text),  # 原文长度
                len(viral_text),     # 爆款文长度
                len(viral_text.split()),  # 词数
                item.get("engagement_score", 0.0),  # 参与度分数
                1.0 if "！" in viral_text else 0.0,  # 是否有感叹号
                1.0 if "震撼" in viral_text else 0.0,  # 是否有震撼词汇
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return [0.0] * 6
