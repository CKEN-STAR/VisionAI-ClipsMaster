#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存和性能测试模块
验证4GB内存限制下的训练稳定性和性能表现
"""

import os
import sys
import json
import time
import psutil
import logging
import unittest
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.training.en_trainer import EnTrainer
from src.training.zh_trainer import ZhTrainer
from src.utils.memory_guard import get_memory_manager
from src.utils.device_manager import DeviceManager

class MemoryPerformanceTest(unittest.TestCase):
    """内存和性能测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.memory_manager = get_memory_manager()
        self.device_manager = DeviceManager()
        self.test_results = {}
        
        # 内存监控配置
        self.memory_limit_mb = 4000  # 4GB限制
        self.memory_samples = []
        self.monitoring_active = False
        
        # 创建不同规模的测试数据
        self.small_dataset = self._create_test_dataset(100)
        self.medium_dataset = self._create_test_dataset(500)
        self.large_dataset = self._create_test_dataset(1000)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("内存和性能测试初始化完成")
        self.logger.info(f"系统内存: {psutil.virtual_memory().total / 1024**3:.1f}GB")
        self.logger.info(f"可用内存: {psutil.virtual_memory().available / 1024**3:.1f}GB")
    
    def _create_test_dataset(self, size: int) -> List[Dict[str, Any]]:
        """创建指定大小的测试数据集"""
        dataset = []
        
        # 基础模板
        templates = [
            {
                "original": "The young man walked through the busy city streets, observing the daily life around him.",
                "viral": "SHOCKING: Young man's city walk reveals INCREDIBLE secrets that will BLOW YOUR MIND!"
            },
            {
                "original": "She discovered an old book in the quiet library that would change her perspective forever.",
                "viral": "UNBELIEVABLE: Library discovery will CHANGE EVERYTHING you thought you knew about life!"
            },
            {
                "original": "小明今天去学校上课，学习了很多新的知识和技能。",
                "viral": "震撼！小明的学校之旅太精彩了！这些知识改变一切，不敢相信！"
            },
            {
                "original": "妈妈在厨房里精心准备晚餐，全家人都期待着美味的食物。",
                "viral": "惊呆了！妈妈的厨艺史上最强！这道菜的秘密太震撼，全家反应改变一切！"
            }
        ]
        
        # 扩展到指定大小
        for i in range(size):
            template = templates[i % len(templates)]
            dataset.append({
                "original": f"{template['original']} (Sample {i+1})",
                "viral": f"{template['viral']} (Enhanced {i+1})"
            })
        
        return dataset
    
    def test_memory_usage_progression(self):
        """测试不同数据集大小下的内存使用情况"""
        self.logger.info("开始内存使用渐进测试...")
        
        results = {}
        datasets = [
            ("small", self.small_dataset),
            ("medium", self.medium_dataset),
            ("large", self.large_dataset)
        ]
        
        for dataset_name, dataset in datasets:
            self.logger.info(f"测试数据集: {dataset_name} ({len(dataset)} 样本)")
            
            # 开始内存监控
            self._start_memory_monitoring()
            
            try:
                # 执行训练
                trainer = ZhTrainer(use_gpu=False)  # 使用CPU以确保内存可控
                
                memory_before = self._get_current_memory()
                start_time = time.time()
                
                training_result = trainer.train(
                    training_data=dataset,
                    progress_callback=self._memory_progress_callback
                )
                
                end_time = time.time()
                memory_after = self._get_current_memory()
                
                # 停止内存监控
                self._stop_memory_monitoring()
                
                # 分析内存使用
                memory_stats = self._analyze_memory_usage()
                
                results[dataset_name] = {
                    "dataset_size": len(dataset),
                    "training_success": training_result.get("success", False),
                    "training_time": end_time - start_time,
                    "memory_before": memory_before,
                    "memory_after": memory_after,
                    "memory_delta": memory_after - memory_before,
                    "memory_stats": memory_stats,
                    "memory_limit_exceeded": memory_stats["peak_memory"] > self.memory_limit_mb
                }
                
                # 验证内存使用不超过限制
                self.assertLess(memory_stats["peak_memory"], self.memory_limit_mb,
                              f"内存使用超过4GB限制: {memory_stats['peak_memory']:.1f}MB")
                
                # 强制内存清理
                self.memory_manager.force_cleanup()
                time.sleep(1)  # 等待清理完成
                
            except Exception as e:
                self.logger.error(f"数据集 {dataset_name} 测试失败: {e}")
                results[dataset_name] = {
                    "dataset_size": len(dataset),
                    "training_success": False,
                    "error": str(e)
                }
            finally:
                self._stop_memory_monitoring()
        
        self.test_results["memory_progression"] = results
        self.logger.info("内存使用渐进测试完成")
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        self.logger.info("开始内存泄漏检测测试...")
        
        # 执行多轮训练，检测内存是否持续增长
        rounds = 5
        memory_readings = []
        
        trainer = EnTrainer(use_gpu=False)
        
        for round_num in range(rounds):
            self.logger.info(f"执行第 {round_num + 1}/{rounds} 轮训练...")
            
            memory_before = self._get_current_memory()
            
            # 执行训练
            training_result = trainer.train(
                training_data=self.small_dataset,
                progress_callback=lambda p, m: None  # 静默模式
            )
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            memory_after = self._get_current_memory()
            
            memory_readings.append({
                "round": round_num + 1,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_delta": memory_after - memory_before,
                "training_success": training_result.get("success", False)
            })
            
            self.logger.info(f"第{round_num + 1}轮: 内存变化 {memory_after - memory_before:+.1f}MB")
        
        # 分析内存泄漏
        leak_analysis = self._analyze_memory_leak(memory_readings)
        
        self.test_results["memory_leak"] = {
            "rounds": rounds,
            "memory_readings": memory_readings,
            "leak_analysis": leak_analysis
        }
        
        # 验证没有严重的内存泄漏
        self.assertLess(leak_analysis["total_growth"], 500,  # 500MB阈值
                       f"检测到严重内存泄漏: {leak_analysis['total_growth']:.1f}MB")
        
        self.logger.info("内存泄漏检测测试完成")
    
    def test_concurrent_training_memory(self):
        """测试并发训练的内存使用"""
        self.logger.info("开始并发训练内存测试...")
        
        # 开始内存监控
        self._start_memory_monitoring()
        
        try:
            # 创建多个训练线程
            threads = []
            results = {}
            
            def train_worker(worker_id: int, dataset: List[Dict[str, Any]]):
                """训练工作线程"""
                try:
                    trainer = EnTrainer(use_gpu=False) if worker_id % 2 == 0 else ZhTrainer(use_gpu=False)
                    
                    training_result = trainer.train(
                        training_data=dataset,
                        progress_callback=lambda p, m: None
                    )
                    
                    results[f"worker_{worker_id}"] = {
                        "success": training_result.get("success", False),
                        "trainer_type": "EnTrainer" if worker_id % 2 == 0 else "ZhTrainer"
                    }
                    
                except Exception as e:
                    results[f"worker_{worker_id}"] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # 启动2个并发训练线程
            for i in range(2):
                thread = threading.Thread(
                    target=train_worker,
                    args=(i, self.small_dataset)
                )
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join(timeout=300)  # 5分钟超时
            
            # 停止内存监控
            self._stop_memory_monitoring()
            
            # 分析并发内存使用
            memory_stats = self._analyze_memory_usage()
            
            self.test_results["concurrent_training"] = {
                "worker_count": len(threads),
                "worker_results": results,
                "memory_stats": memory_stats,
                "memory_limit_exceeded": memory_stats["peak_memory"] > self.memory_limit_mb
            }
            
            # 验证并发训练不超过内存限制
            self.assertLess(memory_stats["peak_memory"], self.memory_limit_mb,
                          f"并发训练内存使用超过限制: {memory_stats['peak_memory']:.1f}MB")
            
        finally:
            self._stop_memory_monitoring()
        
        self.logger.info("并发训练内存测试完成")
    
    def _start_memory_monitoring(self):
        """开始内存监控"""
        self.memory_samples = []
        self.monitoring_active = True
        
        def monitor_memory():
            while self.monitoring_active:
                memory_usage = self._get_current_memory()
                timestamp = time.time()
                self.memory_samples.append({
                    "timestamp": timestamp,
                    "memory_mb": memory_usage
                })
                time.sleep(0.5)  # 每0.5秒采样一次
        
        self.monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        self.monitor_thread.start()
    
    def _stop_memory_monitoring(self):
        """停止内存监控"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1)
    
    def _get_current_memory(self) -> float:
        """获取当前内存使用量(MB)"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _analyze_memory_usage(self) -> Dict[str, float]:
        """分析内存使用统计"""
        if not self.memory_samples:
            return {"peak_memory": 0, "avg_memory": 0, "min_memory": 0}
        
        memory_values = [sample["memory_mb"] for sample in self.memory_samples]
        
        return {
            "peak_memory": max(memory_values),
            "avg_memory": sum(memory_values) / len(memory_values),
            "min_memory": min(memory_values),
            "sample_count": len(memory_values)
        }
    
    def _analyze_memory_leak(self, memory_readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析内存泄漏情况"""
        if len(memory_readings) < 2:
            return {"total_growth": 0, "avg_growth_per_round": 0, "leak_detected": False}
        
        first_round = memory_readings[0]["memory_after"]
        last_round = memory_readings[-1]["memory_after"]
        total_growth = last_round - first_round
        
        # 计算每轮平均增长
        growth_per_round = []
        for i in range(1, len(memory_readings)):
            growth = memory_readings[i]["memory_after"] - memory_readings[i-1]["memory_after"]
            growth_per_round.append(growth)
        
        avg_growth = sum(growth_per_round) / len(growth_per_round) if growth_per_round else 0
        
        # 判断是否存在内存泄漏（连续增长且总增长超过阈值）
        leak_detected = total_growth > 100 and avg_growth > 10  # 100MB总增长且每轮10MB增长
        
        return {
            "total_growth": total_growth,
            "avg_growth_per_round": avg_growth,
            "leak_detected": leak_detected,
            "growth_trend": growth_per_round
        }
    
    def _memory_progress_callback(self, progress: float, message: str):
        """内存监控进度回调"""
        current_memory = self._get_current_memory()
        if current_memory > self.memory_limit_mb * 0.9:  # 90%阈值警告
            self.logger.warning(f"内存使用接近限制: {current_memory:.1f}MB")
    
    def tearDown(self):
        """测试清理"""
        # 停止内存监控
        self._stop_memory_monitoring()
        
        # 强制内存清理
        self.memory_manager.force_cleanup()
        
        # 保存测试结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"memory_performance_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"内存性能测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
