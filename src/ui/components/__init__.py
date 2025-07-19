#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI组件模块初始化文件
"""

# 导入UI组件
try:
    from .realtime_charts import RealtimeCharts
    from .alert_manager import AlertManager
except ImportError as e:
    print(f"Warning: Some UI components not available: {e}")
    RealtimeCharts = None
    AlertManager = None

# 导入现有组件（仅导入实际存在的组件）
ColorHelper = None
KeyboardNavigationHelper = None
ScreenReaderHelper = None
AnimationManager = None
FallbackNotification = None
MemoryVisualization = None
TutorialManager = None
VersionSuggestionPanel = None
VideoProcessor = None

# 尝试导入现有组件（如果存在）
existing_components = [
    ('accessibility_helper', 'ColorHelper'),
    ('accessibility_helper', 'KeyboardNavigationHelper'),
    ('accessibility_helper', 'ScreenReaderHelper'),
    ('animation_manager', 'AnimationManager'),
    ('fallback_notification', 'FallbackNotification'),
    ('memory_visualization', 'MemoryVisualization'),
    ('tutorial_manager', 'TutorialManager'),
    ('version_suggestion_panel', 'VersionSuggestionPanel'),
    ('video_processor', 'VideoProcessor')
]

for module_name, class_name in existing_components:
    try:
        # 使用相对导入
        from importlib import import_module
        module = import_module(f'.{module_name}', package=__name__)
        globals()[class_name] = getattr(module, class_name)
    except (ImportError, ModuleNotFoundError):
        # 组件不存在，保持为None
        pass

# 导出的公共接口（仅包含实际可用的组件）
__all__ = ['RealtimeCharts', 'AlertManager']

# 动态添加可用的现有组件到__all__
for class_name in ['ColorHelper', 'KeyboardNavigationHelper', 'ScreenReaderHelper',
                   'AnimationManager', 'FallbackNotification', 'MemoryVisualization',
                   'TutorialManager', 'VersionSuggestionPanel', 'VideoProcessor']:
    if globals().get(class_name) is not None:
        __all__.append(class_name)
