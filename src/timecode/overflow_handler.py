#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异常溢出处理模块

此模块处理视频剪辑长度超过目标时长的情况：
1. 提供多种溢出处理策略（软、中、强度压缩）
2. 智能调整场景时长，确保最重要的内容得到保留
3. 根据内容重要性动态调整压缩策略
4. 在无法适配目标时长时提供明确错误信息
5. 与其他时间码处理模块无缝协作
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from enum import Enum
import warnings

# 配置日志
logger = logging.getLogger(__name__)


class RescueMode(Enum):
    """溢出处理模式枚举"""
    SOFT = "soft"             # 柔和压缩，均匀调整所有场景
    MODERATE = "moderate"     # 中等压缩，更多压缩非关键场景
    AGGRESSIVE = "aggressive" # 强力压缩，只保留关键场景，大幅压缩其他


class CriticalOverflowError(Exception):
    """严重溢出错误，无法通过压缩解决"""
    pass


class OverflowRescuer:
    """溢出处理器
    
    处理场景总时长超过目标时长的情况，通过智能调整保持内容的完整性和可理解性。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化溢出处理器
        
        Args:
            config: 配置参数
        """
        # 先设置默认配置
        self.config = self._default_config()
        
        # 然后用用户配置更新默认配置
        if config:
            self.config.update(config)
        
        # 定义各种处理模式的调整系数
        self.rescue_modes = {
            "soft": lambda x: x * 0.98,        # 全体轻度压缩
            "moderate": lambda x: x * 0.95,    # 非关键场景中压缩
            "aggressive": lambda x: x * 0.9    # 全员重度压缩
        }
        
        # 不同重要性水平的处理系数
        self.importance_factors = {
            "critical": 1.0,    # 关键场景不压缩
            "high": 0.95,       # 高重要性场景轻微压缩
            "medium": 0.9,      # 中等重要性较多压缩
            "low": 0.8          # 低重要性场景大幅压缩
        }
        
        logger.info("溢出处理器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "max_iterations": 5,          # 最大迭代次数
            "max_compression_ratio": 0.6, # 单场景最大压缩比例
            "key_importance": "importance_score", # 重要性分数字段名
            "duration_key": "duration",   # 时长字段名
            "auto_mode_select": True,     # 自动选择模式
            "protected_tags": ["critical", "highlight", "climax", "opening", "ending"], # 保护标签
            "min_scene_duration": 1.0,    # 最小场景时长（秒）
            "tolerance": 0.01,            # 容差（目标时长的比例）
            "importance_threshold": {     # 重要性阈值
                "critical": 0.9,          # 关键场景阈值
                "high": 0.7,              # 高重要性阈值
                "medium": 0.4             # 中等重要性阈值
            }
        }
    
    def handle_overflow(self, scenes: List[Dict[str, Any]], target_duration: float) -> List[Dict[str, Any]]:
        """处理时长溢出问题
        
        根据各种策略调整场景时长，确保总时长不超过目标时长
        
        Args:
            scenes: 场景列表
            target_duration: 目标时长上限
            
        Returns:
            处理后的场景列表
            
        Raises:
            CriticalOverflowError: 当无法处理溢出问题时
        """
        if not scenes:
            return []
            
        # 复制场景以避免修改原始数据
        adjusted_scenes = [scene.copy() for scene in scenes]
        
        # 计算当前总时长
        duration_key = self.config["duration_key"]
        current_duration = sum(scene.get(duration_key, 0) for scene in adjusted_scenes)
        
        # 如果当前时长已经在目标范围内，无需调整
        if current_duration <= target_duration:
            logger.info(f"当前总时长 {current_duration:.2f}秒 已在目标时长 {target_duration:.2f}秒 范围内，无需调整")
            return adjusted_scenes
            
        # 计算溢出量和比例
        overflow_amount = current_duration - target_duration
        overflow_ratio = overflow_amount / current_duration
        
        logger.info(f"检测到溢出：当前总时长 {current_duration:.2f}秒，目标时长 {target_duration:.2f}秒")
        logger.info(f"溢出量：{overflow_amount:.2f}秒，溢出比例：{overflow_ratio:.2%}")
        
        # 选择处理模式
        rescue_mode = self._select_rescue_mode(overflow_ratio, adjusted_scenes)
        logger.info(f"选择处理模式：{rescue_mode}")
        
        # 为每个场景分配重要性水平
        adjusted_scenes = self._assign_importance_level(adjusted_scenes)
        
        # 根据选择的模式执行处理
        iteration = 0
        max_iterations = self.config["max_iterations"]
        tolerance = self.config["tolerance"] * target_duration
        
        while iteration < max_iterations:
            iteration += 1
            
            # 根据模式应用调整
            if rescue_mode == RescueMode.SOFT:
                adjusted_scenes = self._apply_soft_rescue(adjusted_scenes, target_duration)
            elif rescue_mode == RescueMode.MODERATE:
                adjusted_scenes = self._apply_moderate_rescue(adjusted_scenes, target_duration)
            elif rescue_mode == RescueMode.AGGRESSIVE:
                adjusted_scenes = self._apply_aggressive_rescue(adjusted_scenes, target_duration)
            
            # 重新计算当前总时长
            current_duration = sum(scene.get(duration_key, 0) for scene in adjusted_scenes)
            
            # 如果已达到目标，退出循环
            if current_duration <= target_duration + tolerance:
                logger.info(f"经过 {iteration} 次调整，总时长已降至 {current_duration:.2f}秒")
                break
                
            # 如果仍然溢出过多，升级处理模式
            if iteration == max_iterations - 1 and current_duration > target_duration + tolerance:
                if rescue_mode == RescueMode.SOFT:
                    rescue_mode = RescueMode.MODERATE
                    logger.info("升级至中等处理模式")
                elif rescue_mode == RescueMode.MODERATE:
                    rescue_mode = RescueMode.AGGRESSIVE
                    logger.info("升级至强力处理模式")
        
        # 最终检查
        if current_duration > target_duration + tolerance:
            # 如果仍然超出目标时长，尝试最后的调整方法
            adjusted_scenes = self._last_resort_adjustment(adjusted_scenes, target_duration)
            current_duration = sum(scene.get(duration_key, 0) for scene in adjusted_scenes)
            
            # 如果仍然无法适配，抛出异常
            if current_duration > target_duration + tolerance:
                msg = f"无法解决溢出问题：当前时长 {current_duration:.2f}秒，目标时长 {target_duration:.2f}秒"
                logger.error(msg)
                raise CriticalOverflowError(msg)
        
        # 记录调整信息
        for scene in adjusted_scenes:
            if "_original_duration" in scene:
                original = scene["_original_duration"]
                current = scene.get(duration_key, 0)
                compression_ratio = current / original if original > 0 else 1.0
                scene["_adjustment_info"] = {
                    "original_duration": original,
                    "adjusted_duration": current,
                    "compression_ratio": compression_ratio,
                    "mode": rescue_mode.value
                }
        
        logger.info(f"溢出处理完成：最终总时长 {current_duration:.2f}秒")
        return adjusted_scenes
    
    def _select_rescue_mode(self, overflow_ratio: float, scenes: List[Dict[str, Any]]) -> RescueMode:
        """根据溢出比例和场景情况选择最合适的处理模式
        
        Args:
            overflow_ratio: 溢出比例
            scenes: 场景列表
            
        Returns:
            处理模式
        """
        # 根据溢出比例初步选择模式
        if overflow_ratio < 0.05:  # 溢出不到5%
            mode = RescueMode.SOFT
        elif overflow_ratio < 0.15:  # 溢出5%-15%
            mode = RescueMode.MODERATE
        else:  # 溢出超过15%
            mode = RescueMode.AGGRESSIVE
            
        # 如果有大量关键场景，可能需要更强的处理模式
        if not self.config["auto_mode_select"]:
            return mode
            
        # 计算关键场景比例
        key_importance = self.config["key_importance"]
        importance_threshold = self.config["importance_threshold"]["critical"]
        
        critical_scenes = [s for s in scenes if s.get(key_importance, 0) >= importance_threshold]
        critical_ratio = len(critical_scenes) / len(scenes) if scenes else 0
        
        # 如果关键场景比例很高，升级处理模式
        if critical_ratio > 0.5 and mode == RescueMode.SOFT:
            logger.info(f"关键场景比例高达 {critical_ratio:.1%}，升级至中等处理模式")
            return RescueMode.MODERATE
        elif critical_ratio > 0.7 and mode == RescueMode.MODERATE:
            logger.info(f"关键场景比例高达 {critical_ratio:.1%}，升级至强力处理模式")
            return RescueMode.AGGRESSIVE
            
        return mode
    
    def _assign_importance_level(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为每个场景分配重要性级别
        
        Args:
            scenes: 场景列表
            
        Returns:
            添加了重要性级别的场景列表
        """
        key_importance = self.config["key_importance"]
        thresholds = self.config["importance_threshold"]
        protected_tags = self.config["protected_tags"]
        
        # 保存原始时长
        duration_key = self.config["duration_key"]
        for scene in scenes:
            scene["_original_duration"] = scene.get(duration_key, 0)
            
            # 根据重要性分数和标签设置重要性级别
            score = scene.get(key_importance, 0)
            tags = scene.get("tags", [])
            
            # 检查是否有保护标签
            has_protected_tag = any(tag in protected_tags for tag in tags) if tags else False
            
            # 分配重要性级别
            if has_protected_tag or score >= thresholds["critical"]:
                scene["_importance_level"] = "critical"
            elif score >= thresholds["high"]:
                scene["_importance_level"] = "high"
            elif score >= thresholds["medium"]:
                scene["_importance_level"] = "medium"
            else:
                scene["_importance_level"] = "low"
                
        return scenes
    
    def _apply_soft_rescue(self, scenes: List[Dict[str, Any]], target_duration: float) -> List[Dict[str, Any]]:
        """应用柔和压缩策略
        
        均匀调整所有场景的时长，但根据重要性有所区分
        
        Args:
            scenes: 场景列表
            target_duration: 目标时长
            
        Returns:
            调整后的场景列表
        """
        duration_key = self.config["duration_key"]
        current_duration = sum(scene.get(duration_key, 0) for scene in scenes)
        
        # 计算所需的整体压缩比例
        if current_duration <= target_duration:
            return scenes
            
        compression_needed = target_duration / current_duration
        
        # 根据重要性级别应用不同的压缩系数
        for scene in scenes:
            level = scene.get("_importance_level", "medium")
            original_duration = scene["_original_duration"]
            
            # 应用压缩，但考虑重要性因素
            factor = self.importance_factors.get(level, 1.0)
            adjusted_factor = 1.0 - ((1.0 - compression_needed) * factor)
            
            # 应用压缩但确保不低于最小场景时长
            new_duration = max(original_duration * adjusted_factor, 
                              self.config["min_scene_duration"])
            
            scene[duration_key] = new_duration
            
        return scenes
    
    def _apply_moderate_rescue(self, scenes: List[Dict[str, Any]], target_duration: float) -> List[Dict[str, Any]]:
        """应用中等压缩策略
        
        更多地压缩非关键场景，尽量保留关键场景的时长
        
        Args:
            scenes: 场景列表
            target_duration: 目标时长
            
        Returns:
            调整后的场景列表
        """
        duration_key = self.config["duration_key"]
        
        # 将场景分为关键场景和非关键场景
        critical_scenes = [s for s in scenes if s.get("_importance_level") == "critical"]
        high_scenes = [s for s in scenes if s.get("_importance_level") == "high"]
        other_scenes = [s for s in scenes if s.get("_importance_level") in ["medium", "low"]]
        
        # 计算各组场景的当前总时长
        critical_duration = sum(scene.get(duration_key, 0) for scene in critical_scenes)
        high_duration = sum(scene.get(duration_key, 0) for scene in high_scenes)
        other_duration = sum(scene.get(duration_key, 0) for scene in other_scenes)
        
        current_total = critical_duration + high_duration + other_duration
        
        # 如果已在目标范围内，无需调整
        if current_total <= target_duration:
            return scenes
            
        # 计算需要压缩的时长
        excess_duration = current_total - target_duration
        
        # 先尝试从低重要性场景中削减
        if other_duration > 0:
            # 计算非关键场景的压缩比例
            other_compression = max(0.7, 1.0 - (excess_duration / other_duration))
            
            # 应用压缩
            for scene in other_scenes:
                original_duration = scene["_original_duration"]
                new_duration = max(original_duration * other_compression, 
                                  self.config["min_scene_duration"])
                scene[duration_key] = new_duration
                
            # 重新计算压缩后的总时长
            other_duration = sum(scene.get(duration_key, 0) for scene in other_scenes)
            current_total = critical_duration + high_duration + other_duration
        
        # 如果仍然超出，开始压缩高重要性场景
        if current_total > target_duration and high_duration > 0:
            excess_duration = current_total - target_duration
            high_compression = max(0.8, 1.0 - (excess_duration / high_duration))
            
            for scene in high_scenes:
                original_duration = scene["_original_duration"]
                new_duration = max(original_duration * high_compression, 
                                  self.config["min_scene_duration"])
                scene[duration_key] = new_duration
                
            # 重新计算
            high_duration = sum(scene.get(duration_key, 0) for scene in high_scenes)
            current_total = critical_duration + high_duration + other_duration
        
        # 如果仍然超出，轻微压缩关键场景
        if current_total > target_duration and critical_duration > 0:
            excess_duration = current_total - target_duration
            critical_compression = max(0.9, 1.0 - (excess_duration / critical_duration))
            
            for scene in critical_scenes:
                original_duration = scene["_original_duration"]
                new_duration = max(original_duration * critical_compression, 
                                  self.config["min_scene_duration"])
                scene[duration_key] = new_duration
                
        return scenes
    
    def _apply_aggressive_rescue(self, scenes: List[Dict[str, Any]], target_duration: float) -> List[Dict[str, Any]]:
        """应用强力压缩策略
        
        大幅压缩低重要性场景，中等压缩高重要性场景，尽量保留关键场景
        
        Args:
            scenes: 场景列表
            target_duration: 目标时长
            
        Returns:
            调整后的场景列表
        """
        duration_key = self.config["duration_key"]
        
        # 将场景按重要性分组
        grouped_scenes = {
            "critical": [s for s in scenes if s.get("_importance_level") == "critical"],
            "high": [s for s in scenes if s.get("_importance_level") == "high"],
            "medium": [s for s in scenes if s.get("_importance_level") == "medium"],
            "low": [s for s in scenes if s.get("_importance_level") == "low"]
        }
        
        # 计算各组场景的时长
        group_durations = {
            k: sum(s.get(duration_key, 0) for s in v) 
            for k, v in grouped_scenes.items()
        }
        
        current_total = sum(group_durations.values())
        
        # 如果已在目标范围内，无需调整
        if current_total <= target_duration:
            return scenes
            
        # 强力压缩系数
        compression_factors = {
            "low": 0.6,      # 低重要性场景压缩至60%
            "medium": 0.7,   # 中等重要性场景压缩至70%
            "high": 0.85,    # 高重要性场景压缩至85%
            "critical": 0.95 # 关键场景压缩至95%
        }
        
        # 应用压缩，从低重要性场景开始
        for importance, factor in compression_factors.items():
            for scene in grouped_scenes[importance]:
                original_duration = scene["_original_duration"]
                new_duration = max(original_duration * factor, 
                                  self.config["min_scene_duration"])
                scene[duration_key] = new_duration
                
            # 重新计算当前总时长
            group_durations[importance] = sum(s.get(duration_key, 0) for s in grouped_scenes[importance])
            current_total = sum(group_durations.values())
            
            # 如果已经达到目标，可以停止压缩
            if current_total <= target_duration:
                break
        
        return scenes
    
    def _last_resort_adjustment(self, scenes: List[Dict[str, Any]], target_duration: float) -> List[Dict[str, Any]]:
        """最后手段调整
        
        当其他策略都无法达到目标时，采取更激进的措施
        
        Args:
            scenes: 场景列表
            target_duration: 目标时长
            
        Returns:
            调整后的场景列表
        """
        duration_key = self.config["duration_key"]
        current_duration = sum(scene.get(duration_key, 0) for scene in scenes)
        
        # 如果已在目标范围内，无需调整
        if current_duration <= target_duration:
            return scenes
            
        logger.warning("采用最后手段调整策略")
        
        # 计算需要的总体压缩比例
        compression_ratio = target_duration / current_duration if current_duration > 0 else 0
        
        # 按重要性排序
        sorted_scenes = sorted(
            scenes, 
            key=lambda s: s.get("_importance_level", "low"),
            reverse=True
        )
        
        # 保留关键场景，压缩其他场景
        remaining_duration = target_duration
        min_duration = self.config["min_scene_duration"]
        
        # 第一遍：尝试给关键场景分配足够的时长
        for scene in sorted_scenes:
            if scene.get("_importance_level") == "critical":
                original_duration = scene["_original_duration"]
                # 关键场景至少保留90%
                scene[duration_key] = max(original_duration * 0.9, min_duration)
                remaining_duration -= scene[duration_key]
        
        # 如果剩余时长不足，需要进一步压缩关键场景
        if remaining_duration < 0:
            # 无法避免，必须压缩关键场景
            critical_scenes = [s for s in scenes if s.get("_importance_level") == "critical"]
            critical_duration = sum(s.get(duration_key, 0) for s in critical_scenes)
            
            # 计算必要的压缩比例
            necessary_ratio = target_duration / critical_duration
            
            # 重新分配
            for scene in critical_scenes:
                scene[duration_key] = max(scene[duration_key] * necessary_ratio, min_duration)
                
            # 非关键场景压缩到最小时长
            for scene in scenes:
                if scene.get("_importance_level") != "critical":
                    scene[duration_key] = min_duration
        else:
            # 还有剩余时长，按重要性分配
            non_critical = [s for s in sorted_scenes if s.get("_importance_level") != "critical"]
            
            # 如果没有非关键场景，直接返回
            if not non_critical:
                return scenes
                
            # 计算非关键场景的原始总时长和相对重要性
            non_critical_original = sum(s["_original_duration"] for s in non_critical)
            
            # 按照原始比例分配剩余时长
            for scene in non_critical:
                weight = scene["_original_duration"] / non_critical_original if non_critical_original > 0 else 0
                allocated = remaining_duration * weight
                scene[duration_key] = max(allocated, min_duration)
        
        return scenes


# 辅助函数
def handle_overflow(scenes: List[Dict[str, Any]], 
                   target_duration: float, 
                   mode: str = "auto",
                   config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """处理场景时长溢出
    
    Args:
        scenes: 场景列表
        target_duration: 目标时长上限
        mode: 处理模式，可选 "soft"，"moderate"，"aggressive" 或 "auto"
        config: 配置参数
        
    Returns:
        处理后的场景列表
        
    Raises:
        CriticalOverflowError: 当无法处理溢出问题时
    """
    # 初始化处理器
    rescuer = OverflowRescuer(config)
    
    # 复制场景列表，避免修改原始数据
    scenes_copy = [scene.copy() for scene in scenes]
    
    try:
        # 根据指定模式进行处理
        if mode == "auto":
            result = rescuer.handle_overflow(scenes_copy, target_duration)
        else:
            # 强制使用指定模式
            original_auto_select = rescuer.config["auto_mode_select"]
            rescuer.config["auto_mode_select"] = False
            
            # 根据模式调整
            result = rescuer.handle_overflow(scenes_copy, target_duration)
            
            # 恢复原有设置
            rescuer.config["auto_mode_select"] = original_auto_select
            
        return result
    except CriticalOverflowError as e:
        logger.error(f"处理溢出失败: {str(e)}")
        raise


# 直接使用的函数
def sum_duration(scenes: List[Dict[str, Any]], key: str = "duration") -> float:
    """计算场景列表的总时长
    
    Args:
        scenes: 场景列表
        key: 时长字段名
        
    Returns:
        总时长
    """
    return sum(scene.get(key, 0) for scene in scenes)


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试数据
    test_scenes = [
        {"duration": 20.0, "importance_score": 0.95, "tags": ["opening"]},
        {"duration": 30.0, "importance_score": 0.7},
        {"duration": 25.0, "importance_score": 0.4},
        {"duration": 40.0, "importance_score": 0.9, "tags": ["climax"]},
        {"duration": 15.0, "importance_score": 0.6}
    ]
    
    target = 100.0  # 目标时长
    
    # 测试处理
    try:
        result = handle_overflow(test_scenes, target)
        print(f"总时长: {sum_duration(result):.2f}秒，目标: {target}秒")
        
        # 打印调整情况
        for i, scene in enumerate(result):
            original = scene.get("_original_duration", 0)
            adjusted = scene.get("duration", 0)
            ratio = adjusted / original if original > 0 else 0
            print(f"场景 {i+1}: {original:.1f}秒 -> {adjusted:.1f}秒 ({ratio:.0%})")
    except CriticalOverflowError as e:
        print(f"错误: {e}") 