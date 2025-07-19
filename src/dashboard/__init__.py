#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
仪表盘模块初始化

提供性能监控、数据分析和可视化功能
"""

# 导出仪表盘核心组件
from src.dashboard.data_integration import DataAggregator
from src.dashboard.visualizer import DataVisualizer
from src.dashboard.correlation_engine import CorrelationEngine
from src.dashboard.predictive_engine import PredictiveModel

# 导出安全审计追踪模块
from src.dashboard.audit_trail import (
    AuditTrail, AuditLevel, AuditCategory,
    get_audit_trail, log_view_action, log_data_access,
    log_model_operation, log_parameter_change, audit_log
)

# 初始化日志
import logging
logger = logging.getLogger(__name__)

__all__ = [
    'DataAggregator',
    'DataVisualizer',
    'CorrelationEngine',
    'PredictiveModel',
    'AuditTrail',
    'AuditLevel',
    'AuditCategory',
    'get_audit_trail',
    'log_view_action',
    'log_data_access',
    'log_model_operation',
    'log_parameter_change',
    'audit_log'
] 