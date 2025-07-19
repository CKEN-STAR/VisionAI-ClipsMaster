"""
启动优化模块
提供智能启动进度管理和性能优化功能
"""

from .progress_manager import (
    StartupProgressManager,
    StartupProgressDialog,
    show_startup_progress
)

from .smart_loader import (
    ModuleInfo,
    SmartModuleLoader,
    get_smart_loader,
    preload_critical_modules,
    get_module
)

from .optimized_startup import (
    OptimizedStartupManager,
    start_optimized_application,
    create_main_window_after_startup
)

__all__ = [
    'StartupProgressManager',
    'StartupProgressDialog',
    'show_startup_progress',
    'ModuleInfo',
    'SmartModuleLoader',
    'get_smart_loader',
    'preload_critical_modules',
    'get_module',
    'OptimizedStartupManager',
    'start_optimized_application',
    'create_main_window_after_startup'
]
