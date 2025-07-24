#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件检测调试和验证工具

提供详细的硬件检测信息和验证功能，帮助排查设备检测问题。
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# 尝试导入相关模块
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False

logger = logging.getLogger(__name__)


class HardwareDebugger:
    """硬件检测调试器"""
    
    def __init__(self):
        """初始化调试器"""
        self.debug_info = {
            "timestamp": time.time(),
            "available_modules": {
                "torch": TORCH_AVAILABLE,
                "gputil": GPUTIL_AVAILABLE,
                "pynvml": PYNVML_AVAILABLE
            },
            "detection_results": {},
            "validation_results": {},
            "recommendations": {}
        }
    
    def run_comprehensive_detection(self) -> Dict[str, Any]:
        """运行全面的硬件检测"""
        logger.info("🔍 开始全面硬件检测...")
        
        # 检测所有可用的GPU检测方法
        self._test_all_gpu_detection_methods()
        
        # 检测内存信息
        self._test_memory_detection()
        
        # 检测CPU信息
        self._test_cpu_detection()
        
        # 验证检测结果一致性
        self._validate_detection_consistency()
        
        # 生成推荐配置
        self._generate_debug_recommendations()
        
        logger.info("✅ 全面硬件检测完成")
        return self.debug_info
    
    def _test_all_gpu_detection_methods(self):
        """测试所有GPU检测方法"""
        logger.info("🔍 测试GPU检测方法...")
        
        gpu_results = {}
        
        # 方法1: PyTorch CUDA
        if TORCH_AVAILABLE:
            gpu_results["pytorch_cuda"] = self._test_pytorch_cuda()
        else:
            gpu_results["pytorch_cuda"] = {"available": False, "error": "PyTorch not installed"}
        
        # 方法2: GPUtil
        if GPUTIL_AVAILABLE:
            gpu_results["gputil"] = self._test_gputil()
        else:
            gpu_results["gputil"] = {"available": False, "error": "GPUtil not installed"}
        
        # 方法3: pynvml
        if PYNVML_AVAILABLE:
            gpu_results["pynvml"] = self._test_pynvml()
        else:
            gpu_results["pynvml"] = {"available": False, "error": "pynvml not installed"}
        
        # 方法4: 系统信息推断
        gpu_results["system_inference"] = self._test_system_inference()
        
        self.debug_info["detection_results"]["gpu"] = gpu_results
    
    def _test_pytorch_cuda(self) -> Dict[str, Any]:
        """测试PyTorch CUDA检测"""
        try:
            result = {
                "available": torch.cuda.is_available(),
                "device_count": 0,
                "devices": [],
                "error": None
            }
            
            if result["available"]:
                result["device_count"] = torch.cuda.device_count()
                for i in range(result["device_count"]):
                    try:
                        device_info = {
                            "id": i,
                            "name": torch.cuda.get_device_name(i),
                            "properties": {}
                        }
                        
                        props = torch.cuda.get_device_properties(i)
                        device_info["properties"] = {
                            "total_memory": props.total_memory,
                            "major": props.major,
                            "minor": props.minor,
                            "multiprocessor_count": props.multiprocessor_count
                        }
                        
                        result["devices"].append(device_info)
                    except Exception as e:
                        result["devices"].append({"id": i, "error": str(e)})
            
            return result
            
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _test_gputil(self) -> Dict[str, Any]:
        """测试GPUtil检测"""
        try:
            gpus = GPUtil.getGPUs()
            result = {
                "available": len(gpus) > 0,
                "device_count": len(gpus),
                "devices": [],
                "error": None
            }
            
            for i, gpu in enumerate(gpus):
                device_info = {
                    "id": i,
                    "name": gpu.name,
                    "memory_total": gpu.memoryTotal,
                    "memory_free": gpu.memoryFree,
                    "memory_used": gpu.memoryUsed,
                    "temperature": gpu.temperature,
                    "load": gpu.load
                }
                result["devices"].append(device_info)
            
            return result
            
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _test_pynvml(self) -> Dict[str, Any]:
        """测试pynvml检测"""
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            result = {
                "available": device_count > 0,
                "device_count": device_count,
                "devices": [],
                "error": None
            }
            
            for i in range(device_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    device_info = {
                        "id": i,
                        "name": name,
                        "memory_total": memory_info.total,
                        "memory_free": memory_info.free,
                        "memory_used": memory_info.used
                    }
                    result["devices"].append(device_info)
                except Exception as e:
                    result["devices"].append({"id": i, "error": str(e)})
            
            return result
            
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def _test_system_inference(self) -> Dict[str, Any]:
        """测试系统信息推断"""
        try:
            import platform
            processor = platform.processor().lower()
            
            result = {
                "processor": processor,
                "inferred_gpu": "none",
                "confidence": "low"
            }
            
            if "intel" in processor:
                result["inferred_gpu"] = "intel_integrated"
                result["confidence"] = "medium"
            elif "amd" in processor:
                result["inferred_gpu"] = "amd_integrated"
                result["confidence"] = "medium"
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _test_memory_detection(self):
        """测试内存检测"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            self.debug_info["detection_results"]["memory"] = {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "percent": memory.percent
            }
        except Exception as e:
            self.debug_info["detection_results"]["memory"] = {"error": str(e)}
    
    def _test_cpu_detection(self):
        """测试CPU检测"""
        try:
            import psutil
            import platform
            
            self.debug_info["detection_results"]["cpu"] = {
                "count": psutil.cpu_count(),
                "freq_current": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "freq_max": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
                "architecture": platform.architecture()[0],
                "processor": platform.processor()
            }
        except Exception as e:
            self.debug_info["detection_results"]["cpu"] = {"error": str(e)}
    
    def _validate_detection_consistency(self):
        """验证检测结果一致性"""
        logger.info("🔍 验证检测结果一致性...")
        
        gpu_results = self.debug_info["detection_results"].get("gpu", {})
        validation = {
            "gpu_count_consistency": True,
            "gpu_memory_consistency": True,
            "issues": []
        }
        
        # 检查GPU数量一致性
        gpu_counts = []
        for method, result in gpu_results.items():
            if result.get("available") and "device_count" in result:
                gpu_counts.append((method, result["device_count"]))
        
        if len(set(count for _, count in gpu_counts)) > 1:
            validation["gpu_count_consistency"] = False
            validation["issues"].append(f"GPU数量不一致: {gpu_counts}")
        
        # 检查GPU内存一致性（如果有多种检测方法都成功）
        gpu_memories = []
        for method, result in gpu_results.items():
            if result.get("available") and result.get("devices"):
                total_memory = 0
                for device in result["devices"]:
                    if "memory_total" in device:
                        total_memory += device["memory_total"]
                    elif "properties" in device and "total_memory" in device["properties"]:
                        total_memory += device["properties"]["total_memory"]
                if total_memory > 0:
                    gpu_memories.append((method, total_memory))
        
        if len(gpu_memories) > 1:
            # 允许10%的误差
            base_memory = gpu_memories[0][1]
            for method, memory in gpu_memories[1:]:
                if abs(memory - base_memory) / base_memory > 0.1:
                    validation["gpu_memory_consistency"] = False
                    validation["issues"].append(f"GPU内存不一致: {gpu_memories}")
                    break
        
        self.debug_info["validation_results"] = validation
    
    def _generate_debug_recommendations(self):
        """生成调试推荐"""
        recommendations = []
        
        gpu_results = self.debug_info["detection_results"].get("gpu", {})
        validation = self.debug_info["validation_results"]
        
        # 检查是否有可用的GPU检测方法
        available_methods = [method for method, result in gpu_results.items() 
                           if result.get("available")]
        
        if not available_methods:
            recommendations.append("❌ 未检测到任何GPU，建议检查驱动安装")
        elif len(available_methods) == 1:
            recommendations.append(f"⚠️ 只有一种GPU检测方法可用: {available_methods[0]}")
        else:
            recommendations.append(f"✅ 多种GPU检测方法可用: {available_methods}")
        
        # 检查一致性问题
        if not validation.get("gpu_count_consistency"):
            recommendations.append("⚠️ GPU数量检测不一致，可能存在驱动问题")
        
        if not validation.get("gpu_memory_consistency"):
            recommendations.append("⚠️ GPU内存检测不一致，建议使用最准确的检测方法")
        
        # 推荐最佳检测方法
        if "gputil" in available_methods:
            recommendations.append("✅ 推荐使用GPUtil进行GPU检测（最准确）")
        elif "pytorch_cuda" in available_methods:
            recommendations.append("✅ 推荐使用PyTorch CUDA进行GPU检测")
        elif "pynvml" in available_methods:
            recommendations.append("✅ 推荐使用pynvml进行GPU检测")
        
        self.debug_info["recommendations"] = recommendations
    
    def save_debug_report(self, output_path: Optional[Path] = None) -> Path:
        """保存调试报告"""
        if output_path is None:
            output_path = Path("logs") / f"hardware_debug_{int(time.time())}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.debug_info, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 调试报告已保存: {output_path}")
        return output_path
    
    def print_summary(self):
        """打印调试摘要"""
        print("\n" + "="*60)
        print("🔍 硬件检测调试摘要")
        print("="*60)
        
        # 可用模块
        print("\n📦 可用模块:")
        for module, available in self.debug_info["available_modules"].items():
            status = "✅" if available else "❌"
            print(f"  {status} {module}")
        
        # GPU检测结果
        print("\n🎮 GPU检测结果:")
        gpu_results = self.debug_info["detection_results"].get("gpu", {})
        for method, result in gpu_results.items():
            if result.get("available"):
                count = result.get("device_count", 0)
                print(f"  ✅ {method}: {count} 个GPU")
            else:
                error = result.get("error", "未知错误")
                print(f"  ❌ {method}: {error}")
        
        # 推荐
        print("\n💡 推荐:")
        for rec in self.debug_info.get("recommendations", []):
            print(f"  {rec}")
        
        print("\n" + "="*60)


def run_hardware_debug() -> Dict[str, Any]:
    """运行硬件调试（便捷函数）"""
    debugger = HardwareDebugger()
    results = debugger.run_comprehensive_detection()
    debugger.print_summary()
    debugger.save_debug_report()
    return results


if __name__ == "__main__":
    # 直接运行调试
    run_hardware_debug()
