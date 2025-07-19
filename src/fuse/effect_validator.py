"""
熔断效果验证系统 (Fuse Effect Validator)
--------------------------------------
验证熔断操作的实际效果是否符合预期，主要功能包括：

1. 内存释放效果验证 - 验证熔断操作是否达到预期的内存释放量
2. 操作耗时验证 - 验证操作执行时间是否在可接受范围内
3. 多级失败处理 - 支持重试、升级操作、触发警报等处理流程
4. 效果报告生成 - 记录各类熔断操作的实际效果，用于优化熔断策略

该系统与安全熔断执行器(safe_executor.py)和熔断状态恢复系统(recovery_manager.py)
协同工作，确保熔断系统的有效性和可靠性。
"""

import os
import time
import logging
import threading
import traceback
import psutil
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from .safe_executor import get_executor, safe_execute

# 配置日志
logger = logging.getLogger("effect_validator")


class FailureHandlingStrategy(Enum):
    """失败处理策略枚举"""
    RETRY = 1                # 重试当前操作
    ESCALATE = 2             # 升级为更强力的操作
    ALERT = 3                # 触发系统警报
    FALLBACK = 4             # 降级使用备选方案
    COMBINE = 5              # 组合多个操作一起执行


@dataclass
class ValidationResult:
    """验证结果数据类"""
    action: str                          # 执行的操作
    success: bool                        # 是否成功
    memory_before: float                 # 操作前内存使用(MB)
    memory_after: float                  # 操作后内存使用(MB)
    reduction: float                     # 实际减少量(MB)
    expected_reduction: float            # 预期减少量(MB)
    execution_time: float                # 执行时间(秒)
    timestamp: datetime = datetime.now() # 执行时间戳
    
    @property
    def reduction_percent(self) -> float:
        """内存减少的百分比"""
        if self.memory_before == 0:
            return 0.0
        return (self.reduction / self.memory_before) * 100.0
    
    @property
    def effectiveness(self) -> float:
        """操作有效性(实际减少/预期减少)"""
        if self.expected_reduction == 0:
            return 0.0
        return self.reduction / self.expected_reduction
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "action": self.action,
            "success": self.success,
            "memory_before_mb": round(self.memory_before, 2),
            "memory_after_mb": round(self.memory_after, 2),
            "reduction_mb": round(self.reduction, 2),
            "expected_reduction_mb": round(self.expected_reduction, 2),
            "execution_time_sec": round(self.execution_time, 3),
            "timestamp": self.timestamp.isoformat(),
            "reduction_percent": round(self.reduction_percent, 2),
            "effectiveness": round(self.effectiveness, 2)
        }


