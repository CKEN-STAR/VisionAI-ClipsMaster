#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节奏调节器

根据叙事结构和情感调整场景节奏，创造更具观赏性的短视频剪辑
通过调整场景时长、过渡方式和内容密度来优化观看体验
"""

import logging
import math
import random
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union

from src.narrative.anchor_types import AnchorType, AnchorInfo
from src.utils.validators import validate_float_range

# 创建日志记录器
logger = logging.getLogger("rhythm_tuner")


class PaceType(Enum):
    """节奏类型枚举"""
    ACCELERATED = "accelerated"   # 加速节奏（前部分慢，后部分快）
    ALTERNATE = "alternate"       # 交替节奏（快慢交替）
    UNIFORM = "uniform"           # 均匀节奏（速度基本一致）
    DECELERATED = "decelerated"   # 减速节奏（前部分快，后部分慢）
    WAVE = "wave"                 # 波浪节奏（快-慢-快的波浪形）
    CLIMAX_FOCUS = "climax_focus" # 高潮聚焦（高潮部分放慢，其他部分加快）


class RhythmTuner:
    """
    节奏调节器，根据场景内容调整节奏感
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化节奏调节器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 默认节奏结构
        self.structure = "激励风暴"  # 默认使用激励风暴结构
        
        # 是否自动检测结构类型
        self.auto_detect = True
        
        logger.info("节奏调节器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载配置文件"""
        # 默认配置
        config = {
            "pace_adjustment": {
                "accelerated": {
                    "start_factor": 1.3,    # 初始减速因子
                    "end_factor": 0.7,      # 结尾加速因子
                    "curve": "exponential"  # 变化曲线类型
                },
                "alternate": {
                    "slow_factor": 1.2,     # 减速因子
                    "fast_factor": 0.8,     # 加速因子
                    "segment_count": 4      # 分段数量
                },
                "uniform": {
                    "factor": 1.0,          # 均匀因子
                    "variation": 0.05       # 允许的微小变化
                },
                "decelerated": {
                    "start_factor": 0.8,    # 初始加速因子
                    "end_factor": 1.3,      # 结尾减速因子
                    "curve": "exponential"  # 变化曲线类型
                },
                "wave": {
                    "amplitude": 0.3,       # 振幅大小
                    "cycles": 2,            # 周期数
                    "base_factor": 1.0      # 基础因子
                },
                "climax_focus": {
                    "normal_factor": 0.85,  # 正常部分加速因子
                    "climax_factor": 1.2,   # 高潮部分减速因子
                    "climax_range": 0.2     # 高潮部分范围（总长度的比例）
                }
            },
            "structure_pace_mapping": {
                "激励风暴": "accelerated",      # 微信/抖音爆款"干货"激励类短视频
                "变形记": "alternate",          # 前后反差对比大
                "交织线索": "alternate",        # 多线索交织推进
                "悬念解构": "decelerated",      # 悬念逐步展开
                "横向对比": "wave",             # 多个案例横向对比
                "金字塔": "climax_focus",       # 核心观点居中，前后铺垫
                "剧情反转": "decelerated",      # 反转在后半段
                "三段式": "uniform"             # 均匀三段式结构
            },
            "transition_styles": [
                "硬切",       # 直接切换
                "淡入淡出",   # 渐变切换
                "滑动",       # 滑动切换
                "缩放",       # 缩放切换
                "旋转",       # 旋转切换
                "闪白"        # 闪白切换
            ],
            "min_duration": 0.8,    # 最短片段时长(秒)
            "max_duration": 8.0,    # 最长片段时长(秒)
            "default_factor": 1.0   # 默认调整因子
        }
        
        # TODO: 如果指定了配置文件路径，加载自定义配置
        
        return config
    
    def set_structure(self, structure: str) -> None:
        """
        设置节奏结构类型
        
        Args:
            structure: 节奏结构名称
        """
        if structure in self.config["structure_pace_mapping"]:
            self.structure = structure
            self.auto_detect = False
            logger.info(f"已设置节奏结构: {structure}")
        else:
            available_structures = list(self.config["structure_pace_mapping"].keys())
            logger.warning(f"未知的节奏结构: {structure}，可用的结构: {', '.join(available_structures)}")
    
    def get_available_structures(self) -> List[str]:
        """
        获取所有可用的节奏结构
        
        Returns:
            节奏结构名称列表
        """
        return list(self.config["structure_pace_mapping"].keys())
    
    def _detect_structure(self, scenes: List[Dict[str, Any]]) -> str:
        """
        根据场景内容自动检测合适的节奏结构
        
        Args:
            scenes: 场景列表
            
        Returns:
            检测到的节奏结构名称
        """
        # 简单检测算法 - 可以未来扩展
        # 1. 检查开头和结尾的情感变化
        # 2. 检查是否有明显的高潮点
        # 3. 检查场景长度分布
        
        if not scenes:
            return "三段式"  # 默认结构
        
        # 检查场景数量
        if len(scenes) <= 3:
            return "三段式"  # 场景较少，使用简单结构
        
        # 检查是否有标签表明内容类型
        all_tags = []
        for scene in scenes:
            tags = scene.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            all_tags.extend(tags)
        
        # 根据标签判断内容类型，按照特异性排序，避免误判
        if any(tag in ["悬念", "悬念线索", "谜题"] for tag in all_tags):
            return "悬念解构"
        
        if any(tag in ["激励", "干货", "成长", "正能量"] for tag in all_tags):
            return "激励风暴"
        
        # 对于容易混淆的标签，使用更精确的匹配条件
        if any(tag == "横向" for tag in all_tags) or (
            any(tag == "对比" for tag in all_tags) and any(tag == "案例" for tag in all_tags)):
            return "横向对比"
            
        if any(tag in ["前后对比", "变化", "变形"] for tag in all_tags) or (
            any(tag == "对比" for tag in all_tags) and not any(tag == "案例" for tag in all_tags)):
            return "变形记"
        
        if any(tag in ["多线索", "交织", "并行"] for tag in all_tags):
            return "交织线索"
            
        if any(tag in ["反转", "转折", "意外"] for tag in all_tags):
            return "剧情反转"
            
        # 检查高潮标签的位置
        climax_positions = []
        for i, scene in enumerate(scenes):
            tags = scene.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            
            if any(tag in ["高潮", "关键", "重点", "核心"] for tag in tags):
                climax_positions.append(i / len(scenes))
        
        # 根据高潮位置判断结构
        if climax_positions:
            # 计算高潮位置的平均值
            avg_climax = sum(climax_positions) / len(climax_positions)
            
            if 0.4 <= avg_climax <= 0.6:
                return "金字塔"
            elif avg_climax > 0.7:
                return "剧情反转"
            elif avg_climax < 0.3:
                return "激励风暴"
        
        # 默认返回三段式
        return "三段式"
    
    def adjust_pacing(self, scenes: List[Dict[str, Any]], anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
        """
        根据节奏结构调整场景节奏
        
        Args:
            scenes: 场景列表
            anchors: 锚点信息，可选
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return []
        
        # 创建场景副本以避免修改原始数据
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 如果开启自动检测，则检测节奏结构
        structure = self.structure
        if self.auto_detect:
            structure = self._detect_structure(scenes)
            logger.info(f"自动检测到节奏结构: {structure}")
            
        # 获取对应的节奏类型
        pace_type = self.config["structure_pace_mapping"].get(structure)
        if not pace_type:
            logger.warning(f"未找到结构 {structure} 对应的节奏类型，使用uniform")
            pace_type = "uniform"
        
        # 根据节奏类型应用调整
        if pace_type == "accelerated":
            adjusted_scenes = self._accelerate_first_half(adjusted_scenes)
        elif pace_type == "alternate":
            adjusted_scenes = self._alternate_pacing(adjusted_scenes)
        elif pace_type == "uniform":
            adjusted_scenes = self._uniform_pacing(adjusted_scenes)
        elif pace_type == "decelerated":
            adjusted_scenes = self._decelerate_second_half(adjusted_scenes)
        elif pace_type == "wave":
            adjusted_scenes = self._wave_pacing(adjusted_scenes)
        elif pace_type == "climax_focus":
            adjusted_scenes = self._climax_focus_pacing(adjusted_scenes, anchors)
        else:
            logger.warning(f"未知的节奏类型: {pace_type}，保持原始节奏")
            
        # 添加节奏元数据
        self._add_rhythm_metadata(adjusted_scenes, structure, pace_type)
        
        # 添加转场建议
        self._suggest_transitions(adjusted_scenes)
        
        return adjusted_scenes
    
    def _accelerate_first_half(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        前半段减速，后半段加速
        
        Args:
            scenes: 场景列表
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return scenes
            
        n = len(scenes)
        midpoint = n // 2
        config = self.config["pace_adjustment"]["accelerated"]
        
        for i, scene in enumerate(scenes):
            # 计算相对位置(0-1)
            rel_pos = i / n
            
            # 根据指数曲线计算调整因子
            if config["curve"] == "exponential":
                if i < midpoint:
                    # 前半段减速（因子>1）
                    rel_first_half = i / midpoint
                    factor = config["start_factor"] * (1 - rel_first_half) + config["end_factor"] * rel_first_half
                else:
                    # 后半段加速（因子<1）
                    rel_second_half = (i - midpoint) / (n - midpoint)
                    # 确保后半段因子小于1（加速）
                    second_half_start = min(1.0, config["end_factor"])  # 确保不大于1
                    second_half_end = min(second_half_start * 0.7, 0.7)  # 确保结尾更快
                    factor = second_half_start * (1 - rel_second_half) + second_half_end * rel_second_half
            else:
                # 线性变化
                if i < midpoint:
                    # 前半段线性从大到小
                    rel_first_half = i / midpoint
                    factor = config["start_factor"] * (1 - rel_first_half) + 1.0 * rel_first_half
                else:
                    # 后半段线性从1到小
                    rel_second_half = (i - midpoint) / (n - midpoint)
                    factor = 1.0 * (1 - rel_second_half) + config["end_factor"] * rel_second_half
            
            # 应用调整因子
            self._apply_duration_factor(scene, factor)
        
        return scenes
    
    def _alternate_pacing(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        交替快慢节奏
        
        Args:
            scenes: 场景列表
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return scenes
            
        n = len(scenes)
        config = self.config["pace_adjustment"]["alternate"]
        segment_count = min(config["segment_count"], n // 2)  # 至少每段2个场景
        segment_length = n / segment_count
        
        for i, scene in enumerate(scenes):
            # 确定当前片段所在的段
            segment = int(i / segment_length)
            
            # 偶数段减速，奇数段加速
            if segment % 2 == 0:
                factor = config["slow_factor"]
            else:
                factor = config["fast_factor"]
            
            # 应用调整因子
            self._apply_duration_factor(scene, factor)
        
        return scenes
    
    def _uniform_pacing(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        均匀节奏，保持一致的速度，只有微小变化
        
        Args:
            scenes: 场景列表
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return scenes
            
        config = self.config["pace_adjustment"]["uniform"]
        base_factor = config["factor"]
        variation = config["variation"]
        
        for scene in scenes:
            # 在基础因子上添加微小随机变化
            factor = base_factor + random.uniform(-variation, variation)
            
            # 应用调整因子
            self._apply_duration_factor(scene, factor)
        
        return scenes
    
    def _decelerate_second_half(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        前半段加速，后半段减速
        
        Args:
            scenes: 场景列表
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return scenes
            
        n = len(scenes)
        midpoint = n // 2
        config = self.config["pace_adjustment"]["decelerated"]
        
        for i, scene in enumerate(scenes):
            # 计算相对位置(0-1)
            rel_pos = i / n
            
            # 根据曲线计算调整因子
            if config["curve"] == "exponential":
                if i < midpoint:
                    # 前半段加速（因子<1）
                    factor = config["start_factor"] * (1 - rel_pos * 2) + config["end_factor"] * (rel_pos * 2)
                else:
                    # 后半段减速（因子>1）
                    rel_second_half = (i - midpoint) / (n - midpoint)
                    factor = config["start_factor"] * (1 - rel_second_half) + config["end_factor"] * rel_second_half
            else:
                # 线性变化
                factor = config["start_factor"] * (1 - rel_pos) + config["end_factor"] * rel_pos
            
            # 应用调整因子
            self._apply_duration_factor(scene, factor)
        
        return scenes
    
    def _wave_pacing(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        波浪形节奏，快慢交替变化
        
        Args:
            scenes: 场景列表
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return scenes
            
        n = len(scenes)
        config = self.config["pace_adjustment"]["wave"]
        
        for i, scene in enumerate(scenes):
            # 计算相对位置(0-1)
            rel_pos = i / n
            
            # 使用正弦波计算调整因子
            # 正弦值范围[-1,1]，转换为因子范围
            wave = math.sin(rel_pos * 2 * math.pi * config["cycles"])
            factor = config["base_factor"] + wave * config["amplitude"]
            
            # 应用调整因子
            self._apply_duration_factor(scene, factor)
        
        return scenes
    
    def _climax_focus_pacing(self, scenes: List[Dict[str, Any]], 
                          anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
        """
        高潮部分放慢，其他部分加快
        
        Args:
            scenes: 场景列表
            anchors: 锚点信息，可选
            
        Returns:
            调整后的场景列表
        """
        if not scenes:
            return scenes
            
        n = len(scenes)
        config = self.config["pace_adjustment"]["climax_focus"]
        
        # 确定高潮位置
        climax_pos = 0.5  # 默认在中间
        
        # 从锚点中查找高潮点
        if anchors:
            for anchor in anchors:
                if anchor.type == AnchorType.CLIMAX:
                    climax_pos = anchor.position
                    break
        
        # 从标签中查找高潮点
        else:
            for i, scene in enumerate(scenes):
                tags = scene.get("tags", [])
                if isinstance(tags, str):
                    tags = [tags]
                
                if any(tag in ["高潮", "关键", "重点", "核心"] for tag in tags):
                    climax_pos = i / n
                    break
        
        # 确定高潮范围
        range_half_width = config["climax_range"] / 2
        climax_start = max(0, climax_pos - range_half_width)
        climax_end = min(1, climax_pos + range_half_width)
        
        # 应用调整
        for i, scene in enumerate(scenes):
            # 计算相对位置(0-1)
            rel_pos = i / n
            
            # 判断是否在高潮范围内
            if climax_start <= rel_pos <= climax_end:
                # 高潮部分减速
                factor = config["climax_factor"]
            else:
                # 其他部分加速
                factor = config["normal_factor"]
            
            # 应用调整因子
            self._apply_duration_factor(scene, factor)
        
        return scenes
    
    def _apply_duration_factor(self, scene: Dict[str, Any], factor: float) -> None:
        """
        应用持续时间调整因子
        
        Args:
            scene: 场景字典
            factor: 调整因子（>1减速，<1加速）
        """
        # 限制因子范围，避免过度调整
        factor = max(0.5, min(2.0, factor))
        
        # 获取原始时长
        if "duration" in scene:
            original_duration = scene["duration"]
        elif "time" in scene and "start" in scene["time"] and "end" in scene["time"]:
            original_duration = scene["time"]["end"] - scene["time"]["start"]
        else:
            # 无法找到时长信息
            return
        
        # 应用调整因子
        new_duration = original_duration * factor
        
        # 确保在合理范围内
        min_duration = self.config["min_duration"]
        max_duration = self.config["max_duration"]
        new_duration = max(min_duration, min(max_duration, new_duration))
        
        # 更新场景时长
        if "duration" in scene:
            scene["duration"] = new_duration
            
        # 更新场景结束时间（假设开始时间不变）
        if "time" in scene and "start" in scene["time"] and "end" in scene["time"]:
            scene["time"]["end"] = scene["time"]["start"] + new_duration
        
        # 记录调整信息
        if "rhythm_adjustments" not in scene:
            scene["rhythm_adjustments"] = {}
            
        scene["rhythm_adjustments"]["original_duration"] = original_duration
        scene["rhythm_adjustments"]["adjustment_factor"] = factor
        scene["rhythm_adjustments"]["adjusted_duration"] = new_duration
    
    def _add_rhythm_metadata(self, scenes: List[Dict[str, Any]], 
                          structure: str, pace_type: str) -> None:
        """
        添加节奏元数据到场景中
        
        Args:
            scenes: 场景列表
            structure: 使用的节奏结构
            pace_type: 使用的节奏类型
        """
        for scene in scenes:
            if "metadata" not in scene:
                scene["metadata"] = {}
                
            scene["metadata"]["rhythm_structure"] = structure
            scene["metadata"]["pace_type"] = pace_type
    
    def _suggest_transitions(self, scenes: List[Dict[str, Any]]) -> None:
        """
        根据节奏和场景内容推荐转场效果
        
        Args:
            scenes: 场景列表
        """
        available_transitions = self.config["transition_styles"]
        
        for i in range(1, len(scenes)):
            prev_scene = scenes[i-1]
            curr_scene = scenes[i]
            
            # 检查情感变化
            prev_sentiment = prev_scene.get("sentiment", {}).get("label", "NEUTRAL")
            curr_sentiment = curr_scene.get("sentiment", {}).get("label", "NEUTRAL")
            
            # 确定转场类型
            transition = None
            
            # 如果情感变化大，使用强调转场
            if prev_sentiment != curr_sentiment:
                if prev_sentiment == "POSITIVE" and curr_sentiment == "NEGATIVE":
                    # 正向到负向的突变
                    transition = "闪白" if "闪白" in available_transitions else "硬切"
                elif prev_sentiment == "NEGATIVE" and curr_sentiment == "POSITIVE":
                    # 负向到正向的明亮转变
                    transition = "淡入淡出" if "淡入淡出" in available_transitions else "硬切"
            
            # 检查是否有特殊标签
            curr_tags = curr_scene.get("tags", [])
            if isinstance(curr_tags, str):
                curr_tags = [curr_tags]
                
            # 根据标签选择转场
            if "高潮" in curr_tags or "关键" in curr_tags:
                transition = "缩放" if "缩放" in available_transitions else "硬切"
            elif "转折" in curr_tags or "转场" in curr_tags:
                transition = "旋转" if "旋转" in available_transitions else "滑动"
            
            # 如果没有特殊情况，使用默认转场
            if not transition:
                # 默认使用硬切，但根据位置有一定随机性
                transition_probability = {
                    "硬切": 0.7,
                    "滑动": 0.15,
                    "淡入淡出": 0.15
                }
                
                # 根据概率选择转场
                r = random.random()
                cumulative = 0
                for t, p in transition_probability.items():
                    cumulative += p
                    if r <= cumulative and t in available_transitions:
                        transition = t
                        break
                
                # 确保有一个转场
                if not transition:
                    transition = "硬切"
            
            # 添加转场信息
            if "transition" not in curr_scene:
                curr_scene["transition"] = {}
                
            curr_scene["transition"]["type"] = transition
            curr_scene["transition"]["from_sentiment"] = prev_sentiment
            curr_scene["transition"]["to_sentiment"] = curr_sentiment


# 提供便捷函数
def adjust_pacing(scenes: List[Dict[str, Any]], structure: str = None, 
                anchors: Optional[List[AnchorInfo]] = None) -> List[Dict[str, Any]]:
    """
    根据节奏结构调整场景节奏的便捷函数
    
    Args:
        scenes: 场景列表
        structure: 节奏结构名称，可选
        anchors: 锚点信息，可选
        
    Returns:
        调整后的场景列表
    """
    tuner = RhythmTuner()
    
    if structure:
        tuner.set_structure(structure)
        
    return tuner.adjust_pacing(scenes, anchors)


def get_available_structures() -> List[str]:
    """
    获取所有可用的节奏结构的便捷函数
    
    Returns:
        节奏结构名称列表
    """
    tuner = RhythmTuner()
    return tuner.get_available_structures() 