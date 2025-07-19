"""硬件降级策略管理模块

该模块负责智能管理系统在低配置硬件环境下的适应性调整，包括：
1. 自适应资源分配
2. 模型精度降级策略
3. 批处理调整
4. 多级内存优化
5. 低端硬件兼容性保障
"""

import os
import time
import threading
import psutil
import json
from typing import Dict, List, Optional, Callable, Union, Any, Tuple
from enum import Enum
from loguru import logger

from ..utils.memory_manager import MemoryManager
from ..utils.device_manager import HybridDevice, DeviceType
from ..utils.resource_predictor import ResourcePredictor
from .degradation import DegradationManager, DegradationLevel
from .model_switcher import ModelSwitcher
from .unload_manager import UnloadManager

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80



class HardwareProfile(Enum):
    """硬件配置档案"""
    HIGH_END = "high_end"         # 高配置: 16GB+内存, 独立GPU
    MID_RANGE = "mid_range"       # 中配置: 8GB内存, 集成显卡
    LOW_END = "low_end"           # 低配置: 4GB内存, 无GPU
    MINIMUM = "minimum"           # 最低配置: 2GB内存, 无GPU


class AdaptiveMode(Enum):
    """自适应模式"""
    PERFORMANCE = "performance"   # 优先性能
    BALANCED = "balanced"         # 平衡模式
    MEMORY_SAVING = "memory_saving" # 节省内存


