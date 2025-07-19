#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存管理模块

该模块提供内存管理和优化功能，包括资源跟踪、内存监控和优化策略。
用于提高应用在各种硬件环境下的性能和稳定性。
"""

# 导入资源跟踪器
from src.memory.resource_tracker import (
    ResourceTracker,
    get_resource_tracker
)

# 导入内存碎片整理器
from src.memory.defragmenter import (
    MemoryDefragmenter,
    defragment_memory
)

# 导入锁管理器
from src.memory.lock_manager import (
    ResourceLockManager,
    acquire_lock,
    release_lock
)

# 导入快照管理
from src.memory.snapshot import (
    create_snapshot,
    restore_snapshot,
    delete_snapshot
)

# 导入透明压缩内存分配器
from src.memory.compressed_allocator import (
    CompressedAllocator,
    malloc,
    access,
    free,
    get_compression_stats
)

# 导入内存泄漏追踪器
try:
    from src.memory.leak_detector import (
        LeakTracker,
        get_leak_tracker,
        start_leak_tracking,
        stop_leak_tracking,
        check_for_leaks,
        save_leak_report
    )
    HAS_LEAK_TRACKER = True
except ImportError:
    HAS_LEAK_TRACKER = False

# 定义辅助函数来兼容旧的API
def track_resource(*args, **kwargs):
    """兼容旧API的资源跟踪函数"""
    tracker = get_resource_tracker()
    return tracker.track_resource(*args, **kwargs)

def release_resource(resource_id):
    """兼容旧API的资源释放函数"""
    tracker = get_resource_tracker()
    return tracker.untrack_resource(resource_id)

def get_resource_stats(resource_id=None):
    """兼容旧API的资源统计函数"""
    tracker = get_resource_tracker()
    if resource_id:
        return tracker.get_resource_status(resource_id)
    else:
        return {
            "memory_status": tracker.get_memory_status(),
            "tracked_resources_count": len(tracker.tracked_resources)
        }

# 泄漏追踪辅助函数
def enable_leak_tracking(interval_seconds=300.0):
    """
    启用内存泄漏追踪
    
    Args:
        interval_seconds: 检查间隔（秒）
    
    Returns:
        bool: 是否成功启用
    """
    if not HAS_LEAK_TRACKER:
        return False
    
    try:
        start_leak_tracking(interval_seconds)
        return True
    except Exception:
        return False

def disable_leak_tracking():
    """
    禁用内存泄漏追踪
    
    Returns:
        bool: 是否成功禁用
    """
    if not HAS_LEAK_TRACKER:
        return False
    
    try:
        stop_leak_tracking()
        return True
    except Exception:
        return False

def check_leaks():
    """
    检查内存泄漏
    
    Returns:
        list or None: 检测到的泄漏列表，如果未启用则返回None
    """
    if not HAS_LEAK_TRACKER:
        return None
    
    try:
        return check_for_leaks()
    except Exception:
        return None

__all__ = [
    # 资源追踪
    'ResourceTracker',
    'track_resource',
    'release_resource',
    'get_resource_stats',
    'get_resource_tracker',
    
    # 碎片整理
    'MemoryDefragmenter',
    'defragment_memory',
    
    # 锁管理
    'ResourceLockManager',
    'acquire_lock',
    'release_lock',
    
    # 快照管理
    'create_snapshot',
    'restore_snapshot',
    'delete_snapshot',
    
    # 透明压缩内存分配
    'CompressedAllocator',
    'malloc',
    'access',
    'free',
    'get_compression_stats',
    
    # 泄漏追踪
    'HAS_LEAK_TRACKER',
    'enable_leak_tracking',
    'disable_leak_tracking',
    'check_leaks'
]

# 如果有泄漏追踪器，添加相关导出
if HAS_LEAK_TRACKER:
    __all__.extend([
        'LeakTracker',
        'get_leak_tracker',
        'start_leak_tracking',
        'stop_leak_tracking',
        'check_for_leaks',
        'save_leak_report'
    ]) 