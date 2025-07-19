#!/usr/bin/env python
"""设备兼容性测试工具

此模块提供设备兼容性矩阵测试功能，用于验证应用在不同设备环境下的兼容性。
"""

import os
import sys
import yaml
import json
import platform
import logging
import argparse
import psutil
import time
from typing import Dict, List, Any, Tuple, Optional
import subprocess
from pathlib import Path
import tempfile
import shutil

# 确保项目根目录在导入路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("device_compat")


class DeviceInfo:
    """设备信息类，用于收集和提供当前设备的硬件和软件信息"""
    
    def __init__(self):
        """初始化设备信息"""
        self.os_name = platform.system()
        self.os_version = platform.version()
        self.os_release = platform.release()
        
        self.cpu_info = self._get_cpu_info()
        self.ram_info = self._get_ram_info()
        self.gpu_info = self._get_gpu_info()
        
        self.features = self._detect_features()
    
    def _get_cpu_info(self) -> Dict[str, Any]:
        """获取CPU信息
        
        Returns:
            Dict: CPU信息字典
        """
        info = {
            "name": platform.processor(),
            "architecture": platform.machine(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "features": []
        }
        
        # 尝试获取更详细的CPU信息
        if self.os_name == "Windows":
            try:
                # 使用wmic获取CPU信息
                output = subprocess.check_output("wmic cpu get name", shell=True).decode()
                lines = output.strip().split('\n')
                if len(lines) > 1:
                    info["name"] = lines[1].strip()
            except Exception as e:
                logger.warning(f"获取详细CPU信息失败: {e}")
        
        elif self.os_name == "Darwin":  # macOS
            try:
                # 使用sysctl获取CPU信息
                output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode()
                info["name"] = output.strip()
                
                # 检查是否为Apple Silicon
                output = subprocess.check_output(["sysctl", "-n", "hw.optional.arm64"]).decode()
                if output.strip() == "1":
                    info["architecture"] = "arm64"
                    info["features"].append("Apple Silicon")
            except Exception as e:
                logger.warning(f"获取详细CPU信息失败: {e}")
        
        elif self.os_name == "Linux":
            try:
                # 从/proc/cpuinfo获取CPU信息
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                
                for line in cpuinfo.split("\n"):
                    if "model name" in line:
                        info["name"] = line.split(":")[1].strip()
                        break
            except Exception as e:
                logger.warning(f"获取详细CPU信息失败: {e}")
        
        return info
    
    def _get_ram_info(self) -> Dict[str, Any]:
        """获取内存信息
        
        Returns:
            Dict: 内存信息字典
        """
        memory = psutil.virtual_memory()
        
        return {
            "total_mb": memory.total / (1024 * 1024),
            "available_mb": memory.available / (1024 * 1024),
            "used_mb": memory.used / (1024 * 1024),
            "percent": memory.percent
        }
    
    def _get_gpu_info(self) -> List[Dict[str, Any]]:
        """获取GPU信息
        
        Returns:
            List[Dict]: GPU信息列表
        """
        gpus = []
        
        # 尝试获取NVIDIA GPU信息
        try:
            # 尝试导入pynvml
            import pynvml
            pynvml.nvmlInit()
            
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                name = pynvml.nvmlDeviceGetName(handle)
                
                gpus.append({
                    "index": i,
                    "name": name,
                    "type": "NVIDIA",
                    "total_memory_mb": info.total / (1024 * 1024),
                    "free_memory_mb": info.free / (1024 * 1024),
                    "used_memory_mb": info.used / (1024 * 1024)
                })
            
            pynvml.nvmlShutdown()
        except (ImportError, Exception) as e:
            logger.debug(f"获取NVIDIA GPU信息失败: {e}")
        
        # 如果没有找到NVIDIA GPU，尝试通过其他方式获取GPU信息
        if not gpus:
            if self.os_name == "Windows":
                try:
                    # 使用wmic获取显卡信息
                    output = subprocess.check_output("wmic path win32_VideoController get name, AdapterRAM", shell=True).decode()
                    lines = output.strip().split('\n')
                    
                    if len(lines) > 1:
                        for i, line in enumerate(lines[1:]):
                            parts = line.split()
                            if not parts:
                                continue
                            
                            # 解析显卡名称和内存
                            ram_parts = []
                            name_parts = []
                            for part in parts:
                                if part.isdigit():
                                    ram_parts.append(part)
                                else:
                                    name_parts.append(part)
                            
                            name = " ".join(name_parts).strip()
                            ram = int("".join(ram_parts)) if ram_parts else 0
                            
                            gpu_type = "Intel" if "Intel" in name else "AMD" if "AMD" in name or "Radeon" in name else "Unknown"
                            
                            gpus.append({
                                "index": i,
                                "name": name,
                                "type": gpu_type,
                                "total_memory_mb": ram / (1024 * 1024) if ram else "Unknown"
                            })
                except Exception as e:
                    logger.warning(f"获取Windows GPU信息失败: {e}")
            
            elif self.os_name == "Darwin":  # macOS
                try:
                    # 使用system_profiler获取GPU信息
                    output = subprocess.check_output(["system_profiler", "SPDisplaysDataType"]).decode()
                    
                    # 简单解析输出
                    chip_model = ""
                    for line in output.split('\n'):
                        if "Chipset Model" in line:
                            chip_model = line.split(":")[1].strip()
                            break
                    
                    if chip_model:
                        gpu_type = "Apple" if "Apple" in chip_model else "Intel" if "Intel" in chip_model else "AMD" if "AMD" in chip_model else "Unknown"
                        
                        gpus.append({
                            "index": 0,
                            "name": chip_model,
                            "type": gpu_type,
                            "total_memory_mb": "Shared with system"
                        })
                except Exception as e:
                    logger.warning(f"获取macOS GPU信息失败: {e}")
            
            elif self.os_name == "Linux":
                try:
                    # 使用lspci获取GPU信息
                    output = subprocess.check_output("lspci | grep -i vga", shell=True).decode()
                    
                    for i, line in enumerate(output.split('\n')):
                        if not line.strip():
                            continue
                        
                        gpu_type = "Intel" if "Intel" in line else "AMD" if "AMD" in line or "Radeon" in line else "Unknown"
                        
                        gpus.append({
                            "index": i,
                            "name": line.split(":")[-1].strip(),
                            "type": gpu_type,
                            "total_memory_mb": "Unknown"
                        })
                except Exception as e:
                    logger.warning(f"获取Linux GPU信息失败: {e}")
        
        return gpus
    
    def _detect_features(self) -> Dict[str, bool]:
        """检测设备支持的特性
        
        Returns:
            Dict: 特性支持情况字典
        """
        features = {
            "avx2": False,
            "avx512": False,
            "ane": False,  # Apple Neural Engine
            "amx": False,  # Apple Matrix Extensions
            "cuda": False,
            "rocm": False,
            "opengl": False,
            "vulkan": False
        }
        
        # 检测AVX指令集支持
        if self.os_name in ["Windows", "Linux"]:
            try:
                import cpuinfo
                info = cpuinfo.get_cpu_info()
                if "flags" in info:
                    features["avx2"] = "avx2" in info["flags"]
                    features["avx512"] = any(flag.startswith("avx512") for flag in info["flags"])
            except ImportError:
                logger.debug("无法导入cpuinfo模块，无法检测AVX指令集")
        
        # 检测Apple特性
        if self.os_name == "Darwin" and platform.machine() == "arm64":
            features["ane"] = True  # Apple Silicon都有Neural Engine
            features["amx"] = True  # M系列芯片都支持AMX
        
        # 检测CUDA支持
        try:
            # 尝试导入pycuda
            import pycuda.driver as cuda
            cuda.init()
            features["cuda"] = True
        except (ImportError, Exception):
            # 如果有NVIDIA GPU，假设有CUDA支持
            features["cuda"] = any(gpu["type"] == "NVIDIA" for gpu in self.gpu_info)
        
        # 检测ROCm支持（AMD GPU加速）
        if self.os_name == "Linux":
            try:
                output = subprocess.check_output("rocminfo", shell=True).decode()
                features["rocm"] = "GPU Agent" in output
            except Exception:
                # 如果有AMD GPU，在Linux上假设有ROCm支持的可能
                features["rocm"] = any(gpu["type"] == "AMD" for gpu in self.gpu_info)
        
        return features
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示
        
        Returns:
            Dict: 设备信息字典
        """
        return {
            "os": {
                "name": self.os_name,
                "version": self.os_version,
                "release": self.os_release,
                "full": f"{self.os_name} {self.os_release} {self.os_version}"
            },
            "cpu": self.cpu_info,
            "ram": self.ram_info,
            "gpu": self.gpu_info,
            "features": self.features
        }
    
    def get_compatibility_profile(self) -> Dict[str, Any]:
        """获取兼容性配置文件
        
        Returns:
            Dict: 兼容性配置
        """
        # 确定OS类型
        if self.os_name == "Windows":
            os_type = "Windows"
        elif self.os_name == "Darwin":
            os_type = "macOS"
        elif self.os_name == "Linux":
            os_type = "Ubuntu"  # 假设Linux是Ubuntu
        else:
            os_type = "Unknown"
        
        # 确定GPU类型
        gpu_type = "None"
        if self.gpu_info:
            gpu_type = self.gpu_info[0]["type"]
        
        # 计算可用内存
        memory_mb = self.ram_info["total_mb"]
        
        # 确定合适的量化级别
        quant_level = "Q4_K_M"  # 默认最低级别
        
        if memory_mb >= 16384:  # 16GB或更高
            if any(gpu["type"] == "NVIDIA" for gpu in self.gpu_info):
                quant_level = "F16"  # 有NVIDIA GPU，使用全精度
            else:
                quant_level = "Q8_0"  # 没有GPU，使用8-bit量化
        elif memory_mb >= 8192:  # 8GB-16GB
            if self.os_name == "Darwin" and platform.machine() == "arm64":
                quant_level = "Q6_K"  # Apple Silicon使用6-bit量化
            else:
                quant_level = "Q5_K_M"  # 其他设备使用5-bit量化
        
        # 构建兼容性配置
        return {
            "device": self._get_device_name(),
            "os": os_type,
            "quant_level": quant_level,
            "memory_limit": int(memory_mb),
            "gpu": bool(self.gpu_info),
            "gpu_type": gpu_type if self.gpu_info else None,
            "features": {
                "avx2": self.features.get("avx2", False),
                "avx512": self.features.get("avx512", False),
                "cuda": self.features.get("cuda", False),
                "rocm": self.features.get("rocm", False),
                "ane": self.features.get("ane", False),
                "amx": self.features.get("amx", False)
            }
        }
    
    def _get_device_name(self) -> str:
        """生成设备名称
        
        Returns:
            str: 设备名称
        """
        # 生成CPU名称部分
        cpu_name = self.cpu_info["name"].split()[0]
        if "Intel" in self.cpu_info["name"]:
            for part in self.cpu_info["name"].split():
                if part.startswith("i3") or part.startswith("i5") or part.startswith("i7") or part.startswith("i9"):
                    cpu_name = part
                    break
        elif "AMD" in self.cpu_info["name"]:
            for part in self.cpu_info["name"].split():
                if "Ryzen" in part:
                    cpu_name = "Ryzen"
                    for num_part in self.cpu_info["name"].split():
                        if num_part.startswith("5") or num_part.startswith("7") or num_part.startswith("9"):
                            cpu_name += " " + num_part
                            break
                    break
        
        # 生成内存部分
        ram_gb = int(self.ram_info["total_mb"] / 1024)
        
        # 如果有GPU，添加GPU信息
        if self.gpu_info:
            gpu_name = self.gpu_info[0]["name"].split()[0]
            if "NVIDIA" in self.gpu_info[0]["name"] or self.gpu_info[0]["type"] == "NVIDIA":
                for part in self.gpu_info[0]["name"].split():
                    if "RTX" in part or "GTX" in part:
                        gpu_name = part
                        # 找到型号
                        for num_part in self.gpu_info[0]["name"].split():
                            if num_part.isdigit() and len(num_part) == 4:
                                gpu_name += " " + num_part
                                break
                        break
            
            # 返回带GPU的设备名称
            return f"{cpu_name}/{ram_gb}GB/{gpu_name}"
        
        # 返回不带GPU的设备名称
        return f"{cpu_name}/{ram_gb}GB"


class DeviceCompatibility:
    """设备兼容性测试类"""
    
    def __init__(self, config_path=None):
        """初始化设备兼容性测试
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "device_matrix.yaml")
        self.config = self._load_config()
        self.device_info = DeviceInfo()
        self.compat_profile = self.device_info.get_compatibility_profile()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            Dict: 配置数据
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"配置文件 {self.config_path} 不存在")
            return {"test_cases": [], "quantization_levels": [], "feature_compatibility": {}}
        
        try:
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {"test_cases": [], "quantization_levels": [], "feature_compatibility": {}}
    
    def find_matching_test_case(self) -> Optional[Dict[str, Any]]:
        """查找匹配的测试用例
        
        Returns:
            Dict: 匹配的测试用例，如果没有找到则返回None
        """
        best_match = None
        best_match_score = -1
        
        for test_case in self.config.get("test_cases", []):
            score = self._calculate_match_score(test_case)
            if score > best_match_score:
                best_match = test_case
                best_match_score = score
        
        return best_match
    
    def _calculate_match_score(self, test_case: Dict[str, Any]) -> float:
        """计算测试用例与当前设备的匹配度
        
        Args:
            test_case: 测试用例
        
        Returns:
            float: 匹配度分数，范围0-1，越高越匹配
        """
        score = 0.0
        total_weight = 0.0
        
        # OS匹配权重
        os_weight = 3.0
        total_weight += os_weight
        if test_case.get("os") == self.compat_profile.get("os"):
            score += os_weight
        
        # 内存匹配权重
        memory_weight = 2.0
        total_weight += memory_weight
        test_memory = test_case.get("memory_limit", 0)
        device_memory = self.compat_profile.get("memory_limit", 0)
        
        # 内存匹配度计算 - 如果设备内存大于测试用例内存的80%，视为匹配
        if device_memory >= test_memory * 0.8:
            memory_match = min(1.0, device_memory / test_memory)
            score += memory_weight * memory_match
        
        # GPU匹配权重
        gpu_weight = 2.0
        total_weight += gpu_weight
        if test_case.get("gpu", False) == self.compat_profile.get("gpu", False):
            score += gpu_weight
        
        # 设备名称匹配（部分匹配即可）
        device_weight = 1.0
        total_weight += device_weight
        test_device = test_case.get("device", "").lower()
        device_name = self.compat_profile.get("device", "").lower()
        
        # 如果测试设备名称包含在当前设备名称中，或反之亦然
        if test_device in device_name or device_name in test_device:
            score += device_weight
        
        # 标准化分数到0-1范围
        return score / total_weight if total_weight > 0 else 0
    
    def get_quantization_level_info(self, level_name: str) -> Optional[Dict[str, Any]]:
        """获取量化级别信息
        
        Args:
            level_name: 量化级别名称
        
        Returns:
            Dict: 量化级别信息
        """
        for level in self.config.get("quantization_levels", []):
            if level.get("name") == level_name:
                return level
        return None
    
    def check_feature_compatibility(self) -> Dict[str, bool]:
        """检查特性兼容性
        
        Returns:
            Dict: 特性兼容性结果
        """
        results = {}
        
        # 获取当前OS类型
        current_os = self.compat_profile.get("os")
        
        # 获取特性兼容性配置
        feature_compat = self.config.get("feature_compatibility", {})
        
        # 检查并行处理兼容性
        parallel_compat = feature_compat.get("parallel_processing", {})
        results["parallel_processing"] = parallel_compat.get(current_os, False)
        
        # 检查GPU加速兼容性
        gpu_compat = feature_compat.get("gpu_acceleration", {}).get(current_os, {})
        gpu_type = self.compat_profile.get("gpu_type")
        # 如果没有GPU，或GPU类型不兼容，则GPU加速不可用
        if not self.compat_profile.get("gpu") or not gpu_type:
            results["gpu_acceleration"] = False
        else:
            # 检查对应GPU类型的兼容性
            results["gpu_acceleration"] = False
            for key, value in gpu_compat.items():
                if key in gpu_type and value:
                    results["gpu_acceleration"] = True
                    break
        
        # 检查硬件加速兼容性
        hw_compat = feature_compat.get("hardware_acceleration", {}).get(current_os, {})
        results["hardware_acceleration"] = False
        
        for feature, supported in hw_compat.items():
            if supported and self.compat_profile.get("features", {}).get(feature.lower(), False):
                results["hardware_acceleration"] = True
                break
        
        # 检查内存映射兼容性
        results["memory_mapping"] = feature_compat.get("memory_mapping", {}).get(current_os, False)
        
        return results
    
    def run_compatibility_test(self) -> Dict[str, Any]:
        """运行兼容性测试
        
        Returns:
            Dict: 测试结果
        """
        # 获取设备信息
        device_info = self.device_info.to_dict()
        
        # 查找匹配的测试用例
        test_case = self.find_matching_test_case()
        
        # 获取量化级别信息
        quant_level_info = None
        if test_case:
            quant_level_info = self.get_quantization_level_info(test_case.get("quant_level"))
        
        # 检查特性兼容性
        feature_compat = self.check_feature_compatibility()
        
        # 构建测试结果
        result = {
            "device_info": device_info,
            "compatibility_profile": self.compat_profile,
            "matching_test_case": test_case,
            "quantization_level": quant_level_info,
            "feature_compatibility": feature_compat,
            "compatibility_score": self._calculate_match_score(test_case) if test_case else 0,
            "timestamp": time.time(),
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return result
    
    def generate_report(self, result: Dict[str, Any], output_path: str = None) -> str:
        """生成兼容性报告
        
        Args:
            result: 测试结果
            output_path: 报告输出路径
        
        Returns:
            str: 报告输出路径
        """
        # 如果没有指定输出路径，创建默认路径
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = os.path.join(os.path.dirname(__file__), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            output_path = os.path.join(reports_dir, f"compat_report_{timestamp}.json")
        
        # 保存JSON报告
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        return output_path


def parse_arguments():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析的参数
    """
    parser = argparse.ArgumentParser(description="设备兼容性测试工具")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--output", help="输出报告路径")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 创建兼容性测试对象
    compat_test = DeviceCompatibility(config_path=args.config)
    
    # 运行兼容性测试
    result = compat_test.run_compatibility_test()
    
    # 如果需要JSON输出，直接输出结果
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    
    # 生成报告
    report_path = compat_test.generate_report(result, output_path=args.output)
    
    # 打印结果摘要
    device_info = result["device_info"]
    profile = result["compatibility_profile"]
    test_case = result["matching_test_case"]
    quant_level = result["quantization_level"]
    feature_compat = result["feature_compatibility"]
    
    print("\n===== 设备兼容性测试结果 =====")
    print(f"设备: {profile['device']}")
    print(f"操作系统: {device_info['os']['full']}")
    print(f"CPU: {device_info['cpu']['name']} ({device_info['cpu']['cores']}核/{device_info['cpu']['threads']}线程)")
    print(f"内存: {device_info['ram']['total_mb']:.0f}MB ({device_info['ram']['percent']}% 已使用)")
    
    if device_info["gpu"]:
        for gpu in device_info["gpu"]:
            print(f"GPU: {gpu['name']} ({gpu['type']})")
    else:
        print("GPU: 无")
    
    print("\n最佳匹配的设备配置:")
    if test_case:
        print(f"  - 设备: {test_case.get('device')}")
        print(f"  - 操作系统: {test_case.get('os')}")
        print(f"  - 内存要求: {test_case.get('memory_limit')}MB")
        print(f"  - 性能目标: {test_case.get('performance_target')}FPS")
        print(f"  - 量化级别: {test_case.get('quant_level')}")
        
        if quant_level:
            print(f"  - 量化详情: {quant_level.get('description')}")
            print(f"  - 内存占用: 原始模型的 {quant_level.get('memory_ratio', 0)*100:.0f}%")
            print(f"  - 性能比例: {quant_level.get('performance_ratio', 0):.1f}x")
            print(f"  - 质量比例: {quant_level.get('quality_ratio', 0):.1f}x")
    else:
        print("  未找到匹配的设备配置")
    
    print("\n特性兼容性:")
    print(f"  - 并行处理: {'支持' if feature_compat.get('parallel_processing', False) else '不支持'}")
    print(f"  - GPU加速: {'支持' if feature_compat.get('gpu_acceleration', False) else '不支持'}")
    print(f"  - 硬件加速: {'支持' if feature_compat.get('hardware_acceleration', False) else '不支持'}")
    print(f"  - 内存映射: {'支持' if feature_compat.get('memory_mapping', False) else '不支持'}")
    
    print(f"\n兼容性分数: {result['compatibility_score']:.2f}")
    print(f"报告已保存到: {report_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 