class HardwareDegradationStrategy:
    """硬件降级策略管理器"""
    
    def __init__(self,
                memory_manager: Optional[MemoryManager] = None,
                device_manager: Optional[HybridDevice] = None,
                degradation_manager: Optional[DegradationManager] = None,
                model_switcher: Optional[ModelSwitcher] = None,
                unload_manager: Optional[UnloadManager] = None,
                config_path: Optional[str] = None):
        """初始化硬件降级策略管理器
        
        Args:
            memory_manager: 内存管理器实例
            device_manager: 设备管理器实例
            degradation_manager: 降级管理器实例
            model_switcher: 模型切换器实例
            unload_manager: 卸载管理器实例
            config_path: 配置文件路径
        """
        # 初始化组件
        self.memory_manager = memory_manager or MemoryManager()
        self.device_manager = device_manager or HybridDevice()
        self.degradation_manager = degradation_manager or DegradationManager()
        self.model_switcher = model_switcher or ModelSwitcher()
        self.unload_manager = unload_manager or UnloadManager()
        
        # 资源预测器
        self.resource_predictor = ResourcePredictor()
        
        # 当前硬件配置
        self.hardware_profile = self._detect_hardware_profile()
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 当前模式设置
        self.adaptive_mode = AdaptiveMode.BALANCED
        
        # 监控线程
        self.monitor_thread = None
        self.monitoring = False
        self.monitor_interval = 10  # 默认10秒检查一次
        
        # 关键组件状态
        self.components_state = {}
        
        # 初始化完成
        logger.info(f"硬件降级策略管理器初始化完成，当前硬件配置: {self.hardware_profile.value}")
        logger.info(f"系统状态: 内存: {self._get_memory_info()}, CPU核心: {psutil.cpu_count(logical=False)}")
        
        # 应用初始配置
        self._apply_initial_configuration()
    
    def _detect_hardware_profile(self) -> HardwareProfile:
        """检测当前硬件配置
        
        Returns:
            HardwareProfile: 检测到的硬件配置
        """
        # 获取系统内存信息
        vm = psutil.virtual_memory()
        total_memory_gb = vm.total / (1024**3)
        
        # 获取GPU信息
        gpu_available = self.device_manager.gpu_available
        
        # 根据配置确定硬件档案
        if total_memory_gb >= 16 and gpu_available:
            return HardwareProfile.HIGH_END
        elif total_memory_gb >= 8:
            return HardwareProfile.MID_RANGE
        elif total_memory_gb >= 4:
            return HardwareProfile.LOW_END
        else:
            return HardwareProfile.MINIMUM
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict: 配置信息
        """
        # 默认配置
        default_config = {
            "profiles": {
                HardwareProfile.HIGH_END.value: {
                    "model_precision": "q4_k_m",
                    "batch_size": 8,
                    "context_length": 8192,
                    "preload_models": True,
                    "video_quality": "high",
                    "concurrent_tasks": 4
                },
                HardwareProfile.MID_RANGE.value: {
                    "model_precision": "q4_k_m",
                    "batch_size": 4,
                    "context_length": 4096,
                    "preload_models": True,
                    "video_quality": "medium",
                    "concurrent_tasks": 2
                },
                HardwareProfile.LOW_END.value: {
                    "model_precision": "q3_k",
                    "batch_size": 2,
                    "context_length": 2048,
                    "preload_models": False,
                    "video_quality": "medium",
                    "concurrent_tasks": 1
                },
                HardwareProfile.MINIMUM.value: {
                    "model_precision": "q2_k",
                    "batch_size": 1,
                    "context_length": 1024,
                    "preload_models": False,
                    "video_quality": "low",
                    "concurrent_tasks": 1
                }
            },
            "adaptive_modes": {
                AdaptiveMode.PERFORMANCE.value: {
                    "memory_threshold": 0.9,  # 内存使用阈值
                    "cpu_threshold": 0.95,    # CPU使用阈值
                    "prioritize_speed": True,
                    "aggressive_gc": False,
                    "unload_unused_models_delay": 300  # 5分钟后卸载未使用模型
                },
                AdaptiveMode.BALANCED.value: {
                    "memory_threshold": 0.8,
                    "cpu_threshold": 0.85,
                    "prioritize_speed": False,
                    "aggressive_gc": False,
                    "unload_unused_models_delay": 120  # 2分钟后卸载未使用模型
                },
                AdaptiveMode.MEMORY_SAVING.value: {
                    "memory_threshold": 0.7,
                    "cpu_threshold": 0.8,
                    "prioritize_speed": False,
                    "aggressive_gc": True,
                    "unload_unused_models_delay": 60   # 1分钟后卸载未使用模型
                }
            },
            "monitor_interval": 10,  # 监控间隔（秒）
            "enable_auto_adaptation": True  # 是否启用自动适应
        }
        
        # 尝试从文件加载配置
        config = default_config
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 递归更新配置
                    config = self._recursive_update(config, file_config)
                logger.info(f"已从 {config_path} 加载硬件降级策略配置")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}，使用默认配置")
        
        return config
    
    def _recursive_update(self, original: Dict, update: Dict) -> Dict:
        """递归更新字典
        
        Args:
            original: 原始字典
            update: 更新内容
            
        Returns:
            Dict: 更新后的字典
        """
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                original[key] = self._recursive_update(original[key], value)
            else:
                original[key] = value
        return original
    
    def _apply_initial_configuration(self):
        """应用初始配置"""
        # 获取当前硬件配置的推荐设置
        profile_config = self.config["profiles"][self.hardware_profile.value]
        
        # 应用降级管理器配置
        if self.hardware_profile in [HardwareProfile.LOW_END, HardwareProfile.MINIMUM]:
            # 低配置硬件直接应用降级配置
            degradation_level = DegradationLevel.WARNING if self.hardware_profile == HardwareProfile.LOW_END else DegradationLevel.CRITICAL
            self.degradation_manager.degrade(degradation_level)
            logger.info(f"已应用{degradation_level.value}级别降级策略")
        
        # 更新组件状态
        self.components_state = {
            "model_precision": profile_config["model_precision"],
            "batch_size": profile_config["batch_size"],
            "context_length": profile_config["context_length"],
            "preload_models": profile_config["preload_models"],
            "video_quality": profile_config["video_quality"],
            "concurrent_tasks": profile_config["concurrent_tasks"]
        }
        
        # 设置监控间隔
        self.monitor_interval = self.config.get("monitor_interval", 10)
        
        # 如果配置为自动适应，启动监控
        if self.config.get("enable_auto_adaptation", True):
            self.start_monitoring()
    
    def set_adaptive_mode(self, mode: AdaptiveMode) -> bool:
        """设置自适应模式
        
        Args:
            mode: 自适应模式
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if isinstance(mode, str):
                try:
                    mode = AdaptiveMode(mode)
                except ValueError:
                    logger.error(f"无效的自适应模式: {mode}")
                    return False
            
            if mode not in AdaptiveMode:
                logger.error(f"无效的自适应模式: {mode}")
                return False
            
            # 更新模式
            self.adaptive_mode = mode
            logger.info(f"已切换到{mode.value}模式")
            
            # 应用新模式的配置
            self._apply_mode_configuration(mode)
            
            return True
        except Exception as e:
            logger.error(f"设置自适应模式失败: {e}")
            return False
    
    def _apply_mode_configuration(self, mode: AdaptiveMode):
        """应用指定模式的配置
        
        Args:
            mode: 自适应模式
        """
        mode_config = self.config["adaptive_modes"][mode.value]
        
        # 应用内存管理配置
        if mode == AdaptiveMode.MEMORY_SAVING:
            # 内存节省模式下进行主动内存清理
            self.memory_manager.optimize_memory(aggressive=True)
            
            # 确保不会预加载模型
            self.components_state["preload_models"] = False
        
        # 更新卸载器配置
        if self.unload_manager:
            unload_delay = mode_config.get("unload_unused_models_delay", 120)
            self.unload_manager.configure({
                "unused_timeout": unload_delay,
                "aggressive": mode == AdaptiveMode.MEMORY_SAVING
            })
    
    def start_monitoring(self) -> bool:
        """启动硬件资源监控
        
        Returns:
            bool: 是否成功启动
        """
        if self.monitoring:
            logger.warning("监控线程已在运行")
            return False
        
        self.monitoring = True
        
        def monitor_task():
            logger.info("硬件资源监控已启动")
            while self.monitoring:
                try:
                    # 检查硬件资源状态
                    self._check_resources()
                    
                    # 根据当前模式处理资源状态
                    self._handle_resource_state()
                except Exception as e:
                    logger.error(f"资源监控出错: {e}")
                finally:
                    # 等待下一次检查
                    time.sleep(self.monitor_interval)
        
        self.monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self) -> bool:
        """停止硬件资源监控
        
        Returns:
            bool: 是否成功停止
        """
        if not self.monitoring:
            logger.warning("监控线程未运行")
            return False
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None
            
        logger.info("硬件资源监控已停止")
        return True
    
    def _check_resources(self) -> Dict:
        """检查当前硬件资源状态
        
        Returns:
            Dict: 资源状态信息
        """
        # 获取内存使用情况
        memory_info = self._get_memory_info()
        
        # 获取CPU使用情况
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # 获取GPU使用情况(如果有)
        gpu_info = None
        if self.device_manager.gpu_available:
            self.device_manager.update_device_stats()
            device_info = self.device_manager.get_device_info()
            if "stats" in device_info and "gpu" in device_info["stats"]:
                gpu_info = device_info["stats"]["gpu"]
        
        # 更新资源状态
        resource_state = {
            "memory": memory_info,
            "cpu_percent": cpu_percent,
            "gpu": gpu_info,
            "timestamp": time.time()
        }
        
        return resource_state
    
    def _get_memory_info(self) -> Dict:
        """获取内存使用情况
        
        Returns:
            Dict: 内存信息
        """
        vm = psutil.virtual_memory()
        return {
            "total": vm.total,
            "available": vm.available,
            "used": vm.used,
            "free": vm.free,
            "percent": vm.percent / 100,  # 转换为0-1之间的值
            "total_gb": vm.total / (1024**3),
            "available_gb": vm.available / (1024**3)
        }
    
    def _handle_resource_state(self):
        """根据资源状态进行相应调整"""
        # 获取当前资源状态
        resource_state = self._check_resources()
        
        # 获取当前模式配置
        mode_config = self.config["adaptive_modes"][self.adaptive_mode.value]
        
        # 检查内存使用是否超过阈值
        memory_percent = resource_state["memory"]["percent"]
        memory_threshold = mode_config["memory_threshold"]
        
        # 检查CPU使用是否超过阈值
        cpu_percent = resource_state["cpu_percent"] / 100  # 转换为0-1之间的值
        cpu_threshold = mode_config["cpu_threshold"]
        
        # 根据资源使用情况决定是否需要降级
        if memory_percent > memory_threshold:
            # 内存使用超过阈值，需要降级
            logger.warning(f"内存使用率({memory_percent:.2%})超过阈值({memory_threshold:.2%})，执行资源释放")
            
            # 尝试释放内存
            self._release_memory_resources()
            
            # 如果仍然超过阈值，则触发降级
            if psutil.virtual_memory().percent / 100 > memory_threshold:
                self._trigger_degradation(resource_state)
        
        if cpu_percent > cpu_threshold:
            # CPU使用超过阈值，需要降级
            logger.warning(f"CPU使用率({cpu_percent:.2%})超过阈值({cpu_threshold:.2%})，执行任务调整")
            
            # 调整任务处理
            self._adjust_task_processing()
    
    def _release_memory_resources(self):
        """释放内存资源"""
        # 1. 尝试优化内存
        before, after = self.memory_manager.optimize_memory(
            aggressive=self.adaptive_mode == AdaptiveMode.MEMORY_SAVING
        )
        logger.info(f"内存优化: {before:.2f}MB -> {after:.2f}MB, 释放了{before - after:.2f}MB")
        
        # 2. 卸载未使用的模型组件
        try:
            unloaded = self.unload_manager.unload_unused_components()
            if unloaded:
                logger.info(f"已卸载 {len(unloaded)} 个未使用组件")
        except Exception as e:
            logger.error(f"卸载未使用组件失败: {e}")
        
        # 3. 调整批处理大小
        current_batch = self.components_state["batch_size"]
        if current_batch > 1:
            new_batch = max(1, current_batch - 1)
            self.components_state["batch_size"] = new_batch
            logger.info(f"已减小批处理大小: {current_batch} -> {new_batch}")
    
    def _adjust_task_processing(self):
        """调整任务处理方式"""
        # 减少并发任务数
        current_concurrent = self.components_state["concurrent_tasks"]
        if current_concurrent > 1:
            new_concurrent = max(1, current_concurrent - 1)
            self.components_state["concurrent_tasks"] = new_concurrent
            logger.info(f"已减少并发任务数: {current_concurrent} -> {new_concurrent}")
    
    def _trigger_degradation(self, resource_state: Dict):
        """触发系统降级
        
        Args:
            resource_state: 资源状态信息
        """
        # 确定降级级别
        memory_percent = resource_state["memory"]["percent"]
        
        if memory_percent > 0.95:
            # 极度紧张，最高级别降级
            degradation_level = DegradationLevel.EMERGENCY
        elif memory_percent > 0.85:
            # 紧张，高级别降级
            degradation_level = DegradationLevel.CRITICAL
        elif memory_percent > 0.75:
            # 警告级别
            degradation_level = DegradationLevel.WARNING
        else:
            # 正常级别
            return
        
        # 触发降级
        try:
            success = self.degradation_manager.degrade(degradation_level)
            if success:
                logger.warning(f"已触发{degradation_level.value}级别降级策略")
                
                # 更新组件状态
                degradation_config = self.degradation_manager.get_state()["config"]
                self.components_state.update({
                    "model_precision": degradation_config["model_precision"],
                    "batch_size": degradation_config["batch_size"],
                    "video_quality": degradation_config["video_quality"],
                    "concurrent_tasks": degradation_config["max_concurrent"]
                })
            else:
                logger.error(f"触发降级失败: {degradation_level.value}")
        except Exception as e:
            logger.error(f"触发降级异常: {e}")
    
    def get_status(self) -> Dict:
        """获取当前状态信息
        
        Returns:
            Dict: 状态信息
        """
        return {
            "hardware_profile": self.hardware_profile.value,
            "adaptive_mode": self.adaptive_mode.value,
            "components_state": self.components_state,
            "monitoring_active": self.monitoring,
            "resource_state": self._check_resources(),
            "degradation_level": self.degradation_manager.get_state()["level"]
        }
    
    def optimize_for_model(self, model_name: str, language: str) -> Dict:
        """为特定模型优化系统配置
        
        Args:
            model_name: 模型名称
            language: 语言("zh"或"en")
            
        Returns:
            Dict: 优化结果
        """
        try:
            # 获取模型配置
            model_configs = self.model_switcher._model_configs
            if model_name not in model_configs:
                return {
                    "success": False,
                    "error": f"未找到模型配置: {model_name}"
                }
            
            model_config = model_configs[model_name]
            
            # 获取当前硬件状态
            resource_state = self._check_resources()
            memory_available = resource_state["memory"]["available"]
            
            # 预测模型最佳配置
            optimal_batch = self.resource_predictor.predict_optimal_batch_size(
                available_memory=memory_available,
                model_size=model_config.get('memory_required', 0),
                min_batch=1,
                max_batch=self.components_state["batch_size"]
            )
            
            # 应用优化配置
            degradation_level = None
            if memory_available < model_config.get('memory_required', 0) * 1.2:
                # 内存紧张，触发降级
                if self.hardware_profile == HardwareProfile.MINIMUM:
                    degradation_level = DegradationLevel.EMERGENCY
                elif self.hardware_profile == HardwareProfile.LOW_END:
                    degradation_level = DegradationLevel.CRITICAL
                else:
                    degradation_level = DegradationLevel.WARNING
                    
                # 应用降级
                if degradation_level:
                    self.degradation_manager.degrade(degradation_level)
            
            # 更新批处理大小
            self.components_state["batch_size"] = optimal_batch
            
            # 根据语言确定模型加载策略
            if language == "zh" and self.hardware_profile in [HardwareProfile.LOW_END, HardwareProfile.MINIMUM]:
                # 低配置设备且为中文模型时，确保英文模型被卸载
                if "mistral-7b-en" in model_configs:
                    self.unload_manager.unload_component("mistral-7b-en")
            
            return {
                "success": True,
                "optimized_settings": {
                    "batch_size": optimal_batch,
                    "degradation_level": degradation_level.value if degradation_level else "normal",
                    "model": model_name,
                    "language": language
                }
            }
            
        except Exception as e:
            logger.error(f"模型优化配置失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reset(self):
        """重置为默认状态"""
        # 停止监控
        if self.monitoring:
            self.stop_monitoring()
        
        # 恢复降级管理器
        self.degradation_manager.recover(force=True)
        
        # 重新应用初始配置
        self._apply_initial_configuration()
        
        logger.info("已重置硬件降级策略管理器")
        
    def __del__(self):
        """清理资源"""
        if self.monitoring:
            self.stop_monitoring() 