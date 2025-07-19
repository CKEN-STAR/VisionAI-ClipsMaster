#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全降级协议模块

负责在内存紧急情况下执行安全降级措施，保证系统稳定性，
包括状态保存、资源释放、切换到低内存量化级别等。
"""

import os
import sys
import time
import gc
import threading
import psutil
import traceback
import uuid
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union
from loguru import logger

# 添加项目根目录到路径以解决导入问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.memory_guard import MemoryGuard
from src.quant.quant_switcher import QuantSwitcher
from src.utils.quant_config_loader import get_quant_config
from src.memory.quant_evaluator import get_quant_evaluator
try:
    from src.memory.quant_logger import get_quant_logger, log_fallback_event
except ImportError:
    # 如果记录器未安装，提供空实现
    def get_quant_logger(): return None
    def log_fallback_event(from_level, to_level, emergency_level, context=None): return None

# 引入熔断效果验证系统
try:
    from src.fuse.effect_validator import (

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

        get_validator, 
        handle_failed_validation, 
        FailureHandlingStrategy
    )
    _validator_available = True
except ImportError:
    _validator_available = False


class EmergencyLevel(Enum):
    """紧急程度枚举"""
    NORMAL = 0       # 正常状态
    WARNING = 1      # 警告状态，接近临界值
    CRITICAL = 2     # 临界状态，需要立即干预
    EMERGENCY = 3    # 紧急状态，需要激活紧急措施
    FATAL = 4        # 致命状态，无法恢复


class FallbackProtocol:
    """安全降级协议管理器"""
    
    def __init__(
        self,
        memory_guard: Optional[MemoryGuard] = None,
        quant_switcher: Optional[QuantSwitcher] = None,
        warning_threshold: float = 0.85,      # 警告阈值
        critical_threshold: float = 0.92,     # 临界阈值
        emergency_threshold: float = 0.98,    # 紧急阈值
        auto_activate: bool = True,           # 自动激活
        emergency_quant_level: str = "Q2_K",  # 紧急情况使用的量化级别
        check_interval: float = 1.0,          # 检查间隔(秒)
    ):
        """
        初始化安全降级协议管理器
        
        Args:
            memory_guard: 内存监控器，如未提供将创建新实例
            quant_switcher: 量化切换器，如未提供将创建新实例
            warning_threshold: 内存使用率警告阈值
            critical_threshold: 内存使用率临界阈值
            emergency_threshold: 内存使用率紧急阈值
            auto_activate: 是否自动激活协议
            emergency_quant_level: 紧急情况切换的量化级别
            check_interval: 自动检测的时间间隔(秒)
        """
        # 初始化组件
        self.memory_guard = memory_guard or MemoryGuard()
        self.quant_switcher = quant_switcher or QuantSwitcher(memory_guard=self.memory_guard)
        self.quant_config = get_quant_config()
        
        # 设置阈值
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.emergency_threshold = emergency_threshold
        
        # 紧急量化级别
        self.emergency_quant_level = emergency_quant_level
        
        # 回调和处理器
        self.custom_handlers: Dict[EmergencyLevel, List[Callable]] = {
            level: [] for level in EmergencyLevel
        }
        
        # 正在执行的降级操作
        self._active_protocols: Dict[EmergencyLevel, bool] = {
            level: False for level in EmergencyLevel
        }
        
        # 保存的处理状态
        self.saved_states: Dict[str, Any] = {}
        self.state_timestamp: float = 0
        
        # 监控线程
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        self.check_interval = check_interval
        
        # 降级历史记录
        self.protocol_history: List[Dict[str, Any]] = []
        self.max_history_len = 50
        
        # 设置状态锁，确保并发安全
        self._protocol_lock = threading.RLock()
        
        # 自动启动监控
        if auto_activate:
            self.start_monitoring()
        
        logger.info("安全降级协议管理器已初始化")
    
    def start_monitoring(self) -> bool:
        """启动监控线程"""
        try:
            if self._monitor_thread is None or not self._monitor_thread.is_alive():
                self._stop_monitor.clear()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_system_state,
                    daemon=True
                )
                self._monitor_thread.start()
                logger.info("安全降级协议监控已启动")
                return True
            return False
        except Exception as e:
            logger.error(f"启动安全降级协议监控失败: {str(e)}")
            return False
    
    def stop_monitoring(self) -> bool:
        """停止监控线程"""
        try:
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._stop_monitor.set()
                self._monitor_thread.join(timeout=5.0)
                logger.info("安全降级协议监控已停止")
                return True
            return False
        except Exception as e:
            logger.error(f"停止安全降级协议监控失败: {str(e)}")
            return False
    
    def register_handler(self, level: EmergencyLevel, handler_func: Callable) -> 'FallbackProtocol':
        """
        注册处理函数
        
        Args:
            level: 紧急级别
            handler_func: 处理函数
            
        Returns:
            FallbackProtocol: 自身实例，支持链式调用
        """
        self.custom_handlers[level].append(handler_func)
        logger.info(f"已为{level.name}级别注册处理函数: {handler_func.__name__}")
        return self
    
    def emergency_fallback(self) -> bool:
        """
        执行紧急降级操作，最高优先级降级
        
        Returns:
            bool: 操作是否成功
        """
        logger.warning("触发紧急降级协议!")
        
        with self._protocol_lock:
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 保存处理状态
                self._save_processing_state()
                
                # 获取量化评估器
                evaluator = get_quant_evaluator()
                
                # 获取当前量化级别
                old_level = self.quant_switcher.get_current_level()
                
                # 使用评估器找到内存压力下最有效的量化级别
                # 优先考虑内存节省，评分阈值可以降低
                mem_info = self.memory_guard.get_memory_info()
                available_mb = mem_info['available'] / (1024 * 1024)
                
                # 由于是紧急情况，我们需要最大限度节省内存，因此使用紧急级别
                target_level = self.emergency_quant_level
                
                logger.debug(f"当前量化级别: {old_level}, 切换到紧急级别: {target_level}")
                
                # 评估并切换
                switch_result = self.quant_switcher.evaluate_and_switch(target_level)
                success = switch_result['success']
                
                # 如果有评估结果，记录
                evaluation = None
                if switch_result.get('evaluation'):
                    eval_result = switch_result['evaluation']
                    evaluation = eval_result
                    logger.info(f"紧急降级效果评估: 内存节省 {eval_result.get('mem_saved', 0):.1f}MB, " 
                               f"质量下降 {eval_result.get('quality_drop', 0):.2f}, "
                               f"评分 {eval_result.get('score', 0):.1f}")
                
                # 记录紧急降级事件
                fallback_context = {
                    'elapsed': time.time() - start_time,
                    'available_mb': available_mb,
                    'evaluation': evaluation,
                    'success': success,
                    'memory_before': mem_info,
                    'memory_after': self.memory_guard.get_memory_info() if success else None,
                    'model': self.quant_switcher.active_model
                }
                
                log_fallback_event(
                    old_level,
                    target_level,
                    'EMERGENCY',
                    fallback_context
                )
                
                if not success:
                    # 如果切换失败，可能是因为资源不足，强制释放非关键资源
                    logger.warning("切换量化级别失败，尝试强制释放资源")
                    self._release_noncritical_resources()
                    
                    # 再次尝试切换
                    success = self.quant_switcher.switch(target_level)
                    
                    # 更新记录
                    fallback_context.update({
                        'success': success,
                        'retry': True,
                        'memory_after': self.memory_guard.get_memory_info() if success else None
                    })
                    
                    log_fallback_event(
                        old_level,
                        target_level,
                        'EMERGENCY_RETRY',
                        fallback_context
                    )
                
                # 记录协议执行
                self._record_protocol_execution(
                    level=EmergencyLevel.EMERGENCY,
                    duration=time.time() - start_time,
                    details={
                        'old_level': old_level,
                        'new_level': target_level,
                        'success': success,
                        'evaluation': switch_result.get('evaluation')
                    }
                )
                
                # 执行自定义处理器
                self._run_custom_handlers(EmergencyLevel.EMERGENCY)
                
                logger.info(f"紧急降级协议执行{'成功' if success else '失败'}")
                return success
                
            except Exception as e:
                logger.error(f"执行紧急降级协议时发生错误: {str(e)}")
                traceback.print_exc()
                return False
    
    def critical_fallback(self) -> bool:
        """
        执行临界降级操作
        
        Returns:
            bool: 操作是否成功
        """
        logger.warning("触发临界降级协议!")
        
        with self._protocol_lock:
            # 标记临界协议激活
            self._active_protocols[EmergencyLevel.CRITICAL] = True
            
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 获取量化评估器
                evaluator = get_quant_evaluator()
                
                # 1. 尝试降低模型量化级别
                old_level = self.quant_switcher.get_current_level()
                
                # 使用量化评估器获取最佳量化级别
                # 内存限制设为当前可用内存的90%，确保有足够安全余量
                mem_info = self.memory_guard.get_memory_info()
                memory_limit_mb = mem_info['available'] / (1024 * 1024) * 0.9
                
                # 获取当前推荐的量化级别
                target_level = evaluator.get_best_quant_level(memory_limit_mb)
                
                # 记录临界降级初始状态
                fallback_context = {
                    'available_mb': memory_limit_mb,
                    'memory_info': mem_info,
                    'model': self.quant_switcher.active_model
                }
                
                # 仅当找到的级别与当前级别不同且内存需求更低时才切换
                switch_result = None
                if target_level != old_level:
                    current_mem = self.quant_config.get_memory_requirement(old_level or "")
                    target_mem = self.quant_config.get_memory_requirement(target_level)
                    
                    if target_mem < current_mem:
                        logger.info(f"临界降级: 从 {old_level} 切换到 {target_level}")
                        
                        # 评估并切换
                        switch_result = self.quant_switcher.evaluate_and_switch(target_level)
                        
                        # 更新上下文
                        fallback_context.update({
                            'switch_result': switch_result,
                            'elapsed': time.time() - start_time,
                            'success': switch_result.get('success', False)
                        })
                        
                        # 如果有评估结果，记录
                        if switch_result.get('evaluation'):
                            eval_result = switch_result['evaluation']
                            logger.info(f"临界降级效果评估: 内存节省 {eval_result.get('mem_saved', 0):.1f}MB, " 
                                       f"质量下降 {eval_result.get('quality_drop', 0):.2f}, "
                                       f"评分 {eval_result.get('score', 0):.1f}")
                            
                            fallback_context.update({
                                'evaluation': eval_result
                            })
                else:
                    # 记录无需切换
                    fallback_context.update({
                        'no_switch_needed': True,
                        'reason': 'current_level_optimal' if target_level == old_level else 'insufficient_memory_difference'
                    })
                
                # 记录临界降级事件
                log_fallback_event(
                    old_level,
                    target_level if target_level != old_level else old_level,
                    'CRITICAL',
                    fallback_context
                )
                
                # 2. 释放部分非关键资源
                logger.info("临界降级: 释放部分非关键资源")
                self._release_noncritical_resources(partial=True)
                
                # 更新内存状态
                mem_after = self.memory_guard.get_memory_info()
                fallback_context.update({
                    'memory_after': mem_after,
                    'memory_freed': (mem_after.get('available', 0) - mem_info.get('available', 0)) / (1024 * 1024)
                })
                
                # 记录非关键资源释放事件
                log_fallback_event(
                    old_level,
                    target_level if switch_result and switch_result.get('success', False) else old_level,
                    'CRITICAL_RESOURCE_RELEASE',
                    {
                        'memory_before': mem_info,
                        'memory_after': mem_after,
                        'elapsed': time.time() - start_time
                    }
                )
                
                # 记录协议执行
                self._record_protocol_execution(
                    level=EmergencyLevel.CRITICAL,
                    duration=time.time() - start_time,
                    details={
                        'old_level': old_level,
                        'new_level': target_level,
                        'evaluation': switch_result.get('evaluation') if switch_result else None
                    }
                )
                
                # 执行自定义处理器
                self._run_custom_handlers(EmergencyLevel.CRITICAL)
                
                logger.info("临界降级协议执行完成")
                return True
                
            except Exception as e:
                logger.error(f"执行临界降级协议时发生错误: {str(e)}")
                
                # 记录错误事件
                log_fallback_event(
                    self.quant_switcher.get_current_level(),
                    "unknown",
                    'CRITICAL_ERROR',
                    {
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                )
                
                return False
            finally:
                # 标记临界协议完成
                self._active_protocols[EmergencyLevel.CRITICAL] = False
    
    def warning_fallback(self) -> bool:
        """
        执行警告降级操作
        
        Returns:
            bool: 操作是否成功
        """
        logger.info("触发警告降级协议")
        
        # 标记警告协议激活
        self._active_protocols[EmergencyLevel.WARNING] = True
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 获取量化评估器
            evaluator = get_quant_evaluator()
            
            # 1. 检查是否需要降低量化级别
            mem_info = self.memory_guard.get_memory_info()
            available_mb = mem_info['available'] / (1024 * 1024)
            
            # 使用评估器寻找性能和内存平衡点
            # 警告阶段需要更高的评分要求，确保性能不会大幅下降
            best_level = self.quant_switcher.find_optimal_level_with_evaluation(min_score=60.0)
            current_level = self.quant_switcher.get_current_level()
            
            # 记录警告降级初始状态
            fallback_context = {
                'available_mb': available_mb,
                'memory_info': mem_info,
                'model': self.quant_switcher.active_model,
                'recommended_level': best_level,
                'current_level': current_level
            }
            
            # 如果推荐级别与当前级别不同，且内存需求更低，切换到推荐级别
            switch_result = None
            if best_level != current_level:
                current_mem = self.quant_config.get_memory_requirement(current_level or "")
                recommended_mem = self.quant_config.get_memory_requirement(best_level)
                
                if recommended_mem < current_mem:
                    logger.info(f"警告降级: 从 {current_level} 切换到 {best_level}")
                    
                    # 评估并切换
                    switch_result = self.quant_switcher.evaluate_and_switch(best_level)
                    
                    # 更新上下文
                    fallback_context.update({
                        'switch_result': switch_result,
                        'elapsed': time.time() - start_time,
                        'success': switch_result.get('success', False)
                    })
                    
                    # 如果有评估结果，记录
                    if switch_result.get('evaluation'):
                        eval_result = switch_result['evaluation']
                        logger.info(f"警告降级效果评估: 内存节省 {eval_result.get('mem_saved', 0):.1f}MB, " 
                                   f"质量下降 {eval_result.get('quality_drop', 0):.2f}, "
                                   f"评分 {eval_result.get('score', 0):.1f}")
                        
                        fallback_context.update({
                            'evaluation': eval_result
                        })
                else:
                    # 记录无需切换原因
                    fallback_context.update({
                        'no_switch_needed': True,
                        'reason': 'insufficient_memory_difference',
                        'current_mem': current_mem,
                        'recommended_mem': recommended_mem
                    })
            else:
                # 记录无需切换
                fallback_context.update({
                    'no_switch_needed': True,
                    'reason': 'current_level_optimal'
                })
            
            # 记录警告降级事件
            log_fallback_event(
                current_level,
                best_level if best_level != current_level and switch_result and switch_result.get('success', False) else current_level,
                'WARNING',
                fallback_context
            )
            
            # 2. 主动进行垃圾回收
            gc_start = time.time()
            collected = gc.collect()
            gc_time = time.time() - gc_start
            
            # 更新内存状态
            mem_after = self.memory_guard.get_memory_info()
            fallback_context.update({
                'memory_after': mem_after,
                'memory_freed': (mem_after.get('available', 0) - mem_info.get('available', 0)) / (1024 * 1024),
                'gc_collected': collected,
                'gc_time': gc_time
            })
            
            # 记录GC事件
            log_fallback_event(
                current_level,
                best_level if switch_result and switch_result.get('success', False) else current_level,
                'WARNING_GC',
                {
                    'gc_collected': collected,
                    'gc_time': gc_time,
                    'memory_before': mem_info,
                    'memory_after': mem_after
                }
            )
            
            # 记录协议执行
            self._record_protocol_execution(
                level=EmergencyLevel.WARNING,
                duration=time.time() - start_time,
                details={
                    'available_mb': available_mb,
                    'recommended_level': best_level,
                    'current_level': current_level,
                    'evaluation': switch_result.get('evaluation') if switch_result else None,
                    'gc_collected': collected
                }
            )
            
            # 执行自定义处理器
            self._run_custom_handlers(EmergencyLevel.WARNING)
            
            logger.info("警告降级协议执行完成")
            return True
            
        except Exception as e:
            logger.error(f"执行警告降级协议时发生错误: {str(e)}")
            
            # 记录错误事件
            log_fallback_event(
                self.quant_switcher.get_current_level(),
                "unknown",
                'WARNING_ERROR',
                {
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }
            )
            
            return False
        finally:
            # 标记警告协议完成
            self._active_protocols[EmergencyLevel.WARNING] = False
    
    def force_shutdown(self) -> None:
        """
        强制关闭处理，防止系统崩溃
        """
        try:
            logger.critical("执行强制关闭操作...")
            
            # 尝试保存状态
            try:
                self._save_processing_state()
            except:
                pass
            
            # 尝试卸载所有模型
            try:
                # 释放所有资源
                self._release_noncritical_resources(force=True)
                
                # 尝试卸载当前模型
                if hasattr(self.quant_switcher, '_unload_model'):
                    self.quant_switcher._unload_model()
            except:
                pass
            
            # 记录关闭事件
            logger.critical("系统资源严重不足，执行强制关闭")
            
            # 抛出异常以中断当前执行
            raise MemoryError("系统资源严重不足，执行强制关闭")
            
        except Exception as e:
            # 这里不再记录日志，以免进一步消耗资源
            # 直接将异常向上传递
            raise e
    
    def check_system_state(self) -> EmergencyLevel:
        """
        检查系统状态，返回当前紧急程度
        
        Returns:
            EmergencyLevel: 当前紧急程度
        """
        try:
            mem_info = self.memory_guard.get_memory_info()
            memory_percent = mem_info['percent']
            
            if memory_percent >= self.emergency_threshold:
                return EmergencyLevel.EMERGENCY
            elif memory_percent >= self.critical_threshold:
                return EmergencyLevel.CRITICAL
            elif memory_percent >= self.warning_threshold:
                return EmergencyLevel.WARNING
            else:
                return EmergencyLevel.NORMAL
                
        except Exception as e:
            logger.error(f"检查系统状态时发生错误: {str(e)}")
            # 如果无法检查，保守返回警告状态
            return EmergencyLevel.WARNING
    
    def recover_from_fallback(self) -> bool:
        """
        从降级状态恢复
        
        Returns:
            bool: 恢复是否成功
        """
        logger.info("尝试从降级状态恢复")
        
        try:
            # 检查当前系统状态
            current_level = self.check_system_state()
            
            # 只有在正常状态下才能恢复
            if current_level != EmergencyLevel.NORMAL:
                logger.warning(f"当前系统状态为{current_level.name}，无法恢复")
                return False
            
            # 获取保存的状态
            if not self.saved_states or time.time() - self.state_timestamp > 300:
                logger.warning("没有有效的状态可恢复或状态已过期")
                return False
            
            # 获取量化评估器
            evaluator = get_quant_evaluator()
            
            # 恢复量化级别
            old_quant_level = self.saved_states.get('quant_level')
            if old_quant_level:
                # 先判断内存是否足够支持该级别
                mem_info = self.memory_guard.get_memory_info()
                available_mb = mem_info['available'] / (1024 * 1024)
                
                # 使用评估器获取推荐级别
                recommended_level = evaluator.get_best_quant_level(available_mb)
                
                # 比较两个级别的内存需求
                old_mem = self.quant_config.get_memory_requirement(old_quant_level)
                rec_mem = self.quant_config.get_memory_requirement(recommended_level)
                
                # 评估恢复到原始级别的效果
                if old_mem <= available_mb:
                    # 可以尝试恢复原级别，但先评估效果
                    evaluation = evaluator.evaluate_quantization_level(old_quant_level, recommended_level)
                    
                    # 如果评分良好，可以恢复到原级别
                    if evaluation.get('score', 0) > 40:  # 恢复时可以接受略低的评分
                        logger.info(f"恢复到原量化级别: {old_quant_level}，评分: {evaluation.get('score', 0):.1f}")
                        self.quant_switcher.switch(old_quant_level)
                    else:
                        # 否则使用推荐级别
                        logger.info(f"原级别评分过低 ({evaluation.get('score', 0):.1f})，恢复到推荐级别: {recommended_level}")
                        self.quant_switcher.switch(recommended_level)
                else:
                    # 如果内存不足，使用推荐级别
                    logger.info(f"由于内存限制，恢复到推荐级别: {recommended_level}")
                    self.quant_switcher.switch(recommended_level)
            
            # 恢复其他状态
            logger.info("状态恢复完成")
            return True
            
        except Exception as e:
            logger.error(f"从降级状态恢复时发生错误: {str(e)}")
            return False
    
    def get_protocol_history(self) -> List[Dict[str, Any]]:
        """获取协议执行历史"""
        return self.protocol_history
    
    def get_latest_protocol(self) -> Optional[Dict[str, Any]]:
        """获取最近一次执行的协议记录"""
        if not self.protocol_history:
            return None
        return self.protocol_history[-1]
    
    def _monitor_system_state(self) -> None:
        """监控系统状态的线程函数"""
        while not self._stop_monitor.is_set():
            try:
                # 检查当前状态
                current_level = self.check_system_state()
                
                # 根据状态执行不同级别的降级操作
                if current_level == EmergencyLevel.EMERGENCY:
                    if not self._active_protocols[EmergencyLevel.EMERGENCY]:
                        self._active_protocols[EmergencyLevel.EMERGENCY] = True
                        self.emergency_fallback()
                        self._active_protocols[EmergencyLevel.EMERGENCY] = False
                
                elif current_level == EmergencyLevel.CRITICAL:
                    if not self._active_protocols[EmergencyLevel.CRITICAL]:
                        self.critical_fallback()
                
                elif current_level == EmergencyLevel.WARNING:
                    if not self._active_protocols[EmergencyLevel.WARNING]:
                        self.warning_fallback()
                
            except Exception as e:
                logger.error(f"监控系统状态时发生错误: {str(e)}")
            
            # 等待下一次检查
            self._stop_monitor.wait(self.check_interval)
    
    def _save_processing_state(self) -> None:
        """保存当前处理状态"""
        try:
            # 保存当前量化级别
            current_quant = self.quant_switcher.get_current_level()
            active_model = self.quant_switcher.active_model
            
            # 保存其他相关状态
            self.saved_states = {
                'timestamp': time.time(),
                'quant_level': current_quant,
                'active_model': active_model,
                'memory_state': self.memory_guard.get_memory_info()
            }
            
            # 更新时间戳
            self.state_timestamp = time.time()
            
            logger.debug(f"已保存处理状态: {self.saved_states}")
            
        except Exception as e:
            logger.error(f"保存处理状态时发生错误: {str(e)}")
    
    def _release_noncritical_resources(self, partial: bool = False, force: bool = False) -> None:
        """
        释放非关键资源
        
        Args:
            partial: 是否只释放部分资源
            force: 是否强制释放所有可能的资源
        """
        try:
            # 强制垃圾回收
            gc.collect()
            
            # 释放缓存和非活动资源
            # 这里可以根据具体项目情况添加额外的资源释放逻辑
            
            if not partial or force:
                # 卸载非活动模型
                if hasattr(self.memory_guard, '_unload_inactive_models'):
                    self.memory_guard._unload_inactive_models(force=force)
            
            # 如果是强制释放，尝试释放更多资源
            if force:
                # 可以添加更激进的资源释放逻辑
                pass
            
            logger.info(f"已释放非关键资源 (partial={partial}, force={force})")
            
        except Exception as e:
            logger.error(f"释放非关键资源时发生错误: {str(e)}")
    
    def _run_custom_handlers(self, level: EmergencyLevel) -> None:
        """
        运行自定义处理器
        
        Args:
            level: 紧急级别
        """
        handlers = self.custom_handlers.get(level, [])
        for handler in handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"执行自定义处理器时发生错误: {str(e)}")
    
    def _record_protocol_execution(self, level: EmergencyLevel, duration: float, details: Dict[str, Any]) -> None:
        """
        记录协议执行
        
        Args:
            level: 紧急级别
            duration: 执行时长(秒)
            details: 详细信息
        """
        record = {
            'timestamp': time.time(),
            'level': level.name,
            'duration': duration,
            'memory_state': self.memory_guard.get_memory_info(),
            'details': details
        }
        
        self.protocol_history.append(record)
        
        # 限制历史记录长度
        if len(self.protocol_history) > self.max_history_len:
            self.protocol_history.pop(0)

    def execute_fallback_action(self, level, action, **kwargs):
        """
        执行特定级别的降级动作
        
        Args:
            level: 降级级别
            action: 动作配置
            **kwargs: 额外参数
        
        Returns:
            执行结果
        """
        action_name = action.get('name')
        if not action_name:
            logger.error(f"降级动作配置错误: 缺少名称")
            return False
            
        # 执行前检查
        if not self._pre_action_check(level, action):
            return False
            
        try:
            # 记录执行信息
            action_id = str(uuid.uuid4())
            start_time = time.time()
            logger.info(f"执行降级动作[{level}]: {action_name} (ID: {action_id})")
            
            # 合并参数
            action_params = action.get('params', {}).copy()
            action_params.update(kwargs)
            
            # 获取动作实现
            action_impl = self._get_action_implementation(action_name)
            if not action_impl:
                logger.error(f"找不到降级动作实现: {action_name}")
                return False
            
            # 执行动作
            result = action_impl(**action_params)
            
            # 记录执行结束
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"降级动作完成[{level}]: {action_name}, 用时: {execution_time:.2f}秒")
            
            # 更新执行历史
            self._action_history.append({
                'id': action_id,
                'level': level,
                'name': action_name,
                'start_time': start_time,
                'end_time': end_time,
                'execution_time': execution_time,
                'success': result is not False,
                'params': action_params
            })
            
            # 如果验证器可用，验证操作效果
            if _validator_available:
                try:
                    validator = get_validator()
                    validation_result = validator.validate(action_name)
                    
                    # 如果验证失败，尝试处理
                    if not validation_result:
                        # 获取最新的验证结果
                        history = validator.get_validation_history(1)
                        if history:
                            failed_result = history[0]
                            # 根据级别选择不同的处理策略
                            if level == "warning":
                                strategy = FailureHandlingStrategy.RETRY
                            elif level == "critical":
                                strategy = FailureHandlingStrategy.ESCALATE
                            else:  # emergency
                                strategy = FailureHandlingStrategy.COMBINE
                                
                            # 处理验证失败
                            handled = handle_failed_validation(
                                action_name, 
                                failed_result, 
                                strategy
                            )
                            logger.info(f"降级动作验证失败处理: {action_name}, 策略: {strategy.name}, 结果: {'成功' if handled else '失败'}")
                except Exception as e:
                    logger.error(f"操作效果验证失败: {e}")
            
            # 调用后处理
            self._post_action_process(level, action, result)
            
            return result
            
        except Exception as e:
            logger.error(f"执行降级动作[{level}]时出错: {action_name}, 错误: {str(e)}")
            logger.debug(traceback.format_exc())
            return False


# 便捷的全局接口函数
_fallback_protocol = None

def get_fallback_protocol() -> FallbackProtocol:
    """获取全局降级协议实例"""
    global _fallback_protocol
    if _fallback_protocol is None:
        _fallback_protocol = FallbackProtocol()
    return _fallback_protocol

def emergency_fallback() -> bool:
    """执行紧急降级操作"""
    return get_fallback_protocol().emergency_fallback()

def critical_fallback() -> bool:
    """执行临界降级操作"""
    return get_fallback_protocol().critical_fallback()

def warning_fallback() -> bool:
    """执行警告降级操作"""
    return get_fallback_protocol().warning_fallback()

def force_shutdown() -> None:
    """强制关闭处理"""
    return get_fallback_protocol().force_shutdown()

def save_processing_state() -> None:
    """保存当前处理状态"""
    fallback = get_fallback_protocol()
    fallback._save_processing_state()

def release_noncritical_resources(partial: bool = False, force: bool = False) -> None:
    """释放非关键资源"""
    fallback = get_fallback_protocol()
    fallback._release_noncritical_resources(partial=partial, force=force)

def recover_from_fallback() -> bool:
    """从降级状态恢复"""
    return get_fallback_protocol().recover_from_fallback()


# 简单使用示例
if __name__ == "__main__":
    # 初始化降级协议
    protocol = FallbackProtocol()
    
    # 测试紧急处理
    print("\n紧急降级协议测试:")
    print("=" * 60)
    
    # 模拟内存紧急情况
    print("模拟内存紧急情况...")
    protocol.emergency_fallback()
    
    # 查看降级历史
    history = protocol.get_protocol_history()
    print("\n降级历史记录:")
    print("=" * 60)
    for record in history:
        level = record['level']
        timestamp = time.strftime("%H:%M:%S", time.localtime(record['timestamp']))
        duration = record['duration']
        
        print(f"{timestamp} - {level}: 执行时间 {duration:.2f}秒")
    
    # 尝试恢复
    print("\n尝试从降级状态恢复...")
    success = protocol.recover_from_fallback()
    print(f"恢复{'成功' if success else '失败'}") 