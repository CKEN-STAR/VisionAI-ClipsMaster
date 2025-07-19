#!/usr/bin/env python3
"""
VisionAI-ClipsMaster GPU检测功能全面验证报告

此脚本对GPU检测功能进行全面验证，包括：
1. 功能验证测试
2. 真实性验证  
3. 有效性测试
4. 异常场景测试
"""

import os
import sys
import json
import time
import psutil
import platform
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any

class GPUVerificationFinal:
    """GPU检测功能最终验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.report = {
            "verification_timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "verification_results": {},
            "performance_data": {},
            "recommendations": []
        }
        
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
        }
    
    def verify_pytorch_gpu_detection(self) -> Dict:
        """验证PyTorch GPU检测"""
        print("🔍 验证PyTorch GPU检测...")
        result = {
            "test_name": "PyTorch GPU检测验证",
            "status": "PASS",
            "details": {},
            "issues": []
        }
        
        try:
            import torch
            
            # 基本信息
            result["details"]["torch_version"] = torch.__version__
            result["details"]["cuda_available"] = torch.cuda.is_available()
            result["details"]["cuda_version"] = torch.version.cuda if torch.cuda.is_available() else None
            
            if torch.cuda.is_available():
                result["details"]["device_count"] = torch.cuda.device_count()
                result["details"]["current_device"] = torch.cuda.current_device()
                
                # 获取每个设备的详细信息
                devices = []
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    device_info = {
                        "index": i,
                        "name": torch.cuda.get_device_name(i),
                        "total_memory_gb": round(props.total_memory / (1024**3), 2),
                        "compute_capability": f"{props.major}.{props.minor}",
                        "multiprocessor_count": props.multi_processor_count,
                        "memory_allocated": torch.cuda.memory_allocated(i),
                        "memory_reserved": torch.cuda.memory_reserved(i)
                    }
                    devices.append(device_info)
                
                result["details"]["devices"] = devices
                
                # 测试基本GPU操作
                try:
                    test_tensor = torch.cuda.FloatTensor([1.0, 2.0, 3.0])
                    result["details"]["basic_operation"] = "SUCCESS"
                    del test_tensor
                    torch.cuda.empty_cache()
                except Exception as e:
                    result["details"]["basic_operation"] = f"FAILED: {str(e)}"
                    result["issues"].append(f"基本GPU操作失败: {str(e)}")
            else:
                result["details"]["no_gpu_reason"] = "CUDA不可用或未安装CUDA版本的PyTorch"
                
        except ImportError:
            result["status"] = "FAIL"
            result["issues"].append("PyTorch未安装")
        except Exception as e:
            result["status"] = "FAIL"
            result["issues"].append(f"PyTorch GPU检测失败: {str(e)}")
            
        return result
    
    def verify_system_gpu_detection(self) -> Dict:
        """验证系统级GPU检测"""
        print("🔍 验证系统级GPU检测...")
        result = {
            "test_name": "系统级GPU检测验证",
            "status": "PASS",
            "details": {},
            "issues": []
        }
        
        # Windows WMI检测
        try:
            wmic_result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM,DriverVersion", "/format:csv"],
                capture_output=True, text=True, timeout=15
            )
            
            if wmic_result.returncode == 0:
                wmi_devices = []
                lines = wmic_result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    if line.strip() and ',' in line:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            name = parts[3].strip()
                            ram = parts[1].strip()
                            driver = parts[2].strip()
                            
                            if name and name != "Name" and name:
                                device = {
                                    "name": name,
                                    "memory_bytes": int(ram) if ram.isdigit() else 0,
                                    "driver_version": driver if driver else "Unknown"
                                }
                                wmi_devices.append(device)
                
                result["details"]["wmi_detection"] = {
                    "success": True,
                    "devices": wmi_devices,
                    "device_count": len(wmi_devices)
                }
            else:
                result["details"]["wmi_detection"] = {
                    "success": False,
                    "error": wmic_result.stderr
                }
                result["issues"].append("WMI GPU查询失败")
                
        except Exception as e:
            result["details"]["wmi_detection"] = {
                "success": False,
                "error": str(e)
            }
            result["issues"].append(f"WMI检测失败: {str(e)}")
        
        # nvidia-smi检测
        try:
            nvidia_smi_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version", 
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=10
            )
            
            if nvidia_smi_result.returncode == 0:
                nvidia_devices = []
                for i, line in enumerate(nvidia_smi_result.stdout.strip().split('\n')):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 4:
                            device = {
                                "index": i,
                                "name": parts[0],
                                "memory_total_mb": int(parts[1]),
                                "memory_free_mb": int(parts[2]),
                                "driver_version": parts[3]
                            }
                            nvidia_devices.append(device)
                
                result["details"]["nvidia_smi_detection"] = {
                    "success": True,
                    "devices": nvidia_devices,
                    "device_count": len(nvidia_devices)
                }
            else:
                result["details"]["nvidia_smi_detection"] = {
                    "success": False,
                    "error": "nvidia-smi命令失败"
                }
        except FileNotFoundError:
            result["details"]["nvidia_smi_detection"] = {
                "success": False,
                "error": "nvidia-smi命令未找到"
            }
        except Exception as e:
            result["details"]["nvidia_smi_detection"] = {
                "success": False,
                "error": str(e)
            }
        
        return result
    
    def verify_device_manager_integration(self) -> Dict:
        """验证设备管理器集成"""
        print("🔍 验证设备管理器集成...")
        result = {
            "test_name": "设备管理器集成验证",
            "status": "PASS",
            "details": {},
            "performance_metrics": {},
            "issues": []
        }
        
        try:
            # 添加项目路径
            project_path = os.path.join(os.path.dirname(__file__), 'VisionAI-ClipsMaster-Core')
            if project_path not in sys.path:
                sys.path.insert(0, project_path)
            
            from src.utils.device_manager import HybridDevice, DeviceType
            
            # 测试初始化
            start_time = time.time()
            device_manager = HybridDevice()
            init_time = time.time() - start_time
            
            result["details"]["initialization"] = {
                "success": True,
                "time_seconds": init_time
            }
            
            # 测试设备信息获取
            start_time = time.time()
            device_info = device_manager.get_device_info()
            info_time = time.time() - start_time
            
            result["details"]["device_info"] = {
                "success": bool(device_info),
                "time_seconds": info_time,
                "current_device": device_info.get("current_device"),
                "available_devices": [d.value for d in device_info.get("available_devices", [])],
                "has_stats": bool(device_info.get("stats"))
            }
            
            # 测试设备选择
            device_selection_results = {}
            for device_type in [DeviceType.AUTO, DeviceType.CPU_BASIC, DeviceType.CPU_AVX2, DeviceType.CUDA]:
                try:
                    start_time = time.time()
                    selected = device_manager.select_device(device_type)
                    selection_time = time.time() - start_time
                    
                    device_selection_results[device_type.value] = {
                        "requested": device_type.value,
                        "selected": selected.value if selected else None,
                        "time_seconds": selection_time,
                        "success": True
                    }
                except Exception as e:
                    device_selection_results[device_type.value] = {
                        "requested": device_type.value,
                        "selected": None,
                        "time_seconds": 0,
                        "success": False,
                        "error": str(e)
                    }
                    result["issues"].append(f"设备选择失败 {device_type.value}: {str(e)}")
            
            result["details"]["device_selection"] = device_selection_results
            
            # 计算性能指标
            successful_selections = [r for r in device_selection_results.values() if r["success"]]
            if successful_selections:
                avg_time = sum(r["time_seconds"] for r in successful_selections) / len(successful_selections)
                max_time = max(r["time_seconds"] for r in successful_selections)
                
                result["performance_metrics"] = {
                    "average_selection_time": avg_time,
                    "max_selection_time": max_time,
                    "meets_1_5s_requirement": max_time <= 1.5,
                    "initialization_time": init_time,
                    "info_retrieval_time": info_time
                }
                
                if max_time > 1.5:
                    result["status"] = "WARN"
                    result["issues"].append(f"设备切换时间 {max_time:.2f}s 超过要求的1.5s")
            
        except Exception as e:
            result["status"] = "FAIL"
            result["issues"].append(f"设备管理器集成验证失败: {str(e)}")
        
        return result
    
    def verify_performance_benchmarks(self) -> Dict:
        """验证性能基准"""
        print("🔍 验证性能基准...")
        result = {
            "test_name": "性能基准验证",
            "status": "PASS",
            "details": {},
            "benchmarks": {},
            "issues": []
        }
        
        try:
            import torch
            
            # CPU基准测试
            matrix_size = 512
            cpu_a = torch.randn(matrix_size, matrix_size)
            cpu_b = torch.randn(matrix_size, matrix_size)
            
            # CPU性能测试
            cpu_times = []
            for _ in range(3):
                start_time = time.time()
                cpu_result = torch.mm(cpu_a, cpu_b)
                cpu_times.append(time.time() - start_time)
            
            cpu_avg_time = sum(cpu_times) / len(cpu_times)
            
            result["benchmarks"]["cpu"] = {
                "matrix_size": f"{matrix_size}x{matrix_size}",
                "iterations": 3,
                "times": cpu_times,
                "average_time": cpu_avg_time,
                "operations_per_second": 1 / cpu_avg_time if cpu_avg_time > 0 else 0
            }
            
            # GPU基准测试（如果可用）
            if torch.cuda.is_available():
                gpu_a = cpu_a.cuda()
                gpu_b = cpu_b.cuda()
                
                # 预热GPU
                for _ in range(2):
                    _ = torch.mm(gpu_a, gpu_b)
                torch.cuda.synchronize()
                
                # GPU性能测试
                gpu_times = []
                for _ in range(3):
                    start_time = time.time()
                    gpu_result = torch.mm(gpu_a, gpu_b)
                    torch.cuda.synchronize()
                    gpu_times.append(time.time() - start_time)
                
                gpu_avg_time = sum(gpu_times) / len(gpu_times)
                
                result["benchmarks"]["gpu"] = {
                    "matrix_size": f"{matrix_size}x{matrix_size}",
                    "iterations": 3,
                    "times": gpu_times,
                    "average_time": gpu_avg_time,
                    "operations_per_second": 1 / gpu_avg_time if gpu_avg_time > 0 else 0,
                    "speedup_vs_cpu": cpu_avg_time / gpu_avg_time if gpu_avg_time > 0 else 0
                }
                
                # 验证结果一致性
                max_diff = torch.max(torch.abs(cpu_result - gpu_result.cpu())).item()
                result["details"]["result_consistency"] = {
                    "max_difference": max_diff,
                    "is_consistent": max_diff < 1e-4
                }
                
                if not result["details"]["result_consistency"]["is_consistent"]:
                    result["issues"].append("CPU和GPU计算结果不一致")
            else:
                result["benchmarks"]["gpu"] = {"status": "GPU不可用"}
            
        except Exception as e:
            result["status"] = "FAIL"
            result["issues"].append(f"性能基准验证失败: {str(e)}")
        
        return result
    
    def run_comprehensive_verification(self) -> Dict:
        """运行全面验证"""
        print("🚀 开始GPU检测功能全面验证...")
        print("=" * 60)
        
        # 执行所有验证测试
        verification_tests = [
            self.verify_pytorch_gpu_detection,
            self.verify_system_gpu_detection,
            self.verify_device_manager_integration,
            self.verify_performance_benchmarks
        ]
        
        for test_func in verification_tests:
            try:
                test_result = test_func()
                self.report["verification_results"][test_result["test_name"]] = test_result
                
                # 打印结果
                status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
                print(f"{status_emoji.get(test_result['status'], '❓')} {test_result['test_name']}: {test_result['status']}")
                
                if test_result["issues"]:
                    for issue in test_result["issues"]:
                        print(f"   ⚠️ {issue}")
                        
            except Exception as e:
                error_result = {
                    "test_name": test_func.__name__,
                    "status": "FAIL",
                    "issues": [f"测试执行异常: {str(e)}"]
                }
                self.report["verification_results"][test_func.__name__] = error_result
                print(f"❌ {test_func.__name__}: FAIL - {str(e)}")
        
        # 生成建议和总结
        self._generate_recommendations()
        self._generate_summary()
        
        return self.report
    
    def _generate_recommendations(self):
        """生成建议"""
        recommendations = []
        
        # 基于验证结果生成建议
        results = self.report["verification_results"]
        
        # 检查GPU可用性
        pytorch_result = results.get("PyTorch GPU检测验证", {})
        if not pytorch_result.get("details", {}).get("cuda_available", False):
            recommendations.append("建议安装CUDA版本的PyTorch以启用GPU加速")
        
        # 检查系统GPU检测
        system_result = results.get("系统级GPU检测验证", {})
        nvidia_detection = system_result.get("details", {}).get("nvidia_smi_detection", {})
        if not nvidia_detection.get("success", False):
            recommendations.append("建议安装NVIDIA GPU驱动程序和CUDA工具包")
        
        # 检查性能
        device_manager_result = results.get("设备管理器集成验证", {})
        performance_metrics = device_manager_result.get("performance_metrics", {})
        if not performance_metrics.get("meets_1_5s_requirement", True):
            recommendations.append("设备切换性能需要优化")
        
        # 系统建议
        if self.report["system_info"]["memory_total_gb"] < 8:
            recommendations.append("建议升级到8GB或更多内存")
        
        self.report["recommendations"] = recommendations
    
    def _generate_summary(self):
        """生成总结"""
        results = self.report["verification_results"]
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("status") == "PASS")
        failed_tests = sum(1 for r in results.values() if r.get("status") == "FAIL")
        warned_tests = sum(1 for r in results.values() if r.get("status") == "WARN")
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "warned": warned_tests,
            "overall_status": "PASS" if failed_tests == 0 else "FAIL",
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        self.report["summary"] = summary
        
        print("\n" + "=" * 60)
        print("📊 验证总结:")
        print(f"   总验证项: {total_tests}")
        print(f"   通过: {passed_tests} ✅")
        print(f"   失败: {failed_tests} ❌")
        print(f"   警告: {warned_tests} ⚠️")
        print(f"   总体状态: {summary['overall_status']}")
        print(f"   成功率: {summary['success_rate']:.1f}%")
        
        if self.report["recommendations"]:
            print("\n💡 建议:")
            for rec in self.report["recommendations"]:
                print(f"   • {rec}")
    
    def save_report(self, filename: str = None):
        """保存验证报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gpu_verification_final_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 验证报告已保存: {filename}")
        return filename

def main():
    """主函数"""
    verifier = GPUVerificationFinal()
    
    try:
        # 运行全面验证
        report = verifier.run_comprehensive_verification()
        
        # 保存报告
        report_file = verifier.save_report()
        
        # 返回退出码
        summary = report.get("summary", {})
        if summary.get("overall_status") == "FAIL":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ 验证执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
