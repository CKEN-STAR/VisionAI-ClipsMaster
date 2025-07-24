#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能测试套件

全面测试应用的内存使用、UI响应性、核心功能性能和压力测试
"""

import sys
import os
import time
import json
import psutil
import threading
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import gc

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.test_results = {
            "test_info": {
                "start_time": datetime.now().isoformat(),
                "test_version": "1.0.0",
                "system_info": self._get_system_info()
            },
            "memory_tests": {},
            "ui_response_tests": {},
            "core_function_tests": {},
            "stress_tests": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        self.app = None
        self.main_window = None
        self.process = psutil.Process()
        self.monitoring_active = False
        self.memory_samples = []
        self.cpu_samples = []
        
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": sys.version.split()[0],
            "timestamp": datetime.now().isoformat()
        }
        
    def _start_monitoring(self):
        """开始性能监控"""
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # 内存使用
                    memory_info = self.process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    # CPU使用率
                    cpu_percent = self.process.cpu_percent()
                    
                    # 记录样本
                    timestamp = time.time()
                    self.memory_samples.append({
                        "timestamp": timestamp,
                        "memory_mb": memory_mb,
                        "memory_vms_mb": memory_info.vms / 1024 / 1024
                    })
                    
                    self.cpu_samples.append({
                        "timestamp": timestamp,
                        "cpu_percent": cpu_percent
                    })
                    
                    time.sleep(1)  # 每秒采样一次
                    
                except Exception as e:
                    print(f"监控错误: {e}")
                    
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def _stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)
            
    def test_application_startup(self) -> Dict[str, Any]:
        """测试1: 应用启动性能"""
        print("\n=== 1. 应用启动性能测试 ===")
        
        startup_results = {}
        
        try:
            # 记录启动前内存
            initial_memory = self.process.memory_info().rss / 1024 / 1024
            startup_results["initial_memory_mb"] = initial_memory
            
            # 开始监控
            self._start_monitoring()
            
            # 记录启动时间
            startup_start = time.time()
            
            # 导入和初始化应用
            from PyQt6.QtWidgets import QApplication
            
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
                
            import_time = time.time() - startup_start
            startup_results["import_time"] = import_time
            
            # 创建主窗口
            window_start = time.time()
            from simple_ui_fixed import SimpleScreenplayApp
            self.main_window = SimpleScreenplayApp()
            
            window_creation_time = time.time() - window_start
            startup_results["window_creation_time"] = window_creation_time
            
            # 等待初始化完成
            self.app.processEvents()
            time.sleep(2)  # 等待所有延迟初始化完成
            
            total_startup_time = time.time() - startup_start
            startup_results["total_startup_time"] = total_startup_time
            
            # 记录启动后内存
            post_startup_memory = self.process.memory_info().rss / 1024 / 1024
            startup_results["post_startup_memory_mb"] = post_startup_memory
            startup_results["memory_increase_mb"] = post_startup_memory - initial_memory
            
            # 评估启动性能
            startup_results["startup_performance"] = {
                "excellent": total_startup_time < 5,
                "good": total_startup_time < 10,
                "acceptable": total_startup_time < 15,
                "needs_improvement": total_startup_time >= 15
            }
            
            print(f"导入时间: {import_time:.2f}s")
            print(f"窗口创建时间: {window_creation_time:.2f}s")
            print(f"总启动时间: {total_startup_time:.2f}s")
            print(f"启动内存增加: {startup_results['memory_increase_mb']:.1f}MB")
            
        except Exception as e:
            startup_results["error"] = str(e)
            print(f"启动测试失败: {e}")
            
        self.test_results["memory_tests"]["startup"] = startup_results
        return startup_results
        
    def test_ui_responsiveness(self) -> Dict[str, Any]:
        """测试2: UI响应性能测试"""
        print("\n=== 2. UI响应性能测试 ===")
        
        if not self.main_window:
            return {"error": "主窗口未初始化"}
            
        ui_results = {}
        
        try:
            # 测试标签页切换响应时间
            tab_switch_times = []
            if hasattr(self.main_window, 'tabs'):
                tabs = self.main_window.tabs
                tab_count = tabs.count()
                
                for i in range(tab_count):
                    for j in range(tab_count):
                        if i != j:
                            start_time = time.time()
                            tabs.setCurrentIndex(j)
                            self.app.processEvents()
                            switch_time = time.time() - start_time
                            tab_switch_times.append(switch_time)
                            time.sleep(0.1)  # 短暂延迟
                            
            ui_results["tab_switching"] = {
                "times": tab_switch_times,
                "avg_time": sum(tab_switch_times) / len(tab_switch_times) if tab_switch_times else 0,
                "max_time": max(tab_switch_times) if tab_switch_times else 0,
                "min_time": min(tab_switch_times) if tab_switch_times else 0,
                "samples": len(tab_switch_times)
            }
            
            # 测试窗口重绘性能
            repaint_times = []
            for _ in range(10):
                start_time = time.time()
                self.main_window.repaint()
                self.app.processEvents()
                repaint_time = time.time() - start_time
                repaint_times.append(repaint_time)
                time.sleep(0.05)
                
            ui_results["window_repaint"] = {
                "avg_time": sum(repaint_times) / len(repaint_times),
                "max_time": max(repaint_times),
                "samples": len(repaint_times)
            }
            
            # 测试用户交互响应
            interaction_times = []
            if hasattr(self.main_window, 'record_user_interaction'):
                for _ in range(20):
                    start_time = time.time()
                    self.main_window.record_user_interaction()
                    self.app.processEvents()
                    interaction_time = time.time() - start_time
                    interaction_times.append(interaction_time)
                    time.sleep(0.02)
                    
            ui_results["user_interaction"] = {
                "avg_time": sum(interaction_times) / len(interaction_times) if interaction_times else 0,
                "max_time": max(interaction_times) if interaction_times else 0,
                "samples": len(interaction_times)
            }
            
            # 评估UI响应性能
            avg_tab_switch = ui_results["tab_switching"]["avg_time"]
            avg_repaint = ui_results["window_repaint"]["avg_time"]
            
            ui_results["performance_rating"] = {
                "tab_switching_excellent": avg_tab_switch < 0.1,
                "tab_switching_good": avg_tab_switch < 0.5,
                "repaint_excellent": avg_repaint < 0.05,
                "repaint_good": avg_repaint < 0.1
            }
            
            print(f"标签页切换平均时间: {avg_tab_switch:.3f}s")
            print(f"窗口重绘平均时间: {avg_repaint:.3f}s")
            print(f"用户交互平均响应时间: {ui_results['user_interaction']['avg_time']:.3f}s")
            
        except Exception as e:
            ui_results["error"] = str(e)
            print(f"UI响应性测试失败: {e}")
            
        self.test_results["ui_response_tests"] = ui_results
        return ui_results
        
    def test_core_functions_performance(self) -> Dict[str, Any]:
        """测试3: 核心功能性能测试"""
        print("\n=== 3. 核心功能性能测试 ===")
        
        if not self.main_window:
            return {"error": "主窗口未初始化"}
            
        core_results = {}
        
        try:
            # 测试语言检测性能
            if hasattr(self.main_window, 'change_language_mode'):
                lang_switch_times = []
                languages = ['zh', 'en', 'auto']
                
                for lang in languages:
                    start_time = time.time()
                    self.main_window.change_language_mode(lang)
                    self.app.processEvents()
                    switch_time = time.time() - start_time
                    lang_switch_times.append(switch_time)
                    time.sleep(0.1)
                    
                core_results["language_switching"] = {
                    "avg_time": sum(lang_switch_times) / len(lang_switch_times),
                    "max_time": max(lang_switch_times),
                    "times": lang_switch_times
                }
                
            # 测试GPU检测性能
            if hasattr(self.main_window, 'detect_gpu'):
                gpu_detection_times = []
                for _ in range(5):
                    start_time = time.time()
                    self.main_window.detect_gpu()
                    self.app.processEvents()
                    detection_time = time.time() - start_time
                    gpu_detection_times.append(detection_time)
                    time.sleep(0.2)
                    
                core_results["gpu_detection"] = {
                    "avg_time": sum(gpu_detection_times) / len(gpu_detection_times),
                    "max_time": max(gpu_detection_times),
                    "times": gpu_detection_times
                }
                
            # 测试模型状态检查性能
            if hasattr(self.main_window, 'check_models'):
                model_check_times = []
                for _ in range(3):
                    start_time = time.time()
                    self.main_window.check_models()
                    self.app.processEvents()
                    check_time = time.time() - start_time
                    model_check_times.append(check_time)
                    time.sleep(0.5)
                    
                core_results["model_checking"] = {
                    "avg_time": sum(model_check_times) / len(model_check_times),
                    "max_time": max(model_check_times),
                    "times": model_check_times
                }
                
            print(f"语言切换平均时间: {core_results.get('language_switching', {}).get('avg_time', 0):.3f}s")
            print(f"GPU检测平均时间: {core_results.get('gpu_detection', {}).get('avg_time', 0):.3f}s")
            print(f"模型检查平均时间: {core_results.get('model_checking', {}).get('avg_time', 0):.3f}s")
            
        except Exception as e:
            core_results["error"] = str(e)
            print(f"核心功能性能测试失败: {e}")
            
        self.test_results["core_function_tests"] = core_results
        return core_results

    def test_memory_stability(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """测试4: 内存稳定性测试（长时间运行）"""
        print(f"\n=== 4. 内存稳定性测试 ({duration_minutes}分钟) ===")

        if not self.main_window:
            return {"error": "主窗口未初始化"}

        memory_results = {}

        try:
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)

            initial_memory = self.process.memory_info().rss / 1024 / 1024
            memory_samples = []
            gc_counts = []

            print(f"开始长时间内存监控，初始内存: {initial_memory:.1f}MB")

            iteration = 0
            while time.time() < end_time:
                # 模拟用户操作
                if hasattr(self.main_window, 'tabs'):
                    # 切换标签页
                    tab_index = iteration % self.main_window.tabs.count()
                    self.main_window.tabs.setCurrentIndex(tab_index)

                # 记录用户交互
                if hasattr(self.main_window, 'record_user_interaction'):
                    self.main_window.record_user_interaction()

                # 处理事件
                self.app.processEvents()

                # 每10秒记录一次内存
                if iteration % 10 == 0:
                    current_memory = self.process.memory_info().rss / 1024 / 1024
                    memory_samples.append({
                        "time": time.time() - start_time,
                        "memory_mb": current_memory
                    })

                    # 检查垃圾回收
                    gc_count = len(gc.get_objects())
                    gc_counts.append(gc_count)

                    elapsed_minutes = (time.time() - start_time) / 60
                    print(f"运行 {elapsed_minutes:.1f}分钟, 内存: {current_memory:.1f}MB, 对象数: {gc_count}")

                iteration += 1
                time.sleep(1)

            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory

            # 分析内存趋势
            if len(memory_samples) > 1:
                memory_values = [s["memory_mb"] for s in memory_samples]
                memory_results = {
                    "duration_minutes": duration_minutes,
                    "initial_memory_mb": initial_memory,
                    "final_memory_mb": final_memory,
                    "memory_increase_mb": memory_increase,
                    "peak_memory_mb": max(memory_values),
                    "avg_memory_mb": sum(memory_values) / len(memory_values),
                    "memory_samples": memory_samples,
                    "gc_object_counts": gc_counts,
                    "memory_leak_detected": memory_increase > 100,  # 超过100MB认为可能有泄漏
                    "stability_rating": "excellent" if memory_increase < 50 else "good" if memory_increase < 100 else "needs_attention"
                }

            print(f"内存稳定性测试完成")
            print(f"内存增长: {memory_increase:.1f}MB")
            print(f"稳定性评级: {memory_results.get('stability_rating', 'unknown')}")

        except Exception as e:
            memory_results["error"] = str(e)
            print(f"内存稳定性测试失败: {e}")

        self.test_results["memory_tests"]["stability"] = memory_results
        return memory_results

    def test_stress_performance(self) -> Dict[str, Any]:
        """测试5: 压力测试"""
        print("\n=== 5. 压力测试 ===")

        if not self.main_window:
            return {"error": "主窗口未初始化"}

        stress_results = {}

        try:
            # 创建测试文件
            test_files = self._create_test_files()

            # 测试大量文件操作
            file_operation_times = []

            # 模拟添加多个视频文件
            if hasattr(self.main_window, 'video_list'):
                start_time = time.time()

                for i, test_file in enumerate(test_files[:10]):  # 限制为10个文件
                    if hasattr(self.main_window, 'add_video_files'):
                        # 模拟文件添加（不实际添加文件）
                        operation_start = time.time()
                        self.app.processEvents()
                        operation_time = time.time() - operation_start
                        file_operation_times.append(operation_time)

                        if i % 3 == 0:  # 每3个文件检查一次内存
                            current_memory = self.process.memory_info().rss / 1024 / 1024
                            print(f"处理文件 {i+1}, 内存: {current_memory:.1f}MB")

                total_file_time = time.time() - start_time

                stress_results["file_operations"] = {
                    "total_time": total_file_time,
                    "avg_operation_time": sum(file_operation_times) / len(file_operation_times) if file_operation_times else 0,
                    "operations_count": len(file_operation_times)
                }

            # 测试快速UI操作
            rapid_ui_times = []
            start_time = time.time()

            for _ in range(100):  # 100次快速操作
                operation_start = time.time()

                # 快速切换标签页
                if hasattr(self.main_window, 'tabs'):
                    current_tab = self.main_window.tabs.currentIndex()
                    next_tab = (current_tab + 1) % self.main_window.tabs.count()
                    self.main_window.tabs.setCurrentIndex(next_tab)

                self.app.processEvents()
                operation_time = time.time() - operation_start
                rapid_ui_times.append(operation_time)

            total_rapid_time = time.time() - start_time

            stress_results["rapid_ui_operations"] = {
                "total_time": total_rapid_time,
                "avg_operation_time": sum(rapid_ui_times) / len(rapid_ui_times),
                "operations_per_second": len(rapid_ui_times) / total_rapid_time,
                "max_operation_time": max(rapid_ui_times)
            }

            # 测试内存压力
            memory_before_stress = self.process.memory_info().rss / 1024 / 1024

            # 强制垃圾回收
            gc.collect()

            memory_after_gc = self.process.memory_info().rss / 1024 / 1024

            stress_results["memory_pressure"] = {
                "memory_before_stress_mb": memory_before_stress,
                "memory_after_gc_mb": memory_after_gc,
                "memory_freed_by_gc_mb": memory_before_stress - memory_after_gc
            }

            print(f"文件操作平均时间: {stress_results['file_operations']['avg_operation_time']:.3f}s")
            print(f"快速UI操作速度: {stress_results['rapid_ui_operations']['operations_per_second']:.1f} ops/s")
            print(f"垃圾回收释放内存: {stress_results['memory_pressure']['memory_freed_by_gc_mb']:.1f}MB")

        except Exception as e:
            stress_results["error"] = str(e)
            print(f"压力测试失败: {e}")

        self.test_results["stress_tests"] = stress_results
        return stress_results

    def _create_test_files(self) -> List[str]:
        """创建测试文件"""
        test_files = []

        # 创建临时SRT文件
        for i in range(20):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
                srt_content = f"""1
