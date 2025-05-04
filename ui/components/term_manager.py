#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
终端管理模块 - 简化版（UI演示用）
"""

import logging

logger = logging.getLogger(__name__)

class TermManager:
    """终端管理器 - 简化版（UI演示用）"""
    
    def __init__(self, parent=None):
        """初始化终端管理器"""
        self.parent = parent
        self.active = False
        
    def run_command(self, command):
        """运行命令"""
        logger.info(f"运行命令: {command}")
        return True 