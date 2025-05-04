"""
VisionAI-ClipsMaster的用户界面模块

提供交互界面、可视化组件和用户反馈机制，
支持剧本重构、视频处理和预览功能。
"""

from ui.main_window import MainWindow
from ui.error_display import handle_error, ErrorMessageLocalizer
from ui.screenplay_app import ScreenplayApp

# 导出主要组件
__all__ = [
    'MainWindow',
    'ScreenplayApp',
    'handle_error',
    'ErrorMessageLocalizer'
] 