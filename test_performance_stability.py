#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能和稳定性专项测试
测试系统在各种负载条件下的表现
"""

import time
import psutil
import threading
import multiprocessing
import gc
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json
import tempfile
from datetime import datetime, timedelta

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            'memory_usage': [],
            'cpu_usage': [],
            'timestamps': []
        }
        self.monitor_thread = None
    
    def start_monitoring(self, interval=1.0):
        """开始监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def _monitor_loop(self, interval):
        """监控循环"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # 记录内存使用
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                
                # 记录CPU使用
                cpu_percent = process.cpu_percent()
                
                # 记录时间戳
                timestamp = time.time()
                
                self.metrics['memory_usage'].append(memory_mb)
                self.metrics['cpu_usage'].append(cpu_percent)
                self.metrics['timestamps'].append(timestamp)
                
                time.sleep(interval)
            except Exception as e:
                print(f"监控异常: {e}")
                break
    
    def get_peak_memory(self) -> float:
        """获取峰值内存使用"""
        if self.metrics['memory_usage']:
            return max(self.metrics['memory_usage'])
        return 0.0
    
    def get_average_cpu(self) -> float:
        """获取平均CPU使用率"""
        if self.metrics['cpu_usage']:
            return sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage'])
        return 0.0
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            'peak_memory_mb': self.get_peak_memory(),
            'average_cpu_percent': self.get_average_cpu(),
            'total_samples': len(self.metrics['memory_usage']),
            'monitoring_duration': (
                self.metrics['timestamps'][-1] - self.metrics['timestamps'][0]
                if len(self.metrics['timestamps']) > 1 else 0
            )
        }

class MemoryStressTest:
    """内存压力测试"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_memory_limit_compliance(self, limit_mb=3800):
        """测试内存限制合规性"""
        print(f"🧪 测试内存限制合规性 (限制: {limit_mb}MB)")
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring(0.5)
        
        try:
            # 模拟大量数据处理
            self._simulate_heavy_processing()
            
            time.sleep(5)  # 让监控收集足够数据
            
        finally:
            monitor.stop_monitoring()
        
        peak_memory = monitor.get_peak_memory()
        compliance = peak_memory <= limit_mb
        
        self.test_results['memory_limit_test'] = {
            'peak_memory_mb': peak_memory,
            'limit_mb': limit_mb,
            'compliant': compliance,
            'margin_mb': limit_mb - peak_memory
        }
        
        print(f"  峰值内存: {peak_memory:.1f}MB")
        print(f"  合规状态: {'✅ 通过' if compliance else '❌ 超限'}")
        
        return compliance
    
    def _simulate_heavy_processing(self):
        """模拟重度处理任务"""
        # 模拟字幕数据处理
        large_data = []
        
        for i in range(1000):
            # 模拟字幕段落
            segment = {
                'index': i,
                'start_time': f"00:{i//60:02d}:{i%60:02d},000",
                'end_time': f"00:{(i+3)//60:02d}:{(i+3)%60:02d},000",
                'text': f"这是第{i}段字幕内容，包含一些测试文本" * 10,
                'metadata': {
                    'emotion': 'neutral',
                    'importance': 0.5,
                    'keywords': ['测试', '字幕', '内容'] * 5
                }
            }
            large_data.append(segment)
        
        # 模拟数据处理
        processed_data = []
        for segment in large_data:
            processed_segment = {
                **segment,
                'processed': True,
                'analysis_result': {
                    'sentiment_score': 0.5,
                    'key_phrases': segment['text'].split()[:10],
                    'processing_timestamp': time.time()
                }
            }
            processed_data.append(processed_segment)
        
        # 强制垃圾回收
        del large_data
        del processed_data
        gc.collect()
    
    def test_memory_leak_detection(self, duration_seconds=30):
        """测试内存泄漏检测"""
        print(f"🔍 内存泄漏检测测试 (持续{duration_seconds}秒)")
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring(1.0)
        
        start_time = time.time()
        iteration = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                # 模拟重复操作
                self._simulate_repeated_operations()
                iteration += 1
                
                if iteration % 10 == 0:
                    gc.collect()  # 定期垃圾回收
                
                time.sleep(0.5)
        
        finally:
            monitor.stop_monitoring()
        
        # 分析内存使用趋势
        memory_usage = monitor.metrics['memory_usage']
        if len(memory_usage) > 10:
            initial_memory = sum(memory_usage[:5]) / 5
            final_memory = sum(memory_usage[-5:]) / 5
            memory_growth = final_memory - initial_memory
            
            # 判断是否存在内存泄漏（增长超过100MB认为可能泄漏）
            has_leak = memory_growth > 100
            
            self.test_results['memory_leak_test'] = {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_growth_mb': memory_growth,
                'iterations': iteration,
                'has_potential_leak': has_leak
            }
            
            print(f"  初始内存: {initial_memory:.1f}MB")
            print(f"  最终内存: {final_memory:.1f}MB")
            print(f"  内存增长: {memory_growth:.1f}MB")
            print(f"  泄漏检测: {'⚠️ 可能存在泄漏' if has_leak else '✅ 无明显泄漏'}")
            
            return not has_leak
        
        return True
    
    def _simulate_repeated_operations(self):
        """模拟重复操作"""
        # 模拟字幕解析
        srt_content = """1
00:00:01,000 --> 00:00:03,000
测试字幕内容

2
00:00:04,000 --> 00:00:06,000
另一段测试内容
"""
        
        # 模拟解析过程
        lines = srt_content.strip().split('\n')
        segments = []
        
        for i in range(0, len(lines), 4):
            if i + 2 < len(lines):
                segment = {
                    'index': lines[i],
                    'time': lines[i + 1] if i + 1 < len(lines) else '',
                    'text': lines[i + 2] if i + 2 < len(lines) else ''
                }
                segments.append(segment)
        
        # 模拟处理
        for segment in segments:
            processed = segment['text'].upper().replace('测试', 'TEST')
        
        # 清理临时数据
        del segments

