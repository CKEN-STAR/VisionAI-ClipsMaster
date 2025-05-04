#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心功能模块

提供系统核心功能和基础服务。
"""

from .auto_recovery import (
    init_recovery_system,
    get_recovery_report
)

__all__ = [
    'init_recovery_system',
    'get_recovery_report'
] 