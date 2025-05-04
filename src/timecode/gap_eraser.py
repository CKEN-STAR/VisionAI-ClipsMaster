#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
毫秒级间隙消除模块

此模块实现视频场景之间的微小间隙消除功能：
1. 自动检测视频场景之间的微小间隙 
2. 根据设定的阈值自动消除这些间隙
3. 支持自定义最小/最大间隙阈值
4. 保证关键场景边界完整性
5. 支持处理多种时间码格式
"""

import logging
import math
from typing import Dict, List, Tuple, Optional, Any, Union, Callable

# 配置日志
logger = logging.getLogger(__name__)

class GapEraser:
    """场景间隙消除器
    
    检测并消除视频场景之间的微小间隙，确保视频剪辑的连续性。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化间隙消除器
        
        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()
        logger.info("间隙消除器初始化完成")
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "min_gap_threshold": 1,         # 最小间隙阈值（毫秒）
            "max_gap_threshold": 50,        # 最大间隙阈值（毫秒），超过此值的间隙不会被消除
            "prefer_end_adjustment": True,  # 优先调整结束点而不是起始点
            "preserve_keyframes": True,     # 尝试保留关键帧（避免在关键帧处切割）
            "respect_protection": True,     # 尊重场景保护标记
            "start_key": "start_time",      # 场景起始时间键名
            "end_key": "end_time",          # 场景结束时间键名
            "duration_key": "duration",     # 场景持续时间键名
            "time_unit": "seconds"          # 时间单位：seconds（秒）或 ms（毫秒）
        }
    
    def eliminate_gaps(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """消除场景之间的微小间隙
        
        Args:
            scenes: 场景列表
            
        Returns:
            处理后的场景列表
        """
        if not scenes or len(scenes) < 2:
            return scenes
        
        # 获取配置参数
        min_threshold = self.config["min_gap_threshold"]
        max_threshold = self.config["max_gap_threshold"]
        start_key = self.config["start_key"]
        end_key = self.config["end_key"]
        duration_key = self.config["duration_key"]
        time_unit = self.config["time_unit"]
        respect_protection = self.config["respect_protection"]
        
        # 确定时间单位转换系数
        time_factor = 1.0 if time_unit == "seconds" else 0.001
        
        # 复制场景列表以避免修改原始数据
        processed_scenes = [scene.copy() for scene in scenes]
        gaps_eliminated = 0
        
        # 处理每一对相邻场景
        for i in range(1, len(processed_scenes)):
            prev_scene = processed_scenes[i-1]
            curr_scene = processed_scenes[i]
            
            # 获取前一场景的结束时间
            prev_end = prev_scene.get(end_key, 0)
            
            # 获取当前场景的开始时间
            curr_start = curr_scene.get(start_key, 0)
            
            # 计算间隙大小（毫秒）
            gap_size = (curr_start - prev_end) / time_factor * 1000
            
            # 检查间隙是否在阈值范围内
            if min_threshold <= gap_size <= max_threshold:
                # 检查是否有保护标记
                if respect_protection:
                    prev_protected = self._is_scene_protected(prev_scene)
                    curr_protected = self._is_scene_protected(curr_scene)
                    
                    # 如果两个场景都受保护，则不消除间隙
                    if prev_protected and curr_protected:
                        logger.debug(f"场景 {i-1} 和 {i} 之间的间隙未消除（两个场景都受保护）")
                        continue
                
                # 决定要调整哪个场景
                if (self.config["prefer_end_adjustment"] and not self._is_scene_protected(prev_scene)) or \
                   self._is_scene_protected(curr_scene):
                    # 调整前一场景的结束时间
                    prev_scene[end_key] = curr_start
                    # 更新持续时间
                    if duration_key in prev_scene:
                        prev_scene[duration_key] = curr_start - prev_scene.get(start_key, 0)
                else:
                    # 调整当前场景的开始时间
                    curr_scene[start_key] = prev_end
                    # 更新持续时间
                    if duration_key in curr_scene:
                        curr_scene[duration_key] = curr_scene.get(end_key, 0) - prev_end
                
                gaps_eliminated += 1
                logger.debug(f"消除了场景 {i-1} 和 {i} 之间的 {gap_size:.2f} 毫秒间隙")
        
        logger.info(f"总共消除了 {gaps_eliminated} 个间隙")
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
        if protection_level in ("HIGH", "CRITICAL"):
            return True
        
        # 检查保护策略
        strategies = protection_info.get("strategies", [])
        return "NO_TRIM" in strategies or "LOCK" in strategies


def eliminate_gaps(scenes: List[Dict[str, Any]], 
                 max_gap_ms: float = 50.0,
                 config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """消除场景之间的微小间隙
    
    Args:
        scenes: 场景列表
        max_gap_ms: 最大间隙阈值（毫秒）
        config: 额外配置参数
        
    Returns:
        处理后的场景列表
    """
    # 创建一个临时的GapEraser对象以获取默认配置
    temp_eraser = GapEraser()
    default_config = temp_eraser._default_config()
    
    # 合并配置
    merged_config = default_config.copy()
    if config:
        merged_config.update(config)
    
    # 设置最大间隙阈值
    merged_config["max_gap_threshold"] = max_gap_ms
    
    # 创建间隙消除器并处理
    eraser = GapEraser(merged_config)
    return eraser.eliminate_gaps(scenes) 