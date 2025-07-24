#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI功能测试脚本

模拟用户实际操作流程，测试UI的响应性和功能完整性
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

class UIFunctionalTester:
    """UI功能测试器"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "functional_tests": {},
            "performance_metrics": {},
            "user_workflow_tests": {},
            "issues_found": [],
            "recommendations": []
        }
        
        self.app = None
        self.main_window = None
        
    def setup_test_environment(self):
        """设置测试环境"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            
            # 创建应用程序
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
                
            # 创建主窗口
            from simple_ui_fixed import SimpleScreenplayApp
            self.main_window = SimpleScreenplayApp()
            
            print("[OK] 测试环境设置完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] 测试环境设置失败: {e}")
            return False
            
    def test_ui_responsiveness(self):
        """测试UI响应性"""
        print("\n=== UI响应性测试 ===")
        
        if not self.main_window:
            return False
            
        # 测试标签页切换响应时间
        start_time = time.time()
        
        try:
            # 模拟标签页切换
            if hasattr(self.main_window, 'tabs'):
                tabs = self.main_window.tabs
                for i in range(tabs.count()):
                    switch_start = time.time()
                    tabs.setCurrentIndex(i)
                    self.app.processEvents()  # 处理事件
                    switch_time = time.time() - switch_start
                    
                    tab_name = tabs.tabText(i)
                    self.test_results["performance_metrics"][f"tab_switch_{i}"] = {
                        "tab_name": tab_name,
                        "switch_time": switch_time,
                        "responsive": switch_time < 0.5
                    }
                    
                    print(f"标签页 '{tab_name}' 切换时间: {switch_time:.3f}s")
                    
        except Exception as e:
            print(f"标签页切换测试失败: {e}")
            
        total_time = time.time() - start_time
        print(f"UI响应性测试完成，总耗时: {total_time:.3f}s")
        
        return True
        
    def test_file_handling_workflow(self):
        """测试文件处理工作流"""
        print("\n=== 文件处理工作流测试 ===")
        
        if not self.main_window:
            return False
            
        # 创建测试SRT文件
        test_srt_content = """1
00:00:01,000 --> 00:00:03,000
这是一个测试字幕

2
00:00:04,000 --> 00:00:06,000
用于测试系统功能
"""
        
        try:
            # 创建临时测试文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
                f.write(test_srt_content)
                test_srt_path = f.name
                
            print(f"创建测试SRT文件: {test_srt_path}")
            
            # 测试语言检测功能
            if hasattr(self.main_window, 'lang_combo'):
                combo = self.main_window.lang_combo
                original_index = combo.currentIndex()
                
                # 测试语言切换
                for i in range(combo.count()):
                    combo.setCurrentIndex(i)
                    self.app.processEvents()
                    lang_mode = combo.currentData()
                    print(f"语言模式切换到: {combo.currentText()} ({lang_mode})")
                    
                combo.setCurrentIndex(original_index)  # 恢复原始设置
                
            # 测试SRT文件列表功能
            if hasattr(self.main_window, 'srt_list'):
                srt_list = self.main_window.srt_list
                initial_count = srt_list.count()
                print(f"SRT列表初始项目数: {initial_count}")
                
            self.test_results["user_workflow_tests"]["file_handling"] = {
                "test_file_created": True,
                "language_detection_available": hasattr(self.main_window, 'lang_combo'),
                "srt_list_available": hasattr(self.main_window, 'srt_list'),
                "status": "completed"
            }
            
            # 清理测试文件
            os.unlink(test_srt_path)
            print("测试文件已清理")
            
        except Exception as e:
            print(f"文件处理工作流测试失败: {e}")
            self.test_results["issues_found"].append(f"文件处理工作流测试失败: {e}")
            
        return True
        
    def test_model_status_display(self):
        """测试模型状态显示"""
        print("\n=== 模型状态显示测试 ===")
        
        if not self.main_window:
            return False
            
        try:
            # 检查模型状态相关的UI元素
            model_ui_elements = [
                ("zh_model_exists", "中文模型状态"),
                ("en_model_exists", "英文模型状态")
            ]
            
            for attr_name, display_name in model_ui_elements:
                if hasattr(self.main_window, attr_name):
                    status = getattr(self.main_window, attr_name)
                    print(f"{display_name}: {'已安装' if status else '未安装'}")
                    self.test_results["functional_tests"][attr_name] = status
                else:
                    print(f"{display_name}: 状态检查不可用")
                    
            # 测试模型下载功能可用性
            download_methods = [
                ("download_zh_model", "中文模型下载"),
                ("download_en_model", "英文模型下载")
            ]
            
            for method_name, display_name in download_methods:
                if hasattr(self.main_window, method_name):
                    print(f"{display_name}功能可用")
                    self.test_results["functional_tests"][f"{method_name}_available"] = True
                else:
                    print(f"{display_name}功能不可用")
                    self.test_results["functional_tests"][f"{method_name}_available"] = False
                    
        except Exception as e:
            print(f"模型状态显示测试失败: {e}")
            
        return True
        
    def test_gpu_detection_functionality(self):
        """测试GPU检测功能"""
        print("\n=== GPU检测功能测试 ===")
        
        try:
            # 测试GPU检测函数
            from simple_ui_fixed import detect_gpu_info
            gpu_info = detect_gpu_info()
            
            print(f"GPU检测结果:")
            print(f"  可用性: {gpu_info.get('available', False)}")
            print(f"  设备名称: {gpu_info.get('name', '未知')}")
            print(f"  检测方法: {gpu_info.get('detection_methods', [])}")
            
            self.test_results["functional_tests"]["gpu_detection"] = {
                "available": gpu_info.get('available', False),
                "name": gpu_info.get('name', '未知'),
                "methods": gpu_info.get('detection_methods', []),
                "errors": gpu_info.get('errors', [])
            }
            
            # 测试GPU对话框功能
            if hasattr(self.main_window, 'show_gpu_detection_dialog'):
                print("GPU检测对话框功能可用")
                self.test_results["functional_tests"]["gpu_dialog_available"] = True
            else:
                print("GPU检测对话框功能不可用")
                self.test_results["functional_tests"]["gpu_dialog_available"] = False
                
        except Exception as e:
            print(f"GPU检测功能测试失败: {e}")
            self.test_results["issues_found"].append(f"GPU检测功能测试失败: {e}")
            
        return True
        
    def test_memory_monitoring(self):
        """测试内存监控功能"""
        print("\n=== 内存监控功能测试 ===")
        
        try:
            import psutil
            process = psutil.Process()
            
            # 获取内存使用情况
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            print(f"当前内存使用: {memory_mb:.1f}MB")
            
            # 测试进程稳定性监控器
            if hasattr(self.main_window, 'stability_monitor'):
                monitor = self.main_window.stability_monitor
                if hasattr(monitor, 'get_performance_summary'):
                    summary = monitor.get_performance_summary()
                    print(f"性能监控摘要: {summary}")
                    self.test_results["performance_metrics"]["stability_monitor"] = summary
                    
            self.test_results["performance_metrics"]["memory_usage"] = {
                "current_mb": memory_mb,
                "within_limits": memory_mb < 800,  # 4GB系统的合理限制
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"内存监控功能测试失败: {e}")
            
        return True
        
    def run_all_tests(self):
        """运行所有功能测试"""
        print("开始VisionAI-ClipsMaster UI功能测试...")
        print("=" * 60)
        
        # 设置测试环境
        if not self.setup_test_environment():
            print("测试环境设置失败，退出测试")
            return
            
        # 执行测试序列
        test_sequence = [
            self.test_ui_responsiveness,
            self.test_file_handling_workflow,
            self.test_model_status_display,
            self.test_gpu_detection_functionality,
            self.test_memory_monitoring
        ]
        
        for test_func in test_sequence:
            try:
                test_func()
                time.sleep(0.5)  # 短暂延迟，确保UI稳定
            except Exception as e:
                print(f"测试执行异常: {test_func.__name__}: {e}")
                self.test_results["issues_found"].append(f"测试执行异常: {test_func.__name__}: {e}")
                
        # 生成测试报告
        self.generate_test_report()
        
        # 清理资源
        self.cleanup()
        
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("UI功能测试报告")
        print("=" * 60)
        
        # 统计测试结果
        total_tests = len(self.test_results["functional_tests"])
        issues_count = len(self.test_results["issues_found"])
        
        print(f"功能测试项目: {total_tests}")
        print(f"发现问题: {issues_count}")
        
        if issues_count == 0:
            print("✅ 所有功能测试通过")
        else:
            print("⚠️ 发现以下问题:")
            for issue in self.test_results["issues_found"]:
                print(f"  - {issue}")
                
        # 保存详细报告
        report_file = f"ui_functional_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
        print(f"\n详细测试报告已保存到: {report_file}")
        
    def cleanup(self):
        """清理资源"""
        if self.main_window:
            try:
                self.main_window.close()
            except:
                pass
                
        if self.app:
            try:
                self.app.quit()
            except:
                pass

def main():
    """主函数"""
    tester = UIFunctionalTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
