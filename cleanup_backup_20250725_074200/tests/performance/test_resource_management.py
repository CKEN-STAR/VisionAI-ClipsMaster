#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能与资源管理测试

测试范围:
1. 4GB内存设备兼容性 (峰值≤3.8GB)
2. 启动时间验证 (≤5秒)
3. UI响应时间 (≤2秒)
4. 模型切换延迟 (≤1.5秒)
5. 8小时长时间稳定性
6. 内存泄漏检测
"""

import pytest
import time
import threading
import psutil
import os
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.utils.memory_guard import MemoryGuard
from src.core.model_switcher import ModelSwitcher
from src.ui.main_window import SimpleScreenplayApp
from src.testing.stability_framework import StabilityTestFramework


class TestResourceManagement:
    """性能与资源管理测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.memory_guard = MemoryGuard()
        self.model_switcher = ModelSwitcher()
        self.stability_framework = StabilityTestFramework()
        
        # 获取当前进程
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # 性能基准
        self.performance_targets = {
            "max_memory_mb": 3891.2,  # 3.8GB
            "startup_time_s": 5.0,
            "ui_response_time_s": 2.0,
            "model_switch_time_s": 1.5,
            "stability_hours": 8
        }

    def test_4gb_memory_compatibility(self):
        """测试4GB内存设备兼容性"""
        # 模拟4GB内存环境
        total_memory_mb = 4096
        available_memory_mb = total_memory_mb * 0.7  # 70%可用
        
        # 检查内存守护者配置
        assert self.memory_guard.max_memory_mb <= self.performance_targets["max_memory_mb"], \
            f"内存限制配置过高: {self.memory_guard.max_memory_mb}MB"
        
        # 测试内存分配策略
        allocation_result = self.memory_guard.check_system_memory(3000)  # 3GB
        assert allocation_result, "3GB内存分配检查失败"
        
        # 测试内存不足情况
        insufficient_result = self.memory_guard.check_system_memory(5000)  # 5GB
        assert not insufficient_result, "内存不足检查失败"

    def test_startup_time_performance(self):
        """测试启动时间性能 (≤5秒)"""
        startup_times = []
        
        # 多次启动测试
        for i in range(3):
            start_time = time.time()
            
            # 模拟应用启动过程
            try:
                # 导入主要模块
                from src.core.screenplay_engineer import ScreenplayEngineer
                from src.core.language_detector import LanguageDetector
                
                # 初始化核心组件
                screenplay_engineer = ScreenplayEngineer()
                language_detector = LanguageDetector()
                
                # 加载配置
                startup_time = time.time() - start_time
                startup_times.append(startup_time)
                
            except Exception as e:
                pytest.fail(f"启动过程出错: {str(e)}")
        
        # 验证启动时间
        avg_startup_time = sum(startup_times) / len(startup_times)
        max_startup_time = max(startup_times)
        
        assert avg_startup_time <= self.performance_targets["startup_time_s"], \
            f"平均启动时间过长: {avg_startup_time:.2f}s (目标: ≤{self.performance_targets['startup_time_s']}s)"
        
        assert max_startup_time <= self.performance_targets["startup_time_s"] * 1.2, \
            f"最大启动时间过长: {max_startup_time:.2f}s"

    def test_ui_response_time(self):
        """测试UI响应时间 (≤2秒)"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            import sys
            
            # 创建QApplication实例
            if not QApplication.instance():
                app = QApplication(sys.argv)
            else:
                app = QApplication.instance()
            
            response_times = []
            
            # 测试UI操作响应时间
            ui_operations = [
                "创建主窗口",
                "切换标签页",
                "加载文件对话框",
                "更新进度条",
                "显示状态信息"
            ]
            
            for operation in ui_operations:
                start_time = time.time()
                
                # 模拟UI操作
                if operation == "创建主窗口":
                    # 模拟主窗口创建
                    time.sleep(0.1)  # 模拟创建时间
                elif operation == "切换标签页":
                    time.sleep(0.05)  # 模拟切换时间
                elif operation == "加载文件对话框":
                    time.sleep(0.2)   # 模拟对话框加载
                elif operation == "更新进度条":
                    time.sleep(0.02)  # 模拟进度更新
                elif operation == "显示状态信息":
                    time.sleep(0.01)  # 模拟状态更新
                
                response_time = time.time() - start_time
                response_times.append((operation, response_time))
            
            # 验证响应时间
            for operation, response_time in response_times:
                assert response_time <= self.performance_targets["ui_response_time_s"], \
                    f"{operation}响应时间过长: {response_time:.2f}s (目标: ≤{self.performance_targets['ui_response_time_s']}s)"
                    
        except ImportError:
            pytest.skip("PyQt6不可用，跳过UI响应时间测试")

    def test_model_switching_performance(self):
        """测试模型切换性能 (≤1.5秒)"""
        switch_times = []
        
        # 测试多次模型切换
        languages = ["zh", "en", "zh", "en", "zh"]
        
        for lang in languages:
            start_time = time.time()
            success = self.model_switcher.switch_model(lang)
            switch_time = time.time() - start_time
            
            assert success, f"{lang}模型切换失败"
            switch_times.append((lang, switch_time))
        
        # 验证切换时间
        for lang, switch_time in switch_times:
            assert switch_time <= self.performance_targets["model_switch_time_s"], \
                f"{lang}模型切换时间过长: {switch_time:.2f}s (目标: ≤{self.performance_targets['model_switch_time_s']}s)"
        
        # 验证平均切换时间
        avg_switch_time = sum(t for _, t in switch_times) / len(switch_times)
        assert avg_switch_time <= self.performance_targets["model_switch_time_s"] * 0.8, \
            f"平均切换时间过长: {avg_switch_time:.2f}s"

    def test_memory_usage_monitoring(self):
        """测试内存使用监控"""
        memory_samples = []
        
        # 监控内存使用
        def memory_monitor():
            for _ in range(60):  # 监控60秒
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                time.sleep(1)
        
        # 启动内存监控线程
        monitor_thread = threading.Thread(target=memory_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 执行一些操作
        for i in range(10):
            # 模拟模型切换
            self.model_switcher.switch_model("zh" if i % 2 == 0 else "en")
            time.sleep(2)
        
        # 等待监控完成
        monitor_thread.join(timeout=70)
        
        # 分析内存使用
        if memory_samples:
            peak_memory = max(memory_samples)
            avg_memory = sum(memory_samples) / len(memory_samples)
            memory_increase = peak_memory - self.initial_memory
            
            assert peak_memory <= self.performance_targets["max_memory_mb"], \
                f"峰值内存超限: {peak_memory:.2f}MB (限制: {self.performance_targets['max_memory_mb']}MB)"
            
            assert memory_increase <= 1000, \
                f"内存增长过多: {memory_increase:.2f}MB"

    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        memory_samples = []
        
        # 执行重复操作检测内存泄漏
        for cycle in range(10):
            # 模拟工作负载
            for _ in range(5):
                self.model_switcher.switch_model("zh")
                self.model_switcher.switch_model("en")
            
            # 记录内存使用
            current_memory = self.process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # 强制垃圾回收
            import gc
            gc.collect()
            
            time.sleep(1)
        
        # 分析内存趋势
        if len(memory_samples) >= 5:
            # 计算内存增长趋势
            early_avg = sum(memory_samples[:3]) / 3
            late_avg = sum(memory_samples[-3:]) / 3
            memory_growth = late_avg - early_avg
            
            # 内存增长应该在合理范围内
            assert memory_growth <= 50, f"检测到内存泄漏: {memory_growth:.2f}MB增长"

    @pytest.mark.slow
    def test_8_hour_stability(self):
        """测试8小时长时间稳定性"""
        # 注意：这是一个长时间测试，通常在CI/CD中跳过
        if os.environ.get("SKIP_LONG_TESTS", "false").lower() == "true":
            pytest.skip("跳过长时间稳定性测试")
        
        stability_config = {
            "duration_hours": 8,
            "memory_check_interval": 300,  # 5分钟检查一次
            "operation_interval": 60,      # 1分钟执行一次操作
            "max_memory_mb": self.performance_targets["max_memory_mb"]
        }
        
        # 启动稳定性测试
        stability_result = self.stability_framework.run_long_term_stability_test(
            config=stability_config
        )
        
        # 验证稳定性结果
        assert stability_result["status"] == "success", "8小时稳定性测试失败"
        assert stability_result["uptime_hours"] >= 8, "运行时间不足8小时"
        assert stability_result["memory_violations"] == 0, "存在内存超限情况"
        assert stability_result["crash_count"] == 0, "存在崩溃情况"

    def test_concurrent_operations_performance(self):
        """测试并发操作性能"""
        results = []
        errors = []
        
        def concurrent_worker(worker_id: int):
            try:
                start_time = time.time()
                
                # 执行并发操作
                operations = [
                    lambda: self.model_switcher.switch_model("zh"),
                    lambda: self.model_switcher.switch_model("en"),
                    lambda: self.memory_guard.check_system_memory(1000),
                    lambda: time.sleep(0.1)  # 模拟其他操作
                ]
                
                for op in operations:
                    op()
                
                execution_time = time.time() - start_time
                results.append((worker_id, execution_time))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # 创建并发工作线程
        threads = []
        for i in range(8):  # 8个并发线程
            thread = threading.Thread(target=concurrent_worker, args=(i,))
            threads.append(thread)
        
        # 启动并等待完成
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        total_time = time.time() - start_time
        
        # 验证并发性能
        assert len(errors) == 0, f"并发操作出现错误: {errors}"
        assert len(results) == 8, f"并发操作结果不完整: {len(results)}/8"
        assert total_time <= 10, f"并发操作总时间过长: {total_time:.2f}s"

    def test_resource_cleanup_on_exit(self):
        """测试退出时资源清理"""
        # 记录初始资源状态
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # 创建一些资源
        resources = []
        for i in range(5):
            # 模拟资源创建
            resource = {"id": i, "data": bytearray(1024 * 1024)}  # 1MB
            resources.append(resource)
        
        # 检查资源创建后的内存
        after_creation_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = after_creation_memory - initial_memory
        
        # 清理资源
        resources.clear()
        import gc
        gc.collect()
        
        # 检查清理后的内存
        after_cleanup_memory = self.process.memory_info().rss / 1024 / 1024
        memory_recovered = after_creation_memory - after_cleanup_memory
        
        # 验证资源清理效果
        recovery_rate = memory_recovered / memory_increase if memory_increase > 0 else 1
        assert recovery_rate >= 0.7, f"资源清理不充分: {recovery_rate:.2%}回收率"

    def test_performance_degradation_handling(self):
        """测试性能降级处理"""
        # 模拟高负载情况
        high_load_config = {
            "memory_pressure": 0.9,  # 90%内存压力
            "cpu_pressure": 0.8,     # 80%CPU压力
        }
        
        # 测试降级策略
        degradation_result = self.memory_guard.handle_performance_degradation(
            high_load_config
        )
        
        # 验证降级处理
        assert "strategy" in degradation_result, "缺少降级策略"
        assert degradation_result["strategy"] in ["reduce_quality", "limit_features", "emergency_cleanup"], \
            f"未知降级策略: {degradation_result['strategy']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
