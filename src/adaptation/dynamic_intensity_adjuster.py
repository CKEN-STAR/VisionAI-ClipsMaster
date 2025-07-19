#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态强度调节器模块

负责实时调整情感强度、冲突激烈度和视觉刺激强度，以创建引人入胜的混剪体验。
根据用户偏好、叙事结构和情感流动动态调整各元素强度，保持观众参与度。

主要功能:
1. 情感强度调节: 控制情感表达的强烈程度和深度
2. 冲突激烈度调节: 管理角色冲突和情节对抗的紧张程度
3. 视觉刺激强度调节: 调整视觉元素的活跃度和冲击力
4. 自适应用户偏好: 学习用户喜好，实时调整强度设置
"""

import os
import math
import json
import yaml
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

from ..utils.config_loader import ConfigLoader
from ..emotion.intensity_mapper import EmotionMapper
from ..emotion.lexicon_enhancer import EmotionLexicon, adjust_emotion_level
from ..narrative.structure_analyzer import identify_narrative_beats

logger = logging.getLogger(__name__)

class DynamicIntensityAdjuster:
    """动态强度调节器类
    
    负责根据叙事需求和用户偏好调整情感、冲突和视觉刺激的强度。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化动态强度调节器
        
        Args:
            config_path: 配置文件路径，如不提供则使用默认配置
        """
        self.config = self._load_config(config_path)
        self.emotion_mapper = EmotionMapper()
        self.emotion_lexicon = EmotionLexicon()
        
        # 用户偏好设置
        self.user_preference = self.config["user_preferences"]["default_preset"]
        self.preset_configs = self.config["user_preferences"]["global_presets"]
        
        # 历史调整数据
        self.adjustment_history = []
        
        logger.info("动态强度调节器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        # 默认配置路径
        if config_path is None:
            module_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(module_dir, "configs", "dynamic_intensity.yaml")
        
        # 加载配置
        try:
            config_loader = ConfigLoader()
            config = config_loader.load(config_path)
            logger.info(f"已加载动态强度调节器配置: {config_path}")
            return config
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """返回默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "user_preferences": {
                "global_presets": {
                    "balanced": {
                        "emotion_intensity": 1.0,
                        "conflict_intensity": 1.0,
                        "visual_intensity": 1.0
                    }
                },
                "default_preset": "balanced",
                "adaptive_adjustment": {
                    "enabled": True,
                    "learning_rate": 0.05,
                    "history_window": 10,
                    "min_samples": 5
                }
            },
            "emotion_intensity": {
                "adjustment_factors": {
                    "text_intensity": 0.4,
                    "dialog_intensity": 0.3,
                    "action_intensity": 0.3
                },
                "type_specific": {
                    "joy": 1.0,
                    "sadness": 1.1,
                    "anger": 1.2,
                    "fear": 1.15,
                    "surprise": 1.05,
                    "disgust": 0.95
                },
                "peak_adjustment": {
                    "enabled": True,
                    "peak_boost": 1.2,
                    "valley_reduction": 0.9,
                    "transition_smoothing": 0.8
                }
            },
            "conflict_intensity": {
                "element_weights": {
                    "dialog_confrontation": 0.35,
                    "action_conflict": 0.4,
                    "tension_build": 0.25
                },
                "type_adjustment": {
                    "verbal": 0.9,
                    "physical": 1.1,
                    "emotional": 1.0,
                    "psychological": 1.05
                },
                "narrative_adjustment": {
                    "rising_action": 1.1,
                    "climax": 1.3,
                    "falling_action": 0.9,
                    "resolution": 0.8
                }
            },
            "visual_intensity": {
                "element_weights": {
                    "movement": 0.3,
                    "color_contrast": 0.25,
                    "scene_transitions": 0.2,
                    "facial_expressions": 0.25
                },
                "style_adjustment": {
                    "fast_paced": 1.2,
                    "slow_paced": 0.9,
                    "high_contrast": 1.15,
                    "low_contrast": 0.85
                }
            },
            "adjustment_rules": {
                "consecutive_scenes": {
                    "max_similar_intensity": 3,
                    "variation_threshold": 0.15,
                    "forced_variation": 0.2
                },
                "rate_limiting": {
                    "max_increase_rate": 0.3,
                    "max_decrease_rate": 0.25,
                    "smoothing_window": 2
                },
                "narrative_nodes": {
                    "introduction_factor": 0.9,
                    "buildup_factor": 1.05,
                    "climax_factor": 1.25,
                    "resolution_factor": 0.85
                }
            }
        }
    
    def set_user_preference(self, preset: str) -> bool:
        """设置用户偏好预设
        
        Args:
            preset: 预设名称，如 'balanced'、'intense'、'subtle' 等
            
        Returns:
            是否成功设置
        """
        if preset in self.preset_configs:
            self.user_preference = preset
            logger.info(f"用户偏好已设置为: {preset}")
            return True
        else:
            logger.warning(f"无效的预设名称: {preset}，可用预设: {list(self.preset_configs.keys())}")
            return False
    
    def get_current_preference(self) -> Dict[str, float]:
        """获取当前用户偏好设置
        
        Returns:
            当前预设的具体配置
        """
        return self.preset_configs[self.user_preference]
    
    def adjust_scenes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """调整场景序列的强度
        
        根据用户偏好、叙事结构和情感流程调整场景的情感、冲突和视觉强度。
        
        Args:
            scenes: 场景列表，每个场景包含文本、情感等信息
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            logger.warning("场景列表为空，无法调整强度")
            return []
        
        # 创建场景副本以避免修改原始数据
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 分析叙事结构
        narrative_structure = self._analyze_narrative_structure(adjusted_scenes)
        
        # 应用情感流程分析
        emotion_flow = self._analyze_emotion_flow(adjusted_scenes)
        
        # 应用连续调整规则
        adjusted_scenes = self._apply_sequence_rules(adjusted_scenes, narrative_structure)
        
        # 逐个处理场景
        for i, scene in enumerate(adjusted_scenes):
            # 获取叙事位置信息
            narrative_position = narrative_structure.get(i, 'neutral')
            
            # 获取前后场景进行连续性分析
            prev_scene = adjusted_scenes[i-1] if i > 0 else None
            next_scene = adjusted_scenes[i+1] if i < len(adjusted_scenes) - 1 else None
            
            # 应用情感强度调整
            scene = self._adjust_emotion_intensity(scene, narrative_position, prev_scene)
            
            # 应用冲突强度调整
            scene = self._adjust_conflict_intensity(scene, narrative_position, prev_scene, next_scene)
            
            # 应用视觉强度调整
            scene = self._adjust_visual_intensity(scene, narrative_position)
            
            # 处理速率限制和过渡平滑
            scene = self._smooth_transitions(scene, prev_scene, next_scene)
            
            # 更新到调整后的场景列表
            adjusted_scenes[i] = scene
        
        # 记录调整历史
        self._record_adjustment(adjusted_scenes)
        
        return adjusted_scenes
    
    def _analyze_narrative_structure(self, scenes: List[Dict[str, Any]]) -> Dict[int, str]:
        """分析场景序列的叙事结构
        
        Args:
            scenes: 场景列表
            
        Returns:
            场景索引与叙事节点类型的映射
        """
        try:
            # 使用叙事结构分析器识别叙事节点
            narrative_beats = identify_narrative_beats(scenes)
            
            # 构建索引到叙事位置的映射
            narrative_map = {}
            
            # 如果无法获取叙事节点，进行简单的位置估计
            if not narrative_beats:
                # 简单将场景分为四个部分: 引入、铺垫、高潮、解决
                total = len(scenes)
                intro_end = total // 6
                buildup_end = total // 2
                climax_end = total * 4 // 5
                
                for i in range(total):
                    if i <= intro_end:
                        narrative_map[i] = 'introduction'
                    elif i <= buildup_end:
                        narrative_map[i] = 'buildup'
                    elif i <= climax_end:
                        narrative_map[i] = 'climax'
                    else:
                        narrative_map[i] = 'resolution'
            else:
                # 使用分析器识别的节点
                for i, beat in narrative_beats.items():
                    narrative_map[i] = beat['type']
            
            return narrative_map
            
        except Exception as e:
            logger.warning(f"叙事结构分析失败: {e}，使用默认结构")
            
            # 默认结构: 简单分四个阶段
            total = len(scenes)
            narrative_map = {}
            
            for i in range(total):
                if i < total // 6:
                    narrative_map[i] = 'introduction'
                elif i < total // 2:
                    narrative_map[i] = 'buildup'
                elif i < total * 4 // 5:
                    narrative_map[i] = 'climax'
                else:
                    narrative_map[i] = 'resolution'
            
            return narrative_map
    
    def _analyze_emotion_flow(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析场景序列的情感流程
        
        Args:
            scenes: 场景列表
            
        Returns:
            情感流程分析结果
        """
        # 提取情感信息
        emotion_scores = []
        
        for scene in scenes:
            emotion_data = scene.get('emotion', {})
            score = 0.5  # 默认中性
            
            # 提取情感分数
            if isinstance(emotion_data, dict):
                score = emotion_data.get('score', emotion_data.get('intensity', 0.5))
            
            emotion_scores.append(score)
        
        # 分析情感变化趋势
        trend = self._analyze_trend(emotion_scores)
        
        # 识别情感高峰和低谷
        peaks, valleys = self._find_extremes(emotion_scores)
        
        # 计算情感流程质量指标
        quality = self._calculate_emotion_flow_quality(emotion_scores, peaks, valleys)
        
        return {
            'trend': trend,
            'peaks': peaks,
            'valleys': valleys,
            'avg_intensity': sum(emotion_scores) / len(emotion_scores) if emotion_scores else 0.5,
            'quality': quality
        }
    
    def _analyze_trend(self, scores: List[float]) -> str:
        """分析数值序列的趋势
        
        Args:
            scores: 数值序列
            
        Returns:
            趋势描述: 'rising', 'falling', 'fluctuating', 'stable'
        """
        if not scores or len(scores) < 2:
            return 'stable'
        
        # 计算差值序列
        diffs = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
        
        # 计算平均差值和标准差
        avg_diff = sum(diffs) / len(diffs)
        std_diff = math.sqrt(sum((d - avg_diff) ** 2 for d in diffs) / len(diffs)) if len(diffs) > 1 else 0
        
        # 根据平均差值和标准差判断趋势
        if abs(avg_diff) < 0.05:
            if std_diff > 0.1:
                return 'fluctuating'
            else:
                return 'stable'
        elif avg_diff > 0:
            return 'rising'
        else:
            return 'falling'
    
    def _find_extremes(self, values: List[float]) -> Tuple[List[int], List[int]]:
        """查找序列中的极大值和极小值点
        
        Args:
            values: 数值序列
            
        Returns:
            (极大值索引列表, 极小值索引列表)
        """
        if len(values) < 3:
            return [], []
        
        peaks = []
        valleys = []
        
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append(i)
            elif values[i] < values[i-1] and values[i] < values[i+1]:
                valleys.append(i)
        
        return peaks, valleys
    
    def _calculate_emotion_flow_quality(self, scores: List[float], 
                                      peaks: List[int], valleys: List[int]) -> float:
        """计算情感流程质量
        
        Args:
            scores: 情感分数序列
            peaks: 峰值索引列表
            valleys: 谷值索引列表
            
        Returns:
            质量评分 (0-1)
        """
        if not scores:
            return 0.5
        
        # 计算变化幅度
        amplitude = max(scores) - min(scores) if scores else 0
        
        # 计算极值点密度
        extremes_density = (len(peaks) + len(valleys)) / len(scores) if scores else 0
        
        # 计算情感变化丰富度 (理想值在0.2-0.4之间)
        richness = min(1.0, extremes_density * 2.5) if 0 < extremes_density < 0.5 else 0.5
        
        # 计算最终质量分数
        quality = 0.3 * min(1.0, amplitude * 1.5) + 0.7 * richness
        
        return quality
    
    def _apply_sequence_rules(self, scenes: List[Dict[str, Any]], 
                             narrative_structure: Dict[int, str]) -> List[Dict[str, Any]]:
        """应用场景序列调整规则
        
        确保连续场景间有适当的变化，避免单调和过度变化。
        
        Args:
            scenes: 场景列表
            narrative_structure: 叙事结构映射
            
        Returns:
            调整后的场景列表
        """
        # 获取配置
        consecutive_rules = self.config["adjustment_rules"]["consecutive_scenes"]
        max_similar = consecutive_rules["max_similar_intensity"]
        variation_threshold = consecutive_rules["variation_threshold"]
        
        # 创建场景副本
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 分析连续相似场景
        similar_count = 1
        
        for i in range(1, len(adjusted_scenes)):
            # 检查前一个场景和当前场景的情感强度
            prev_intensity = self._get_scene_emotion_intensity(adjusted_scenes[i-1])
            curr_intensity = self._get_scene_emotion_intensity(adjusted_scenes[i])
            
            # 判断是否相似 (强度差值小于阈值)
            if abs(prev_intensity - curr_intensity) < variation_threshold:
                similar_count += 1
            else:
                similar_count = 1
            
            # 如果连续相似场景过多，强制添加变化
            if similar_count > max_similar:
                # 根据叙事位置决定变化方向
                position = narrative_structure.get(i, 'neutral')
                
                if position == 'climax':
                    # 高潮部分增加强度
                    intensity_adjustment = consecutive_rules["forced_variation"]
                elif position == 'resolution':
                    # 解决部分降低强度
                    intensity_adjustment = -consecutive_rules["forced_variation"]
                else:
                    # 其他部分交替变化
                    intensity_adjustment = consecutive_rules["forced_variation"] * (1 if i % 2 == 0 else -1)
                
                # 创建强制调整标记供后续处理
                adjusted_scenes[i]["forced_adjustment"] = {
                    "emotion_intensity": intensity_adjustment,
                    "reason": "avoid_monotony"
                }
                
                # 重置连续计数
                similar_count = 1
        
        return adjusted_scenes 
    
    def _adjust_emotion_intensity(self, scene: Dict[str, Any], 
                                 narrative_position: str,
                                 prev_scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调整场景的情感强度
        
        Args:
            scene: 场景数据
            narrative_position: 叙事位置
            prev_scene: 前一个场景
            
        Returns:
            调整后的场景
        """
        # 创建场景副本
        adjusted_scene = scene.copy()
        
        # 获取用户偏好中的情感强度因子
        user_factor = self.preset_configs[self.user_preference]["emotion_intensity"]
        
        # 获取场景情感信息
        emotion_data = scene.get("emotion", {})
        if not isinstance(emotion_data, dict):
            emotion_data = {"type": "neutral", "score": 0.5}
        
        emotion_type = emotion_data.get("type", "neutral")
        emotion_score = emotion_data.get("score", emotion_data.get("intensity", 0.5))
        
        # 获取情感类型特定调节因子
        type_config = self.config["emotion_intensity"]["type_specific"]
        type_factor = type_config.get(emotion_type, 1.0)
        
        # 获取叙事位置调节因子
        narrative_config = self.config["adjustment_rules"]["narrative_nodes"]
        narrative_factors = {
            "introduction": narrative_config["introduction_factor"],
            "buildup": narrative_config["buildup_factor"],
            "climax": narrative_config["climax_factor"],
            "resolution": narrative_config["resolution_factor"]
        }
        narrative_factor = narrative_factors.get(narrative_position, 1.0)
        
        # 应用峰值调节 (如果启用)
        peak_config = self.config["emotion_intensity"]["peak_adjustment"]
        peak_factor = 1.0
        
        if peak_config["enabled"]:
            # 如果是情感高峰或低谷，应用相应调节
            if emotion_score > 0.7:  # 高峰
                peak_factor = peak_config["peak_boost"]
            elif emotion_score < 0.3:  # 低谷
                peak_factor = peak_config["valley_reduction"]
        
        # 计算强制调整 (如果有)
        forced_adjustment = scene.get("forced_adjustment", {}).get("emotion_intensity", 0)
        
        # 计算综合调整因子
        combined_factor = user_factor * type_factor * narrative_factor * peak_factor
        
        # 应用调整
        new_score = min(1.0, max(0.1, emotion_score * combined_factor + forced_adjustment))
        
        # 更新情感数据
        adjusted_emotion = emotion_data.copy()
        adjusted_emotion["original_score"] = emotion_score
        adjusted_emotion["adjusted_score"] = new_score
        adjusted_emotion["intensity"] = new_score  # 兼容不同的字段名
        
        if "score" in emotion_data:
            adjusted_emotion["score"] = new_score
        
        # 记录调整详情
        adjustment_details = {
            "user_factor": user_factor,
            "type_factor": type_factor,
            "narrative_factor": narrative_factor,
            "peak_factor": peak_factor,
            "forced_adjustment": forced_adjustment,
            "combined_factor": combined_factor,
            "original_score": emotion_score,
            "adjusted_score": new_score
        }
        
        # 更新场景数据
        adjusted_scene["emotion"] = adjusted_emotion
        adjusted_scene["emotion_adjustment"] = adjustment_details
        
        # 如果场景包含文本，调整文本情感强度
        if "text" in scene and isinstance(scene["text"], str):
            adjusted_text = self._adjust_text_emotion(
                scene["text"], 
                emotion_score, 
                new_score,
                emotion_type
            )
            adjusted_scene["original_text"] = scene["text"]
            adjusted_scene["text"] = adjusted_text
        
        return adjusted_scene
    
    def _adjust_text_emotion(self, text: str, original_score: float, 
                            target_score: float, emotion_type: str) -> str:
        """调整文本的情感表达强度
        
        Args:
            text: 原始文本
            original_score: 原始情感强度
            target_score: 目标情感强度
            emotion_type: 情感类型
            
        Returns:
            调整后的文本
        """
        if not text or original_score == target_score:
            return text
        
        try:
            # 计算调整方向和幅度
            adjustment_direction = 1 if target_score > original_score else -1
            adjustment_magnitude = abs(target_score - original_score)
            
            # 根据调整幅度选择适当的调整级别
            if adjustment_magnitude < 0.1:
                # 微小调整，保持原文
                return text
            elif adjustment_magnitude < 0.25:
                # 小幅调整
                factor = 0.8 if adjustment_direction < 0 else 1.2
            else:
                # 大幅调整
                factor = 0.6 if adjustment_direction < 0 else 1.5
            
            # 应用情感词汇强化器调整文本
            if adjustment_direction > 0:
                return self.emotion_lexicon.intensify(text, factor)
            else:
                return self.emotion_lexicon.reduce(text, factor)
        
        except Exception as e:
            logger.warning(f"文本情感调整失败: {e}")
            return text
    
    def _get_scene_emotion_intensity(self, scene: Dict[str, Any]) -> float:
        """获取场景的情感强度
        
        Args:
            scene: 场景数据
            
        Returns:
            情感强度 (0-1)
        """
        emotion_data = scene.get("emotion", {})
        
        if not isinstance(emotion_data, dict):
            return 0.5
        
        # 尝试获取情感强度
        intensity = emotion_data.get("adjusted_score",  # 优先使用已调整的分数
                    emotion_data.get("score",           # 然后是原始分数
                    emotion_data.get("intensity", 0.5)))  # 最后是intensity字段
        
        return intensity 
    
    def _adjust_conflict_intensity(self, scene: Dict[str, Any],
                                  narrative_position: str,
                                  prev_scene: Optional[Dict[str, Any]] = None,
                                  next_scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """调整场景的冲突激烈度
        
        Args:
            scene: 场景数据
            narrative_position: 叙事位置
            prev_scene: 前一个场景
            next_scene: 后一个场景
            
        Returns:
            调整后的场景
        """
        # 创建场景副本
        adjusted_scene = scene.copy()
        
        # 获取用户偏好中的冲突强度因子
        user_factor = self.preset_configs[self.user_preference]["conflict_intensity"]
        
        # 获取场景冲突信息
        conflict_data = scene.get("conflict", {})
        if not isinstance(conflict_data, dict):
            # 如果没有冲突数据，根据情感和其他数据估算
            conflict_data = self._estimate_conflict_data(scene)
        
        conflict_type = conflict_data.get("type", "neutral")
        conflict_score = conflict_data.get("intensity", 0.5)
        
        # 获取冲突类型特定调节因子
        type_config = self.config["conflict_intensity"]["type_adjustment"]
        type_factor = type_config.get(conflict_type, 1.0)
        
        # 获取叙事位置调节因子
        narrative_config = self.config["conflict_intensity"]["narrative_adjustment"]
        narrative_mapping = {
            "introduction": "rising_action",
            "buildup": "rising_action",
            "climax": "climax",
            "resolution": "resolution"
        }
        narrative_key = narrative_mapping.get(narrative_position, "rising_action")
        narrative_factor = narrative_config.get(narrative_key, 1.0)
        
        # 计算强制调整 (如果有)
        forced_adjustment = scene.get("forced_adjustment", {}).get("conflict_intensity", 0)
        
        # 计算相邻场景影响因子
        neighbor_factor = self._calculate_neighbor_conflict_impact(scene, prev_scene, next_scene)
        
        # 计算综合调整因子
        combined_factor = user_factor * type_factor * narrative_factor * neighbor_factor
        
        # 应用调整
        new_score = min(1.0, max(0.1, conflict_score * combined_factor + forced_adjustment))
        
        # 更新冲突数据
        adjusted_conflict = conflict_data.copy()
        adjusted_conflict["original_intensity"] = conflict_score
        adjusted_conflict["adjusted_intensity"] = new_score
        
        # 记录调整详情
        adjustment_details = {
            "user_factor": user_factor,
            "type_factor": type_factor,
            "narrative_factor": narrative_factor,
            "neighbor_factor": neighbor_factor,
            "forced_adjustment": forced_adjustment,
            "combined_factor": combined_factor,
            "original_score": conflict_score,
            "adjusted_score": new_score
        }
        
        # 更新场景数据
        adjusted_scene["conflict"] = adjusted_conflict
        adjusted_scene["conflict_adjustment"] = adjustment_details
        
        # 更新对话或动作数据中的冲突元素
        if new_score > conflict_score + 0.15:
            adjusted_scene = self._enhance_conflict_elements(adjusted_scene, new_score)
        elif new_score < conflict_score - 0.15:
            adjusted_scene = self._reduce_conflict_elements(adjusted_scene, new_score)
        
        return adjusted_scene
    
    def _estimate_conflict_data(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """根据场景数据估算冲突信息
        
        Args:
            scene: 场景数据
            
        Returns:
            估算的冲突数据
        """
        # 从情感数据估算冲突程度
        emotion_data = scene.get("emotion", {})
        if not isinstance(emotion_data, dict):
            emotion_data = {"type": "neutral", "score": 0.5}
        
        emotion_type = emotion_data.get("type", "neutral")
        emotion_score = emotion_data.get("score", emotion_data.get("intensity", 0.5))
        
        # 根据情感类型推断冲突类型
        conflict_type_map = {
            "anger": "verbal",
            "fear": "physical",
            "disgust": "emotional",
            "sadness": "emotional",
            "joy": "neutral",
            "surprise": "psychological"
        }
        
        conflict_type = conflict_type_map.get(emotion_type, "neutral")
        
        # 根据情感强度估算冲突强度
        # 负面情感越强，冲突越激烈
        if emotion_type in ["anger", "fear", "disgust", "sadness"]:
            conflict_score = min(0.9, emotion_score * 1.2)
        elif emotion_type == "surprise":
            conflict_score = emotion_score * 0.8
        else:
            conflict_score = emotion_score * 0.5
        
        # 检查对话中的冲突标记
        dialog = scene.get("dialog", [])
        if dialog and isinstance(dialog, list):
            confrontation_words = ["争吵", "反对", "冲突", "争执", "反驳", "质疑", "否认", "拒绝"]
            for line in dialog:
                if isinstance(line, dict) and "text" in line:
                    text = line["text"]
                    if any(word in text for word in confrontation_words):
                        conflict_score = min(1.0, conflict_score + 0.15)
                        conflict_type = "verbal"
                        break
        
        return {
            "type": conflict_type,
            "intensity": conflict_score,
            "estimated": True
        }
    
    def _calculate_neighbor_conflict_impact(self, scene: Dict[str, Any],
                                         prev_scene: Optional[Dict[str, Any]],
                                         next_scene: Optional[Dict[str, Any]]) -> float:
        """计算相邻场景对当前场景冲突强度的影响
        
        Args:
            scene: 当前场景
            prev_scene: 前一个场景
            next_scene: 后一个场景
            
        Returns:
            邻居影响因子
        """
        # 默认没有影响
        factor = 1.0
        
        # 获取当前场景冲突
        curr_conflict = self._get_scene_conflict_intensity(scene)
        
        # 前一个场景影响
        if prev_scene:
            prev_conflict = self._get_scene_conflict_intensity(prev_scene)
            # 如果前一个场景冲突很高，当前场景可能是延续或缓解
            if prev_conflict > 0.7 and curr_conflict > 0.6:
                # 前一个场景冲突高且当前场景也高，强化延续效果
                factor *= 1.1
            elif prev_conflict > 0.7 and curr_conflict < 0.5:
                # 前一个场景冲突高但当前场景低，降低形成对比
                factor *= 0.9
        
        # 后一个场景影响
        if next_scene:
            next_conflict = self._get_scene_conflict_intensity(next_scene)
            # 如果下一个场景是高冲突，可能需要铺垫
            if next_conflict > 0.7 and curr_conflict < 0.5:
                # 当前场景冲突低但下一个高，增强铺垫效果
                factor *= 1.15
        
        return factor
    
    def _get_scene_conflict_intensity(self, scene: Dict[str, Any]) -> float:
        """获取场景的冲突强度
        
        Args:
            scene: 场景数据
            
        Returns:
            冲突强度 (0-1)
        """
        conflict_data = scene.get("conflict", {})
        
        if not isinstance(conflict_data, dict):
            return 0.5
        
        # 尝试获取冲突强度
        intensity = conflict_data.get("adjusted_intensity",  # 优先使用已调整的强度
                    conflict_data.get("intensity", 0.5))     # 然后是原始强度
        
        return intensity
    
    def _enhance_conflict_elements(self, scene: Dict[str, Any], target_intensity: float) -> Dict[str, Any]:
        """增强场景中的冲突元素
        
        Args:
            scene: 场景数据
            target_intensity: 目标冲突强度
            
        Returns:
            增强冲突后的场景
        """
        # 创建场景副本
        enhanced_scene = scene.copy()
        
        # 根据目标强度选择增强程度
        enhancement_level = "moderate"
        if target_intensity > 0.8:
            enhancement_level = "strong"
        elif target_intensity < 0.6:
            enhancement_level = "mild"
        
        # 增强对话冲突 (如果有)
        if "dialog" in scene and isinstance(scene["dialog"], list):
            dialog = scene["dialog"]
            enhanced_dialog = []
            
            for line in dialog:
                if isinstance(line, dict) and "text" in line:
                    # 保留原始文本
                    enhanced_line = line.copy()
                    
                    # 根据不同程度增强冲突表达
                    text = line["text"]
                    character = line.get("character", "")
                    
                    # 如果是关键角色且文本适合增强
                    if len(text) > 10 and not text.endswith(("?", "。", "!", "?")):
                        if enhancement_level == "strong":
                            # 添加强烈情感表达
                            enhanced_line["text"] = self._add_conflict_markers(text, "strong")
                        elif enhancement_level == "moderate":
                            # 添加中等情感表达
                            enhanced_line["text"] = self._add_conflict_markers(text, "moderate")
                        else:
                            # 轻微增强
                            enhanced_line["text"] = self._add_conflict_markers(text, "mild")
                    
                    enhanced_dialog.append(enhanced_line)
                else:
                    enhanced_dialog.append(line)
            
            enhanced_scene["dialog"] = enhanced_dialog
        
        return enhanced_scene
    
    def _reduce_conflict_elements(self, scene: Dict[str, Any], target_intensity: float) -> Dict[str, Any]:
        """减弱场景中的冲突元素
        
        Args:
            scene: 场景数据
            target_intensity: 目标冲突强度
            
        Returns:
            减弱冲突后的场景
        """
        # 创建场景副本
        reduced_scene = scene.copy()
        
        # 根据目标强度选择减弱程度
        reduction_level = "moderate"
        if target_intensity < 0.3:
            reduction_level = "strong"
        elif target_intensity > 0.5:
            reduction_level = "mild"
        
        # 减弱对话冲突 (如果有)
        if "dialog" in scene and isinstance(scene["dialog"], list):
            dialog = scene["dialog"]
            reduced_dialog = []
            
            for line in dialog:
                if isinstance(line, dict) and "text" in line:
                    # 保留原始文本
                    reduced_line = line.copy()
                    
                    # 根据不同程度减弱冲突表达
                    text = line["text"]
                    
                    # 检测并减弱强烈的冲突标记
                    if any(marker in text for marker in ["!", "！", "?", "？"]):
                        if reduction_level == "strong":
                            #
                            reduced_line["text"] = self._remove_conflict_markers(text, "strong")
                        elif reduction_level == "moderate":
                            # 中等减弱
                            reduced_line["text"] = self._remove_conflict_markers(text, "moderate")
                        else:
                            # 轻微减弱
                            reduced_line["text"] = self._remove_conflict_markers(text, "mild")
                    
                    reduced_dialog.append(reduced_line)
                else:
                    reduced_dialog.append(line)
            
            reduced_scene["dialog"] = reduced_dialog
        
        return reduced_scene
    
    def _add_conflict_markers(self, text: str, level: str) -> str:
        """添加冲突标记以增强冲突强度
        
        Args:
            text: 原始文本
            level: 增强级别 ('mild', 'moderate', 'strong')
            
        Returns:
            增强后的文本
        """
        if level == "strong":
            # 添加强烈的冲突标记
            if not any(mark in text for mark in ["!", "！"]):
                return text + "！"
            else:
                return text.replace("!", "!!").replace("！", "！！")
        elif level == "moderate":
            # 添加中等冲突标记
            if not any(mark in text for mark in ["!", "！", "?", "？"]):
                return text + "!"
        else:  # mild
            # 轻微增强，只对已有一定程度冲突的文本进行增强
            if "." in text or "。" in text:
                return text.replace(".", "!").replace("。", "！")
        
        return text
    
    def _remove_conflict_markers(self, text: str, level: str) -> str:
        """移除冲突标记以减弱冲突强度
        
        Args:
            text: 原始文本
            level: 减弱级别 ('mild', 'moderate', 'strong')
            
        Returns:
            减弱后的文本
        """
        if level == "strong":
            # 移除所有强烈的冲突标记
            text = text.replace("!!", ".").replace("！！", "。")
            text = text.replace("!", ".").replace("！", "。")
            text = text.replace("??", "?").replace("？？", "？")
            return text
        elif level == "moderate":
            # 减少重复的标记
            text = text.replace("!!", "!").replace("！！", "！")
            text = text.replace("??", "?").replace("？？", "？")
            return text
        else:  # mild
            # 轻微减弱，只处理重复标记
            text = text.replace("!!!", "!").replace("！！！", "！")
            return text
        
        return text
    
    def _adjust_visual_intensity(self, scene: Dict[str, Any], 
                                 narrative_position: str) -> Dict[str, Any]:
        """调整场景的视觉刺激强度
        
        Args:
            scene: 场景数据
            narrative_position: 叙事位置
            
        Returns:
            调整后的场景
        """
        # 创建场景副本
        adjusted_scene = scene.copy()
        
        # 获取用户偏好中的视觉强度因子
        user_factor = self.preset_configs[self.user_preference]["visual_intensity"]
        
        # 获取场景视觉信息
        visual_data = scene.get("visual", {})
        if not isinstance(visual_data, dict):
            # 如果没有视觉数据，创建默认数据
            visual_data = {"style": "neutral", "intensity": 0.5}
        
        visual_style = visual_data.get("style", "neutral")
        visual_score = visual_data.get("intensity", 0.5)
        
        # 获取视觉风格特定调节因子
        style_config = self.config["visual_intensity"]["style_adjustment"]
        style_mapping = {
            "fast_paced": "fast_paced",
            "slow_paced": "slow_paced",
            "high_contrast": "high_contrast",
            "low_contrast": "low_contrast",
            # 默认映射
            "intense": "fast_paced",
            "subtle": "slow_paced",
            "dramatic": "high_contrast",
            "gentle": "low_contrast"
        }
        
        style_key = style_mapping.get(visual_style, "neutral")
        style_factor = style_config.get(style_key, 1.0)
        
        # 根据叙事位置决定视觉强度调整策略
        narrative_factor = 1.0
        if narrative_position == "climax":
            narrative_factor = 1.2  # 高潮部分视觉更强烈
        elif narrative_position == "introduction":
            narrative_factor = 0.9  # 引入部分视觉相对平和
        
        # 计算强制调整 (如果有)
        forced_adjustment = scene.get("forced_adjustment", {}).get("visual_intensity", 0)
        
        # 计算综合调整因子
        combined_factor = user_factor * style_factor * narrative_factor
        
        # 应用调整
        new_score = min(1.0, max(0.1, visual_score * combined_factor + forced_adjustment))
        
        # 更新视觉数据
        adjusted_visual = visual_data.copy()
        adjusted_visual["original_intensity"] = visual_score
        adjusted_visual["adjusted_intensity"] = new_score
        
        # 记录调整详情
        adjustment_details = {
            "user_factor": user_factor,
            "style_factor": style_factor,
            "narrative_factor": narrative_factor,
            "forced_adjustment": forced_adjustment,
            "combined_factor": combined_factor,
            "original_score": visual_score,
            "adjusted_score": new_score
        }
        
        # 更新场景数据
        adjusted_scene["visual"] = adjusted_visual
        adjusted_scene["visual_adjustment"] = adjustment_details
        
        return adjusted_scene
    
    def _smooth_transitions(self, scene: Dict[str, Any],
                           prev_scene: Optional[Dict[str, Any]] = None,
                           next_scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """平滑场景转换，处理速率限制
        
        确保场景之间的情感、冲突和视觉强度变化不会过大或过小。
        
        Args:
            scene: 当前场景
            prev_scene: 前一个场景
            next_scene: 后一个场景
            
        Returns:
            平滑后的场景
        """
        if not prev_scene:
            # 没有前一个场景，无需平滑
            return scene
        
        # 创建场景副本
        smoothed_scene = scene.copy()
        
        # 获取速率限制配置
        rate_config = self.config["adjustment_rules"]["rate_limiting"]
        max_increase = rate_config["max_increase_rate"]
        max_decrease = rate_config["max_decrease_rate"]
        
        # 平滑情感强度变化
        if "emotion" in smoothed_scene and "emotion" in prev_scene:
            prev_emotion = self._get_scene_emotion_intensity(prev_scene)
            curr_emotion = self._get_scene_emotion_intensity(smoothed_scene)
            
            # 计算变化率
            change_rate = curr_emotion - prev_emotion
            
            # 应用速率限制
            if change_rate > max_increase:
                # 增长过快，限制增长率
                new_emotion = prev_emotion + max_increase
                self._update_emotion_intensity(smoothed_scene, new_emotion)
            elif change_rate < -max_decrease:
                # 下降过快，限制下降率
                new_emotion = prev_emotion - max_decrease
                self._update_emotion_intensity(smoothed_scene, new_emotion)
        
        # 平滑冲突强度变化
        if "conflict" in smoothed_scene and "conflict" in prev_scene:
            prev_conflict = self._get_scene_conflict_intensity(prev_scene)
            curr_conflict = self._get_scene_conflict_intensity(smoothed_scene)
            
            # 计算变化率
            change_rate = curr_conflict - prev_conflict
            
            # 应用速率限制
            if change_rate > max_increase:
                # 增长过快，限制增长率
                new_conflict = prev_conflict + max_increase
                self._update_conflict_intensity(smoothed_scene, new_conflict)
            elif change_rate < -max_decrease:
                # 下降过快，限制下降率
                new_conflict = prev_conflict - max_decrease
                self._update_conflict_intensity(smoothed_scene, new_conflict)
        
        return smoothed_scene
    
    def _update_emotion_intensity(self, scene: Dict[str, Any], new_intensity: float) -> None:
        """更新场景的情感强度
        
        Args:
            scene: 场景数据
            new_intensity: 新的情感强度
        """
        if "emotion" not in scene or not isinstance(scene["emotion"], dict):
            return
        
        # 确保值在合理范围内
        new_intensity = min(1.0, max(0.1, new_intensity))
        
        # 更新情感数据
        scene["emotion"]["adjusted_score"] = new_intensity
        scene["emotion"]["intensity"] = new_intensity
        
        if "score" in scene["emotion"]:
            scene["emotion"]["score"] = new_intensity
        
        # 更新调整记录
        if "emotion_adjustment" in scene:
            scene["emotion_adjustment"]["smoothed"] = True
            scene["emotion_adjustment"]["final_score"] = new_intensity
    
    def _update_conflict_intensity(self, scene: Dict[str, Any], new_intensity: float) -> None:
        """更新场景的冲突强度
        
        Args:
            scene: 场景数据
            new_intensity: 新的冲突强度
        """
        if "conflict" not in scene or not isinstance(scene["conflict"], dict):
            return
        
        # 确保值在合理范围内
        new_intensity = min(1.0, max(0.1, new_intensity))
        
        # 更新冲突数据
        scene["conflict"]["adjusted_intensity"] = new_intensity
        
        # 更新调整记录
        if "conflict_adjustment" in scene:
            scene["conflict_adjustment"]["smoothed"] = True
            scene["conflict_adjustment"]["final_score"] = new_intensity
    
    def _record_adjustment(self, adjusted_scenes: List[Dict[str, Any]]) -> None:
        """记录调整历史
        
        Args:
            adjusted_scenes: 调整后的场景列表
        """
        # 如果没有启用历史记录，直接返回
        persistence_config = self.config.get("persistence", {})
        if not persistence_config.get("history_tracking", False):
            return
        
        # 提取摘要信息
        summary = {
            "timestamp": self._get_timestamp(),
            "preset": self.user_preference,
            "scene_count": len(adjusted_scenes),
            "average_emotion": self._calculate_average(adjusted_scenes, "emotion"),
            "average_conflict": self._calculate_average(adjusted_scenes, "conflict"),
            "average_visual": self._calculate_average(adjusted_scenes, "visual")
        }
        
        # 添加到历史记录
        self.adjustment_history.append(summary)
        
        # 限制历史记录大小
        max_history = 100  # 最大保留100条历史记录
        if len(self.adjustment_history) > max_history:
            self.adjustment_history = self.adjustment_history[-max_history:]
        
        # 如果配置了，保存到文件
        history_file = persistence_config.get("history_file")
        if persistence_config.get("save_user_prefs", False) and history_file:
            try:
                self._save_history(history_file)
            except Exception as e:
                logger.warning(f"保存历史记录失败: {e}")
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳
        
        Returns:
            格式化的时间戳
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _calculate_average(self, scenes: List[Dict[str, Any]], field: str) -> float:
        """计算场景列表某一字段的平均值
        
        Args:
            scenes: 场景列表
            field: 字段名称 ('emotion', 'conflict', 'visual')
            
        Returns:
            平均值
        """
        if not scenes:
            return 0.5
        
        total = 0.0
        count = 0
        
        for scene in scenes:
            if field == "emotion":
                value = self._get_scene_emotion_intensity(scene)
            elif field == "conflict":
                value = self._get_scene_conflict_intensity(scene)
            elif field == "visual" and "visual" in scene:
                visual_data = scene["visual"]
                if isinstance(visual_data, dict):
                    value = visual_data.get("adjusted_intensity", 
                           visual_data.get("intensity", 0.5))
                else:
                    continue
            else:
                continue
            
            total += value
            count += 1
        
        return total / count if count > 0 else 0.5
    
    def _save_history(self, filename: str) -> None:
        """保存历史记录到文件
        
        Args:
            filename: 文件名
        """
        # 确保目录存在
        dir_path = os.path.dirname(filename)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # 保存为JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.adjustment_history, f, ensure_ascii=False, indent=2)
    
    def get_adjustment_history(self) -> List[Dict[str, Any]]:
        """获取调整历史
        
        Returns:
            调整历史记录列表
        """
        return self.adjustment_history 