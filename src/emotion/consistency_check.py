#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感一致性检验模块

检查场景序列中的情感流动是否合理，防止情感断层和不自然的跳跃。
支持对中文和英文内容的情感连贯性检验，确保混剪作品情感流畅。
"""

import logging
import json
import math
from typing import Dict, List, Any, Optional, Tuple, Union

from ..config.constants import MAX_EMOTION_DELTA
from ..utils.exceptions import EmotionJumpError, EmotionMissingError

logger = logging.getLogger(__name__)

class EmotionValidator:
    """情感一致性检验器
    
    检查场景序列中的情感变化是否合理，防止剧情情感跳跃过大导致观感割裂。
    可配置的阈值和检验规则，支持不同类型内容的检验需求。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化情感一致性检验器
        
        Args:
            config: 配置参数，用于自定义检验规则
        """
        self.config = config or self._default_config()
        self.max_emotion_delta = self.config.get("max_emotion_delta", 0.5)
        self.require_smooth_transitions = self.config.get("require_smooth_transitions", True)
        self.allow_jumps_at_scene_change = self.config.get("allow_jumps_at_scene_change", True)
        self.min_scenes_for_check = self.config.get("min_scenes_for_check", 2)
        
        # 特殊情感转换规则，某些情感类型之间的转换可以有更大的跳跃
        self.special_transition_rules = self.config.get("special_transition_rules", {})
        
        logger.info("情感一致性检验器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "max_emotion_delta": 0.5,  # 相邻场景情感强度最大差值
            "require_smooth_transitions": True,  # 是否需要平滑过渡
            "allow_jumps_at_scene_change": True,  # 场景切换处是否允许较大跳跃
            "min_scenes_for_check": 2,  # 最少需要多少场景才进行检查
            "special_transition_rules": {
                # 特殊情感类型转换规则，允许某些情感类型之间有更大的跳跃
                "surprise_to_any": 0.7,  # 惊讶到任何情感允许更大变化
                "any_to_climax": 0.65,   # 任何情感到高潮场景允许更大变化
                "opposite_emotions": {    # 对立情感类型之间的转换限制
                    "joy_to_sadness": 0.4,
                    "anger_to_calm": 0.35
                }
            },
            "narrative_position_rules": {
                # 基于叙事位置的规则，在特定叙事节点允许更大/更小的变化
                "climax": 0.65,  # 高潮部分允许更大情感变化
                "resolution": 0.4 # 解决部分要求更平滑的过渡
            }
        }
    
    def check_arc(self, scenes: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """检查情感弧线合理性
        
        验证场景序列中的情感变化是否合理，防止情感断层。
        
        Args:
            scenes: 场景列表，每个场景需包含情感信息
            
        Returns:
            (是否通过检查, 错误信息)
        """
        if not scenes or len(scenes) < self.min_scenes_for_check:
            logger.info(f"场景数量不足 ({len(scenes) if scenes else 0}), 跳过情感一致性检查")
            return True, None
        
        try:
            # 检查每个场景是否包含情感数据
            self._check_emotion_data_exists(scenes)
            
            # 检查情感变化是否平滑
            self._check_emotion_transitions(scenes)
            
            # 检查情感弧线整体形状
            self._check_emotion_arc_shape(scenes)
            
            return True, None
        
        except EmotionJumpError as e:
            logger.warning(f"情感断层检测: {str(e)}")
            return False, str(e)
        
        except EmotionMissingError as e:
            logger.warning(f"情感数据缺失: {str(e)}")
            return False, str(e)
        
        except Exception as e:
            logger.error(f"情感一致性检查异常: {str(e)}")
            return False, f"情感一致性检查失败: {str(e)}"
    
    def _check_emotion_data_exists(self, scenes: List[Dict[str, Any]]) -> None:
        """检查场景是否包含必要的情感数据
        
        Args:
            scenes: 场景列表
            
        Raises:
            EmotionMissingError: 当场景缺少必要情感数据时
        """
        for i, scene in enumerate(scenes):
            # 检查是否存在emotion字段
            if "emotion" not in scene:
                raise EmotionMissingError(f"场景 {i+1} 缺少情感数据")
            
            # 检查情感数据格式
            emotion = scene["emotion"]
            if not isinstance(emotion, dict):
                raise EmotionMissingError(f"场景 {i+1} 情感数据格式错误")
            
            # 检查情感强度值
            if "score" not in emotion and "intensity" not in emotion:
                raise EmotionMissingError(f"场景 {i+1} 缺少情感强度数据")
    
    def _check_emotion_transitions(self, scenes: List[Dict[str, Any]]) -> None:
        """检查相邻场景的情感变化是否平滑
        
        Args:
            scenes: 场景列表
            
        Raises:
            EmotionJumpError: 当检测到情感断层时
        """
        prev_score = self._get_emotion_score(scenes[0])
        prev_type = self._get_emotion_type(scenes[0])
        prev_narrative_pos = scenes[0].get("narrative_position", "unknown")
        
        for i, scene in enumerate(scenes[1:], 1):
            current_score = self._get_emotion_score(scene)
            current_type = self._get_emotion_type(scene)
            current_narrative_pos = scene.get("narrative_position", "unknown")
            
            # 计算情感强度变化
            delta = abs(current_score - prev_score)
            
            # 获取基于情感类型和叙事位置的阈值调整
            transition_threshold = self._get_transition_threshold(
                prev_type, current_type, 
                prev_narrative_pos, current_narrative_pos
            )
            
            # 检查情感变化是否超过阈值
            if delta > transition_threshold:
                # 如果在场景切换处且允许跳跃，则跳过检查
                scene_change = scenes[i-1].get("is_scene_boundary", False) or \
                               scene.get("is_scene_boundary", False)
                
                if not (scene_change and self.allow_jumps_at_scene_change):
                    # 构建详细的错误信息
                    error_info = {
                        "prev_scene": i,
                        "curr_scene": i+1,
                        "prev_score": prev_score,
                        "curr_score": current_score,
                        "delta": delta,
                        "threshold": transition_threshold,
                        "prev_type": prev_type,
                        "curr_type": current_type
                    }
                    
                    # 抛出情感断层异常
                    raise EmotionJumpError(
                        f"情感断层: 场景 {i} 到 {i+1} 情感变化过大 "
                        f"({prev_score:.2f}->{current_score:.2f}, 差值: {delta:.2f}, "
                        f"阈值: {transition_threshold:.2f})",
                        error_info
                    )
            
            # 更新前一个场景的信息
            prev_score = current_score
            prev_type = current_type
            prev_narrative_pos = current_narrative_pos
    
    def _check_emotion_arc_shape(self, scenes: List[Dict[str, Any]]) -> None:
        """检查情感弧线的整体形状是否合理
        
        对整体情感曲线进行评估，确保有适当的起伏变化。
        
        Args:
            scenes: 场景列表
            
        Raises:
            EmotionJumpError: 当情感弧线形状不合理时
        """
        # 提取情感分数序列
        scores = [self._get_emotion_score(scene) for scene in scenes]
        
        # 如果场景过少，不做整体形状检查
        if len(scores) < 4:
            return
        
        # 计算变化率
        changes = [scores[i] - scores[i-1] for i in range(1, len(scores))]
        
        # 检查是否全部单调递增或递减 (不自然)
        if all(c >= 0 for c in changes) or all(c <= 0 for c in changes):
            # 检查总体变化幅度，如果很小则允许
            total_change = abs(scores[-1] - scores[0])
            if total_change > 0.4:  # 较大的单调变化不自然
                logger.warning(f"情感弧线过于单调: {total_change:.2f}")
                # 对于单调情感不抛出异常，但记录警告
                # 这里可以根据需要调整为抛出异常
        
        # 检查是否缺乏情感变化
        max_score = max(scores)
        min_score = min(scores)
        range_size = max_score - min_score
        
        if range_size < 0.2 and len(scores) > 5:
            logger.warning(f"情感弧线缺乏变化: 范围 {range_size:.2f}")
            # 同样对于单调情感不抛出异常，但记录警告
    
    def _get_emotion_score(self, scene: Dict[str, Any]) -> float:
        """获取场景的情感强度分数
        
        Args:
            scene: 场景数据
            
        Returns:
            情感强度分数 (0-1)
        """
        emotion = scene["emotion"]
        
        # 尝试获取调整后的分数和原始分数
        adjusted_score = emotion.get("adjusted_score")
        if adjusted_score is not None:
            return adjusted_score
        
        # 尝试获取score字段
        score = emotion.get("score")
        if score is not None:
            return score
        
        # 回退到intensity字段
        intensity = emotion.get("intensity", 0.5)
        return intensity
    
    def _get_emotion_type(self, scene: Dict[str, Any]) -> str:
        """获取场景的情感类型
        
        Args:
            scene: 场景数据
            
        Returns:
            情感类型
        """
        emotion = scene["emotion"]
        return emotion.get("type", "neutral")
    
    def _get_transition_threshold(self, 
                                prev_type: str, 
                                current_type: str,
                                prev_narrative_pos: str,
                                current_narrative_pos: str) -> float:
        """获取基于情感类型和叙事位置的过渡阈值
        
        Args:
            prev_type: 前一个场景的情感类型
            current_type: 当前场景的情感类型
            prev_narrative_pos: 前一个场景的叙事位置
            current_narrative_pos: 当前场景的叙事位置
            
        Returns:
            情感过渡阈值
        """
        # 基础阈值
        threshold = self.max_emotion_delta
        
        # 检查特殊情感转换规则
        special_rules = self.special_transition_rules
        
        # 检查从惊讶到任何情感的转换
        if prev_type == "surprise" or prev_type == "惊讶":
            threshold = max(threshold, special_rules.get("surprise_to_any", threshold))
        
        # 检查任何情感到高潮的转换
        if current_narrative_pos == "climax":
            threshold = max(threshold, special_rules.get("any_to_climax", threshold))
        
        # 检查对立情感之间的转换
        opposite_emotions = special_rules.get("opposite_emotions", {})
        transition_key = f"{prev_type}_to_{current_type}"
        if transition_key in opposite_emotions:
            threshold = min(threshold, opposite_emotions[transition_key])
        
        # 考虑叙事位置的调整
        narrative_rules = self.config.get("narrative_position_rules", {})
        
        # 高潮部分允许更大的情感变化
        if current_narrative_pos == "climax" or prev_narrative_pos == "climax":
            threshold = max(threshold, narrative_rules.get("climax", threshold))
        
        # 解决部分要求更平滑的过渡
        if current_narrative_pos == "resolution" or prev_narrative_pos == "resolution":
            threshold = min(threshold, narrative_rules.get("resolution", threshold)) 
        
        return threshold
    
    def suggest_fixes(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """建议修复情感断层的方法
        
        对检测出情感断层的场景序列提供修复建议。
        
        Args:
            scenes: 原始场景列表
            
        Returns:
            修复建议列表
        """
        result, error_msg = self.check_arc(scenes)
        if result:
            return []  # 没有错误，不需要修复
        
        suggestions = []
        
        # 检查相邻场景的情感变化
        for i in range(1, len(scenes)):
            prev_score = self._get_emotion_score(scenes[i-1])
            current_score = self._get_emotion_score(scenes[i])
            delta = abs(current_score - prev_score)
            
            # 获取基于情感类型和叙事位置的阈值
            prev_type = self._get_emotion_type(scenes[i-1])
            current_type = self._get_emotion_type(scenes[i])
            prev_pos = scenes[i-1].get("narrative_position", "unknown")
            current_pos = scenes[i].get("narrative_position", "unknown")
            
            threshold = self._get_transition_threshold(
                prev_type, current_type, prev_pos, current_pos
            )
            
            # 如果变化超过阈值，提供修复建议
            if delta > threshold:
                # 计算中间值
                middle_score = (prev_score + current_score) / 2
                
                suggestion = {
                    "type": "emotion_jump",
                    "location": {
                        "prev_scene_index": i-1,
                        "current_scene_index": i,
                    },
                    "issue": {
                        "delta": delta,
                        "threshold": threshold,
                        "prev_score": prev_score,
                        "current_score": current_score
                    },
                    "solutions": [
                        {
                            "type": "adjust_current",
                            "description": f"调整当前场景情感强度至 {(prev_score + threshold * (1 if current_score > prev_score else -1)):.2f}",
                            "target_value": prev_score + threshold * (1 if current_score > prev_score else -1)
                        },
                        {
                            "type": "adjust_previous",
                            "description": f"调整前一场景情感强度至 {(current_score - threshold * (1 if current_score > prev_score else -1)):.2f}",
                            "target_value": current_score - threshold * (1 if current_score > prev_score else -1)
                        },
                        {
                            "type": "insert_transition",
                            "description": "插入过渡场景",
                            "target_value": middle_score
                        }
                    ]
                }
                
                suggestions.append(suggestion)
        
        return suggestions
    
    def apply_suggestion(self, scenes: List[Dict[str, Any]], 
                        suggestion: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用修复建议
        
        根据提供的修复建议，调整场景序列中的情感数据。
        
        Args:
            scenes: 原始场景列表
            suggestion: 修复建议
            
        Returns:
            调整后的场景列表
        """
        # 创建场景的副本，避免修改原始数据
        fixed_scenes = [scene.copy() for scene in scenes]
        
        solution = suggestion.get("solutions", [{}])[0]  # 默认使用第一个解决方案
        solution_type = solution.get("type", "")
        
        if solution_type == "adjust_current":
            # 调整当前场景情感强度
            scene_index = suggestion["location"]["current_scene_index"]
            target_value = solution["target_value"]
            
            # 获取情感数据副本
            emotion = fixed_scenes[scene_index]["emotion"].copy()
            
            # 更新情感强度
            emotion["original_score"] = self._get_emotion_score(fixed_scenes[scene_index])
            emotion["adjusted_score"] = target_value
            emotion["score"] = target_value
            emotion["intensity"] = target_value
            
            # 替换原情感数据
            fixed_scenes[scene_index]["emotion"] = emotion
            
        elif solution_type == "adjust_previous":
            # 调整前一个场景情感强度
            scene_index = suggestion["location"]["prev_scene_index"]
            target_value = solution["target_value"]
            
            # 获取情感数据副本
            emotion = fixed_scenes[scene_index]["emotion"].copy()
            
            # 更新情感强度
            emotion["original_score"] = self._get_emotion_score(fixed_scenes[scene_index])
            emotion["adjusted_score"] = target_value
            emotion["score"] = target_value
            emotion["intensity"] = target_value
            
            # 替换原情感数据
            fixed_scenes[scene_index]["emotion"] = emotion
            
        elif solution_type == "insert_transition":
            # 插入过渡场景
            prev_index = suggestion["location"]["prev_scene_index"]
            curr_index = suggestion["location"]["current_scene_index"]
            target_value = solution["target_value"]
            
            # 创建过渡场景
            prev_scene = fixed_scenes[prev_index]
            curr_scene = fixed_scenes[curr_index]
            
            # 计算过渡场景的时间范围
            mid_start = prev_scene.get("end", 0)
            mid_end = curr_scene.get("start", mid_start)
            
            # 如果没有合适的时间空间，使用简单平均
            if mid_start >= mid_end:
                mid_start = (prev_scene.get("start", 0) + prev_scene.get("end", 0)) / 2
                mid_end = (curr_scene.get("start", 0) + curr_scene.get("end", 0)) / 2
            
            # 创建过渡场景
            transition_scene = {
                "id": f"transition_{prev_index}_to_{curr_index}",
                "start": mid_start,
                "end": mid_end,
                "is_transition": True,
                "emotion": {
                    "type": self._get_emotion_type(curr_scene),  # 采用目标场景的情感类型
                    "score": target_value,
                    "intensity": target_value,
                    "is_generated": True
                },
                "text": f"[过渡场景 - 情感强度: {target_value:.2f}]"
            }
            
            # 插入过渡场景
            fixed_scenes.insert(curr_index, transition_scene)
        
        return fixed_scenes


# 用于异常处理的类定义
class EmotionJumpError(Exception):
    """情感跳跃异常
    
    当检测到场景间情感变化过大时抛出。
    """
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class EmotionMissingError(Exception):
    """情感数据缺失异常
    
    当场景缺少必要的情感数据时抛出。
    """
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# 便捷函数
def validate_emotion_consistency(scenes: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """验证情感一致性的便捷函数
    
    Args:
        scenes: 场景列表
    
    Returns:
        (是否通过验证, 错误信息)
    """
    validator = EmotionValidator()
    return validator.check_arc(scenes)


def get_consistency_suggestions(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """获取情感一致性修复建议的便捷函数
    
    Args:
        scenes: 场景列表
    
    Returns:
        修复建议列表
    """
    validator = EmotionValidator()
    return validator.suggest_fixes(scenes) 