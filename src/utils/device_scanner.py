"""设备扫描模块

此模块负责扫描和监控系统硬件资源，主要功能包括：
1. CPU信息检测
2. 内存资源检测
3. GPU设备检测
4. 磁盘空间检测
5. 系统负载监控
"""

import os
import sys
import platform
import psutil
import shutil
from typing import Dict, List, Optional, Union
from pathlib import Path
from loguru import logger

class DeviceScanner:
    """设备扫描器"""
    
    def __init__(self):
        """初始化设备扫描器"""
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        self.min_memory = 4 * 1024 * 1024 * 1024  # 最小4GB内存要求
        self.min_disk = 10 * 1024 * 1024 * 1024   # 最小10GB磁盘空间要求
        
    def detect_hardware(self) -> Dict:
        """检测系统硬件信息
        
        Returns:
            Dict: 硬件信息字典
        """
        try:
            hardware_info = {
                "system": self._get_system_info(),
                "cpu": self._get_cpu_info(),
                "memory": self._get_memory_info(),
                "gpu": self._get_gpu_info(),
                "disk": self._get_disk_info(),
                "network": self._get_network_info()
            }
            
            logger.info("硬件检测完成")
            return hardware_info
            
        except Exception as e:
            logger.error(f"硬件检测失败: {str(e)}")
            return {}
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        return {
            "os": self.system,
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version
        }
    
    def _get_cpu_info(self) -> Dict:
        """获取CPU信息"""
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "usage_per_core": [percentage for percentage in psutil.cpu_percent(percpu=True)],
            "total_usage": psutil.cpu_percent()
        }
        
        # 获取CPU温度（如果支持）
        try:
            cpu_info["temperature"] = psutil.sensors_temperatures()
        except Exception:
            cpu_info["temperature"] = None
            
        return cpu_info
    
    def _get_memory_info(self) -> Dict:
        """获取内存信息"""
        virtual_memory = psutil.virtual_memory()
        swap_memory = psutil.swap_memory()
        
        return {
            "total": virtual_memory.total,
            "available": virtual_memory.available,
            "used": virtual_memory.used,
            "free": virtual_memory.free,
            "percent": virtual_memory.percent,
            "swap_total": swap_memory.total,
            "swap_used": swap_memory.used,
            "swap_free": swap_memory.free,
            "swap_percent": swap_memory.percent
        }
    
    def _get_gpu_info(self) -> Optional[List[Dict]]:
        """获取GPU信息"""
        try:
            import torch
            import nvidia_smi
            
            gpu_info = []
            if torch.cuda.is_available():
                nvidia_smi.nvmlInit()
                
                for i in range(torch.cuda.device_count()):
                    handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
                    info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
                    
                    gpu_info.append({
                        "index": i,
                        "name": torch.cuda.get_device_name(i),
                        "total_memory": info.total,
                        "free_memory": info.free,
                        "used_memory": info.used,
                        "temperature": nvidia_smi.nvmlDeviceGetTemperature(
                            handle, nvidia_smi.NVML_TEMPERATURE_GPU
                        ),
                        "power_usage": nvidia_smi.nvmlDeviceGetPowerUsage(handle) / 1000.0,
                        "power_limit": nvidia_smi.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0
                    })
                
                nvidia_smi.nvmlShutdown()
                return gpu_info
            
            return None
            
        except Exception as e:
            logger.warning(f"GPU信息获取失败: {str(e)}")
            return None
    
    def _get_disk_info(self) -> Dict:
        """获取磁盘信息"""
        disk_info = {
            "partitions": [],
            "io_counters": {}
        }
        
        # 获取分区信息
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info["partitions"].append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                })
            except Exception:
                continue
        
        # 获取IO计数器
        try:
            io_counters = psutil.disk_io_counters(perdisk=True)
            for disk, counters in io_counters.items():
                disk_info["io_counters"][disk] = {
                    "read_count": counters.read_count,
                    "write_count": counters.write_count,
                    "read_bytes": counters.read_bytes,
                    "write_bytes": counters.write_bytes,
                    "read_time": counters.read_time,
                    "write_time": counters.write_time
                }
        except Exception:
            pass
            
        return disk_info
    
    def _get_network_info(self) -> Dict:
        """获取网络信息"""
        network_info = {
            "interfaces": {},
            "connections": []
        }
        
        # 获取网络接口信息
        for interface, addresses in psutil.net_if_addrs().items():
            network_info["interfaces"][interface] = []
            for addr in addresses:
                network_info["interfaces"][interface].append({
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "family": str(addr.family)
                })
        
        # 获取网络连接信息
        try:
            for conn in psutil.net_connections(kind='inet'):
                network_info["connections"].append({
                    "fd": conn.fd,
                    "family": conn.family,
                    "type": conn.type,
                    "local_addr": conn.laddr,
                    "remote_addr": conn.raddr,
                    "status": conn.status
                })
        except Exception:
            pass
            
        return network_info
    
    def check_requirements(self) -> Dict[str, bool]:
        """检查系统是否满足运行要求
        
        Returns:
            Dict[str, bool]: 需求检查结果
        """
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(os.getcwd())
        
        requirements = {
            "memory": memory.total >= self.min_memory,
            "disk": disk.free >= self.min_disk,
            "gpu": self._has_gpu_support()
        }
        
        if not requirements["memory"]:
            logger.warning(f"内存不足: 需要至少{self.min_memory / 1024**3:.1f}GB")
        if not requirements["disk"]:
            logger.warning(f"磁盘空间不足: 需要至少{self.min_disk / 1024**3:.1f}GB")
        if not requirements["gpu"]:
            logger.warning("未检测到可用的GPU设备")
            
        return requirements
    
    def _has_gpu_support(self) -> bool:
        """检查是否支持GPU"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def monitor_resources(self, interval: int = 1) -> Dict:
        """监控系统资源使用情况
        
        Args:
            interval: 监控间隔（秒）
            
        Returns:
            Dict: 资源使用统计
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=interval)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(os.getcwd())
            
            stats = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "gpu_usage": None
            }
            
            # 获取GPU使用情况
            if self._has_gpu_support():
                import torch
                import nvidia_smi
                
                nvidia_smi.nvmlInit()
                handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
                gpu_utilization = nvidia_smi.nvmlDeviceGetUtilizationRates(handle)
                stats["gpu_usage"] = gpu_utilization.gpu
                nvidia_smi.nvmlShutdown()
            
            return stats
            
        except Exception as e:
            logger.error(f"资源监控失败: {str(e)}")
            return {}
    
    def get_available_memory(self) -> int:
        """获取可用内存大小（字节）
        
        Returns:
            int: 可用内存大小
        """
        return psutil.virtual_memory().available
    
    def get_available_disk_space(self, path: Union[str, Path] = None) -> int:
        """获取可用磁盘空间（字节）
        
        Args:
            path: 目标路径，默认为当前目录
            
        Returns:
            int: 可用空间大小
        """
        path = path or os.getcwd()
        return psutil.disk_usage(path).free
    
    def get_gpu_memory_info(self) -> Optional[Dict]:
        """获取GPU内存信息
        
        Returns:
            Optional[Dict]: GPU内存信息
        """
        try:
            if not self._has_gpu_support():
                return None
                
            import nvidia_smi
            nvidia_smi.nvmlInit()
            handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
            info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
            
            memory_info = {
                "total": info.total,
                "free": info.free,
                "used": info.used
            }
            
            nvidia_smi.nvmlShutdown()
            return memory_info
            
        except Exception:
            return None 