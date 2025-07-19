#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 时间轴精度最终验证测试
验证改进后的alignment_engineer.py是否达到95%精度目标

最终验证目标：
1. 平均误差 ≤ 0.2秒
2. 精度达标率 ≥ 95%
3. 最大误差 ≤ 0.5秒
4. 处理各种边界情况
"""

import os
import sys
import json
import time
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 导入优化后的对齐工程师
from src.core.alignment_engineer import (
    PrecisionAlignmentEngineer, 
    AlignmentPrecision,
    align_subtitles_with_precision
)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalTimecodeValidator:
    """时间轴精度最终验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.validation_results = {
            "validation_start_time": datetime.now().isoformat(),
            "test_scenarios": {},
            "final_metrics": {},
            "validation_passed": False
        }
        
    def run_final_validation(self) -> Dict[str, Any]:
        """运行最终验证"""
        logger.info("开始时间轴精度最终验证")
        
        try:
            # 场景1: 标准对齐测试
            scenario1 = self._test_standard_alignment()
            self.validation_results["test_scenarios"]["standard_alignment"] = scenario1
            
            # 场景2: 边界情况测试
            scenario2 = self._test_boundary_cases()
            self.validation_results["test_scenarios"]["boundary_cases"] = scenario2
            
            # 场景3: 高精度要求测试
            scenario3 = self._test_high_precision_requirements()
            self.validation_results["test_scenarios"]["high_precision"] = scenario3
            
            # 场景4: 实际数据模拟测试
            scenario4 = self._test_realistic_data()
            self.validation_results["test_scenarios"]["realistic_data"] = scenario4
            
            # 计算最终指标
            final_metrics = self._calculate_final_metrics([scenario1, scenario2, scenario3, scenario4])
            self.validation_results["final_metrics"] = final_metrics
            
            # 判断是否通过验证
            self.validation_results["validation_passed"] = self._evaluate_final_validation(final_metrics)
            
        except Exception as e:
            logger.error(f"最终验证失败: {str(e)}")
            self.validation_results["error"] = str(e)
        
        self.validation_results["validation_end_time"] = datetime.now().isoformat()
        return self.validation_results
    
    def _test_standard_alignment(self) -> Dict[str, Any]:
        """测试标准对齐场景"""
        logger.info("测试场景1: 标准对齐")
        
        # 标准测试数据：轻微时间偏移
        original_subtitles = [
            {"start": "00:00:01,000", "end": "00:00:03,000", "text": "开场介绍"},
            {"start": "00:00:05,000", "end": "00:00:07,000", "text": "主要内容"},
            {"start": "00:00:10,000", "end": "00:00:12,000", "text": "关键信息"},
            {"start": "00:00:15,000", "end": "00:00:17,000", "text": "重要转折"},
            {"start": "00:00:20,000", "end": "00:00:22,000", "text": "精彩高潮"},
            {"start": "00:00:25,000", "end": "00:00:27,000", "text": "完美结尾"}
        ]
        
        reconstructed_subtitles = [
            {"start": "00:00:01,100", "end": "00:00:03,100", "text": "开场介绍"},
            {"start": "00:00:05,150", "end": "00:00:07,150", "text": "主要内容"},
            {"start": "00:00:10,200", "end": "00:00:12,200", "text": "关键信息"},
            {"start": "00:00:15,050", "end": "00:00:17,050", "text": "重要转折"},
            {"start": "00:00:20,180", "end": "00:00:22,180", "text": "精彩高潮"},
            {"start": "00:00:25,120", "end": "00:00:27,120", "text": "完美结尾"}
        ]
        
        return self._execute_alignment_test("标准对齐", original_subtitles, reconstructed_subtitles, 30.0)
    
    def _test_boundary_cases(self) -> Dict[str, Any]:
        """测试边界情况"""
        logger.info("测试场景2: 边界情况")
        
        # 边界测试数据：包含视频开头、结尾、大间隙
        original_subtitles = [
            {"start": "00:00:00,500", "end": "00:00:02,000", "text": "视频开头"},
            {"start": "00:00:05,000", "end": "00:00:06,500", "text": "早期内容"},
            {"start": "00:00:15,000", "end": "00:00:16,500", "text": "中期内容"},  # 大间隙
            {"start": "00:00:28,000", "end": "00:00:29,500", "text": "后期内容"},  # 大间隙
            {"start": "00:00:29,800", "end": "00:00:30,000", "text": "视频结尾"}   # 接近结尾
        ]
        
        reconstructed_subtitles = [
            {"start": "00:00:00,600", "end": "00:00:02,100", "text": "视频开头"},
            {"start": "00:00:05,200", "end": "00:00:06,700", "text": "早期内容"},
            {"start": "00:00:15,300", "end": "00:00:16,800", "text": "中期内容"},
            {"start": "00:00:28,100", "end": "00:00:29,600", "text": "后期内容"},
            {"start": "00:00:29,900", "end": "00:00:30,100", "text": "视频结尾"}
        ]
        
        return self._execute_alignment_test("边界情况", original_subtitles, reconstructed_subtitles, 30.0)
    
    def _test_high_precision_requirements(self) -> Dict[str, Any]:
        """测试高精度要求"""
        logger.info("测试场景3: 高精度要求")
        
        # 高精度测试数据：非常小的时间偏移
        original_subtitles = [
            {"start": "00:00:01,000", "end": "00:00:02,500", "text": "精确时间点1"},
            {"start": "00:00:03,000", "end": "00:00:04,500", "text": "精确时间点2"},
            {"start": "00:00:05,000", "end": "00:00:06,500", "text": "精确时间点3"},
            {"start": "00:00:07,000", "end": "00:00:08,500", "text": "精确时间点4"},
            {"start": "00:00:09,000", "end": "00:00:10,500", "text": "精确时间点5"}
        ]
        
        reconstructed_subtitles = [
            {"start": "00:00:01,050", "end": "00:00:02,550", "text": "精确时间点1"},  # 0.05秒偏移
            {"start": "00:00:03,080", "end": "00:00:04,580", "text": "精确时间点2"},  # 0.08秒偏移
            {"start": "00:00:05,120", "end": "00:00:06,620", "text": "精确时间点3"},  # 0.12秒偏移
            {"start": "00:00:07,030", "end": "00:00:08,530", "text": "精确时间点4"},  # 0.03秒偏移
            {"start": "00:00:09,090", "end": "00:00:10,590", "text": "精确时间点5"}   # 0.09秒偏移
        ]
        
        return self._execute_alignment_test("高精度要求", original_subtitles, reconstructed_subtitles, 12.0)
    
    def _test_realistic_data(self) -> Dict[str, Any]:
        """测试真实数据模拟"""
        logger.info("测试场景4: 真实数据模拟")
        
        # 真实数据模拟：不规则间隔和偏移
        original_subtitles = [
            {"start": "00:00:01,200", "end": "00:00:03,800", "text": "真实场景开始"},
            {"start": "00:00:04,500", "end": "00:00:06,200", "text": "对话内容A"},
            {"start": "00:00:07,800", "end": "00:00:09,100", "text": "对话内容B"},
            {"start": "00:00:12,300", "end": "00:00:14,700", "text": "情节发展"},
            {"start": "00:00:16,100", "end": "00:00:18,900", "text": "关键转折"},
            {"start": "00:00:22,400", "end": "00:00:24,100", "text": "高潮部分"},
            {"start": "00:00:26,800", "end": "00:00:28,500", "text": "结局收尾"}
        ]
        
        reconstructed_subtitles = [
            {"start": "00:00:01,350", "end": "00:00:03,950", "text": "真实场景开始"},  # 0.15秒偏移
            {"start": "00:00:04,680", "end": "00:00:06,380", "text": "对话内容A"},    # 0.18秒偏移
            {"start": "00:00:12,450", "end": "00:00:14,850", "text": "情节发展"},      # 跳过一个，0.15秒偏移
            {"start": "00:00:16,280", "end": "00:00:19,080", "text": "关键转折"},      # 0.18秒偏移
            {"start": "00:00:22,600", "end": "00:00:24,300", "text": "高潮部分"},      # 0.2秒偏移
            {"start": "00:00:26,950", "end": "00:00:28,650", "text": "结局收尾"}       # 0.15秒偏移
        ]
        
        return self._execute_alignment_test("真实数据模拟", original_subtitles, reconstructed_subtitles, 30.0)
    
    def _execute_alignment_test(self, test_name: str, original_subtitles: List[Dict], 
                               reconstructed_subtitles: List[Dict], video_duration: float) -> Dict[str, Any]:
        """执行对齐测试"""
        try:
            start_time = time.time()
            
            # 执行对齐
            alignment_result = align_subtitles_with_precision(
                original_subtitles, reconstructed_subtitles, video_duration, "high"
            )
            
            processing_time = time.time() - start_time
            
            # 提取误差数据
            errors = [point.precision_error for point in alignment_result.alignment_points]
            
            if errors:
                avg_error = sum(errors) / len(errors)
                max_error = max(errors)
                min_error = min(errors)
                
                # 计算各精度等级的达标率
                ultra_high_count = sum(1 for e in errors if e <= 0.1)
                high_count = sum(1 for e in errors if e <= 0.2)
                standard_count = sum(1 for e in errors if e <= 0.5)
                
                ultra_high_rate = ultra_high_count / len(errors) * 100
                high_rate = high_count / len(errors) * 100
                standard_rate = standard_count / len(errors) * 100
            else:
                avg_error = max_error = min_error = 0.0
                ultra_high_rate = high_rate = standard_rate = 100.0
            
            return {
                "test_name": test_name,
                "success": True,
                "metrics": {
                    "average_error_seconds": round(avg_error, 4),
                    "max_error_seconds": round(max_error, 4),
                    "min_error_seconds": round(min_error, 4),
                    "ultra_high_precision_rate": round(ultra_high_rate, 1),  # ≤0.1秒
                    "high_precision_rate": round(high_rate, 1),              # ≤0.2秒
                    "standard_precision_rate": round(standard_rate, 1),      # ≤0.5秒
                    "total_alignment_points": len(errors),
                    "processing_time_seconds": round(processing_time, 4),
                    "engine_precision_rate": alignment_result.precision_rate,
                    "engine_quality_score": alignment_result.quality_score
                },
                "target_achievement": {
                    "average_error_target": avg_error <= 0.2,
                    "precision_rate_target": high_rate >= 95.0,
                    "max_error_target": max_error <= 0.5
                }
            }
            
        except Exception as e:
            logger.error(f"测试 {test_name} 失败: {str(e)}")
            return {
                "test_name": test_name,
                "success": False,
                "error": str(e),
                "metrics": {},
                "target_achievement": {
                    "average_error_target": False,
                    "precision_rate_target": False,
                    "max_error_target": False
                }
            }
    
    def _calculate_final_metrics(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算最终指标"""
        successful_scenarios = [s for s in scenarios if s.get("success", False)]
        
        if not successful_scenarios:
            return {
                "overall_success_rate": 0.0,
                "average_error_across_scenarios": 999.0,
                "max_error_across_scenarios": 999.0,
                "precision_rate_across_scenarios": 0.0,
                "targets_achieved": 0,
                "total_targets": 12  # 4个场景 × 3个目标
            }
        
        # 聚合所有场景的指标
        all_avg_errors = [s["metrics"]["average_error_seconds"] for s in successful_scenarios]
        all_max_errors = [s["metrics"]["max_error_seconds"] for s in successful_scenarios]
        all_precision_rates = [s["metrics"]["high_precision_rate"] for s in successful_scenarios]
        
        # 计算目标达成情况
        targets_achieved = 0
        total_targets = 0
        
        for scenario in scenarios:
            if scenario.get("success", False):
                targets = scenario.get("target_achievement", {})
                targets_achieved += sum(targets.values())
                total_targets += len(targets)
        
        return {
            "overall_success_rate": len(successful_scenarios) / len(scenarios) * 100,
            "average_error_across_scenarios": round(sum(all_avg_errors) / len(all_avg_errors), 4),
            "max_error_across_scenarios": round(max(all_max_errors), 4),
            "precision_rate_across_scenarios": round(sum(all_precision_rates) / len(all_precision_rates), 1),
            "targets_achieved": targets_achieved,
            "total_targets": total_targets,
            "target_achievement_rate": round(targets_achieved / total_targets * 100, 1) if total_targets > 0 else 0
        }
    
    def _evaluate_final_validation(self, final_metrics: Dict[str, Any]) -> bool:
        """评估最终验证是否通过"""
        criteria = [
            final_metrics["overall_success_rate"] >= 100.0,           # 所有场景成功
            final_metrics["average_error_across_scenarios"] <= 0.2,   # 平均误差≤0.2秒
            final_metrics["max_error_across_scenarios"] <= 0.5,       # 最大误差≤0.5秒
            final_metrics["precision_rate_across_scenarios"] >= 95.0, # 精度≥95%
            final_metrics["target_achievement_rate"] >= 90.0          # 目标达成率≥90%
        ]
        
        return all(criteria)
    
    def save_validation_results(self, filename: Optional[str] = None):
        """保存验证结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"final_timecode_precision_validation_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"验证结果已保存到: {filename}")
        return filename


def main():
    """主函数"""
    print("=" * 70)
    print("VisionAI-ClipsMaster 时间轴精度最终验证")
    print("=" * 70)
    
    validator = FinalTimecodeValidator()
    
    try:
        # 运行最终验证
        results = validator.run_final_validation()
        
        # 保存结果
        report_path = validator.save_validation_results()
        
        # 打印结果摘要
        print("\n" + "=" * 70)
        print("最终验证结果")
        print("=" * 70)
        
        validation_passed = results["validation_passed"]
        print(f"验证状态: {'✅ 通过' if validation_passed else '❌ 未通过'}")
        
        if "final_metrics" in results:
            metrics = results["final_metrics"]
            print(f"总体成功率: {metrics.get('overall_success_rate', 0):.1f}%")
            print(f"平均误差: {metrics.get('average_error_across_scenarios', 0):.4f}秒 (目标: ≤0.2秒)")
            print(f"最大误差: {metrics.get('max_error_across_scenarios', 0):.4f}秒 (目标: ≤0.5秒)")
            print(f"精度达标率: {metrics.get('precision_rate_across_scenarios', 0):.1f}% (目标: ≥95%)")
            print(f"目标达成率: {metrics.get('target_achievement_rate', 0):.1f}%")
        
        print(f"\n详细报告: {report_path}")
        
        if validation_passed:
            print("\n🎉 时间轴精度改进验证成功！可以部署使用。")
        else:
            print("\n⚠️  时间轴精度需要进一步优化。")
        
        return results
        
    except Exception as e:
        print(f"验证执行失败: {str(e)}")
        return None


if __name__ == "__main__":
    main()
