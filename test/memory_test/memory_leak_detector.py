"""内存泄露检测器模块

此模块提供内存使用追踪和泄露检测功能，主要特性：
1. 内存使用量监控
2. 泄露趋势分析
3. 对象引用计数追踪
4. 内存占用报告生成
"""

import os
import sys
import time
import gc
import psutil
import threading
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable, Set
from enum import Enum, auto
from datetime import datetime
import tracemalloc
import weakref
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory_leak_detector")

# 确保项目根目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class MemorySnapshotType(Enum):
    """内存快照类型"""
    PROCESS = auto()  # 进程级别内存
    PYTHON = auto()   # Python解释器内存
    TRACEMALLOC = auto()  # tracemalloc跟踪的内存


class MemorySnapshot:
    """内存快照类，记录某一时刻的内存使用情况"""
    
    def __init__(self, snapshot_type: MemorySnapshotType = MemorySnapshotType.PROCESS):
        """初始化内存快照
        
        Args:
            snapshot_type: 快照类型
        """
        self.timestamp = time.time()
        self.datetime = datetime.fromtimestamp(self.timestamp)
        self.snapshot_type = snapshot_type
        
        # 进程信息
        self.process = psutil.Process()
        self.process_memory = self.process.memory_info()
        
        # 系统内存
        self.system_memory = psutil.virtual_memory()
        
        # Python内存
        if snapshot_type == MemorySnapshotType.PYTHON:
            self.gc_counts = gc.get_count()
            self.gc_objects = len(gc.get_objects())
        
        # tracemalloc内存
        if snapshot_type == MemorySnapshotType.TRACEMALLOC:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            self.tracemalloc_snapshot = tracemalloc.take_snapshot()
    
    @property
    def rss_mb(self) -> float:
        """获取RSS内存（MB）"""
        return self.process_memory.rss / (1024 * 1024)
    
    @property
    def vms_mb(self) -> float:
        """获取VMS内存（MB）"""
        return self.process_memory.vms / (1024 * 1024)
    
    @property
    def system_percent(self) -> float:
        """获取系统内存使用百分比"""
        return self.system_memory.percent
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            Dict: 快照数据字典
        """
        data = {
            "timestamp": self.timestamp,
            "datetime": self.datetime.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "type": self.snapshot_type.name,
            "process": {
                "pid": self.process.pid,
                "rss_mb": self.rss_mb,
                "vms_mb": self.vms_mb,
            },
            "system": {
                "total_mb": self.system_memory.total / (1024 * 1024),
                "available_mb": self.system_memory.available / (1024 * 1024),
                "used_mb": self.system_memory.used / (1024 * 1024),
                "percent": self.system_memory.percent
            }
        }
        
        if self.snapshot_type == MemorySnapshotType.PYTHON:
            data["python"] = {
                "gc_counts": self.gc_counts,
                "gc_objects": self.gc_objects
            }
        
        return data


class MemoryLeakAnalyzer:
    """内存泄露分析器，用于检测内存泄露趋势"""
    
    def __init__(
        self, 
        leak_threshold: float = 0.05, 
        window_size: int = 10,
        snapshot_type: MemorySnapshotType = MemorySnapshotType.PROCESS
    ):
        """初始化内存泄露分析器
        
        Args:
            leak_threshold: 内存增长阈值，超过此值认为有泄露（占初始内存的比例）
            window_size: 分析窗口大小（快照数量）
            snapshot_type: 内存快照类型
        """
        self.leak_threshold = leak_threshold
        self.window_size = window_size
        self.snapshot_type = snapshot_type
        self.snapshots: List[MemorySnapshot] = []
        self.is_tracking = False
        self.tracking_thread: Optional[threading.Thread] = None
        self.tracking_interval = 1.0  # 默认1秒
        self._lock = threading.Lock()
        self.callbacks: Dict[str, List[Callable]] = {
            "leak_detected": [],
            "snapshot_taken": []
        }
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """注册事件回调函数
        
        Args:
            event: 事件名称 ('leak_detected' 或 'snapshot_taken')
            callback: 回调函数
        """
        if event not in self.callbacks:
            raise ValueError(f"未知的事件类型: {event}")
        self.callbacks[event].append(callback)
    
    def take_snapshot(self) -> MemorySnapshot:
        """获取当前内存快照
        
        Returns:
            MemorySnapshot: 内存快照对象
        """
        snapshot = MemorySnapshot(self.snapshot_type)
        
        with self._lock:
            self.snapshots.append(snapshot)
            # 保持窗口大小限制
            if len(self.snapshots) > self.window_size:
                self.snapshots.pop(0)
        
        # 触发快照回调
        for callback in self.callbacks["snapshot_taken"]:
            try:
                callback(snapshot)
            except Exception as e:
                logger.error(f"快照回调执行失败: {e}")
        
        return snapshot
    
    def start_tracking(self, interval: float = 1.0) -> None:
        """开始内存跟踪
        
        Args:
            interval: 快照间隔时间（秒）
        """
        if self.is_tracking:
            logger.warning("内存跟踪已经在运行")
            return
        
        self.tracking_interval = interval
        self.is_tracking = True
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True
        )
        self.tracking_thread.start()
        logger.info(f"内存跟踪已启动，间隔: {interval}秒")
    
    def stop_tracking(self) -> None:
        """停止内存跟踪"""
        if not self.is_tracking:
            return
        
        self.is_tracking = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5.0)
        logger.info("内存跟踪已停止")
    
    def _tracking_loop(self) -> None:
        """内存跟踪循环"""
        while self.is_tracking:
            try:
                snapshot = self.take_snapshot()
                leak_detected = self.analyze_leak_trend()
                
                if leak_detected:
                    # 触发泄露回调
                    for callback in self.callbacks["leak_detected"]:
                        try:
                            callback(self.get_leak_info())
                        except Exception as e:
                            logger.error(f"泄露回调执行失败: {e}")
                
                time.sleep(self.tracking_interval)
            except Exception as e:
                logger.error(f"内存跟踪过程中出错: {e}")
                time.sleep(self.tracking_interval)
    
    def analyze_leak_trend(self) -> bool:
        """分析内存泄露趋势
        
        Returns:
            bool: 是否检测到内存泄露趋势
        """
        with self._lock:
            if len(self.snapshots) < 3:
                return False
            
            # 获取内存使用趋势
            memory_values = [snapshot.rss_mb for snapshot in self.snapshots]
            
            # 计算线性回归斜率
            x = np.arange(len(memory_values))
            slope, _ = np.polyfit(x, memory_values, 1)
            
            # 计算增长率
            initial_memory = memory_values[0]
            if initial_memory <= 0:
                return False
            
            growth_rate = slope * len(memory_values) / initial_memory
            
            # 判断是否有泄露趋势
            has_leak_trend = growth_rate > self.leak_threshold
            
            if has_leak_trend:
                logger.warning(f"检测到内存泄露趋势: 增长率 {growth_rate:.2%}, 阈值 {self.leak_threshold:.2%}")
            
            return has_leak_trend
    
    def get_leak_info(self) -> Dict[str, Any]:
        """获取泄露信息
        
        Returns:
            Dict: 泄露信息字典
        """
        with self._lock:
            if len(self.snapshots) < 2:
                return {"error": "快照数量不足"}
            
            first_snapshot = self.snapshots[0]
            last_snapshot = self.snapshots[-1]
            
            memory_values = [snapshot.rss_mb for snapshot in self.snapshots]
            x = np.arange(len(memory_values))
            slope, intercept = np.polyfit(x, memory_values, 1)
            
            return {
                "start_time": first_snapshot.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": last_snapshot.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": last_snapshot.timestamp - first_snapshot.timestamp,
                "initial_memory_mb": first_snapshot.rss_mb,
                "final_memory_mb": last_snapshot.rss_mb,
                "absolute_growth_mb": last_snapshot.rss_mb - first_snapshot.rss_mb,
                "growth_percent": (last_snapshot.rss_mb - first_snapshot.rss_mb) / first_snapshot.rss_mb * 100 if first_snapshot.rss_mb > 0 else 0,
                "trend": {
                    "slope_mb_per_snapshot": slope,
                    "intercept_mb": intercept,
                    "r_squared": np.corrcoef(x, memory_values)[0, 1] ** 2
                }
            }
    
    def save_snapshots(self, filename: str) -> None:
        """保存快照到文件
        
        Args:
            filename: 文件名
        """
        with self._lock:
            data = [snapshot.to_dict() for snapshot in self.snapshots]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"内存快照已保存到 {filename}")
    
    def clear_snapshots(self) -> None:
        """清除所有快照"""
        with self._lock:
            self.snapshots.clear()
        logger.info("所有内存快照已清除")


class ObjectTracker:
    """对象跟踪器，用于跟踪特定类型对象的创建和销毁"""
    
    def __init__(self):
        """初始化对象跟踪器"""
        self.tracked_objects: Dict[str, Dict[int, weakref.ref]] = {}
        self.creation_locations: Dict[str, Dict[int, str]] = {}
    
    def track_type(self, cls_or_name):
        """开始跟踪指定类型的对象
        
        Args:
            cls_or_name: 类型或类型名称
        """
        if isinstance(cls_or_name, type):
            class_name = cls_or_name.__name__
            cls = cls_or_name
        else:
            class_name = cls_or_name
            for obj in gc.get_objects():
                if type(obj).__name__ == class_name:
                    cls = type(obj)
                    break
            else:
                logger.error(f"找不到类型: {class_name}")
                return
        
        if class_name not in self.tracked_objects:
            self.tracked_objects[class_name] = {}
            self.creation_locations[class_name] = {}
        
        # 保存原始__init__方法
        original_init = cls.__init__
        
        # 定义新的__init__方法，用于跟踪对象创建
        def tracking_init(self, *args, **kwargs):
            # 调用原始__init__
            original_init(self, *args, **kwargs)
            
            # 记录对象创建位置
            stack = traceback.extract_stack()
            creation_location = ''.join(traceback.format_list(stack[:-1]))
            
            # 跟踪对象
            obj_id = id(self)
            obj_tracker = sys.modules[ObjectTracker.__module__]
            tracker_instance = getattr(obj_tracker, '_tracker_instance', None)
            
            if tracker_instance:
                tracker_instance._track_object(class_name, self, obj_id, creation_location)
        
        # 替换__init__方法
        cls.__init__ = tracking_init
        logger.info(f"开始跟踪类型: {class_name}")
    
    def _track_object(self, class_name: str, obj, obj_id: int, creation_location: str) -> None:
        """跟踪单个对象
        
        Args:
            class_name: 类名
            obj: 对象
            obj_id: 对象ID
            creation_location: 创建位置
        """
        self.tracked_objects[class_name][obj_id] = weakref.ref(obj, 
            lambda ref, id=obj_id, cls=class_name: self._object_destroyed(cls, id))
        self.creation_locations[class_name][obj_id] = creation_location
    
    def _object_destroyed(self, class_name: str, obj_id: int) -> None:
        """对象被销毁时的回调
        
        Args:
            class_name: 类名
            obj_id: 对象ID
        """
        if obj_id in self.tracked_objects.get(class_name, {}):
            del self.tracked_objects[class_name][obj_id]
        
        if obj_id in self.creation_locations.get(class_name, {}):
            del self.creation_locations[class_name][obj_id]
    
    def get_object_count(self, class_name: Optional[str] = None) -> Dict[str, int]:
        """获取跟踪对象数量
        
        Args:
            class_name: 类名，如果为None则返回所有类型的对象数量
        
        Returns:
            Dict: 类名到对象数量的映射
        """
        if class_name:
            return {class_name: len(self.tracked_objects.get(class_name, {}))}
        else:
            return {cls: len(objs) for cls, objs in self.tracked_objects.items()}
    
    def get_alive_objects(self, class_name: str) -> List[Any]:
        """获取指定类型的存活对象
        
        Args:
            class_name: 类名
        
        Returns:
            List: 存活对象列表
        """
        if class_name not in self.tracked_objects:
            return []
        
        alive_objects = []
        for obj_ref in self.tracked_objects[class_name].values():
            obj = obj_ref()
            if obj is not None:
                alive_objects.append(obj)
        
        return alive_objects
    
    def get_creation_info(self, class_name: str) -> Dict[int, str]:
        """获取对象创建信息
        
        Args:
            class_name: 类名
        
        Returns:
            Dict: 对象ID到创建位置的映射
        """
        if class_name not in self.creation_locations:
            return {}
        
        return self.creation_locations[class_name].copy()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成对象跟踪报告
        
        Returns:
            Dict: 报告数据
        """
        report = {}
        
        for class_name in self.tracked_objects.keys():
            alive_count = len(self.get_alive_objects(class_name))
            report[class_name] = {
                "alive_count": alive_count,
                "creation_locations": {}
            }
            
            # 统计创建位置计数
            location_counts = {}
            for location in self.creation_locations.get(class_name, {}).values():
                location_summary = location.split('\n')[-2] if location else "Unknown"
                location_counts[location_summary] = location_counts.get(location_summary, 0) + 1
            
            report[class_name]["creation_locations"] = location_counts
        
        return report


