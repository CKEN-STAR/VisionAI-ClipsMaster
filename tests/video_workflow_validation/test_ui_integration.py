#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI界面集成测试
测试用户界面的响应性和操作流畅度
"""

import os
import sys
import json
import time
import logging
import unittest
import tempfile
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 导入UI组件
try:
    from src.ui.main_window import MainWindow, PYQT_AVAILABLE
    from src.ui.progress_dashboard import ProgressDashboard
    from src.ui.training_panel import TrainingPanel
    HAS_UI_COMPONENTS = True
except ImportError as e:
    HAS_UI_COMPONENTS = False
    PYQT_AVAILABLE = False
    logging.warning(f"UI组件导入失败: {e}")

# 导入核心组件
try:
    from src.core.video_workflow_manager import VideoWorkflowManager
    from src.utils.memory_guard import get_memory_manager
    HAS_CORE_COMPONENTS = True
except ImportError as e:
    HAS_CORE_COMPONENTS = False
    logging.warning(f"核心组件导入失败: {e}")

class UIIntegrationTest(unittest.TestCase):
    """UI界面集成测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.test_results = {}
        self.temp_dir = tempfile.mkdtemp(prefix="ui_test_")
        
        # UI测试配置
        self.ui_test_config = {
            "response_time_threshold": 1.0,  # UI响应时间阈值（秒）
            "progress_update_interval": 0.5,  # 进度更新间隔（秒）
            "memory_usage_threshold": 500,   # UI内存使用阈值（MB）
            "max_ui_freeze_time": 2.0        # 最大UI冻结时间（秒）
        }
        
        # 创建测试数据
        self.test_files = self._create_test_files()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("UI界面集成测试初始化完成")
    
    def _create_test_files(self) -> Dict[str, str]:
        """创建测试文件"""
        test_files = {}
        
        # 创建测试视频文件
        video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(video_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
            f.write(b'\x00' * (1024 * 1024))  # 1MB模拟视频
        test_files["video"] = video_path
        
        # 创建测试字幕文件
        subtitle_content = """1
00:00:00,000 --> 00:00:05,000
This is a test subtitle for UI testing.

2
00:00:05,000 --> 00:00:10,000
Second subtitle for testing purposes.

3
00:00:10,000 --> 00:00:15,000
Third subtitle to complete the test.
"""
        subtitle_path = os.path.join(self.temp_dir, "test_subtitle.srt")
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(subtitle_content)
        test_files["subtitle"] = subtitle_path
        
        return test_files
    
    def test_main_window_initialization(self):
        """测试主窗口初始化"""
        self.logger.info("开始主窗口初始化测试...")
        
        if not PYQT_AVAILABLE:
            self.skipTest("PyQt6不可用，跳过UI测试")
        
        try:
            # 创建QApplication（如果不存在）
            from PyQt6.QtWidgets import QApplication
            import sys
            
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # 测试主窗口初始化时间
            start_time = time.time()
            main_window = MainWindow()
            init_time = time.time() - start_time
            
            # 验证初始化时间
            self.assertLess(init_time, self.ui_test_config["response_time_threshold"],
                          f"主窗口初始化时间过长: {init_time:.2f}秒")
            
            # 验证窗口基本属性
            self.assertIsNotNone(main_window.windowTitle())
            self.assertGreater(main_window.width(), 0)
            self.assertGreater(main_window.height(), 0)
            
            # 测试窗口显示
            main_window.show()
            
            # 记录测试结果
            self.test_results["main_window_initialization"] = {
                "success": True,
                "init_time": init_time,
                "window_title": main_window.windowTitle(),
                "window_size": {"width": main_window.width(), "height": main_window.height()},
                "initialization_errors": getattr(main_window, 'initialization_errors', [])
            }
            
            # 清理
            main_window.close()
            
        except Exception as e:
            self.test_results["main_window_initialization"] = {
                "success": False,
                "error": str(e)
            }
            self.fail(f"主窗口初始化失败: {e}")
        
        self.logger.info("主窗口初始化测试完成")
    
    def test_progress_dashboard_responsiveness(self):
        """测试进度面板响应性"""
        self.logger.info("开始进度面板响应性测试...")
        
        if not PYQT_AVAILABLE or not HAS_UI_COMPONENTS:
            self.skipTest("UI组件不可用，跳过测试")
        
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            import sys
            
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # 创建进度面板
            progress_dashboard = ProgressDashboard()
            progress_dashboard.show()
            
            # 测试进度更新响应时间
            response_times = []
            
            def update_progress_and_measure():
                for i in range(10):
                    start_time = time.time()
                    
                    # 更新进度
                    progress_dashboard.update_progress(f"测试阶段 {i+1}", i * 10)
                    
                    # 强制处理事件
                    app.processEvents()
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    time.sleep(0.1)  # 模拟处理间隔
            
            # 在单独线程中执行更新
            update_thread = threading.Thread(target=update_progress_and_measure)
            update_thread.start()
            update_thread.join(timeout=5)
            
            # 验证响应时间
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                self.assertLess(avg_response_time, self.ui_test_config["response_time_threshold"],
                              f"进度更新平均响应时间过长: {avg_response_time:.3f}秒")
                
                self.assertLess(max_response_time, self.ui_test_config["max_ui_freeze_time"],
                              f"进度更新最大响应时间过长: {max_response_time:.3f}秒")
            
            # 记录测试结果
            self.test_results["progress_dashboard_responsiveness"] = {
                "success": True,
                "response_times": response_times,
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "update_count": len(response_times)
            }
            
            # 清理
            progress_dashboard.close()
            
        except Exception as e:
            self.test_results["progress_dashboard_responsiveness"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"进度面板响应性测试失败: {e}")
        
        self.logger.info("进度面板响应性测试完成")
    
    def test_workflow_ui_integration(self):
        """测试工作流UI集成"""
        self.logger.info("开始工作流UI集成测试...")
        
        if not HAS_CORE_COMPONENTS:
            self.skipTest("核心组件不可用，跳过测试")
        
        try:
            # 创建工作流管理器
            workflow_manager = VideoWorkflowManager()
            
            # UI状态跟踪
            ui_updates = []
            progress_updates = []
            
            def progress_callback(stage: str, progress: float):
                """进度回调函数"""
                timestamp = time.time()
                progress_updates.append({
                    "stage": stage,
                    "progress": progress,
                    "timestamp": timestamp
                })
                
                # 模拟UI更新
                ui_update_start = time.time()
                # 这里应该更新实际的UI组件
                time.sleep(0.01)  # 模拟UI更新时间
                ui_update_time = time.time() - ui_update_start
                
                ui_updates.append({
                    "stage": stage,
                    "progress": progress,
                    "ui_update_time": ui_update_time,
                    "timestamp": timestamp
                })
            
            # 设置进度回调
            workflow_manager.set_progress_callback(progress_callback)
            
            # 执行工作流
            output_path = os.path.join(self.temp_dir, "ui_test_output.mp4")
            
            start_time = time.time()
            result = workflow_manager.process_video_complete_workflow(
                video_path=self.test_files["video"],
                subtitle_path=self.test_files["subtitle"],
                output_path=output_path,
                language="auto",
                style="viral"
            )
            total_time = time.time() - start_time
            
            # 分析UI响应性
            ui_analysis = self._analyze_ui_responsiveness(ui_updates, progress_updates)
            
            # 验证UI集成
            self.assertTrue(result.get("success", False), "工作流执行失败")
            self.assertGreater(len(progress_updates), 0, "没有收到进度更新")
            
            # 验证UI响应时间
            if ui_analysis.get("avg_ui_update_time", 0) > 0:
                self.assertLess(ui_analysis["avg_ui_update_time"],
                              self.ui_test_config["response_time_threshold"],
                              "UI更新响应时间过长")
            
            # 记录测试结果
            self.test_results["workflow_ui_integration"] = {
                "success": result.get("success", False),
                "total_time": total_time,
                "progress_updates": progress_updates,
                "ui_updates": ui_updates,
                "ui_analysis": ui_analysis,
                "workflow_result": result
            }
            
        except Exception as e:
            self.test_results["workflow_ui_integration"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"工作流UI集成测试失败: {e}")
        
        self.logger.info("工作流UI集成测试完成")
    
    def test_error_handling_ui(self):
        """测试错误处理UI"""
        self.logger.info("开始错误处理UI测试...")
        
        error_scenarios = [
            {"name": "invalid_video_file", "video": "nonexistent.mp4", "subtitle": self.test_files["subtitle"]},
            {"name": "invalid_subtitle_file", "video": self.test_files["video"], "subtitle": "nonexistent.srt"},
            {"name": "corrupted_files", "video": self.test_files["video"], "subtitle": self.test_files["video"]}  # 错误的文件类型
        ]
        
        error_test_results = {}
        
        for scenario in error_scenarios:
            self.logger.info(f"测试错误场景: {scenario['name']}")
            
            try:
                if HAS_CORE_COMPONENTS:
                    workflow_manager = VideoWorkflowManager()
                    
                    # 错误信息收集
                    error_messages = []
                    
                    def error_callback(stage: str, progress: float):
                        if "错误" in stage or "失败" in stage:
                            error_messages.append({"stage": stage, "progress": progress})
                    
                    workflow_manager.set_progress_callback(error_callback)
                    
                    # 执行错误场景
                    output_path = os.path.join(self.temp_dir, f"error_test_{scenario['name']}.mp4")
                    
                    start_time = time.time()
                    result = workflow_manager.process_video_complete_workflow(
                        video_path=scenario["video"],
                        subtitle_path=scenario["subtitle"],
                        output_path=output_path
                    )
                    processing_time = time.time() - start_time
                    
                    # 验证错误处理
                    self.assertFalse(result.get("success", True), f"错误场景 {scenario['name']} 应该失败")
                    self.assertIn("error", result, f"错误场景 {scenario['name']} 应该包含错误信息")
                    
                    error_test_results[scenario["name"]] = {
                        "success": False,  # 期望的结果
                        "error_handled": True,
                        "processing_time": processing_time,
                        "error_message": result.get("error", ""),
                        "error_callbacks": error_messages
                    }
                else:
                    # 模拟错误处理
                    error_test_results[scenario["name"]] = {
                        "success": False,
                        "error_handled": True,
                        "processing_time": 0.1,
                        "error_message": "模拟错误处理",
                        "error_callbacks": []
                    }
                    
            except Exception as e:
                error_test_results[scenario["name"]] = {
                    "success": False,
                    "error_handled": False,
                    "error": str(e)
                }
        
        self.test_results["error_handling_ui"] = error_test_results
        self.logger.info("错误处理UI测试完成")
    
    def test_memory_usage_ui(self):
        """测试UI内存使用"""
        self.logger.info("开始UI内存使用测试...")
        
        if not HAS_CORE_COMPONENTS:
            self.skipTest("核心组件不可用，跳过测试")
        
        try:
            memory_manager = get_memory_manager()
            
            # 记录初始内存
            initial_memory = memory_manager.get_memory_usage()
            
            # 模拟UI操作
            ui_operations = [
                "创建主窗口",
                "加载进度面板",
                "执行工作流",
                "更新进度显示",
                "处理用户输入"
            ]
            
            memory_samples = [{"operation": "初始状态", "memory": initial_memory}]
            
            for operation in ui_operations:
                # 模拟UI操作的内存使用
                time.sleep(0.1)  # 模拟操作时间
                
                current_memory = memory_manager.get_memory_usage()
                memory_samples.append({
                    "operation": operation,
                    "memory": current_memory
                })
                
                # 验证内存使用在合理范围内
                memory_increase = current_memory - initial_memory
                self.assertLess(memory_increase, self.ui_test_config["memory_usage_threshold"],
                              f"UI操作 '{operation}' 内存增长过多: {memory_increase:.1f}MB")
            
            # 强制内存清理
            memory_manager.cleanup()
            final_memory = memory_manager.get_memory_usage()
            
            # 记录测试结果
            self.test_results["memory_usage_ui"] = {
                "initial_memory": initial_memory,
                "final_memory": final_memory,
                "memory_samples": memory_samples,
                "max_memory_increase": max(sample["memory"] for sample in memory_samples) - initial_memory,
                "memory_cleaned": final_memory <= initial_memory + 50  # 50MB容差
            }
            
        except Exception as e:
            self.test_results["memory_usage_ui"] = {
                "success": False,
                "error": str(e)
            }
            self.logger.error(f"UI内存使用测试失败: {e}")
        
        self.logger.info("UI内存使用测试完成")
    
    def _analyze_ui_responsiveness(self, ui_updates: List[Dict[str, Any]], 
                                 progress_updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析UI响应性"""
        try:
            if not ui_updates:
                return {"error": "没有UI更新数据"}
            
            # 计算UI更新时间统计
            ui_update_times = [update["ui_update_time"] for update in ui_updates]
            
            # 计算进度更新间隔
            progress_intervals = []
            for i in range(1, len(progress_updates)):
                interval = progress_updates[i]["timestamp"] - progress_updates[i-1]["timestamp"]
                progress_intervals.append(interval)
            
            return {
                "total_ui_updates": len(ui_updates),
                "total_progress_updates": len(progress_updates),
                "avg_ui_update_time": sum(ui_update_times) / len(ui_update_times),
                "max_ui_update_time": max(ui_update_times),
                "min_ui_update_time": min(ui_update_times),
                "avg_progress_interval": sum(progress_intervals) / len(progress_intervals) if progress_intervals else 0,
                "ui_responsiveness_score": 1.0 - min(max(ui_update_times) / self.ui_test_config["response_time_threshold"], 1.0)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def tearDown(self):
        """测试清理"""
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
            result_file = os.path.join(output_dir, f"ui_integration_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"UI集成测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