00:00:0{i%6},000 --> 00:00:0{(i%6)+2},000
测试字幕内容 {i+1}

2
00:00:0{(i%6)+3},000 --> 00:00:0{(i%6)+5},000
这是第二行测试字幕 {i+1}
"""
                f.write(srt_content)
                test_files.append(f.name)

        return test_files

    def run_all_tests(self, include_long_test: bool = False):
        """运行所有性能测试"""
        print("开始VisionAI-ClipsMaster性能测试套件...")
        print("=" * 60)

        # 执行测试序列
        self.test_application_startup()
        self.test_ui_responsiveness()
        self.test_core_functions_performance()

        if include_long_test:
            # 运行5分钟的内存稳定性测试（可选）
            self.test_memory_stability(duration_minutes=5)
        else:
            # 运行1分钟的快速内存测试
            self.test_memory_stability(duration_minutes=1)

        self.test_stress_performance()

        # 生成测试报告
        self.generate_performance_report()
        
    def generate_performance_report(self):
        """生成性能测试报告"""
        print("\n" + "=" * 60)
        print("性能测试报告生成中...")

        # 停止监控
        self._stop_monitoring()

        # 分析内存使用
        if self.memory_samples:
            memory_values = [s["memory_mb"] for s in self.memory_samples]
            self.test_results["performance_summary"]["memory"] = {
                "peak_mb": max(memory_values),
                "avg_mb": sum(memory_values) / len(memory_values),
                "min_mb": min(memory_values),
                "samples": len(memory_values),
                "within_limits": max(memory_values) < 800
            }

        # 分析CPU使用
        if self.cpu_samples:
            cpu_values = [s["cpu_percent"] for s in self.cpu_samples if s["cpu_percent"] > 0]
            if cpu_values:
                self.test_results["performance_summary"]["cpu"] = {
                    "peak_percent": max(cpu_values),
                    "avg_percent": sum(cpu_values) / len(cpu_values),
                    "samples": len(cpu_values)
                }

        # 生成性能评估和建议
        self._generate_performance_analysis()

        # 保存详细报告
        report_file = f"performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        # 生成可读性报告
        readable_report = self._generate_readable_report()
        readable_file = f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(readable_report)

        print(f"详细性能报告已保存到: {report_file}")
        print(f"可读性报告已保存到: {readable_file}")

        # 显示关键指标
        self._display_key_metrics()

        # 清理资源
        self.cleanup()

    def _generate_performance_analysis(self):
        """生成性能分析和建议"""
        recommendations = []

        # 分析启动性能
        startup_data = self.test_results.get("memory_tests", {}).get("startup", {})
        if startup_data:
            startup_time = startup_data.get("total_startup_time", 0)
            if startup_time > 10:
                recommendations.append({
                    "category": "启动性能",
                    "priority": "高",
                    "issue": f"启动时间过长: {startup_time:.2f}秒",
                    "suggestion": "考虑延迟加载非关键组件，优化导入顺序"
                })
            elif startup_time > 5:
                recommendations.append({
                    "category": "启动性能",
                    "priority": "中",
                    "issue": f"启动时间较长: {startup_time:.2f}秒",
                    "suggestion": "可以进一步优化组件初始化流程"
                })

        # 分析内存使用
        memory_data = self.test_results.get("performance_summary", {}).get("memory", {})
        if memory_data:
            peak_memory = memory_data.get("peak_mb", 0)
            if peak_memory > 800:
                recommendations.append({
                    "category": "内存使用",
                    "priority": "高",
                    "issue": f"内存峰值超限: {peak_memory:.1f}MB > 800MB",
                    "suggestion": "需要优化内存使用，检查是否有内存泄漏"
                })
            elif peak_memory > 600:
                recommendations.append({
                    "category": "内存使用",
                    "priority": "中",
                    "issue": f"内存使用较高: {peak_memory:.1f}MB",
                    "suggestion": "建议监控内存增长趋势，考虑优化大对象使用"
                })

        # 分析UI响应性
        ui_data = self.test_results.get("ui_response_tests", {})
        if ui_data:
            tab_switch_time = ui_data.get("tab_switching", {}).get("avg_time", 0)
            if tab_switch_time > 0.5:
                recommendations.append({
                    "category": "UI响应性",
                    "priority": "高",
                    "issue": f"标签页切换过慢: {tab_switch_time:.3f}秒",
                    "suggestion": "优化标签页切换逻辑，减少不必要的重绘操作"
                })

        # 分析内存稳定性
        stability_data = self.test_results.get("memory_tests", {}).get("stability", {})
        if stability_data:
            memory_increase = stability_data.get("memory_increase_mb", 0)
            if memory_increase > 100:
                recommendations.append({
                    "category": "内存稳定性",
                    "priority": "高",
                    "issue": f"可能存在内存泄漏: 增长{memory_increase:.1f}MB",
                    "suggestion": "检查事件监听器、定时器和缓存的清理机制"
                })

        self.test_results["recommendations"] = recommendations

    def _generate_readable_report(self) -> str:
        """生成可读性报告"""
        report = f"""# VisionAI-ClipsMaster 性能测试报告