class MemoryLeakDetector:
    """内存泄露检测器，整合各种内存分析工具"""
    
    # 单例实例
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super(MemoryLeakDetector, cls).__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        leak_threshold: float = 0.05,
        window_size: int = 10,
        snapshot_type: MemorySnapshotType = MemorySnapshotType.PROCESS,
        log_dir: Optional[str] = None
    ):
        """初始化内存泄露检测器
        
        Args:
            leak_threshold: 内存增长阈值
            window_size: 分析窗口大小
            snapshot_type: 内存快照类型
            log_dir: 日志目录
        """
        # 避免重复初始化
        if hasattr(self, "initialized"):
            return
        
        self.leak_analyzer = MemoryLeakAnalyzer(
            leak_threshold=leak_threshold,
            window_size=window_size,
            snapshot_type=snapshot_type
        )
        
        self.object_tracker = ObjectTracker()
        
        # 设置日志目录
        self.log_dir = log_dir or os.path.join("logs", "memory")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 注册事件回调
        self.leak_analyzer.register_callback("leak_detected", self._on_leak_detected)
        
        # 标记为已初始化
        self.initialized = True
        
        # 在模块级别保存跟踪器实例，用于对象跟踪
        sys.modules[self.__class__.__module__]._tracker_instance = self
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """开始内存监控
        
        Args:
            interval: 监控间隔（秒）
        """
        # 启动内存分析器
        self.leak_analyzer.start_tracking(interval)
        logger.info(f"内存泄露监控已启动，间隔: {interval}秒")
    
    def stop_monitoring(self) -> None:
        """停止内存监控"""
        self.leak_analyzer.stop_tracking()
        logger.info("内存泄露监控已停止")
    
    def track_objects_of_type(self, cls_or_name) -> None:
        """跟踪指定类型的对象
        
        Args:
            cls_or_name: 类或类名
        """
        self.object_tracker.track_type(cls_or_name)
    
    def _on_leak_detected(self, leak_info: Dict[str, Any]) -> None:
        """内存泄露检测回调
        
        Args:
            leak_info: 泄露信息
        """
        logger.warning("检测到内存泄露!")
        
        # 生成详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.log_dir, f"leak_report_{timestamp}.json")
        
        report_data = {
            "timestamp": timestamp,
            "leak_info": leak_info,
            "object_tracking": self.object_tracker.generate_report(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "process_id": os.getpid()
            }
        }
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        # 保存内存快照
        snapshots_file = os.path.join(self.log_dir, f"memory_snapshots_{timestamp}.json")
        self.leak_analyzer.save_snapshots(snapshots_file)
        
        logger.info(f"泄露报告已保存到 {report_file}")
    
    def force_gc(self) -> None:
        """强制执行垃圾回收"""
        gc.collect()
        logger.info("已强制执行垃圾回收")
    
    def take_tracemalloc_snapshot(self) -> None:
        """获取tracemalloc内存快照并保存"""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            logger.info("已启动tracemalloc内存跟踪")
        
        snapshot = tracemalloc.take_snapshot()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = os.path.join(self.log_dir, f"tracemalloc_{timestamp}.pickle")
        
        snapshot.dump(snapshot_file)
        logger.info(f"tracemalloc快照已保存到 {snapshot_file}")
        
        # 打印内存占用最多的10个位置
        logger.info("内存占用最多的10个位置:")
        top_stats = snapshot.statistics('lineno')
        for i, stat in enumerate(top_stats[:10], 1):
            logger.info(f"#{i}: {stat}")


