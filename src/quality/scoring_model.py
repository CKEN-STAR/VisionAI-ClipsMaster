#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多维度评分模型

基于多个维度综合评估视频质量，包括技术质量与艺术质量。
该模型结合了客观指标与主观评价，提供全面的质量评分。
"""

import os
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from src.utils.log_handler import get_logger
from src.config.constants import QUALITY_THRESHOLDS
from src.utils.file_handler import ensure_dir_exists

# 获取logger
logger = get_logger("quality_scorer")

class QualityScorer(nn.Module):
    """
    多维度质量评分模型
    
    将视频质量拆分为技术维度与艺术维度进行评分,
    技术维度关注编码质量、分辨率等客观指标,
    艺术维度关注构图、色彩、节奏等主观因素。
    """
    
    def __init__(self):
        """初始化多维度评分模型"""
        super(QualityScorer, self).__init__()
        
        # 技术维度评分层
        self.tech_layer = nn.Sequential(
            nn.Linear(5, 10),
            nn.ReLU(),
            nn.Linear(10, 5),
            nn.ReLU(),
            nn.Linear(5, 1),
            nn.Sigmoid()
        )
        
        # 艺术维度评分层
        self.art_layer = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU(),
            nn.Linear(4, 1),
            nn.Sigmoid()
        )
        
        # 加载预训练权重（如果存在）
        self._load_weights()
        
        # 定义技术指标权重
        self.tech_weights = {
            "vmaf": 0.4,          # 视频多方法评估融合
            "bitrate": 0.2,       # 视频码率
            "resolution": 0.15,   # 分辨率
            "fps": 0.15,          # 帧率
            "audio_quality": 0.1  # 音频质量
        }
        
        # 定义艺术指标权重
        self.art_weights = {
            "color_grading": 0.3,  # 色彩分级
            "framing": 0.3,        # 画面构图
            "pacing": 0.2,         # 节奏控制
            "scene_flow": 0.2      # 场景流畅度
        }
        
        # 维度权重
        self.dimension_weights = {
            "technical": 0.6,  # 技术维度权重
            "artistic": 0.4    # 艺术维度权重
        }
        
        logger.info("多维度质量评分模型初始化完成")
    
    def _load_weights(self):
        """加载预训练权重"""
        weights_path = os.path.join("models", "quality", "scorer_weights.pth")
        
        if os.path.exists(weights_path):
            try:
                self.load_state_dict(torch.load(weights_path))
                logger.info(f"从 {weights_path} 加载模型权重成功")
            except Exception as e:
                logger.error(f"加载模型权重失败: {str(e)}")
        else:
            logger.warning(f"未找到预训练权重文件: {weights_path}")
    
    def forward(self, features: Dict[str, Any]) -> float:
        """
        综合质量评分模型
        
        Args:
            features: 特征字典，包含技术和艺术特征
            
        Returns:
            float: 综合质量得分 (0-1)
        """
        # 提取技术特征
        tech_features = self._extract_tech_features(features)
        
        # 提取艺术特征
        art_features = self._extract_art_features(features)
        
        # 计算技术得分
        technical_score = self._compute_technical_score(tech_features)
        
        # 计算艺术得分
        artistic_score = self._compute_artistic_score(art_features)
        
        # 计算加权综合得分
        final_score = (
            self.dimension_weights["technical"] * technical_score + 
            self.dimension_weights["artistic"] * artistic_score
        )
        
        logger.debug(f"技术得分: {technical_score:.2f}, 艺术得分: {artistic_score:.2f}, 最终得分: {final_score:.2f}")
        
        return final_score
    
    def _extract_tech_features(self, features: Dict[str, Any]) -> torch.Tensor:
        """
        提取技术特征
        
        Args:
            features: 特征字典
            
        Returns:
            torch.Tensor: 技术特征张量
        """
        # 提取技术指标并归一化
        vmaf = features.get("vmaf", 0) / 100.0
        bitrate = min(features.get("bitrate", 0) / 10000.0, 1.0)  # 10Mbps归一化
        
        # 分辨率归一化 (参考4K分辨率)
        resolution = features.get("resolution", [1280, 720])
        if isinstance(resolution, list) and len(resolution) >= 2:
            width, height = resolution[0], resolution[1]
        else:
            width, height = 1280, 720
        
        resolution_score = min((width * height) / (3840 * 2160), 1.0)
        
        # 帧率归一化 (参考60fps)
        fps = min(features.get("fps", 30) / 60.0, 1.0)
        
        # 音频质量归一化
        audio_quality = features.get("audio_quality", 0.5)
        
        # 构建特征向量
        tech_tensor = torch.tensor([
            vmaf, bitrate, resolution_score, fps, audio_quality
        ], dtype=torch.float32)
        
        return tech_tensor
    
    def _extract_art_features(self, features: Dict[str, Any]) -> torch.Tensor:
        """
        提取艺术特征
        
        Args:
            features: 特征字典
            
        Returns:
            torch.Tensor: 艺术特征张量
        """
        # 提取艺术指标
        color_grading = features.get("color_grading", 0.5)
        framing = features.get("framing", 0.5)
        pacing = features.get("pacing", 0.5)
        scene_flow = features.get("scene_flow", 0.5)
        
        # 构建特征向量
        art_tensor = torch.tensor([
            color_grading, framing, pacing, scene_flow
        ], dtype=torch.float32)
        
        return art_tensor
    
    def _compute_technical_score(self, features: torch.Tensor) -> float:
        """
        计算技术质量得分
        
        Args:
            features: 技术特征张量
            
        Returns:
            float: 技术质量得分 (0-1)
        """
        # 使用神经网络或加权求和
        if self.training:
            with torch.no_grad():
                score = self.tech_layer(features).item()
        else:
            # 简化计算: 加权求和
            tech_features = features.numpy()
            weights = np.array(list(self.tech_weights.values()))
            score = np.sum(tech_features * weights)
            score = min(max(score, 0.0), 1.0)  # 限制在[0,1]范围
            
        return score
    
    def _compute_artistic_score(self, features: torch.Tensor) -> float:
        """
        计算艺术质量得分
        
        Args:
            features: 艺术特征张量
            
        Returns:
            float: 艺术质量得分 (0-1)
        """
        # 使用神经网络或加权求和
        if self.training:
            with torch.no_grad():
                score = self.art_layer(features).item()
        else:
            # 简化计算: 加权求和
            art_features = features.numpy()
            weights = np.array(list(self.art_weights.values()))
            score = np.sum(art_features * weights)
            score = min(max(score, 0.0), 1.0)  # 限制在[0,1]范围
            
        return score
    
    def tech_layer(self, features: Dict[str, Any]) -> float:
        """
        技术层评分函数 - 可直接调用的接口
        
        Args:
            features: 特征字典
            
        Returns:
            float: 技术得分
        """
        tech_features = self._extract_tech_features(features)
        return self._compute_technical_score(tech_features)
    
    def art_layer(self, features: Dict[str, Any]) -> float:
        """
        艺术层评分函数 - 可直接调用的接口
        
        Args:
            features: 特征字典
            
        Returns:
            float: 艺术得分
        """
        art_features = self._extract_art_features(features)
        return self._compute_artistic_score(art_features)
    
    def save_weights(self, path: Optional[str] = None):
        """
        保存模型权重
        
        Args:
            path: 保存路径
        """
        if path is None:
            path = os.path.join("models", "quality", "scorer_weights.pth")
        
        # 确保目录存在
        ensure_dir_exists(os.path.dirname(path))
        
        try:
            torch.save(self.state_dict(), path)
            logger.info(f"模型权重已保存至: {path}")
        except Exception as e:
            logger.error(f"保存模型权重失败: {str(e)}")
    
    def get_quality_rating(self, score: float) -> str:
        """
        获取质量等级评定
        
        Args:
            score: 质量得分 (0-1)
            
        Returns:
            str: 质量等级 (S/A/B/C/D)
        """
        # 转换为百分制
        percent_score = score * 100
        
        # 按阈值判断等级
        if percent_score >= QUALITY_THRESHOLDS.QUALITY_RATINGS["S"]:
            return "S"
        elif percent_score >= QUALITY_THRESHOLDS.QUALITY_RATINGS["A"]:
            return "A"
        elif percent_score >= QUALITY_THRESHOLDS.QUALITY_RATINGS["B"]:
            return "B"
        elif percent_score >= QUALITY_THRESHOLDS.QUALITY_RATINGS["C"]:
            return "C"
        else:
            return "D"
    
    def generate_report(self, features: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        生成质量评分报告
        
        Args:
            features: 特征字典
            output_path: 报告输出路径
            
        Returns:
            Dict[str, Any]: 评分报告
        """
        # 计算各维度得分
        tech_score = self.tech_layer(features)
        art_score = self.art_layer(features)
        final_score = self.forward(features)
        
        # 获取质量等级
        quality_rating = self.get_quality_rating(final_score)
        
        # 创建报告
        report = {
            "overall_score": round(final_score, 4),
            "quality_rating": quality_rating,
            "dimensions": {
                "technical": {
                    "score": round(tech_score, 4),
                    "features": {k: features.get(k, None) for k in self.tech_weights.keys()}
                },
                "artistic": {
                    "score": round(art_score, 4),
                    "features": {k: features.get(k, None) for k in self.art_weights.keys()}
                }
            },
            "recommendations": self._generate_recommendations(features, tech_score, art_score)
        }
        
        # 如果提供了输出路径，保存报告
        if output_path:
            ensure_dir_exists(os.path.dirname(output_path))
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                logger.info(f"质量评分报告已保存至: {output_path}")
            except Exception as e:
                logger.error(f"保存质量报告失败: {str(e)}")
        
        return report
    
    def _generate_recommendations(self, features: Dict[str, Any], tech_score: float, art_score: float) -> List[str]:
        """
        生成质量改进建议
        
        Args:
            features: 特征字典
            tech_score: 技术得分
            art_score: 艺术得分
            
        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []
        
        # 技术维度建议
        if tech_score < 0.7:
            # 检查各个技术指标
            if features.get("vmaf", 0) / 100.0 < 0.7:
                recommendations.append("视频质量偏低，建议提高编码质量或码率")
            
            if features.get("bitrate", 0) / 10000.0 < 0.5:
                recommendations.append("视频码率较低，考虑增加码率以提高画面清晰度")
            
            resolution = features.get("resolution", [1280, 720])
            if isinstance(resolution, list) and len(resolution) >= 2:
                width, height = resolution[0], resolution[1]
                if width * height < 1280 * 720:
                    recommendations.append("视频分辨率较低，建议提高至少720p")
            
            if features.get("fps", 30) < 24:
                recommendations.append("帧率过低，可能影响观看流畅度，建议提高至24fps以上")
            
            if features.get("audio_quality", 0.5) < 0.6:
                recommendations.append("音频质量有待提高，检查音频码率或考虑降噪处理")
        
        # 艺术维度建议
        if art_score < 0.7:
            if features.get("color_grading", 0.5) < 0.6:
                recommendations.append("色彩处理有提升空间，考虑调整色彩分级以增强视觉吸引力")
            
            if features.get("framing", 0.5) < 0.6:
                recommendations.append("画面构图可以优化，注意主体突出和空间平衡")
            
            if features.get("pacing", 0.5) < 0.6:
                recommendations.append("节奏控制有待改进，考虑优化剪辑节奏以保持观众注意力")
            
            if features.get("scene_flow", 0.5) < 0.6:
                recommendations.append("场景转换流畅度不足，可优化转场效果或调整场景顺序")
        
        return recommendations


def score_video_quality(video_path: str, features: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    评估视频质量的便捷函数
    
    Args:
        video_path: 视频文件路径
        features: 预提取的特征，如果为None则自动提取
        
    Returns:
        Dict[str, Any]: 质量评分报告
    """
    from src.quality.metrics import extract_video_features
    
    # 初始化评分模型
    scorer = QualityScorer()
    
    # 如果没有提供特征，则提取特征
    if features is None:
        features = extract_video_features(video_path)
    
    # 生成评分报告
    report_path = os.path.join(
        "data", 
        "quality_reports", 
        f"quality_score_{Path(video_path).stem}.json"
    )
    
    return scorer.generate_report(features, report_path) 