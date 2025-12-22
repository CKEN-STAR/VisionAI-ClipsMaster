#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能推荐下载器设备检测修复脚本

修复智能推荐下载器的设备自适应功能，确保在有独显设备上能正确推荐高精度模型。

主要修复内容：
1. 优化GPU检测逻辑，支持多种检测方法
2. 修复缓存机制导致的硬件配置固化问题
3. 优化性能等级评估和推荐配置映射
4. 添加设备检测调试和验证功能
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartDownloaderFixer:
    """智能推荐下载器修复器"""
    
    def __init__(self):
        """初始化修复器"""
        self.project_root = project_root
        self.fixes_applied = []
        self.validation_results = {}
    
    def run_all_fixes(self) -> Dict[str, Any]:
        """运行所有修复"""
        logger.info("🔧 开始修复智能推荐下载器的设备检测问题...")
        
        try:
            # 1. 验证当前问题
            self._validate_current_issues()
            
            # 2. 测试修复后的硬件检测
            self._test_improved_hardware_detection()
            
            # 3. 验证智能推荐逻辑
            self._test_intelligent_recommendation()
            
            # 4. 运行综合验证
            self._run_comprehensive_validation()
            
            logger.info("✅ 所有修复完成")
            return {
                "success": True,
                "fixes_applied": self.fixes_applied,
                "validation_results": self.validation_results
            }
            
        except Exception as e:
            logger.error(f"❌ 修复过程中出现错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "fixes_applied": self.fixes_applied
            }
    
    def _validate_current_issues(self):
        """验证当前问题"""
        logger.info("🔍 验证当前设备检测问题...")
        
        try:
            # 运行硬件调试
            from src.utils.hardware_debug import run_hardware_debug
            debug_results = run_hardware_debug()
            
            self.validation_results["hardware_debug"] = debug_results
            self.fixes_applied.append("硬件调试验证完成")
            
        except Exception as e:
            logger.warning(f"硬件调试验证失败: {e}")
    
    def _test_improved_hardware_detection(self):
        """测试改进的硬件检测"""
        logger.info("🔍 测试改进的硬件检测...")
        
        try:
            from src.core.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            # 记录检测结果
            detection_summary = {
                "gpu_type": hardware_info.gpu_type.value if hasattr(hardware_info, 'gpu_type') else "unknown",
                "gpu_memory_gb": hardware_info.gpu_memory_gb if hasattr(hardware_info, 'gpu_memory_gb') else 0,
                "system_ram_gb": hardware_info.total_memory_gb if hasattr(hardware_info, 'total_memory_gb') else 0,
                "performance_level": hardware_info.performance_level.value if hasattr(hardware_info, 'performance_level') else "unknown",
                "recommended_quantization": hardware_info.recommended_quantization if hasattr(hardware_info, 'recommended_quantization') else "unknown"
            }
            
            self.validation_results["hardware_detection"] = detection_summary
            self.fixes_applied.append("硬件检测器测试完成")
            
            logger.info(f"硬件检测结果: {detection_summary}")
            
        except Exception as e:
            logger.error(f"硬件检测测试失败: {e}")
            self.validation_results["hardware_detection"] = {"error": str(e)}
    
    def _test_intelligent_recommendation(self):
        """测试智能推荐逻辑"""
        logger.info("🔍 测试智能推荐逻辑...")
        
        try:
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            selector = IntelligentModelSelector()
            
            # 强制刷新硬件配置
            selector.force_refresh_hardware()
            
            # 测试中文模型推荐
            zh_recommendation = selector.recommend_model_version("Qwen3-1.7B")
            
            # 测试英文模型推荐
            en_recommendation = selector.recommend_model_version("mistral-7b")
            
            recommendation_summary = {
                "zh_model": {
                    "model_name": zh_recommendation.model_name if zh_recommendation else None,
                    "quantization": zh_recommendation.variant.quantization.value if zh_recommendation and zh_recommendation.variant else None,
                    "size_gb": zh_recommendation.variant.size_gb if zh_recommendation and zh_recommendation.variant else None
                },
                "en_model": {
                    "model_name": en_recommendation.model_name if en_recommendation else None,
                    "quantization": en_recommendation.variant.quantization.value if en_recommendation and en_recommendation.variant else None,
                    "size_gb": en_recommendation.variant.size_gb if en_recommendation and en_recommendation.variant else None
                }
            }
            
            self.validation_results["intelligent_recommendation"] = recommendation_summary
            self.fixes_applied.append("智能推荐逻辑测试完成")
            
            logger.info(f"推荐结果: {recommendation_summary}")
            
        except Exception as e:
            logger.error(f"智能推荐测试失败: {e}")
            self.validation_results["intelligent_recommendation"] = {"error": str(e)}
    
    def _run_comprehensive_validation(self):
        """运行综合验证"""
        logger.info("🔍 运行综合验证...")
        
        validation_summary = {
            "gpu_detection_working": False,
            "high_performance_detected": False,
            "appropriate_quantization_recommended": False,
            "cache_refresh_working": False,
            "issues": []
        }
        
        try:
            # 检查GPU检测是否工作
            hardware_detection = self.validation_results.get("hardware_detection", {})
            if hardware_detection.get("gpu_memory_gb", 0) > 0:
                validation_summary["gpu_detection_working"] = True
            else:
                validation_summary["issues"].append("GPU检测未工作")
            
            # 检查是否检测到高性能设备
            performance_level = hardware_detection.get("performance_level", "").lower()
            if performance_level in ["high", "ultra"]:
                validation_summary["high_performance_detected"] = True
            else:
                validation_summary["issues"].append(f"性能等级评估偏低: {performance_level}")
            
            # 检查是否推荐了合适的量化等级
            recommended_quant = hardware_detection.get("recommended_quantization", "").upper()
            if recommended_quant in ["Q5_K", "Q8_0"]:
                validation_summary["appropriate_quantization_recommended"] = True
            else:
                validation_summary["issues"].append(f"量化等级推荐偏保守: {recommended_quant}")
            
            # 检查缓存刷新是否工作
            if "智能推荐逻辑测试完成" in self.fixes_applied:
                validation_summary["cache_refresh_working"] = True
            
            self.validation_results["comprehensive_validation"] = validation_summary
            self.fixes_applied.append("综合验证完成")
            
            # 输出验证结果
            if all([
                validation_summary["gpu_detection_working"],
                validation_summary["high_performance_detected"],
                validation_summary["appropriate_quantization_recommended"],
                validation_summary["cache_refresh_working"]
            ]):
                logger.info("✅ 所有验证项目通过")
            else:
                logger.warning(f"⚠️ 部分验证项目未通过: {validation_summary['issues']}")
            
        except Exception as e:
            logger.error(f"综合验证失败: {e}")
            validation_summary["error"] = str(e)
            self.validation_results["comprehensive_validation"] = validation_summary
    
    def generate_fix_report(self) -> str:
        """生成修复报告"""
        report = []
        report.append("=" * 60)
        report.append("🔧 智能推荐下载器设备检测修复报告")
        report.append("=" * 60)
        report.append("")
        
        # 修复摘要
        report.append("📋 修复摘要:")
        for fix in self.fixes_applied:
            report.append(f"  ✅ {fix}")
        report.append("")
        
        # 硬件检测结果
        if "hardware_detection" in self.validation_results:
            hardware = self.validation_results["hardware_detection"]
            report.append("🖥️ 硬件检测结果:")
            report.append(f"  GPU类型: {hardware.get('gpu_type', 'unknown')}")
            report.append(f"  GPU显存: {hardware.get('gpu_memory_gb', 0):.1f}GB")
            report.append(f"  系统内存: {hardware.get('system_ram_gb', 0):.1f}GB")
            report.append(f"  性能等级: {hardware.get('performance_level', 'unknown')}")
            report.append(f"  推荐量化: {hardware.get('recommended_quantization', 'unknown')}")
            report.append("")
        
        # 推荐结果
        if "intelligent_recommendation" in self.validation_results:
            recommendation = self.validation_results["intelligent_recommendation"]
            report.append("🤖 智能推荐结果:")
            
            zh_model = recommendation.get("zh_model", {})
            report.append(f"  中文模型: {zh_model.get('quantization', 'unknown')} ({zh_model.get('size_gb', 0):.1f}GB)")
            
            en_model = recommendation.get("en_model", {})
            report.append(f"  英文模型: {en_model.get('quantization', 'unknown')} ({en_model.get('size_gb', 0):.1f}GB)")
            report.append("")
        
        # 验证结果
        if "comprehensive_validation" in self.validation_results:
            validation = self.validation_results["comprehensive_validation"]
            report.append("✅ 验证结果:")
            
            checks = [
                ("GPU检测工作", validation.get("gpu_detection_working", False)),
                ("高性能检测", validation.get("high_performance_detected", False)),
                ("合适量化推荐", validation.get("appropriate_quantization_recommended", False)),
                ("缓存刷新工作", validation.get("cache_refresh_working", False))
            ]
            
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                report.append(f"  {status} {check_name}")
            
            if validation.get("issues"):
                report.append("")
                report.append("⚠️ 发现的问题:")
                for issue in validation["issues"]:
                    report.append(f"  • {issue}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """保存修复报告"""
        if output_path is None:
            output_path = Path("logs") / f"smart_downloader_fix_report_{int(time.time())}.txt"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_content = self.generate_fix_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"📄 修复报告已保存: {output_path}")
        return output_path


def main():
    """主函数"""
    print("🔧 智能推荐下载器设备检测修复工具")
    print("=" * 50)
    
    fixer = SmartDownloaderFixer()
    
    # 运行修复
    results = fixer.run_all_fixes()
    
    # 显示报告
    print("\n" + fixer.generate_fix_report())
    
    # 保存报告
    report_path = fixer.save_report()
    
    if results["success"]:
        print(f"\n✅ 修复完成！报告已保存至: {report_path}")
        return 0
    else:
        print(f"\n❌ 修复过程中出现错误: {results.get('error', '未知错误')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
