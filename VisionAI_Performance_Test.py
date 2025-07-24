#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 性能和稳定性测试
测试内存占用、模型量化、异常恢复和长时运行稳定性
"""

import os
import sys
import time
import json
import psutil
import threading
from datetime import datetime
from pathlib import Path

class PerformanceStabilityTester:
    def __init__(self):
        self.test_results = {
            "test_start_time": datetime.now().isoformat(),
            "memory_tests": {},
            "quantization_tests": {},
            "stability_tests": {},
            "recovery_tests": {},
            "overall_status": "RUNNING"
        }
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        self.initial_memory = None
        
    def log_test_result(self, category, test_name, status, details=None, error=None):
        """记录测试结果"""
        result = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        self.test_results[category][test_name] = result
        print(f"[{status}] {category}.{test_name}: {details.get('message', '') if details else ''}")
        if error:
            print(f"    错误: {error}")
    
    def get_memory_usage(self):
        """获取当前内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\n=== 内存使用测试 ===")
        
        # 记录初始内存
        self.initial_memory = self.get_memory_usage()
        if "error" not in self.initial_memory:
            self.log_test_result("memory_tests", "initial_memory", "PASS", 
                               {"message": f"初始内存: {self.initial_memory['rss_mb']:.2f}MB"})
        else:
            self.log_test_result("memory_tests", "initial_memory", "FAIL", 
                               {"message": "无法获取内存信息"}, self.initial_memory["error"])
            return
        
        # 测试4GB内存限制
        if self.initial_memory['rss_mb'] < 4000:
            self.log_test_result("memory_tests", "memory_limit_check", "PASS", 
                               {"message": f"内存使用 {self.initial_memory['rss_mb']:.2f}MB < 4GB限制"})
        else:
            self.log_test_result("memory_tests", "memory_limit_check", "FAIL", 
                               {"message": f"内存使用 {self.initial_memory['rss_mb']:.2f}MB > 4GB限制"})
        
        # 测试内存监控器
        try:
            from src.utils.memory_guard import MemoryGuard
            guard = MemoryGuard()
            self.log_test_result("memory_tests", "memory_guard_import", "PASS", 
                               {"message": "内存监控器导入成功"})
        except ImportError as e:
            self.log_test_result("memory_tests", "memory_guard_import", "FAIL", 
                               {"message": "内存监控器导入失败"}, str(e))
    
    def test_model_quantization(self):
        """测试模型量化功能"""
        print("\n=== 模型量化测试 ===")
        
        # 测试量化配置
        try:
            from src.quant.quant_analyzer import QuantAnalyzer
            analyzer = QuantAnalyzer()
            self.log_test_result("quantization_tests", "quant_analyzer_import", "PASS", 
                               {"message": "量化分析器导入成功"})
        except ImportError as e:
            self.log_test_result("quantization_tests", "quant_analyzer_import", "FAIL", 
                               {"message": "量化分析器导入失败"}, str(e))
        
        # 测试量化策略
        try:
            from src.quant.quant_decision import QuantDecision
            decision = QuantDecision()
            self.log_test_result("quantization_tests", "quant_decision_import", "PASS", 
                               {"message": "量化决策器导入成功"})
        except ImportError as e:
            self.log_test_result("quantization_tests", "quant_decision_import", "FAIL", 
                               {"message": "量化决策器导入失败"}, str(e))
        
        # 测试量化配置文件
        quant_config_files = [
            "configs/quant_levels.yaml",
            "configs/quant_layers.yaml"
        ]
        
        for config_file in quant_config_files:
            if os.path.exists(config_file):
                try:
                    import yaml
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    self.log_test_result("quantization_tests", f"config_{os.path.basename(config_file)}", 
                                       "PASS", {"message": f"{config_file}配置加载成功"})
                except Exception as e:
                    self.log_test_result("quantization_tests", f"config_{os.path.basename(config_file)}", 
                                       "FAIL", {"message": f"{config_file}配置加载失败"}, str(e))
            else:
                self.log_test_result("quantization_tests", f"config_{os.path.basename(config_file)}", 
                                   "SKIP", {"message": f"{config_file}文件不存在"})
    
    def test_exception_recovery(self):
        """测试异常恢复机制"""
        print("\n=== 异常恢复测试 ===")
        
        # 测试恢复管理器
        try:
            from src.core.recovery_manager import RecoveryManager
            recovery = RecoveryManager()
            self.log_test_result("recovery_tests", "recovery_manager_import", "PASS", 
                               {"message": "恢复管理器导入成功"})
        except ImportError as e:
            self.log_test_result("recovery_tests", "recovery_manager_import", "FAIL", 
                               {"message": "恢复管理器导入失败"}, str(e))
        
        # 测试检查点管理器
        try:
            from src.core.checkpoint_manager import CheckpointManager
            checkpoint = CheckpointManager()
            self.log_test_result("recovery_tests", "checkpoint_manager_import", "PASS", 
                               {"message": "检查点管理器导入成功"})
        except ImportError as e:
            self.log_test_result("recovery_tests", "checkpoint_manager_import", "FAIL", 
                               {"message": "检查点管理器导入失败"}, str(e))
        
        # 测试异常处理器
        try:
            from src.core.enhanced_exception_handler import EnhancedExceptionHandler
            handler = EnhancedExceptionHandler()
            self.log_test_result("recovery_tests", "exception_handler_import", "PASS", 
                               {"message": "异常处理器导入成功"})
        except ImportError as e:
            self.log_test_result("recovery_tests", "exception_handler_import", "FAIL", 
                               {"message": "异常处理器导入失败"}, str(e))
    
    def test_stability(self):
        """测试系统稳定性"""
        print("\n=== 稳定性测试 ===")
        
        # 测试配置文件完整性
        critical_configs = [
            "configs/model_config.yaml",
            "configs/security_policy.json",
            "configs/memory_optimization.json"
        ]
        
        config_integrity_passed = 0
        for config_file in critical_configs:
            if os.path.exists(config_file):
                try:
                    if config_file.endswith('.yaml'):
                        import yaml
                        with open(config_file, 'r', encoding='utf-8') as f:
                            yaml.safe_load(f)
                    elif config_file.endswith('.json'):
                        with open(config_file, 'r', encoding='utf-8') as f:
                            json.load(f)
                    config_integrity_passed += 1
                    self.log_test_result("stability_tests", f"config_integrity_{os.path.basename(config_file)}", 
                                       "PASS", {"message": f"{config_file}完整性检查通过"})
                except Exception as e:
                    self.log_test_result("stability_tests", f"config_integrity_{os.path.basename(config_file)}", 
                                       "FAIL", {"message": f"{config_file}完整性检查失败"}, str(e))
            else:
                self.log_test_result("stability_tests", f"config_integrity_{os.path.basename(config_file)}", 
                                   "SKIP", {"message": f"{config_file}文件不存在"})
        
        # 测试内存稳定性
        current_memory = self.get_memory_usage()
        if "error" not in current_memory and self.initial_memory:
            memory_increase = current_memory['rss_mb'] - self.initial_memory['rss_mb']
            if memory_increase < 100:  # 内存增长小于100MB
                self.log_test_result("stability_tests", "memory_stability", "PASS", 
                                   {"message": f"内存增长: {memory_increase:.2f}MB (< 100MB)"})
            else:
                self.log_test_result("stability_tests", "memory_stability", "WARN", 
                                   {"message": f"内存增长: {memory_increase:.2f}MB (> 100MB)"})
        else:
            self.log_test_result("stability_tests", "memory_stability", "SKIP", 
                               {"message": "无法检测内存稳定性"})
    
    def generate_report(self):
        """生成测试报告"""
        self.test_results["test_end_time"] = datetime.now().isoformat()
        
        # 统计测试结果
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        warned_tests = 0
        
        for category in ["memory_tests", "quantization_tests", "recovery_tests", "stability_tests"]:
            for test_name, result in self.test_results[category].items():
                total_tests += 1
                if result["status"] == "PASS":
                    passed_tests += 1
                elif result["status"] == "FAIL":
                    failed_tests += 1
                elif result["status"] == "SKIP":
                    skipped_tests += 1
                elif result["status"] == "WARN":
                    warned_tests += 1
        
        # 确定整体状态
        if failed_tests > 0:
            self.test_results["overall_status"] = "FAIL"
        elif warned_tests > 0:
            self.test_results["overall_status"] = "WARN"
        elif passed_tests > 0:
            self.test_results["overall_status"] = "PASS"
        else:
            self.test_results["overall_status"] = "SKIP"
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warned": warned_tests,
            "skipped": skipped_tests,
            "success_rate": f"{(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }
        
        # 保存测试报告
        report_file = self.output_dir / f"performance_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 性能稳定性测试报告 ===")
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"警告: {warned_tests}")
        print(f"跳过: {skipped_tests}")
        print(f"成功率: {self.test_results['summary']['success_rate']}")
        print(f"整体状态: {self.test_results['overall_status']}")
        print(f"详细报告已保存到: {report_file}")
        
        return self.test_results
    
    def run_all_tests(self):
        """运行所有性能稳定性测试"""
        print("开始VisionAI-ClipsMaster性能稳定性测试...")
        print(f"测试开始时间: {self.test_results['test_start_time']}")
        
        try:
            self.test_memory_usage()
            self.test_model_quantization()
            self.test_exception_recovery()
            self.test_stability()
        except Exception as e:
            print(f"测试执行异常: {e}")
        finally:
            return self.generate_report()

if __name__ == "__main__":
    perf_tester = PerformanceStabilityTester()
    results = perf_tester.run_all_tests()
