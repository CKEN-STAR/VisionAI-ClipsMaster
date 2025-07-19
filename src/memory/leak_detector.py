#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存泄漏追踪系统 - VisionAI-ClipsMaster

此模块提供轻量级内存泄漏检测功能，专为低内存设备(4GB RAM无GPU)优化。
系统使用tracemalloc跟踪内存分配，并通过连续快照比较检测泄漏趋势。
"""

import os
import sys
import time
import gc
import logging
import threading
import tracemalloc
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
import json
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

class LeakTracker:
    """
    内存泄漏追踪器
    
    基于tracemalloc实现的轻量级内存泄漏检测系统。
    专为低内存设备优化，能够检测连续测试中内存增长趋势。
    """
    
    def __init__(self, 
                 leak_threshold_percent: float = 2.0,
                 consecutive_leaks_threshold: int = 3,
                 top_stats_limit: int = 20,
                 auto_cleanup: bool = True,
                 log_dir: Optional[str] = None):
        """
        初始化内存泄漏追踪器
        
        Args:
            leak_threshold_percent: 视为泄漏的内存增长百分比阈值
            consecutive_leaks_threshold: 连续多少次检测到增长才视为泄漏
            top_stats_limit: 跟踪的最大内存分配点数量
            auto_cleanup: 检测到泄漏时是否自动尝试清理内存
            log_dir: 日志保存目录，如果为None则使用默认位置
        """
        self.leak_threshold = leak_threshold_percent / 100.0
        self.consecutive_threshold = consecutive_leaks_threshold
        self.top_stats_limit = top_stats_limit
        self.auto_cleanup = auto_cleanup
        
        # 设置日志目录
        if log_dir is None:
            self.log_dir = Path.home() / ".visionai" / "logs" / "memory"
        else:
            self.log_dir = Path(log_dir)
        
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 跟踪状态
        self.is_tracking = False
        self.tracking_thread = None
        self.stop_event = threading.Event()
        
        # 历史记录
        self.snapshots = []
        self.snapshot_stats = []
        self.leak_locations = {}
        self.consecutive_leaks = 0
        self.last_check_time = 0
        
        # 监测到的泄漏
        self.detected_leaks = []
        
        # 初始化tracemalloc（如果尚未初始化）
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            logger.info("已启动tracemalloc内存跟踪")
    
    def track_allocations(self) -> List[Dict[str, Any]]:
        """
        使用tracemalloc进行内存分配追踪
        
        Returns:
            检测到的内存泄漏列表
        """
        # 使用tracemalloc进行内存分配追踪
        tracemalloc.start()
        
        # 执行测试用例
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        # 筛选出大于1MB的内存分配
        return [stat for stat in top_stats if stat.size_diff > 1e6]  # >1MB可疑
    
    def take_snapshot(self) -> Tuple[Any, List]:
        """
        获取内存快照及统计信息
        
        Returns:
            快照对象和统计信息列表
        """
        # 强制执行垃圾回收
        gc.collect()
        
        # 获取tracemalloc快照
        snapshot = tracemalloc.take_snapshot()
        
        # 获取统计信息，按行号分组
        top_stats = snapshot.statistics('lineno')
        
        # 限制数量
        top_stats = top_stats[:self.top_stats_limit]
        
        # 记录时间
        timestamp = time.time()
        
        # 保存快照历史
        self.snapshots.append((timestamp, snapshot))
        self.snapshot_stats.append(top_stats)
        
        # 保持历史长度适中
        if len(self.snapshots) > 10:
            self.snapshots.pop(0)
            self.snapshot_stats.pop(0)
        
        return snapshot, top_stats
    
    def analyze_snapshot(self, top_stats) -> List[Dict[str, Any]]:
        """
        分析快照统计信息，检测可能的泄漏
        
        Args:
            top_stats: 统计信息列表
            
        Returns:
            可能的泄漏信息列表
        """
        leaks = []
        
        # 如果之前没有快照，无法比较
        if len(self.snapshot_stats) < 2:
            return leaks
        
        # 获取上一个统计信息
        prev_stats = self.snapshot_stats[-2]
        
        # 比较当前与上一个快照
        for curr_stat in top_stats:
            # 查找上一个快照中相同位置的统计信息
            prev_stat = next((s for s in prev_stats if s.traceback.frame.filename == curr_stat.traceback.frame.filename 
                              and s.traceback.frame.lineno == curr_stat.traceback.frame.lineno), None)
            
            if prev_stat:
                # 计算增长量和增长率
                size_diff = curr_stat.size - prev_stat.size
                growth_rate = size_diff / prev_stat.size if prev_stat.size > 0 else 0
                
                # 如果增长率超过阈值，可能是泄漏
                if growth_rate > self.leak_threshold:
                    location = f"{curr_stat.traceback.frame.filename}:{curr_stat.traceback.frame.lineno}"
                    
                    # 更新连续泄漏计数
                    if location in self.leak_locations:
                        self.leak_locations[location] += 1
                    else:
                        self.leak_locations[location] = 1
                    
                    # 如果连续多次检测到，确认为泄漏
                    if self.leak_locations[location] >= self.consecutive_threshold:
                        leak_info = {
                            "location": location,
                            "current_size": curr_stat.size,
                            "previous_size": prev_stat.size,
                            "size_diff": size_diff,
                            "growth_rate": growth_rate,
                            "count": curr_stat.count,
                            "consecutive_detections": self.leak_locations[location],
                            "timestamp": time.time()
                        }
                        
                        leaks.append(leak_info)
                        
                        # 记录检测到的泄漏
                        self.detected_leaks.append(leak_info)
                        
                        # 记录日志
                        logger.warning(f"检测到内存泄漏: {location}, "
                                      f"当前大小: {curr_stat.size/1024/1024:.2f}MB, "
                                      f"增长: {size_diff/1024/1024:.2f}MB "
                                      f"({growth_rate*100:.1f}%)")
                        
                        # 如果启用了自动清理，尝试清理内存
                        if self.auto_cleanup:
                            self._try_cleanup()
        
        # 如果有泄漏，增加连续泄漏计数
        if leaks:
            self.consecutive_leaks += 1
        else:
            self.consecutive_leaks = 0
        
        return leaks
    
    def _try_cleanup(self) -> None:
        """尝试清理内存泄漏"""
        # 执行完整的垃圾回收
        pre_count = len(gc.get_objects())
        
        # 运行完整的垃圾回收循环
        for i in range(3):
            gc.collect(i)
        
        # 获取清理后的对象数量
        post_count = len(gc.get_objects())
        cleaned = pre_count - post_count
        
        if cleaned > 0:
            logger.info(f"内存清理: 释放了 {cleaned} 个对象")
        else:
            logger.warning("内存清理未能释放对象，可能存在真正的泄漏")
    
    def start_tracking(self, interval_seconds: float = 60.0) -> None:
        """
        开始定期跟踪内存分配
        
        Args:
            interval_seconds: 检查间隔（秒）
        """
        if self.is_tracking:
            logger.warning("内存泄漏跟踪已在运行")
            return
        
        self.is_tracking = True
        self.stop_event.clear()
        
        def tracking_loop():
            logger.info(f"开始内存泄漏跟踪，间隔: {interval_seconds}秒")
            
            while not self.stop_event.is_set():
                try:
                    # 获取并分析快照
                    snapshot, top_stats = self.take_snapshot()
                    leaks = self.analyze_snapshot(top_stats)
                    
                    # 如果检测到严重泄漏，保存详细报告
                    if self.consecutive_leaks >= self.consecutive_threshold:
                        self.save_leak_report()
                    
                    # 等待下一次检查
                    self.stop_event.wait(interval_seconds)
                    
                except Exception as e:
                    logger.error(f"内存泄漏跟踪出错: {e}")
                    # 出错后短暂暂停再继续
                    self.stop_event.wait(5.0)
            
            logger.info("内存泄漏跟踪已停止")
        
        # 启动跟踪线程
        self.tracking_thread = threading.Thread(
            target=tracking_loop,
            daemon=True,
            name="LeakTracker"
        )
        self.tracking_thread.start()
    
    def stop_tracking(self) -> None:
        """停止内存泄漏跟踪"""
        if not self.is_tracking:
            return
            
        self.stop_event.set()
        if self.tracking_thread:
            self.tracking_thread.join(timeout=5.0)
            
        self.is_tracking = False
    
    def check_for_leaks(self, force_gc: bool = True) -> List[Dict[str, Any]]:
        """
        主动检查内存泄漏
        
        Args:
            force_gc: 是否强制执行垃圾回收
            
        Returns:
            检测到的泄漏列表
        """
        if force_gc:
            gc.collect()
            
        # 获取并分析快照
        snapshot, top_stats = self.take_snapshot()
        leaks = self.analyze_snapshot(top_stats)
        
        return leaks

    def check_leaks(self, force_gc: bool = True) -> List[Dict[str, Any]]:
        """检查内存泄漏的别名方法"""
        return self.check_for_leaks(force_gc)

    def save_leak_report(self) -> str:
        """
        保存泄漏报告到文件
        
        Returns:
            报告文件路径
        """
        # 创建报告数据
        report = {
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "detected_leaks": self.detected_leaks,
            "consecutive_leaks": self.consecutive_leaks,
            "memory_info": {
                "process": self._get_process_memory(),
                "gc_stats": {
                    "objects": len(gc.get_objects()),
                    "garbage": len(gc.garbage),
                    "collections": gc.get_count()
                }
            }
        }
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.log_dir / f"leak_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"泄漏报告已保存: {report_file}")
        return str(report_file)
    
    def _get_process_memory(self) -> Dict[str, Any]:
        """获取进程内存信息"""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()

            return {
                "rss_mb": mem_info.rss / (1024 * 1024),
                "vms_mb": mem_info.vms / (1024 * 1024),
                "percent": process.memory_percent(),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, 'num_fds') else None
            }
        except ImportError:
            logger.warning("psutil不可用，使用基础内存信息")
            # 使用基础的内存信息
            import resource
            try:
                usage = resource.getrusage(resource.RUSAGE_SELF)
                # 在Windows上，ru_maxrss是以KB为单位，在Unix上是以KB为单位
                max_rss_mb = usage.ru_maxrss / 1024 if os.name != 'nt' else usage.ru_maxrss / 1024
                return {
                    "rss_mb": max_rss_mb,
                    "vms_mb": max_rss_mb,  # 近似值
                    "percent": 0.0,  # 无法计算百分比
                    "num_threads": 1,  # 近似值
                    "num_fds": None
                }
            except Exception:
                return {
                    "rss_mb": 0.0,
                    "vms_mb": 0.0,
                    "percent": 0.0,
                    "num_threads": 1,
                    "num_fds": None
                }
        except Exception as e:
            logger.error(f"获取进程内存信息失败: {e}")
            return {
                "rss_mb": 0.0,
                "vms_mb": 0.0,
                "percent": 0.0,
                "num_threads": 1,
                "num_fds": None
            }
    
    def get_leak_summary(self) -> Dict[str, Any]:
        """
        获取泄漏摘要信息
        
        Returns:
            泄漏摘要字典
        """
        return {
            "detected_leaks_count": len(self.detected_leaks),
            "consecutive_leaks": self.consecutive_leaks,
            "unique_locations": len(set(leak["location"] for leak in self.detected_leaks)),
            "last_check_time": self.last_check_time,
            "is_tracking": self.is_tracking,
            "top_leaks": sorted(self.detected_leaks, 
                               key=lambda x: x["size_diff"], 
                               reverse=True)[:5] if self.detected_leaks else []
        }

    def reset(self) -> None:
        """重置跟踪状态和历史记录"""
        # 停止跟踪
        self.stop_tracking()
        
        # 清理历史记录
        self.snapshots = []
        self.snapshot_stats = []
        self.leak_locations = {}
        self.consecutive_leaks = 0
        self.detected_leaks = []
        
        # 执行垃圾回收
        gc.collect()
        
        # 重启tracemalloc
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        tracemalloc.start()
        
        logger.info("内存泄漏跟踪器已重置")


# 全局单例
_leak_tracker = None

def get_leak_tracker() -> LeakTracker:
    """获取内存泄漏跟踪器的全局实例"""
    global _leak_tracker
    if _leak_tracker is None:
        _leak_tracker = LeakTracker()
    return _leak_tracker


def start_leak_tracking(interval_seconds: float = 300.0) -> None:
    """
    启动内存泄漏跟踪
    
    Args:
        interval_seconds: 检查间隔（秒）
    """
    tracker = get_leak_tracker()
    tracker.start_tracking(interval_seconds)


def stop_leak_tracking() -> None:
    """停止内存泄漏跟踪"""
    tracker = get_leak_tracker()
    tracker.stop_tracking()


def check_for_leaks() -> List[Dict[str, Any]]:
    """
    检查内存泄漏
    
    Returns:
        检测到的泄漏列表
    """
    tracker = get_leak_tracker()
    return tracker.check_for_leaks()


def save_leak_report() -> str:
    """
    保存泄漏报告
    
    Returns:
        报告文件路径
    """
    tracker = get_leak_tracker()
    return tracker.save_leak_report()


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试泄漏检测器
    logger.info("测试内存泄漏跟踪器")
    
    # 创建跟踪器
    tracker = LeakTracker(
        leak_threshold_percent=2.0,
        consecutive_leaks_threshold=3
    )
    
    # 进行初始泄漏检测
    leaks = tracker.check_for_leaks()
    
    # 创建一些临时对象模拟潜在泄漏
    logger.info("创建临时对象...")
    temp_data = []
    for i in range(5):
        # 每个大约1MB
        temp_data.append(bytearray(1024 * 1024))
    
    # 再次检测
    logger.info("检测泄漏...")
    leaks = tracker.check_for_leaks()
    
    if leaks:
        logger.info(f"检测到 {len(leaks)} 个潜在泄漏")
    else:
        logger.info("未检测到泄漏")
    
    # 清理
    temp_data.clear()
    gc.collect()
    
    logger.info("测试完成") 