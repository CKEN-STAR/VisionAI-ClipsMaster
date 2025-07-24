#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存限制测试模块

此模块在4GB内存限制下测试系统的稳定性和性能，
验证内存使用控制、内存泄漏检测、长时间运行稳定性等关键指标。
"""

import os
import sys
import gc
import time
import psutil
import logging
import threading
import unittest
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.video_processor import VideoProcessor
from src.core.ai_content_analyzer import AIContentAnalyzer
from src.core.viral_script_generator import ViralScriptGenerator
from src.utils.log_handler import LogHandler
from src.utils.memory_monitor import MemoryMonitor

logger = logging.getLogger(__name__)


@dataclass
class MemoryUsageSnapshot:
    """内存使用快照"""
    timestamp: float
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    memory_percent: float
    process_memory_mb: float
    process_memory_percent: float


@dataclass
class MemoryConstraintTestResult:
    """内存限制测试结果"""
    test_name: str
    test_duration: float
    max_memory_usage_mb: float
    average_memory_usage_mb: float
    memory_peak_count: int
    memory_leak_detected: bool
    memory_leak_rate_mb_per_hour: float
    oom_events: int
    gc_collections: int
    memory_snapshots: List[MemoryUsageSnapshot]
    performance_impact: Dict[str, float]
    stability_score: float
    success: bool
    error_messages: List[str]
    warnings: List[str]


class MemoryConstraintTester:
    """内存限制测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化内存限制测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 内存监控配置
        self.memory_config = self.config.get('performance_monitoring', {}).get('memory_constraints', {})
        self.max_memory_gb = self.memory_config.get('max_memory_gb', 4.0)
        self.warning_threshold_gb = self.memory_config.get('warning_threshold_gb', 3.5)
        self.monitoring_interval = self.memory_config.get('monitoring_interval_seconds', 1)
        self.leak_threshold = self.memory_config.get('memory_leak_threshold_mb_per_hour', 10)
        
        # 初始化组件
        self.video_processor = VideoProcessor()
        self.ai_analyzer = AIContentAnalyzer()
        self.viral_generator = ViralScriptGenerator()
        self.memory_monitor = MemoryMonitor()
        
        # 监控状态
        self.monitoring_active = False
        self.memory_snapshots = []
        self.monitoring_thread = None
        
        # 测试结果存储
        self.test_results = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/real_world_validation/real_world_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'test_environment': {'log_level': 'INFO'},
            'performance_monitoring': {
                'memory_constraints': {
                    'max_memory_gb': 4.0,
                    'warning_threshold_gb': 3.5,
                    'monitoring_interval_seconds': 1,
                    'memory_leak_threshold_mb_per_hour': 10
                }
            }
        }
    
    def test_memory_constrained_processing(self, video_files: List[str], 
                                         test_duration_hours: float = 2.0) -> MemoryConstraintTestResult:
        """
        测试内存限制下的处理能力
        
        Args:
            video_files: 测试视频文件列表
            test_duration_hours: 测试持续时间（小时）
            
        Returns:
            MemoryConstraintTestResult: 内存限制测试结果
        """
        test_name = "memory_constrained_processing"
        start_time = time.time()
        
        self.logger.info(f"开始内存限制测试，时长: {test_duration_hours}小时")
        
        # 启动内存监控
        self._start_memory_monitoring()
        
        error_messages = []
        warnings = []
        oom_events = 0
        gc_collections_start = self._get_gc_stats()
        
        try:
            # 设置内存限制（如果支持）
            self._set_memory_limit(self.max_memory_gb)
            
            # 执行持续的视频处理任务
            end_time = start_time + (test_duration_hours * 3600)
            processing_count = 0
            
            while time.time() < end_time:
                try:
                    # 选择一个视频文件进行处理
                    video_file = video_files[processing_count % len(video_files)]
                    
                    if os.path.exists(video_file):
                        self.logger.debug(f"处理视频 #{processing_count + 1}: {video_file}")
                        
                        # 执行视频处理
                        processing_result = self._process_video_with_memory_monitoring(video_file)
                        
                        if not processing_result['success']:
                            error_messages.extend(processing_result.get('errors', []))
                            
                            # 检查是否为内存不足错误
                            if self._is_oom_error(processing_result.get('errors', [])):
                                oom_events += 1
                                self.logger.warning(f"检测到内存不足事件 #{oom_events}")
                        
                        processing_count += 1
                        
                        # 检查内存使用情况
                        current_memory = self._get_current_memory_usage()
                        if current_memory > self.warning_threshold_gb * 1024:
                            warnings.append(f"内存使用超过警告阈值: {current_memory:.1f}MB")
                            
                            # 强制垃圾回收
                            gc.collect()
                        
                        # 短暂休息以避免过度负载
                        time.sleep(1)
                    
                    else:
                        self.logger.warning(f"视频文件不存在: {video_file}")
                        time.sleep(5)  # 等待更长时间
                
                except Exception as e:
                    error_messages.append(f"处理异常: {str(e)}")
                    if self._is_oom_error([str(e)]):
                        oom_events += 1
                    
                    # 异常后进行内存清理
                    gc.collect()
                    time.sleep(2)
            
            # 停止内存监控
            self._stop_memory_monitoring()
            
            # 计算测试结果
            test_duration = time.time() - start_time
            gc_collections_end = self._get_gc_stats()
            gc_collections = gc_collections_end - gc_collections_start
            
            # 分析内存使用情况
            memory_analysis = self._analyze_memory_usage()
            
            # 检测内存泄漏
            memory_leak_analysis = self._detect_memory_leak(test_duration)
            
            # 计算稳定性评分
            stability_score = self._calculate_stability_score(
                oom_events, memory_analysis, memory_leak_analysis
            )
            
            success = (
                oom_events == 0 and
                memory_analysis['max_memory_mb'] <= self.max_memory_gb * 1024 and
                not memory_leak_analysis['leak_detected'] and
                stability_score >= 0.8
            )
            
            result = MemoryConstraintTestResult(
                test_name=test_name,
                test_duration=test_duration,
                max_memory_usage_mb=memory_analysis['max_memory_mb'],
                average_memory_usage_mb=memory_analysis['avg_memory_mb'],
                memory_peak_count=memory_analysis['peak_count'],
                memory_leak_detected=memory_leak_analysis['leak_detected'],
                memory_leak_rate_mb_per_hour=memory_leak_analysis['leak_rate_mb_per_hour'],
                oom_events=oom_events,
                gc_collections=gc_collections,
                memory_snapshots=self.memory_snapshots.copy(),
                performance_impact=memory_analysis.get('performance_impact', {}),
                stability_score=stability_score,
                success=success,
                error_messages=error_messages,
                warnings=warnings
            )
            
            self.test_results.append(result)
            self.logger.info(f"内存限制测试完成，稳定性评分: {stability_score:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"内存限制测试异常: {str(e)}")
            
            # 确保停止监控
            self._stop_memory_monitoring()
            
            return MemoryConstraintTestResult(
                test_name=test_name,
                test_duration=time.time() - start_time,
                max_memory_usage_mb=0,
                average_memory_usage_mb=0,
                memory_peak_count=0,
                memory_leak_detected=False,
                memory_leak_rate_mb_per_hour=0,
                oom_events=oom_events,
                gc_collections=0,
                memory_snapshots=[],
                performance_impact={},
                stability_score=0.0,
                success=False,
                error_messages=[str(e)],
                warnings=[]
            )
    
    def _start_memory_monitoring(self):
        """启动内存监控"""
        self.monitoring_active = True
        self.memory_snapshots = []
        
        def monitor_memory():
            while self.monitoring_active:
                try:
                    snapshot = self._take_memory_snapshot()
                    self.memory_snapshots.append(snapshot)
                    
                    # 检查内存使用是否超限
                    if snapshot.used_memory_mb > self.max_memory_gb * 1024:
                        self.logger.warning(f"内存使用超限: {snapshot.used_memory_mb:.1f}MB > {self.max_memory_gb * 1024}MB")
                    
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    self.logger.error(f"内存监控异常: {str(e)}")
                    break
        
        self.monitoring_thread = threading.Thread(target=monitor_memory, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.debug("内存监控已启动")
    
    def _stop_memory_monitoring(self):
        """停止内存监控"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self.logger.debug(f"内存监控已停止，收集了 {len(self.memory_snapshots)} 个快照")
    
    def _take_memory_snapshot(self) -> MemoryUsageSnapshot:
        """获取内存使用快照"""
        try:
            # 系统内存信息
            system_memory = psutil.virtual_memory()
            
            # 当前进程内存信息
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return MemoryUsageSnapshot(
                timestamp=time.time(),
                total_memory_mb=system_memory.total / (1024 * 1024),
                used_memory_mb=system_memory.used / (1024 * 1024),
                available_memory_mb=system_memory.available / (1024 * 1024),
                memory_percent=system_memory.percent,
                process_memory_mb=process_memory.rss / (1024 * 1024),
                process_memory_percent=process.memory_percent()
            )
            
        except Exception as e:
            self.logger.error(f"获取内存快照失败: {str(e)}")
            return MemoryUsageSnapshot(
                timestamp=time.time(),
                total_memory_mb=0, used_memory_mb=0, available_memory_mb=0,
                memory_percent=0, process_memory_mb=0, process_memory_percent=0
            )
    
    def _get_current_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        try:
            return psutil.virtual_memory().used / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _set_memory_limit(self, limit_gb: float):
        """设置内存限制（如果支持）"""
        try:
            import resource
            
            # 设置虚拟内存限制
            limit_bytes = int(limit_gb * 1024 * 1024 * 1024)
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
            
            self.logger.info(f"设置内存限制: {limit_gb}GB")
            
        except Exception as e:
            self.logger.warning(f"无法设置内存限制: {str(e)}")
    
    def _process_video_with_memory_monitoring(self, video_file: str) -> Dict[str, Any]:
        """在内存监控下处理视频"""
        try:
            memory_before = self._get_current_memory_usage()
            
            # 执行视频处理
            processing_start = time.time()
            
            # 1. 视频信息获取
            video_info = self.video_processor.get_video_info(video_file)
            
            # 2. AI内容分析
            analysis_result = self.ai_analyzer.analyze_content(video_file)
            
            # 3. 爆款脚本生成
            if analysis_result.get('success', False):
                script_result = self.viral_generator.generate_viral_script(
                    content_analysis=analysis_result.get('analysis', {}),
                    target_style='viral',
                    compression_ratio=0.5
                )
            else:
                script_result = {'success': False}
            
            processing_time = time.time() - processing_start
            memory_after = self._get_current_memory_usage()
            memory_delta = memory_after - memory_before
            
            # 强制垃圾回收
            gc.collect()
            memory_after_gc = self._get_current_memory_usage()
            memory_freed = memory_after - memory_after_gc
            
            success = (
                video_info is not None and
                analysis_result.get('success', False) and
                script_result.get('success', False)
            )
            
            return {
                'success': success,
                'processing_time': processing_time,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_delta_mb': memory_delta,
                'memory_freed_mb': memory_freed,
                'video_info': video_info,
                'errors': [] if success else ['处理失败']
            }
            
        except MemoryError as e:
            return {
                'success': False,
                'errors': [f"内存不足: {str(e)}"],
                'memory_error': True
            }
        except Exception as e:
            return {
                'success': False,
                'errors': [f"处理异常: {str(e)}"],
                'memory_error': False
            }
    
    def _is_oom_error(self, error_messages: List[str]) -> bool:
        """检查是否为内存不足错误"""
        oom_keywords = ['memory', 'oom', 'out of memory', 'cannot allocate', 'memoryerror']
        
        for error in error_messages:
            error_lower = error.lower()
            if any(keyword in error_lower for keyword in oom_keywords):
                return True
        
        return False
    
    def _get_gc_stats(self) -> int:
        """获取垃圾回收统计"""
        try:
            return sum(gc.get_stats()[i]['collections'] for i in range(len(gc.get_stats())))
        except Exception:
            return 0
    
    def _analyze_memory_usage(self) -> Dict[str, Any]:
        """分析内存使用情况"""
        if not self.memory_snapshots:
            return {
                'max_memory_mb': 0,
                'avg_memory_mb': 0,
                'min_memory_mb': 0,
                'peak_count': 0,
                'performance_impact': {}
            }
        
        used_memory_values = [snapshot.used_memory_mb for snapshot in self.memory_snapshots]
        process_memory_values = [snapshot.process_memory_mb for snapshot in self.memory_snapshots]
        
        max_memory = max(used_memory_values)
        avg_memory = sum(used_memory_values) / len(used_memory_values)
        min_memory = min(used_memory_values)
        
        # 计算内存峰值次数（超过警告阈值的次数）
        warning_threshold_mb = self.warning_threshold_gb * 1024
        peak_count = sum(1 for memory in used_memory_values if memory > warning_threshold_mb)
        
        # 计算性能影响
        max_process_memory = max(process_memory_values)
        avg_process_memory = sum(process_memory_values) / len(process_memory_values)
        
        performance_impact = {
            'max_process_memory_mb': max_process_memory,
            'avg_process_memory_mb': avg_process_memory,
            'memory_efficiency': avg_process_memory / max_memory if max_memory > 0 else 0
        }
        
        return {
            'max_memory_mb': max_memory,
            'avg_memory_mb': avg_memory,
            'min_memory_mb': min_memory,
            'peak_count': peak_count,
            'performance_impact': performance_impact
        }
    
    def _detect_memory_leak(self, test_duration_seconds: float) -> Dict[str, Any]:
        """检测内存泄漏"""
        if len(self.memory_snapshots) < 10:
            return {
                'leak_detected': False,
                'leak_rate_mb_per_hour': 0.0,
                'confidence': 0.0
            }
        
        # 使用线性回归检测内存增长趋势
        timestamps = [snapshot.timestamp for snapshot in self.memory_snapshots]
        process_memory_values = [snapshot.process_memory_mb for snapshot in self.memory_snapshots]
        
        # 简化的线性回归
        n = len(timestamps)
        sum_x = sum(timestamps)
        sum_y = sum(process_memory_values)
        sum_xy = sum(t * m for t, m in zip(timestamps, process_memory_values))
        sum_x2 = sum(t * t for t in timestamps)
        
        # 计算斜率（内存增长率）
        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        else:
            slope = 0
        
        # 将斜率转换为每小时的内存增长率
        leak_rate_mb_per_hour = slope * 3600  # 斜率单位是MB/秒
        
        # 判断是否存在内存泄漏
        leak_detected = leak_rate_mb_per_hour > self.leak_threshold
        
        # 计算置信度（基于数据点数量和趋势一致性）
        confidence = min(1.0, len(self.memory_snapshots) / 100)
        
        return {
            'leak_detected': leak_detected,
            'leak_rate_mb_per_hour': leak_rate_mb_per_hour,
            'confidence': confidence,
            'slope': slope
        }
    
    def _calculate_stability_score(self, oom_events: int, memory_analysis: Dict[str, Any], 
                                 memory_leak_analysis: Dict[str, Any]) -> float:
        """计算稳定性评分"""
        try:
            score = 1.0
            
            # OOM事件扣分
            if oom_events > 0:
                score -= min(0.5, oom_events * 0.1)
            
            # 内存峰值扣分
            peak_count = memory_analysis.get('peak_count', 0)
            if peak_count > 0:
                score -= min(0.2, peak_count * 0.01)
            
            # 内存泄漏扣分
            if memory_leak_analysis.get('leak_detected', False):
                leak_rate = memory_leak_analysis.get('leak_rate_mb_per_hour', 0)
                score -= min(0.3, leak_rate / 100)
            
            # 内存使用效率加分
            efficiency = memory_analysis.get('performance_impact', {}).get('memory_efficiency', 0)
            if efficiency > 0.8:
                score += 0.1
            
            return max(0.0, score)
            
        except Exception:
            return 0.0


class TestMemoryConstraints(unittest.TestCase):
    """内存限制测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = MemoryConstraintTester()
        
        # 设置测试视频文件
        cls.test_videos = [
            "tests/real_world_validation/test_data/videos/short_video_5min.mp4",
            "tests/real_world_validation/test_data/videos/medium_video_15min.mov"
        ]
        
        # 过滤存在的视频文件
        cls.existing_videos = [v for v in cls.test_videos if os.path.exists(v)]
    
    def test_short_term_memory_constraint(self):
        """测试短期内存限制"""
        if not self.existing_videos:
            self.skipTest("没有可用的测试视频文件")
        
        # 30分钟测试
        result = self.tester.test_memory_constrained_processing(
            self.existing_videos, test_duration_hours=0.5
        )
        
        self.assertTrue(result.success, "短期内存限制测试应该成功")
        self.assertEqual(result.oom_events, 0, "不应该有内存不足事件")
        self.assertLessEqual(result.max_memory_usage_mb, 4096, "最大内存使用应该≤4GB")
        self.assertFalse(result.memory_leak_detected, "不应该检测到内存泄漏")
    
    def test_memory_usage_monitoring(self):
        """测试内存使用监控"""
        if not self.existing_videos:
            self.skipTest("没有可用的测试视频文件")
        
        # 10分钟监控测试
        result = self.tester.test_memory_constrained_processing(
            self.existing_videos, test_duration_hours=1/6
        )
        
        self.assertGreater(len(result.memory_snapshots), 0, "应该收集到内存快照")
        self.assertGreater(result.stability_score, 0.7, "稳定性评分应该良好")
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        if not self.existing_videos:
            self.skipTest("没有可用的测试视频文件")
        
        # 1小时测试用于检测内存泄漏
        result = self.tester.test_memory_constrained_processing(
            self.existing_videos, test_duration_hours=1.0
        )
        
        # 内存泄漏率应该在可接受范围内
        self.assertLessEqual(result.memory_leak_rate_mb_per_hour, 10, 
                           f"内存泄漏率应该≤10MB/小时: {result.memory_leak_rate_mb_per_hour:.2f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
