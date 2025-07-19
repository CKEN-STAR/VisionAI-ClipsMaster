"""
高级性能监控系统
提供详细的性能分析、内存优化和CPU监控功能
"""

import os
import gc
import sys
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import deque
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: float
    memory_mb: float
    memory_percent: float
    cpu_percent: float
    thread_count: int
    handle_count: int
    gc_objects: int
    process_time: float

@dataclass
class MemoryAnalysis:
    """内存分析结果"""
    current_mb: float
    peak_mb: float
    average_mb: float
    growth_rate: float  # MB/minute
    gc_collections: int
    large_objects: int
    memory_leaks_detected: bool
    optimization_suggestions: List[str]

@dataclass
class CPUAnalysis:
    """CPU分析结果"""
    current_percent: float
    average_percent: float
    peak_percent: float
    thread_efficiency: float
    bottleneck_functions: List[str]
    optimization_suggestions: List[str]

class AdvancedPerformanceMonitor(QObject):
    """高级性能监控器"""
    
    performance_updated = pyqtSignal(dict)  # 性能数据更新
    memory_warning = pyqtSignal(str, float)  # 内存警告
    cpu_warning = pyqtSignal(str, float)  # CPU警告
    optimization_suggested = pyqtSignal(list)  # 优化建议
    
    def __init__(self, max_history: int = 1000):
        super().__init__()
        self.max_history = max_history
        self.snapshots: deque = deque(maxlen=max_history)
        self.is_monitoring = False
        self.monitor_timer = QTimer()
        self.monitor_interval = 1000  # 1秒
        
        # 性能阈值
        self.memory_warning_threshold = 300  # MB
        self.memory_critical_threshold = 500  # MB
        self.cpu_warning_threshold = 80  # %
        self.cpu_critical_threshold = 95  # %
        
        # 优化器
        self.memory_optimizer = MemoryOptimizer()
        self.cpu_optimizer = CPUOptimizer()
        
        # 设置监控定时器
        self.monitor_timer.timeout.connect(self._collect_performance_data)
        
        # 获取进程对象
        try:
            self.process = psutil.Process()
        except Exception as e:
            print(f"[WARN] 无法获取进程信息: {e}")
            self.process = None
    
    def start_monitoring(self):
        """开始性能监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_timer.start(self.monitor_interval)
        print(f"[OK] 性能监控已启动，间隔: {self.monitor_interval}ms")
    
    def stop_monitoring(self):
        """停止性能监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self.monitor_timer.stop()
        print("[OK] 性能监控已停止")
    
    def set_monitor_interval(self, interval_ms: int):
        """设置监控间隔"""
        self.monitor_interval = max(100, interval_ms)  # 最小100ms
        if self.is_monitoring:
            self.monitor_timer.setInterval(self.monitor_interval)
    
    def _collect_performance_data(self):
        """收集性能数据"""
        try:
            if not self.process:
                return
            
            # 收集基础性能数据
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = self.process.memory_percent()
            
            # CPU使用率（需要一定时间间隔）
            cpu_percent = self.process.cpu_percent()
            
            # 线程和句柄数
            thread_count = self.process.num_threads()
            try:
                handle_count = self.process.num_handles() if hasattr(self.process, 'num_handles') else 0
            except:
                handle_count = 0
            
            # 垃圾回收信息
            gc_objects = len(gc.get_objects())
            
            # 进程运行时间
            process_time = time.time() - self.process.create_time()
            
            # 创建性能快照
            snapshot = PerformanceSnapshot(
                timestamp=time.time(),
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                cpu_percent=cpu_percent,
                thread_count=thread_count,
                handle_count=handle_count,
                gc_objects=gc_objects,
                process_time=process_time
            )
            
            # 添加到历史记录
            self.snapshots.append(snapshot)
            
            # 检查警告条件
            self._check_performance_warnings(snapshot)
            
            # 发送性能更新信号
            self.performance_updated.emit(asdict(snapshot))
            
        except Exception as e:
            print(f"[WARN] 性能数据收集失败: {e}")
    
    def _check_performance_warnings(self, snapshot: PerformanceSnapshot):
        """检查性能警告"""
        # 内存警告
        if snapshot.memory_mb > self.memory_critical_threshold:
            self.memory_warning.emit("内存使用严重超标", snapshot.memory_mb)
        elif snapshot.memory_mb > self.memory_warning_threshold:
            self.memory_warning.emit("内存使用过高", snapshot.memory_mb)
        
        # CPU警告
        if snapshot.cpu_percent > self.cpu_critical_threshold:
            self.cpu_warning.emit("CPU使用率严重过高", snapshot.cpu_percent)
        elif snapshot.cpu_percent > self.cpu_warning_threshold:
            self.cpu_warning.emit("CPU使用率过高", snapshot.cpu_percent)
    
    def get_memory_analysis(self) -> MemoryAnalysis:
        """获取内存分析"""
        if not self.snapshots:
            return MemoryAnalysis(0, 0, 0, 0, 0, 0, False, [])
        
        # 计算内存统计
        memory_values = [s.memory_mb for s in self.snapshots]
        current_mb = memory_values[-1]
        peak_mb = max(memory_values)
        average_mb = sum(memory_values) / len(memory_values)
        
        # 计算增长率（MB/分钟）
        growth_rate = 0
        if len(self.snapshots) > 1:
            time_span = self.snapshots[-1].timestamp - self.snapshots[0].timestamp
            if time_span > 0:
                memory_growth = memory_values[-1] - memory_values[0]
                growth_rate = (memory_growth / time_span) * 60  # 转换为每分钟
        
        # 垃圾回收统计
        gc_collections = gc.get_count()[0] if gc.get_count() else 0
        
        # 大对象检测
        large_objects = self._count_large_objects()
        
        # 内存泄漏检测
        memory_leaks_detected = self._detect_memory_leaks()
        
        # 生成优化建议
        optimization_suggestions = self._generate_memory_suggestions(
            current_mb, peak_mb, average_mb, growth_rate, large_objects
        )
        
        return MemoryAnalysis(
            current_mb=current_mb,
            peak_mb=peak_mb,
            average_mb=average_mb,
            growth_rate=growth_rate,
            gc_collections=gc_collections,
            large_objects=large_objects,
            memory_leaks_detected=memory_leaks_detected,
            optimization_suggestions=optimization_suggestions
        )
    
    def get_cpu_analysis(self) -> CPUAnalysis:
        """获取CPU分析"""
        if not self.snapshots:
            return CPUAnalysis(0, 0, 0, 0, [], [])
        
        # 计算CPU统计
        cpu_values = [s.cpu_percent for s in self.snapshots]
        current_percent = cpu_values[-1]
        average_percent = sum(cpu_values) / len(cpu_values)
        peak_percent = max(cpu_values)
        
        # 线程效率计算
        thread_counts = [s.thread_count for s in self.snapshots]
        avg_threads = sum(thread_counts) / len(thread_counts)
        thread_efficiency = average_percent / max(1, avg_threads)
        
        # 瓶颈函数检测（简化版）
        bottleneck_functions = self._detect_cpu_bottlenecks()
        
        # 生成优化建议
        optimization_suggestions = self._generate_cpu_suggestions(
            current_percent, average_percent, peak_percent, thread_efficiency
        )
        
        return CPUAnalysis(
            current_percent=current_percent,
            average_percent=average_percent,
            peak_percent=peak_percent,
            thread_efficiency=thread_efficiency,
            bottleneck_functions=bottleneck_functions,
            optimization_suggestions=optimization_suggestions
        )
    
    def _count_large_objects(self) -> int:
        """统计大对象数量"""
        try:
            large_objects = 0
            for obj in gc.get_objects():
                if hasattr(obj, '__sizeof__'):
                    size = obj.__sizeof__()
                    if size > 1024 * 1024:  # 大于1MB的对象
                        large_objects += 1
            return large_objects
        except Exception:
            return 0
    
    def _detect_memory_leaks(self) -> bool:
        """检测内存泄漏"""
        if len(self.snapshots) < 10:
            return False
        
        # 简单的内存泄漏检测：连续增长
        recent_snapshots = list(self.snapshots)[-10:]
        memory_trend = []
        
        for i in range(1, len(recent_snapshots)):
            memory_trend.append(
                recent_snapshots[i].memory_mb - recent_snapshots[i-1].memory_mb
            )
        
        # 如果连续增长且增长率较高，可能存在内存泄漏
        positive_growth = sum(1 for x in memory_trend if x > 0)
        return positive_growth > len(memory_trend) * 0.8
    
    def _detect_cpu_bottlenecks(self) -> List[str]:
        """检测CPU瓶颈"""
        # 这里可以集成更复杂的性能分析工具
        # 目前返回一些常见的瓶颈点
        bottlenecks = []
        
        if len(self.snapshots) > 5:
            recent_cpu = [s.cpu_percent for s in list(self.snapshots)[-5:]]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            
            if avg_cpu > 50:
                bottlenecks.append("高CPU使用率检测到")
            
            # 检查线程数是否过多
            recent_threads = [s.thread_count for s in list(self.snapshots)[-5:]]
            avg_threads = sum(recent_threads) / len(recent_threads)
            
            if avg_threads > 20:
                bottlenecks.append("线程数过多")
        
        return bottlenecks
    
    def _generate_memory_suggestions(self, current: float, peak: float, 
                                   average: float, growth_rate: float, 
                                   large_objects: int) -> List[str]:
        """生成内存优化建议"""
        suggestions = []
        
        if current > 200:
            suggestions.append("当前内存使用过高，建议执行垃圾回收")
        
        if growth_rate > 5:  # 每分钟增长超过5MB
            suggestions.append("检测到内存快速增长，可能存在内存泄漏")
        
        if large_objects > 10:
            suggestions.append(f"检测到{large_objects}个大对象，考虑优化数据结构")
        
        if peak - average > 100:
            suggestions.append("内存使用波动较大，建议优化内存分配策略")
        
        if not suggestions:
            suggestions.append("内存使用正常")
        
        return suggestions
    
    def _generate_cpu_suggestions(self, current: float, average: float, 
                                peak: float, thread_efficiency: float) -> List[str]:
        """生成CPU优化建议"""
        suggestions = []
        
        if current > 80:
            suggestions.append("当前CPU使用率过高，建议检查后台任务")
        
        if average > 50:
            suggestions.append("平均CPU使用率较高，考虑优化算法或使用多线程")
        
        if thread_efficiency < 5:
            suggestions.append("线程效率较低，建议优化线程使用策略")
        
        if peak > 90:
            suggestions.append("检测到CPU峰值过高，建议优化性能瓶颈")
        
        if not suggestions:
            suggestions.append("CPU使用正常")
        
        return suggestions
    
    def optimize_memory(self) -> Dict[str, Any]:
        """执行内存优化"""
        return self.memory_optimizer.optimize()
    
    def optimize_cpu(self) -> Dict[str, Any]:
        """执行CPU优化"""
        return self.cpu_optimizer.optimize()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        memory_analysis = self.get_memory_analysis()
        cpu_analysis = self.get_cpu_analysis()
        
        return {
            'timestamp': time.time(),
            'monitoring_duration': len(self.snapshots) * (self.monitor_interval / 1000),
            'data_points': len(self.snapshots),
            'memory_analysis': asdict(memory_analysis),
            'cpu_analysis': asdict(cpu_analysis),
            'current_snapshot': asdict(self.snapshots[-1]) if self.snapshots else None,
            'recommendations': self._generate_overall_recommendations(memory_analysis, cpu_analysis)
        }
    
    def _generate_overall_recommendations(self, memory_analysis: MemoryAnalysis, 
                                        cpu_analysis: CPUAnalysis) -> List[str]:
        """生成总体优化建议"""
        recommendations = []
        
        # 内存优化建议
        if memory_analysis.current_mb > 200:
            recommendations.append("🔧 执行内存优化以降低内存使用")
        
        # CPU优化建议
        if cpu_analysis.average_percent > 30:
            recommendations.append("⚡ 优化CPU密集型操作")
        
        # 综合建议
        if memory_analysis.growth_rate > 3 and cpu_analysis.average_percent > 40:
            recommendations.append("🚨 系统负载较高，建议全面优化")
        
        if not recommendations:
            recommendations.append("✅ 系统性能良好，无需特别优化")
        
        return recommendations

