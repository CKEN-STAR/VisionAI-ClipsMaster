#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI功能测试脚本
测试VisionAI-ClipsMaster的UI界面功能
"""

import os
import sys
import time
import json
import logging
import tempfile
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 导入UI组件
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtTest import QTest
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

class UIFunctionalTest:
    """UI功能测试类"""
    
    def __init__(self):
        """初始化测试"""
        self.test_results = {}
        self.app = None
        self.main_window = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("UI功能测试初始化完成")
    
    def run_ui_tests(self) -> dict:
        """运行UI测试"""
        self.logger.info("🖥️ 开始UI功能测试...")
        
        results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
        
        if not PYQT_AVAILABLE:
            self.logger.warning("PyQt6不可用，跳过UI测试")
            results["tests"]["pyqt_availability"] = {
                "success": False,
                "error": "PyQt6不可用",
                "note": "需要安装PyQt6: pip install PyQt6"
            }
            results["summary"] = self._generate_summary(results["tests"])
            return results
        
        try:
            # 1. 测试应用程序创建
            self.logger.info("\n🚀 测试应用程序创建...")
            app_result = self._test_application_creation()
            results["tests"]["application_creation"] = app_result
            
            if app_result.get("success", False):
                # 2. 测试主窗口启动
                self.logger.info("\n🏠 测试主窗口启动...")
                window_result = self._test_main_window_startup()
                results["tests"]["main_window_startup"] = window_result
                
                if window_result.get("success", False):
                    # 3. 测试UI组件响应性
                    self.logger.info("\n⚡ 测试UI组件响应性...")
                    responsiveness_result = self._test_ui_responsiveness()
                    results["tests"]["ui_responsiveness"] = responsiveness_result
                    
                    # 4. 测试标签页切换
                    self.logger.info("\n📑 测试标签页切换...")
                    tab_result = self._test_tab_switching()
                    results["tests"]["tab_switching"] = tab_result
                    
                    # 5. 测试文件选择功能
                    self.logger.info("\n📁 测试文件选择功能...")
                    file_result = self._test_file_selection()
                    results["tests"]["file_selection"] = file_result
                    
                    # 6. 测试窗口操作
                    self.logger.info("\n🪟 测试窗口操作...")
                    window_ops_result = self._test_window_operations()
                    results["tests"]["window_operations"] = window_ops_result
            
        except Exception as e:
            self.logger.error(f"UI测试执行失败: {e}")
            results["tests"]["execution_error"] = {
                "success": False,
                "error": str(e)
            }
        finally:
            # 清理资源
            self._cleanup_ui()
        
        # 生成摘要
        results["summary"] = self._generate_summary(results["tests"])
        results["end_time"] = datetime.now().isoformat()
        
        # 显示结果
        self._display_results(results)
        
        # 保存结果
        self._save_results(results)
        
        return results
    
    def _test_application_creation(self) -> dict:
        """测试应用程序创建"""
        try:
            start_time = time.time()
            
            # 创建QApplication
            self.app = QApplication.instance()
            if self.app is None:
                self.app = QApplication(sys.argv)
            
            creation_time = time.time() - start_time
            
            # 验证应用程序属性
            app_name = self.app.applicationName() or "VisionAI-ClipsMaster"
            
            return {
                "success": True,
                "creation_time": creation_time,
                "app_name": app_name,
                "qt_version": self.app.applicationVersion() or "Unknown",
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_main_window_startup(self) -> dict:
        """测试主窗口启动"""
        try:
            # 导入主窗口
            from simple_ui_fixed import SimpleScreenplayApp
            
            start_time = time.time()
            
            # 创建主窗口
            self.main_window = SimpleScreenplayApp()
            
            startup_time = time.time() - start_time
            
            # 验证窗口属性
            window_title = self.main_window.windowTitle()
            window_size = (self.main_window.width(), self.main_window.height())
            
            # 显示窗口
            self.main_window.show()
            
            # 等待窗口完全显示
            self.app.processEvents()
            time.sleep(0.5)
            
            return {
                "success": True,
                "startup_time": startup_time,
                "window_title": window_title,
                "window_size": window_size,
                "is_visible": self.main_window.isVisible(),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_ui_responsiveness(self) -> dict:
        """测试UI组件响应性"""
        try:
            if not self.main_window:
                return {"success": False, "error": "主窗口未创建"}
            
            response_times = []
            
            # 测试多次UI交互
            for i in range(5):
                start_time = time.time()
                
                # 处理事件
                self.app.processEvents()
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                time.sleep(0.1)
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            return {
                "success": True,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "response_times": response_times,
                "responsive": max_response_time < 1.0,  # 1秒阈值
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_tab_switching(self) -> dict:
        """测试标签页切换"""
        try:
            if not self.main_window:
                return {"success": False, "error": "主窗口未创建"}
            
            # 查找标签页组件
            tab_widget = None
            for child in self.main_window.findChildren(object):
                if hasattr(child, 'setCurrentIndex') and hasattr(child, 'count'):
                    tab_widget = child
                    break
            
            if not tab_widget:
                return {"success": False, "error": "未找到标签页组件"}
            
            tab_count = tab_widget.count()
            switch_times = []
            
            # 测试标签页切换
            for i in range(min(tab_count, 4)):  # 最多测试4个标签页
                start_time = time.time()
                
                tab_widget.setCurrentIndex(i)
                self.app.processEvents()
                
                switch_time = time.time() - start_time
                switch_times.append(switch_time)
                
                time.sleep(0.2)
            
            avg_switch_time = sum(switch_times) / len(switch_times) if switch_times else 0
            
            return {
                "success": True,
                "tab_count": tab_count,
                "switches_tested": len(switch_times),
                "avg_switch_time": avg_switch_time,
                "switch_times": switch_times,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_file_selection(self) -> dict:
        """测试文件选择功能"""
        try:
            if not self.main_window:
                return {"success": False, "error": "主窗口未创建"}
            
            # 查找文件选择按钮
            file_buttons = []
            for child in self.main_window.findChildren(object):
                if hasattr(child, 'text') and hasattr(child, 'clicked'):
                    button_text = str(child.text()).lower()
                    if any(keyword in button_text for keyword in ['选择', '导入', '文件', 'select', 'import']):
                        file_buttons.append(child)
            
            button_tests = []
            
            for i, button in enumerate(file_buttons[:3]):  # 最多测试3个按钮
                try:
                    button_text = str(button.text())
                    is_enabled = button.isEnabled()
                    is_visible = button.isVisible()
                    
                    button_tests.append({
                        "button_index": i,
                        "button_text": button_text,
                        "is_enabled": is_enabled,
                        "is_visible": is_visible,
                        "test_success": True
                    })
                    
                except Exception as e:
                    button_tests.append({
                        "button_index": i,
                        "test_success": False,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "buttons_found": len(file_buttons),
                "buttons_tested": len(button_tests),
                "button_tests": button_tests,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_window_operations(self) -> dict:
        """测试窗口操作"""
        try:
            if not self.main_window:
                return {"success": False, "error": "主窗口未创建"}
            
            operations = []
            
            # 测试窗口最小化
            try:
                original_state = self.main_window.windowState()
                self.main_window.showMinimized()
                self.app.processEvents()
                time.sleep(0.2)
                
                # 恢复窗口
                self.main_window.showNormal()
                self.app.processEvents()
                
                operations.append({
                    "operation": "minimize_restore",
                    "success": True
                })
            except Exception as e:
                operations.append({
                    "operation": "minimize_restore",
                    "success": False,
                    "error": str(e)
                })
            
            # 测试窗口大小调整
            try:
                original_size = (self.main_window.width(), self.main_window.height())
                self.main_window.resize(800, 600)
                self.app.processEvents()
                time.sleep(0.2)
                
                new_size = (self.main_window.width(), self.main_window.height())
                
                # 恢复原始大小
                self.main_window.resize(*original_size)
                self.app.processEvents()
                
                operations.append({
                    "operation": "resize",
                    "success": True,
                    "original_size": original_size,
                    "new_size": new_size
                })
            except Exception as e:
                operations.append({
                    "operation": "resize",
                    "success": False,
                    "error": str(e)
                })
            
            successful_operations = sum(1 for op in operations if op.get("success", False))
            
            return {
                "success": successful_operations > 0,
                "operations_tested": len(operations),
                "successful_operations": successful_operations,
                "operations": operations,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _cleanup_ui(self):
        """清理UI资源"""
        try:
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
            if self.app:
                self.app.quit()
                self.app = None
                
            self.logger.info("UI资源清理完成")
            
        except Exception as e:
            self.logger.error(f"UI资源清理失败: {e}")
    
    def _generate_summary(self, tests: dict) -> dict:
        """生成测试摘要"""
        total_tests = len(tests)
        successful_tests = sum(1 for test in tests.values() if test.get("success", False))
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "overall_success": successful_tests == total_tests
        }
    
    def _display_results(self, results: dict):
        """显示测试结果"""
        summary = results["summary"]
        
        self.logger.info("\n" + "="*60)
        self.logger.info("🎯 UI功能测试结果摘要")
        self.logger.info("="*60)
        
        # 显示各项测试结果
        test_names = {
            "pyqt_availability": "PyQt6可用性",
            "application_creation": "应用程序创建",
            "main_window_startup": "主窗口启动",
            "ui_responsiveness": "UI响应性",
            "tab_switching": "标签页切换",
            "file_selection": "文件选择功能",
            "window_operations": "窗口操作"
        }
        
        for test_key, test_result in results["tests"].items():
            test_name = test_names.get(test_key, test_key)
            status = "✅ 成功" if test_result.get("success", False) else "❌ 失败"
            self.logger.info(f"{test_name}: {status}")
            
            if not test_result.get("success", False) and test_result.get("error"):
                self.logger.info(f"  错误: {test_result['error']}")
            elif test_result.get("note"):
                self.logger.info(f"  说明: {test_result['note']}")
        
        self.logger.info(f"\n总体结果: {'✅ 全部通过' if summary['overall_success'] else '❌ 部分失败'}")
        self.logger.info(f"成功率: {summary['success_rate']:.1%} ({summary['successful_tests']}/{summary['total_tests']})")
        
        # 显示建议
        if summary['overall_success']:
            self.logger.info("\n🎉 恭喜！所有UI功能测试通过！")
            self.logger.info("💡 建议: UI界面运行正常，可以进行实际使用")
        else:
            self.logger.info("\n⚠️  部分UI测试失败，请检查相关组件")
            self.logger.info("💡 建议: 查看详细错误信息并修复问题")
    
    def _save_results(self, results: dict):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"ui_functional_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"\n📄 测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

def main():
    """主函数"""
    print("🖥️ VisionAI-ClipsMaster UI功能测试")
    print("=" * 50)
    
    try:
        # 运行UI测试
        tester = UIFunctionalTest()
        results = tester.run_ui_tests()
        
        # 返回适当的退出码
        if results["summary"]["overall_success"]:
            print("\n✅ UI功能测试完成 - 所有功能正常！")
            sys.exit(0)
        else:
            print("\n❌ UI功能测试发现问题 - 请查看详细日志")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试执行失败: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
