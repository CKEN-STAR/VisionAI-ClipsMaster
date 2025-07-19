#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 异常处理与恢复测试

测试范围:
1. 断点续剪功能 (≥95%恢复成功率)
2. 内存不足情况处理
3. 文件损坏恢复
4. 网络中断处理
5. 异常处理成功率 (≥90%)
6. 8小时稳定性验证
"""

import pytest
import time
import os
import json
import tempfile
import threading
import psutil
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock

from src.utils.memory_guard import MemoryGuard
from src.core.recovery_manager import RecoveryManager
from src.testing.stability_framework import StabilityTestFramework


class TestStabilityRecovery:
    """异常处理与恢复测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.memory_guard = MemoryGuard()
        self.recovery_manager = RecoveryManager()
        self.stability_framework = StabilityTestFramework()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 恢复成功率目标
        self.recovery_targets = {
            "checkpoint_recovery_rate": 0.95,  # 95%
            "exception_handling_rate": 0.90,   # 90%
            "stability_hours": 8,
            "max_recovery_time_s": 30
        }
        
        # 测试数据
        self.sample_project_data = {
            "project_id": "test_project_001",
            "video_segments": [
                {"id": "seg_001", "start": 0, "end": 5, "processed": True},
                {"id": "seg_002", "start": 5, "end": 10, "processed": True},
                {"id": "seg_003", "start": 10, "end": 15, "processed": False},
                {"id": "seg_004", "start": 15, "end": 20, "processed": False}
            ],
            "current_progress": 0.5,
            "last_checkpoint": time.time()
        }

    def test_checkpoint_resume_functionality(self):
        """测试断点续剪功能"""
        checkpoint_file = os.path.join(self.temp_dir, "checkpoint.json")
        
        # 保存检查点
        checkpoint_success = self.recovery_manager.save_checkpoint(
            project_data=self.sample_project_data,
            checkpoint_path=checkpoint_file
        )
        assert checkpoint_success, "检查点保存失败"
        assert os.path.exists(checkpoint_file), "检查点文件未创建"
        
        # 模拟中断后恢复
        recovered_data = self.recovery_manager.load_checkpoint(checkpoint_file)
        assert recovered_data is not None, "检查点加载失败"
        
        # 验证恢复数据完整性
        assert recovered_data["project_id"] == self.sample_project_data["project_id"], "项目ID不匹配"
        assert len(recovered_data["video_segments"]) == len(self.sample_project_data["video_segments"]), "片段数量不匹配"
        
        # 验证处理进度恢复
        processed_segments = [seg for seg in recovered_data["video_segments"] if seg["processed"]]
        assert len(processed_segments) == 2, f"已处理片段数量错误: {len(processed_segments)}"

    def test_checkpoint_recovery_success_rate(self):
        """测试检查点恢复成功率 (≥95%)"""
        recovery_attempts = 100
        successful_recoveries = 0
        
        for i in range(recovery_attempts):
            checkpoint_file = os.path.join(self.temp_dir, f"checkpoint_{i}.json")
            
            # 创建测试项目数据
            test_project = self.sample_project_data.copy()
            test_project["project_id"] = f"test_project_{i:03d}"
            
            try:
                # 保存检查点
                save_success = self.recovery_manager.save_checkpoint(
                    project_data=test_project,
                    checkpoint_path=checkpoint_file
                )
                
                if save_success:
                    # 尝试恢复
                    recovered_data = self.recovery_manager.load_checkpoint(checkpoint_file)
                    
                    if recovered_data and recovered_data["project_id"] == test_project["project_id"]:
                        successful_recoveries += 1
                        
            except Exception as e:
                # 记录失败但继续测试
                print(f"恢复测试{i}失败: {str(e)}")
        
        # 计算成功率
        recovery_rate = successful_recoveries / recovery_attempts
        assert recovery_rate >= self.recovery_targets["checkpoint_recovery_rate"], \
            f"检查点恢复成功率不足: {recovery_rate:.2%} (目标: ≥{self.recovery_targets['checkpoint_recovery_rate']:.0%})"

    def test_memory_overflow_handling(self):
        """测试内存不足情况处理"""
        # 模拟内存压力
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # 创建内存压力
        memory_hogs = []
        try:
            # 逐步增加内存使用
            for i in range(10):
                # 分配100MB内存
                memory_hog = bytearray(100 * 1024 * 1024)
                memory_hogs.append(memory_hog)
                
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_usage = current_memory - initial_memory
                
                # 测试内存守护者响应
                if memory_usage > 2000:  # 2GB
                    memory_status = self.memory_guard.check_memory_status()
                    
                    if memory_status["level"] == "critical":
                        # 测试紧急清理
                        cleanup_success = self.memory_guard.emergency_cleanup()
                        assert cleanup_success, "紧急内存清理失败"
                        break
                        
        except MemoryError:
            # 预期的内存错误，测试恢复机制
            recovery_success = self.memory_guard.handle_memory_overflow()
            assert recovery_success, "内存溢出恢复失败"
            
        finally:
            # 清理内存
            memory_hogs.clear()
            import gc
            gc.collect()

    def test_file_corruption_recovery(self):
        """测试文件损坏恢复"""
        # 创建正常的项目文件
        project_file = os.path.join(self.temp_dir, "project.json")
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(self.sample_project_data, f)
        
        # 验证正常加载
        normal_data = self.recovery_manager.load_project_file(project_file)
        assert normal_data is not None, "正常文件加载失败"
        
        # 模拟文件损坏
        corrupted_scenarios = [
            "invalid_json",      # 无效JSON
            "truncated_file",    # 截断文件
            "empty_file",        # 空文件
            "binary_corruption"  # 二进制损坏
        ]
        
        for scenario in corrupted_scenarios:
            corrupted_file = os.path.join(self.temp_dir, f"corrupted_{scenario}.json")
            
            # 创建损坏文件
            if scenario == "invalid_json":
                with open(corrupted_file, 'w') as f:
                    f.write('{"invalid": json content}')
            elif scenario == "truncated_file":
                with open(corrupted_file, 'w') as f:
                    f.write('{"project_id": "test"')  # 截断
            elif scenario == "empty_file":
                with open(corrupted_file, 'w') as f:
                    pass  # 空文件
            elif scenario == "binary_corruption":
                with open(corrupted_file, 'wb') as f:
                    f.write(b'\x00\x01\x02\x03\x04')  # 二进制数据
            
            # 测试损坏文件恢复
            recovery_result = self.recovery_manager.recover_corrupted_file(
                corrupted_file, 
                backup_dir=self.temp_dir
            )
            
            # 验证恢复机制
            assert "status" in recovery_result, f"{scenario}恢复结果缺少状态"
            assert recovery_result["status"] in ["recovered", "failed", "no_backup"], \
                f"{scenario}恢复状态无效: {recovery_result['status']}"

    def test_network_interruption_handling(self):
        """测试网络中断处理"""
        # 模拟网络操作
        network_operations = [
            "model_download",
            "config_sync", 
            "update_check",
            "telemetry_upload"
        ]
        
        for operation in network_operations:
            # 模拟网络中断
            with patch('requests.get') as mock_get:
                mock_get.side_effect = ConnectionError("网络连接失败")
                
                # 测试网络错误处理
                result = self.recovery_manager.handle_network_operation(
                    operation_type=operation,
                    retry_count=3,
                    timeout=10
                )
                
                # 验证错误处理
                assert "status" in result, f"{operation}操作结果缺少状态"
                assert result["status"] in ["success", "failed", "retry"], \
                    f"{operation}操作状态无效: {result['status']}"
                
                # 如果失败，应该有重试机制
                if result["status"] == "failed":
                    assert result.get("retry_count", 0) >= 3, f"{operation}重试次数不足"

    def test_exception_handling_success_rate(self):
        """测试异常处理成功率 (≥90%)"""
        exception_scenarios = [
            {"type": "ValueError", "message": "无效参数"},
            {"type": "FileNotFoundError", "message": "文件未找到"},
            {"type": "MemoryError", "message": "内存不足"},
            {"type": "TimeoutError", "message": "操作超时"},
            {"type": "PermissionError", "message": "权限不足"},
            {"type": "ConnectionError", "message": "连接失败"},
            {"type": "KeyError", "message": "键不存在"},
            {"type": "IndexError", "message": "索引越界"},
            {"type": "TypeError", "message": "类型错误"},
            {"type": "RuntimeError", "message": "运行时错误"}
        ]
        
        successful_handles = 0
        total_exceptions = len(exception_scenarios)
        
        for scenario in exception_scenarios:
            try:
                # 模拟异常处理
                handle_result = self.recovery_manager.handle_exception(
                    exception_type=scenario["type"],
                    exception_message=scenario["message"],
                    context={"operation": "test", "timestamp": time.time()}
                )
                
                # 验证处理结果
                if handle_result and handle_result.get("handled", False):
                    successful_handles += 1
                    
            except Exception as e:
                # 异常处理器本身不应该抛出异常
                print(f"异常处理器失败: {scenario['type']} - {str(e)}")
        
        # 计算成功率
        handling_rate = successful_handles / total_exceptions
        assert handling_rate >= self.recovery_targets["exception_handling_rate"], \
            f"异常处理成功率不足: {handling_rate:.2%} (目标: ≥{self.recovery_targets['exception_handling_rate']:.0%})"

    def test_recovery_time_performance(self):
        """测试恢复时间性能"""
        recovery_scenarios = [
            "checkpoint_recovery",
            "memory_cleanup", 
            "file_repair",
            "network_reconnect",
            "model_reload"
        ]
        
        for scenario in recovery_scenarios:
            start_time = time.time()
            
            # 执行恢复操作
            if scenario == "checkpoint_recovery":
                checkpoint_file = os.path.join(self.temp_dir, "test_checkpoint.json")
                self.recovery_manager.save_checkpoint(self.sample_project_data, checkpoint_file)
                result = self.recovery_manager.load_checkpoint(checkpoint_file)
                
            elif scenario == "memory_cleanup":
                result = self.memory_guard.emergency_cleanup()
                
            elif scenario == "file_repair":
                test_file = os.path.join(self.temp_dir, "test_repair.json")
                with open(test_file, 'w') as f:
                    f.write('{"invalid": json}')
                result = self.recovery_manager.recover_corrupted_file(test_file, self.temp_dir)
                
            elif scenario == "network_reconnect":
                result = self.recovery_manager.handle_network_operation("test_reconnect")
                
            elif scenario == "model_reload":
                result = self.recovery_manager.reload_model_after_error("zh")
            
            recovery_time = time.time() - start_time
            
            # 验证恢复时间
            assert recovery_time <= self.recovery_targets["max_recovery_time_s"], \
                f"{scenario}恢复时间过长: {recovery_time:.2f}s (限制: {self.recovery_targets['max_recovery_time_s']}s)"

    @pytest.mark.slow
    def test_8_hour_stability_with_recovery(self):
        """测试8小时稳定性与恢复"""
        if os.environ.get("SKIP_LONG_TESTS", "false").lower() == "true":
            pytest.skip("跳过长时间稳定性测试")
        
        stability_config = {
            "duration_hours": 8,
            "inject_failures": True,
            "failure_rate": 0.05,  # 5%故障率
            "recovery_enabled": True,
            "checkpoint_interval": 300  # 5分钟检查点
        }
        
        # 启动稳定性测试
        stability_result = self.stability_framework.run_stability_test_with_recovery(
            config=stability_config
        )
        
        # 验证稳定性结果
        assert stability_result["status"] == "success", "8小时稳定性测试失败"
        assert stability_result["uptime_hours"] >= 8, "运行时间不足8小时"
        
        # 验证恢复性能
        recovery_stats = stability_result.get("recovery_stats", {})
        if recovery_stats.get("total_failures", 0) > 0:
            recovery_rate = recovery_stats.get("successful_recoveries", 0) / recovery_stats["total_failures"]
            assert recovery_rate >= 0.9, f"长期稳定性恢复率不足: {recovery_rate:.2%}"

    def test_concurrent_recovery_operations(self):
        """测试并发恢复操作"""
        recovery_results = []
        recovery_errors = []
        
        def recovery_worker(worker_id: int, operation_type: str):
            try:
                start_time = time.time()
                
                if operation_type == "checkpoint":
                    checkpoint_file = os.path.join(self.temp_dir, f"checkpoint_{worker_id}.json")
                    save_success = self.recovery_manager.save_checkpoint(
                        self.sample_project_data, checkpoint_file
                    )
                    load_success = self.recovery_manager.load_checkpoint(checkpoint_file) is not None
                    success = save_success and load_success
                    
                elif operation_type == "memory":
                    success = self.memory_guard.emergency_cleanup()
                    
                elif operation_type == "file":
                    test_file = os.path.join(self.temp_dir, f"test_{worker_id}.json")
                    with open(test_file, 'w') as f:
                        f.write('{"test": "data"}')
                    success = self.recovery_manager.load_project_file(test_file) is not None
                
                recovery_time = time.time() - start_time
                recovery_results.append((worker_id, operation_type, success, recovery_time))
                
            except Exception as e:
                recovery_errors.append((worker_id, operation_type, str(e)))
        
        # 创建并发恢复线程
        threads = []
        operations = ["checkpoint", "memory", "file"]
        
        for i in range(12):  # 12个并发线程
            operation = operations[i % len(operations)]
            thread = threading.Thread(target=recovery_worker, args=(i, operation))
            threads.append(thread)
        
        # 启动并等待完成
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=60)
        
        # 验证并发恢复结果
        assert len(recovery_errors) == 0, f"并发恢复出现错误: {recovery_errors}"
        assert len(recovery_results) == 12, f"并发恢复结果不完整: {len(recovery_results)}/12"
        
        # 验证所有恢复操作成功
        successful_recoveries = sum(1 for _, _, success, _ in recovery_results if success)
        success_rate = successful_recoveries / len(recovery_results)
        assert success_rate >= 0.9, f"并发恢复成功率不足: {success_rate:.2%}"

    def test_cascading_failure_recovery(self):
        """测试级联故障恢复"""
        # 模拟级联故障场景
        failure_chain = [
            {"type": "memory_pressure", "severity": "high"},
            {"type": "file_corruption", "affected_files": ["config.json", "checkpoint.json"]},
            {"type": "network_failure", "duration": 30},
            {"type": "model_error", "model": "zh"}
        ]
        
        recovery_success_count = 0
        
        for i, failure in enumerate(failure_chain):
            try:
                # 模拟故障
                if failure["type"] == "memory_pressure":
                    # 触发内存压力
                    memory_hog = bytearray(500 * 1024 * 1024)  # 500MB
                    recovery_result = self.memory_guard.handle_memory_pressure(failure["severity"])
                    del memory_hog
                    
                elif failure["type"] == "file_corruption":
                    # 模拟文件损坏
                    for filename in failure["affected_files"]:
                        corrupted_file = os.path.join(self.temp_dir, filename)
                        with open(corrupted_file, 'w') as f:
                            f.write("corrupted data")
                        recovery_result = self.recovery_manager.recover_corrupted_file(
                            corrupted_file, self.temp_dir
                        )
                        
                elif failure["type"] == "network_failure":
                    # 模拟网络故障
                    recovery_result = self.recovery_manager.handle_network_failure(
                        duration=failure["duration"]
                    )
                    
                elif failure["type"] == "model_error":
                    # 模拟模型错误
                    recovery_result = self.recovery_manager.handle_model_error(
                        model_name=failure["model"]
                    )
                
                # 验证恢复结果
                if recovery_result and recovery_result.get("status") == "recovered":
                    recovery_success_count += 1
                    
            except Exception as e:
                print(f"级联故障{i}恢复失败: {str(e)}")
        
        # 验证级联恢复成功率
        cascade_recovery_rate = recovery_success_count / len(failure_chain)
        assert cascade_recovery_rate >= 0.75, \
            f"级联故障恢复率不足: {cascade_recovery_rate:.2%} (目标: ≥75%)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