class MemoryOptimizer:
    """内存优化器"""
    
    def optimize(self) -> Dict[str, Any]:
        """执行内存优化"""
        start_time = time.time()
        
        try:
            # 获取优化前的内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # 执行垃圾回收
            collected_objects = gc.collect()
            
            # 清理模块缓存
            modules_cleared = self._clear_module_cache()
            
            # 优化Python内部缓存
            cache_cleared = self._clear_python_caches()
            
            # 获取优化后的内存使用
            memory_after = process.memory_info().rss / 1024 / 1024
            memory_freed = memory_before - memory_after
            
            optimization_time = time.time() - start_time
            
            return {
                'success': True,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_freed_mb': memory_freed,
                'collected_objects': collected_objects,
                'modules_cleared': modules_cleared,
                'cache_cleared': cache_cleared,
                'optimization_time': optimization_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'optimization_time': time.time() - start_time
            }
    
    def _clear_module_cache(self) -> int:
        """清理模块缓存"""
        try:
            initial_count = len(sys.modules)
            
            # 清理一些可以安全清理的模块
            modules_to_clear = []
            for module_name in list(sys.modules.keys()):
                if any(pattern in module_name for pattern in ['__pycache__', 'test_', '_test']):
                    modules_to_clear.append(module_name)
            
            for module_name in modules_to_clear:
                if module_name in sys.modules:
                    del sys.modules[module_name]
            
            return len(modules_to_clear)
        except Exception:
            return 0
    
    def _clear_python_caches(self) -> int:
        """清理Python内部缓存"""
        try:
            cache_count = 0
            
            # 清理正则表达式缓存
            import re
            re.purge()
            cache_count += 1
            
            # 清理编译缓存
            import py_compile
            if hasattr(py_compile, 'cache_clear'):
                py_compile.cache_clear()
                cache_count += 1
            
            return cache_count
        except Exception:
            return 0

