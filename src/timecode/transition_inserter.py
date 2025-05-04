#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
过渡帧智能插入模块

此模块实现视频场景之间的过渡帧智能插入功能：
1. 在高压缩率场景之间自动插入过渡效果
2. 支持多种过渡类型（淡入淡出、交叉溶解、滑动转场等）
3. 智能匹配场景内容与适合的过渡效果类型
4. 根据场景重要性和压缩情况动态调整过渡时长
5. 支持自定义过渡参数与阈值
"""

import logging
import random
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

# 配置日志
logger = logging.getLogger(__name__)

# 定义过渡类型枚举
class TransitionType:
    """过渡效果类型"""
    CROSSFADE = "crossfade"         # 交叉溶解(50ms)
    SLIDE = "slide"                 # 滑动转场(80ms)
    FADE = "fade"                   # 淡入淡出(100ms)
    DYNAMIC = "dynamic"             # 动态模糊(30ms)
    SHARP_CUT = "sharp_cut"         # 硬切(0ms)

# 过渡效果默认时长（毫秒）
TRANSITION_DURATIONS = {
    TransitionType.CROSSFADE: 50,
    TransitionType.SLIDE: 80,
    TransitionType.FADE: 100,
    TransitionType.DYNAMIC: 30,
    TransitionType.SHARP_CUT: 0
}

class TransitionInserter:
    """过渡帧插入器
    
    在视频场景之间智能插入过渡效果，提升视频流畅度和观感。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化过渡帧插入器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()
        logger.info("过渡帧插入器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "compression_threshold": 0.3,    # 压缩率阈值，超过此值的场景间会插入过渡
            "max_transition_duration": 100,  # 最大过渡时长（毫秒）
            "min_transition_duration": 20,   # 最小过渡时长（毫秒）
            "prefer_dynamic_types": True,    # 是否优先使用动态过渡类型
            "respect_protection": True,      # 尊重场景保护标记
            "auto_select_type": True,        # 自动选择适合的过渡类型
            "default_type": TransitionType.CROSSFADE,  # 默认过渡类型
            "start_key": "start_time",       # 场景起始时间键名
            "end_key": "end_time",           # 场景结束时间键名
            "duration_key": "duration",      # 场景持续时间键名
            "time_unit": "seconds",          # 时间单位：seconds（秒）或 ms（毫秒）
            "compression_rate_key": "compression_rate"  # 压缩率键名
        }
    
    def insert_transitions(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """在满足条件的场景之间插入过渡帧
        
        Args:
            scenes: 场景列表
            
        Returns:
            处理后的场景列表
        """
        if not scenes or len(scenes) < 2:
            return scenes
        
        # 获取配置参数
        compression_threshold = self.config["compression_threshold"]
        start_key = self.config["start_key"]
        end_key = self.config["end_key"]
        duration_key = self.config["duration_key"]
        time_unit = self.config["time_unit"]
        compression_rate_key = self.config["compression_rate_key"]
        
        # 确定时间单位转换系数
        time_factor = 1.0 if time_unit == "seconds" else 0.001
        
        # 复制场景列表以避免修改原始数据
        processed_scenes = [scene.copy() for scene in scenes]
        transitions_inserted = 0
        
        # 处理每一对相邻场景
        i = 0
        while i < len(processed_scenes) - 1:
            curr_scene = processed_scenes[i]
            next_scene = processed_scenes[i+1]
            
            # 检查是否需要插入过渡帧（基于压缩率）
            curr_compression_rate = curr_scene.get(compression_rate_key, 0)
            next_compression_rate = next_scene.get(compression_rate_key, 0)
            
            need_transition = (curr_compression_rate > compression_threshold or 
                               next_compression_rate > compression_threshold)
            
            if need_transition:
                # 如果保护设置开启，检查场景是否受保护
                if self.config["respect_protection"]:
                    curr_protected = self._is_scene_protected(curr_scene)
                    next_protected = self._is_scene_protected(next_scene)
                    
                    # 如果两个场景都受高级别保护，则不插入过渡
                    if curr_protected and next_protected and self._is_critical_protection(curr_scene) and self._is_critical_protection(next_scene):
                        logger.debug(f"场景 {i} 和 {i+1} 之间未插入过渡（两个场景都受严格保护）")
                        i += 1
                        continue
                
                # 为当前场景创建过渡效果
                transition_type = self._select_transition_type(curr_scene, next_scene)
                transition_duration = self._calculate_transition_duration(curr_scene, next_scene, transition_type)
                
                # 为过渡效果预留空间（从当前场景结尾减去一些时间）
                if transition_duration > 0:
                    # 在毫秒级操作
                    transition_sec = transition_duration * time_factor
                    
                    # 调整当前场景结束时间，为过渡预留空间
                    curr_end = curr_scene.get(end_key, 0)
                    curr_scene[end_key] = curr_end - transition_sec / 2
                    
                    # 更新当前场景持续时间
                    if duration_key in curr_scene:
                        curr_scene[duration_key] = curr_scene[end_key] - curr_scene.get(start_key, 0)
                    
                    # 调整下一个场景开始时间
                    next_start = next_scene.get(start_key, 0)
                    next_scene[start_key] = next_start - transition_sec / 2
                    
                    # 更新下一个场景持续时间
                    if duration_key in next_scene:
                        next_scene[duration_key] = next_scene.get(end_key, 0) - next_scene[start_key]
                
                # 创建过渡帧场景并插入到场景列表中
                transition_frame = self._create_transition_frame(curr_scene, next_scene, transition_type, transition_duration)
                
                processed_scenes.insert(i + 1, transition_frame)
                transitions_inserted += 1
                
                # 跳过刚插入的过渡场景
                i += 2
            else:
                i += 1
        
        logger.info(f"总共插入了 {transitions_inserted} 个过渡场景")
        return processed_scenes
    
    def _is_scene_protected(self, scene: Dict[str, Any]) -> bool:
        """检查场景是否受保护
        
        Args:
            scene: 场景数据
            
        Returns:
            是否受保护
        """
        # 检查是否有保护信息
        protection_info = scene.get("_protection_info", {})
        if not protection_info:
            return False
        
        # 检查保护级别
        protection_level = protection_info.get("level", "NONE")
        if protection_level in ("MEDIUM", "HIGH", "CRITICAL"):
            return True
        
        # 检查保护策略
        strategies = protection_info.get("strategies", [])
        return "NO_TRANSITION" in strategies or "LOCK" in strategies
    
    def _is_critical_protection(self, scene: Dict[str, Any]) -> bool:
        """检查场景是否受严格保护
        
        Args:
            scene: 场景数据
            
        Returns:
            是否受严格保护
        """
        protection_info = scene.get("_protection_info", {})
        if not protection_info:
            return False
        
        protection_level = protection_info.get("level", "NONE")
        return protection_level in ("HIGH", "CRITICAL")
    
    def _select_transition_type(self, curr_scene: Dict[str, Any], next_scene: Dict[str, Any]) -> str:
        """根据场景特性选择合适的过渡类型
        
        Args:
            curr_scene: 当前场景
            next_scene: 下一个场景
            
        Returns:
            过渡类型
        """
        if not self.config["auto_select_type"]:
            return self.config["default_type"]
        
        # 智能选择过渡类型的逻辑
        # 根据场景类型、内容、情绪等选择合适的过渡效果
        
        # 检查场景标签和内容
        curr_tags = curr_scene.get("tags", [])
        next_tags = next_scene.get("tags", [])
        
        # 如果场景是动态场景或有动作标签，使用动态过渡
        if (("动作" in curr_tags or "action" in curr_tags) or 
            ("动态" in curr_tags or "dynamic" in curr_tags) or
            ("动作" in next_tags or "action" in next_tags) or 
            ("动态" in next_tags or "dynamic" in next_tags)):
            return TransitionType.DYNAMIC
        
        # 如果是叙事转折或情节变化，使用滑动转场
        if (("转折" in curr_tags or "transition" in curr_tags) or 
            ("场景变化" in curr_tags or "scene_change" in curr_tags) or
            ("转折" in next_tags or "transition" in next_tags) or 
            ("场景变化" in next_tags or "scene_change" in next_tags)):
            return TransitionType.SLIDE
        
        # 如果场景包含情感内容或氛围变化，使用淡入淡出
        if (("情感" in curr_tags or "emotion" in curr_tags) or 
            ("氛围" in curr_tags or "mood" in curr_tags) or
            ("情感" in next_tags or "emotion" in next_tags) or 
            ("氛围" in next_tags or "mood" in next_tags)):
            return TransitionType.FADE
        
        # 默认使用交叉溶解
        return TransitionType.CROSSFADE
    
    def _calculate_transition_duration(self, curr_scene: Dict[str, Any], next_scene: Dict[str, Any], 
                                      transition_type: str) -> int:
        """计算过渡效果的持续时间（毫秒）
        
        Args:
            curr_scene: 当前场景
            next_scene: 下一个场景
            transition_type: 过渡类型
            
        Returns:
            过渡持续时间（毫秒）
        """
        # 获取该类型的默认时长
        base_duration = TRANSITION_DURATIONS.get(transition_type, 50)
        
        # 根据场景重要性和压缩率调整持续时间
        curr_importance = curr_scene.get("importance", 0.5)
        next_importance = next_scene.get("importance", 0.5)
        
        curr_compression = curr_scene.get(self.config["compression_rate_key"], 0)
        next_compression = next_scene.get(self.config["compression_rate_key"], 0)
        
        # 计算重要性调整因子（两个场景的平均重要性）
        importance_factor = (curr_importance + next_importance) / 2.0
        
        # 计算压缩率调整因子（两个场景的平均压缩率）
        compression_factor = (curr_compression + next_compression) / 2.0
        
        # 重要场景的过渡时间会略短，压缩率高的场景过渡时间会略长
        adjusted_duration = base_duration * (1 - importance_factor * 0.3 + compression_factor * 0.5)
        
        # 确保在配置的范围内
        min_duration = self.config["min_transition_duration"]
        max_duration = self.config["max_transition_duration"]
        
        return min(max(int(adjusted_duration), min_duration), max_duration)
    
    def _create_transition_frame(self, curr_scene: Dict[str, Any], next_scene: Dict[str, Any], 
                                transition_type: str, transition_duration: int) -> Dict[str, Any]:
        """创建过渡帧场景
        
        Args:
            curr_scene: 当前场景
            next_scene: 下一个场景
            transition_type: 过渡类型
            transition_duration: 过渡持续时间（毫秒）
            
        Returns:
            过渡帧场景字典
        """
        start_key = self.config["start_key"]
        end_key = self.config["end_key"]
        duration_key = self.config["duration_key"]
        time_unit = self.config["time_unit"]
        
        # 确定时间单位转换系数
        time_factor = 1.0 if time_unit == "seconds" else 0.001
        
        # 计算过渡帧的时间属性（毫秒转为秒或保持毫秒，取决于时间单位）
        transition_time = transition_duration * time_factor
        
        # 计算过渡帧的开始和结束时间
        curr_end = curr_scene.get(end_key, 0)
        next_start = next_scene.get(start_key, 0)
        
        # 过渡帧开始于当前场景调整后的结束点，结束于下一场景调整后的开始点
        transition_start = curr_end
        transition_end = next_start
        
        # 创建过渡帧场景
        transition_frame = {
            "id": f"transition_{curr_scene.get('id', 'scene')}_{next_scene.get('id', 'scene')}",
            start_key: transition_start,
            end_key: transition_end,
            duration_key: transition_end - transition_start,
            "type": "transition",
            "transition_type": transition_type,
            "transition_duration_ms": transition_duration,
            "source_scenes": [curr_scene.get("id", ""), next_scene.get("id", "")],
            "_meta": {
                "auto_generated": True,
                "created_by": "TransitionInserter",
                "original_curr_end": curr_scene.get(end_key, 0) + transition_time / 2,
                "original_next_start": next_scene.get(start_key, 0) - transition_time / 2
            }
        }
        
        return transition_frame


def insert_transitions(scenes: List[Dict[str, Any]], 
                       compression_threshold: float = 0.3,
                       config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """在满足条件的场景之间插入过渡帧
    
    Args:
        scenes: 场景列表
        compression_threshold: 压缩率阈值，超过此值的场景间会插入过渡
        config: 额外配置参数
        
    Returns:
        处理后的场景列表
    """
    # 创建一个临时的TransitionInserter对象以获取默认配置
    temp_inserter = TransitionInserter()
    default_config = temp_inserter._default_config()
    
    # 合并配置
    merged_config = default_config.copy()
    if config:
        merged_config.update(config)
    
    # 设置压缩率阈值
    merged_config["compression_threshold"] = compression_threshold
    
    # 创建过渡帧插入器并处理
    inserter = TransitionInserter(merged_config)
    return inserter.insert_transitions(scenes)


def create_transition_frame(curr_scene: Dict[str, Any], next_scene: Dict[str, Any], 
                           transition_type: str = TransitionType.CROSSFADE, 
                           transition_duration_ms: int = 50) -> Dict[str, Any]:
    """创建过渡帧
    
    创建一个表示两个场景之间过渡效果的帧
    
    Args:
        curr_scene: 当前场景
        next_scene: 下一个场景
        transition_type: 过渡类型，默认为交叉溶解
        transition_duration_ms: 过渡持续时间（毫秒），默认为50ms
        
    Returns:
        过渡帧场景字典
    """
    inserter = TransitionInserter()
    
    # 使用内部方法创建过渡帧
    return inserter._create_transition_frame(
        curr_scene, 
        next_scene, 
        transition_type, 
        transition_duration_ms
    ) 