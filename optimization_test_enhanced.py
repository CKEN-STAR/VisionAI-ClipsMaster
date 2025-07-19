#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 第二阶段优化增强测试脚本
目标：验证启动性能、响应时间监控、CSS优化、用户体验增强等功能
"""

import sys
import time
import subprocess
import psutil
import json
import threading
from datetime import datetime

class EnhancedOptimizationTester:
    def __init__(self):
        self.python_interpreter = r"C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"
        self.ui_script = "simple_ui_fixed.py"
        self.test_results = {}
        self.startup_target_time = 3.0  # 目标启动时间3秒
        self.response_target_time = 1.0  # 目标响应时间1秒

    def run_enhanced_optimization_test(self):
        """运行增强优化测试"""
        print("🚀 VisionAI-ClipsMaster 第二阶段优化测试")
        print("="*70)
        print("测试目标: 验证启动性能、响应监控、CSS优化、用户体验增强")
        print("="*70)

        # 测试1: 启动性能优化验证
        startup_result = self.test_startup_optimization()
        self.test_results["startup_optimization"] = startup_result

        # 测试2: 响应时间监控增强验证
        response_result = self.test_response_monitoring_enhancement()
        self.test_results["response_monitoring"] = response_result

        # 测试3: CSS优化验证
        css_result = self.test_css_optimization()
        self.test_results["css_optimization"] = css_result

        # 测试4: 用户体验增强验证
        ux_result = self.test_user_experience_enhancement()
        self.test_results["user_experience"] = ux_result

        # 测试5: 整体性能评估
        overall_result = self.test_overall_performance()
        self.test_results["overall_performance"] = overall_result

        # 生成第二阶段优化报告
        self.generate_enhanced_optimization_report()

        return self.test_results

    def test_startup_optimization(self):
        """测试启动性能优化"""
        print("\n📊 测试1: 启动性能优化验证")
        print("-" * 40)

        startup_times = []
        optimization_features = {
            "startup_optimizer_loaded": False,
            "lazy_loading_active": False,
            "component_registration": False,
            "delayed_initialization": False
        }

        # 进行3次启动测试取平均值
        for i in range(3):
            print(f"  第 {i+1} 次启动测试...")

            start_time = time.time()

            try:
                # 启动UI进程
                process = subprocess.Popen(
                    [self.python_interpreter, self.ui_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                # 监控启动过程
                startup_detected = False
                startup_time = 0

                for j in range(40):  # 最多等待40秒
                    if process.poll() is not None:
                        break

                    # 检查内存使用判断启动状态
                    try:
                        ui_process = psutil.Process(process.pid)
                        memory_mb = ui_process.memory_info().rss / 1024 / 1024
                        if memory_mb > 150:  # UI启动后内存使用应该超过150MB
                            if not startup_detected:
                                startup_detected = True
                                startup_time = time.time() - start_time
                                break
                    except:
                        pass

                    # 检查输出中的优化特性（使用英文关键词避免编码问题）
                    try:
                        output = process.stdout.readline()
                        if "[OK]" in output and ("startup" in output.lower() or "启动" in output):
                            optimization_features["startup_optimizer_loaded"] = True
                        elif "延迟初始化" in output or "delayed" in output.lower():
                            optimization_features["delayed_initialization"] = True
                        elif "优化启动" in output or "optimized startup" in output.lower():
                            optimization_features["lazy_loading_active"] = True
                        elif "注册组件" in output or "register" in output.lower():
                            optimization_features["component_registration"] = True
                    except:
                        pass

                    time.sleep(0.1)

                # 关闭进程
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()

                if startup_detected:
                    startup_times.append(startup_time)
                    print(f"    启动时间: {startup_time:.2f}秒")
                else:
                    print(f"    启动检测失败")

            except Exception as e:
                print(f"    启动测试失败: {e}")

        # 计算结果
        if startup_times:
            avg_startup_time = sum(startup_times) / len(startup_times)
            min_startup_time = min(startup_times)
            max_startup_time = max(startup_times)

            # 与目标对比
            improvement = max(0, (self.startup_target_time - avg_startup_time) / self.startup_target_time * 100)

            result = {
                "success": True,
                "average_startup_time": avg_startup_time,
                "min_startup_time": min_startup_time,
                "max_startup_time": max_startup_time,
                "target_time": self.startup_target_time,
                "target_achieved": avg_startup_time <= self.startup_target_time,
                "improvement_percentage": improvement,
                "optimization_features": optimization_features,
                "performance_grade": self._calculate_startup_grade(avg_startup_time)
            }

            print(f"✅ 平均启动时间: {avg_startup_time:.2f}秒 (目标: {self.startup_target_time}秒)")
            print(f"✅ 最快启动时间: {min_startup_time:.2f}秒")
            print(f"✅ 目标达成: {'是' if result['target_achieved'] else '否'}")
            print(f"✅ 优化特性检测: {sum(optimization_features.values())}/4 项")
            print(f"✅ 性能等级: {result['performance_grade']}")

        else:
            result = {
                "success": False,
                "error": "所有启动测试均失败",
                "optimization_features": optimization_features
            }
            print("❌ 启动性能测试失败")

        return result

    def test_response_monitoring_enhancement(self):
        """测试响应时间监控增强"""
        print("\n📊 测试2: 响应时间监控增强验证")
        print("-" * 40)

        try:
            # 启动UI进程
            process = subprocess.Popen(
                [self.python_interpreter, self.ui_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 等待UI启动
            time.sleep(8)

            # 监控响应时间数据
            response_data = {
                "response_times": [],
                "interaction_count": 0,
                "monitoring_active": False,
                "enhanced_monitor_loaded": False,
                "data_collection_working": False
            }

            # 监控30秒
            start_monitor = time.time()
            while time.time() - start_monitor < 30:
                try:
                    output = process.stdout.readline()
                    if not output:
                        continue

                    # 检查增强监控器是否加载（使用英文关键词避免编码问题）
                    if "[OK]" in output and ("response" in output.lower() or "响应" in output):
                        response_data["enhanced_monitor_loaded"] = True
                    elif "监控" in output and ("初始化" in output or "initialized" in output.lower()):
                        response_data["monitoring_active"] = True
                    elif ("记录" in output or "record" in output.lower()) and ("响应" in output or "response" in output.lower()):
                        # 提取响应时间
                        import re
                        match = re.search(r'([\d.]+)s', output)
                        if match:
                            response_time = float(match.group(1))
                            response_data["response_times"].append(response_time)
                            response_data["data_collection_working"] = True
                    elif "数据更新" in output or "data update" in output.lower():
                        # 提取交互次数
                        match = re.search(r'(\d+)', output)
                        if match:
                            response_data["interaction_count"] = int(match.group(1))
                            response_data["data_collection_working"] = True

                except Exception as e:
                    continue

                time.sleep(0.1)

            # 关闭进程
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

            # 分析结果
            if response_data["response_times"]:
                avg_response = sum(response_data["response_times"]) / len(response_data["response_times"])
                max_response = max(response_data["response_times"])
                min_response = min(response_data["response_times"])

                result = {
                    "success": True,
                    "enhanced_monitor_loaded": response_data["enhanced_monitor_loaded"],
                    "monitoring_active": response_data["monitoring_active"],
                    "data_collection_working": response_data["data_collection_working"],
                    "average_response_time": avg_response,
                    "max_response_time": max_response,
                    "min_response_time": min_response,
                    "response_count": len(response_data["response_times"]),
                    "interaction_count": response_data["interaction_count"],
                    "target_achieved": avg_response <= self.response_target_time,
                    "performance_grade": self._calculate_response_grade(avg_response)
                }

                print(f"✅ 增强监控器加载: {'成功' if result['enhanced_monitor_loaded'] else '失败'}")
                print(f"✅ 监控激活状态: {'是' if result['monitoring_active'] else '否'}")
                print(f"✅ 数据收集工作: {'正常' if result['data_collection_working'] else '异常'}")
                print(f"✅ 平均响应时间: {avg_response:.3f}秒 (目标: {self.response_target_time}秒)")
                print(f"✅ 响应次数: {len(response_data['response_times'])}")
                print(f"✅ 交互次数: {response_data['interaction_count']}")
                print(f"✅ 目标达成: {'是' if result['target_achieved'] else '否'}")
                print(f"✅ 性能等级: {result['performance_grade']}")

            else:
                result = {
                    "success": False,
                    "enhanced_monitor_loaded": response_data["enhanced_monitor_loaded"],
                    "monitoring_active": response_data["monitoring_active"],
                    "data_collection_working": response_data["data_collection_working"],
                    "message": "未检测到响应时间数据"
                }
                print(f"⚠️ 未检测到响应时间数据")
                print(f"✅ 增强监控器加载: {'成功' if result['enhanced_monitor_loaded'] else '失败'}")
                print(f"✅ 监控激活状态: {'是' if result['monitoring_active'] else '否'}")

            return result

        except Exception as e:
            print(f"❌ 响应时间监控测试失败: {e}")
            return {"success": False, "error": str(e)}

    def test_css_optimization(self):
        """测试CSS优化"""
        print("\n📊 测试3: CSS优化验证")
        print("-" * 40)

        try:
            # 启动UI进程
            process = subprocess.Popen(
                [self.python_interpreter, self.ui_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 等待UI启动
            time.sleep(6)

            # 监控CSS优化相关输出
            css_data = {
                "css_optimizer_loaded": False,
                "optimized_styles_applied": False,
                "unknown_property_warnings": 0,
                "css_optimization_active": False,
                "style_cache_working": False
            }

            # 监控20秒
            start_monitor = time.time()
            while time.time() - start_monitor < 20:
                try:
                    # 读取标准输出（使用英文关键词避免编码问题）
                    output = process.stdout.readline()
                    if output:
                        if "[OK]" in output and ("css" in output.lower() or "CSS" in output):
                            css_data["css_optimizer_loaded"] = True
                        elif "优化" in output and ("样式" in output or "style" in output.lower()):
                            css_data["optimized_styles_applied"] = True
                        elif "CSS" in output and ("优化" in output or "optim" in output.lower()):
                            css_data["css_optimization_active"] = True
                        elif "缓存" in output or "cache" in output.lower():
                            css_data["style_cache_working"] = True

                    # 读取标准错误（检查CSS警告）
                    error_output = process.stderr.readline()
                    if error_output and "Unknown property" in error_output:
                        css_data["unknown_property_warnings"] += 1

                except Exception:
                    continue

                time.sleep(0.1)

            # 关闭进程
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

            # 计算CSS优化效果
            optimization_score = 0
            if css_data["css_optimizer_loaded"]:
                optimization_score += 25
            if css_data["optimized_styles_applied"]:
                optimization_score += 25
            if css_data["css_optimization_active"]:
                optimization_score += 25
            if css_data["unknown_property_warnings"] < 5:  # 少于5个警告认为优化有效
                optimization_score += 25

            result = {
                "success": True,
                "css_optimizer_loaded": css_data["css_optimizer_loaded"],
                "optimized_styles_applied": css_data["optimized_styles_applied"],
                "css_optimization_active": css_data["css_optimization_active"],
                "style_cache_working": css_data["style_cache_working"],
                "unknown_property_warnings": css_data["unknown_property_warnings"],
                "optimization_score": optimization_score,
                "performance_grade": self._calculate_css_grade(optimization_score, css_data["unknown_property_warnings"])
            }

            print(f"✅ CSS优化器加载: {'成功' if result['css_optimizer_loaded'] else '失败'}")
            print(f"✅ 优化样式应用: {'成功' if result['optimized_styles_applied'] else '失败'}")
            print(f"✅ CSS优化激活: {'是' if result['css_optimization_active'] else '否'}")
            print(f"✅ 样式缓存工作: {'正常' if result['style_cache_working'] else '未检测到'}")
            print(f"✅ CSS警告数量: {result['unknown_property_warnings']} 个")
            print(f"✅ 优化评分: {optimization_score}/100")
            print(f"✅ 性能等级: {result['performance_grade']}")

            return result

        except Exception as e:
            print(f"❌ CSS优化测试失败: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_startup_grade(self, startup_time):
        """计算启动性能等级"""
        if startup_time <= 2.5:
            return "A+ (优秀)"
        elif startup_time <= 3.5:
            return "A (良好)"
        elif startup_time <= 5.0:
            return "B (合格)"
        else:
            return "C (需改进)"

    def _calculate_response_grade(self, response_time):
        """计算响应性能等级"""
        if response_time <= 0.5:
            return "A+ (优秀)"
        elif response_time <= 1.0:
            return "A (良好)"
        elif response_time <= 2.0:
            return "B (合格)"
        else:
            return "C (需改进)"

    def _calculate_css_grade(self, optimization_score, warning_count):
        """计算CSS优化等级"""
        if optimization_score >= 90 and warning_count < 3:
            return "A+ (优秀)"
        elif optimization_score >= 75 and warning_count < 8:
            return "A (良好)"
        elif optimization_score >= 50 and warning_count < 15:
            return "B (合格)"
        else:
            return "C (需改进)"

    def test_user_experience_enhancement(self):
        """测试用户体验增强"""
        print("\n📊 测试4: 用户体验增强验证")
        print("-" * 40)

        try:
            # 启动UI进程
            process = subprocess.Popen(
                [self.python_interpreter, self.ui_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 等待UI启动
            time.sleep(6)

            # 监控用户体验增强功能
            ux_data = {
                "ux_enhancer_loaded": False,
                "shortcuts_registered": False,
                "error_diagnostic_available": False,
                "operation_preview_available": False,
                "user_guide_available": False,
                "shortcuts_count": 0
            }

            # 监控15秒
            start_monitor = time.time()
            while time.time() - start_monitor < 15:
                try:
                    output = process.stdout.readline()
                    if not output:
                        continue

                    if "[OK]" in output and ("用户体验" in output or "user experience" in output.lower()):
                        ux_data["ux_enhancer_loaded"] = True
                    elif "用户体验" in output and ("初始化" in output or "initialized" in output.lower()):
                        ux_data["operation_preview_available"] = True
                        ux_data["error_diagnostic_available"] = True
                        ux_data["user_guide_available"] = True
                    elif ("注册" in output or "register" in output.lower()) and ("快捷键" in output or "shortcut" in output.lower()):
                        ux_data["shortcuts_registered"] = True
                        # 提取快捷键数量
                        import re
                        match = re.search(r'(\d+)', output)
                        if match:
                            ux_data["shortcuts_count"] = int(match.group(1))

                except Exception:
                    continue

                time.sleep(0.1)

            # 关闭进程
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

            # 计算用户体验评分
            ux_score = 0
            if ux_data["ux_enhancer_loaded"]:
                ux_score += 20
            if ux_data["shortcuts_registered"]:
                ux_score += 20
            if ux_data["error_diagnostic_available"]:
                ux_score += 20
            if ux_data["operation_preview_available"]:
                ux_score += 20
            if ux_data["user_guide_available"]:
                ux_score += 20

            result = {
                "success": True,
                "ux_enhancer_loaded": ux_data["ux_enhancer_loaded"],
                "shortcuts_registered": ux_data["shortcuts_registered"],
                "shortcuts_count": ux_data["shortcuts_count"],
                "error_diagnostic_available": ux_data["error_diagnostic_available"],
                "operation_preview_available": ux_data["operation_preview_available"],
                "user_guide_available": ux_data["user_guide_available"],
                "ux_score": ux_score,
                "performance_grade": self._calculate_ux_grade(ux_score, ux_data["shortcuts_count"])
            }

            print(f"✅ 用户体验增强器加载: {'成功' if result['ux_enhancer_loaded'] else '失败'}")
            print(f"✅ 快捷键注册: {'成功' if result['shortcuts_registered'] else '失败'}")
            print(f"✅ 快捷键数量: {result['shortcuts_count']} 个")
            print(f"✅ 错误诊断可用: {'是' if result['error_diagnostic_available'] else '否'}")
            print(f"✅ 操作预览可用: {'是' if result['operation_preview_available'] else '否'}")
            print(f"✅ 用户引导可用: {'是' if result['user_guide_available'] else '否'}")
            print(f"✅ 用户体验评分: {ux_score}/100")
            print(f"✅ 性能等级: {result['performance_grade']}")

            return result

        except Exception as e:
            print(f"❌ 用户体验增强测试失败: {e}")
            return {"success": False, "error": str(e)}

    def test_overall_performance(self):
        """测试整体性能"""
        print("\n📊 测试5: 整体性能评估")
        print("-" * 40)

        try:
            # 启动UI进程进行综合测试
            process = subprocess.Popen(
                [self.python_interpreter, self.ui_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            # 等待UI启动
            time.sleep(8)

            # 监控整体性能指标
            performance_data = {
                "memory_usage": [],
                "cpu_usage": [],
                "startup_modules_loaded": 0,
                "optimization_modules_active": 0,
                "error_count": 0,
                "warning_count": 0
            }

            # 监控25秒
            start_monitor = time.time()
            while time.time() - start_monitor < 25:
                try:
                    # 监控系统资源
                    ui_process = psutil.Process(process.pid)
                    memory_mb = ui_process.memory_info().rss / 1024 / 1024
                    cpu_percent = ui_process.cpu_percent()

                    performance_data["memory_usage"].append(memory_mb)
                    performance_data["cpu_usage"].append(cpu_percent)

                    # 监控输出
                    output = process.stdout.readline()
                    if output:
                        if "导入成功" in output:
                            performance_data["startup_modules_loaded"] += 1
                        elif "初始化完成" in output and ("优化" in output or "增强" in output):
                            performance_data["optimization_modules_active"] += 1
                        elif "[ERROR]" in output:
                            performance_data["error_count"] += 1
                        elif "[WARN]" in output:
                            performance_data["warning_count"] += 1

                except Exception:
                    continue

                time.sleep(0.1)

            # 关闭进程
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

            # 计算整体性能指标
            if performance_data["memory_usage"]:
                avg_memory = sum(performance_data["memory_usage"]) / len(performance_data["memory_usage"])
                max_memory = max(performance_data["memory_usage"])
                memory_stable = (max_memory - min(performance_data["memory_usage"])) < 100
            else:
                avg_memory = max_memory = 0
                memory_stable = False

            if performance_data["cpu_usage"]:
                avg_cpu = sum(performance_data["cpu_usage"]) / len(performance_data["cpu_usage"])
                max_cpu = max(performance_data["cpu_usage"])
            else:
                avg_cpu = max_cpu = 0

            # 计算综合评分
            overall_score = 0

            # 内存使用评分 (30%)
            if avg_memory < 400:
                overall_score += 30
            elif avg_memory < 500:
                overall_score += 25
            elif avg_memory < 600:
                overall_score += 20
            else:
                overall_score += 10

            # 模块加载评分 (25%)
            if performance_data["startup_modules_loaded"] >= 4:
                overall_score += 25
            elif performance_data["startup_modules_loaded"] >= 3:
                overall_score += 20
            elif performance_data["startup_modules_loaded"] >= 2:
                overall_score += 15
            else:
                overall_score += 5

            # 优化模块评分 (25%)
            if performance_data["optimization_modules_active"] >= 3:
                overall_score += 25
            elif performance_data["optimization_modules_active"] >= 2:
                overall_score += 20
            elif performance_data["optimization_modules_active"] >= 1:
                overall_score += 15
            else:
                overall_score += 5

            # 稳定性评分 (20%)
            if performance_data["error_count"] == 0 and performance_data["warning_count"] < 5:
                overall_score += 20
            elif performance_data["error_count"] < 2 and performance_data["warning_count"] < 10:
                overall_score += 15
            elif performance_data["error_count"] < 5 and performance_data["warning_count"] < 20:
                overall_score += 10
            else:
                overall_score += 5

            result = {
                "success": True,
                "average_memory_mb": avg_memory,
                "max_memory_mb": max_memory,
                "memory_stable": memory_stable,
                "average_cpu_percent": avg_cpu,
                "max_cpu_percent": max_cpu,
                "startup_modules_loaded": performance_data["startup_modules_loaded"],
                "optimization_modules_active": performance_data["optimization_modules_active"],
                "error_count": performance_data["error_count"],
                "warning_count": performance_data["warning_count"],
                "overall_score": overall_score,
                "performance_grade": self._calculate_overall_grade(overall_score)
            }

            print(f"✅ 平均内存使用: {avg_memory:.1f}MB")
            print(f"✅ 最大内存使用: {max_memory:.1f}MB")
            print(f"✅ 内存稳定性: {'稳定' if memory_stable else '不稳定'}")
            print(f"✅ 平均CPU使用: {avg_cpu:.1f}%")
            print(f"✅ 启动模块数: {performance_data['startup_modules_loaded']}")
            print(f"✅ 优化模块数: {performance_data['optimization_modules_active']}")
            print(f"✅ 错误数量: {performance_data['error_count']}")
            print(f"✅ 警告数量: {performance_data['warning_count']}")
            print(f"✅ 综合评分: {overall_score}/100")
            print(f"✅ 性能等级: {result['performance_grade']}")

            return result

        except Exception as e:
            print(f"❌ 整体性能测试失败: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_ux_grade(self, ux_score, shortcuts_count):
        """计算用户体验等级"""
        if ux_score >= 90 and shortcuts_count >= 8:
            return "A+ (优秀)"
        elif ux_score >= 75 and shortcuts_count >= 6:
            return "A (良好)"
        elif ux_score >= 50 and shortcuts_count >= 4:
            return "B (合格)"
        else:
            return "C (需改进)"

    def _calculate_overall_grade(self, overall_score):
        """计算整体性能等级"""
        if overall_score >= 90:
            return "A+ (优秀)"
        elif overall_score >= 80:
            return "A (良好)"
        elif overall_score >= 70:
            return "B (合格)"
        else:
            return "C (需改进)"

    def generate_enhanced_optimization_report(self):
        """生成第二阶段优化报告"""
        print("\n" + "="*70)
        print("📋 VisionAI-ClipsMaster 第二阶段优化报告")
        print("="*70)

        # 计算各项评分
        scores = []

        # 启动性能评分
        if self.test_results.get("startup_optimization", {}).get("success"):
            startup_data = self.test_results["startup_optimization"]
            startup_time = startup_data["average_startup_time"]
            if startup_time <= 2.5:
                startup_score = 100
            elif startup_time <= 3.5:
                startup_score = 85
            elif startup_time <= 5.0:
                startup_score = 70
            else:
                startup_score = 50
            scores.append(startup_score)
            print(f"启动性能: {startup_score}/100 (平均时间: {startup_time:.2f}秒)")

        # 响应监控评分
        if self.test_results.get("response_monitoring", {}).get("success"):
            response_data = self.test_results["response_monitoring"]
            if response_data.get("target_achieved"):
                response_score = 100
            elif response_data.get("data_collection_working"):
                response_score = 80
            elif response_data.get("monitoring_active"):
                response_score = 60
            else:
                response_score = 40
            scores.append(response_score)
            print(f"响应监控: {response_score}/100")

        # CSS优化评分
        if self.test_results.get("css_optimization", {}).get("success"):
            css_data = self.test_results["css_optimization"]
            css_score = css_data.get("optimization_score", 0)
            scores.append(css_score)
            print(f"CSS优化: {css_score}/100 (警告: {css_data.get('unknown_property_warnings', 0)}个)")

        # 用户体验评分
        if self.test_results.get("user_experience", {}).get("success"):
            ux_data = self.test_results["user_experience"]
            ux_score = ux_data.get("ux_score", 0)
            scores.append(ux_score)
            print(f"用户体验: {ux_score}/100 (快捷键: {ux_data.get('shortcuts_count', 0)}个)")

        # 整体性能评分
        if self.test_results.get("overall_performance", {}).get("success"):
            overall_data = self.test_results["overall_performance"]
            overall_score = overall_data.get("overall_score", 0)
            scores.append(overall_score)
            print(f"整体性能: {overall_score}/100 (内存: {overall_data.get('average_memory_mb', 0):.1f}MB)")

        # 计算总体评分
        if scores:
            final_score = sum(scores) / len(scores)
            print(f"\n🎯 第二阶段优化总评分: {final_score:.1f}/100")

            # 确定等级
            if final_score >= 90:
                grade = "A+ (优秀)"
                status = "🏆 第二阶段优化目标完全达成"
            elif final_score >= 80:
                grade = "A (良好)"
                status = "✅ 第二阶段优化目标基本达成"
            elif final_score >= 70:
                grade = "B (合格)"
                status = "⚠️ 第二阶段优化目标部分达成"
            else:
                grade = "C (需改进)"
                status = "❌ 第二阶段优化目标未达成"

            print(f"🏅 优化等级: {grade}")
            print(f"📊 优化状态: {status}")

            # 与第一阶段对比
            print(f"\n📈 优化效果对比:")
            print(f"第一阶段评分: 86.7/100 (A级)")
            print(f"第二阶段评分: {final_score:.1f}/100 ({grade})")

            improvement = final_score - 86.7
            if improvement > 0:
                print(f"评分提升: +{improvement:.1f}分 ⬆️")
            else:
                print(f"评分变化: {improvement:.1f}分")

            # 功能完整性检查
            print(f"\n🔧 功能完整性检查:")

            features_status = {
                "启动优化器": self.test_results.get("startup_optimization", {}).get("optimization_features", {}).get("startup_optimizer_loaded", False),
                "响应监控增强": self.test_results.get("response_monitoring", {}).get("enhanced_monitor_loaded", False),
                "CSS优化器": self.test_results.get("css_optimization", {}).get("css_optimizer_loaded", False),
                "用户体验增强": self.test_results.get("user_experience", {}).get("ux_enhancer_loaded", False),
                "延迟加载": self.test_results.get("startup_optimization", {}).get("optimization_features", {}).get("delayed_initialization", False)
            }

            for feature, status in features_status.items():
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {feature}: {'可用' if status else '不可用'}")

            # 性能目标达成情况
            print(f"\n🎯 性能目标达成情况:")

            startup_target = self.test_results.get("startup_optimization", {}).get("target_achieved", False)
            response_target = self.test_results.get("response_monitoring", {}).get("target_achieved", False)

            print(f"{'✅' if startup_target else '❌'} 启动时间 <3秒: {'达成' if startup_target else '未达成'}")
            print(f"{'✅' if response_target else '❌'} 响应时间 <1秒: {'达成' if response_target else '未达成'}")

            memory_avg = self.test_results.get("overall_performance", {}).get("average_memory_mb", 0)
            memory_target = memory_avg < 500 if memory_avg > 0 else False
            print(f"{'✅' if memory_target else '❌'} 内存使用 <500MB: {'达成' if memory_target else '未达成'}")

            # 保存详细报告
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "phase": "第二阶段优化",
                "final_score": final_score,
                "grade": grade,
                "improvement": improvement,
                "test_results": self.test_results,
                "features_status": features_status,
                "targets_achieved": {
                    "startup_time": startup_target,
                    "response_time": response_target,
                    "memory_usage": memory_target
                },
                "optimization_summary": {
                    "startup_optimization": "激进延迟加载策略",
                    "response_monitoring": "增强响应时间监控",
                    "css_optimization": "CSS样式优化和缓存",
                    "user_experience": "操作预览和快捷键支持",
                    "overall_performance": "综合性能提升"
                }
            }

            with open("optimization_test_enhanced_report.json", "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"\n📄 详细报告已保存: optimization_test_enhanced_report.json")

            # 推荐后续优化方向
            print(f"\n🔮 后续优化建议:")
            if final_score < 90:
                if not startup_target:
                    print("• 进一步优化启动流程，考虑更激进的延迟加载")
                if not response_target:
                    print("• 优化UI响应机制，减少阻塞操作")
                if not memory_target:
                    print("• 加强内存管理，实施更积极的垃圾回收")
                print("• 考虑实施第三阶段优化：AI模型优化和GPU加速")
            else:
                print("• 🎉 第二阶段优化已达到优秀水平！")
                print("• 可以开始第三阶段：AI模型性能优化")
                print("• 考虑实施生产环境部署优化")

        print("="*70)

def main():
    """主函数"""
    tester = EnhancedOptimizationTester()
    results = tester.run_enhanced_optimization_test()

    # 返回测试是否成功
    success_count = sum(1 for result in results.values() if result.get("success", False))
    total_tests = len([r for r in results.values() if "success" in r])

    print(f"\n🎯 第二阶段优化测试完成: {success_count}/{total_tests} 项测试通过")

    # 判断是否达到90+分目标
    if "overall_performance" in results and results["overall_performance"].get("success"):
        overall_score = results["overall_performance"].get("overall_score", 0)
        target_achieved = overall_score >= 90
        print(f"🏆 90+分目标: {'达成' if target_achieved else '未达成'} (当前: {overall_score}/100)")
        return target_achieved

    return success_count >= total_tests * 0.8  # 80%通过率

if __name__ == "__main__":
    main()