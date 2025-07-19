#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 熔断动作优先级调度器 - 简化演示
不依赖完整项目，可以独立运行以展示调度原理
"""

import time
import logging
import argparse
from enum import Enum
from typing import List, Dict, Any, Optional, Set

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("action_scheduler_demo")

# 熔断级别枚举
class FuseLevel(Enum):
    """熔断级别枚举"""
    NORMAL = 0      # 正常状态
    WARNING = 1     # 警告状态
    CRITICAL = 2    # 临界状态
    EMERGENCY = 3   # 紧急状态


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


class ActionEffectSimulator:
    """模拟不同熔断动作的效果"""
    
    def __init__(self):
        """初始化动作效果模拟器"""
        # 模拟内存使用率
        self.memory_usage = 85.0
        
        # 各动作的内存释放效果 (百分比减少)
        self.action_effects = {
            'clear_temp_files': 2.0,
            'reduce_log_verbosity': 1.0,
            'flush_memory_cache': 3.0,
            'reduce_cache_size': 2.5,
            'unload_noncritical_shards': 5.0,
            'pause_background_tasks': 3.0,
            'degrade_quality': 4.0,
            'switch_to_lightweight_models': 6.0,
            'disable_features': 7.0,
            'kill_largest_process': 15.0,
            'force_gc': 8.0,
            'activate_survival_mode': 20.0
        }
        
        # 各动作的执行时间 (秒)
        self.action_durations = {
            'clear_temp_files': 1.5,
            'reduce_log_verbosity': 0.5,
            'flush_memory_cache': 0.8,
            'reduce_cache_size': 1.0,
            'unload_noncritical_shards': 2.0,
            'pause_background_tasks': 1.0,
            'degrade_quality': 1.2,
            'switch_to_lightweight_models': 3.0,
            'disable_features': 1.5,
            'kill_largest_process': 2.5,
            'force_gc': 2.0,
            'activate_survival_mode': 4.0
        }
        
        # 各动作的用户体验影响 (1-10，越高表示影响越大)
        self.action_ux_impact = {
            'clear_temp_files': 1,
            'reduce_log_verbosity': 1,
            'flush_memory_cache': 2,
            'reduce_cache_size': 2,
            'unload_noncritical_shards': 4,
            'pause_background_tasks': 3,
            'degrade_quality': 6,
            'switch_to_lightweight_models': 5,
            'disable_features': 7,
            'kill_largest_process': 9,
            'force_gc': 4,
            'activate_survival_mode': 10
        }
        
        # 执行历史
        self.history = []
    
    def simulate_action(self, action: str) -> Dict[str, Any]:
        """
        模拟执行一个动作
        
        Args:
            action: 动作名称
            
        Returns:
            动作结果字典
        """
        # 获取动作效果
        memory_decrease = self.action_effects.get(action, 1.0)
        duration = self.action_durations.get(action, 1.0)
        ux_impact = self.action_ux_impact.get(action, 5)
        
        # 等待模拟执行时间
        time.sleep(max(0.1, duration / 10))  # 加速模拟
        
        # 减少内存使用率
        old_memory = self.memory_usage
        self.memory_usage = max(50.0, self.memory_usage - memory_decrease)
        
        # 记录结果
        result = {
            'action': action,
            'time': time.time(),
            'duration': duration,
            'memory_before': old_memory,
            'memory_after': self.memory_usage,
            'memory_saved': old_memory - self.memory_usage,
            'ux_impact': ux_impact
        }
        
        self.history.append(result)
        print(f"执行动作: {action}, 释放内存: {result['memory_saved']:.1f}%, 当前内存: {self.memory_usage:.1f}%")
        
        return result
    
    def reset(self, initial_memory: float = 85.0) -> None:
        """
        重置模拟器
        
        Args:
            initial_memory: 初始内存使用率
        """
        self.memory_usage = initial_memory
        self.history = []


def run_demo():
    """运行简化演示"""
    print("======= VisionAI-ClipsMaster 熔断动作优先级调度器 - 简化演示 =======")
    
    # 创建调度器和模拟器
    prioritizer = ActionPrioritizer()
    simulator = ActionEffectSimulator()
    
    # 测试动作集
    test_actions = [
        "clear_temp_files",
        "reduce_log_verbosity",
        "unload_noncritical_shards",
        "degrade_quality",
        "kill_largest_process",
        "force_gc"
    ]
    
    # 测试不同压力级别下的排序
    pressure_levels = [70, 85, 95]
    
    for pressure in pressure_levels:
        print(f"\n\n======= 压力级别: {pressure}% =======")
        simulator.reset(pressure)
        
        # 获取优先级排序
        scheduled_actions = prioritizer.schedule_actions(test_actions, pressure)
        print(f"排序结果: {scheduled_actions}")
        
        # 执行动作模拟
        print("\n执行模拟:")
        
        for action in scheduled_actions:
            simulator.simulate_action(action)
        
        # 打印总体结果
        total_memory_saved = pressure - simulator.memory_usage
        total_ux_impact = sum(entry['ux_impact'] for entry in simulator.history)
        
        print(f"\n总计释放内存: {total_memory_saved:.1f}%")
        print(f"总体用户体验影响: {total_ux_impact} (范围: 1-60)")
    
    # 对比测试
    pressure = 95
    print("\n\n======= 对比测试: 优化前 vs 优化后 (压力: 95%) =======")
    
    # 未优化版本 (固定顺序)
    print("\n未优化版本（固定顺序）:")
    simulator.reset(pressure)
    for action in test_actions:
        simulator.simulate_action(action)
    
    unoptimized_memory_saved = pressure - simulator.memory_usage
    unoptimized_ux_impact = sum(entry['ux_impact'] for entry in simulator.history)
    unoptimized_actions = [entry['action'] for entry in simulator.history]
    
    # 优化版本
    print("\n优化版本（按压力调度）:")
    simulator.reset(pressure)
    optimal_actions = prioritizer.schedule_actions(test_actions, pressure)
    for action in optimal_actions:
        simulator.simulate_action(action)
    
    optimized_memory_saved = pressure - simulator.memory_usage
    optimized_ux_impact = sum(entry['ux_impact'] for entry in simulator.history)
    optimized_actions = [entry['action'] for entry in simulator.history]
    
    # 打印对比结果
    print("\n======= 对比结果 =======")
    print(f"未优化执行顺序: {unoptimized_actions}")
    print(f"优化后执行顺序: {optimized_actions}")
    print(f"内存节省: {unoptimized_memory_saved:.1f}% vs {optimized_memory_saved:.1f}%")
    print(f"用户体验影响: {unoptimized_ux_impact} vs {optimized_ux_impact}")
    
    memory_improvement = ((optimized_memory_saved / unoptimized_memory_saved) - 1) * 100
    ux_improvement = ((unoptimized_ux_impact - optimized_ux_impact) / unoptimized_ux_impact) * 100
    
    print(f"内存节省改进: {memory_improvement:.1f}%")
    print(f"用户体验改进: {ux_improvement:.1f}%")


if __name__ == "__main__":
    run_demo() 