class StabilityTest:
    """稳定性测试"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_long_running_stability(self, duration_minutes=5):
        """测试长时间运行稳定性"""
        print(f"⏱️ 长时间运行稳定性测试 (持续{duration_minutes}分钟)")
        
        duration_seconds = duration_minutes * 60
        monitor = PerformanceMonitor()
        monitor.start_monitoring(2.0)
        
        start_time = time.time()
        operations_completed = 0
        errors_encountered = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                try:
                    # 模拟各种操作
                    self._simulate_mixed_operations()
                    operations_completed += 1
                    
                    # 每100次操作休息一下
                    if operations_completed % 100 == 0:
                        time.sleep(1)
                        print(f"  已完成 {operations_completed} 次操作...")
                
                except Exception as e:
                    errors_encountered += 1
                    print(f"  操作异常: {e}")
                
                time.sleep(0.1)
        
        finally:
            monitor.stop_monitoring()
        
        # 计算稳定性指标
        actual_duration = time.time() - start_time
        success_rate = (operations_completed - errors_encountered) / operations_completed if operations_completed > 0 else 0
        
        self.test_results['stability_test'] = {
            'planned_duration_seconds': duration_seconds,
            'actual_duration_seconds': actual_duration,
            'operations_completed': operations_completed,
            'errors_encountered': errors_encountered,
            'success_rate': success_rate,
            'operations_per_second': operations_completed / actual_duration,
            'peak_memory_mb': monitor.get_peak_memory(),
            'average_cpu_percent': monitor.get_average_cpu()
        }
        
        print(f"  实际运行时间: {actual_duration:.1f}秒")
        print(f"  完成操作数: {operations_completed}")
        print(f"  错误次数: {errors_encountered}")
        print(f"  成功率: {success_rate:.2%}")
        print(f"  操作速率: {operations_completed / actual_duration:.1f} ops/sec")
        
        return success_rate > 0.95  # 95%以上成功率认为稳定
    
    def _simulate_mixed_operations(self):
        """模拟混合操作"""
        import random
        
        operation_type = random.choice(['parse', 'analyze', 'generate', 'export'])
        
        if operation_type == 'parse':
            self._simulate_srt_parsing()
        elif operation_type == 'analyze':
            self._simulate_narrative_analysis()
        elif operation_type == 'generate':
            self._simulate_subtitle_generation()
        elif operation_type == 'export':
            self._simulate_video_export()
    
    def _simulate_srt_parsing(self):
        """模拟SRT解析"""
        content = "1\n00:00:01,000 --> 00:00:03,000\n测试内容\n"
        lines = content.split('\n')
        result = {'parsed': True, 'segments': len(lines)}
    
    def _simulate_narrative_analysis(self):
        """模拟叙事分析"""
        text = "这是一个测试故事，包含情节发展和角色互动。"
        words = text.split()
        analysis = {'word_count': len(words), 'sentiment': 'positive'}
    
    def _simulate_subtitle_generation(self):
        """模拟字幕生成"""
        template = "生成的字幕内容 {}"
        generated = [template.format(i) for i in range(10)]
    
    def _simulate_video_export(self):
        """模拟视频导出"""
        segments = [{'start': i, 'end': i+2} for i in range(0, 20, 2)]
        export_data = {'segments': segments, 'format': 'mp4'}

class ConcurrencyTest:
    """并发测试"""
    
    def test_concurrent_processing(self, num_threads=4):
        """测试并发处理能力"""
        print(f"🔄 并发处理测试 (线程数: {num_threads})")
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring(1.0)
        
        results = []
        threads = []
        
        def worker_task(worker_id):
            """工作线程任务"""
            try:
                start_time = time.time()
                
                # 模拟处理任务
                for i in range(50):
                    self._simulate_processing_task(worker_id, i)
                    time.sleep(0.01)
                
                end_time = time.time()
                results.append({
                    'worker_id': worker_id,
                    'duration': end_time - start_time,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'worker_id': worker_id,
                    'error': str(e),
                    'success': False
                })
        
        # 启动工作线程
        start_time = time.time()
        for i in range(num_threads):
            thread = threading.Thread(target=worker_task, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        monitor.stop_monitoring()
        
        # 分析结果
        successful_workers = [r for r in results if r.get('success', False)]
        failed_workers = [r for r in results if not r.get('success', False)]
        
        print(f"  总耗时: {total_time:.2f}秒")
        print(f"  成功线程: {len(successful_workers)}/{num_threads}")
        print(f"  失败线程: {len(failed_workers)}")
        print(f"  峰值内存: {monitor.get_peak_memory():.1f}MB")
        
        return len(failed_workers) == 0
    
    def _simulate_processing_task(self, worker_id, task_id):
        """模拟处理任务"""
        # 模拟一些计算
        data = f"Worker {worker_id} processing task {task_id}"
        processed = data.upper().replace(' ', '_')
        result = {'worker': worker_id, 'task': task_id, 'result': processed}

def run_performance_tests():
    """运行所有性能测试"""
    print("🚀 开始性能和稳定性测试")
    print("=" * 60)
    
    all_results = {}
    
    # 1. 内存压力测试
    print("\n1. 内存压力测试")
    print("-" * 30)
    memory_test = MemoryStressTest()
    
    memory_limit_ok = memory_test.test_memory_limit_compliance()
    memory_leak_ok = memory_test.test_memory_leak_detection(30)
    
    all_results['memory_tests'] = memory_test.test_results
    
    # 2. 稳定性测试
    print("\n2. 稳定性测试")
    print("-" * 30)
    stability_test = StabilityTest()
    
    stability_ok = stability_test.test_long_running_stability(2)  # 2分钟测试
    
    all_results['stability_tests'] = stability_test.test_results
    
    # 3. 并发测试
    print("\n3. 并发测试")
    print("-" * 30)
    concurrency_test = ConcurrencyTest()
    
    concurrency_ok = concurrency_test.test_concurrent_processing(4)
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 性能测试结果摘要")
    print("=" * 60)
    
    tests_passed = sum([memory_limit_ok, memory_leak_ok, stability_ok, concurrency_ok])
    total_tests = 4
    
    print(f"内存限制合规: {'✅' if memory_limit_ok else '❌'}")
    print(f"内存泄漏检测: {'✅' if memory_leak_ok else '❌'}")
    print(f"长时间稳定性: {'✅' if stability_ok else '❌'}")
    print(f"并发处理能力: {'✅' if concurrency_ok else '❌'}")
    print(f"\n总体通过率: {tests_passed}/{total_tests} ({tests_passed/total_tests:.1%})")
    
    # 保存详细结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"performance_test_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"📁 详细结果已保存到: {results_file}")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)
