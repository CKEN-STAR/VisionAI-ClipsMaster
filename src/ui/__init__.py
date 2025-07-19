#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI模块初始化文件
提供UI组件的统一导入接口
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "VisionAI-ClipsMaster Team"

# 首先修复环境问题
try:
    from .ui_environment_fix import initialize_ui_environment
    ui_components = initialize_ui_environment()
    print("[OK] UI环境初始化完成")
except ImportError as e:
    print(f"[WARN] UI环境修复模块不可用: {e}")
    ui_components = {}
except Exception as e:
    print(f"[WARN] UI环境初始化失败: {e}")
    ui_components = {}
    # 继续执行，不中断启动流程

# 导入核心UI组件（使用环境修复后的组件）
TrainingPanel = ui_components.get('TrainingPanel')
ProgressDashboard = ui_components.get('ProgressDashboard')
RealtimeCharts = ui_components.get('RealtimeCharts')
AlertManager = ui_components.get('AlertManager')

# 主窗口组件（延迟导入以避免循环依赖）
MainWindow = None

def get_main_window():
    """延迟导入主窗口以避免循环依赖"""
    global MainWindow
    if MainWindow is None:
        try:
            from .main_window import MainWindow
        except ImportError:
            try:
                # 尝试从根目录导入
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from simple_ui import VisionAIClipsMasterUI as MainWindow
            except ImportError as e:
                print(f"Warning: Main window not available: {e}")
                MainWindow = None
    return MainWindow

# 导入UI组件子模块
try:
    from .components import *
except ImportError as e:
    print(f"Warning: UI components submodule not fully available: {e}")

# 导出的公共接口
__all__ = [
    'TrainingPanel',
    'ProgressDashboard',
    'RealtimeCharts',
    'AlertManager',
    'get_main_window'
]

# UI模块配置
UI_CONFIG = {
    "theme": "dark",
    "language": "zh_CN",
    "font_size": 12,
    "window_size": (1200, 800),
    "enable_animations": True,
    "enable_tooltips": True
}

def get_ui_config():
    """获取UI配置"""
    return UI_CONFIG.copy()

def set_ui_config(**kwargs):
    """设置UI配置"""
    UI_CONFIG.update(kwargs)