if __name__ == "__main__":
    # 简单的命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description="内存泄露检测工具")
    parser.add_argument("--interval", type=float, default=1.0, help="监控间隔（秒）")
    parser.add_argument("--threshold", type=float, default=0.05, help="泄露阈值（比例）")
    parser.add_argument("--window", type=int, default=10, help="分析窗口大小")
    parser.add_argument("--duration", type=int, default=60, help="监控持续时间（秒）")
    parser.add_argument("--log-dir", default="./logs/memory", help="日志目录")
    args = parser.parse_args()
    
    # 创建日志目录
    os.makedirs(args.log_dir, exist_ok=True)
    
    # 初始化检测器
    detector = MemoryLeakDetector(
        leak_threshold=args.threshold,
        window_size=args.window,
        log_dir=args.log_dir
    )
    
    try:
        # 启动监控
        detector.start_monitoring(args.interval)
        
        # 运行指定时间
        logger.info(f"内存泄露检测已启动，将运行 {args.duration} 秒")
        time.sleep(args.duration)
    except KeyboardInterrupt:
        logger.info("检测被用户中断")
    finally:
        # 停止监控
        detector.stop_monitoring()
        
        # 保存最终快照
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshots_file = os.path.join(args.log_dir, f"final_snapshots_{timestamp}.json")
        detector.leak_analyzer.save_snapshots(snapshots_file)
        
        logger.info("内存泄露检测已完成") 