class CPUOptimizer:
    """CPU优化器"""
    
    def optimize(self) -> Dict[str, Any]:
        """执行CPU优化"""
        start_time = time.time()
        
        try:
            # 获取优化前的CPU使用
            process = psutil.Process()
            cpu_before = process.cpu_percent()
            
            # 优化线程优先级
            thread_optimized = self._optimize_thread_priority()
            
            # 清理后台任务
            tasks_cleaned = self._clean_background_tasks()
            
            # 优化Python解释器设置
            interpreter_optimized = self._optimize_interpreter()
            
            # 等待一段时间测量CPU使用变化
            time.sleep(1)
            cpu_after = process.cpu_percent()
            cpu_improvement = cpu_before - cpu_after
            
            optimization_time = time.time() - start_time
            
            return {
                'success': True,
                'cpu_before_percent': cpu_before,
                'cpu_after_percent': cpu_after,
                'cpu_improvement_percent': cpu_improvement,
                'thread_optimized': thread_optimized,
                'tasks_cleaned': tasks_cleaned,
                'interpreter_optimized': interpreter_optimized,
                'optimization_time': optimization_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'optimization_time': time.time() - start_time
            }
    
    def _optimize_thread_priority(self) -> bool:
        """优化线程优先级"""
        try:
            # 在Windows上设置进程优先级
            if os.name == 'nt':
                import subprocess
                subprocess.run(['wmic', 'process', 'where', f'processid={os.getpid()}', 
                              'CALL', 'setpriority', '32768'], 
                              capture_output=True, check=False)
            return True
        except Exception:
            return False
    
    def _clean_background_tasks(self) -> int:
        """清理后台任务"""
        try:
            # 这里可以添加清理特定后台任务的逻辑
            # 目前只是一个占位符
            return 0
        except Exception:
            return 0
    
    def _optimize_interpreter(self) -> bool:
        """优化Python解释器"""
        try:
            # 设置一些Python优化选项
            sys.setcheckinterval(1000)  # 减少线程切换频率
            return True
        except Exception:
            return False

