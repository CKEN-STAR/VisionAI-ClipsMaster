#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 双模型切换测试模块

此模块验证Mistral-7B英文和Qwen2.5-7B中文模型的自动切换功能，包括：
1. 语言检测准确性验证
2. 模型切换延迟测试
3. 处理质量一致性验证
4. 内存管理效率测试
5. 并发处理能力测试
"""

import os
import sys
import json
import time
import logging
import unittest
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 导入核心模块
from src.core.model_switcher import ModelSwitcher
from src.core.language_detector import LanguageDetector
from src.core.srt_parser import SRTParser
from src.utils.log_handler import LogHandler
from src.utils.memory_guard import MemoryGuard

logger = logging.getLogger(__name__)


@dataclass
class ModelSwitchingResult:
    """模型切换测试结果数据类"""
    test_name: str
    input_text: str
    detected_language: str
    expected_language: str
    language_detection_correct: bool
    model_used: str
    switch_delay: float  # 模型切换延迟（秒）
    processing_time: float
    memory_before: float  # 切换前内存使用（MB）
    memory_after: float   # 切换后内存使用（MB）
    memory_peak: float    # 峰值内存使用（MB）
    output_quality_score: float  # 输出质量评分
    success: bool
    error_message: Optional[str] = None


class ModelSwitchingTester:
    """双模型切换测试器"""
    
    def __init__(self, config_path: str = None):
        """初始化模型切换测试器"""
        self.config = self._load_config(config_path)
        
        # 设置日志
        self.logger = LogHandler.get_logger(
            name=__name__,
            level=self.config.get('test_environment', {}).get('log_level', 'INFO')
        )
        
        # 初始化核心组件
        self.model_switcher = ModelSwitcher(self.config)
        self.language_detector = LanguageDetector()
        self.srt_parser = SRTParser()
        self.memory_guard = MemoryGuard()
        
        # 测试结果存储
        self.test_results = []
        
        # 测试阈值
        self.thresholds = self.config.get('test_thresholds', {})
        self.max_switch_delay = self.thresholds.get('model_switch_delay', 1.5)
        self.min_language_detection_accuracy = self.thresholds.get('language_detection', 0.95)
        self.max_memory_peak = self._parse_memory_limit(self.thresholds.get('memory_peak', '3.8GB'))
    
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
                'test_thresholds': {
                    'model_switch_delay': 1.5,
                    'language_detection': 0.95,
                    'memory_peak': '3.8GB'
                },
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
    
    def test_language_detection_accuracy(self, test_cases: List[Tuple[str, str]]) -> List[ModelSwitchingResult]:
        """
        测试语言检测准确性
        
        Args:
            test_cases: 测试用例列表，每个元素为(text, expected_language)元组
            
        Returns:
            List[ModelSwitchingResult]: 测试结果列表
        """
        results = []
        
        for text, expected_language in test_cases:
            start_time = time.time()
            
            try:
                # 记录初始内存
                memory_before = self.memory_guard.get_memory_usage()
                
                # 执行语言检测
                detected_language = self.language_detector.detect_language(text)
                
                # 检查检测结果
                detection_correct = self._is_language_detection_correct(detected_language, expected_language)
                
                # 记录处理后内存
                memory_after = self.memory_guard.get_memory_usage()
                
                result = ModelSwitchingResult(
                    test_name="language_detection_accuracy",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language=detected_language,
                    expected_language=expected_language,
                    language_detection_correct=detection_correct,
                    model_used="language_detector",
                    switch_delay=0.0,  # 语言检测不涉及模型切换
                    processing_time=time.time() - start_time,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_peak=max(memory_before, memory_after),
                    output_quality_score=1.0 if detection_correct else 0.0,
                    success=detection_correct
                )
                
                results.append(result)
                self.test_results.append(result)
                
            except Exception as e:
                self.logger.error(f"语言检测测试失败: {str(e)}")
                error_result = ModelSwitchingResult(
                    test_name="language_detection_accuracy",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language="error",
                    expected_language=expected_language,
                    language_detection_correct=False,
                    model_used="language_detector",
                    switch_delay=0.0,
                    processing_time=time.time() - start_time,
                    memory_before=0.0,
                    memory_after=0.0,
                    memory_peak=0.0,
                    output_quality_score=0.0,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                self.test_results.append(error_result)
        
        return results
    
    def test_model_switching_delay(self, test_cases: List[Tuple[str, str]]) -> List[ModelSwitchingResult]:
        """
        测试模型切换延迟
        
        Args:
            test_cases: 测试用例列表，每个元素为(text, expected_language)元组
            
        Returns:
            List[ModelSwitchingResult]: 测试结果列表
        """
        results = []
        
        for text, expected_language in test_cases:
            try:
                # 记录初始内存
                memory_before = self.memory_guard.get_memory_usage()
                
                # 测量模型切换时间
                switch_start_time = time.time()
                
                # 执行模型切换和处理
                processing_result = self.model_switcher.process_text(
                    text=text,
                    target_language=expected_language,
                    task_type="subtitle_generation"
                )
                
                switch_delay = time.time() - switch_start_time
                
                # 记录处理后内存
                memory_after = self.memory_guard.get_memory_usage()
                memory_peak = self.memory_guard.get_peak_memory_usage()
                
                # 评估输出质量
                output_quality = self._evaluate_output_quality(processing_result, expected_language)
                
                result = ModelSwitchingResult(
                    test_name="model_switching_delay",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language=processing_result.get('detected_language', 'unknown'),
                    expected_language=expected_language,
                    language_detection_correct=processing_result.get('language_correct', False),
                    model_used=processing_result.get('model_used', 'unknown'),
                    switch_delay=switch_delay,
                    processing_time=switch_delay,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_peak=memory_peak,
                    output_quality_score=output_quality,
                    success=switch_delay <= self.max_switch_delay and output_quality >= 0.7
                )
                
                results.append(result)
                self.test_results.append(result)
                
            except Exception as e:
                self.logger.error(f"模型切换延迟测试失败: {str(e)}")
                error_result = ModelSwitchingResult(
                    test_name="model_switching_delay",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language="error",
                    expected_language=expected_language,
                    language_detection_correct=False,
                    model_used="error",
                    switch_delay=float('inf'),
                    processing_time=0.0,
                    memory_before=0.0,
                    memory_after=0.0,
                    memory_peak=0.0,
                    output_quality_score=0.0,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                self.test_results.append(error_result)
        
        return results
    
    def test_concurrent_processing(self, test_cases: List[Tuple[str, str]], max_workers: int = 3) -> List[ModelSwitchingResult]:
        """
        测试并发处理能力
        
        Args:
            test_cases: 测试用例列表
            max_workers: 最大并发数
            
        Returns:
            List[ModelSwitchingResult]: 测试结果列表
        """
        results = []
        
        def process_single_case(case_data):
            text, expected_language = case_data
            thread_id = threading.current_thread().ident
            
            try:
                start_time = time.time()
                memory_before = self.memory_guard.get_memory_usage()
                
                # 并发处理
                processing_result = self.model_switcher.process_text(
                    text=text,
                    target_language=expected_language,
                    task_type="subtitle_generation"
                )
                
                processing_time = time.time() - start_time
                memory_after = self.memory_guard.get_memory_usage()
                memory_peak = self.memory_guard.get_peak_memory_usage()
                
                output_quality = self._evaluate_output_quality(processing_result, expected_language)
                
                return ModelSwitchingResult(
                    test_name=f"concurrent_processing_thread_{thread_id}",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language=processing_result.get('detected_language', 'unknown'),
                    expected_language=expected_language,
                    language_detection_correct=processing_result.get('language_correct', False),
                    model_used=processing_result.get('model_used', 'unknown'),
                    switch_delay=processing_result.get('switch_delay', 0.0),
                    processing_time=processing_time,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_peak=memory_peak,
                    output_quality_score=output_quality,
                    success=output_quality >= 0.7
                )
                
            except Exception as e:
                return ModelSwitchingResult(
                    test_name=f"concurrent_processing_thread_{thread_id}",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language="error",
                    expected_language=expected_language,
                    language_detection_correct=False,
                    model_used="error",
                    switch_delay=0.0,
                    processing_time=0.0,
                    memory_before=0.0,
                    memory_after=0.0,
                    memory_peak=0.0,
                    output_quality_score=0.0,
                    success=False,
                    error_message=str(e)
                )
        
        # 使用线程池进行并发测试
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_case = {executor.submit(process_single_case, case): case for case in test_cases}
            
            for future in concurrent.futures.as_completed(future_to_case):
                try:
                    result = future.result()
                    results.append(result)
                    self.test_results.append(result)
                except Exception as e:
                    self.logger.error(f"并发处理测试异常: {str(e)}")
        
        return results
    
    def test_memory_efficiency(self, test_cases: List[Tuple[str, str]]) -> List[ModelSwitchingResult]:
        """
        测试内存使用效率
        
        Args:
            test_cases: 测试用例列表
            
        Returns:
            List[ModelSwitchingResult]: 测试结果列表
        """
        results = []
        
        # 强制垃圾回收，获取基准内存
        import gc
        gc.collect()
        baseline_memory = self.memory_guard.get_memory_usage()
        
        for i, (text, expected_language) in enumerate(test_cases):
            try:
                # 记录处理前内存
                memory_before = self.memory_guard.get_memory_usage()
                
                # 执行处理
                start_time = time.time()
                processing_result = self.model_switcher.process_text(
                    text=text,
                    target_language=expected_language,
                    task_type="subtitle_generation"
                )
                processing_time = time.time() - start_time
                
                # 记录处理后内存
                memory_after = self.memory_guard.get_memory_usage()
                memory_peak = self.memory_guard.get_peak_memory_usage()
                
                # 强制垃圾回收
                gc.collect()
                memory_after_gc = self.memory_guard.get_memory_usage()
                
                # 计算内存增长
                memory_growth = memory_after - baseline_memory
                memory_leak = memory_after_gc - baseline_memory
                
                output_quality = self._evaluate_output_quality(processing_result, expected_language)
                
                # 判断内存使用是否合理
                memory_efficient = (
                    memory_peak <= self.max_memory_peak and
                    memory_leak <= 100  # 允许100MB的内存增长
                )
                
                result = ModelSwitchingResult(
                    test_name=f"memory_efficiency_test_{i+1}",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language=processing_result.get('detected_language', 'unknown'),
                    expected_language=expected_language,
                    language_detection_correct=processing_result.get('language_correct', False),
                    model_used=processing_result.get('model_used', 'unknown'),
                    switch_delay=processing_result.get('switch_delay', 0.0),
                    processing_time=processing_time,
                    memory_before=memory_before,
                    memory_after=memory_after,
                    memory_peak=memory_peak,
                    output_quality_score=output_quality,
                    success=memory_efficient and output_quality >= 0.7
                )
                
                # 添加内存相关的详细信息
                result.memory_growth = memory_growth
                result.memory_leak = memory_leak
                result.memory_efficient = memory_efficient
                
                results.append(result)
                self.test_results.append(result)
                
            except Exception as e:
                self.logger.error(f"内存效率测试失败: {str(e)}")
                error_result = ModelSwitchingResult(
                    test_name=f"memory_efficiency_test_{i+1}",
                    input_text=text[:100] + "..." if len(text) > 100 else text,
                    detected_language="error",
                    expected_language=expected_language,
                    language_detection_correct=False,
                    model_used="error",
                    switch_delay=0.0,
                    processing_time=0.0,
                    memory_before=0.0,
                    memory_after=0.0,
                    memory_peak=0.0,
                    output_quality_score=0.0,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                self.test_results.append(error_result)
        
        return results
    
    def _is_language_detection_correct(self, detected: str, expected: str) -> bool:
        """判断语言检测是否正确"""
        if expected == "mixed":
            return detected in ["zh", "en", "mixed"]
        else:
            return detected == expected
    
    def _evaluate_output_quality(self, processing_result: Dict[str, Any], expected_language: str) -> float:
        """评估输出质量"""
        try:
            # 基础质量评分
            base_score = 0.5
            
            # 语言检测正确性
            if processing_result.get('language_correct', False):
                base_score += 0.2
            
            # 模型选择正确性
            model_used = processing_result.get('model_used', '')
            if expected_language == 'zh' and 'qwen' in model_used.lower():
                base_score += 0.2
            elif expected_language == 'en' and 'mistral' in model_used.lower():
                base_score += 0.2
            
            # 输出内容质量
            output_text = processing_result.get('output_text', '')
            if output_text and len(output_text) > 0:
                base_score += 0.1
            
            return min(1.0, base_score)
            
        except Exception:
            return 0.0
    
    def generate_switching_test_report(self, output_path: str = None) -> Dict[str, Any]:
        """生成模型切换测试报告"""
        if not self.test_results:
            self.logger.warning("没有测试结果可生成报告")
            return {}
        
        # 按测试类型分组
        test_groups = {}
        for result in self.test_results:
            test_type = result.test_name.split('_')[0] if '_' in result.test_name else result.test_name
            if test_type not in test_groups:
                test_groups[test_type] = []
            test_groups[test_type].append(result)
        
        # 计算各类指标
        report = {
            'test_summary': {
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for r in self.test_results if r.success),
                'failed_tests': sum(1 for r in self.test_results if not r.success),
                'overall_success_rate': sum(1 for r in self.test_results if r.success) / len(self.test_results)
            },
            'language_detection_analysis': self._analyze_language_detection(),
            'model_switching_analysis': self._analyze_model_switching(),
            'memory_efficiency_analysis': self._analyze_memory_efficiency(),
            'performance_metrics': self._analyze_performance_metrics(),
            'recommendations': self._generate_switching_recommendations()
        }
        
        # 保存报告
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"模型切换测试报告已保存: {output_path}")
        
        return report
    
    def _analyze_language_detection(self) -> Dict[str, Any]:
        """分析语言检测结果"""
        detection_results = [r for r in self.test_results if 'language_detection' in r.test_name]
        
        if not detection_results:
            return {}
        
        correct_detections = sum(1 for r in detection_results if r.language_detection_correct)
        total_detections = len(detection_results)
        
        return {
            'accuracy': correct_detections / total_detections,
            'total_tests': total_detections,
            'correct_detections': correct_detections,
            'meets_threshold': (correct_detections / total_detections) >= self.min_language_detection_accuracy
        }
    
    def _analyze_model_switching(self) -> Dict[str, Any]:
        """分析模型切换性能"""
        switching_results = [r for r in self.test_results if 'switching' in r.test_name]
        
        if not switching_results:
            return {}
        
        switch_delays = [r.switch_delay for r in switching_results if r.switch_delay < float('inf')]
        
        return {
            'average_delay': np.mean(switch_delays) if switch_delays else 0,
            'max_delay': np.max(switch_delays) if switch_delays else 0,
            'min_delay': np.min(switch_delays) if switch_delays else 0,
            'delays_within_threshold': sum(1 for d in switch_delays if d <= self.max_switch_delay),
            'total_switches': len(switch_delays),
            'meets_threshold': all(d <= self.max_switch_delay for d in switch_delays)
        }
    
    def _analyze_memory_efficiency(self) -> Dict[str, Any]:
        """分析内存使用效率"""
        memory_results = [r for r in self.test_results if hasattr(r, 'memory_peak')]
        
        if not memory_results:
            return {}
        
        peak_memories = [r.memory_peak for r in memory_results]
        
        return {
            'average_peak_memory': np.mean(peak_memories),
            'max_peak_memory': np.max(peak_memories),
            'memory_within_limit': sum(1 for m in peak_memories if m <= self.max_memory_peak),
            'total_tests': len(peak_memories),
            'meets_memory_limit': all(m <= self.max_memory_peak for m in peak_memories)
        }
    
    def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """分析性能指标"""
        processing_times = [r.processing_time for r in self.test_results if r.processing_time > 0]
        quality_scores = [r.output_quality_score for r in self.test_results]
        
        return {
            'average_processing_time': np.mean(processing_times) if processing_times else 0,
            'average_quality_score': np.mean(quality_scores) if quality_scores else 0,
            'processing_time_std': np.std(processing_times) if processing_times else 0,
            'quality_score_std': np.std(quality_scores) if quality_scores else 0
        }
    
    def _generate_switching_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 分析语言检测
        detection_analysis = self._analyze_language_detection()
        if detection_analysis.get('accuracy', 0) < self.min_language_detection_accuracy:
            recommendations.append(f"语言检测准确率({detection_analysis.get('accuracy', 0):.1%})低于阈值，建议优化语言检测算法")
        
        # 分析切换延迟
        switching_analysis = self._analyze_model_switching()
        if switching_analysis.get('average_delay', 0) > self.max_switch_delay:
            recommendations.append(f"模型切换延迟({switching_analysis.get('average_delay', 0):.2f}秒)超过阈值，建议优化模型加载策略")
        
        # 分析内存使用
        memory_analysis = self._analyze_memory_efficiency()
        if not memory_analysis.get('meets_memory_limit', True):
            recommendations.append(f"内存使用超过限制({memory_analysis.get('max_peak_memory', 0):.0f}MB)，建议优化内存管理")
        
        if not recommendations:
            recommendations.append("所有双模型切换测试均达到预期标准，系统运行良好")
        
        return recommendations


class TestModelSwitching(unittest.TestCase):
    """模型切换测试用例类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        cls.tester = ModelSwitchingTester()
    
    def test_chinese_english_detection(self):
        """测试中英文检测"""
        test_cases = [
            ("这是一个中文测试句子", "zh"),
            ("This is an English test sentence", "en"),
            ("这是中文 and this is English", "mixed")
        ]
        
        results = self.tester.test_language_detection_accuracy(test_cases)
        
        # 验证检测准确性
        accuracy = sum(1 for r in results if r.language_detection_correct) / len(results)
        self.assertGreaterEqual(accuracy, 0.95, "语言检测准确率应≥95%")
    
    def test_model_switch_performance(self):
        """测试模型切换性能"""
        test_cases = [
            ("中文字幕生成测试", "zh"),
            ("English subtitle generation test", "en")
        ]
        
        results = self.tester.test_model_switching_delay(test_cases)
        
        # 验证切换延迟
        for result in results:
            self.assertLessEqual(result.switch_delay, 1.5, f"模型切换延迟应≤1.5秒，实际: {result.switch_delay:.2f}秒")
    
    def test_memory_usage(self):
        """测试内存使用"""
        test_cases = [
            ("内存使用测试中文", "zh"),
            ("Memory usage test English", "en")
        ]
        
        results = self.tester.test_memory_efficiency(test_cases)
        
        # 验证内存使用
        for result in results:
            self.assertLessEqual(result.memory_peak, 3800, f"峰值内存应≤3.8GB，实际: {result.memory_peak:.0f}MB")


if __name__ == "__main__":
    unittest.main(verbosity=2)
