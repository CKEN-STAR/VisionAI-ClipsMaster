#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化策略切换执行器
负责根据系统状态动态切换模型量化级别
"""

import os
import time
import threading
import importlib
from typing import Dict, Optional, List, Callable, Any, Tuple, Union
from loguru import logger

# 添加项目根目录到路径以解决导入问题
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.memory_guard import MemoryGuard, QuantizationManager
from src.utils.quant_config_loader import get_quant_config
from src.quant.quant_decision import QuantDecisionEngine
try:
    from src.memory.quant_logger import get_quant_logger, log_strategy_change
except ImportError:
    # 如果记录器未安装，提供空实现
    def get_quant_logger(): return None
    def log_strategy_change(old_quant, new_quant, context): return None


class QuantSwitcher:
    """量化策略切换执行器，实现模型量化级别的动态切换"""
    
    def __init__(self, 
                 memory_guard: Optional[MemoryGuard] = None,
                 decision_engine: Optional[QuantDecisionEngine] = None):
        """
        初始化量化级别切换器
        
        Args:
            memory_guard: 内存监控器实例，如未提供则创建新实例
            decision_engine: 量化决策引擎实例，如未提供则创建新实例
        """
        self.memory_guard = memory_guard or MemoryGuard()
        self.decision_engine = decision_engine or QuantDecisionEngine(self.memory_guard)
        self.quant_config = get_quant_config()
        
        # 当前量化级别
        self.current_quant = None
        
        # 模型加载和卸载回调函数
        self.load_callbacks: Dict[str, Callable] = {}
        self.unload_callbacks: Dict[str, Callable] = {}
        
        # 切换锁，确保并发安全
        self._switch_lock = threading.RLock()
        
        # 切换历史记录
        self.switch_history: List[Dict[str, Any]] = []
        self.max_history_len = 100
        
        # 切换性能评估数据
        self.switch_timing: Dict[str, Dict[str, float]] = {}
        
        # 当前活动模型
        self.active_model = None
        
        logger.info("量化切换管理器已初始化")
    
    def register_model(self, 
                      model_name: str, 
                      load_func: Optional[Callable] = None, 
                      unload_func: Optional[Callable] = None) -> 'QuantSwitcher':
        """
        注册模型和相关回调函数
        
        Args:
            model_name: 模型名称
            load_func: 加载模型的回调函数，参数为量化级别
            unload_func: 卸载模型的回调函数
            
        Returns:
            QuantSwitcher: 自身实例，支持链式调用
        """
        if load_func:
            self.load_callbacks[model_name] = load_func
            
        if unload_func:
            self.unload_callbacks[model_name] = unload_func
        
        logger.info(f"已注册模型 {model_name} 到量化切换器")
        return self
    
    def switch(self, new_quant: str) -> bool:
        """
        执行量化级别切换
        
        Args:
            new_quant: 新的量化级别，如 'Q4_K_M'
            
        Returns:
            bool: 切换是否成功
        """
        if self.current_quant == new_quant:
            logger.debug(f"当前已经是 {new_quant} 量化级别，无需切换")
            return True
        
        with self._switch_lock:
            switch_start = time.time()
            try:
                # 记录当前内存状态
                mem_before = self.memory_guard.get_memory_info()
                
                # 如果有活动模型，先卸载
                self._unload_model()
                
                # 加载新的量化模型
                success = self._load_quantized_model(new_quant)
                if not success:
                    logger.error(f"切换到量化级别 {new_quant} 失败")
                    
                    # 记录失败的切换事件
                    log_strategy_change(
                        self.current_quant, 
                        new_quant, 
                        {
                            'success': False,
                            'reason': 'load_failed',
                            'switch_time': time.time() - switch_start,
                            'memory_before': mem_before,
                            'model': self.active_model
                        }
                    )
                    return False
                
                # 更新当前量化级别
                old_quant = self.current_quant
                self.current_quant = new_quant
                
                # 记录切换后内存状态
                mem_after = self.memory_guard.get_memory_info()
                
                # 记录切换时间
                switch_duration = time.time() - switch_start
                
                # 记录此次切换历史
                self._record_switch(old_quant, new_quant, switch_duration, mem_before, mem_after)
                
                # 使用策略记录器记录切换事件
                log_strategy_change(
                    old_quant, 
                    new_quant, 
                    {
                        'switch_time': switch_duration,
                        'memory_before': mem_before,
                        'memory_after': mem_after,
                        'success': True,
                        'reason': 'manual_switch',
                        'model': self.active_model
                    }
                )
                
                logger.info(f"量化策略已切换至 {new_quant}")
                return True
                
            except Exception as e:
                logger.error(f"量化策略切换过程中发生错误: {str(e)}")
                # 记录错误事件
                log_strategy_change(
                    self.current_quant,
                    new_quant,
                    {
                        'success': False,
                        'reason': 'error',
                        'error_msg': str(e),
                        'switch_time': time.time() - switch_start,
                        'model': self.active_model
                    }
                )
                return False
    
    def auto_switch(self, model_name: Optional[str] = None) -> bool:
        """
        根据系统状态自动切换到最佳量化级别
        
        Args:
            model_name: 可选的模型名称，用于获取模型特定的量化建议
            
        Returns:
            bool: 切换是否成功
        """
        try:
            # 获取内存状态
            mem_info = self.memory_guard.get_memory_info()
            available_mb = mem_info['available'] / (1024 * 1024)
            
            # 确定最佳量化级别
            if model_name:
                # 获取模型特定的配置
                params = self.decision_engine.select_model_specific_quant(model_name, available_mb)
                recommended_level = params['level']
                self.active_model = model_name
            else:
                # 获取通用推荐
                recommended_level = self.decision_engine.select_quant_level(available_mb)
            
            # 检查是否与当前级别相同
            if recommended_level == self.current_quant:
                logger.debug(f"自动选择的级别 {recommended_level} 与当前级别相同，无需切换")
                return True
                
            # 记录自动切换事件上下文
            context = {
                'reason': 'auto_select',
                'available_memory': available_mb,
                'model': model_name or self.active_model
            }
            
            # 执行切换
            success = self.switch(recommended_level)
            
            # 如果切换成功，更新记录上下文
            if success:
                mem_after = self.memory_guard.get_memory_info()
                available_after = mem_after['available'] / (1024 * 1024)
                context.update({
                    'memory_freed': available_after - available_mb
                })
                
                # 更新记录（切换已经记录了基本事件，这里添加额外信息）
                log_strategy_change(
                    self.current_quant,
                    recommended_level,
                    context
                )
                
            return success
            
        except Exception as e:
            logger.error(f"自动量化级别切换失败: {str(e)}")
            return False
    
    def get_level_difference(self, level1: str, level2: str) -> Dict[str, Any]:
        """
        比较两个量化级别的差异
        
        Args:
            level1: 第一个量化级别
            level2: 第二个量化级别
            
        Returns:
            Dict: 差异比较结果
        """
        level1_info = self.quant_config.get_level_info(level1) or {}
        level2_info = self.quant_config.get_level_info(level2) or {}
        
        # 比较质量差异
        quality_diff = level1_info.get('quality_score', 0) - level2_info.get('quality_score', 0)
        
        # 比较内存差异
        memory_diff = level1_info.get('memory_usage', 0) - level2_info.get('memory_usage', 0)
        
        # 比较性能差异
        performance_diff = level1_info.get('token_speed', 0) - level2_info.get('token_speed', 0)
        
        # 计算综合评分(质量提升与内存增加的比值)
        if memory_diff > 0 and quality_diff > 0:
            efficiency = quality_diff / memory_diff
        else:
            efficiency = 0
        
        # 获取当前可用内存(MB)
        mem_info = self.memory_guard.get_memory_info()
        available_memory_mb = mem_info['available'] / (1024 * 1024)
        
        return {
            'quality_diff': quality_diff,
            'memory_diff': memory_diff,
            'performance_diff': performance_diff,
            'efficiency': efficiency,
            'from_level': level1,
            'to_level': level2,
            'recommendation': level1 if quality_diff > 0 and memory_diff < available_memory_mb else level2
        }
    
    def get_switch_history(self) -> List[Dict[str, Any]]:
        """获取切换历史记录"""
        return self.switch_history
    
    def get_average_switch_time(self, from_level: Optional[str] = None, to_level: Optional[str] = None) -> float:
        """
        获取平均切换时间
        
        Args:
            from_level: 起始量化级别
            to_level: 目标量化级别
            
        Returns:
            float: 平均切换时间(秒)
        """
        if from_level and to_level:
            # 获取特定切换路径的平均时间
            key = f"{from_level}_to_{to_level}"
            if key in self.switch_timing and 'count' in self.switch_timing[key]:
                count = self.switch_timing[key]['count']
                total_time = self.switch_timing[key]['total_time']
                return total_time / count if count > 0 else 0
            return 0
        
        # 获取所有切换的平均时间
        total_count = 0
        total_time = 0
        
        for key, timing in self.switch_timing.items():
            total_count += timing.get('count', 0)
            total_time += timing.get('total_time', 0)
        
        return total_time / total_count if total_count > 0 else 0
    
    def get_current_level(self) -> Optional[str]:
        """获取当前量化级别"""
        return self.current_quant
    
    def get_available_levels(self) -> List[str]:
        """获取所有可用的量化级别"""
        return self.quant_config.get_quant_level_names()
    
    def evaluate_and_switch(self, target_level: str) -> Dict[str, Any]:
        """
        评估并切换量化级别，包含切换前后的效果评估
        
        Args:
            target_level: 目标量化级别
            
        Returns:
            Dict: 包含切换结果和评估信息的字典
        """
        # 记录当前级别和内存使用情况
        current_level = self.current_quant
        mem_before = self.memory_guard.get_memory_info()
        
        # 如果没有当前级别(首次加载)，则无法进行比较评估
        if not current_level:
            success = self.switch(target_level)
            
            # 记录首次加载事件
            log_strategy_change(
                None,
                target_level,
                {
                    'reason': 'first_load',
                    'success': success,
                    'model': self.active_model
                }
            )
            
            return {
                'success': success,
                'from_level': None,
                'to_level': target_level,
                'evaluation': None,
                'first_load': True
            }
        
        # 构建量化前数据
        before_quant = {
            'mem': mem_before['used'] / (1024 * 1024),  # 转换为MB
            'quant_level': current_level
        }
        
        # 执行切换
        switch_start = time.time()
        success = self.switch(target_level)
        switch_time = time.time() - switch_start
        
        # 记录切换后内存
        mem_after = self.memory_guard.get_memory_info()
        
        # 构建量化后数据
        after_quant = {
            'mem': mem_after['used'] / (1024 * 1024),  # 转换为MB
            'quant_level': target_level
        }
        
        # 评估效果
        evaluation = None
        try:
            # 动态导入评估器以避免循环导入
            from src.memory.quant_evaluator import get_quant_evaluator
            evaluator = get_quant_evaluator()
            evaluation = evaluator.evaluate(before_quant, after_quant)
            
            # 记录评估事件
            try:
                from src.memory.quant_logger import log_evaluation_result
                log_evaluation_result(
                    evaluation,
                    {
                        'from_level': current_level,
                        'to_level': target_level,
                        'switch_time': switch_time,
                        'memory_before': mem_before,
                        'memory_after': mem_after,
                        'model': self.active_model
                    }
                )
            except ImportError:
                pass
            
        except Exception as e:
            logger.error(f"评估量化效果时出错: {str(e)}")
        
        return {
            'success': success,
            'from_level': current_level,
            'to_level': target_level,
            'evaluation': evaluation,
            'first_load': False,
            'memory_before': mem_before,
            'memory_after': mem_after,
            'switch_time': switch_time
        }
        
    def find_optimal_level_with_evaluation(self, min_score: float = 50.0) -> str:
        """
        找到具有最佳评估分数的量化级别
        
        Args:
            min_score: 最低可接受分数
            
        Returns:
            str: 最佳量化级别
        """
        try:
            # 动态导入评估器以避免循环导入
            from src.memory.quant_evaluator import get_quant_evaluator
            evaluator = get_quant_evaluator()
            
            # 获取当前可用内存
            mem_info = self.memory_guard.get_memory_info()
            available_mb = mem_info['available'] / (1024 * 1024)
            
            # 获取最佳量化级别
            best_level = evaluator.get_best_quant_level(available_mb)
            
            # 评估该级别
            evaluation = evaluator.evaluate_quantization_level(best_level)
            
            # 如果评分不满足最低要求，尝试找到其他可能的选择
            if evaluation.get('score', 0) < min_score:
                # 评估所有级别
                all_evaluations = evaluator.evaluate_all_levels()
                
                # 筛选符合内存限制且评分满足要求的级别
                valid_levels = []
                for level, data in all_evaluations.items():
                    if data.get('memory_usage', 0) <= available_mb and data.get('score', 0) >= min_score:
                        valid_levels.append((level, data.get('score', 0)))
                
                if valid_levels:
                    # 按评分排序
                    valid_levels.sort(key=lambda x: x[1], reverse=True)
                    best_level = valid_levels[0][0]
            
            return best_level
            
        except Exception as e:
            logger.error(f"获取最佳量化级别时出错: {str(e)}")
            # 出错时回退到决策引擎
            return self.decision_engine.select_quant_level()
    
    def _unload_model(self) -> bool:
        """卸载当前活动模型"""
        if not self.active_model or self.active_model not in self.unload_callbacks:
            return True
        
        try:
            # 执行卸载回调
            self.unload_callbacks[self.active_model]()
            logger.info(f"模型 {self.active_model} 已卸载")
            return True
            
        except Exception as e:
            logger.error(f"卸载模型 {self.active_model} 时发生错误: {str(e)}")
            return False
    
    def _load_quantized_model(self, quant_level: str) -> bool:
        """
        加载指定量化级别的模型
        
        Args:
            quant_level: 量化级别
            
        Returns:
            bool: 加载是否成功
        """
        if not self.active_model or self.active_model not in self.load_callbacks:
            logger.warning(f"没有有效的模型加载回调函数")
            return False
        
        try:
            # 执行加载回调，传入量化级别
            result = self.load_callbacks[self.active_model](quant_level)
            
            if result:
                logger.info(f"已加载 {quant_level} 级别的模型 {self.active_model}")
                return True
            else:
                logger.error(f"加载 {quant_level} 级别的模型 {self.active_model} 失败")
                return False
            
        except Exception as e:
            logger.error(f"加载 {quant_level} 级别的模型 {self.active_model} 时发生错误: {str(e)}")
            return False
    
    def _record_switch(self, 
                     from_level: Optional[str], 
                     to_level: str, 
                     duration: float,
                     mem_before: Dict[str, Any],
                     mem_after: Dict[str, Any]) -> None:
        """
        记录量化级别切换历史
        
        Args:
            from_level: 切换前的量化级别
            to_level: 切换后的量化级别
            duration: 切换耗时(秒)
            mem_before: 切换前的内存状态
            mem_after: 切换后的内存状态
        """
        # 记录切换历史
        switch_record = {
            'timestamp': time.time(),
            'from_level': from_level,
            'to_level': to_level,
            'duration': duration,
            'memory_before': mem_before.get('percent', 0) * 100,  # 转为百分比
            'memory_after': mem_after.get('percent', 0) * 100,  # 转为百分比
            'memory_change': (mem_after.get('used', 0) - mem_before.get('used', 0)) / (1024 * 1024)  # MB
        }
        
        self.switch_history.append(switch_record)
        
        # 限制历史记录长度
        if len(self.switch_history) > self.max_history_len:
            self.switch_history.pop(0)
        
        # 更新切换时间统计
        key = f"{from_level or 'None'}_to_{to_level}"
        if key not in self.switch_timing:
            self.switch_timing[key] = {'count': 0, 'total_time': 0}
        
        self.switch_timing[key]['count'] += 1
        self.switch_timing[key]['total_time'] += duration


# 支持的模型加载和卸载实现示例
def load_model_with_level(model_name: str, quant_level: str) -> bool:
    """
    加载指定量化级别的模型实现示例
    
    Args:
        model_name: 模型名称
        quant_level: 量化级别
        
    Returns:
        bool: 加载是否成功
    """
    logger.info(f"[示例] 加载模型 {model_name}，量化级别 {quant_level}")
    # 这里是实际加载模型的代码
    # ...
    return True


def unload_model(model_name: str) -> bool:
    """
    卸载模型实现示例
    
    Args:
        model_name: 模型名称
        
    Returns:
        bool: 卸载是否成功
    """
    logger.info(f"[示例] 卸载模型 {model_name}")
    # 这里是实际卸载模型的代码
    # ...
    return True


# 简单使用示例
if __name__ == "__main__":
    # 创建量化切换器实例
    switcher = QuantSwitcher()
    
    # 注册模型加载和卸载回调
    model_name = "qwen2.5-7b-zh"
    switcher.register_model(
        model_name=model_name,
        load_func=lambda level: load_model_with_level(model_name, level),
        unload_func=lambda: unload_model(model_name)
    )
    
    # 设置当前活动模型
    switcher.active_model = model_name
    
    # 测试切换
    print("\n量化级别切换测试:")
    print("=" * 60)
    print(f"{'切换路径':20} | {'耗时(秒)':10} | {'结果':10}")
    print("-" * 60)
    
    # 测试不同的量化级别切换
    switcher.switch("Q4_K_M")  # 初始化到Q4_K_M
    for level in ["Q2_K", "Q3_K_M", "Q5_K_M", "Q6_K"]:
        start_time = time.time()
        success = switcher.switch(level)
        duration = time.time() - start_time
        
        print(f"Q4_K_M -> {level:10} | {duration:.6f} | {'成功' if success else '失败'}")
    
    # 测试自动切换
    print("\n自动量化级别切换测试:")
    print("=" * 60)
    success = switcher.auto_switch()
    current = switcher.get_current_level()
    print(f"自动选择的量化级别: {current}")
    
    # 查看切换历史
    print("\n切换历史记录:")
    print("=" * 60)
    history = switcher.get_switch_history()
    for i, record in enumerate(history[-5:], 1):  # 显示最近5条记录
        print(f"{i}. {record['from_level'] or 'None'} -> {record['to_level']} "
              f"(耗时: {record['duration']:.6f}秒, 内存变化: {record['memory_change']:.2f}MB)") 