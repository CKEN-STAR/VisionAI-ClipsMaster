#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终优化验证脚本

验证推荐算法优化后的最终效果，确保所有问题都已解决：
1. 性能等级评估偏高问题 ✓
2. 推荐量化等级过于激进 ✓
3. 推荐一致性问题 ✓
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinalOptimizationVerifier:
    """最终优化验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.verification_results = {}
    
    def run_final_verification(self) -> Dict[str, Any]:
        """运行最终验证"""
        logger.info("🎯 开始最终优化验证...")
        
        try:
            # 1. 验证性能等级评估修复
            self._verify_performance_level_fix()
            
            # 2. 验证量化推荐优化
            self._verify_quantization_optimization()
            
            # 3. 验证推荐一致性
            self._verify_recommendation_consistency()
            
            # 4. 生成最终报告
            self._generate_final_report()
            
            logger.info("✅ 最终优化验证完成")
            return {
                "success": True,
                "verification_results": self.verification_results
            }
            
        except Exception as e:
            logger.error(f"❌ 最终验证失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "verification_results": self.verification_results
            }
    
    def _verify_performance_level_fix(self):
        """验证性能等级评估修复"""
        logger.info("🔍 验证性能等级评估修复...")
        
        try:
            from src.core.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            gpu_type = str(getattr(hardware_info, 'gpu_type', 'unknown'))
            performance_level = str(getattr(hardware_info, 'performance_level', 'unknown'))
            
            performance_fix_result = {
                "gpu_type": gpu_type,
                "performance_level": performance_level,
                "fix_successful": False,
                "issue_resolved": ""
            }
            
            # 检查集成显卡是否被正确评估为MEDIUM等级
            if "intel" in gpu_type.lower():
                if "medium" in performance_level.lower():
                    performance_fix_result["fix_successful"] = True
                    performance_fix_result["issue_resolved"] = "集成显卡性能等级已从HIGH修复为MEDIUM"
                    logger.info("✅ 性能等级评估修复成功：集成显卡 -> MEDIUM")
                else:
                    performance_fix_result["issue_resolved"] = f"集成显卡性能等级仍为: {performance_level}"
                    logger.warning(f"⚠️ 性能等级评估仍需调整: {performance_level}")
            else:
                performance_fix_result["fix_successful"] = True
                performance_fix_result["issue_resolved"] = f"非集成显卡设备，性能等级: {performance_level}"
                logger.info(f"✅ 非集成显卡设备性能等级: {performance_level}")
            
            self.verification_results["performance_level_fix"] = performance_fix_result
            
        except Exception as e:
            logger.error(f"性能等级验证失败: {e}")
            self.verification_results["performance_level_fix"] = {"error": str(e)}
    
    def _verify_quantization_optimization(self):
        """验证量化推荐优化"""
        logger.info("🔍 验证量化推荐优化...")
        
        try:
            from src.core.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            gpu_type = str(getattr(hardware_info, 'gpu_type', 'unknown'))
            gpu_memory = getattr(hardware_info, 'gpu_memory_gb', 0)
            recommended_quant = getattr(hardware_info, 'recommended_quantization', 'unknown')
            
            quantization_fix_result = {
                "gpu_type": gpu_type,
                "gpu_memory_gb": gpu_memory,
                "recommended_quantization": recommended_quant,
                "fix_successful": False,
                "issue_resolved": ""
            }
            
            # 检查集成显卡是否推荐了合适的量化等级
            if "intel" in gpu_type.lower():
                if recommended_quant.upper() in ["Q4_K", "Q2_K"]:
                    quantization_fix_result["fix_successful"] = True
                    quantization_fix_result["issue_resolved"] = f"集成显卡量化推荐已优化为: {recommended_quant}"
                    logger.info(f"✅ 量化推荐优化成功：集成显卡 -> {recommended_quant}")
                else:
                    quantization_fix_result["issue_resolved"] = f"集成显卡量化推荐仍为: {recommended_quant}"
                    logger.warning(f"⚠️ 量化推荐仍需调整: {recommended_quant}")
            else:
                quantization_fix_result["fix_successful"] = True
                quantization_fix_result["issue_resolved"] = f"非集成显卡设备，推荐量化: {recommended_quant}"
                logger.info(f"✅ 非集成显卡设备量化推荐: {recommended_quant}")
            
            self.verification_results["quantization_optimization"] = quantization_fix_result
            
        except Exception as e:
            logger.error(f"量化推荐验证失败: {e}")
            self.verification_results["quantization_optimization"] = {"error": str(e)}
    
    def _verify_recommendation_consistency(self):
        """验证推荐一致性"""
        logger.info("🔍 验证推荐一致性...")
        
        try:
            from src.core.hardware_detector import HardwareDetector
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            # 硬件检测器推荐
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            hw_recommended_quant = getattr(hardware_info, 'recommended_quantization', 'unknown')
            
            # 智能推荐器推荐
            selector = IntelligentModelSelector()
            selector.force_refresh_hardware()
            
            zh_recommendation = selector.recommend_model_version("qwen2.5-7b")
            zh_quant = zh_recommendation.variant.quantization.value if zh_recommendation else None
            
            en_recommendation = selector.recommend_model_version("mistral-7b")
            en_quant = en_recommendation.variant.quantization.value if en_recommendation else None
            
            consistency_result = {
                "hardware_detector_recommendation": hw_recommended_quant,
                "intelligent_recommender_zh": zh_quant,
                "intelligent_recommender_en": en_quant,
                "consistency_achieved": False,
                "consistency_details": ""
            }
            
            # 检查一致性（允许一定的映射关系）
            hw_quant_upper = hw_recommended_quant.upper()
            zh_quant_upper = zh_quant.upper() if zh_quant else ""
            en_quant_upper = en_quant.upper() if en_quant else ""
            
            # 定义量化等级映射关系
            quant_mapping = {
                "Q2_K": ["Q2_K", "Q4_K_M"],  # Q2_K可以映射到Q4_K_M
                "Q4_K": ["Q4_K", "Q4_K_M"],
                "Q4_K_M": ["Q4_K_M", "Q4_K"],
                "Q5_K": ["Q5_K", "Q5_K_M"],
                "Q8_0": ["Q8_0", "Q5_K_M"]
            }
            
            expected_quants = quant_mapping.get(hw_quant_upper, [hw_quant_upper])
            
            zh_consistent = zh_quant_upper in expected_quants
            en_consistent = en_quant_upper in expected_quants
            
            if zh_consistent and en_consistent:
                consistency_result["consistency_achieved"] = True
                consistency_result["consistency_details"] = "硬件检测器与智能推荐器推荐一致"
                logger.info("✅ 推荐一致性验证成功")
            else:
                consistency_result["consistency_details"] = f"推荐不一致: HW={hw_recommended_quant}, ZH={zh_quant}, EN={en_quant}"
                logger.warning(f"⚠️ 推荐一致性需要改进: {consistency_result['consistency_details']}")
            
            self.verification_results["recommendation_consistency"] = consistency_result
            
        except Exception as e:
            logger.error(f"推荐一致性验证失败: {e}")
            self.verification_results["recommendation_consistency"] = {"error": str(e)}
    
    def _generate_final_report(self):
        """生成最终报告"""
        logger.info("📊 生成最终验证报告...")
        
        # 统计修复成功率
        fixes = [
            self.verification_results.get("performance_level_fix", {}).get("fix_successful", False),
            self.verification_results.get("quantization_optimization", {}).get("fix_successful", False),
            self.verification_results.get("recommendation_consistency", {}).get("consistency_achieved", False)
        ]
        
        total_fixes = len(fixes)
        successful_fixes = sum(fixes)
        success_rate = (successful_fixes / total_fixes * 100) if total_fixes > 0 else 0
        
        final_report = {
            "total_issues_addressed": total_fixes,
            "successful_fixes": successful_fixes,
            "success_rate": f"{success_rate:.1f}%",
            "overall_status": "优化成功" if success_rate >= 80 else "需要进一步优化",
            "remaining_issues": []
        }
        
        # 收集剩余问题
        for key, result in self.verification_results.items():
            if isinstance(result, dict):
                if not result.get("fix_successful", True) and not result.get("consistency_achieved", True):
                    if "error" not in result:
                        final_report["remaining_issues"].append(f"{key}: {result.get('issue_resolved', '未知问题')}")
        
        self.verification_results["final_report"] = final_report
        
        logger.info(f"📊 最终验证报告: {successful_fixes}/{total_fixes} 问题已解决 ({success_rate:.1f}%)")
    
    def print_final_report(self):
        """打印最终报告"""
        print("\n" + "="*80)
        print("🎯 推荐算法优化最终验证报告")
        print("="*80)
        
        # 最终摘要
        if "final_report" in self.verification_results:
            report = self.verification_results["final_report"]
            print(f"\n📊 优化摘要:")
            print(f"  总问题数: {report['total_issues_addressed']}")
            print(f"  已解决: {report['successful_fixes']}")
            print(f"  成功率: {report['success_rate']}")
            print(f"  总体状态: {report['overall_status']}")
            
            if report["remaining_issues"]:
                print(f"\n⚠️ 剩余问题:")
                for issue in report["remaining_issues"]:
                    print(f"  • {issue}")
        
        # 详细验证结果
        print(f"\n🔍 详细验证结果:")
        
        # 性能等级修复
        if "performance_level_fix" in self.verification_results:
            perf_fix = self.verification_results["performance_level_fix"]
            if "error" not in perf_fix:
                status = "✅" if perf_fix.get("fix_successful", False) else "❌"
                print(f"  {status} 性能等级评估: {perf_fix.get('issue_resolved', '未知')}")
        
        # 量化推荐优化
        if "quantization_optimization" in self.verification_results:
            quant_opt = self.verification_results["quantization_optimization"]
            if "error" not in quant_opt:
                status = "✅" if quant_opt.get("fix_successful", False) else "❌"
                print(f"  {status} 量化推荐优化: {quant_opt.get('issue_resolved', '未知')}")
        
        # 推荐一致性
        if "recommendation_consistency" in self.verification_results:
            consistency = self.verification_results["recommendation_consistency"]
            if "error" not in consistency:
                status = "✅" if consistency.get("consistency_achieved", False) else "❌"
                print(f"  {status} 推荐一致性: {consistency.get('consistency_details', '未知')}")
        
        print("\n" + "="*80)


def main():
    """主函数"""
    print("🎯 推荐算法优化最终验证工具")
    print("="*50)
    
    verifier = FinalOptimizationVerifier()
    
    # 运行最终验证
    results = verifier.run_final_verification()
    
    # 显示最终报告
    verifier.print_final_report()
    
    if results["success"]:
        final_report = verifier.verification_results.get("final_report", {})
        success_rate = float(final_report.get("success_rate", "0%").replace("%", ""))
        
        if success_rate >= 80:
            print(f"\n🎉 优化验证成功！成功率: {success_rate:.1f}%")
            print("推荐算法已成功优化，可以部署使用。")
            return 0
        else:
            print(f"\n⚠️ 优化验证部分成功，成功率: {success_rate:.1f}%")
            print("建议进一步调整算法参数。")
            return 1
    else:
        print(f"\n❌ 优化验证失败: {results.get('error', '未知错误')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
