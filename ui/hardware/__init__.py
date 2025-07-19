"""
UI硬件模块
提供硬件检测和优化功能
"""

__version__ = "1.0.0"

# 导入硬件模块
try:
    from .performance_tier import *
    from .render_optimizer import *
    from .memory_manager import *
    from .disk_cache import *
    from .input_latency import *
    from .power_manager import *
    from .compute_offloader import *
    from .enterprise_deploy import *
except ImportError as e:
    print(f"[WARN] UI硬件模块导入警告: {e}")

__all__ = [
    'performance_tier',
    'render_optimizer',
    'memory_manager',
    'disk_cache',
    'input_latency',
    'power_manager',
    'compute_offloader',
    'enterprise_deploy'
]
