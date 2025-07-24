#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.0.1 UI界面功能测试
全面测试UI组件、响应性、主题切换等功能
"""

import sys
import os
import time
import json
import traceback
from datetime import datetime
from pathlib import Path
import psutil
import threading
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QScreen

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

class UITestResult:
    def __init__(self):
        self.test_results = {}
        self.performance_data = {}
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    def add_test_result(self, test_name, passed, details="", error_msg=""):
        self.test_results[test_name] = {
            "passed": passed,
            "details": details,
            "error_msg": error_msg,
            "timestamp": datetime.now().isoformat()
        }
        
    def add_performance_data(self, metric_name, value, unit=""):
        self.performance_data[metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
    def add_error(self, error_msg, traceback_str=""):
        self.errors.append({
            "error": error_msg,
            "traceback": traceback_str,
            "timestamp": datetime.now().isoformat()
        })

class UITester:
    def __init__(self):
        self.result = UITestResult()
        self.app = None
        self.main_window = None
        self.test_timeout = 30  # 30秒超时
        
    def setup_test_environment(self):
        """设置测试环境"""
        try:
            # 创建QApplication
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
                
            # 设置应用属性
            self.app.setApplicationName("VisionAI-ClipsMaster-Test")
            self.app.setApplicationVersion("1.0.1")
            
            self.result.add_test_result("setup_test_environment", True, "测试环境设置成功")
            return True
            
        except Exception as e:
            error_msg = f"测试环境设置失败: {str(e)}"
            self.result.add_test_result("setup_test_environment", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_ui_startup(self):
        """测试UI启动"""
        try:
            start_time = time.time()
            
            # 尝试导入simple_ui_fixed模块
            try:
                import simple_ui_fixed
                self.result.add_test_result("import_simple_ui_fixed", True, "成功导入simple_ui_fixed模块")
            except ImportError as e:
                self.result.add_test_result("import_simple_ui_fixed", False, 
                                          error_msg=f"导入simple_ui_fixed失败: {str(e)}")
                return False
                
            # 尝试创建主窗口
            try:
                # 检查是否有SimpleScreenplayApp类
                if hasattr(simple_ui_fixed, 'SimpleScreenplayApp'):
                    self.main_window = simple_ui_fixed.SimpleScreenplayApp()
                    startup_time = time.time() - start_time
                    self.result.add_performance_data("ui_startup_time", startup_time, "seconds")
                    self.result.add_test_result("create_main_window", True,
                                              f"主窗口创建成功，耗时: {startup_time:.2f}秒")
                elif hasattr(simple_ui_fixed, 'VisionAIClipsMaster'):
                    self.main_window = simple_ui_fixed.VisionAIClipsMaster()
                    startup_time = time.time() - start_time
                    self.result.add_performance_data("ui_startup_time", startup_time, "seconds")
                    self.result.add_test_result("create_main_window", True,
                                              f"主窗口创建成功，耗时: {startup_time:.2f}秒")
                else:
                    self.result.add_test_result("create_main_window", False,
                                              error_msg="simple_ui_fixed中未找到主窗口类")
                    return False
                    
            except Exception as e:
                startup_time = time.time() - start_time
                error_msg = f"主窗口创建失败: {str(e)}"
                self.result.add_test_result("create_main_window", False, error_msg=error_msg)
                self.result.add_error(error_msg, traceback.format_exc())
                return False
                
            return True
            
        except Exception as e:
            error_msg = f"UI启动测试失败: {str(e)}"
            self.result.add_test_result("test_ui_startup", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_ui_components(self):
        """测试UI组件"""
        if not self.main_window:
            self.result.add_test_result("test_ui_components", False, 
                                      error_msg="主窗口未创建，无法测试UI组件")
            return False
            
        try:
            # 测试窗口基本属性
            if hasattr(self.main_window, 'setWindowTitle'):
                self.main_window.setWindowTitle("VisionAI-ClipsMaster v1.0.1 - 测试模式")
                self.result.add_test_result("window_title", True, "窗口标题设置成功")
            else:
                self.result.add_test_result("window_title", False, "窗口标题设置失败")
                
            # 测试窗口大小
            if hasattr(self.main_window, 'resize'):
                self.main_window.resize(1200, 800)
                self.result.add_test_result("window_resize", True, "窗口大小调整成功")
            else:
                self.result.add_test_result("window_resize", False, "窗口大小调整失败")
                
            # 测试窗口显示
            if hasattr(self.main_window, 'show'):
                self.main_window.show()
                self.result.add_test_result("window_show", True, "窗口显示成功")
            else:
                self.result.add_test_result("window_show", False, "窗口显示失败")
                
            # 检查窗口是否可见
            if hasattr(self.main_window, 'isVisible'):
                is_visible = self.main_window.isVisible()
                self.result.add_test_result("window_visible", is_visible, 
                                          f"窗口可见性: {is_visible}")
            
            return True
            
        except Exception as e:
            error_msg = f"UI组件测试失败: {str(e)}"
            self.result.add_test_result("test_ui_components", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_performance_monitoring(self):
        """测试性能监控"""
        try:
            # 获取当前进程信息
            process = psutil.Process()
            
            # CPU使用率
            cpu_percent = process.cpu_percent(interval=1)
            self.result.add_performance_data("cpu_usage", cpu_percent, "%")
            
            # 内存使用
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.result.add_performance_data("memory_usage", memory_mb, "MB")
            
            # 线程数
            thread_count = process.num_threads()
            self.result.add_performance_data("thread_count", thread_count, "threads")
            
            self.result.add_test_result("performance_monitoring", True, 
                                      f"性能监控数据收集成功 - CPU: {cpu_percent}%, 内存: {memory_mb:.1f}MB")
            return True
            
        except Exception as e:
            error_msg = f"性能监控测试失败: {str(e)}"
            self.result.add_test_result("performance_monitoring", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_high_dpi_support(self):
        """测试高DPI支持"""
        try:
            if self.app:
                # 获取屏幕信息
                screen = self.app.primaryScreen()
                if screen:
                    dpi = screen.logicalDotsPerInch()
                    device_pixel_ratio = screen.devicePixelRatio()
                    
                    self.result.add_performance_data("screen_dpi", dpi, "DPI")
                    self.result.add_performance_data("device_pixel_ratio", device_pixel_ratio, "ratio")
                    
                    # 检查高DPI支持
                    high_dpi_support = device_pixel_ratio > 1.0
                    self.result.add_test_result("high_dpi_support", True, 
                                              f"DPI: {dpi}, 像素比: {device_pixel_ratio}, 高DPI: {high_dpi_support}")
                else:
                    self.result.add_test_result("high_dpi_support", False, "无法获取屏幕信息")
                    
            return True
            
        except Exception as e:
            error_msg = f"高DPI支持测试失败: {str(e)}"
            self.result.add_test_result("high_dpi_support", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_version_info(self):
        """测试版本信息显示"""
        try:
            # 导入版本模块
            import version
            
            # 检查版本信息
            version_str = version.get_version()
            version_info = version.get_version_info()
            
            expected_version = "1.0.1"
            if version_str == expected_version:
                self.result.add_test_result("version_check", True, 
                                          f"版本信息正确: {version_str}")
            else:
                self.result.add_test_result("version_check", False, 
                                          f"版本信息错误: 期望 {expected_version}, 实际 {version_str}")
                
            # 检查发布信息
            release_date = version_info.get('release_date', '')
            release_name = version_info.get('release_name', '')
            
            self.result.add_test_result("release_info", True, 
                                      f"发布日期: {release_date}, 发布名称: {release_name}")
            
            return True
            
        except Exception as e:
            error_msg = f"版本信息测试失败: {str(e)}"
            self.result.add_test_result("version_info", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            return False
            
    def cleanup(self):
        """清理测试环境"""
        try:
            if self.main_window:
                self.main_window.close()
                
            if self.app:
                self.app.quit()
                
            self.result.add_test_result("cleanup", True, "测试环境清理成功")
            
        except Exception as e:
            error_msg = f"清理失败: {str(e)}"
            self.result.add_test_result("cleanup", False, error_msg=error_msg)
            self.result.add_error(error_msg, traceback.format_exc())
            
    def run_all_tests(self):
        """运行所有测试"""
        self.result.start_time = datetime.now()
        
        print("🔍 开始VisionAI-ClipsMaster v1.0.1 UI界面功能测试")
        print("=" * 60)
        
        # 测试序列
        tests = [
            ("设置测试环境", self.setup_test_environment),
            ("UI启动测试", self.test_ui_startup),
            ("UI组件测试", self.test_ui_components),
            ("性能监控测试", self.test_performance_monitoring),
            ("高DPI支持测试", self.test_high_dpi_support),
            ("版本信息测试", self.test_version_info),
        ]
        
        for test_name, test_func in tests:
            print(f"🧪 执行测试: {test_name}")
            try:
                success = test_func()
                status = "✅ 通过" if success else "❌ 失败"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ 异常: {str(e)}")
                self.result.add_error(f"{test_name}异常", traceback.format_exc())
                
        # 清理
        self.cleanup()
        
        self.result.end_time = datetime.now()
        
        return self.result
        
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.result.test_results)
        passed_tests = sum(1 for r in self.result.test_results.values() if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 UI界面功能测试报告")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if self.result.start_time and self.result.end_time:
            duration = (self.result.end_time - self.result.start_time).total_seconds()
            print(f"测试耗时: {duration:.2f}秒")
            
        print("\n📋 详细测试结果:")
        for test_name, result in self.result.test_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {test_name}: {result.get('details', '')}")
            if result.get('error_msg'):
                print(f"   错误: {result['error_msg']}")
                
        print("\n📈 性能数据:")
        for metric_name, data in self.result.performance_data.items():
            print(f"• {metric_name}: {data['value']} {data['unit']}")
            
        if self.result.errors:
            print("\n🚨 错误详情:")
            for i, error in enumerate(self.result.errors, 1):
                print(f"{i}. {error['error']}")
                
        return self.result

def main():
    """主函数"""
    tester = UITester()
    result = tester.run_all_tests()
    tester.generate_report()
    
    # 保存测试结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"ui_test_report_v1_0_1_{timestamp}.json"
    
    report_data = {
        "version": "1.0.1",
        "test_type": "UI界面功能测试",
        "timestamp": timestamp,
        "test_results": result.test_results,
        "performance_data": result.performance_data,
        "errors": result.errors,
        "summary": {
            "total_tests": len(result.test_results),
            "passed_tests": sum(1 for r in result.test_results.values() if r['passed']),
            "success_rate": sum(1 for r in result.test_results.values() if r['passed']) / len(result.test_results) * 100
        }
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n📄 测试报告已保存至: {report_file}")
    
    return result

if __name__ == "__main__":
    main()
