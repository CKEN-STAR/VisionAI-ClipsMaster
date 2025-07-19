"""缓存策略管理模块

此模块管理和协调不同的缓存策略，根据系统资源和使用模式自动选择最合适的策略。
提供以下功能：
1. 加载和解析缓存策略配置
2. 智能选择适用的缓存策略
3. 根据设备资源动态调整缓存参数
4. 提供统一的策略接口
5. 收集和分析缓存性能指标
"""

import os
import time
import yaml
import threading
import psutil
from enum import Enum
from typing import Dict, List, Set, Any, Optional, Tuple, Union, Type
from dataclasses import dataclass
from loguru import logger

from src.sharding.cache_policy import (
    CachePolicy, 
    LRUPolicy, 
    LFUPolicy, 
    FIFOPolicy, 
    WeightAwarePolicy, 
    FreqAwarePolicy,
    CachePolicyType,
    CachePolicyFactory
)


@dataclass
class StrategyConfig:
    """缓存策略配置"""
    name: str
    description: str
    implementation: str
    default_max_items: int
    parameters: Dict[str, Any]
    suitable_for: str
    priority: int


@dataclass
class DeviceConfig:
    """设备特定配置"""
    default_strategy: str
    max_items: int
    warm_up_items: List[str]
    parameters: Dict[str, Dict[str, Any]]


