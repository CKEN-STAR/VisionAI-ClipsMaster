#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU检测详细测试脚本

专门测试GPU检测功能的准确性和不同硬件配置下的推荐效果
"""

import logging
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPUDetectionTester:
    """GPU检测测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.test_results = {}
    
    def run_comprehensive_gpu_tests(self) -> Dict[str, Any]:
        """运行全面的GPU检测测试"""
        logger.info("🔍 开始全面GPU检测测试...")
        
        try:
            # 1. 测试所有GPU检测方法
            self._test_all_detection_methods()
            
            # 2. 测试硬件检测器
            self._test_hardware_detector()
            
            # 3. 测试智能推荐器
            self._test_intelligent_recommender()
            
            # 4. 模拟不同GPU配置
            self._test_simulated_gpu_configs()
            
            # 5. 验证推荐逻辑
            self._validate_recommendation_logic()
            
            logger.info("✅ 所有GPU检测测试完成")
            return {
                "success": True,
                "test_results": self.test_results
            }
            
        except Exception as e:
            logger.error(f"❌ GPU检测测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_results": self.test_results
            }
    
    def _test_all_detection_methods(self):
        """测试所有GPU检测方法"""
        logger.info("🔍 测试所有GPU检测方法...")
        
        detection_results = {}
        
        # 方法1: PyTorch CUDA
        try:
            import torch
            if hasattr(torch, 'cuda'):
                cuda_available = torch.cuda.is_available()
                device_count = torch.cuda.device_count() if cuda_available else 0
                
                devices = []
                if cuda_available:
                    for i in range(device_count):
                        try:
                            name = torch.cuda.get_device_name(i)
                            props = torch.cuda.get_device_properties(i)
                            devices.append({
                                "id": i,
                                "name": name,
                                "memory_gb": props.total_memory / (1024**3),
                                "compute_capability": f"{props.major}.{props.minor}"
                            })
                        except Exception as e:
                            devices.append({"id": i, "error": str(e)})
                
                detection_results["pytorch_cuda"] = {
                    "available": cuda_available,
                    "device_count": device_count,
                    "devices": devices
                }
            else:
                detection_results["pytorch_cuda"] = {"available": False, "error": "CUDA not available"}
        except Exception as e:
            detection_results["pytorch_cuda"] = {"available": False, "error": str(e)}
        
        # 方法2: GPUtil
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            
            devices = []
            for i, gpu in enumerate(gpus):
                devices.append({
                    "id": i,
                    "name": gpu.name,
                    "memory_total_gb": gpu.memoryTotal / 1024,
                    "memory_free_gb": gpu.memoryFree / 1024,
                    "memory_used_gb": gpu.memoryUsed / 1024,
                    "temperature": gpu.temperature,
                    "load": gpu.load
                })
            
            detection_results["gputil"] = {
                "available": len(gpus) > 0,
                "device_count": len(gpus),
                "devices": devices
            }
        except Exception as e:
            detection_results["gputil"] = {"available": False, "error": str(e)}
        
        # 方法3: pynvml
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            devices = []
            for i in range(device_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    devices.append({
                        "id": i,
                        "name": name,
                        "memory_total_gb": memory_info.total / (1024**3),
                        "memory_free_gb": memory_info.free / (1024**3),
                        "memory_used_gb": memory_info.used / (1024**3)
                    })
                except Exception as e:
                    devices.append({"id": i, "error": str(e)})
            
            detection_results["pynvml"] = {
                "available": device_count > 0,
                "device_count": device_count,
                "devices": devices
            }
        except Exception as e:
            detection_results["pynvml"] = {"available": False, "error": str(e)}
        
        self.test_results["detection_methods"] = detection_results
        
        # 分析检测结果
        available_methods = [method for method, result in detection_results.items() if result.get("available")]
        logger.info(f"可用的GPU检测方法: {available_methods}")
        
        if available_methods:
            # 比较不同方法的结果
            self._compare_detection_methods(detection_results)
        else:
            logger.info("❌ 未检测到任何GPU设备")
    
    def _compare_detection_methods(self, detection_results: Dict[str, Any]):
        """比较不同检测方法的结果"""
        logger.info("🔍 比较不同检测方法的结果...")
        
        comparison = {
            "device_counts": {},
            "memory_info": {},
            "consistency_check": {}
        }
        
        # 收集设备数量
        for method, result in detection_results.items():
            if result.get("available"):
                comparison["device_counts"][method] = result.get("device_count", 0)
        
        # 收集内存信息
        for method, result in detection_results.items():
            if result.get("available") and result.get("devices"):
                total_memory = 0
                for device in result["devices"]:
                    if "memory_gb" in device:
                        total_memory += device["memory_gb"]
                    elif "memory_total_gb" in device:
                        total_memory += device["memory_total_gb"]
                comparison["memory_info"][method] = total_memory
        
        # 一致性检查
        device_counts = list(comparison["device_counts"].values())
        memory_values = list(comparison["memory_info"].values())
        
        comparison["consistency_check"] = {
            "device_count_consistent": len(set(device_counts)) <= 1,
            "memory_info_consistent": len(memory_values) <= 1 or (
                max(memory_values) - min(memory_values) <= max(memory_values) * 0.1
            ) if memory_values else True
        }
        
        self.test_results["method_comparison"] = comparison
        logger.info(f"检测方法比较结果: {comparison}")
    
    def _test_hardware_detector(self):
        """测试硬件检测器"""
        logger.info("🔍 测试硬件检测器...")
        
        try:
            from src.core.hardware_detector import HardwareDetector
            
            detector = HardwareDetector()
            hardware_info = detector.detect_hardware()
            
            hardware_result = {
                "gpu_type": str(hardware_info.gpu_type) if hasattr(hardware_info, 'gpu_type') else "unknown",
                "gpu_count": getattr(hardware_info, 'gpu_count', 0),
                "gpu_memory_gb": getattr(hardware_info, 'gpu_memory_gb', 0),
                "gpu_names": getattr(hardware_info, 'gpu_names', []),
                "system_ram_gb": getattr(hardware_info, 'total_memory_gb', 0),
                "performance_level": str(hardware_info.performance_level) if hasattr(hardware_info, 'performance_level') else "unknown",
                "recommended_quantization": getattr(hardware_info, 'recommended_quantization', 'unknown'),
                "gpu_acceleration": getattr(hardware_info, 'gpu_acceleration', False)
            }
            
            self.test_results["hardware_detector"] = hardware_result
            logger.info(f"硬件检测器结果: {hardware_result}")
            
        except Exception as e:
            logger.error(f"硬件检测器测试失败: {e}")
            self.test_results["hardware_detector"] = {"error": str(e)}
    
    def _test_intelligent_recommender(self):
        """测试智能推荐器"""
        logger.info("🔍 测试智能推荐器...")
        
        try:
            from src.core.intelligent_model_selector import IntelligentModelSelector
            
            selector = IntelligentModelSelector()
            selector.force_refresh_hardware()
            
            # 测试中文模型推荐
            zh_recommendation = selector.recommend_model_version("qwen2.5-7b")
            
            # 测试英文模型推荐
            en_recommendation = selector.recommend_model_version("mistral-7b")
            
            recommender_result = {
                "zh_model": {
                    "model_name": zh_recommendation.model_name if zh_recommendation else None,
                    "variant_name": zh_recommendation.variant.name if zh_recommendation and zh_recommendation.variant else None,
                    "quantization": zh_recommendation.variant.quantization.value if zh_recommendation and zh_recommendation.variant else None,
                    "size_gb": zh_recommendation.variant.size_gb if zh_recommendation and zh_recommendation.variant else None,
                    "quality_retention": zh_recommendation.variant.quality_retention if zh_recommendation and zh_recommendation.variant else None,
                    "reasoning": zh_recommendation.reasoning if zh_recommendation else None
                },
                "en_model": {
                    "model_name": en_recommendation.model_name if en_recommendation else None,
                    "variant_name": en_recommendation.variant.name if en_recommendation and en_recommendation.variant else None,
                    "quantization": en_recommendation.variant.quantization.value if en_recommendation and en_recommendation.variant else None,
                    "size_gb": en_recommendation.variant.size_gb if en_recommendation and en_recommendation.variant else None,
                    "quality_retention": en_recommendation.variant.quality_retention if en_recommendation and en_recommendation.variant else None,
                    "reasoning": en_recommendation.reasoning if en_recommendation else None
                }
            }
            
            self.test_results["intelligent_recommender"] = recommender_result
            logger.info(f"智能推荐器结果: 中文模型={recommender_result['zh_model']['quantization']}, 英文模型={recommender_result['en_model']['quantization']}")
            
        except Exception as e:
            logger.error(f"智能推荐器测试失败: {e}")
            self.test_results["intelligent_recommender"] = {"error": str(e)}
    
    def _test_simulated_gpu_configs(self):
        """测试模拟GPU配置"""
        logger.info("🔍 测试模拟GPU配置...")
        
        gpu_configs = [
            {"name": "RTX 4090", "memory_gb": 24, "expected_quant": "Q8_0"},
            {"name": "RTX 4080", "memory_gb": 16, "expected_quant": "Q8_0"},
            {"name": "RTX 4070", "memory_gb": 12, "expected_quant": "Q5_K"},
            {"name": "RTX 4060", "memory_gb": 8, "expected_quant": "Q5_K"},
            {"name": "GTX 1660", "memory_gb": 6, "expected_quant": "Q4_K_M"},
            {"name": "集成显卡", "memory_gb": 2, "expected_quant": "Q4_K_M"},
            {"name": "无GPU", "memory_gb": 0, "expected_quant": "Q2_K"}
        ]
        
        simulation_results = {}
        
        for config in gpu_configs:
            # 模拟推荐逻辑
            memory_gb = config["memory_gb"]
            
            if memory_gb >= 16:
                recommended_quant = "Q8_0"
                performance_level = "ultra"
            elif memory_gb >= 8:
                recommended_quant = "Q5_K"
                performance_level = "high"
            elif memory_gb >= 4:
                recommended_quant = "Q4_K_M"
                performance_level = "medium"
            else:
                recommended_quant = "Q2_K"
                performance_level = "low"
            
            simulation_results[config["name"]] = {
                "memory_gb": memory_gb,
                "recommended_quantization": recommended_quant,
                "expected_quantization": config["expected_quant"],
                "performance_level": performance_level,
                "match": recommended_quant == config["expected_quant"]
            }
        
        self.test_results["simulated_configs"] = simulation_results
        
        # 统计匹配率
        total_configs = len(simulation_results)
        matched_configs = sum(1 for result in simulation_results.values() if result["match"])
        match_rate = (matched_configs / total_configs * 100) if total_configs > 0 else 0
        
        logger.info(f"模拟配置测试: {matched_configs}/{total_configs} 匹配 ({match_rate:.1f}%)")
    
    def _validate_recommendation_logic(self):
        """验证推荐逻辑"""
        logger.info("🔍 验证推荐逻辑...")
        
        validation_results = {
            "gpu_detection_working": False,
            "performance_scaling": False,
            "quantization_appropriate": False,
            "gpu_acceleration_considered": False,
            "issues": []
        }
        
        # 检查GPU检测是否工作
        detection_methods = self.test_results.get("detection_methods", {})
        available_methods = [method for method, result in detection_methods.items() if result.get("available")]
        
        if available_methods:
            validation_results["gpu_detection_working"] = True
        else:
            validation_results["issues"].append("GPU检测未工作")
        
        # 检查性能等级是否合理
        hardware_detector = self.test_results.get("hardware_detector", {})
        gpu_memory = hardware_detector.get("gpu_memory_gb", 0)
        performance_level = hardware_detector.get("performance_level", "").lower()
        
        if gpu_memory > 0:
            if gpu_memory >= 8 and performance_level in ["high", "ultra"]:
                validation_results["performance_scaling"] = True
            elif gpu_memory < 8 and performance_level in ["medium", "low"]:
                validation_results["performance_scaling"] = True
            else:
                validation_results["issues"].append(f"性能等级不匹配GPU配置: {gpu_memory}GB -> {performance_level}")
        else:
            if performance_level in ["low", "medium"]:
                validation_results["performance_scaling"] = True
        
        # 检查量化等级是否合适
        recommender = self.test_results.get("intelligent_recommender", {})
        zh_quant = recommender.get("zh_model", {}).get("quantization", "").upper()
        
        if gpu_memory >= 16 and zh_quant in ["Q8_0", "Q5_K"]:
            validation_results["quantization_appropriate"] = True
        elif gpu_memory >= 8 and zh_quant in ["Q5_K", "Q4_K_M"]:
            validation_results["quantization_appropriate"] = True
        elif gpu_memory < 8 and zh_quant in ["Q4_K_M", "Q2_K"]:
            validation_results["quantization_appropriate"] = True
        else:
            validation_results["issues"].append(f"量化等级不适合GPU配置: {gpu_memory}GB -> {zh_quant}")
        
        # 检查是否考虑了GPU加速
        gpu_acceleration = hardware_detector.get("gpu_acceleration", False)
        if gpu_memory > 0:
            validation_results["gpu_acceleration_considered"] = gpu_acceleration
            if not gpu_acceleration:
                validation_results["issues"].append("有GPU但未启用GPU加速")
        else:
            validation_results["gpu_acceleration_considered"] = not gpu_acceleration
        
        self.test_results["validation"] = validation_results
        
        # 输出验证结果
        passed_checks = sum(1 for key, value in validation_results.items() 
                          if key != "issues" and value)
        total_checks = 4
        
        logger.info(f"推荐逻辑验证: {passed_checks}/{total_checks} 项通过")
        
        if validation_results["issues"]:
            logger.warning(f"发现问题: {validation_results['issues']}")
    
    def print_detailed_report(self):
        """打印详细报告"""
        print("\n" + "="*80)
        print("🔍 GPU检测详细测试报告")
        print("="*80)
        
        # GPU检测方法结果
        if "detection_methods" in self.test_results:
            print(f"\n🎮 GPU检测方法结果:")
            detection_methods = self.test_results["detection_methods"]
            
            for method, result in detection_methods.items():
                if result.get("available"):
                    device_count = result.get("device_count", 0)
                    print(f"  ✅ {method}: {device_count} 个GPU")
                    
                    if result.get("devices"):
                        for device in result["devices"]:
                            if "error" not in device:
                                name = device.get("name", "Unknown")
                                memory = device.get("memory_gb") or device.get("memory_total_gb", 0)
                                print(f"    • {name}: {memory:.1f}GB")
                else:
                    error = result.get("error", "未知错误")
                    print(f"  ❌ {method}: {error}")
        
        # 硬件检测器结果
        if "hardware_detector" in self.test_results:
            print(f"\n🖥️ 硬件检测器结果:")
            hw = self.test_results["hardware_detector"]
            
            if "error" not in hw:
                print(f"  GPU类型: {hw.get('gpu_type', 'unknown')}")
                print(f"  GPU数量: {hw.get('gpu_count', 0)}")
                print(f"  GPU显存: {hw.get('gpu_memory_gb', 0):.1f}GB")
                print(f"  系统内存: {hw.get('system_ram_gb', 0):.1f}GB")
                print(f"  性能等级: {hw.get('performance_level', 'unknown')}")
                print(f"  推荐量化: {hw.get('recommended_quantization', 'unknown')}")
                print(f"  GPU加速: {hw.get('gpu_acceleration', False)}")
            else:
                print(f"  ❌ 错误: {hw['error']}")
        
        # 智能推荐结果
        if "intelligent_recommender" in self.test_results:
            print(f"\n🤖 智能推荐结果:")
            rec = self.test_results["intelligent_recommender"]
            
            if "error" not in rec:
                zh_model = rec.get("zh_model", {})
                en_model = rec.get("en_model", {})
                
                print(f"  中文模型:")
                print(f"    量化等级: {zh_model.get('quantization', 'unknown')}")
                print(f"    模型大小: {zh_model.get('size_gb', 0):.1f}GB")
                print(f"    质量保持: {zh_model.get('quality_retention', 0):.1%}")
                
                print(f"  英文模型:")
                print(f"    量化等级: {en_model.get('quantization', 'unknown')}")
                print(f"    模型大小: {en_model.get('size_gb', 0):.1f}GB")
                print(f"    质量保持: {en_model.get('quality_retention', 0):.1%}")
            else:
                print(f"  ❌ 错误: {rec['error']}")
        
        # 验证结果
        if "validation" in self.test_results:
            print(f"\n✅ 验证结果:")
            validation = self.test_results["validation"]
            
            checks = [
                ("GPU检测工作", validation.get("gpu_detection_working", False)),
                ("性能等级合理", validation.get("performance_scaling", False)),
                ("量化等级适当", validation.get("quantization_appropriate", False)),
                ("GPU加速考虑", validation.get("gpu_acceleration_considered", False))
            ]
            
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
            
            if validation.get("issues"):
                print(f"\n⚠️ 发现的问题:")
                for issue in validation["issues"]:
                    print(f"  • {issue}")
        
        print("\n" + "="*80)
    
    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """保存测试报告"""
        if output_path is None:
            output_path = Path("logs") / f"gpu_detection_test_{int(time.time())}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 测试报告已保存: {output_path}")
        return output_path


def main():
    """主函数"""
    print("🔍 GPU检测详细测试工具")
    print("="*50)
    
    tester = GPUDetectionTester()
    
    # 运行测试
    results = tester.run_comprehensive_gpu_tests()
    
    # 显示详细报告
    tester.print_detailed_report()
    
    # 保存报告
    report_path = tester.save_report()
    
    if results["success"]:
        print(f"\n✅ 测试完成！报告已保存至: {report_path}")
        return 0
    else:
        print(f"\n❌ 测试过程中出现错误: {results.get('error', '未知错误')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
