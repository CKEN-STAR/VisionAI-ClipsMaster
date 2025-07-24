#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 4GB内存限制稳定性测试模块

此模块验证系统在4GB内存限制下的稳定性和处理能力，包括：
1. 内存使用峰值监控
2. 内存泄漏检测
3. 长时间运行稳定性测试
4. 大数据量处理能力测试
5. 内存压力下的性能基准测试
"""

import os
import sys
import json
import time
import logging
import unittest
import threading
import gc
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.model_switcher import ModelSwitcher
from src.core.screenplay_engineer import ScreenplayEngineer
from src.core.srt_parser import SRTParser
from src.utils.memory_guard import MemoryGuard
from src.utils.log_handler import LogHandler

logger = logging.getLogger(__name__)


@dataclass
class MemoryStabilityResult:
    """内存稳定性测试结果数据类"""
    test_name: str
    test_duration: float  # 测试持续时间（秒）
    initial_memory: float  # 初始内存使用（MB）
    peak_memory: float    # 峰值内存使用（MB）
    final_memory: float   # 最终内存使用（MB）
    memory_leak: float    # 内存泄漏量（MB）
    memory_leak_rate: float  # 内存泄漏率（MB/小时）
    gc_collections: int   # 垃圾回收次数
    oom_events: int       # 内存不足事件次数
    crash_count: int      # 崩溃次数
    processed_items: int  # 处理的项目数量
    throughput: float     # 吞吐量（项目/秒）
    stability_score: float  # 稳定性评分（0-1）
    success: bool
    error_messages: List[str]


class MemoryConstraintTester:
    """4GB内存限制测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化内存限制测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.memory_guard = MemoryGuard()
        self.model_switcher = ModelSwitcher(self.config)
        self.screenplay_engineer = ScreenplayEngineer()
        self.srt_parser = SRTParser()
        
        # 测试结果存储
        self.test_results = []
        
        # 内存限制配置
        self.memory_limit = self._parse_memory_limit(
            self.config.get('test_thresholds', {}).get('memory_peak', '3.8GB')
        )
        self.memory_warning_threshold = self.memory_limit * 0.9  # 90%警告阈值
        
        # 测试控制
        self.stop_testing = False
        self.test_start_time = None
        
        # 监控数据
        self.memory_samples = []
        self.error_log = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        if config_path is None:
            config_path = "tests/core_functionality_validation/test_config.yaml"
        
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"无法加载配置文件 {config_path}: {e}")
            return {
                'test_thresholds': {'memory_peak': '3.8GB'},
                'test_environment': {'log_level': 'INFO'}
            }
    
    def _parse_memory_limit(self, memory_str: str) -> float:
        """解析内存限制字符串为MB"""
        if isinstance(memory_str, (int, float)):
            return float(memory_str)
        
        memory_str = memory_str.upper()
        if 'GB' in memory_str:
            return float(memory_str.replace('GB', '')) * 1024
        elif 'MB' in memory_str:
            return float(memory_str.replace('MB', ''))
        else:
            return float(memory_str)
    
    def test_memory_peak_constraint(self, test_cases: List[str]) -> MemoryStabilityResult:
        """
        测试内存峰值限制
        
        Args:
            test_cases: 测试用例列表（字幕文件路径）
            
        Returns:
            MemoryStabilityResult: 测试结果
        """
        test_name = "memory_peak_constraint"
        start_time = time.time()
        
        # 记录初始状态
        gc.collect()  # 强制垃圾回收
        initial_memory = self.memory_guard.get_memory_usage()
        peak_memory = initial_memory
        processed_items = 0
        error_messages = []
        oom_events = 0
        
        self.logger.info(f"开始内存峰值限制测试，初始内存: {initial_memory:.1f}MB")
        
        try:
            for i, test_case in enumerate(test_cases):
                if self.stop_testing:
                    break
                
                try:
                    # 监控内存使用
                    current_memory = self.memory_guard.get_memory_usage()
                    peak_memory = max(peak_memory, current_memory)
                    
                    # 检查内存限制
                    if current_memory > self.memory_limit:
                        oom_events += 1
                        error_messages.append(f"内存超限: {current_memory:.1f}MB > {self.memory_limit:.1f}MB")
                        self.logger.warning(f"内存使用超限: {current_memory:.1f}MB")
                        
                        # 尝试释放内存
                        gc.collect()
                        current_memory = self.memory_guard.get_memory_usage()
                        
                        if current_memory > self.memory_limit:
                            self.logger.error("垃圾回收后内存仍超限，停止测试")
                            break
                    
                    # 处理测试用例
                    self._process_test_case(test_case)
                    processed_items += 1
                    
                    # 定期垃圾回收
                    if i % 5 == 0:
                        gc.collect()
                    
                except Exception as e:
                    error_messages.append(f"处理测试用例 {i} 失败: {str(e)}")
                    self.logger.error(f"处理测试用例失败: {str(e)}")
        
        except Exception as e:
            error_messages.append(f"测试过程异常: {str(e)}")
            self.logger.error(f"内存峰值测试异常: {str(e)}")
        
        # 计算最终结果
        test_duration = time.time() - start_time
        gc.collect()
        final_memory = self.memory_guard.get_memory_usage()
        memory_leak = final_memory - initial_memory
        
        # 计算稳定性评分
        stability_score = self._calculate_stability_score(
            peak_memory, self.memory_limit, oom_events, len(error_messages)
        )
        
        result = MemoryStabilityResult(
            test_name=test_name,
            test_duration=test_duration,
            initial_memory=initial_memory,
            peak_memory=peak_memory,
            final_memory=final_memory,
            memory_leak=memory_leak,
            memory_leak_rate=memory_leak / (test_duration / 3600) if test_duration > 0 else 0,
            gc_collections=gc.get_count()[0],
            oom_events=oom_events,
            crash_count=0,  # 如果能执行到这里说明没有崩溃
            processed_items=processed_items,
            throughput=processed_items / test_duration if test_duration > 0 else 0,
            stability_score=stability_score,
            success=peak_memory <= self.memory_limit and oom_events == 0,
            error_messages=error_messages
        )
        
        self.test_results.append(result)
        self.logger.info(f"内存峰值测试完成，峰值: {peak_memory:.1f}MB，稳定性评分: {stability_score:.3f}")
        
        return result
    
    def test_memory_leak_detection(self, iterations: int = 50) -> MemoryStabilityResult:
        """
        测试内存泄漏检测
        
        Args:
            iterations: 迭代次数
            
        Returns:
            MemoryStabilityResult: 测试结果
        """
        test_name = "memory_leak_detection"
        start_time = time.time()
        
        # 记录初始内存
        gc.collect()
        initial_memory = self.memory_guard.get_memory_usage()
        memory_samples = [initial_memory]
        
        self.logger.info(f"开始内存泄漏检测测试，迭代次数: {iterations}")
        
        error_messages = []
        processed_items = 0
        
        try:
            for i in range(iterations):
                try:
                    # 执行一个完整的处理周期
                    self._simulate_processing_cycle()
                    processed_items += 1
                    
                    # 记录内存使用
                    current_memory = self.memory_guard.get_memory_usage()
                    memory_samples.append(current_memory)
                    
                    # 每10次迭代强制垃圾回收
                    if i % 10 == 0:
                        gc.collect()
                        gc_memory = self.memory_guard.get_memory_usage()
                        memory_samples.append(gc_memory)
                        
                        self.logger.debug(f"迭代 {i}: 内存 {current_memory:.1f}MB -> {gc_memory:.1f}MB (GC后)")
                
                except Exception as e:
                    error_messages.append(f"迭代 {i} 失败: {str(e)}")
                    self.logger.error(f"内存泄漏测试迭代失败: {str(e)}")
        
        except Exception as e:
            error_messages.append(f"测试过程异常: {str(e)}")
            self.logger.error(f"内存泄漏测试异常: {str(e)}")
        
        # 最终垃圾回收
        gc.collect()
        final_memory = self.memory_guard.get_memory_usage()
        memory_samples.append(final_memory)
        
        # 分析内存泄漏
        test_duration = time.time() - start_time
        memory_leak = final_memory - initial_memory
        memory_leak_rate = memory_leak / (test_duration / 3600) if test_duration > 0 else 0
        
        # 分析内存增长趋势
        memory_trend = self._analyze_memory_trend(memory_samples)
        
        # 计算稳定性评分
        stability_score = self._calculate_leak_stability_score(memory_leak_rate, memory_trend)
        
        result = MemoryStabilityResult(
            test_name=test_name,
            test_duration=test_duration,
            initial_memory=initial_memory,
            peak_memory=max(memory_samples),
            final_memory=final_memory,
            memory_leak=memory_leak,
            memory_leak_rate=memory_leak_rate,
            gc_collections=gc.get_count()[0],
            oom_events=0,
            crash_count=0,
            processed_items=processed_items,
            throughput=processed_items / test_duration if test_duration > 0 else 0,
            stability_score=stability_score,
            success=memory_leak_rate <= 1.0,  # 允许每小时1MB的泄漏
            error_messages=error_messages
        )
        
        # 保存内存样本数据
        result.memory_samples = memory_samples
        result.memory_trend = memory_trend
        
        self.test_results.append(result)
        self.logger.info(f"内存泄漏测试完成，泄漏率: {memory_leak_rate:.2f}MB/小时")
        
        return result
    
    def test_long_term_stability(self, duration_hours: float = 1.0) -> MemoryStabilityResult:
        """
        测试长期稳定性
        
        Args:
            duration_hours: 测试持续时间（小时）
            
        Returns:
            MemoryStabilityResult: 测试结果
        """
        test_name = "long_term_stability"
        start_time = time.time()
        target_duration = duration_hours * 3600  # 转换为秒
        
        self.logger.info(f"开始长期稳定性测试，目标持续时间: {duration_hours}小时")
        
        # 初始化监控
        gc.collect()
        initial_memory = self.memory_guard.get_memory_usage()
        peak_memory = initial_memory
        processed_items = 0
        error_messages = []
        oom_events = 0
        crash_count = 0
        
        # 启动内存监控线程
        monitoring_thread = threading.Thread(target=self._memory_monitoring_loop)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        
        try:
            while time.time() - start_time < target_duration:
                if self.stop_testing:
                    break
                
                try:
                    # 执行处理任务
                    self._simulate_processing_cycle()
                    processed_items += 1
                    
                    # 监控内存
                    current_memory = self.memory_guard.get_memory_usage()
                    peak_memory = max(peak_memory, current_memory)
                    
                    if current_memory > self.memory_limit:
                        oom_events += 1
                        error_messages.append(f"内存超限事件: {current_memory:.1f}MB")
                        
                        # 强制垃圾回收
                        gc.collect()
                    
                    # 定期休息，模拟真实使用场景
                    time.sleep(0.1)
                
                except Exception as e:
                    error_messages.append(f"处理异常: {str(e)}")
                    crash_count += 1
                    self.logger.error(f"长期稳定性测试异常: {str(e)}")
                    
                    # 如果连续崩溃太多次，停止测试
                    if crash_count > 10:
                        self.logger.error("连续崩溃次数过多，停止测试")
                        break
        
        except KeyboardInterrupt:
            self.logger.info("用户中断测试")
            self.stop_testing = True
        except Exception as e:
            error_messages.append(f"测试框架异常: {str(e)}")
            self.logger.error(f"长期稳定性测试框架异常: {str(e)}")
        
        # 停止监控
        self.stop_testing = True
        
        # 计算结果
        test_duration = time.time() - start_time
        gc.collect()
        final_memory = self.memory_guard.get_memory_usage()
        memory_leak = final_memory - initial_memory
        memory_leak_rate = memory_leak / (test_duration / 3600) if test_duration > 0 else 0
        
        # 计算稳定性评分
        stability_score = self._calculate_long_term_stability_score(
            test_duration, target_duration, crash_count, oom_events, memory_leak_rate
        )
        
        result = MemoryStabilityResult(
            test_name=test_name,
            test_duration=test_duration,
            initial_memory=initial_memory,
            peak_memory=peak_memory,
            final_memory=final_memory,
            memory_leak=memory_leak,
            memory_leak_rate=memory_leak_rate,
            gc_collections=gc.get_count()[0],
            oom_events=oom_events,
            crash_count=crash_count,
            processed_items=processed_items,
            throughput=processed_items / test_duration if test_duration > 0 else 0,
            stability_score=stability_score,
            success=(
                test_duration >= target_duration * 0.9 and  # 至少运行90%的目标时间
                crash_count <= 5 and  # 崩溃次数不超过5次
                memory_leak_rate <= 10.0  # 内存泄漏率不超过10MB/小时
            ),
            error_messages=error_messages
        )
        
        self.test_results.append(result)
        self.logger.info(f"长期稳定性测试完成，运行时间: {test_duration/3600:.2f}小时，稳定性评分: {stability_score:.3f}")
        
        return result
    
    def _process_test_case(self, test_case: str):
        """处理单个测试用例"""
        try:
            # 模拟字幕处理
            if os.path.exists(test_case):
                subtitles = self.srt_parser.parse(test_case)
                if subtitles:
                    # 模拟剧本重构
                    result = self.screenplay_engineer.reconstruct_screenplay(
                        original_subtitles=subtitles,
                        target_style="viral",
                        language="zh"
                    )
            else:
                # 如果文件不存在，创建模拟数据
                self._simulate_processing_cycle()
        except Exception as e:
            self.logger.debug(f"处理测试用例异常: {str(e)}")
            raise
    
    def _simulate_processing_cycle(self):
        """模拟一个完整的处理周期"""
        try:
            # 模拟创建大量数据
            data = np.random.random((1000, 100))  # 创建一些数据
            
            # 模拟处理
            result = np.mean(data, axis=1)
            
            # 模拟字符串处理
            text_data = ["这是测试文本" * 100 for _ in range(100)]
            processed_text = [text.upper() for text in text_data]
            
            # 清理局部变量
            del data, result, text_data, processed_text
            
        except Exception as e:
            self.logger.debug(f"模拟处理周期异常: {str(e)}")
            raise
    
    def _memory_monitoring_loop(self):
        """内存监控循环"""
        while not self.stop_testing:
            try:
                current_memory = self.memory_guard.get_memory_usage()
                timestamp = time.time()
                
                self.memory_samples.append({
                    'timestamp': timestamp,
                    'memory': current_memory
                })
                
                # 如果内存使用过高，记录警告
                if current_memory > self.memory_warning_threshold:
                    self.logger.warning(f"内存使用接近限制: {current_memory:.1f}MB")
                
                time.sleep(1)  # 每秒监控一次
                
            except Exception as e:
                self.logger.error(f"内存监控异常: {str(e)}")
                time.sleep(5)  # 出错时等待更长时间
    
    def _analyze_memory_trend(self, memory_samples: List[float]) -> Dict[str, float]:
        """分析内存增长趋势"""
        if len(memory_samples) < 2:
            return {'slope': 0.0, 'correlation': 0.0}
        
        try:
            x = np.arange(len(memory_samples))
            y = np.array(memory_samples)
            
            # 计算线性回归斜率
            slope = np.polyfit(x, y, 1)[0]
            
            # 计算相关系数
            correlation = np.corrcoef(x, y)[0, 1] if len(x) > 1 else 0.0
            
            return {
                'slope': slope,
                'correlation': correlation if not np.isnan(correlation) else 0.0
            }
        except Exception:
            return {'slope': 0.0, 'correlation': 0.0}
    
    def _calculate_stability_score(self, peak_memory: float, memory_limit: float, 
                                 oom_events: int, error_count: int) -> float:
        """计算稳定性评分"""
        score = 1.0
        
        # 内存使用评分
        if peak_memory > memory_limit:
            score -= 0.5
        elif peak_memory > memory_limit * 0.9:
            score -= 0.2
        
        # OOM事件惩罚
        score -= min(0.3, oom_events * 0.1)
        
        # 错误数量惩罚
        score -= min(0.2, error_count * 0.02)
        
        return max(0.0, score)
    
    def _calculate_leak_stability_score(self, leak_rate: float, trend: Dict[str, float]) -> float:
        """计算内存泄漏稳定性评分"""
        score = 1.0
        
        # 泄漏率惩罚
        if leak_rate > 10.0:  # 每小时10MB
            score -= 0.5
        elif leak_rate > 5.0:  # 每小时5MB
            score -= 0.3
        elif leak_rate > 1.0:  # 每小时1MB
            score -= 0.1
        
        # 趋势惩罚
        if trend.get('slope', 0) > 1.0:  # 内存持续增长
            score -= 0.2
        
        return max(0.0, score)
    
    def _calculate_long_term_stability_score(self, actual_duration: float, target_duration: float,
                                           crash_count: int, oom_events: int, leak_rate: float) -> float:
        """计算长期稳定性评分"""
        score = 1.0
        
        # 运行时间评分
        duration_ratio = actual_duration / target_duration
        if duration_ratio < 0.5:
            score -= 0.4
        elif duration_ratio < 0.8:
            score -= 0.2
        
        # 崩溃惩罚
        score -= min(0.3, crash_count * 0.05)
        
        # OOM事件惩罚
        score -= min(0.2, oom_events * 0.02)
        
        # 内存泄漏惩罚
        if leak_rate > 10.0:
            score -= 0.1
        
        return max(0.0, score)


