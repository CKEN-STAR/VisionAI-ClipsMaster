#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
版本管理模块 - 简化版

提供参数管理和版本控制简化功能。
"""

# 导出简化版参数管理器函数
from .param_manager import (
    get_params,
    prepare_params,
    save_params_to_file,
    load_params_from_file
)

__all__ = [
    'get_params',
    'prepare_params',
    'save_params_to_file',
    'load_params_from_file'
] 