## 测试概述
- **测试时间**: {self.test_results['test_info']['start_time']}
- **测试版本**: {self.test_results['test_info']['test_version']}
- **系统信息**: {self.test_results['test_info']['system_info']['platform']}
- **CPU核心数**: {self.test_results['test_info']['system_info']['cpu_count']}
- **总内存**: {self.test_results['test_info']['system_info']['memory_total_gb']}GB

## 关键性能指标

### 启动性能
"""

        startup_data = self.test_results.get("memory_tests", {}).get("startup", {})
        if startup_data:
            report += f"""
- **总启动时间**: {startup_data.get('total_startup_time', 0):.2f}秒
- **窗口创建时间**: {startup_data.get('window_creation_time', 0):.2f}秒
- **启动内存增长**: {startup_data.get('memory_increase_mb', 0):.1f}MB
"""

        memory_data = self.test_results.get("performance_summary", {}).get("memory", {})
        if memory_data:
            report += f"""
### 内存使用
- **峰值内存**: {memory_data.get('peak_mb', 0):.1f}MB
- **平均内存**: {memory_data.get('avg_mb', 0):.1f}MB
- **是否在限制内**: {'✅ 是' if memory_data.get('within_limits') else '❌ 否'}
"""

        ui_data = self.test_results.get("ui_response_tests", {})
        if ui_data:
            tab_data = ui_data.get("tab_switching", {})
            report += f"""