class MemoryLevel(Enum):

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """内存级别枚举"""
    CRITICAL = "critical"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class StrategyManager:
    """缓存策略管理器
    
    负责加载和管理缓存策略配置，根据系统状态选择最合适的策略。
    """
    
    def __init__(
        self, 
        config_path: Optional[str] = None,
        model_name: Optional[str] = None,
        auto_adjust: bool = True
    ):
        """初始化策略管理器
        
        Args:
            config_path: 配置文件路径，默认为configs/cache_strategy.yaml
            model_name: 模型名称，用于加载模型特定配置
            auto_adjust: 是否自动调整策略
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "configs", 
            "cache_strategy.yaml"
        )
        
        # 配置数据
        self.config = {}
        self.strategies: Dict[str, StrategyConfig] = {}
        self.device_configs: Dict[str, DeviceConfig] = {}
        self.model_configs: Dict[str, DeviceConfig] = {}
        self.thresholds: Dict[str, Optional[int]] = {}
        
        # 当前状态
        self.model_name = model_name
        self.auto_adjust = auto_adjust
        self.current_strategy = None
        self.memory_level = MemoryLevel.NORMAL
        
        # 策略实例映射
        self.policy_instances: Dict[str, CachePolicy] = {}
        
        # 策略性能指标
        self.strategy_metrics: Dict[str, Dict[str, Any]] = {}
        
        # 加载配置
        self._load_config()
        
        # 自动选择初始策略
        if self.auto_adjust:
            self._update_memory_level()
            self._auto_select_strategy()
        
        logger.info(f"缓存策略管理器初始化完成，当前内存级别: {self.memory_level.name}")
    
    def _load_config(self) -> None:
        """加载缓存策略配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"缓存策略配置文件不存在: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                logger.debug("成功加载缓存策略配置")
                
            # 解析策略配置
            if "strategies" in self.config:
                for strategy_data in self.config["strategies"]:
                    name = strategy_data.get("name")
                    if name:
                        self.strategies[name] = StrategyConfig(
                            name=name,
                            description=strategy_data.get("description", ""),
                            implementation=strategy_data.get("implementation", "LRUPolicy"),
                            default_max_items=strategy_data.get("default_max_items", 5),
                            parameters=strategy_data.get("parameters", {}),
                            suitable_for=strategy_data.get("suitable_for", ""),
                            priority=strategy_data.get("priority", 0)
                        )
            
            # 解析设备特定配置
            if "device_specific" in self.config:
                for device_name, device_data in self.config["device_specific"].items():
                    self.device_configs[device_name] = DeviceConfig(
                        default_strategy=device_data.get("default_strategy", "lru"),
                        max_items=device_data.get("max_items", 5),
                        warm_up_items=device_data.get("warm_up_items", []),
                        parameters=device_data.get("parameters", {})
                    )
            
            # 解析模型特定配置
            if "model_specific" in self.config and self.model_name:
                for model_name, model_data in self.config["model_specific"].items():
                    self.model_configs[model_name] = DeviceConfig(
                        default_strategy=model_data.get("default_strategy", "lru"),
                        max_items=model_data.get("max_items", 5),
                        warm_up_items=model_data.get("warm_up_items", []),
                        parameters=model_data.get("parameters", {})
                    )
            
            # 解析内存阈值
            if "auto_select_thresholds" in self.config:
                self.thresholds = self.config["auto_select_thresholds"]
                
            logger.info(f"缓存策略配置解析完成: {len(self.strategies)} 个策略定义")
            
        except Exception as e:
            logger.error(f"加载缓存策略配置失败: {str(e)}")
    
    def _update_memory_level(self) -> None:
        """更新内存级别"""
        # 获取可用内存（MB）
        available_memory = psutil.virtual_memory().available // (1024 * 1024)
        
        # 根据阈值确定内存级别
        if self.thresholds.get("critical") and available_memory <= self.thresholds["critical"]:
            self.memory_level = MemoryLevel.CRITICAL
        elif self.thresholds.get("low") and available_memory <= self.thresholds["low"]:
            self.memory_level = MemoryLevel.LOW
        elif self.thresholds.get("normal") and available_memory <= self.thresholds["normal"]:
            self.memory_level = MemoryLevel.NORMAL
        else:
            self.memory_level = MemoryLevel.HIGH
    
    def _get_device_config(self) -> Optional[DeviceConfig]:
        """获取当前设备配置
        
        根据内存级别选择对应的设备配置
        
        Returns:
            Optional[DeviceConfig]: 设备配置，如果不存在返回None
        """
        device_map = {
            MemoryLevel.CRITICAL: "low_memory",
            MemoryLevel.LOW: "low_memory",
            MemoryLevel.NORMAL: "medium_memory",
            MemoryLevel.HIGH: "high_memory"
        }
        
        device_type = device_map.get(self.memory_level)
        if device_type and device_type in self.device_configs:
            return self.device_configs[device_type]
        
        return None
    
    def _get_model_config(self) -> Optional[DeviceConfig]:
        """获取当前模型配置
        
        Returns:
            Optional[DeviceConfig]: 模型配置，如果不存在返回None
        """
        if self.model_name and self.model_name in self.model_configs:
            return self.model_configs[self.model_name]
        
        return None
    
    def _auto_select_strategy(self) -> str:
        """根据当前状态自动选择策略
        
        优先级：模型特定配置 > 设备配置 > 全局默认配置
        
        Returns:
            str: 选择的策略名称
        """
        # 优先使用模型特定配置
        model_config = self._get_model_config()
        if model_config:
            self.current_strategy = model_config.default_strategy
            return self.current_strategy
        
        # 其次使用设备配置
        device_config = self._get_device_config()
        if device_config:
            self.current_strategy = device_config.default_strategy
            return self.current_strategy
        
        # 最后使用全局默认配置
        default_strategy = self.config.get("cache_settings", {}).get("default_strategy", "lru")
        self.current_strategy = default_strategy
        return self.current_strategy
    
    def get_policy(self, strategy_name: Optional[str] = None) -> CachePolicy:
        """获取策略实例
        
        如果没有指定策略名称，使用当前策略
        如果实例不存在，创建新实例
        
        Args:
            strategy_name: 策略名称，如果为None则使用当前策略
            
        Returns:
            CachePolicy: 缓存策略实例
        """
        # 确定要使用的策略名称
        name = strategy_name or self.current_strategy or "lru"
        
        # 如果实例已存在，直接返回
        if name in self.policy_instances:
            return self.policy_instances[name]
        
        # 获取策略配置
        strategy_config = self.strategies.get(name)
        if not strategy_config:
            logger.warning(f"策略配置不存在: {name}，使用默认LRU策略")
            self.policy_instances[name] = LRUPolicy(max_size=5)
            return self.policy_instances[name]
        
        # 获取设备/模型配置的缓存大小
        max_items = strategy_config.default_max_items
        parameters = strategy_config.parameters.copy()
        
        # 更新模型特定参数
        model_config = self._get_model_config()
        if model_config:
            max_items = model_config.max_items
            if name in model_config.parameters:
                parameters.update(model_config.parameters[name])
        
        # 更新设备特定参数
        device_config = self._get_device_config()
        if device_config:
            if not model_config:  # 只有在没有模型配置时才使用设备配置
                max_items = device_config.max_items
            if name in device_config.parameters:
                # 模型参数优先级更高，所以先应用设备参数
                device_params = device_config.parameters[name]
                parameters.update(device_params)
        
        # 创建策略实例
        try:
            # 使用工厂方法创建策略实例
            policy_type = strategy_config.implementation.replace("Policy", "").lower()
            policy = CachePolicyFactory.create_policy(
                policy_type=policy_type,
                max_size=max_items,
                **parameters
            )
            
            # 保存实例
            self.policy_instances[name] = policy
            logger.debug(f"创建策略实例成功: {name}, 最大缓存项: {max_items}")
            
            return policy
            
        except Exception as e:
            logger.error(f"创建策略实例失败: {name}, 错误: {str(e)}")
            # 返回默认LRU策略
            self.policy_instances[name] = LRUPolicy(max_size=max_items)
            return self.policy_instances[name]
    
    def switch_strategy(self, strategy_name: str) -> bool:
        """切换到指定策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            bool: 是否成功切换
        """
        if strategy_name not in self.strategies:
            logger.warning(f"策略不存在: {strategy_name}")
            return False
        
        self.current_strategy = strategy_name
        logger.info(f"已切换到策略: {strategy_name}")
        return True
    
    def get_warm_up_items(self) -> List[str]:
        """获取预热项目列表
        
        Returns:
            List[str]: 应该预加载的项目键列表
        """
        # 优先使用模型配置
        model_config = self._get_model_config()
        if model_config and model_config.warm_up_items:
            return model_config.warm_up_items
        
        # 其次使用设备配置
        device_config = self._get_device_config()
        if device_config and device_config.warm_up_items:
            return device_config.warm_up_items
        
        return []
    
    def update_metrics(self, strategy_name: str, metrics: Dict[str, Any]) -> None:
        """更新策略性能指标
        
        Args:
            strategy_name: 策略名称
            metrics: 性能指标数据
        """
        self.strategy_metrics[strategy_name] = metrics
    
    def get_metrics(self, strategy_name: Optional[str] = None) -> Dict[str, Any]:
        """获取策略性能指标
        
        Args:
            strategy_name: 策略名称，如果为None则返回所有策略的指标
            
        Returns:
            Dict[str, Any]: 性能指标数据
        """
        if strategy_name:
            return self.strategy_metrics.get(strategy_name, {})
        
        return self.strategy_metrics
    
    def adjust_strategy_if_needed(self) -> bool:
        """根据当前系统状态调整策略
        
        Returns:
            bool: 是否进行了策略调整
        """
        if not self.auto_adjust:
            return False
        
        # 更新内存级别
        old_level = self.memory_level
        self._update_memory_level()
        
        # 如果内存级别变化，重新选择策略
        if old_level != self.memory_level:
            old_strategy = self.current_strategy
            new_strategy = self._auto_select_strategy()
            
            # 如果策略发生变化，记录日志
            if old_strategy != new_strategy:
                logger.info(f"内存级别变化: {old_level.name} -> {self.memory_level.name}，"
                           f"自动切换策略: {old_strategy} -> {new_strategy}")
                return True
        
        return False
    
    def get_all_strategies(self) -> Dict[str, StrategyConfig]:
        """获取所有策略配置
        
        Returns:
            Dict[str, StrategyConfig]: 策略配置字典
        """
        return self.strategies
    
    def get_strategy_config(self, strategy_name: str) -> Optional[StrategyConfig]:
        """获取指定策略的配置
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            Optional[StrategyConfig]: 策略配置，如果不存在返回None
        """
        return self.strategies.get(strategy_name)
    
    def get_current_strategy_name(self) -> str:
        """获取当前策略名称
        
        Returns:
            str: 当前策略名称
        """
        return self.current_strategy or "lru" 