class FuseValidator:
    """熔断效果验证器，验证各类熔断操作的实际效果"""
    
    # 预期的内存减少量(MB)
    EXPECTED_REDUCTION = {
        'clear_cache': 100,         # 清理缓存预期减少100MB
        'unload_model': 500,        # 卸载模型预期减少500MB
        'kill_process': 1500,       # 终止进程预期减少1500MB
        'force_gc': 150,            # 强制GC预期减少150MB
        'release_resources': 200,   # 释放资源预期减少200MB
        'reduce_cache_size': 80,    # 减小缓存大小预期减少80MB
        'pause_background': 50      # 暂停后台任务预期减少50MB
    }
    
    # 可接受的操作执行时间上限(秒)
    MAX_EXECUTION_TIME = {
        'clear_cache': 2.0,
        'unload_model': 5.0,
        'kill_process': 3.0,
        'force_gc': 3.0,
        'release_resources': 2.0,
        'reduce_cache_size': 1.0,
        'pause_background': 0.5
    }
    
    # 不同操作的重试次数
    MAX_RETRIES = {
        'clear_cache': 3,
        'unload_model': 2,
        'kill_process': 1,
        'force_gc': 3,
        'release_resources': 2,
        'reduce_cache_size': 3,
        'pause_background': 3
    }
    
    # 操作升级映射，当一个操作失败时升级为更强力的操作
    ESCALATION_MAP = {
        'clear_cache': 'force_gc',
        'unload_model': 'kill_process',
        'reduce_cache_size': 'clear_cache',
        'pause_background': 'release_resources',
        'force_gc': 'release_resources',
        'release_resources': 'unload_model'
    }
    
    def __init__(self):
        """初始化验证器"""
        # 内存使用记录器，记录最近的内存使用情况
        self.mem_recorder = []
        self.update_interval = 1.0  # 内存更新间隔(秒)
        self.max_records = 30       # 最多保留30条记录
        
        # 验证历史
        self.validation_history = []
        
        # 验证结果回调
        self.result_callbacks = []
        
        # 内存监控线程
        self.monitor_thread = None
        self.should_monitor = False
        self.monitor_lock = threading.RLock()
        
        # 初始化内存记录
        self._init_memory_recorder()
        
        logger.info("熔断效果验证器初始化完成")
    
    def _init_memory_recorder(self):
        """初始化内存记录器"""
        # 初始添加一个内存记录
        current_mem = self._get_current_memory()
        self.mem_recorder.append(current_mem)
    
    def _get_current_memory(self) -> float:
        """获取当前内存使用量(MB)"""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)  # 转换为MB
    
    def start_monitoring(self):
        """开始内存使用监控"""
        with self.monitor_lock:
            if self.monitor_thread is not None and self.monitor_thread.is_alive():
                return
            
            self.should_monitor = True
            self.monitor_thread = threading.Thread(
                target=self._memory_monitor_thread,
                daemon=True,
                name="EffectValidatorMonitor"
            )
            self.monitor_thread.start()
            logger.debug("内存使用监控已启动")
    
    def stop_monitoring(self):
        """停止内存使用监控"""
        with self.monitor_lock:
            self.should_monitor = False
            if self.monitor_thread is not None:
                self.monitor_thread.join(timeout=2.0)
                self.monitor_thread = None
            logger.debug("内存使用监控已停止")
    
    def _memory_monitor_thread(self):
        """内存监控线程，定期更新内存使用记录"""
        while self.should_monitor:
            try:
                # 获取当前内存使用
                current_mem = self._get_current_memory()
                
                # 更新内存记录
                with self.monitor_lock:
                    self.mem_recorder.append(current_mem)
                    # 保持记录数量在限制范围内
                    if len(self.mem_recorder) > self.max_records:
                        self.mem_recorder = self.mem_recorder[-self.max_records:]
                
                # 等待下一次更新
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"内存监控线程错误: {e}")
                time.sleep(5.0)  # 出错后等待较长时间再继续
    
    def register_result_callback(self, callback: Callable[[ValidationResult], None]):
        """注册验证结果回调函数"""
        self.result_callbacks.append(callback)
    
    def validate(self, action: str) -> bool:
        """
        验证熔断操作是否达到预期效果
        
        Args:
            action: 要验证的操作名称
            
        Returns:
            是否达到预期效果
        """
        # 确保内存记录已经初始化
        if not self.mem_recorder:
            logger.warning("内存记录为空，无法验证操作效果")
            return False
        
        # 确保预期减少量已定义
        if action not in self.EXPECTED_REDUCTION:
            logger.warning(f"未定义操作 {action} 的预期减少量")
            return False
        
        # 获取操作前内存使用量
        before = self.mem_recorder[-2] if len(self.mem_recorder) >= 2 else self.mem_recorder[0]
        # 获取操作后内存使用量
        after = self.mem_recorder[-1]
        # 计算实际减少量
        actual = before - after
        # 获取预期减少量
        expected = self.EXPECTED_REDUCTION.get(action, 0)
        
        # 创建验证结果
        result = ValidationResult(
            action=action,
            success=actual >= expected,
            memory_before=before,
            memory_after=after,
            reduction=actual,
            expected_reduction=expected,
            execution_time=0.0  # 此处没有执行时间信息
        )
        
        # 记录结果
        self.validation_history.append(result)
        
        # 调用回调函数
        for callback in self.result_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"回调函数错误: {e}")
        
        # 记录日志
        if result.success:
            logger.info(f"操作 {action} 验证成功: 减少 {actual:.2f}MB，预期 {expected:.2f}MB")
        else:
            logger.warning(f"操作 {action} 验证失败: 减少 {actual:.2f}MB，未达预期 {expected:.2f}MB")
        
        return result.success
    
    def execute_and_validate(self, action: str, **kwargs) -> Tuple[Any, ValidationResult]:
        """
        执行操作并验证其效果
        
        Args:
            action: 要执行的操作
            **kwargs: 传递给操作的参数
            
        Returns:
            (操作结果, 验证结果)
        """
        # 记录操作前内存
        before_mem = self._get_current_memory()
        start_time = time.time()
        
        # 执行操作
        try:
            result = safe_execute(action, **kwargs)
        except Exception as e:
            logger.error(f"执行操作 {action} 时发生错误: {e}")
            result = None
        
        # 记录执行时间
        execution_time = time.time() - start_time
        
        # 等待短暂时间，让内存变化稳定
        time.sleep(0.2)
        
        # 记录操作后内存
        after_mem = self._get_current_memory()
        
        # 计算减少量
        reduction = before_mem - after_mem
        expected = self.EXPECTED_REDUCTION.get(action, 0)
        
        # 检查执行时间
        time_ok = execution_time <= self.MAX_EXECUTION_TIME.get(action, float('inf'))
        
        # 创建验证结果
        validation_result = ValidationResult(
            action=action,
            success=reduction >= expected and time_ok,
            memory_before=before_mem,
            memory_after=after_mem,
            reduction=reduction,
            expected_reduction=expected,
            execution_time=execution_time
        )
        
        # 记录结果
        self.validation_history.append(validation_result)
        
        # 调用回调函数
        for callback in self.result_callbacks:
            try:
                callback(validation_result)
            except Exception as e:
                logger.error(f"回调函数错误: {e}")
        
        # 记录日志
        log_func = logger.info if validation_result.success else logger.warning
        log_func(f"操作 {action} 执行与验证: 减少 {reduction:.2f}MB (预期 {expected:.2f}MB)，"
                f"耗时 {execution_time:.3f}秒，成功: {validation_result.success}")
        
        return result, validation_result
    
    def handle_validation_failure(self, failed_action: str, result: ValidationResult,
                               strategy: FailureHandlingStrategy = FailureHandlingStrategy.RETRY,
                               retry_count: int = 0, **kwargs) -> Tuple[bool, ValidationResult]:
        """
        处理验证失败
        
        Args:
            failed_action: 失败的操作
            result: 失败的验证结果
            strategy: 处理策略
            retry_count: 当前重试次数
            **kwargs: 额外参数
            
        Returns:
            (是否处理成功, 最后的验证结果)
        """
        if result.success:
            return True, result
        
        logger.warning(f"操作 {failed_action} 验证失败，采用 {strategy.name} 策略处理，当前重试次数: {retry_count}")
        
        if strategy == FailureHandlingStrategy.RETRY:
            # 检查是否超过最大重试次数
            max_retries = self.MAX_RETRIES.get(failed_action, 3)
            if retry_count >= max_retries:
                logger.error(f"操作 {failed_action} 重试次数已达上限 {max_retries}，升级处理策略")
                # 升级为ESCALATE策略
                return self.handle_validation_failure(
                    failed_action, result, FailureHandlingStrategy.ESCALATE, 0, **kwargs
                )
            
            # 重试当前操作
            logger.info(f"重试操作 {failed_action}，第 {retry_count + 1} 次")
            
            # 在重试前先强制GC，可能有助于释放内存
            if retry_count > 0:
                safe_execute("force_gc")
                time.sleep(0.5)
            
            # 重新执行操作
            _, new_result = self.execute_and_validate(failed_action, **kwargs)
            
            # 递归处理，增加重试计数
            return self.handle_validation_failure(
                failed_action, new_result, strategy, retry_count + 1, **kwargs
            )
            
        elif strategy == FailureHandlingStrategy.ESCALATE:
            # 获取升级操作
            escalated_action = self.ESCALATION_MAP.get(failed_action)
            if not escalated_action:
                logger.error(f"操作 {failed_action} 没有定义升级操作，改用ALERT策略")
                return self.handle_validation_failure(
                    failed_action, result, FailureHandlingStrategy.ALERT, 0, **kwargs
                )
            
            logger.info(f"升级操作: {failed_action} -> {escalated_action}")
            
            # 执行升级操作
            _, new_result = self.execute_and_validate(escalated_action, **kwargs)
            
            # 如果升级操作成功，返回成功
            if new_result.success:
                return True, new_result
            
            # 如果升级操作也失败，转为ALERT策略
            logger.error(f"升级操作 {escalated_action} 也失败，改用ALERT策略")
            return self.handle_validation_failure(
                escalated_action, new_result, FailureHandlingStrategy.ALERT, 0, **kwargs
            )
            
        elif strategy == FailureHandlingStrategy.ALERT:
            # 触发系统警报
            logger.critical(f"熔断操作 {failed_action} 验证失败，触发系统警报！")
            
            # 这里可以添加发送警报的代码，如邮件通知、短信提醒等
            # 为简化实现，这里只记录日志
            
            # 返回处理失败
            return False, result
            
        elif strategy == FailureHandlingStrategy.FALLBACK:
            # 使用备选方案
            fallback_actions = kwargs.get('fallback_actions', ['force_gc', 'release_resources'])
            
            logger.info(f"使用备选方案: {fallback_actions}")
            
            # 执行所有备选操作
            success = False
            latest_result = result
            
            for action in fallback_actions:
                _, action_result = self.execute_and_validate(action)
                latest_result = action_result
                
                if action_result.success:
                    success = True
                    logger.info(f"备选操作 {action} 成功")
                    break
            
            # 返回处理结果
            return success, latest_result
            
        elif strategy == FailureHandlingStrategy.COMBINE:
            # 组合多个操作
            combined_actions = kwargs.get('combined_actions', ['force_gc', 'clear_cache', 'release_resources'])
            
            logger.info(f"组合执行操作: {combined_actions}")
            
            # 执行所有组合操作
            success = True
            latest_result = result
            
            for action in combined_actions:
                _, action_result = self.execute_and_validate(action)
                latest_result = action_result
                
                if not action_result.success:
                    success = False
                    logger.warning(f"组合操作 {action} 失败")
            
            # 返回处理结果
            return success, latest_result
        
        # 默认返回失败
        return False, result
    
    def get_recent_memory_usage(self, count: int = 10) -> List[float]:
        """获取最近的内存使用记录"""
        with self.monitor_lock:
            return self.mem_recorder[-count:] if count < len(self.mem_recorder) else self.mem_recorder[:]
    
    def get_validation_history(self, count: int = None) -> List[ValidationResult]:
        """获取验证历史记录"""
        if count is None:
            return self.validation_history[:]
        return self.validation_history[-count:] if count < len(self.validation_history) else self.validation_history[:]
    
    def get_action_effectiveness(self, action: str = None) -> Dict[str, float]:
        """
        获取操作的有效性数据
        
        Args:
            action: 指定操作，为None时获取所有操作
            
        Returns:
            操作有效性字典 {操作: 有效性得分}
        """
        if not self.validation_history:
            return {}
        
        # 过滤指定操作的记录
        if action:
            filtered_history = [r for r in self.validation_history if r.action == action]
        else:
            filtered_history = self.validation_history
        
        # 按操作分组计算平均有效性
        effectiveness = {}
        for result in filtered_history:
            if result.action not in effectiveness:
                effectiveness[result.action] = []
            effectiveness[result.action].append(result.effectiveness)
        
        # 计算每个操作的平均有效性
        return {k: sum(v) / len(v) for k, v in effectiveness.items()}


# 单例模式
_validator_instance = None

def get_validator() -> FuseValidator:
    """获取验证器单例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = FuseValidator()
    return _validator_instance


def execute_with_validation(action: str, **kwargs) -> Tuple[Any, bool]:
    """
    执行操作并验证效果
    
    Args:
        action: 要执行的操作
        **kwargs: 传递给操作的参数
        
    Returns:
        (操作结果, 验证是否成功)
    """
    validator = get_validator()
    result, validation = validator.execute_and_validate(action, **kwargs)
    return result, validation.success


def handle_failed_validation(action: str, validation_result: ValidationResult, 
                      strategy: FailureHandlingStrategy = FailureHandlingStrategy.RETRY,
                      **kwargs) -> bool:
    """
    处理验证失败
    
    Args:
        action: 失败的操作
        validation_result: 验证结果
        strategy: 处理策略
        **kwargs: 额外参数
        
    Returns:
        是否处理成功
    """
    validator = get_validator()
    success, _ = validator.handle_validation_failure(action, validation_result, strategy, **kwargs)
    return success 