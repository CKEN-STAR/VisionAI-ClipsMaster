#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境管理器

负责检测、记录和管理应用运行环境，根据设备能力自动调整配置。
提供统一的环境信息查询接口，用于应用中的性能优化和功能适配。
"""

import os
import sys
import json
import logging
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# 添加tests目录到系统路径，以便导入device_detector
tests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests'))
if tests_dir not in sys.path:
    sys.path.append(tests_dir)

# 导入设备检测功能
from tests.device_compatibility.device_detector import detect_environment
from tests.device_compatibility.device_matrix import generate_compatibility_report

# 设置日志记录器
logger = logging.getLogger("environment_manager")

class EnvironmentManager:
    """环境管理器类，负责应用环境的检测和配置调整"""
    
    def __init__(self, config_dir: Optional[str] = None, auto_detect: bool = True):
        """
        初始化环境管理器
        
        Args:
            config_dir: 配置目录路径，如果为None则使用默认目录
            auto_detect: 是否自动检测环境
        """
        # 设置配置目录
        if config_dir is None:
            self.config_dir = Path.home() / ".visionai" / "config"
        else:
            self.config_dir = Path(config_dir)
            
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 环境配置文件路径
        self.env_config_file = self.config_dir / "environment.json"
        
        # 环境信息和兼容性报告
        self.environment = {}
        self.compatibility = {}
        
        # 如果需要自动检测环境
        if auto_detect:
            self.detect_environment()
    
    def detect_environment(self) -> Dict[str, Any]:
        """
        检测当前运行环境
        
        Returns:
            Dict[str, Any]: 环境信息
        """
        try:
            logger.info("开始检测运行环境...")
            
            # 调用环境检测功能
            self.environment = detect_environment()
            
            # 生成兼容性报告
            device_info = {
                "os": self.environment["os"],
                "cpu": self.environment["cpu"],
                "ram": self.environment["ram"],
                "gpu": self.environment["gpu"],
                "cpu_cores": self.environment.get("cpu_cores", 0),
                "gpu_vram_gb": 0,  # 简单检测无法获取显存
                "storage_available_gb": self.environment.get("storage", {}).get("free_gb", 0)
            }
            
            self.compatibility = generate_compatibility_report(device_info)
            
            # 保存环境信息和兼容性报告
            self._save_environment_info()
            
            logger.info(f"环境检测完成: {self.get_device_summary()}")
            
            return self.environment
            
        except Exception as e:
            logger.error(f"环境检测失败: {e}")
            # 如果检测失败，尝试加载之前保存的环境信息
            if self._load_environment_info():
                logger.info("已加载缓存的环境信息")
                return self.environment
            else:
                # 如果加载也失败，返回基本信息
                logger.warning("无法加载环境信息，将使用基本环境配置")
                self.environment = self._get_basic_environment()
                self.compatibility = self._get_basic_compatibility()
                return self.environment
    
    def _save_environment_info(self) -> bool:
        """
        保存环境信息和兼容性报告到配置文件
        
        Returns:
            bool: 是否成功保存
        """
        try:
            # 组合环境信息和兼容性报告
            data = {
                "environment": self.environment,
                "compatibility": self.compatibility,
                "timestamp": self.environment.get("detection_time", "")
            }
            
            # 保存到文件
            with open(self.env_config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"保存环境信息失败: {e}")
            return False
    
    def _load_environment_info(self) -> bool:
        """
        从配置文件加载环境信息和兼容性报告
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if self.env_config_file.exists():
                with open(self.env_config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.environment = data.get("environment", {})
                self.compatibility = data.get("compatibility", {})
                
                return bool(self.environment and self.compatibility)
            return False
            
        except Exception as e:
            logger.error(f"加载环境信息失败: {e}")
            return False
    
    def _get_basic_environment(self) -> Dict[str, Any]:
        """
        获取基本环境信息（当检测和加载都失败时使用）
        
        Returns:
            Dict[str, Any]: 基本环境信息
        """
        return {
            "cpu": platform.processor() or "Unknown CPU",
            "gpu": "集成显卡",
            "ram": 4.0,  # 假设4GB内存
            "os": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_cores": os.cpu_count() or 2,
            "is_64bit": platform.machine().endswith('64'),
            "detection_time": "Unknown"
        }
    
    def _get_basic_compatibility(self) -> Dict[str, Any]:
        """
        获取基本兼容性报告（当检测和加载都失败时使用）
        
        Returns:
            Dict[str, Any]: 基本兼容性报告
        """
        return {
            "device_tier": "entry",
            "expected_performance": {
                "fps": 15,
                "processing_speed": "0.5x实时",
                "max_resolution": "1080p",
                "concurrent_tasks": 1
            },
            "supported_features": ["basic_processing"],
            "limited_features": ["batch_processing", "multi_language"],
            "unsupported_features": ["4k_processing", "real_time_enhancement"],
            "recommendations": [
                "建议至少升级至8GB内存以支持更多功能",
                "建议添加支持的GPU以启用实时增强和4K处理功能"
            ]
        }
    
    def get_device_summary(self) -> str:
        """
        获取设备摘要信息
        
        Returns:
            str: 设备摘要信息
        """
        if not self.environment:
            return "未检测到环境信息"
        
        device_tier = self.compatibility.get("device_tier", "未知")
        tier_names = {
            "entry": "入门级",
            "mid": "中端",
            "high": "高端",
            "premium": "顶级"
        }
        
        tier_display = tier_names.get(device_tier, "未知")
        
        return (f"{tier_display}设备 - "
                f"CPU: {self.environment.get('cpu', 'Unknown')}, "
                f"RAM: {self.environment.get('ram', 0):.1f}GB, "
                f"GPU: {self.environment.get('gpu', 'Unknown')}")
    
    def get_optimal_config(self) -> Dict[str, Any]:
        """
        根据当前环境生成最佳应用配置
        
        Returns:
            Dict[str, Any]: 最佳应用配置
        """
        config = {
            "general": {
                "debug_mode": False,
                "log_level": "INFO",
                "data_dir": str(Path.home() / ".visionai" / "data"),
                "temp_dir": str(Path.home() / ".visionai" / "temp"),
                "max_history": 100
            },
            "performance": {
                "threads": min(self.environment.get("cpu_cores", 2), 4),
                "use_gpu": self.environment.get("gpu", "集成显卡") != "集成显卡",
                "memory_limit": int(self.environment.get("ram", 4) * 0.7 * 1024),  # MB, 最多使用70%内存
                "batch_size": self._get_optimal_batch_size(),
                "preview_quality": self._get_preview_quality()
            },
            "models": {
                "use_quantization": self.environment.get("ram", 0) < 16,
                "use_low_memory": self.environment.get("ram", 0) < 8,
                "preferred_model": self._get_preferred_model()
            }
        }
        
        return config
    
    def _get_optimal_batch_size(self) -> int:
        """
        根据环境确定最佳批处理大小
        
        Returns:
            int: 批处理大小
        """
        ram_gb = self.environment.get("ram", 4)
        has_gpu = self.environment.get("gpu", "集成显卡") != "集成显卡"
        
        if has_gpu and ram_gb >= 16:
            return 16
        elif has_gpu and ram_gb >= 8:
            return 8
        elif ram_gb >= 8:
            return 4
        else:
            return 1
    
    def _get_preview_quality(self) -> str:
        """
        根据环境确定预览质量
        
        Returns:
            str: 预览质量 (high, medium, low)
        """
        device_tier = self.compatibility.get("device_tier", "entry")
        
        if device_tier in ["premium", "high"]:
            return "high"
        elif device_tier == "mid":
            return "medium"
        else:
            return "low"
    
    def _get_preferred_model(self) -> str:
        """
        根据环境确定首选模型
        
        Returns:
            str: 首选模型名称
        """
        # 获取RAM和GPU信息
        ram_gb = self.environment.get("ram", 4)
        has_gpu = self.environment.get("gpu", "集成显卡") != "集成显卡"
        
        # 检测系统语言来决定默认模型语言
        system_locale = self._detect_system_locale()
        is_chinese = "zh" in system_locale.lower()
        
        # 根据内存和GPU情况选择模型
        if is_chinese:
            if ram_gb >= 16 and has_gpu:
                return "qwen2.5-7b"
            else:
                return "qwen2.5-1.8b"  # 轻量版
        else:
            if ram_gb >= 16 and has_gpu:
                return "mistral-7b"
            else:
                return "mistral-instruct"  # 轻量版
    
    def _detect_system_locale(self) -> str:
        """
        检测系统语言环境
        
        Returns:
            str: 系统语言代码
        """
        try:
            import locale
            return locale.getdefaultlocale()[0] or "en_US"
        except:
            return "en_US"  # 默认英语
    
    def check_feature_availability(self, feature_name: str) -> Tuple[bool, str]:
        """
        检查特定功能是否可用
        
        Args:
            feature_name: 功能名称
            
        Returns:
            Tuple[bool, str]: (是否可用, 原因或建议)
        """
        if not self.compatibility:
            return False, "环境兼容性信息不可用"
        
        if feature_name in self.compatibility.get("supported_features", []):
            return True, "功能完全支持"
        elif feature_name in self.compatibility.get("limited_features", []):
            # 查找相关建议
            for rec in self.compatibility.get("recommendations", []):
                if feature_name.lower() in rec.lower():
                    return True, f"功能受限: {rec}"
            return True, "功能受限，但可使用"
        else:
            # 查找相关建议
            for rec in self.compatibility.get("recommendations", []):
                if feature_name.lower() in rec.lower():
                    return False, f"不支持: {rec}"
            return False, "当前设备不支持此功能"
    
    def get_expected_performance(self) -> Dict[str, Any]:
        """
        获取预期性能指标
        
        Returns:
            Dict[str, Any]: 预期性能指标
        """
        if self.compatibility and "expected_performance" in self.compatibility:
            return self.compatibility["expected_performance"]
        else:
            # 默认性能指标
            return {
                "fps": 15,
                "processing_speed": "0.5x实时",
                "max_resolution": "1080p",
                "concurrent_tasks": 1
            }


# 全局环境管理器实例
_environment_manager = None

def get_environment_manager() -> EnvironmentManager:
    """
    获取环境管理器实例（单例模式）
    
    Returns:
        EnvironmentManager: 环境管理器实例
    """
    global _environment_manager
    
    if _environment_manager is None:
        _environment_manager = EnvironmentManager()
    
    return _environment_manager


def get_optimal_config() -> Dict[str, Any]:
    """
    获取最佳应用配置（便捷函数）
    
    Returns:
        Dict[str, Any]: 最佳应用配置
    """
    return get_environment_manager().get_optimal_config()


def detect_current_environment() -> Dict[str, Any]:
    """
    检测当前环境（便捷函数）
    
    Returns:
        Dict[str, Any]: 环境信息
    """
    return get_environment_manager().detect_environment()


def check_feature_availability(feature_name: str) -> bool:
    """
    检查特定功能是否可用（便捷函数）
    
    Args:
        feature_name: 功能名称
        
    Returns:
        bool: 是否可用
    """
    available, _ = get_environment_manager().check_feature_availability(feature_name)
    return available


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 检测环境并打印信息
    env_manager = EnvironmentManager()
    environment = env_manager.detect_environment()
    
    print("\n环境检测结果:")
    print("-" * 60)
    print(f"设备摘要: {env_manager.get_device_summary()}")
    
    if env_manager.compatibility:
        tier = env_manager.compatibility.get("device_tier", "未知")
        print(f"设备等级: {tier}")
        
        print("\n功能支持状态:")
        for feature in ["basic_processing", "4k_processing", "real_time_enhancement", 
                        "batch_processing", "multi_language"]:
            available, reason = env_manager.check_feature_availability(feature)
            status = "✅ 支持" if available else "❌ 不支持"
            print(f"- {feature}: {status} ({reason})")
    
    print("\n推荐配置:")
    config = env_manager.get_optimal_config()
    print(f"- 使用GPU: {config['performance']['use_gpu']}")
    print(f"- 线程数: {config['performance']['threads']}")
    print(f"- 批处理大小: {config['performance']['batch_size']}")
    print(f"- 使用量化: {config['models']['use_quantization']}")
    print(f"- 首选模型: {config['models']['preferred_model']}")
    
    print("-" * 60) 