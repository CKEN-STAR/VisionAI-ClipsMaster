#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 熔断动作优先级调度器钩子
将动作优先级调度器集成到内存熔断管理系统中
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set

from src.memory.fuse_manager import get_fuse_manager, FuseLevel
from src.fuse.pressure_detector import get_pressure_detector
from src.fuse.action_scheduler import get_action_prioritizer

# 设置日志
logger = logging.getLogger("action_scheduler_hook")

class ActionSchedulerHook:
    """
    熔断动作优先级调度器钩子
    将动作优先级调度器集成到熔断管理系统中
    """
    
    def __init__(self):
        """初始化调度器钩子"""
        self._fuse_manager = get_fuse_manager()
        self._pressure_detector = get_pressure_detector()
        self._action_prioritizer = get_action_prioritizer()
        
        # 保存原始方法引用
        self._original_trigger_fuse = self._fuse_manager._trigger_fuse
        
        # 是否已安装钩子
        self._hooked = False
        
        # 调度统计信息
        self._scheduling_stats = {
            'scheduled_count': 0,        # 已调度动作总数
            'reordered_count': 0,        # 重排序动作次数
            'last_pressure': 0.0,        # 上次触发时的压力值
            'actions_by_level': {        # 各级别执行的动作统计
                FuseLevel.WARNING.name: set(),
                FuseLevel.CRITICAL.name: set(),
                FuseLevel.EMERGENCY.name: set()
            }
        }
        
        logger.info("熔断动作调度钩子初始化完成")
    
    def install(self) -> bool:
        """
        安装钩子，将调度器集成到熔断管理系统
        
        Returns:
            安装是否成功
        """
        if self._hooked:
            logger.warning("钩子已安装，跳过")
            return False
        
        try:
            # 替换熔断管理器的_trigger_fuse方法
            self._fuse_manager._trigger_fuse = self._trigger_fuse_hook
            self._hooked = True
            logger.info("动作调度钩子安装成功")
            return True
        except Exception as e:
            logger.error(f"安装动作调度钩子失败: {str(e)}")
            return False
    
    def uninstall(self) -> bool:
        """
        卸载钩子，恢复原始熔断行为
        
        Returns:
            卸载是否成功
        """
        if not self._hooked:
            logger.warning("钩子未安装，跳过")
            return False
        
        try:
            # 恢复原始方法
            self._fuse_manager._trigger_fuse = self._original_trigger_fuse
            self._hooked = False
            logger.info("动作调度钩子卸载成功")
            return True
        except Exception as e:
            logger.error(f"卸载动作调度钩子失败: {str(e)}")
            return False
    
    def _trigger_fuse_hook(self, level: FuseLevel, memory_percent: float) -> None:
        """
        触发熔断的自定义钩子
        
        Args:
            level: 熔断级别
            memory_percent: 内存使用百分比
        """
        logger.info(f"钩子拦截到{level.name}级别熔断触发，内存使用率: {memory_percent:.1f}%")
        
        # 获取当前压力指数
        current_pressure = self._pressure_detector.get_current_pressure()
        self._scheduling_stats['last_pressure'] = current_pressure
        
        # 更新状态
        self._fuse_manager.current_level = level
        self._fuse_manager.last_trigger_time[level] = time.time()
        
        # 获取对应级别的动作
        actions = []
        for level_config in self._fuse_manager.config["fuse_levels"]:
            if level_config["level"] == level.name:
                actions = level_config["actions"]
                break
        
        if not actions:
            logger.warning(f"未找到{level.name}级别对应的动作")
            return
        
        # 使用优先级调度器排序动作
        original_order = list(actions)
        scheduled_actions = self._action_prioritizer.schedule_actions(actions, current_pressure)
        
        # 检测是否发生了重排序
        is_reordered = original_order != scheduled_actions
        if is_reordered:
            self._scheduling_stats['reordered_count'] += 1
            logger.info(f"动作顺序已优化: {original_order} -> {scheduled_actions}")
        
        # 记录统计信息
        self._scheduling_stats['scheduled_count'] += len(scheduled_actions)
        for action in scheduled_actions:
            self._scheduling_stats['actions_by_level'][level.name].add(action)
        
        # 执行动作
        for action in scheduled_actions:
            if action not in self._fuse_manager.triggered_actions[level]:
                self._fuse_manager._execute_action(action, level)
                self._fuse_manager.triggered_actions[level].add(action)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取调度统计信息
        
        Returns:
            统计信息字典
        """
        # 计算动作级别分布
        action_importance = {}
        for level_name, actions in self._scheduling_stats['actions_by_level'].items():
            action_importance[level_name] = {}
            for action in actions:
                weight, importance = self._action_prioritizer.get_action_importance(action)
                if importance not in action_importance[level_name]:
                    action_importance[level_name][importance] = 0
                action_importance[level_name][importance] += 1
        
        return {
            'installed': self._hooked,
            'scheduled_count': self._scheduling_stats['scheduled_count'],
            'reordered_count': self._scheduling_stats['reordered_count'],
            'last_pressure': self._scheduling_stats['last_pressure'],
            'actions_by_level': {
                level: list(actions)
                for level, actions in self._scheduling_stats['actions_by_level'].items()
                if actions
            },
            'action_importance': action_importance
        }
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._scheduling_stats = {
            'scheduled_count': 0,
            'reordered_count': 0,
            'last_pressure': 0.0,
            'actions_by_level': {
                FuseLevel.WARNING.name: set(),
                FuseLevel.CRITICAL.name: set(),
                FuseLevel.EMERGENCY.name: set()
            }
        }
        logger.info("调度统计信息已重置")


# 全局单例
_scheduler_hook = None

def get_scheduler_hook() -> ActionSchedulerHook:
    """
    获取调度器钩子单例
    
    Returns:
        调度器钩子实例
    """
    global _scheduler_hook
    
    if _scheduler_hook is None:
        _scheduler_hook = ActionSchedulerHook()
        
    return _scheduler_hook


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import json
    
    # 测试调度器钩子
    hook = get_scheduler_hook()
    
    # 安装钩子
    print("安装调度器钩子...")
    success = hook.install()
    print(f"钩子安装{'成功' if success else '失败'}")
    
    # 初始状态
    print("\n初始统计信息:")
    stats = hook.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 模拟触发熔断
    print("\n模拟触发熔断...")
    fuse_manager = get_fuse_manager()
    fuse_manager.force_trigger("WARNING")
    time.sleep(1)
    fuse_manager.force_trigger("CRITICAL")
    time.sleep(1)
    fuse_manager.force_trigger("EMERGENCY")
    
    # 查看统计信息
    print("\n触发熔断后的统计信息:")
    stats = hook.get_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 卸载钩子
    print("\n卸载调度器钩子...")
    success = hook.uninstall()
    print(f"钩子卸载{'成功' if success else '失败'}") 