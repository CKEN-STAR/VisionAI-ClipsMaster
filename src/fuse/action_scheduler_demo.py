#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 熔断动作优先级调度器演示
展示如何使用动作优先级调度器来优化熔断动作执行顺序
"""

import os
import time
import logging
import argparse
import sys
import json
import threading
from typing import Dict, List, Any, Set

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入相关模块
from src.memory.fuse_manager import get_fuse_manager, FuseLevel
from src.fuse.pressure_detector import get_pressure_detector
from src.fuse.action_scheduler import get_action_prioritizer, ActionPrioritizer
from src.fuse.action_scheduler_hook import get_scheduler_hook
from src.fuse.integration import get_integration_manager

# 设置日志
logger = logging.getLogger("action_scheduler_demo")


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
        time.sleep(max(0.2, duration / 5))  # 加速模拟
        
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
        logger.info(f"执行动作: {action}, 释放内存: {result['memory_saved']:.1f}%, 当前内存: {self.memory_usage:.1f}%")
        
        return result
    
    def reset(self, initial_memory: float = 85.0) -> None:
        """
        重置模拟器
        
        Args:
            initial_memory: 初始内存使用率
        """
        self.memory_usage = initial_memory
        self.history = []


class DemoRunner:
    """演示运行器"""
    
    def __init__(self):
        """初始化演示运行器"""
        self.fuse_manager = get_fuse_manager()
        self.pressure_detector = get_pressure_detector()
        self.action_prioritizer = get_action_prioritizer()
        self.scheduler_hook = get_scheduler_hook()
        self.simulator = ActionEffectSimulator()
        
        # 注册自定义动作
        original_execute = self.fuse_manager._execute_action
        
        def custom_execute_action(action, level):
            """自定义动作执行函数，使用模拟器"""
            print(f"执行动作: {action} (级别: {level.name})")
            result = self.simulator.simulate_action(action)
            return True
        
        # 保存原函数
        self._original_execute = original_execute
        # 替换为自定义函数
        self.fuse_manager._execute_action = custom_execute_action
    
    def run_comparison(self, memory_pressure: float = 95.0) -> Dict[str, Any]:
        """
        运行对比演示，比较使用调度器与不使用调度器的效果
        
        Args:
            memory_pressure: 模拟的内存压力值
            
        Returns:
            对比结果
        """
        results = {
            'unoptimized': None,
            'optimized': None,
            'comparison': None
        }
        
        # 定义测试动作集
        test_actions = [
            "clear_temp_files",
            "reduce_log_verbosity",
            "unload_noncritical_shards",
            "degrade_quality",
            "kill_largest_process",
            "force_gc"
        ]
        
        # 运行未优化版本
        print("\n======= 运行未优化版本 =======")
        self.scheduler_hook.uninstall()
        self.simulator.reset(memory_pressure)
        start_time = time.time()
        
        for action in test_actions:
            self.fuse_manager._execute_action(action, FuseLevel.EMERGENCY)
        
        unoptimized_duration = time.time() - start_time
        unoptimized_final_memory = self.simulator.memory_usage
        unoptimized_history = self.simulator.history.copy()
        
        # 计算累计用户体验影响
        unoptimized_ux_impact = sum(entry['ux_impact'] for entry in unoptimized_history)
        
        # 保存结果
        results['unoptimized'] = {
            'duration': unoptimized_duration,
            'initial_memory': memory_pressure,
            'final_memory': unoptimized_final_memory,
            'memory_saved': memory_pressure - unoptimized_final_memory,
            'ux_impact': unoptimized_ux_impact,
            'actions': [entry['action'] for entry in unoptimized_history]
        }
        
        # 运行优化版本
        print("\n======= 运行优化版本 =======")
        self.scheduler_hook.install()
        self.simulator.reset(memory_pressure)
        start_time = time.time()
        
        # 使用优先级调度器对动作进行排序
        optimized_actions = self.action_prioritizer.schedule_actions(test_actions, memory_pressure)
        
        for action in optimized_actions:
            self.fuse_manager._execute_action(action, FuseLevel.EMERGENCY)
        
        optimized_duration = time.time() - start_time
        optimized_final_memory = self.simulator.memory_usage
        optimized_history = self.simulator.history.copy()
        
        # 计算累计用户体验影响
        optimized_ux_impact = sum(entry['ux_impact'] for entry in optimized_history)
        
        # 保存结果
        results['optimized'] = {
            'duration': optimized_duration,
            'initial_memory': memory_pressure,
            'final_memory': optimized_final_memory,
            'memory_saved': memory_pressure - optimized_final_memory,
            'ux_impact': optimized_ux_impact,
            'actions': [entry['action'] for entry in optimized_history]
        }
        
        # 计算对比
        memory_improvement = ((results['optimized']['memory_saved'] / results['unoptimized']['memory_saved']) - 1) * 100
        ux_improvement = ((results['unoptimized']['ux_impact'] - results['optimized']['ux_impact']) / results['unoptimized']['ux_impact']) * 100
        speed_improvement = ((results['unoptimized']['duration'] - results['optimized']['duration']) / results['unoptimized']['duration']) * 100
        
        results['comparison'] = {
            'memory_improvement_pct': memory_improvement,
            'ux_improvement_pct': ux_improvement,
            'speed_improvement_pct': speed_improvement,
            'reordered': results['unoptimized']['actions'] != results['optimized']['actions']
        }
        
        return results
    
    def run_pressure_demo(self, pressure_levels: List[float] = [70, 85, 98]) -> Dict[str, Any]:
        """
        演示不同压力级别下的动作优先级
        
        Args:
            pressure_levels: 要测试的压力级别列表
            
        Returns:
            不同压力级别的结果
        """
        results = {}
        
        # 定义测试动作集
        test_actions = [
            "clear_temp_files",
            "reduce_log_verbosity",
            "unload_noncritical_shards",
            "degrade_quality",
            "kill_largest_process",
            "force_gc"
        ]
        
        # 安装钩子
        self.scheduler_hook.install()
        
        # 测试每个压力级别
        for pressure in pressure_levels:
            print(f"\n======= 压力级别: {pressure}% =======")
            self.simulator.reset(pressure)
            
            # 获取最优动作
            optimal_actions = self.action_prioritizer.get_optimal_actions(test_actions, pressure)
            
            # 执行动作
            for action in optimal_actions:
                self.fuse_manager._execute_action(action, FuseLevel.EMERGENCY)
            
            # 保存结果
            results[str(pressure)] = {
                'pressure': pressure,
                'optimal_actions': optimal_actions,
                'final_memory': self.simulator.memory_usage,
                'memory_saved': pressure - self.simulator.memory_usage,
                'executed_actions': [entry['action'] for entry in self.simulator.history],
                'action_details': [{
                    'action': entry['action'],
                    'memory_saved': entry['memory_saved'],
                    'ux_impact': entry['ux_impact']
                } for entry in self.simulator.history]
            }
        
        return results
    
    def cleanup(self) -> None:
        """清理所有钩子"""
        # 恢复原始执行方法
        self.fuse_manager._execute_action = self._original_execute
        # 卸载调度钩子
        self.scheduler_hook.uninstall()
        logger.info("已清理所有钩子和自定义方法")


def run_demo(args):
    """
    运行演示
    
    Args:
        args: 命令行参数
    """
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化演示运行器
    runner = DemoRunner()
    
    try:
        # 如果指定了自定义权重
        if args.custom_weights:
            custom_weights = {}
            for weight_spec in args.custom_weights:
                parts = weight_spec.split(':')
                if len(parts) == 2:
                    action, weight = parts
                    try:
                        custom_weights[action] = float(weight)
                        print(f"自定义权重: {action} = {weight}")
                    except ValueError:
                        print(f"警告: 无效的权重值 '{weight}' for action '{action}'")
            
            # 更新动作优先级调度器的权重
            for action, weight in custom_weights.items():
                runner.action_prioritizer.register_custom_weight(action, weight)
        
        # 运行对比演示
        if args.compare:
            print("\n============ 运行优化对比演示 ============")
            comparison = runner.run_comparison(args.pressure)
            
            print("\n============ 对比结果 ============")
            print(f"未优化执行顺序: {comparison['unoptimized']['actions']}")
            print(f"优化后执行顺序: {comparison['optimized']['actions']}")
            print(f"内存节省改进: {comparison['comparison']['memory_improvement_pct']:.1f}%")
            print(f"用户体验改进: {comparison['comparison']['ux_improvement_pct']:.1f}%")
            print(f"速度改进: {comparison['comparison']['speed_improvement_pct']:.1f}%")
            
            if args.export:
                with open(args.export, 'w', encoding='utf-8') as f:
                    json.dump(comparison, f, indent=2, ensure_ascii=False)
                print(f"对比结果已保存到: {args.export}")
        
        # 运行压力级别演示
        if args.pressure_levels:
            print("\n============ 运行不同压力级别演示 ============")
            levels = [float(level) for level in args.pressure_levels.split(',')]
            pressure_results = runner.run_pressure_demo(levels)
            
            print("\n============ 压力级别结果 ============")
            for pressure, result in pressure_results.items():
                print(f"\n压力级别: {pressure}%")
                print(f"最优动作: {result['optimal_actions']}")
                print(f"内存节省: {result['memory_saved']:.1f}%")
                print(f"执行细节:")
                for detail in result['action_details']:
                    print(f"  - {detail['action']}: 释放 {detail['memory_saved']:.1f}%, 影响 {detail['ux_impact']}/10")
            
            if args.export:
                with open(args.export, 'w', encoding='utf-8') as f:
                    json.dump(pressure_results, f, indent=2, ensure_ascii=False)
                print(f"压力级别结果已保存到: {args.export}")
    finally:
        # 清理
        runner.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 熔断动作优先级调度器演示")
    
    parser.add_argument("--compare", action="store_true", help="运行优化对比演示")
    parser.add_argument("--pressure", type=float, default=95.0, help="模拟的内存压力值 (0-100)")
    parser.add_argument("--pressure-levels", type=str, help="要测试的压力级别列表，逗号分隔 (例如: 70,85,95)")
    parser.add_argument("--custom-weights", nargs="+", help="自定义动作权重，格式: 'action:weight'")
    parser.add_argument("--export", type=str, help="导出结果到JSON文件")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    
    args = parser.parse_args()
    
    # 如果没有提供任何运行模式，默认运行对比和压力级别演示
    if not (args.compare or args.pressure_levels):
        args.compare = True
        args.pressure_levels = "70,85,95"
    
    run_demo(args) 