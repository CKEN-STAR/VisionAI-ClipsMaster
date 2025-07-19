"""
性能监控模块
提供高级性能监控、内存优化和CPU分析功能
"""

__version__ = "2.0.0"

# 导入原有性能模块
try:
    from .memory_guard import *
except ImportError as e:
    print(f"[WARN] 原有性能模块导入警告: {e}")

# 导入新的高级性能监控模块
try:
    from .advanced_monitor import (
        PerformanceSnapshot,
        MemoryAnalysis,
        CPUAnalysis,
        AdvancedPerformanceMonitor,
        MemoryOptimizer,
        CPUOptimizer,
        PerformanceVisualizationWidget
    )

    from .monitor_dashboard import (
        PerformanceMetricWidget,
        PerformanceMonitorDashboard
    )

    print("[OK] 高级性能监控模块导入成功")

except ImportError as e:
    print(f"[WARN] 高级性能监控模块导入警告: {e}")

__all__ = [
    'memory_guard',
    'PerformanceSnapshot',
    'MemoryAnalysis',
    'CPUAnalysis',
    'AdvancedPerformanceMonitor',
    'MemoryOptimizer',
    'CPUOptimizer',
    'PerformanceVisualizationWidget',
    'PerformanceMetricWidget',
    'PerformanceMonitorDashboard'
]
