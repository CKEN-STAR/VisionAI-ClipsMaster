#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能默认值引擎

根据系统硬件、软件环境和使用模式，自动检测并推荐最优配置值。
"""

import os
import sys
import platform
import logging
import psutil
import json
from typing import Dict, Any, Optional, Union, List, Tuple

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("smart_defaults")

class SmartDefaults:
    """智能默认值引擎，根据系统环境自动推荐最优配置"""
    
    def __init__(self):
        """初始化智能默认值引擎"""
        # 硬件感知设置
        self.hardware_aware = {
            'resolution': self._detect_max_resolution,
            'frame_rate': self._get_display_refresh_rate,
            'gpu_memory': self._detect_gpu_memory,
            'cpu_threads': self._detect_optimal_threads,
            'storage_path': self._detect_optimal_storage_path,
            'cache_size': self._detect_optimal_cache_size
        }
        
        # 软件环境感知设置
        self.software_aware = {
            'language': self._detect_preferred_language,
            'codec': self._detect_optimal_codec,
            'theme': self._detect_system_theme
        }
        
        # 用户行为感知
        self.usage_aware = {
            'auto_save_interval': self._suggest_auto_save_interval,
            'export_preset': self._suggest_export_preset,
            'timeline_zoom': self._suggest_timeline_zoom
        }
        
        # 系统信息缓存
        self.system_info = self._collect_system_info()
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        info = {
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version()
            },
            "cpu": {
                "cores_physical": psutil.cpu_count(logical=False),
                "cores_logical": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=0.1)
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available
            },
            "disk": {}
        }
        
        # 收集磁盘信息
        for part in psutil.disk_partitions():
            if os.name == 'nt' and 'cdrom' in part.opts or part.fstype == '':
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                info["disk"][part.mountpoint] = {
                    "total": usage.total,
                    "free": usage.free
                }
            except:
                pass
        
        # 尝试获取GPU信息
        try:
            info["gpu"] = self._detect_gpu_info()
        except:
            info["gpu"] = {"available": False}
        
        logger.debug(f"收集到系统信息: {json.dumps(info, indent=2, ensure_ascii=False)}")
        return info
    
    def _detect_gpu_info(self) -> Dict[str, Any]:
        """检测GPU信息"""
        gpu_info = {"available": False}
        
        try:
            # 尝试使用NVIDIA工具
            import pynvml
            pynvml.nvmlInit()
            gpu_count = pynvml.nvmlDeviceGetCount()
            
            if gpu_count > 0:
                gpu_info["available"] = True
                gpu_info["count"] = gpu_count
                gpu_info["devices"] = []
                
                for i in range(gpu_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    name = pynvml.nvmlDeviceGetName(handle)
                    
                    gpu_info["devices"].append({
                        "name": name,
                        "memory_total": info.total,
                        "memory_free": info.free
                    })
            
            pynvml.nvmlShutdown()
        except:
            # 如果失败，尝试使用其他方法检测
            try:
                if platform.system() == "Windows":
                    # Windows系统使用wmi
                    import wmi
                    w = wmi.WMI()
                    gpu_devices = w.Win32_VideoController()
                    
                    if len(gpu_devices) > 0:
                        gpu_info["available"] = True
                        gpu_info["count"] = len(gpu_devices)
                        gpu_info["devices"] = []
                        
                        for gpu in gpu_devices:
                            gpu_info["devices"].append({
                                "name": gpu.Name,
                                "driver_version": gpu.DriverVersion,
                                "memory_total": "unknown"
                            })
            except:
                pass
        
        return gpu_info
    
    def _detect_max_resolution(self) -> str:
        """根据显卡能力自动选择分辨率"""
        try:
            if self._check_gpu_capability():
                return "4K"
            else:
                return "1080p"
        except:
            return "1080p"
    
    def _check_gpu_capability(self) -> bool:
        """检查GPU是否支持4K处理"""
        try:
            # 检查是否有NVIDIA GPU并且内存大于等于4GB
            if "gpu" in self.system_info and self.system_info["gpu"]["available"]:
                for device in self.system_info["gpu"]["devices"]:
                    if "memory_total" in device and device["memory_total"] >= 4 * 1024 * 1024 * 1024:
                        return True
                    if "name" in device and any(x in device["name"].lower() for x in ["rtx", "gtx 1", "gtx 2", "radeon"]):
                        return True
            return False
        except:
            return False
    
    def _get_display_refresh_rate(self) -> int:
        """获取显示器刷新率"""
        try:
            if platform.system() == "Windows":
                import ctypes
                user32 = ctypes.windll.user32
                device_context = user32.GetDC(0)
                refresh_rate = ctypes.c_int()
                ctypes.windll.gdi32.GetDeviceCaps(device_context, 116, ctypes.byref(refresh_rate))
                user32.ReleaseDC(0, device_context)
                
                if refresh_rate.value > 0:
                    # 向下取整到标准帧率值：24, 30, 60
                    if refresh_rate.value >= 60:
                        return 60
                    elif refresh_rate.value >= 30:
                        return 30
                    else:
                        return 24
            return 30
        except:
            return 30
    
    def _detect_gpu_memory(self) -> int:
        """检测GPU可用内存并推荐合适的限制"""
        try:
            if "gpu" in self.system_info and self.system_info["gpu"]["available"]:
                # 遍历所有GPU，找到内存最大的一个
                max_memory = 0
                for device in self.system_info["gpu"]["devices"]:
                    if "memory_total" in device and device["memory_total"] > max_memory:
                        max_memory = device["memory_total"]
                
                # 转换为MB并推荐使用70%
                if max_memory > 0:
                    recommended = int((max_memory / (1024 * 1024)) * 0.7)
                    # 限制在合理范围内
                    return max(512, min(recommended, 8192))
            
            # 默认设置
            return 2048
        except:
            return 2048
    
    def _detect_optimal_threads(self) -> Union[int, str]:
        """检测CPU并推荐最佳线程数"""
        try:
            logical_cores = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False)
            
            if physical_cores is None or logical_cores is None:
                return "auto"
            
            # 根据核心数推荐合理的线程数
            # 对于低核心数CPU，使用所有逻辑核心
            if physical_cores <= 2:
                return logical_cores
            
            # 对于中等核心数，留一个核心给系统
            if physical_cores <= 6:
                return max(2, logical_cores - 2)
            
            # 对于高核心数，使用75%的逻辑核心
            return max(4, int(logical_cores * 0.75))
        except:
            return "auto"
    
    def _detect_optimal_storage_path(self) -> str:
        """检测并推荐最佳存储路径"""
        try:
            # 获取可用空间最大的非系统盘
            system_drive = os.environ.get('SystemDrive', 'C:') if platform.system() == "Windows" else "/"
            max_space = 0
            best_path = os.path.expanduser("~/ClipsMasterOutput")
            
            for mountpoint, info in self.system_info["disk"].items():
                # 跳过系统盘
                if platform.system() == "Windows" and mountpoint.lower().startswith(system_drive.lower()):
                    continue
                
                # 寻找空间最大的分区
                if info["free"] > max_space:
                    max_space = info["free"]
                    if platform.system() == "Windows":
                        best_path = os.path.join(mountpoint, "ClipsMasterOutput")
                    else:
                        best_path = os.path.join(mountpoint, "ClipsMasterOutput")
            
            # 确保路径有效
            if not os.path.isdir(os.path.dirname(best_path)):
                return os.path.expanduser("~/ClipsMasterOutput")
            
            return best_path
        except:
            return os.path.expanduser("~/ClipsMasterOutput")
    
    def _detect_optimal_cache_size(self) -> int:
        """根据系统内存和磁盘空间推荐合适的缓存大小"""
        try:
            # 获取总内存和可用磁盘空间
            total_memory_mb = self.system_info["memory"]["total"] / (1024 * 1024)
            
            # 可用磁盘空间（取最小值）
            min_free_space_mb = float('inf')
            for _, info in self.system_info["disk"].items():
                free_space_mb = info["free"] / (1024 * 1024)
                min_free_space_mb = min(min_free_space_mb, free_space_mb)
            
            if min_free_space_mb == float('inf'):
                min_free_space_mb = 10240  # 默认10GB
            
            # 基于内存和磁盘空间计算建议缓存大小
            memory_based = int(total_memory_mb * 0.3)  # 内存的30%
            disk_based = int(min_free_space_mb * 0.2)  # 可用磁盘空间的20%
            
            # 取较小的值，并限制在合理范围内
            recommended = min(memory_based, disk_based)
            return max(1024, min(recommended, 51200))  # 最小1GB，最大50GB
        except:
            return 10240  # 默认10GB
    
    def _detect_preferred_language(self) -> str:
        """检测系统语言并推荐界面语言"""
        try:
            import locale
            current_locale = locale.getdefaultlocale()[0]
            
            # 检查是否是中文
            if current_locale and current_locale.startswith(('zh_', 'zh-')):
                return "zh_CN"
            return "en_US"
        except:
            return "zh_CN"  # 默认中文
    
    def _detect_optimal_codec(self) -> str:
        """根据硬件能力推荐最佳编解码器"""
        try:
            # 检测GPU型号和驱动，推荐合适的编解码器
            if "gpu" in self.system_info and self.system_info["gpu"]["available"]:
                for device in self.system_info["gpu"]["devices"]:
                    name = device.get("name", "").lower()
                    
                    # 对于较新的NVIDIA卡，推荐H265
                    if "rtx" in name or "gtx 16" in name or "gtx 20" in name:
                        return "h265"
                    
                    # 对于较新的AMD卡
                    if "radeon rx" in name and any(x in name for x in ["5", "6", "7"]):
                        return "h265"
            
            # 默认使用最通用的H264
            return "h264"
        except:
            return "h264"
    
    def _detect_system_theme(self) -> str:
        """检测系统主题并推荐匹配的界面主题"""
        try:
            if platform.system() == "Windows":
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                
                return "light" if value == 1 else "dark"
            
            # 默认为系统自动
            return "system"
        except:
            return "system"
    
    def _suggest_auto_save_interval(self) -> int:
        """根据系统性能推荐自动保存间隔"""
        try:
            # 基于CPU性能推荐间隔
            cpu_performance = self.system_info["cpu"]["cores_physical"] * 2
            
            if cpu_performance >= 16:  # 高性能
                return 3
            elif cpu_performance >= 8:  # 中等性能
                return 5
            else:  # 低性能
                return 10
        except:
            return 5  # 默认5分钟
    
    def _suggest_export_preset(self) -> str:
        """根据系统能力推荐导出预设"""
        if self._check_gpu_capability():
            return "高质量 (4K)"
        else:
            return "网络视频 (1080p)"
    
    def _suggest_timeline_zoom(self) -> int:
        """根据显示分辨率推荐时间线缩放级别"""
        try:
            if platform.system() == "Windows":
                import ctypes
                user32 = ctypes.windll.user32
                width = user32.GetSystemMetrics(0)
                
                if width >= 3840:  # 4K及以上
                    return 7
                elif width >= 2560:  # 2K
                    return 6
                elif width >= 1920:  # 1080p
                    return 5
                else:  # 低分辨率
                    return 4
            return 5
        except:
            return 5
    
    def get_hardware_aware_defaults(self) -> Dict[str, Any]:
        """获取硬件感知的默认设置"""
        result = {}
        for key, detector in self.hardware_aware.items():
            try:
                result[key] = detector()
            except Exception as e:
                logger.error(f"检测{key}默认值时出错: {str(e)}")
        return result
    
    def get_software_aware_defaults(self) -> Dict[str, Any]:
        """获取软件环境感知的默认设置"""
        result = {}
        for key, detector in self.software_aware.items():
            try:
                result[key] = detector()
            except Exception as e:
                logger.error(f"检测{key}默认值时出错: {str(e)}")
        return result
    
    def get_usage_aware_defaults(self) -> Dict[str, Any]:
        """获取使用模式感知的默认设置"""
        result = {}
        for key, detector in self.usage_aware.items():
            try:
                result[key] = detector()
            except Exception as e:
                logger.error(f"检测{key}默认值时出错: {str(e)}")
        return result
    
    def get_all_smart_defaults(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能默认设置"""
        return {
            "hardware": self.get_hardware_aware_defaults(),
            "software": self.get_software_aware_defaults(),
            "usage": self.get_usage_aware_defaults()
        }
    
    def apply_to_config(self, config_manager, override_existing=False) -> bool:
        """
        将智能默认值应用到配置管理器
        
        Args:
            config_manager: 配置管理器实例
            override_existing: 是否覆盖已存在的配置
            
        Returns:
            bool: 是否成功应用
        """
        try:
            # 获取所有智能默认值
            all_defaults = self.get_all_smart_defaults()
            
            # 映射智能默认值到配置路径
            mapping = {
                # 硬件相关
                "hardware.resolution": "user.export.resolution",
                "hardware.frame_rate": "user.export.frame_rate",
                "hardware.gpu_memory": "system.gpu.memory_limit",
                "hardware.cpu_threads": "system.cpu.threads",
                "hardware.storage_path": "user.export.storage.output_path",
                "hardware.cache_size": "system.cache.size_limit",
                
                # 软件相关
                "software.language": "app.default_language",
                "software.codec": "user.export.codec",
                "software.theme": "app.theme",
                
                # 使用习惯相关
                "usage.auto_save_interval": "app.auto_save_interval",
                "usage.timeline_zoom": "user.interface.timeline_zoom"
            }
            
            # 应用映射
            for smart_path, config_path in mapping.items():
                cat, key = smart_path.split(".")
                value = all_defaults[cat].get(key)
                
                if value is not None:
                    try:
                        # 解析配置路径
                        config_type, *config_keys = config_path.split(".")
                        config_key = ".".join(config_keys)
                        
                        # 如果不覆盖已存在的值，先检查是否存在
                        if not override_existing:
                            try:
                                existing_value = config_manager.get_config(config_type, config_key)
                                # 如果已有有效值，跳过
                                if existing_value:
                                    continue
                            except:
                                pass  # 如果获取失败，说明不存在，继续设置
                        
                        # 设置配置值
                        config_manager.set_config(config_type, config_key, value)
                        logger.debug(f"应用智能默认值: {config_path} = {value}")
                    except Exception as e:
                        logger.error(f"应用智能默认值{config_path}时出错: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"应用智能默认值失败: {str(e)}")
            return False


# 创建全局智能默认值引擎实例
smart_defaults = SmartDefaults()

if __name__ == "__main__":
    # 简单测试
    import json
    defaults = smart_defaults.get_all_smart_defaults()
    print(json.dumps(defaults, indent=2, ensure_ascii=False))
    
    # 测试应用到配置
    try:
        from src.config.config_manager import config_manager
        result = smart_defaults.apply_to_config(config_manager)
        print(f"应用智能默认值结果: {'成功' if result else '失败'}")
    except ImportError:
        print("未找到配置管理器，无法应用") 