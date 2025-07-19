"""分片加载监控模块

此模块提供分片加载监控功能，包括：
1. 跟踪分片加载次数和耗时
2. 识别热点分片（频繁加载的分片）
3. 统计加载性能和内存使用
4. 检测加载异常和失败
5. 提供优化建议
6. 可视化加载模式
"""

import time
import heapq
import statistics
from enum import Enum
from typing import Dict, List, Tuple, Set, Optional, Any, Callable, Union
from collections import defaultdict, Counter, deque
from datetime import datetime, timedelta
import json
import threading
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from src.sharding.cache_manager import ShardManager


class LoadStatus(Enum):
    """加载状态枚举"""
    SUCCESS = "success"          # 加载成功
    FAILED = "failed"            # 加载失败
    CACHE_HIT = "cache_hit"      # 缓存命中
    FROM_CACHE = "from_cache"    # 从缓存加载


class ShardMonitor:
    """分片加载监控器
    
    跟踪分片加载性能和模式，提供优化建议。
    """
    
    def __init__(
        self,
        shard_manager: Optional[ShardManager] = None,
        history_size: int = 1000,
        hot_threshold: int = 5,
        save_path: Optional[str] = None
    ):
        """初始化分片监控器
        
        Args:
            shard_manager: 分片管理器实例
            history_size: 历史记录最大条数
            hot_threshold: 判定为热点分片的最小加载次数
            save_path: 监控数据保存路径
        """
        self.shard_manager = shard_manager
        self.history_size = history_size
        self.hot_threshold = hot_threshold
        self.save_path = save_path
        
        # 分片加载次数计数
        self.load_times = defaultdict(list)
        
        # 分片加载历史记录
        self.load_history = deque(maxlen=history_size)
        
        # 加载失败计数
        self.failed_loads = Counter()
        
        # 依赖加载统计
        self.dependency_loads = defaultdict(int)
        
        # 当前正在加载的分片
        self.currently_loading = set()
        
        # 加载间隔统计 (分片ID -> 上次加载时间)
        self.last_load_time = {}
        
        # 同时加载的最大分片数
        self.max_concurrent_loads = 0
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 是否已经集成到分片管理器
        self._integrated = False
        
        # 如果提供了分片管理器，自动集成
        if shard_manager:
            self.integrate_with_shard_manager(shard_manager)
        
        logger.info(f"分片监控器初始化完成")
    
    def integrate_with_shard_manager(self, shard_manager: ShardManager) -> None:
        """与分片管理器集成
        
        通过替换分片管理器的加载回调函数来监控分片加载
        
        Args:
            shard_manager: 分片管理器实例
        """
        if self._integrated:
            logger.warning("监控器已经集成到分片管理器")
            return
        
        self.shard_manager = shard_manager
        
        # 保存原始的回调函数
        original_load_callback = shard_manager.shard_cache.load_callback
        original_unload_callback = shard_manager.shard_cache.unload_callback
        
        # 创建新的加载回调函数
        def monitored_load_callback(shard_id: str) -> Any:
            """添加监控的分片加载回调"""
            # 记录加载开始
            start_time = time.time()
            
            with self._lock:
                self.currently_loading.add(shard_id)
                self.max_concurrent_loads = max(
                    self.max_concurrent_loads, 
                    len(self.currently_loading)
                )
            
            try:
                # 调用原始加载函数
                result = original_load_callback(shard_id)
                
                # 记录加载结束
                duration = time.time() - start_time
                
                # 记录加载结果
                if result is not None:
                    self.record_load(
                        shard_id, 
                        duration, 
                        status=LoadStatus.SUCCESS,
                        size_bytes=getattr(result, 'nbytes', 0)
                    )
                else:
                    self.record_load(
                        shard_id, 
                        duration, 
                        status=LoadStatus.FAILED
                    )
                    self.failed_loads[shard_id] += 1
                
                return result
            
            except Exception as e:
                # 记录加载失败
                duration = time.time() - start_time
                self.record_load(
                    shard_id, 
                    duration, 
                    status=LoadStatus.FAILED,
                    error=str(e)
                )
                self.failed_loads[shard_id] += 1
                
                # 重新抛出异常
                raise
            
            finally:
                # 无论成功失败，移除正在加载标记
                with self._lock:
                    self.currently_loading.discard(shard_id)
        
        # 创建新的卸载回调函数
        def monitored_unload_callback(shard_id: str) -> bool:
            """添加监控的分片卸载回调"""
            # 记录卸载时间
            timestamp = time.time()
            
            # 调用原始卸载函数
            result = original_unload_callback(shard_id)
            
            # 记录卸载事件
            if result:
                self.record_unload(shard_id, timestamp)
            
            return result
        
        # 替换分片缓存的回调函数
        shard_manager.shard_cache.load_callback = monitored_load_callback
        shard_manager.shard_cache.unload_callback = monitored_unload_callback
        
        # 包装分片管理器的load_shard方法，以监控依赖加载
        original_load_shard = shard_manager.load_shard
        
        def monitored_load_shard(shard_id: str, recursive: bool = True) -> Any:
            """添加监控的load_shard方法"""
            # 如果需要递归加载依赖
            if recursive and shard_manager.metadata:
                # 获取分片元数据
                shard_meta = shard_manager.metadata.get_shard(shard_id)
                if shard_meta:
                    # 记录依赖加载
                    dependencies = shard_meta.get("depends_on", [])
                    for dep_id in dependencies:
                        self.dependency_loads[dep_id] += 1
            
            return original_load_shard(shard_id, recursive)
        
        # 替换分片管理器的load_shard方法
        shard_manager.load_shard = monitored_load_shard
        
        self._integrated = True
        logger.info("分片监控器已集成到分片管理器")
    
    def record_load(
        self, 
        shard_id: str, 
        duration: float,
        status: LoadStatus = LoadStatus.SUCCESS,
        size_bytes: int = 0,
        error: str = None
    ) -> None:
        """记录分片加载
        
        Args:
            shard_id: 分片ID
            duration: 加载耗时（秒）
            status: 加载状态
            size_bytes: 分片大小（字节）
            error: 如果加载失败，错误信息
        """
        timestamp = time.time()
        
        with self._lock:
            # 记录加载时间
            self.load_times[shard_id].append(duration)
            
            # 记录加载间隔
            if shard_id in self.last_load_time:
                interval = timestamp - self.last_load_time[shard_id]
            else:
                interval = None
            
            self.last_load_time[shard_id] = timestamp
            
            # 记录加载历史
            record = {
                "shard_id": shard_id,
                "timestamp": timestamp,
                "duration": duration,
                "status": status.value,
                "size_bytes": size_bytes,
                "interval": interval,
                "error": error
            }
            
            self.load_history.append(record)
        
        # 定期保存监控数据
        if self.save_path and len(self.load_history) % 50 == 0:
            self._save_monitoring_data()
    
    def record_unload(self, shard_id: str, timestamp: float) -> None:
        """记录分片卸载
        
        Args:
            shard_id: 分片ID
            timestamp: 卸载时间戳
        """
        with self._lock:
            # 记录卸载历史
            record = {
                "shard_id": shard_id,
                "timestamp": timestamp,
                "action": "unload"
            }
            
            self.load_history.append(record)
    
    def get_hot_shards(self, limit: int = 5) -> List[Tuple[str, int]]:
        """获取热点分片
        
        按加载次数获取最频繁访问的分片
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            List[Tuple[str, int]]: (分片ID, 加载次数) 列表
        """
        with self._lock:
            # 计算每个分片的加载次数
            counts = {shard_id: len(times) for shard_id, times in self.load_times.items()}
            
            # 过滤掉低于阈值的分片
            hot_shards = {
                shard_id: count for shard_id, count in counts.items()
                if count >= self.hot_threshold
            }
            
            # 返回排序后的热点分片
            return heapq.nlargest(limit, hot_shards.items(), key=lambda x: x[1])
    
    def get_slow_loading_shards(self, limit: int = 5) -> List[Tuple[str, float]]:
        """获取加载缓慢的分片
        
        返回平均加载时间最长的分片
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            List[Tuple[str, float]]: (分片ID, 平均加载时间) 列表
        """
        with self._lock:
            # 计算每个分片的平均加载时间
            avg_times = {}
            for shard_id, times in self.load_times.items():
                if times:  # 确保分片有加载记录
                    avg_times[shard_id] = sum(times) / len(times)
            
            # 返回排序后的结果
            return heapq.nlargest(limit, avg_times.items(), key=lambda x: x[1])
    
    def get_loading_pattern(self, shard_id: str) -> Dict[str, Any]:
        """获取分片的加载模式分析
        
        分析特定分片的加载频率、时间分布等
        
        Args:
            shard_id: 分片ID
            
        Returns:
            Dict[str, Any]: 加载模式分析结果
        """
        with self._lock:
            if shard_id not in self.load_times:
                return {"error": f"没有 {shard_id} 的加载记录"}
            
            times = self.load_times[shard_id]
            
            # 基本统计
            count = len(times)
            total_time = sum(times)
            avg_time = total_time / count if count > 0 else 0
            
            # 更多统计指标
            try:
                median_time = statistics.median(times) if times else 0
                min_time = min(times) if times else 0
                max_time = max(times) if times else 0
                std_dev = statistics.stdev(times) if len(times) > 1 else 0
            except statistics.StatisticsError:
                median_time = min_time = max_time = std_dev = 0
            
            # 依赖加载统计
            dependency_load_count = self.dependency_loads.get(shard_id, 0)
            
            # 失败统计
            failed_count = self.failed_loads.get(shard_id, 0)
            
            # 间隔分析
            intervals = []
            loads = []
            
            for record in self.load_history:
                if record.get("shard_id") == shard_id and record.get("interval") is not None:
                    intervals.append(record["interval"])
                    loads.append(record["timestamp"])
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            # 重复加载模式
            repeat_loads = len(intervals)
            
            return {
                "shard_id": shard_id,
                "load_count": count,
                "failed_loads": failed_count,
                "as_dependency_count": dependency_load_count,
                "total_load_time": total_time,
                "avg_load_time": avg_time,
                "median_load_time": median_time,
                "min_load_time": min_time,
                "max_load_time": max_time,
                "std_dev": std_dev,
                "repeat_loads": repeat_loads,
                "avg_interval": avg_interval
            }
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """获取监控统计信息
        
        Returns:
            Dict[str, Any]: 监控统计信息
        """
        with self._lock:
            # 计算总加载次数
            total_loads = sum(len(times) for times in self.load_times.values())
            
            # 计算总加载时间
            total_load_time = sum(
                sum(times) for times in self.load_times.values()
            )
            
            # 计算总失败次数
            total_fails = sum(self.failed_loads.values())
            
            # 计算失败率
            fail_rate = total_fails / total_loads if total_loads > 0 else 0
            
            # 最大并发加载
            max_concurrent = self.max_concurrent_loads
            
            # 计算不同分片的数量
            unique_shards = len(self.load_times)
            
            # 未使用但作为依赖加载的分片
            only_as_dependency = {
                shard_id for shard_id in self.dependency_loads
                if shard_id not in self.load_times
            }
            
            return {
                "total_loads": total_loads,
                "total_load_time": total_load_time,
                "unique_shards": unique_shards,
                "failed_loads": total_fails,
                "fail_rate": fail_rate,
                "max_concurrent_loads": max_concurrent,
                "dependency_only_shards": len(only_as_dependency),
                "history_size": len(self.load_history)
            }
    
    def report_hot_shards(self, limit: int = 3) -> List[Tuple[str, int]]:
        """报告热点分片
        
        Args:
            limit: 最多返回的热点分片数量
            
        Returns:
            List[Tuple[str, int]]: (分片ID, 加载次数) 列表
        """
        hot_shards = self.get_hot_shards(limit=limit)
        
        if not hot_shards:
            logger.info("没有检测到热点分片")
        else:
            logger.info(f"检测到 {len(hot_shards)} 个热点分片:")
            for shard_id, count in hot_shards:
                avg_time = sum(self.load_times[shard_id]) / count
                logger.info(f"  {shard_id}: 加载 {count} 次, 平均耗时 {avg_time:.4f}秒")
        
        return hot_shards
    
    def generate_optimization_suggestions(self) -> List[str]:
        """生成优化建议
        
        基于监控数据生成分片加载优化建议
        
        Returns:
            List[str]: 优化建议列表
        """
        suggestions = []
        
        # 获取热点分片
        hot_shards = self.get_hot_shards(limit=10)
        if hot_shards:
            hot_shard_ids = [shard_id for shard_id, _ in hot_shards]
            suggestions.append(f"考虑预加载热点分片: {', '.join(hot_shard_ids[:3])}")
            
            # 检查热点分片是否作为依赖频繁加载
            for shard_id, count in hot_shards:
                if self.dependency_loads.get(shard_id, 0) > count / 2:
                    suggestions.append(
                        f"分片 {shard_id} 频繁作为依赖加载，"
                        "考虑调整依赖关系或合并相关分片"
                    )
        
        # 获取加载最慢的分片
        slow_shards = self.get_slow_loading_shards(limit=5)
        if slow_shards:
            slow_shard_ids = [f"{shard_id} ({time:.4f}秒)" for shard_id, time in slow_shards]
            suggestions.append(f"优化加载缓慢的分片: {', '.join(slow_shard_ids[:3])}")
        
        # 检查加载失败
        if sum(self.failed_loads.values()) > 0:
            failed_shards = [
                f"{shard_id} ({count}次)" 
                for shard_id, count in self.failed_loads.most_common(3)
            ]
            suggestions.append(f"修复加载失败的分片: {', '.join(failed_shards)}")
        
        # 检查并发加载
        if self.max_concurrent_loads > 3:
            suggestions.append(
                f"检测到大量并发加载 ({self.max_concurrent_loads}个分片)，"
                "考虑优化加载顺序减少内存压力"
            )
        
        # 检查频繁重复加载的分片
        repeat_loads = []
        for shard_id, times in self.load_times.items():
            pattern = self.get_loading_pattern(shard_id)
            if pattern.get("repeat_loads", 0) > 5 and pattern.get("avg_interval", float('inf')) < 60:
                repeat_loads.append(shard_id)
        
        if repeat_loads:
            suggestions.append(
                f"分片 {', '.join(repeat_loads[:3])} 短时间内频繁重复加载，"
                "考虑增大缓存大小或调整卸载策略"
            )
        
        return suggestions
    
    def visualize_load_pattern(self, output_path: Optional[str] = None) -> None:
        """可视化分片加载模式
        
        生成加载时间和频率分布图
        
        Args:
            output_path: 图表保存路径，如果为None则显示图表
        """
        try:
            plt.figure(figsize=(12, 8))
            
            # 准备数据
            shard_ids = []
            load_counts = []
            avg_times = []
            
            for shard_id, times in self.load_times.items():
                if times:
                    shard_ids.append(shard_id)
                    load_counts.append(len(times))
                    avg_times.append(sum(times) / len(times))
            
            # 排序数据
            sorted_indices = sorted(range(len(shard_ids)), key=lambda i: load_counts[i], reverse=True)
            shard_ids = [shard_ids[i] for i in sorted_indices]
            load_counts = [load_counts[i] for i in sorted_indices]
            avg_times = [avg_times[i] for i in sorted_indices]
            
            # 绘制加载次数柱状图
            plt.subplot(2, 1, 1)
            plt.bar(shard_ids[:10], load_counts[:10], color='skyblue')
            plt.title('分片加载频率')
            plt.xlabel('分片ID')
            plt.ylabel('加载次数')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 绘制平均加载时间柱状图
            plt.subplot(2, 1, 2)
            plt.bar(shard_ids[:10], avg_times[:10], color='salmon')
            plt.title('分片平均加载时间')
            plt.xlabel('分片ID')
            plt.ylabel('平均时间 (秒)')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 保存或显示图表
            if output_path:
                plt.savefig(output_path)
                logger.info(f"加载模式图表已保存到: {output_path}")
            else:
                plt.show()
            
        except Exception as e:
            logger.error(f"生成图表失败: {str(e)}")
        finally:
            plt.close()
    
    def _save_monitoring_data(self) -> None:
        """保存监控数据到文件"""
        if not self.save_path:
            return
        
        try:
            # 创建保存目录
            save_dir = Path(self.save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 准备要保存的数据
            data = {
                "timestamp": time.time(),
                "load_times": {k: list(v) for k, v in self.load_times.items()},
                "failed_loads": dict(self.failed_loads),
                "dependency_loads": dict(self.dependency_loads),
                "stats": self.get_monitor_stats(),
                "hot_shards": self.get_hot_shards(limit=10),
                "slow_shards": [
                    {"shard_id": shard_id, "avg_time": avg_time}
                    for shard_id, avg_time in self.get_slow_loading_shards(limit=10)
                ],
                "suggestions": self.generate_optimization_suggestions()
            }
            
            # 转换为JSON并保存
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"监控数据已保存到: {self.save_path}")
            
        except Exception as e:
            logger.error(f"保存监控数据失败: {str(e)}")
    
    def clear_history(self) -> None:
        """清除历史记录"""
        with self._lock:
            self.load_times.clear()
            self.load_history.clear()
            self.failed_loads.clear()
            self.dependency_loads.clear()
            self.last_load_time.clear()
            self.max_concurrent_loads = 0
        
        logger.info("监控历史记录已清除")


def create_shard_monitor(
    shard_manager: ShardManager,
    save_path: Optional[str] = None,
    hot_threshold: int = 5
) -> ShardMonitor:
    """创建分片监控器
    
    便捷函数，创建并配置分片监控器
    
    Args:
        shard_manager: 分片管理器实例
        save_path: 监控数据保存路径
        hot_threshold: 热点分片阈值
        
    Returns:
        ShardMonitor: 配置好的分片监控器实例
    """
    monitor = ShardMonitor(
        shard_manager=None,  # 避免在构造函数中自动集成
        hot_threshold=hot_threshold,
        save_path=save_path
    )
    
    # 手动集成
    monitor.integrate_with_shard_manager(shard_manager)
    
    return monitor 