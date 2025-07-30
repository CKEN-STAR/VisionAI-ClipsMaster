#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能推荐下载器集成回退模块
当主集成模块失败时使用的简化版本
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FallbackIntegrator:
    """回退集成器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        logger.info("✅ 回退集成器初始化完成")
    
    def show_smart_downloader(self, model_name: str = None):
        """显示智能下载器（回退版本）"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self.main_window,
                "智能下载器",
                f"智能下载器功能暂时不可用\n请使用传统下载方式下载模型: {model_name or '未指定'}"
            )
            return False
        except Exception as e:
            logger.error(f"回退集成器显示失败: {e}")
            return False

def integrate_smart_downloader_to_main_ui(main_window) -> FallbackIntegrator:
    """回退集成函数"""
    try:
        return FallbackIntegrator(main_window)
    except Exception as e:
        logger.error(f"回退集成失败: {e}")
        return None
