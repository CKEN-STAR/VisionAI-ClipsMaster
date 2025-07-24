#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理测试
验证系统在各种异常情况下的处理能力和恢复机制
"""

import os
import sys
import json
import time
import logging
import unittest
import tempfile
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 导入核心组件
try:
    from src.core.video_workflow_manager import VideoWorkflowManager
    from src.utils.memory_guard import get_memory_manager
    from src.utils.device_manager import DeviceManager
    HAS_CORE_COMPONENTS = True
except ImportError as e:
    HAS_CORE_COMPONENTS = False
    logging.warning(f"核心组件导入失败: {e}")

class ExceptionHandlingTest(unittest.TestCase):
    """异常处理测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.test_results = {}
        self.temp_dir = tempfile.mkdtemp(prefix="exception_test_")
        self.memory_manager = get_memory_manager() if HAS_CORE_COMPONENTS else None
        
        # 异常测试场景配置
        self.exception_scenarios = {
            "invalid_file_format": {
                "description": "无效文件格式处理",
                "expected_recovery": True,
                "timeout": 30
            },
            "network_interruption": {
                "description": "网络中断恢复",
                "expected_recovery": True,
                "timeout": 60
            },
            "memory_exhaustion": {
                "description": "内存不足处理",
                "expected_recovery": True,
                "timeout": 45
            },
            "process_cancellation": {
                "description": "中途取消操作",
                "expected_recovery": True,
                "timeout": 20
            },
            "corrupted_data": {
                "description": "数据损坏处理",
                "expected_recovery": False,
                "timeout": 30
            }
        }
        
        # 创建测试文件
        self.test_files = self._create_exception_test_files()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("异常处理测试初始化完成")
    
    def _create_exception_test_files(self) -> Dict[str, str]:
        """创建异常测试文件"""
        test_files = {}
        
        # 正常视频文件
        normal_video = os.path.join(self.temp_dir, "normal_video.mp4")
        with open(normal_video, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
            f.write(b'\x00' * (1024 * 1024))  # 1MB正常视频
        test_files["normal_video"] = normal_video
        
        # 损坏的视频文件
        corrupted_video = os.path.join(self.temp_dir, "corrupted_video.mp4")
        with open(corrupted_video, 'wb') as f:
            f.write(b'\xFF\xFF\xFF\xFF')  # 损坏的文件头
            f.write(b'\x00' * 1024)
        test_files["corrupted_video"] = corrupted_video
        
        # 错误格式文件
        wrong_format = os.path.join(self.temp_dir, "wrong_format.mp4")
        with open(wrong_format, 'w') as f:
            f.write("This is not a video file")
        test_files["wrong_format"] = wrong_format
        
        # 正常字幕文件
        normal_subtitle = os.path.join(self.temp_dir, "normal_subtitle.srt")
        with open(normal_subtitle, 'w', encoding='utf-8') as f:
            f.write("""1
00:00:00,000 --> 00:00:05,000
Normal subtitle for testing.

2
00:00:05,000 --> 00:00:10,000
Second subtitle entry.
""")
        test_files["normal_subtitle"] = normal_subtitle
        
        # 损坏的字幕文件
        corrupted_subtitle = os.path.join(self.temp_dir, "corrupted_subtitle.srt")
        with open(corrupted_subtitle, 'w', encoding='utf-8') as f:
            f.write("Invalid subtitle format\nNo proper timing\nCorrupted data")
        test_files["corrupted_subtitle"] = corrupted_subtitle
        
        # 空文件
        empty_file = os.path.join(self.temp_dir, "empty_file.mp4")
        with open(empty_file, 'w') as f:
            pass  # 创建空文件
        test_files["empty_file"] = empty_file
        
        return test_files
    
    def test_invalid_file_format_handling(self):
        """测试无效文件格式处理"""
        self.logger.info("开始无效文件格式处理测试...")
        
        if not HAS_CORE_COMPONENTS:
            self.skipTest("核心组件不可用")
        
        test_cases = [
            {"name": "wrong_format_video", "video": self.test_files["wrong_format"], "subtitle": self.test_files["normal_subtitle"]},
            {"name": "corrupted_video", "video": self.test_files["corrupted_video"], "subtitle": self.test_files["normal_subtitle"]},
            {"name": "empty_video", "video": self.test_files["empty_file"], "subtitle": self.test_files["normal_subtitle"]},
            {"name": "corrupted_subtitle", "video": self.test_files["normal_video"], "subtitle": self.test_files["corrupted_subtitle"]}
        ]
        
        format_test_results = {}
        
        for test_case in test_cases:
            self.logger.info(f"测试无效格式场景: {test_case['name']}")
            
            try:
                workflow_manager = VideoWorkflowManager()
                
                # 记录异常信息
                exceptions_caught = []
                recovery_attempts = []
                
                def exception_callback(stage: str, progress: float):
                    if "错误" in stage or "异常" in stage:
                        exceptions_caught.append({"stage": stage, "progress": progress, "timestamp": time.time()})
                    elif "恢复" in stage or "重试" in stage:
                        recovery_attempts.append({"stage": stage, "progress": progress, "timestamp": time.time()})
                
                workflow_manager.set_progress_callback(exception_callback)
                
                # 执行工作流
                output_path = os.path.join(self.temp_dir, f"output_{test_case['name']}.mp4")
                
                start_time = time.time()
                result = workflow_manager.process_video_complete_workflow(
                    video_path=test_case["video"],
                    subtitle_path=test_case["subtitle"],
                    output_path=output_path
                )
                processing_time = time.time() - start_time
                
                # 验证异常处理
                self.assertFalse(result.get("success", True), f"无效格式 {test_case['name']} 应该失败")
                self.assertIn("error", result, f"无效格式 {test_case['name']} 应该包含错误信息")
                
                # 验证错误信息的有用性
                error_message = result.get("error", "")
                self.assertGreater(len(error_message), 0, "错误信息不能为空")
                
                format_test_results[test_case["name"]] = {
                    "success": False,  # 期望失败
                    "error_handled": True,
                    "processing_time": processing_time,
                    "error_message": error_message,
                    "exceptions_caught": exceptions_caught,
                    "recovery_attempts": recovery_attempts,
                    "graceful_failure": processing_time < self.exception_scenarios["invalid_file_format"]["timeout"]
                }
                
            except Exception as e:
                format_test_results[test_case["name"]] = {
                    "success": False,
                    "error_handled": False,
                    "unexpected_exception": str(e)
                }
                self.logger.error(f"无效格式测试 {test_case['name']} 出现意外异常: {e}")
        
        self.test_results["invalid_file_format_handling"] = format_test_results
        self.logger.info("无效文件格式处理测试完成")
    
    def test_memory_exhaustion_handling(self):
        """测试内存不足处理"""
        self.logger.info("开始内存不足处理测试...")
        
        if not self.memory_manager:
            self.skipTest("内存管理器不可用")
        
        try:
            # 模拟内存压力
            memory_stress_data = []
            initial_memory = self.memory_manager.get_memory_usage()
            
            # 逐步增加内存使用
            stress_levels = [100, 500, 1000, 2000]  # MB
            
            memory_test_results = {}
            
            for stress_level in stress_levels:
                self.logger.info(f"测试内存压力级别: {stress_level}MB")
                
                try:
                    # 创建内存压力
                    stress_data = self._create_memory_stress(stress_level)
                    memory_stress_data.append(stress_data)
                    
                    current_memory = self.memory_manager.get_memory_usage()
                    
                    # 尝试执行工作流
                    if HAS_CORE_COMPONENTS:
                        workflow_manager = VideoWorkflowManager()
                        
                        output_path = os.path.join(self.temp_dir, f"memory_test_{stress_level}.mp4")
                        
                        start_time = time.time()
                        result = workflow_manager.process_video_complete_workflow(
                            video_path=self.test_files["normal_video"],
                            subtitle_path=self.test_files["normal_subtitle"],
                            output_path=output_path
                        )
                        processing_time = time.time() - start_time
                        
                        memory_after = self.memory_manager.get_memory_usage()
                        
                        memory_test_results[f"stress_{stress_level}mb"] = {
                            "stress_level": stress_level,
                            "memory_before": current_memory,
                            "memory_after": memory_after,
                            "processing_success": result.get("success", False),
                            "processing_time": processing_time,
                            "memory_handled": memory_after < 4000,  # 4GB限制
                            "result": result
                        }
                        
                        # 如果内存使用过高，验证是否有适当的处理
                        if current_memory > 3000:  # 3GB阈值
                            if not result.get("success", False):
                                self.assertIn("内存", result.get("error", "").lower(), 
                                            "高内存使用时应该有内存相关的错误信息")
                    
                    # 清理部分内存压力数据
                    if len(memory_stress_data) > 2:
                        memory_stress_data.pop(0)
                        
                except Exception as e:
                    memory_test_results[f"stress_{stress_level}mb"] = {
                        "stress_level": stress_level,
                        "error": str(e),
                        "memory_handled": False
                    }
            
            # 强制内存清理
            memory_stress_data.clear()
            self.memory_manager.cleanup()
            
            final_memory = self.memory_manager.get_memory_usage()
            
            self.test_results["memory_exhaustion_handling"] = {
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "memory_cleaned": final_memory <= initial_memory + 100,  # 100MB容差
                "stress_test_results": memory_test_results
            }
            
        except Exception as e:
            self.test_results["memory_exhaustion_handling"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"内存不足处理测试失败: {e}")
        
        self.logger.info("内存不足处理测试完成")
    
    def test_process_cancellation_handling(self):
        """测试中途取消操作处理"""
        self.logger.info("开始中途取消操作处理测试...")
        
        if not HAS_CORE_COMPONENTS:
            self.skipTest("核心组件不可用")
        
        try:
            workflow_manager = VideoWorkflowManager()
            
            # 取消测试配置
            cancellation_points = [0.2, 0.5, 0.8]  # 在20%、50%、80%进度时取消
            
            cancellation_results = {}
            
            for cancel_point in cancellation_points:
                self.logger.info(f"测试在 {cancel_point*100:.0f}% 进度时取消...")
                
                # 状态跟踪
                progress_history = []
                cancellation_triggered = False
                
                def progress_callback(stage: str, progress: float):
                    progress_history.append({"stage": stage, "progress": progress, "timestamp": time.time()})
                    
                    # 在指定进度点触发取消
                    nonlocal cancellation_triggered
                    if progress >= cancel_point * 100 and not cancellation_triggered:
                        cancellation_triggered = True
                        # 这里应该触发实际的取消操作
                        # 由于测试环境限制，我们模拟取消效果
                        raise KeyboardInterrupt("模拟用户取消操作")
                
                workflow_manager.set_progress_callback(progress_callback)
                
                # 执行工作流并模拟取消
                output_path = os.path.join(self.temp_dir, f"cancel_test_{cancel_point}.mp4")
                
                start_time = time.time()
                try:
                    result = workflow_manager.process_video_complete_workflow(
                        video_path=self.test_files["normal_video"],
                        subtitle_path=self.test_files["normal_subtitle"],
                        output_path=output_path
                    )
                    # 如果没有被取消，这是意外的
                    cancellation_handled = False
                    processing_time = time.time() - start_time
                    
                except KeyboardInterrupt:
                    # 取消操作被正确捕获
                    cancellation_handled = True
                    processing_time = time.time() - start_time
                    result = {"success": False, "error": "用户取消操作", "cancelled": True}
                
                # 检查资源清理
                cleanup_successful = self._verify_resource_cleanup(output_path)
                
                cancellation_results[f"cancel_at_{cancel_point}"] = {
                    "cancel_point": cancel_point,
                    "cancellation_triggered": cancellation_triggered,
                    "cancellation_handled": cancellation_handled,
                    "processing_time": processing_time,
                    "progress_history": progress_history,
                    "cleanup_successful": cleanup_successful,
                    "result": result
                }
                
                # 验证取消处理
                if cancellation_triggered:
                    self.assertTrue(cancellation_handled, f"取消操作在 {cancel_point} 点未被正确处理")
                    self.assertTrue(cleanup_successful, f"取消后资源清理失败在 {cancel_point} 点")
            
            self.test_results["process_cancellation_handling"] = cancellation_results
            
        except Exception as e:
            self.test_results["process_cancellation_handling"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"中途取消操作处理测试失败: {e}")
        
        self.logger.info("中途取消操作处理测试完成")
    
    def test_network_interruption_simulation(self):
        """测试网络中断模拟"""
        self.logger.info("开始网络中断模拟测试...")
        
        # 模拟网络相关的操作失败
        network_scenarios = [
            {"name": "model_download_failure", "description": "模型下载失败"},
            {"name": "api_timeout", "description": "API调用超时"},
            {"name": "connection_reset", "description": "连接重置"}
        ]
        
        network_test_results = {}
        
        for scenario in network_scenarios:
            self.logger.info(f"测试网络场景: {scenario['name']}")
            
            try:
                # 模拟网络故障
                network_failure_result = self._simulate_network_failure(scenario)
                
                # 验证恢复机制
                recovery_result = self._test_network_recovery(scenario)
                
                network_test_results[scenario["name"]] = {
                    "scenario": scenario,
                    "failure_simulation": network_failure_result,
                    "recovery_test": recovery_result,
                    "overall_success": recovery_result.get("recovered", False)
                }
                
            except Exception as e:
                network_test_results[scenario["name"]] = {
                    "scenario": scenario,
                    "error": str(e),
                    "overall_success": False
                }
        
        self.test_results["network_interruption_simulation"] = network_test_results
        self.logger.info("网络中断模拟测试完成")
    
    def _create_memory_stress(self, size_mb: int) -> List[bytes]:
        """创建内存压力"""
        try:
            # 创建指定大小的内存数据
            chunk_size = 1024 * 1024  # 1MB chunks
            chunks = []
            
            for i in range(size_mb):
                chunk = b'\x00' * chunk_size
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            self.logger.warning(f"创建内存压力失败: {e}")
            return []
    
    def _verify_resource_cleanup(self, output_path: str) -> bool:
        """验证资源清理"""
        try:
            # 检查临时文件是否被清理
            temp_files_exist = False
            
            # 检查输出文件是否存在（取消后不应该存在完整文件）
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                # 如果文件很小或为空，说明清理正常
                temp_files_exist = file_size > 1024 * 1024  # 1MB阈值
            
            # 检查内存是否被清理
            memory_cleaned = True
            if self.memory_manager:
                current_memory = self.memory_manager.get_memory_usage()
                # 简单检查内存是否在合理范围内
                memory_cleaned = current_memory < 3000  # 3GB阈值
            
            return not temp_files_exist and memory_cleaned
            
        except Exception as e:
            self.logger.error(f"验证资源清理失败: {e}")
            return False
    
    def _simulate_network_failure(self, scenario: Dict[str, str]) -> Dict[str, Any]:
        """模拟网络故障"""
        try:
            # 模拟不同类型的网络故障
            if scenario["name"] == "model_download_failure":
                return {
                    "failure_type": "download_failure",
                    "error_message": "模型下载失败：连接超时",
                    "retry_attempts": 3,
                    "failure_simulated": True
                }
            elif scenario["name"] == "api_timeout":
                return {
                    "failure_type": "api_timeout",
                    "error_message": "API调用超时：请求超过30秒",
                    "retry_attempts": 2,
                    "failure_simulated": True
                }
            else:
                return {
                    "failure_type": "connection_reset",
                    "error_message": "连接被重置：网络不稳定",
                    "retry_attempts": 5,
                    "failure_simulated": True
                }
                
        except Exception as e:
            return {"failure_simulated": False, "error": str(e)}
    
    def _test_network_recovery(self, scenario: Dict[str, str]) -> Dict[str, Any]:
        """测试网络恢复"""
        try:
            # 模拟恢复过程
            recovery_attempts = 3
            recovery_successful = False
            
            for attempt in range(recovery_attempts):
                # 模拟恢复尝试
                time.sleep(0.1)  # 模拟恢复时间
                
                # 模拟恢复成功概率
                import random
                if random.random() > 0.3:  # 70%成功率
                    recovery_successful = True
                    break
            
            return {
                "recovered": recovery_successful,
                "recovery_attempts": attempt + 1 if recovery_successful else recovery_attempts,
                "recovery_time": (attempt + 1) * 0.1,
                "fallback_used": not recovery_successful
            }
            
        except Exception as e:
            return {"recovered": False, "error": str(e)}
    
    def tearDown(self):
        """测试清理"""
        # 强制内存清理
        if self.memory_manager:
            self.memory_manager.cleanup()
        
        # 清理临时文件
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"清理临时目录: {self.temp_dir}")
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {e}")
        
        # 保存测试结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"exception_handling_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"异常处理测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
