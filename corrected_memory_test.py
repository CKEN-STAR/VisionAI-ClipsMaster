#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 修正版内存测试
准确测量进程内存使用，而非系统总内存
"""

import os
import sys
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CorrectedMemoryTest:
    """修正版内存测试器"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.current_process = psutil.Process()
        self.baseline_memory = self._get_process_memory_gb()
        
    def _get_process_memory_gb(self) -> float:
        """获取当前进程的内存使用（GB）"""
        memory_info = self.current_process.memory_info()
        return memory_info.rss / 1024**3  # RSS = 实际物理内存使用
    
    def _get_system_memory_info(self) -> Dict[str, float]:
        """获取系统内存信息"""
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / 1024**3,
            "available_gb": memory.available / 1024**3,
            "used_gb": memory.used / 1024**3,
            "percent": memory.percent
        }
    
    def test_memory_usage_during_workflow(self) -> Dict[str, Any]:
        """测试工作流程中的实际内存使用"""
        print("🧪 测试工作流程中的实际内存使用...")
        
        # 记录基线内存
        baseline = self._get_process_memory_gb()
        print(f"   基线内存: {baseline:.3f}GB")
        
        memory_snapshots = []
        
        # 步骤1: 导入核心模块
        print("   步骤1: 导入核心模块...")
        step1_start = self._get_process_memory_gb()
        
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            from src.core.language_detector import LanguageDetector
            from src.exporters.jianying_pro_exporter import JianYingProExporter
        except ImportError as e:
            print(f"   ⚠️ 模块导入失败: {e}")
        
        step1_end = self._get_process_memory_gb()
        step1_increase = step1_end - step1_start
        
        memory_snapshots.append({
            "step": "模块导入",
            "start_gb": step1_start,
            "end_gb": step1_end,
            "increase_gb": step1_increase
        })
        
        print(f"   模块导入后: {step1_end:.3f}GB (增加: {step1_increase:.3f}GB)")
        
        # 步骤2: 创建对象实例
        print("   步骤2: 创建对象实例...")
        step2_start = self._get_process_memory_gb()
        
        try:
            engineer = ScreenplayEngineer()
            detector = LanguageDetector()
            exporter = JianYingProExporter()
        except Exception as e:
            print(f"   ⚠️ 对象创建失败: {e}")
        
        step2_end = self._get_process_memory_gb()
        step2_increase = step2_end - step2_start
        
        memory_snapshots.append({
            "step": "对象创建",
            "start_gb": step2_start,
            "end_gb": step2_end,
            "increase_gb": step2_increase
        })
        
        print(f"   对象创建后: {step2_end:.3f}GB (增加: {step2_increase:.3f}GB)")
        
        # 步骤3: 执行AI处理
        print("   步骤3: 执行AI处理...")
        step3_start = self._get_process_memory_gb()
        
        try:
            test_subtitles = [
                {"start_time": 0.0, "end_time": 2.0, "text": "测试字幕1"},
                {"start_time": 2.0, "end_time": 4.0, "text": "测试字幕2"}
            ]
            result = engineer.generate_screenplay(test_subtitles, language='zh')
        except Exception as e:
            print(f"   ⚠️ AI处理失败: {e}")
        
        step3_end = self._get_process_memory_gb()
        step3_increase = step3_end - step3_start
        
        memory_snapshots.append({
            "step": "AI处理",
            "start_gb": step3_start,
            "end_gb": step3_end,
            "increase_gb": step3_increase
        })
        
        print(f"   AI处理后: {step3_end:.3f}GB (增加: {step3_increase:.3f}GB)")
        
        # 步骤4: 导出处理
        print("   步骤4: 导出处理...")
        step4_start = self._get_process_memory_gb()
        
        try:
            project_data = {
                "project_name": "MemoryTest",
                "segments": result.get("screenplay", []),
                "subtitles": []
            }
            output_path = self.project_root / "test_outputs" / "memory_test_export.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            success = exporter.export_project(project_data, str(output_path))
        except Exception as e:
            print(f"   ⚠️ 导出处理失败: {e}")
        
        step4_end = self._get_process_memory_gb()
        step4_increase = step4_end - step4_start
        
        memory_snapshots.append({
            "step": "导出处理",
            "start_gb": step4_start,
            "end_gb": step4_end,
            "increase_gb": step4_increase
        })
        
        print(f"   导出处理后: {step4_end:.3f}GB (增加: {step4_increase:.3f}GB)")
        
        # 计算总体内存使用
        total_increase = step4_end - baseline
        peak_memory = max(snapshot["end_gb"] for snapshot in memory_snapshots)
        
        result = {
            "baseline_memory_gb": baseline,
            "peak_memory_gb": peak_memory,
            "total_increase_gb": total_increase,
            "memory_snapshots": memory_snapshots,
            "target_met": peak_memory <= 3.8,
            "system_info": self._get_system_memory_info()
        }
        
        print(f"\n📊 内存使用总结:")
        print(f"   基线内存: {baseline:.3f}GB")
        print(f"   峰值内存: {peak_memory:.3f}GB")
        print(f"   总增长: {total_increase:.3f}GB")
        print(f"   目标达成: {'是' if result['target_met'] else '否'} (≤3.8GB)")
        
        return result
    
    def test_memory_cleanup_effectiveness(self) -> Dict[str, Any]:
        """测试内存清理效果"""
        print("\n🧹 测试内存清理效果...")
        
        # 记录清理前内存
        before_cleanup = self._get_process_memory_gb()
        print(f"   清理前内存: {before_cleanup:.3f}GB")
        
        # 执行内存清理
        import gc
        
        # 强制垃圾回收
        collected_objects = 0
        for _ in range(3):
            collected = gc.collect()
            collected_objects += collected
        
        # 清理后内存
        after_cleanup = self._get_process_memory_gb()
        memory_freed = before_cleanup - after_cleanup
        
        print(f"   清理后内存: {after_cleanup:.3f}GB")
        print(f"   释放内存: {memory_freed:.3f}GB")
        print(f"   回收对象: {collected_objects}个")
        
        return {
            "before_cleanup_gb": before_cleanup,
            "after_cleanup_gb": after_cleanup,
            "memory_freed_gb": memory_freed,
            "objects_collected": collected_objects,
            "cleanup_effective": memory_freed > 0.01  # 释放超过10MB认为有效
        }
    
    def test_4gb_device_simulation(self) -> Dict[str, Any]:
        """模拟4GB设备测试"""
        print("\n💻 模拟4GB设备兼容性测试...")
        
        # 获取系统信息
        system_info = self._get_system_memory_info()
        current_process_memory = self._get_process_memory_gb()
        
        # 模拟4GB设备的可用内存（考虑系统占用约1GB）
        simulated_available_memory = 3.0  # 4GB - 1GB系统占用
        
        # 评估兼容性
        memory_usage_ratio = current_process_memory / simulated_available_memory
        compatible = current_process_memory <= simulated_available_memory * 0.9  # 90%阈值
        
        result = {
            "simulated_device_memory_gb": 4.0,
            "simulated_available_gb": simulated_available_memory,
            "current_process_memory_gb": current_process_memory,
            "memory_usage_ratio": memory_usage_ratio,
            "compatible": compatible,
            "recommendation": self._get_4gb_recommendation(current_process_memory, simulated_available_memory)
        }
        
        print(f"   模拟4GB设备可用内存: {simulated_available_memory:.1f}GB")
        print(f"   当前进程内存: {current_process_memory:.3f}GB")
        print(f"   内存使用率: {memory_usage_ratio*100:.1f}%")
        print(f"   兼容性: {'兼容' if compatible else '不兼容'}")
        
        return result
    
    def _get_4gb_recommendation(self, current_memory: float, available_memory: float) -> str:
        """获取4GB设备优化建议"""
        if current_memory <= available_memory * 0.5:
            return "内存使用优秀，完全兼容4GB设备"
        elif current_memory <= available_memory * 0.7:
            return "内存使用良好，基本兼容4GB设备"
        elif current_memory <= available_memory * 0.9:
            return "内存使用偏高，需要优化以更好兼容4GB设备"
        else:
            return "内存使用超标，必须优化才能兼容4GB设备"
    
    def run_comprehensive_memory_test(self) -> Dict[str, Any]:
        """运行综合内存测试"""
        print("=== VisionAI-ClipsMaster 修正版内存测试 ===")
        print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示系统信息
        system_info = self._get_system_memory_info()
        print(f"\n📊 系统信息:")
        print(f"   系统总内存: {system_info['total_gb']:.2f}GB")
        print(f"   系统可用内存: {system_info['available_gb']:.2f}GB")
        print(f"   系统使用率: {system_info['percent']:.1f}%")
        print(f"   进程基线内存: {self.baseline_memory:.3f}GB")
        print()
        
        # 执行各项测试
        test_results = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "system_info": system_info,
            "baseline_memory_gb": self.baseline_memory,
            "workflow_memory_test": self.test_memory_usage_during_workflow(),
            "cleanup_test": self.test_memory_cleanup_effectiveness(),
            "4gb_compatibility_test": self.test_4gb_device_simulation()
        }
        
        # 生成最终评估
        workflow_result = test_results["workflow_memory_test"]
        compatibility_result = test_results["4gb_compatibility_test"]
        
        test_results["final_assessment"] = {
            "peak_memory_gb": workflow_result["peak_memory_gb"],
            "target_met": workflow_result["target_met"],
            "4gb_compatible": compatibility_result["compatible"],
            "overall_status": "PASSED" if (workflow_result["target_met"] and compatibility_result["compatible"]) else "FAILED",
            "recommendations": [
                compatibility_result["recommendation"]
            ]
        }
        
        # 显示最终结果
        print("\n📋 最终评估结果:")
        print(f"   峰值内存使用: {workflow_result['peak_memory_gb']:.3f}GB")
        print(f"   3.8GB目标: {'达成' if workflow_result['target_met'] else '未达成'}")
        print(f"   4GB设备兼容: {'是' if compatibility_result['compatible'] else '否'}")
        print(f"   总体状态: {test_results['final_assessment']['overall_status']}")
        
        # 保存测试结果
        results_file = self.project_root / "test_outputs" / f"corrected_memory_test_{time.strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📊 测试结果已保存: {results_file}")
        
        return test_results


def main():
    """主函数"""
    tester = CorrectedMemoryTest()
    return tester.run_comprehensive_memory_test()


if __name__ == "__main__":
    main()
