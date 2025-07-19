#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 熔断动作优先级调度器
根据内存压力级别对熔断动作进行排序，决定最优的执行顺序
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union, Set

# 设置日志
logger = logging.getLogger("fuse_action_scheduler")

class ActionPrioritizer:
    """
    熔断动作优先级调度器，根据内存压力水平确定最优动作执行顺序
    """
    
    # 动作权重配置，数值越高表示动作影响越大
    ACTION_WEIGHTS = {
        # 轻影响动作（仅移除不必要的资源）
        'clear_temp_files': 0.3,        # 清理临时文件，影响小
        'reduce_log_verbosity': 0.3,    # 降低日志级别，影响小
        'flush_memory_cache': 0.4,      # 清空内存缓存，影响较小
        'reduce_cache_size': 0.4,       # 减少缓存大小，影响较小
        
        # 中影响动作（影响功能但不影响核心体验）
        'unload_noncritical_shards': 0.6,      # 卸载非关键分片，中等影响
        'pause_background_tasks': 0.6,         # 暂停后台任务，中等影响
        'degrade_quality': 0.7,                # 降低质量，中等影响
        'switch_to_lightweight_models': 0.7,   # 切换到轻量模型，中等影响
        
        # 高影响动作（显著影响用户体验）
        'disable_features': 0.8,         # 禁用特性，高影响
        'kill_largest_process': 0.9,     # 杀死最大进程，高影响
        'force_gc': 0.8,                 # 强制垃圾回收，可能导致卡顿
        'activate_survival_mode': 1.0    # 生存模式，最高影响
    }
    
    # 压力级别阈值
    PRESSURE_THRESHOLDS = {
        'low': 70,      # 低压力
        'medium': 85,   # 中等压力
        'high': 95      # 高压力
    }
    
    def __init__(self, custom_weights: Optional[Dict[str, float]] = None):
        """
        初始化动作优先级调度器
        
        Args:
            custom_weights: 自定义动作权重，可覆盖默认配置
        """
        # 合并默认权重和自定义权重
        self._action_weights = self.ACTION_WEIGHTS.copy()
        if custom_weights:
            self._action_weights.update(custom_weights)
        
        # 动作分类缓存
        self._action_categories = self._categorize_actions()
        
        logger.info("熔断动作优先级调度器初始化完成")
    
    def _categorize_actions(self) -> Dict[str, List[str]]:
        """
        根据权重对动作进行分类
        
        Returns:
            分类结果字典
        """
        categories = {
            'light': [],     # 轻量级动作 (权重 <= 0.4)
            'medium': [],    # 中等动作 (0.4 < 权重 <= 0.7)
            'heavy': []      # 重量级动作 (权重 > 0.7)
        }
        
        for action, weight in self._action_weights.items():
            if weight <= 0.4:
                categories['light'].append(action)
            elif weight <= 0.7:
                categories['medium'].append(action)
            else:
                categories['heavy'].append(action)
        
        return categories
    
    def schedule_actions(self, available_actions: List[str], pressure_level: float) -> List[str]:
        """
        根据压力级别对动作进行优先级排序
        
        优先级调度策略:
        - 当压力 < 90% 时，优先执行轻量级动作，影响较小的先执行
        - 当压力 >= 90% 时，优先执行重量级动作，影响较大的先执行
        
        Args:
            available_actions: 可用的动作列表
            pressure_level: 当前内存压力级别 (0-100)
            
        Returns:
            按优先级排序后的动作列表
        """
        logger.debug(f"为压力级别 {pressure_level:.1f}% 调度 {len(available_actions)} 个动作")
        
        # 过滤出合法的动作
        valid_actions = [action for action in available_actions if action in self._action_weights]
        
        if not valid_actions:
            logger.warning("无有效动作可调度")
            return []
        
        # 压力级别大于90%时，优先执行高影响动作；否则优先执行低影响动作
        reverse_sort = (pressure_level >= 90)
        
        # 排序动作
        sorted_actions = sorted(
            valid_actions,
            key=lambda x: self._action_weights.get(x, 0.5),
            reverse=reverse_sort
        )
        
        # 记录调度结果
        log_level = logging.DEBUG if len(sorted_actions) <= 3 else logging.INFO
        logger.log(log_level, f"动作调度结果 (压力={pressure_level:.1f}%): {sorted_actions}")
        
        return sorted_actions
    
    def get_optimal_actions(self, all_actions: List[str], pressure_level: float, max_actions: int = 3) -> List[str]:
        """
        从所有动作中选择最优的N个动作
        
        Args:
            all_actions: 所有可用动作
            pressure_level: 当前内存压力级别 (0-100)
            max_actions: 最多选择的动作数量
            
        Returns:
            最优的N个动作
        """
        # 首先对所有动作进行排序
        sorted_actions = self.schedule_actions(all_actions, pressure_level)
        
        # 动态确定需要返回多少个动作，压力级别越高返回越多
        if pressure_level >= self.PRESSURE_THRESHOLDS['high']:
            # 高压力，返回所有动作但不超过上限
            count = min(len(sorted_actions), max_actions)
        elif pressure_level >= self.PRESSURE_THRESHOLDS['medium']:
            # 中等压力，返回约2/3的动作
            count = min(len(sorted_actions), max(2, int(max_actions * 0.67)))
        else:
            # 低压力，返回较少动作
            count = min(len(sorted_actions), max(1, int(max_actions * 0.5)))
        
        return sorted_actions[:count]
    
    def get_action_importance(self, action: str) -> Tuple[float, str]:
        """
        获取动作的重要性评级
        
        Args:
            action: 动作名称
            
        Returns:
            (权重值, 重要性等级)
        """
        weight = self._action_weights.get(action, 0.5)
        
        if weight <= 0.4:
            level = "低"
        elif weight <= 0.7:
            level = "中"
        else:
            level = "高"
            
        return weight, level
    
    def register_custom_weight(self, action: str, weight: float) -> None:
        """
        注册自定义动作权重
        
        Args:
            action: 动作名称
            weight: 权重值 (0.0-1.0)
        """
        if weight < 0.0 or weight > 1.0:
            logger.warning(f"动作权重应在0.0-1.0范围内，收到: {weight}")
            weight = max(0.0, min(weight, 1.0))
            
        self._action_weights[action] = weight
        
        # 更新分类缓存
        self._action_categories = self._categorize_actions()
        
        logger.info(f"注册自定义动作权重: {action} = {weight}")
    
    def get_action_weights(self) -> Dict[str, float]:
        """
        获取所有动作权重配置
        
        Returns:
            动作权重字典
        """
        return self._action_weights.copy()


# 全局单例
_action_prioritizer = None

def get_action_prioritizer() -> ActionPrioritizer:
    """
    获取动作优先级调度器单例
    
    Returns:
        动作优先级调度器实例
    """
    global _action_prioritizer
    
    if _action_prioritizer is None:
        _action_prioritizer = ActionPrioritizer()
        
    return _action_prioritizer


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试动作优先级调度器
    prioritizer = get_action_prioritizer()
    
    # 定义测试动作集
    test_actions = [
        "clear_temp_files",
        "reduce_log_verbosity",
        "unload_noncritical_shards",
        "degrade_quality",
        "kill_largest_process",
        "force_gc"
    ]
    
    # 不同压力级别下的调度结果
    for pressure in [60, 80, 95]:
        print(f"\n压力级别: {pressure}%")
        scheduled = prioritizer.schedule_actions(test_actions, pressure)
        print(f"调度结果: {scheduled}")
        
        optimal = prioritizer.get_optimal_actions(test_actions, pressure, max_actions=3)
        print(f"最优动作: {optimal}")
        
        for action in optimal:
            weight, level = prioritizer.get_action_importance(action)

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

            print(f"  - {action}: 权重={weight}, 影响级别={level}") 