#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 实时日志功能测试脚本

测试内容：
1. UI组件导入测试
2. 日志处理器功能测试
3. 实时日志显示测试
4. 信号槽机制测试
5. 性能标准验证
"""

import sys
import os
import time
import logging
import threading
import psutil
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class LoggingTestSuite:
    """实时日志功能测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("VisionAI-ClipsMaster 实时日志功能测试")
        print("=" * 60)
        
        tests = [
            ("UI组件导入测试", self.test_ui_imports),
            ("日志处理器功能测试", self.test_log_handler),
            ("核心模块日志集成测试", self.test_core_module_logging),
            ("实时日志显示测试", self.test_realtime_display),
            ("信号槽机制测试", self.test_signal_mechanism),
            ("性能标准验证", self.test_performance_standards),
        ]
        
        for test_name, test_func in tests:
            print(f"\n[测试] {test_name}")
            try:
                result = test_func()
                self.test_results[test_name] = result
                status = "✅ 通过" if result["success"] else "❌ 失败"
                print(f"[结果] {status} - {result.get('message', '')}")
            except Exception as e:
                self.test_results[test_name] = {"success": False, "error": str(e)}
                print(f"[结果] ❌ 异常 - {str(e)}")
        
        self.generate_report()
    
    def test_ui_imports(self):
        """测试UI组件导入"""
        try:
            # 测试主窗口导入
            from src.visionai_clipsmaster.ui.main_window import SimpleScreenplayApp, LogHandler, log_signal_emitter
            
            # 测试UI组件导入
            from src.ui.training_panel import TrainingPanel
            from src.ui.progress_dashboard import ProgressDashboard
            from src.ui.realtime_charts import RealtimeCharts
            from src.ui.alert_manager import AlertManager
            
            return {
                "success": True,
                "message": "所有UI组件导入成功",
                "components": ["SimpleScreenplayApp", "TrainingPanel", "ProgressDashboard", "RealtimeCharts", "AlertManager"]
            }
        except ImportError as e:
            return {"success": False, "message": f"导入失败: {e}"}
    
    def test_log_handler(self):
        """测试日志处理器功能"""
        try:
            from src.visionai_clipsmaster.ui.main_window import LogHandler
            
            # 创建日志处理器
            log_handler = LogHandler("test_logger")
            
            # 测试日志记录
            test_messages = [
                ("info", "测试信息日志"),
                ("warning", "测试警告日志"),
                ("error", "测试错误日志"),
            ]
            
            for level, message in test_messages:
                log_handler.log(level, message)
            
            # 测试日志获取
            logs = log_handler.get_logs(n=10)
            realtime_logs = log_handler.get_realtime_logs(n=10)
            
            return {
                "success": True,
                "message": f"日志处理器功能正常，文件日志: {len(logs)}条，实时缓存: {len(realtime_logs)}条",
                "file_logs": len(logs),
                "cache_logs": len(realtime_logs)
            }
        except Exception as e:
            return {"success": False, "message": f"日志处理器测试失败: {e}"}
    
    def test_core_module_logging(self):
        """测试核心模块日志集成"""
        try:
            # 测试screenplay_engineer日志
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()
            engineer.load_subtitles([])  # 触发日志
            
            # 测试model_switcher日志
            from src.core.model_switcher import ModelSwitcher
            switcher = ModelSwitcher()
            switcher.switch_model("zh")  # 触发日志
            
            # 测试clip_generator日志
            try:
                from src.core.clip_generator import ClipGenerator
                generator = ClipGenerator()
                # generator会在初始化时记录日志
            except ImportError:
                # 使用备用导入
                from src.core.clip_generator import clip_generator
                # clip_generator是全局实例
            
            # 测试jianying_exporter日志
            from src.exporters.jianying_pro_exporter import JianYingProExporter
            exporter = JianYingProExporter()
            # exporter会在初始化时记录日志
            
            return {
                "success": True,
                "message": "核心模块日志集成正常",
                "modules": ["screenplay_engineer", "model_switcher", "clip_generator", "jianying_exporter"]
            }
        except Exception as e:
            return {"success": False, "message": f"核心模块日志测试失败: {e}"}
    
    def test_realtime_display(self):
        """测试实时日志显示"""
        try:
            # 这个测试需要在实际UI环境中运行
            # 这里只测试基础功能
            from src.visionai_clipsmaster.ui.main_window import log_signal_emitter, RealtimeCacheHandler
            
            # 测试信号发射器
            test_callback_called = False
            
            def test_callback(message, level):
                nonlocal test_callback_called
                test_callback_called = True
            
            # 连接测试回调
            log_signal_emitter.log_message.connect(test_callback)
            
            # 发射测试信号
            log_signal_emitter.log_message.emit("测试消息", "INFO")
            
            # 断开连接
            log_signal_emitter.log_message.disconnect(test_callback)
            
            return {
                "success": test_callback_called,
                "message": "实时日志显示机制正常" if test_callback_called else "信号回调未触发",
                "callback_triggered": test_callback_called
            }
        except Exception as e:
            return {"success": False, "message": f"实时显示测试失败: {e}"}
    
    def test_signal_mechanism(self):
        """测试信号槽机制"""
        try:
            from src.visionai_clipsmaster.ui.main_window import log_signal_emitter, LogHandler
            
            # 创建日志处理器
            log_handler = LogHandler("signal_test")
            
            # 测试信号连接
            signal_messages = []
            
            def signal_slot(message, level):
                signal_messages.append((message, level))
            
            # 连接信号
            success = log_handler.connect_to_signal(signal_slot)
            
            if success:
                # 发送测试日志
                log_handler.log("info", "信号测试消息")
                time.sleep(0.1)  # 等待信号处理
                
                # 断开信号
                log_handler.disconnect_from_signal(signal_slot)
            
            return {
                "success": success and len(signal_messages) > 0,
                "message": f"信号槽机制正常，接收到 {len(signal_messages)} 条消息" if success else "信号连接失败",
                "messages_received": len(signal_messages)
            }
        except Exception as e:
            return {"success": False, "message": f"信号机制测试失败: {e}"}
    
    def test_performance_standards(self):
        """测试性能标准"""
        try:
            current_time = time.time()
            startup_time = current_time - self.start_time
            
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_usage = current_memory - self.memory_start
            
            # 性能标准
            startup_ok = startup_time <= 5.0  # 启动时间≤5秒
            memory_ok = current_memory <= 400  # 内存使用≤400MB
            
            return {
                "success": startup_ok and memory_ok,
                "message": f"启动时间: {startup_time:.2f}s, 内存使用: {current_memory:.1f}MB",
                "startup_time": startup_time,
                "memory_usage": current_memory,
                "startup_ok": startup_ok,
                "memory_ok": memory_ok
            }
        except Exception as e:
            return {"success": False, "message": f"性能测试失败: {e}"}
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅" if result.get("success", False) else "❌"
            print(f"{status} {test_name}: {result.get('message', '无消息')}")
        
        # 保存报告到文件
        report_file = f"realtime_logging_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"VisionAI-ClipsMaster 实时日志功能测试报告\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"通过率: {passed_tests/total_tests*100:.1f}%\n\n")
            
            for test_name, result in self.test_results.items():
                f.write(f"{test_name}: {'通过' if result.get('success', False) else '失败'}\n")
                f.write(f"  消息: {result.get('message', '无消息')}\n")
                if 'error' in result:
                    f.write(f"  错误: {result['error']}\n")
                f.write("\n")
        
        print(f"\n测试报告已保存到: {report_file}")

if __name__ == "__main__":
    # 运行测试
    test_suite = LoggingTestSuite()
    test_suite.run_all_tests()