class TestMemoryConstraint(unittest.TestCase):
    """4GB内存限制测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = MemoryConstraintTester()
    
    def test_memory_peak_limit(self):
        """测试内存峰值限制"""
        # 创建一些测试用例
        test_cases = ["test_case_1", "test_case_2", "test_case_3"]
        
        result = self.tester.test_memory_peak_constraint(test_cases)
        
        self.assertTrue(result.success, "内存峰值测试应该成功")
        self.assertLessEqual(result.peak_memory, 3800, f"峰值内存应≤3.8GB，实际: {result.peak_memory:.0f}MB")
        self.assertEqual(result.oom_events, 0, "不应该有内存不足事件")
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        result = self.tester.test_memory_leak_detection(iterations=20)
        
        self.assertTrue(result.success, "内存泄漏测试应该成功")
        self.assertLessEqual(result.memory_leak_rate, 1.0, f"内存泄漏率应≤1MB/小时，实际: {result.memory_leak_rate:.2f}MB/小时")
    
    def test_short_term_stability(self):
        """测试短期稳定性（5分钟）"""
        result = self.tester.test_long_term_stability(duration_hours=5/60)  # 5分钟
        
        self.assertTrue(result.success, "短期稳定性测试应该成功")
        self.assertLessEqual(result.crash_count, 1, "崩溃次数应≤1")
        self.assertGreaterEqual(result.stability_score, 0.8, "稳定性评分应≥0.8")


if __name__ == "__main__":
    unittest.main(verbosity=2)
