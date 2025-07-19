#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
黄金标准对比引擎

提供对生成的短视频进行质量评估的功能，通过与黄金标准样本进行对比，
评估结构相似性、峰值信噪比和运动一致性等指标。
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from pathlib import Path

from .metrics import calculate_ssim, calculate_psnr, optical_flow_analysis
from ..config.constants import QUALITY_THRESHOLDS
from ..utils.file_utils import get_file_path
from ..utils.error_handler import handle_exception

# 配置日志
logger = logging.getLogger(__name__)

# 默认阈值 (在constants.py中没有定义时使用)
DEFAULT_THRESHOLDS = {
    "ssim": 0.92,
    "psnr": 38.0,
    "motion_consistency": 0.85
}

def load_golden_dataset(dataset_name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """加载黄金标准数据集
    
    从数据存储中加载预先选择的高质量样本集，用于对比评估。
    
    Args:
        dataset_name: 数据集名称，如果为None则加载默认数据集
        
    Returns:
        Dict[str, Dict[str, Any]]: 样本ID到样本数据的映射
    """
    try:
        # 确定数据集路径
        if dataset_name is None:
            dataset_name = "default_golden_set"
            
        dataset_path = get_file_path(f"data/golden_samples/{dataset_name}.json")
        
        # 如果文件不存在，创建一个演示数据集
        if not os.path.exists(dataset_path):
            logger.warning(f"黄金标准数据集 {dataset_name} 不存在，创建演示数据集")
            return _create_demo_dataset(dataset_path)
            
        # 加载数据集
        with open(dataset_path, 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
            
        logger.info(f"已加载黄金标准数据集: {dataset_name}，包含 {len(golden_data)} 个样本")
        return golden_data
    
    except Exception as e:
        handle_exception(e, "加载黄金标准数据集失败")
        # 返回空数据集
        return {}

def _create_demo_dataset(save_path: str) -> Dict[str, Dict[str, Any]]:
    """创建演示数据集
    
    当没有找到黄金标准数据集时，创建一个演示数据集
    
    Args:
        save_path: 保存路径
        
    Returns:
        Dict[str, Dict[str, Any]]: 演示数据集
    """
    # 创建演示数据
    demo_data = {
        "sample_001": {
            "title": "经典喜剧场景重组",
            "path": "samples/comedy_remix_001.mp4",
            "duration": 120.5,
            "category": "comedy",
            "tags": ["funny", "classic", "dialogue_driven"],
            "metrics": {
                "ssim_baseline": 0.95,
                "psnr_baseline": 42.3,
                "motion_consistency_baseline": 0.92,
                "audio_quality_baseline": 0.88
            },
            "metadata": {
                "resolution": "1080p",
                "fps": 30,
                "audio_sample_rate": 44100
            }
        },
        "sample_002": {
            "title": "动作片精彩片段",
            "path": "samples/action_highlights_002.mp4",
            "duration": 95.2,
            "category": "action",
            "tags": ["fast_paced", "dramatic", "visual_effects"],
            "metrics": {
                "ssim_baseline": 0.93,
                "psnr_baseline": 40.5,
                "motion_consistency_baseline": 0.89,
                "audio_quality_baseline": 0.91
            },
            "metadata": {
                "resolution": "1080p",
                "fps": 30,
                "audio_sample_rate": 48000
            }
        },
        "sample_003": {
            "title": "情感戏剧高潮部分",
            "path": "samples/drama_climax_003.mp4",
            "duration": 150.8,
            "category": "drama",
            "tags": ["emotional", "character_focused", "dialogue_driven"],
            "metrics": {
                "ssim_baseline": 0.96,
                "psnr_baseline": 43.1,
                "motion_consistency_baseline": 0.94,
                "audio_quality_baseline": 0.92
            },
            "metadata": {
                "resolution": "1080p",
                "fps": 24,
                "audio_sample_rate": 48000
            }
        }
    }
    
    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 保存演示数据集
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"已创建演示黄金标准数据集: {save_path}")
    return demo_data

class GoldenComparator:
    """黄金标准对比器
    
    将生成的短视频与黄金标准样本进行对比，评估质量指标
    """
    
    def __init__(self):
        """初始化黄金标准对比器"""
        self.golden_samples = load_golden_dataset()
        
        # 加载质量阈值
        try:
            self.quality_thresholds = getattr(QUALITY_THRESHOLDS, 'GOLDEN_STANDARD', DEFAULT_THRESHOLDS)
        except (AttributeError, TypeError):
            logger.warning("无法加载质量阈值常量，使用默认值")
            self.quality_thresholds = DEFAULT_THRESHOLDS
        
        logger.info(f"黄金标准对比器初始化完成，使用阈值: {self.quality_thresholds}")
    
    def structural_similarity(self, generated: str, sample_id: str) -> Dict[str, float]:
        """评估生成视频与黄金样本的结构相似性
        
        通过SSIM、PSNR和光流分析比较视频质量
        
        Args:
            generated: 生成视频的路径
            sample_id: 黄金标准样本ID
            
        Returns:
            Dict[str, float]: 包含各项指标的结果字典
        """
        try:
            # 获取黄金样本路径
            if sample_id not in self.golden_samples:
                logger.error(f"样本ID不存在: {sample_id}")
                return {"error": "样本ID不存在"}
                
            golden = self.golden_samples[sample_id]["path"]
            golden_path = get_file_path(golden)
            
            # 执行SSIM比较
            ssim_score = calculate_ssim(generated, golden_path)
            
            # 执行PSNR计算
            psnr_score = calculate_psnr(generated, golden_path)
            
            # 执行光流分析
            motion_score = optical_flow_analysis(generated, golden_path)
            
            # 返回结果
            return {
                "ssim": ssim_score,
                "psnr": psnr_score,
                "motion_consistency": motion_score
            }
            
        except Exception as e:
            logger.error(f"结构相似性评估失败: {str(e)}")
            handle_exception(e, "结构相似性评估失败")
            return {"error": str(e)}
    
    def compare_with_all_samples(self, generated: str) -> Dict[str, Dict[str, Any]]:
        """与所有黄金标准样本比较
        
        将生成的视频与所有黄金标准样本进行比较，找出最匹配的样本
        
        Args:
            generated: 生成视频的路径
            
        Returns:
            Dict[str, Dict[str, Any]]: 所有比较结果，按匹配度排序
        """
        results = {}
        
        for sample_id, sample_data in self.golden_samples.items():
            # 获取比较结果
            comparison = self.structural_similarity(generated, sample_id)
            
            # 如果出错则跳过
            if "error" in comparison:
                continue
                
            # 计算总体匹配分数 (加权平均)
            match_score = (
                comparison["ssim"] * 0.4 + 
                (comparison["psnr"] / 50) * 0.3 + 
                comparison["motion_consistency"] * 0.3
            )
            
            # 存储结果
            results[sample_id] = {
                "sample_data": sample_data,
                "comparison": comparison,
                "match_score": match_score
            }
        
        # 按匹配度排序
        sorted_results = {
            k: v for k, v in sorted(
                results.items(), 
                key=lambda item: item[1]["match_score"], 
                reverse=True
            )
        }
        
        return sorted_results
    
    def get_best_match(self, generated: str) -> Tuple[str, Dict[str, Any]]:
        """获取最佳匹配的黄金样本
        
        Args:
            generated: 生成视频的路径
            
        Returns:
            Tuple[str, Dict[str, Any]]: 最佳匹配的样本ID和详细信息
        """
        comparisons = self.compare_with_all_samples(generated)
        
        if not comparisons:
            return "", {"error": "没有找到匹配的样本"}
            
        # 获取第一个条目 (最佳匹配)
        best_id = next(iter(comparisons))
        return best_id, comparisons[best_id]
    
    def evaluate_quality(self, generated: str, sample_id: Optional[str] = None) -> Dict[str, Any]:
        """评估生成视频的质量
        
        如果提供了sample_id，则与指定的黄金样本比较
        否则，找出最匹配的样本进行比较
        
        Args:
            generated: 生成视频的路径
            sample_id: 黄金标准样本ID (可选)
            
        Returns:
            Dict[str, Any]: 质量评估结果
        """
        # 如果未指定样本ID，找出最佳匹配
        if sample_id is None:
            sample_id, match_info = self.get_best_match(generated)
            
            # 如果没有找到匹配
            if "error" in match_info:
                return {
                    "status": "error",
                    "message": match_info["error"],
                    "passed": False
                }
                
            comparison = match_info["comparison"]
            match_score = match_info["match_score"]
        else:
            # 使用指定的样本ID
            comparison = self.structural_similarity(generated, sample_id)
            
            # 如果出错
            if "error" in comparison:
                return {
                    "status": "error",
                    "message": comparison["error"],
                    "passed": False
                }
                
            # 计算匹配分数
            match_score = (
                comparison["ssim"] * 0.4 + 
                (comparison["psnr"] / 50) * 0.3 + 
                comparison["motion_consistency"] * 0.3
            )
        
        # 检查是否通过质量阈值
        passed_ssim = comparison["ssim"] >= self.quality_thresholds["ssim"]
        passed_psnr = comparison["psnr"] >= self.quality_thresholds["psnr"]
        passed_motion = comparison["motion_consistency"] >= self.quality_thresholds["motion_consistency"]
        
        # 所有指标都通过才算通过
        all_passed = passed_ssim and passed_psnr and passed_motion
        
        # 整体质量评级 (S/A/B/C/D)
        quality_rating = self._get_quality_rating(comparison)
        
        return {
            "status": "success",
            "sample_id": sample_id,
            "comparison": comparison,
            "match_score": match_score,
            "thresholds": self.quality_thresholds,
            "passed_criteria": {
                "ssim": passed_ssim,
                "psnr": passed_psnr,
                "motion_consistency": passed_motion
            },
            "passed": all_passed,
            "quality_rating": quality_rating,
            "sample_info": self.golden_samples.get(sample_id, {})
        }
    
    def _get_quality_rating(self, comparison: Dict[str, float]) -> str:
        """基于比较结果获取质量评级
        
        Args:
            comparison: 比较结果
            
        Returns:
            str: 质量评级 (S/A/B/C/D)
        """
        # 计算综合分数 (满分100)
        ssim_score = min(comparison["ssim"] / 0.96 * 100, 100)
        psnr_score = min(comparison["psnr"] / 45 * 100, 100)
        motion_score = min(comparison["motion_consistency"] / 0.95 * 100, 100)
        
        # 加权平均
        weighted_score = (ssim_score * 0.4 + psnr_score * 0.3 + motion_score * 0.3)
        
        # 评定等级
        if weighted_score >= 95:
            return "S"
        elif weighted_score >= 85:
            return "A"
        elif weighted_score >= 75:
            return "B"
        elif weighted_score >= 65:
            return "C"
        else:
            return "D" 