class PerformanceVisualizationWidget(QObject):
    """性能可视化组件"""

    def __init__(self, monitor: AdvancedPerformanceMonitor):
        super().__init__()
        self.monitor = monitor
        self.charts_data = {
            'memory': deque(maxlen=100),
            'cpu': deque(maxlen=100),
            'threads': deque(maxlen=100)
        }

        # 连接监控器信号
        self.monitor.performance_updated.connect(self._update_charts_data)

    def _update_charts_data(self, performance_data: Dict[str, Any]):
        """更新图表数据"""
        timestamp = performance_data.get('timestamp', time.time())

        self.charts_data['memory'].append({
            'timestamp': timestamp,
            'value': performance_data.get('memory_mb', 0)
        })

        self.charts_data['cpu'].append({
            'timestamp': timestamp,
            'value': performance_data.get('cpu_percent', 0)
        })

        self.charts_data['threads'].append({
            'timestamp': timestamp,
            'value': performance_data.get('thread_count', 0)
        })

    def get_memory_chart_data(self) -> List[Dict[str, float]]:
        """获取内存图表数据"""
        return list(self.charts_data['memory'])

    def get_cpu_chart_data(self) -> List[Dict[str, float]]:
        """获取CPU图表数据"""
        return list(self.charts_data['cpu'])

    def get_threads_chart_data(self) -> List[Dict[str, float]]:
        """获取线程图表数据"""
        return list(self.charts_data['threads'])

__all__ = [
    'PerformanceSnapshot',
    'MemoryAnalysis',
    'CPUAnalysis',
    'AdvancedPerformanceMonitor',
    'MemoryOptimizer',
    'CPUOptimizer',
    'PerformanceVisualizationWidget'
]
