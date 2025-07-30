#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster GPU诊断工具
全面诊断GPU检测问题并提供修复方案

诊断内容:
1. PyTorch CUDA支持检测
2. NVIDIA-SMI可用性检测
3. Windows WMI GPU检测
4. 内存使用与GPU关系分析
5. 提供针对性修复方案
"""

import os
import sys
import platform
import subprocess
import psutil
import time
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

class GPUDiagnosticTool:
    """GPU诊断工具"""
    
    def __init__(self):
        self.diagnosis_results = {
            "system_info": {},
            "pytorch_cuda": {},
            "nvidia_smi": {},
            "windows_wmi": {},
            "memory_analysis": {},
            "recommendations": []
        }
        
    def collect_system_info(self):
        """收集系统基础信息"""
        print("🔍 收集系统基础信息...")
        
        try:
            memory = psutil.virtual_memory()
            self.diagnosis_results["system_info"] = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture()[0],
                "python_version": platform.python_version(),
                "total_memory_gb": memory.total / 1024**3,
                "available_memory_gb": memory.available / 1024**3,
                "memory_percent": memory.percent,
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True)
            }
            
            print(f"  操作系统: {self.diagnosis_results['system_info']['platform']}")
            print(f"  Python版本: {self.diagnosis_results['system_info']['python_version']}")
            print(f"  总内存: {self.diagnosis_results['system_info']['total_memory_gb']:.2f}GB")
            print(f"  可用内存: {self.diagnosis_results['system_info']['available_memory_gb']:.2f}GB")
            print(f"  CPU核心: {self.diagnosis_results['system_info']['cpu_count']}")
            
        except Exception as e:
            print(f"  ❌ 系统信息收集失败: {e}")
            
    def diagnose_pytorch_cuda(self):
        """诊断PyTorch CUDA支持"""
        print("\n🔥 诊断PyTorch CUDA支持...")
        
        try:
            import torch
            self.diagnosis_results["pytorch_cuda"]["installed"] = True
            self.diagnosis_results["pytorch_cuda"]["version"] = torch.__version__
            
            print(f"  ✅ PyTorch已安装: {torch.__version__}")
            
            # 检查CUDA编译支持
            cuda_compiled = torch.version.cuda is not None
            self.diagnosis_results["pytorch_cuda"]["cuda_compiled"] = cuda_compiled
            self.diagnosis_results["pytorch_cuda"]["cuda_version"] = torch.version.cuda
            
            if cuda_compiled:
                print(f"  ✅ CUDA编译支持: {torch.version.cuda}")
            else:
                print(f"  ❌ CUDA编译支持: 无")
                self.diagnosis_results["recommendations"].append(
                    "安装支持CUDA的PyTorch版本: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                )
            
            # 检查CUDA运行时可用性
            cuda_available = torch.cuda.is_available()
            self.diagnosis_results["pytorch_cuda"]["cuda_available"] = cuda_available
            
            if cuda_available:
                device_count = torch.cuda.device_count()
                self.diagnosis_results["pytorch_cuda"]["device_count"] = device_count
                print(f"  ✅ CUDA运行时可用: {device_count}个设备")
                
                # 获取GPU设备信息
                devices = []
                for i in range(device_count):
                    device_name = torch.cuda.get_device_name(i)
                    device_props = torch.cuda.get_device_properties(i)
                    devices.append({
                        "id": i,
                        "name": device_name,
                        "memory_total_gb": device_props.total_memory / 1024**3,
                        "multiprocessor_count": device_props.multi_processor_count
                    })
                    print(f"    GPU {i}: {device_name} ({device_props.total_memory / 1024**3:.1f}GB)")
                
                self.diagnosis_results["pytorch_cuda"]["devices"] = devices
            else:
                print(f"  ❌ CUDA运行时不可用")
                if cuda_compiled:
                    self.diagnosis_results["recommendations"].append(
                        "CUDA运行时不可用，可能原因：1) 无NVIDIA GPU 2) 驱动版本不兼容 3) CUDA Toolkit未安装"
                    )
                
        except ImportError:
            print(f"  ❌ PyTorch未安装")
            self.diagnosis_results["pytorch_cuda"]["installed"] = False
            self.diagnosis_results["recommendations"].append(
                "安装PyTorch: pip install torch torchvision torchaudio"
            )
        except Exception as e:
            print(f"  ❌ PyTorch CUDA检测异常: {e}")
            self.diagnosis_results["pytorch_cuda"]["error"] = str(e)
    
    def diagnose_nvidia_smi(self):
        """诊断NVIDIA-SMI可用性"""
        print("\n🖥️ 诊断NVIDIA-SMI可用性...")
        
        try:
            # 测试nvidia-smi命令
            result = subprocess.run(
                ["nvidia-smi", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"  ✅ nvidia-smi可用")
                self.diagnosis_results["nvidia_smi"]["available"] = True
                self.diagnosis_results["nvidia_smi"]["version_output"] = result.stdout.strip()
                
                # 获取GPU列表
                gpu_result = subprocess.run(
                    ["nvidia-smi", "-L"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if gpu_result.returncode == 0 and gpu_result.stdout.strip():
                    gpu_lines = gpu_result.stdout.strip().split("\n")
                    self.diagnosis_results["nvidia_smi"]["gpu_list"] = gpu_lines
                    print(f"  ✅ 检测到{len(gpu_lines)}个NVIDIA GPU:")
                    for line in gpu_lines:
                        print(f"    {line}")
                else:
                    print(f"  ⚠️ nvidia-smi可用但未检测到GPU")
                    self.diagnosis_results["nvidia_smi"]["gpu_list"] = []
                    
            else:
                print(f"  ❌ nvidia-smi执行失败: 返回码{result.returncode}")
                self.diagnosis_results["nvidia_smi"]["available"] = False
                self.diagnosis_results["nvidia_smi"]["error"] = f"返回码{result.returncode}"
                
        except FileNotFoundError:
            print(f"  ❌ nvidia-smi命令未找到")
            self.diagnosis_results["nvidia_smi"]["available"] = False
            self.diagnosis_results["nvidia_smi"]["error"] = "命令未找到"
            self.diagnosis_results["recommendations"].append(
                "nvidia-smi不可用，可能原因：1) 无NVIDIA GPU 2) NVIDIA驱动未安装 3) 驱动版本过旧"
            )
            
        except subprocess.TimeoutExpired:
            print(f"  ❌ nvidia-smi执行超时")
            self.diagnosis_results["nvidia_smi"]["available"] = False
            self.diagnosis_results["nvidia_smi"]["error"] = "执行超时"
            
        except Exception as e:
            print(f"  ❌ nvidia-smi检测异常: {e}")
            self.diagnosis_results["nvidia_smi"]["available"] = False
            self.diagnosis_results["nvidia_smi"]["error"] = str(e)
    
    def diagnose_windows_wmi(self):
        """诊断Windows WMI GPU检测"""
        if platform.system() != "Windows":
            print("\n⏭️ 跳过Windows WMI检测（非Windows系统）")
            return
            
        print("\n🪟 诊断Windows WMI GPU检测...")
        
        # 方法1: 使用wmic命令
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name,adapterram,driverversion", "/format:csv"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                gpus = []
                
                for line in lines[1:]:  # 跳过标题行
                    if line.strip() and ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 4:
                            name = parts[3].strip()
                            if name and name != "Name":
                                gpu_info = {
                                    "name": name,
                                    "memory": parts[1].strip() if len(parts) > 1 else "N/A",
                                    "driver": parts[2].strip() if len(parts) > 2 else "N/A"
                                }
                                gpus.append(gpu_info)
                
                self.diagnosis_results["windows_wmi"]["wmic_available"] = True
                self.diagnosis_results["windows_wmi"]["detected_gpus"] = gpus
                
                print(f"  ✅ WMIC检测到{len(gpus)}个显卡:")
                for gpu in gpus:
                    print(f"    {gpu['name']}")
                    
            else:
                print(f"  ❌ WMIC执行失败")
                self.diagnosis_results["windows_wmi"]["wmic_available"] = False
                
        except Exception as e:
            print(f"  ❌ WMIC检测异常: {e}")
            self.diagnosis_results["windows_wmi"]["wmic_error"] = str(e)
        
        # 方法2: 尝试WMI模块
        try:
            import wmi
            c = wmi.WMI()
            wmi_gpus = []
            
            for gpu in c.Win32_VideoController():
                if gpu.Name:
                    wmi_gpus.append({
                        "name": gpu.Name,
                        "driver_version": gpu.DriverVersion,
                        "memory": gpu.AdapterRAM
                    })
            
            self.diagnosis_results["windows_wmi"]["wmi_module_available"] = True
            self.diagnosis_results["windows_wmi"]["wmi_detected_gpus"] = wmi_gpus
            
            print(f"  ✅ WMI模块检测到{len(wmi_gpus)}个显卡:")
            for gpu in wmi_gpus:
                print(f"    {gpu['name']}")
                
        except ImportError:
            print(f"  ⚠️ WMI模块不可用")
            self.diagnosis_results["windows_wmi"]["wmi_module_available"] = False
            self.diagnosis_results["recommendations"].append(
                "安装WMI模块以增强GPU检测: pip install WMI"
            )
        except Exception as e:
            print(f"  ❌ WMI模块检测异常: {e}")
            self.diagnosis_results["windows_wmi"]["wmi_error"] = str(e)
    
    def analyze_memory_usage(self):
        """分析内存使用与GPU的关系"""
        print("\n💾 分析内存使用与GPU关系...")
        
        memory = psutil.virtual_memory()
        
        self.diagnosis_results["memory_analysis"] = {
            "total_gb": memory.total / 1024**3,
            "used_gb": memory.used / 1024**3,
            "available_gb": memory.available / 1024**3,
            "percent": memory.percent,
            "high_usage": memory.percent > 80,
            "target_limit_gb": 3.8
        }
        
        print(f"  总内存: {memory.total / 1024**3:.2f}GB")
        print(f"  已用内存: {memory.used / 1024**3:.2f}GB ({memory.percent:.1f}%)")
        print(f"  可用内存: {memory.available / 1024**3:.2f}GB")
        print(f"  目标限制: 3.8GB")
        
        # 分析内存使用过高的原因
        if memory.percent > 80:
            print(f"  ⚠️ 内存使用过高 ({memory.percent:.1f}%)")
            
            # 检查是否因为无GPU而导致CPU内存占用过大
            pytorch_cuda = self.diagnosis_results.get("pytorch_cuda", {})
            if not pytorch_cuda.get("cuda_available", False):
                print(f"  💡 可能原因: 无GPU加速，CPU处理占用大量内存")
                self.diagnosis_results["recommendations"].append(
                    "内存使用过高可能与无GPU加速有关，建议：1) 安装GPU驱动 2) 优化CPU模式内存使用"
                )
            
            if memory.used / 1024**3 > 3.8:
                print(f"  🚨 超出4GB设备目标限制")
                self.diagnosis_results["recommendations"].append(
                    "当前内存使用超出4GB设备限制，需要优化内存管理策略"
                )
        else:
            print(f"  ✅ 内存使用正常")
    
    def generate_recommendations(self):
        """生成修复建议"""
        print("\n💡 生成修复建议...")
        
        pytorch_cuda = self.diagnosis_results.get("pytorch_cuda", {})
        nvidia_smi = self.diagnosis_results.get("nvidia_smi", {})
        memory_analysis = self.diagnosis_results.get("memory_analysis", {})
        
        # GPU相关建议
        if not pytorch_cuda.get("cuda_available", False):
            if not pytorch_cuda.get("cuda_compiled", False):
                self.diagnosis_results["recommendations"].append(
                    "🔧 安装支持CUDA的PyTorch: pip uninstall torch && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
                )
            
            if not nvidia_smi.get("available", False):
                self.diagnosis_results["recommendations"].append(
                    "🔧 安装NVIDIA驱动: 从NVIDIA官网下载最新驱动程序"
                )
        
        # 内存优化建议
        if memory_analysis.get("high_usage", False):
            self.diagnosis_results["recommendations"].append(
                "🔧 优化内存使用: 实施更激进的内存清理策略"
            )
            
        # 4GB设备优化建议
        if memory_analysis.get("total_gb", 0) <= 6:
            self.diagnosis_results["recommendations"].append(
                "🔧 4GB设备优化: 启用量化模型和分片加载"
            )
        
        # 无GPU环境优化
        if not pytorch_cuda.get("cuda_available", False):
            self.diagnosis_results["recommendations"].append(
                "🔧 CPU模式优化: 使用OpenVINO或ONNX Runtime加速CPU推理"
            )
    
    def run_full_diagnosis(self):
        """运行完整诊断"""
        print("🔍 VisionAI-ClipsMaster GPU诊断工具")
        print("=" * 50)
        
        # 执行各项诊断
        self.collect_system_info()
        self.diagnose_pytorch_cuda()
        self.diagnose_nvidia_smi()
        self.diagnose_windows_wmi()
        self.analyze_memory_usage()
        self.generate_recommendations()
        
        # 生成诊断报告
        print("\n" + "=" * 50)
        print("📊 诊断结果总结:")
        
        # GPU可用性总结
        pytorch_cuda = self.diagnosis_results.get("pytorch_cuda", {})
        nvidia_smi = self.diagnosis_results.get("nvidia_smi", {})
        
        gpu_available = pytorch_cuda.get("cuda_available", False)
        print(f"  GPU加速可用: {'✅ 是' if gpu_available else '❌ 否'}")
        
        if gpu_available:
            device_count = pytorch_cuda.get("device_count", 0)
            print(f"  GPU设备数量: {device_count}")
        else:
            print(f"  运行模式: CPU模式")
        
        # 内存状态总结
        memory_analysis = self.diagnosis_results.get("memory_analysis", {})
        memory_status = "正常" if not memory_analysis.get("high_usage", False) else "过高"
        print(f"  内存状态: {memory_status} ({memory_analysis.get('percent', 0):.1f}%)")
        
        # 修复建议
        recommendations = self.diagnosis_results.get("recommendations", [])
        if recommendations:
            print(f"\n🔧 修复建议 ({len(recommendations)}项):")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print(f"\n✅ 系统状态良好，无需修复")
        
        return self.diagnosis_results

if __name__ == "__main__":
    # 运行GPU诊断
    diagnostic = GPUDiagnosticTool()
    results = diagnostic.run_full_diagnosis()
    
    # 保存诊断报告
    import json
    with open("gpu_diagnostic_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细诊断报告已保存到: gpu_diagnostic_report.json")
