#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
熔断系统模块
---------
提供内存安全和系统稳定性保障
包含内存压力检测、熔断触发、资源恢复和知识库等组件
"""

# 版本信息
__version__ = "1.0.0"

# 导出主要组件
from src.fuse.knowledge_base import get_knowledge_base
from src.fuse.knowledge_service import get_knowledge_service

# 公开API
__all__ = [
    'get_knowledge_base',
    'get_knowledge_service'
]

from .pressure_detector import MemoryPressureDetector, get_pressure_detector
from .integration import MemoryIntegrationManager, get_integration_manager
from .visualization import PressureVisualizer, get_pressure_visualizer
from .action_scheduler import ActionPrioritizer, get_action_prioritizer
from .action_scheduler_hook import ActionSchedulerHook, get_scheduler_hook

# 导出安全熔断执行器功能
from .safe_executor import (
    safe_execute,
    register_action,
    register_resource,
    release_resource,
    force_gc,
    release_models,
    get_executor,
    FuseExecutor,
    MemoryTracker
)

# 导出熔断状态恢复系统功能
from .recovery_manager import (
    FuseRecovery,
    get_recovery_manager,
    save_system_state,
    restore_system_state,
    register_resource_state,
    register_recovery_handler,
    ResourceState
)

# 导出熔断效果验证系统功能
from .effect_validator import (
    FuseValidator,
    ValidationResult,
    FailureHandlingStrategy,
    get_validator,
    execute_with_validation,
    handle_failed_validation
)

# 导出熔断事件溯源系统功能
from .event_tracer import (
    FuseAudit,
    FuseEvent,
    EventType,
    get_audit,
    log_event,
    start_trace,
    end_trace,
    log_fuse_triggered,
    log_fuse_completed,
    log_resource_released,
    log_memory_snapshot,
    log_error,
    log_gc_performed,
    log_system_state_change,
    init_event_tracer,
    FuseEventAnalyzer,
    get_analyzer
)

__all__ = [
    'MemoryPressureDetector', 
    'get_pressure_detector',
    'MemoryIntegrationManager',
    'get_integration_manager',
    'PressureVisualizer',
    'get_pressure_visualizer',
    'ActionPrioritizer',
    'get_action_prioritizer',
    'ActionSchedulerHook',
    'get_scheduler_hook',
    'safe_execute',
    'register_action',
    'register_resource',
    'release_resource',
    'force_gc',
    'release_models',
    'get_executor',
    'FuseExecutor',
    'MemoryTracker',
    'FuseRecovery',
    'get_recovery_manager',
    'save_system_state',
    'restore_system_state',
    'register_resource_state',
    'register_recovery_handler',
    'ResourceState',
    'FuseValidator',
    'ValidationResult',
    'FailureHandlingStrategy',
    'get_validator',
    'execute_with_validation',
    'handle_failed_validation',
    # 熔断事件溯源系统
    'FuseAudit',
    'FuseEvent',
    'EventType',
    'get_audit',
    'log_event',
    'start_trace',
    'end_trace',
    'log_fuse_triggered',
    'log_fuse_completed',
    'log_resource_released',
    'log_memory_snapshot',
    'log_error',
    'log_gc_performed',
    'log_system_state_change',
    'init_event_tracer',
    'FuseEventAnalyzer',
    'get_analyzer'
] 