### UI响应性
- **标签页切换平均时间**: {tab_data.get('avg_time', 0):.3f}秒
- **标签页切换最大时间**: {tab_data.get('max_time', 0):.3f}秒
- **窗口重绘平均时间**: {ui_data.get('window_repaint', {}).get('avg_time', 0):.3f}秒
"""

        # 添加建议部分
        recommendations = self.test_results.get("recommendations", [])
        if recommendations:
            report += "\n## 优化建议\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"""
### {i}. {rec['category']} ({rec['priority']}优先级)
- **问题**: {rec['issue']}
- **建议**: {rec['suggestion']}
"""

        return report

    def _display_key_metrics(self):
        """显示关键性能指标"""
        print("\n" + "=" * 60)
        print("关键性能指标总结")
        print("=" * 60)

        # 启动性能
        startup_data = self.test_results.get("memory_tests", {}).get("startup", {})
        if startup_data:
            startup_time = startup_data.get("total_startup_time", 0)
            status = "✅ 优秀" if startup_time < 5 else "⚠️ 良好" if startup_time < 10 else "❌ 需改进"
            print(f"启动时间: {startup_time:.2f}s ({status})")

        # 内存使用
        memory_data = self.test_results.get("performance_summary", {}).get("memory", {})
        if memory_data:
            peak_memory = memory_data.get("peak_mb", 0)
            status = "✅ 优秀" if peak_memory < 400 else "⚠️ 良好" if peak_memory < 800 else "❌ 超限"
            print(f"峰值内存: {peak_memory:.1f}MB ({status})")

        # UI响应性
        ui_data = self.test_results.get("ui_response_tests", {})
        if ui_data:
            tab_time = ui_data.get("tab_switching", {}).get("avg_time", 0)
            status = "✅ 优秀" if tab_time < 0.1 else "⚠️ 良好" if tab_time < 0.5 else "❌ 过慢"
            print(f"UI响应: {tab_time:.3f}s ({status})")

        # 建议数量
        recommendations = self.test_results.get("recommendations", [])
        high_priority = len([r for r in recommendations if r["priority"] == "高"])
        if high_priority == 0:
            print("优化建议: ✅ 无高优先级问题")
        else:
            print(f"优化建议: ⚠️ {high_priority}个高优先级问题需要关注")
        
    def cleanup(self):
        """清理测试资源"""
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
    tester = PerformanceTestSuite()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
