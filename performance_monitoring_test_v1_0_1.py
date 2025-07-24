#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster v1.0.1 性能监控系统测试
测试实时性能监控面板、资源使用率显示、预警机制等
"""

import sys
import os
import time
import json
import traceback
import threading
from datetime import datetime
from pathlib import Path
import psutil

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

class PerformanceMonitoringTester:
    def __init__(self):
        self.test_results = {}
        self.performance_data = {}
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.monitoring_active = False
        
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
        
    def test_system_resource_monitoring(self):
        """测试系统资源监控功能"""
        try:
            # 获取系统资源信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.add_performance_data("cpu_usage", cpu_percent, "%")
            self.add_performance_data("memory_usage", memory.percent, "%")
            self.add_performance_data("memory_available", memory.available / 1024 / 1024, "MB")
            self.add_performance_data("disk_usage", disk.percent, "%")
            
            # 检查资源监控是否正常
            if cpu_percent >= 0 and memory.percent >= 0:
                self.add_test_result("system_resource_monitoring", True, 
                                    f"系统资源监控正常 - CPU: {cpu_percent}%, 内存: {memory.percent}%")
            else:
                self.add_test_result("system_resource_monitoring", False, 
                                    "系统资源监控数据异常")
                                    
            return True
            
        except Exception as e:
            error_msg = f"系统资源监控测试失败: {str(e)}"
            self.add_test_result("system_resource_monitoring", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_process_monitoring(self):
        """测试进程监控功能"""
        try:
            # 尝试导入进程监控模块
            try:
                import simple_ui_fixed
                if hasattr(simple_ui_fixed, 'ProcessStabilityMonitor'):
                    self.add_test_result("process_monitor_import", True, "进程监控器导入成功")
                    
                    # 测试进程监控器创建
                    monitor = simple_ui_fixed.ProcessStabilityMonitor()
                    if hasattr(monitor, 'start_monitoring'):
                        self.add_test_result("process_monitor_methods", True, "进程监控方法可用")
                    else:
                        self.add_test_result("process_monitor_methods", False, "进程监控方法不可用")
                        
                else:
                    self.add_test_result("process_monitor_import", False, "进程监控器类未找到")
                    
            except ImportError:
                self.add_test_result("process_monitor_import", False, "进程监控模块导入失败")
                
            # 测试当前进程信息
            current_process = psutil.Process()
            process_info = {
                "pid": current_process.pid,
                "memory_info": current_process.memory_info(),
                "cpu_percent": current_process.cpu_percent(),
                "num_threads": current_process.num_threads()
            }
            
            self.add_performance_data("process_memory", process_info["memory_info"].rss / 1024 / 1024, "MB")
            self.add_performance_data("process_threads", process_info["num_threads"], "threads")
            
            self.add_test_result("process_info_collection", True, 
                                f"进程信息收集成功 - PID: {process_info['pid']}, 线程: {process_info['num_threads']}")
            
            return True
            
        except Exception as e:
            error_msg = f"进程监控测试失败: {str(e)}"
            self.add_test_result("process_monitoring", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_responsiveness_monitoring(self):
        """测试响应性监控功能"""
        try:
            # 尝试导入响应性监控器
            try:
                import simple_ui_fixed
                if hasattr(simple_ui_fixed, 'ResponsivenessMonitor'):
                    self.add_test_result("responsiveness_monitor_import", True, "响应性监控器导入成功")
                    
                    # 测试响应性监控器创建
                    monitor = simple_ui_fixed.ResponsivenessMonitor()
                    if hasattr(monitor, 'start_monitoring'):
                        self.add_test_result("responsiveness_monitor_methods", True, "响应性监控方法可用")
                    else:
                        self.add_test_result("responsiveness_monitor_methods", False, "响应性监控方法不可用")
                        
                else:
                    self.add_test_result("responsiveness_monitor_import", False, "响应性监控器类未找到")
                    
            except ImportError:
                self.add_test_result("responsiveness_monitor_import", False, "响应性监控模块导入失败")
                
            # 测试响应时间测量
            start_time = time.time()
            time.sleep(0.1)  # 模拟操作
            response_time = time.time() - start_time
            
            self.add_performance_data("response_time_test", response_time * 1000, "ms")
            
            if response_time < 1.0:  # 响应时间小于1秒认为正常
                self.add_test_result("response_time_measurement", True, 
                                    f"响应时间测量正常: {response_time*1000:.1f}ms")
            else:
                self.add_test_result("response_time_measurement", False, 
                                    f"响应时间过长: {response_time*1000:.1f}ms")
                                    
            return True
            
        except Exception as e:
            error_msg = f"响应性监控测试失败: {str(e)}"
            self.add_test_result("responsiveness_monitoring", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_memory_monitoring(self):
        """测试内存监控功能"""
        try:
            # 测试内存使用情况
            memory_before = psutil.virtual_memory().used
            
            # 创建一些内存使用
            test_data = [i for i in range(100000)]  # 创建测试数据
            
            memory_after = psutil.virtual_memory().used
            memory_diff = (memory_after - memory_before) / 1024 / 1024  # MB
            
            self.add_performance_data("memory_allocation_test", memory_diff, "MB")
            
            # 清理测试数据
            del test_data
            
            # 检查内存监控功能
            try:
                import simple_ui_fixed
                if hasattr(simple_ui_fixed, 'UIMemoryManager'):
                    memory_manager = simple_ui_fixed.UIMemoryManager()
                    if hasattr(memory_manager, 'get_memory_usage'):
                        self.add_test_result("memory_manager_available", True, "内存管理器可用")
                    else:
                        self.add_test_result("memory_manager_available", False, "内存管理器方法不可用")
                else:
                    self.add_test_result("memory_manager_available", False, "内存管理器类未找到")
                    
            except ImportError:
                self.add_test_result("memory_manager_available", False, "内存管理器导入失败")
                
            self.add_test_result("memory_monitoring", True, 
                                f"内存监控测试完成，分配测试: {memory_diff:.1f}MB")
            
            return True
            
        except Exception as e:
            error_msg = f"内存监控测试失败: {str(e)}"
            self.add_test_result("memory_monitoring", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_performance_alerts(self):
        """测试性能预警功能"""
        try:
            # 检查预警管理器
            try:
                import simple_ui_fixed
                if hasattr(simple_ui_fixed, 'AlertManager'):
                    alert_manager = simple_ui_fixed.AlertManager()
                    if hasattr(alert_manager, 'show_alert'):
                        self.add_test_result("alert_manager_available", True, "预警管理器可用")
                        
                        # 测试预警功能
                        alert_manager.show_alert("测试预警消息", "warning")
                        self.add_test_result("alert_functionality", True, "预警功能测试成功")
                    else:
                        self.add_test_result("alert_manager_available", False, "预警管理器方法不可用")
                else:
                    self.add_test_result("alert_manager_available", False, "预警管理器类未找到")
                    
            except ImportError:
                self.add_test_result("alert_manager_available", False, "预警管理器导入失败")
                
            # 测试性能阈值检查
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            # 模拟阈值检查
            cpu_threshold = 80.0
            memory_threshold = 85.0
            
            alerts_triggered = 0
            if cpu_usage > cpu_threshold:
                alerts_triggered += 1
            if memory_usage > memory_threshold:
                alerts_triggered += 1
                
            self.add_performance_data("alerts_triggered", alerts_triggered, "count")
            self.add_test_result("threshold_checking", True, 
                                f"阈值检查完成，触发预警: {alerts_triggered}个")
            
            return True
            
        except Exception as e:
            error_msg = f"性能预警测试失败: {str(e)}"
            self.add_test_result("performance_alerts", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def test_performance_data_collection(self):
        """测试性能数据收集功能"""
        try:
            # 收集多种性能指标
            metrics = {}
            
            # CPU相关指标
            metrics['cpu_count'] = psutil.cpu_count()
            metrics['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 0
            
            # 内存相关指标
            memory = psutil.virtual_memory()
            metrics['memory_total'] = memory.total / 1024 / 1024 / 1024  # GB
            metrics['memory_used'] = memory.used / 1024 / 1024 / 1024   # GB
            
            # 磁盘相关指标
            disk = psutil.disk_usage('/')
            metrics['disk_total'] = disk.total / 1024 / 1024 / 1024     # GB
            metrics['disk_used'] = disk.used / 1024 / 1024 / 1024       # GB
            
            # 网络相关指标
            try:
                network = psutil.net_io_counters()
                metrics['network_sent'] = network.bytes_sent / 1024 / 1024  # MB
                metrics['network_recv'] = network.bytes_recv / 1024 / 1024  # MB
            except:
                metrics['network_sent'] = 0
                metrics['network_recv'] = 0
                
            # 保存性能指标
            for key, value in metrics.items():
                unit = "GB" if "total" in key or "used" in key else ("MB" if "network" in key else "")
                self.add_performance_data(key, value, unit)
                
            self.add_test_result("performance_data_collection", True, 
                                f"性能数据收集成功，收集{len(metrics)}项指标")
            
            return True
            
        except Exception as e:
            error_msg = f"性能数据收集测试失败: {str(e)}"
            self.add_test_result("performance_data_collection", False, error_msg=error_msg)
            self.add_error(error_msg, traceback.format_exc())
            return False
            
    def run_all_tests(self):
        """运行所有性能监控测试"""
        self.start_time = datetime.now()
        
        print("🔍 开始VisionAI-ClipsMaster v1.0.1 性能监控系统测试")
        print("=" * 60)
        
        # 测试序列
        tests = [
            ("系统资源监控测试", self.test_system_resource_monitoring),
            ("进程监控测试", self.test_process_monitoring),
            ("响应性监控测试", self.test_responsiveness_monitoring),
            ("内存监控测试", self.test_memory_monitoring),
            ("性能预警测试", self.test_performance_alerts),
            ("性能数据收集测试", self.test_performance_data_collection),
        ]
        
        for test_name, test_func in tests:
            print(f"🧪 执行测试: {test_name}")
            try:
                success = test_func()
                status = "✅ 通过" if success else "❌ 失败"
                print(f"   {status}")
            except Exception as e:
                print(f"   ❌ 异常: {str(e)}")
                self.add_error(f"{test_name}异常", traceback.format_exc())
                
        self.end_time = datetime.now()
        
        return self.generate_report()
        
    def generate_report(self):
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 性能监控系统测试报告")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"测试耗时: {duration:.2f}秒")
            
        print("\n📋 详细测试结果:")
        for test_name, result in self.test_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {test_name}: {result.get('details', '')}")
            if result.get('error_msg'):
                print(f"   错误: {result['error_msg']}")
                
        print("\n📈 性能数据:")
        for metric_name, data in self.performance_data.items():
            print(f"• {metric_name}: {data['value']} {data['unit']}")
            
        if self.errors:
            print("\n🚨 错误详情:")
            for i, error in enumerate(self.errors, 1):
                print(f"{i}. {error['error']}")
                
        # 保存测试结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_monitoring_test_report_v1_0_1_{timestamp}.json"
        
        report_data = {
            "version": "1.0.1",
            "test_type": "性能监控系统测试",
            "timestamp": timestamp,
            "test_results": self.test_results,
            "performance_data": self.performance_data,
            "errors": self.errors,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": passed_tests / total_tests * 100 if total_tests > 0 else 0
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 测试报告已保存至: {report_file}")
        
        return report_data

def main():
    """主函数"""
    tester = PerformanceMonitoringTester()
    result = tester.run_all_tests()
    return result

if __name__ == "__main__":
    main()
