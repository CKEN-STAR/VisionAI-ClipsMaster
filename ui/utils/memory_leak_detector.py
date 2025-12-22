"""
兼容层：ui.utils.memory_leak_detector

为历史代码提供 start_memory_monitoring/stop_memory_monitoring/
 take_memory_snapshot/generate_memory_report 四个函数接口，
内部基于现有 ui.utils.memory_monitor.MemoryMonitor 实现。
"""
from __future__ import annotations

import time
import threading

from typing import Dict, Any, List, Optional

try:
    from .memory_monitor import MemoryMonitor
except Exception:
    # 极端情况下提供最小空实现，避免运行时崩溃
    class MemoryMonitor:  # type: ignore
        def __init__(self):
            self.monitoring_interval = 5000
            self.last_memory_usage = 0.0
        def start_monitoring(self):
            pass
        def stop_monitoring(self):
            pass
        def _get_memory_usage(self) -> float:
            return 0.0

# 单例监控器与快照缓存
_monitor: Optional[MemoryMonitor] = None
_bg_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None
_interval_sec: int = 60

_snapshots: List[Dict[str, Any]] = []




def _bg_loop():
    m = _ensure_monitor()
    while _stop_event and not _stop_event.is_set():
        try:
            mem = float(m._get_memory_usage())
        except Exception:
            mem = float(getattr(m, "last_memory_usage", 0.0))
        _snapshots.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "memory_mb": mem,
        })
        # 限制快照长度，避免无限增长
        if len(_snapshots) > 500:
            del _snapshots[:-200]
        time.sleep(max(1, _interval_sec))

def _ensure_monitor() -> MemoryMonitor:
    global _monitor
    if _monitor is None:
        _monitor = MemoryMonitor()
    return _monitor


def start_memory_monitoring(interval: int = 60) -> bool:
    """启动后台线程采样内存（interval: 秒）"""
    global _bg_thread, _stop_event, _interval_sec
    try:
        _ensure_monitor()
        _interval_sec = max(1, int(interval))
        if _bg_thread and _bg_thread.is_alive():
            return True
        _stop_event = threading.Event()
        _bg_thread = threading.Thread(target=_bg_loop, name="MemoryLeakDetector", daemon=True)
        _bg_thread.start()
        print(f"[OK] 内存监控线程已启动，间隔: {_interval_sec}s")
        return True
    except Exception as e:
        print(f"[WARN] 启动内存监控失败: {e}")
        return False


def stop_memory_monitoring() -> None:
    """停止后台线程采样"""
    global _bg_thread, _stop_event
    try:
        if _stop_event is not None:
            _stop_event.set()
        if _bg_thread and _bg_thread.is_alive():
            _bg_thread.join(timeout=1.5)
        _bg_thread = None
        _stop_event = None
        print("[OK] 内存监控线程已停止")
    except Exception as e:
        print(f"[WARN] 停止内存监控失败: {e}")


def take_memory_snapshot() -> Dict[str, Any]:
    """拍摄一次内存快照，返回 {time, memory_mb}"""
    m = _ensure_monitor()
    try:
        mem_mb = float(m._get_memory_usage())  # 使用底层查询
    except Exception:
        mem_mb = float(getattr(m, "last_memory_usage", 0.0))
    snap = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "memory_mb": mem_mb,
    }
    _snapshots.append(snap)
    return snap


def generate_memory_report() -> str:
    """生成内存使用文本报告"""
    lines = [
        "===== Memory Usage Report =====",
        f"Snapshots: {len(_snapshots)}",
    ]
    for i, s in enumerate(_snapshots[-50:], 1):  # 限制到最近50条
        lines.append(f"#{i:02d} @ {s['time']} - {s['memory_mb']:.1f} MB")
    if _monitor is not None:
        try:
            current = _monitor._get_memory_usage()
        except Exception:
            current = getattr(_monitor, "last_memory_usage", 0.0)
        lines.append(f"Current: {current:.1f} MB")
    lines.append("===============================")
    return "\n".join(lines)

