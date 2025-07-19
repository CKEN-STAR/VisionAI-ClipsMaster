#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全模块

包含访问控制、敏感数据处理和权限管理相关功能。
"""

from src.security.access_control import (
    get_access_control,
    secure_golden_samples,
    verify_golden_samples_integrity,
    get_audit_logger,
    AccessControl,
    AuditLogger
)

__all__ = [
    'get_access_control',
    'secure_golden_samples',
    'verify_golden_samples_integrity',
    'get_audit_logger',
    'AccessControl',
    'AuditLogger'
] 