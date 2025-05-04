#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全余量管理模块

此模块实现视频剪辑处理过程中的安全余量管理功能：
1. 为视频剪辑保留一定比例的安全余量
2. 在触发压缩条件时自动调整视频时长
3. 支持自定义安全余量比例
4. 保护视频不会因异常情况被过度压缩
5. 提供智能调整策略以保证视频质量
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

# 配置日志
logger = logging.getLogger(__name__)

class MarginKeeper:
    """安全余量管理器
    
    为视频剪辑保留安全余量，确保在需要进行调整时有可用的压缩空间。
    """
    
    def __init__(self, margin_ratio: float = 0.05, config: Optional[Dict[str, Any]] = None):
        """初始化安全余量管理器
        
        Args:
            margin_ratio: 安全余量比例，默认为5%
            config: 额外配置参数
        """
        self.margin = margin_ratio  # 默认保留5%余量
        self.config = config or self._default_config()
        logger.info(f"安全余量管理器初始化完成，余量比例: {self.margin:.1%}")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "auto_adjust": True,           # 自动调整时长
            "min_margin": 0.02,            # 最小安全余量（2%）
            "max_margin": 0.15,            # 最大安全余量（15%）
            "critical_threshold": 0.95,    # 触发压缩的临界阈值（当前时长/目标时长 > 95%）
            "preserve_keyframes": True,    # 在调整时尽量保留关键帧
            "duration_key": "duration",    # 场景持续时间键名
            "time_unit": "seconds"         # 时间单位：seconds（秒）或 ms（毫秒）
        }
    
    def apply_margin(self, target_duration: float) -> float:
        """应用安全余量到目标时长
        
        Args:
            target_duration: 目标时长
            
        Returns:
            应用安全余量后的实际可用时长
        """
        if target_duration <= 0:
            logger.warning("目标时长必须大于零")
            return 0
            
        # 应用安全余量
        adjusted_duration = target_duration * (1 - self.margin)
        logger.debug(f"目标时长: {target_duration:.2f}，应用{self.margin:.1%}安全余量后: {adjusted_duration:.2f}")
        
        return adjusted_duration
    
    def check_duration_safety(self, current_duration: float, target_duration: float) -> Dict[str, Any]:
        """检查当前时长是否超过安全阈值
        
        Args:
            current_duration: 当前总时长
            target_duration: 目标时长上限
            
        Returns:
            安全状态信息
        """
        if target_duration <= 0:
            return {
                "safe": False,
                "ratio": float('inf'),
                "margin_left": 0,
                "needs_compression": True,
                "compression_ratio": 0.5  # 默认压缩一半
            }
            
        # 计算当前时长与目标时长的比率
        ratio = current_duration / target_duration
        margin_left = target_duration - current_duration
        critical_threshold = self.config["critical_threshold"]
        
        # 确定安全状态
        is_safe = ratio <= critical_threshold
        needs_compression = ratio > critical_threshold
        
        # 如果需要压缩，计算建议的压缩比例
        compression_ratio = 1.0
        if needs_compression:
            # 计算需要达到的目标时长
            safe_target = target_duration * critical_threshold
            # 计算压缩比例
            compression_ratio = safe_target / current_duration
            
        return {
            "safe": is_safe,
            "ratio": ratio,
            "margin_left": margin_left,
            "needs_compression": needs_compression,
            "compression_ratio": compression_ratio,
            "safe_target": safe_target if needs_compression else None
        }
    
    def adjust_scene_durations(self, scenes: List[Dict[str, Any]], target_duration: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """根据安全余量调整场景时长
        
        当总时长超过安全阈值时，自动调整场景时长
        
        Args:
            scenes: 场景列表
            target_duration: 目标总时长
            
        Returns:
            调整后的场景列表和调整信息
        """
        if not scenes:
            return scenes, {"adjusted": False, "reason": "无场景可调整"}
            
        # 获取配置
        duration_key = self.config["duration_key"]
        auto_adjust = self.config["auto_adjust"]
        
        # 计算当前总时长
        current_total = sum(scene.get(duration_key, 0) for scene in scenes)
        
        # 检查安全状态
        safety_info = self.check_duration_safety(current_total, target_duration)
        
        # 如果在安全范围内或不需要自动调整，直接返回
        if safety_info["safe"] or not auto_adjust:
            return scenes, {
                "adjusted": False,
                "safety_info": safety_info,
                "reason": "在安全范围内" if safety_info["safe"] else "未启用自动调整"
            }
            
        # 需要调整，复制场景列表以避免修改原始数据
        adjusted_scenes = [scene.copy() for scene in scenes]
        compression_ratio = safety_info["compression_ratio"]
        
        # 根据可压缩性对场景进行分类
        compressible_scenes = []
        protected_scenes = []
        
        for scene in adjusted_scenes:
            if self._is_scene_compressible(scene):
                compressible_scenes.append(scene)
            else:
                protected_scenes.append(scene)
                
        # 如果没有可压缩的场景，返回原场景列表
        if not compressible_scenes:
            return scenes, {
                "adjusted": False,
                "safety_info": safety_info,
                "reason": "没有可压缩的场景"
            }
            
        # 计算可压缩场景的总时长
        compressible_total = sum(scene.get(duration_key, 0) for scene in compressible_scenes)
        
        # 计算需要从可压缩场景中减少的总时长
        protected_total = sum(scene.get(duration_key, 0) for scene in protected_scenes)
        safe_target = safety_info.get("safe_target", target_duration * self.config["critical_threshold"])
        reduction_needed = current_total - safe_target
        
        # 如果需要减少的时长大于可压缩场景总时长的80%，发出警告
        if reduction_needed > compressible_total * 0.8:
            logger.warning(f"需要减少的时长({reduction_needed:.2f})接近可压缩场景总时长({compressible_total:.2f})的80%")
            
        # 计算压缩比例 - 仅应用于可压缩场景
        adjusted_compression_ratio = max(0.2, 1 - (reduction_needed / compressible_total))
        
        # 应用压缩比例到可压缩场景
        for scene in compressible_scenes:
            original_duration = scene.get(duration_key, 0)
            scene[duration_key] = original_duration * adjusted_compression_ratio
            # 记录调整信息
            scene["_adjustment_info"] = {
                "original_duration": original_duration,
                "compression_ratio": adjusted_compression_ratio,
                "reason": "安全余量调整"
            }
            
        # 重新计算调整后的总时长
        new_total = protected_total + sum(scene.get(duration_key, 0) for scene in compressible_scenes)
        
        logger.info(f"安全余量调整：原始时长 {current_total:.2f} -> 调整后 {new_total:.2f}，目标 {target_duration:.2f}")
        
        return adjusted_scenes, {
            "adjusted": True,
            "original_duration": current_total,
            "new_duration": new_total,
            "target_duration": target_duration,
            "safety_threshold": self.config["critical_threshold"],
            "compression_applied": adjusted_compression_ratio,
            "scenes_adjusted": len(compressible_scenes),
            "scenes_protected": len(protected_scenes)
        }
    
    def _is_scene_compressible(self, scene: Dict[str, Any]) -> bool:
        """检查场景是否可压缩
        
        Args:
            scene: 场景数据
            
        Returns:
            是否可压缩
        """
        # 检查是否有压缩限制标记
        compression_info = scene.get("_compression_info", {})
        if not compression_info:
            return True  # 默认可压缩
            
        # 检查是否禁止压缩
        if compression_info.get("no_compress", False):
            return False
            
        # 检查压缩限制级别
        restriction_level = compression_info.get("restriction_level", "NONE")
        if restriction_level in ("HIGH", "CRITICAL"):
            return False
            
        # 检查是否有保护信息
        protection_info = scene.get("_protection_info", {})
        if protection_info:
            # 检查保护级别
            protection_level = protection_info.get("level", "NONE")
            if protection_level in ("HIGH", "CRITICAL"):
                return False
                
            # 检查保护策略
            strategies = protection_info.get("strategies", [])
            if "NO_COMPRESS" in strategies or "LOCK" in strategies:
                return False
                
        return True

    def set_margin_ratio(self, margin_ratio: float) -> None:
        """设置安全余量比例
        
        Args:
            margin_ratio: 新的安全余量比例
        """
        # 确保余量在合理范围内
        min_margin = self.config["min_margin"]
        max_margin = self.config["max_margin"]
        
        if margin_ratio < min_margin:
            logger.warning(f"安全余量比例 {margin_ratio:.1%} 小于最小值 {min_margin:.1%}，已调整为最小值")
            margin_ratio = min_margin
        elif margin_ratio > max_margin:
            logger.warning(f"安全余量比例 {margin_ratio:.1%} 大于最大值 {max_margin:.1%}，已调整为最大值")
            margin_ratio = max_margin
            
        self.margin = margin_ratio
        logger.info(f"安全余量比例已设置为 {self.margin:.1%}")


def apply_safety_margin(target_duration: float, margin_ratio: float = 0.05) -> float:
    """应用安全余量到目标时长
    
    Args:
        target_duration: 目标时长
        margin_ratio: 安全余量比例，默认为5%
        
    Returns:
        应用安全余量后的实际可用时长
    """
    keeper = MarginKeeper(margin_ratio)
    return keeper.apply_margin(target_duration)


def adjust_for_safety(scenes: List[Dict[str, Any]], target_duration: float, 
                    margin_ratio: float = 0.05, 
                    config: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """根据安全余量调整场景时长
    
    Args:
        scenes: 场景列表
        target_duration: 目标总时长
        margin_ratio: 安全余量比例，默认为5%
        config: 额外配置参数
        
    Returns:
        调整后的场景列表和调整信息
    """
    keeper = MarginKeeper(margin_ratio, config)
    return keeper.adjust_scene_durations(scenes, target_duration) 