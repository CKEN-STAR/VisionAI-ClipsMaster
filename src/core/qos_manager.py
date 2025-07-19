"""QoS管理器模块

该模块实现了服务质量(Quality of Service)管理功能，主要职责包括：
1. 管理并调整视频处理服务质量参数
2. 与降级管理器协同工作，根据系统状态自动调整服务质量
3. 提供服务质量优先级策略实现
4. 监控和报告服务质量指标
"""

import os
import json
import time
import logging
import threading
from enum import Enum, auto
from typing import Dict, List, Any, Callable, Optional, Tuple

# 导入降级管理器
from src.core.degradation import DegradationManager, DegradationLevel

# 配置日志
logger = logging.getLogger("qos_manager")

class QoSPriority(Enum):
    """服务质量优先级策略"""
    SPEED = auto()       # 速度优先
    QUALITY = auto()     # 质量优先
    BALANCED = auto()    # 均衡模式
    EFFICIENCY = auto()  # 资源效率优先

class QoSManager:
    """服务质量管理器
    
    该类负责根据系统状态和用户偏好，调整视频处理的质量参数，
    并与降级管理器协同工作，确保系统在各种负载条件下都能提供可接受的服务质量。
    """
    
    def __init__(self, 
                 degradation_manager: Optional[DegradationManager] = None,
                 config_path: Optional[str] = None,
                 default_priority: QoSPriority = QoSPriority.BALANCED):
        """初始化QoS管理器
        
        Args:
            degradation_manager: 降级管理器实例，如果为None则创建新实例
            config_path: QoS配置文件路径
            default_priority: 默认QoS优先级策略
        """
        # 初始化降级管理器
        self.degradation_manager = degradation_manager or DegradationManager()
        
        # 设置默认优先级策略
        self.current_priority = default_priority
        
        # QoS参数和状态
        self.qos_params = {
            "fps": 30,                 # 帧率
            "resolution": "1080p",     # 分辨率
            "encoding_quality": 90,    # 编码质量(0-100)
            "max_batch_latency": 200,  # 最大批处理延迟(毫秒)
            "max_processing_time": 5,  # 最大处理时间(秒)
            "response_timeout": 10,    # 响应超时时间(秒)
            "enable_gpu_acceleration": True,  # 是否启用GPU加速
            "thread_pool_size": 4,     # 线程池大小
        }
        
        # 参数范围限制
        self.param_limits = {
            "fps": (10, 60),
            "encoding_quality": (50, 100),
            "max_batch_latency": (50, 500),
            "max_processing_time": (1, 30),
            "response_timeout": (5, 60),
            "thread_pool_size": (1, 16),
        }
        
        # 优先级策略配置
        self.priority_configs = {
            QoSPriority.SPEED: {
                "fps": 60,
                "resolution": "720p",
                "encoding_quality": 75,
                "max_batch_latency": 100, 
                "max_processing_time": 2,
                "response_timeout": 5,
                "enable_gpu_acceleration": True,
                "thread_pool_size": 8,
            },
            QoSPriority.QUALITY: {
                "fps": 30,
                "resolution": "1080p",
                "encoding_quality": 95,
                "max_batch_latency": 300,
                "max_processing_time": 10,
                "response_timeout": 15,
                "enable_gpu_acceleration": True,
                "thread_pool_size": 4,
            },
            QoSPriority.BALANCED: {
                "fps": 30,
                "resolution": "1080p",
                "encoding_quality": 90,
                "max_batch_latency": 200,
                "max_processing_time": 5,
                "response_timeout": 10,
                "enable_gpu_acceleration": True,
                "thread_pool_size": 4,
            },
            QoSPriority.EFFICIENCY: {
                "fps": 24,
                "resolution": "720p",
                "encoding_quality": 85,
                "max_batch_latency": 300,
                "max_processing_time": 8,
                "response_timeout": 15,
                "enable_gpu_acceleration": True,
                "thread_pool_size": 2,
            }
        }
        
        # 降级映射：将降级级别映射到优先级策略
        self.degradation_priority_map = {
            DegradationLevel.NORMAL: QoSPriority.BALANCED,
            DegradationLevel.WARNING: QoSPriority.EFFICIENCY,
            DegradationLevel.CRITICAL: QoSPriority.SPEED,
            DegradationLevel.EMERGENCY: QoSPriority.SPEED,
        }
        
        # 降级级别对应的参数调整
        self.degradation_adjustments = {
            DegradationLevel.WARNING: {
                "fps": -5,
                "encoding_quality": -10,
                "thread_pool_size": -1,
            },
            DegradationLevel.CRITICAL: {
                "fps": -10,
                "encoding_quality": -20,
                "resolution": "720p", 
                "thread_pool_size": -2,
                "enable_gpu_acceleration": True,
            },
            DegradationLevel.EMERGENCY: {
                "fps": -15,
                "encoding_quality": -30,
                "resolution": "480p",
                "thread_pool_size": 1,
                "enable_gpu_acceleration": True,
            }
        }
        
        # 性能指标
        self.metrics = {
            "avg_response_time": 0,
            "avg_processing_time": 0,
            "dropped_frames": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "degradation_events": 0,
            "qos_adjustments": 0,  # 新增: QoS调整次数
            "last_update_time": time.time(),
        }
        
        # 加载配置
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        
        # 注册降级回调
        self._register_degradation_callbacks()
        
        # 监控线程
        self.monitor_thread = None
        self.monitoring = False
        self.monitor_interval = 10  # 默认10秒检查一次
        
        # 回调函数
        self.qos_callbacks = []
        
        logger.info("QoS管理器初始化完成，当前优先级策略: %s", self.current_priority.name)
    
    def load_config(self, config_path: str) -> bool:
        """从配置文件加载QoS配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新参数范围
            if "param_limits" in config:
                self.param_limits.update(config["param_limits"])
                
            # 更新优先级策略配置
            if "priority_configs" in config:
                for priority_name, values in config["priority_configs"].items():
                    try:
                        priority = QoSPriority[priority_name.upper()]
                        self.priority_configs[priority].update(values)
                    except (KeyError, ValueError):
                        logger.warning("未知的优先级策略: %s", priority_name)
            
            # 更新降级调整配置
            if "degradation_adjustments" in config:
                for level_name, values in config["degradation_adjustments"].items():
                    try:
                        level = DegradationLevel[level_name.upper()]
                        self.degradation_adjustments[level].update(values)
                    except (KeyError, ValueError):
                        logger.warning("未知的降级级别: %s", level_name)
            
            logger.info("成功从 %s 加载QoS配置", config_path)
            return True
            
        except Exception as e:
            logger.error("加载QoS配置失败: %s", str(e))
            return False
    
    def _register_degradation_callbacks(self):
        """注册降级管理器回调函数"""
        for level in DegradationLevel:
            self.degradation_manager.register_callback(
                level, 
                lambda state, level=level: self._handle_degradation(level, state)
            )
        logger.debug("已注册所有降级级别的回调函数")
    
    def _handle_degradation(self, level: DegradationLevel, state: Dict[str, Any]):
        """处理降级事件
        
        Args:
            level: 降级级别
            state: 降级状态
        """
        logger.info("收到降级事件: %s，调整QoS参数", level.name)
        
        # 记录降级事件
        self.metrics["degradation_events"] += 1
        
        # 切换到降级对应的优先级策略
        mapped_priority = self.degradation_priority_map.get(level, self.current_priority)
        
        # 应用降级调整
        self.set_priority(mapped_priority)
        
        # 添加额外的降级调整
        if level in self.degradation_adjustments:
            adjustments = self.degradation_adjustments[level]
            current_params = self.get_qos_params()
            
            for param, value in adjustments.items():
                if param in current_params:
                    if isinstance(value, (int, float)) and param in self.param_limits:
                        # 对于数值型调整，视为增量调整
                        new_value = current_params[param] + value
                        # 确保在参数范围内
                        min_val, max_val = self.param_limits[param]
                        new_value = max(min_val, min(new_value, max_val))
                        current_params[param] = new_value
                    else:
                        # 对于非数值型调整，直接设置
                        current_params[param] = value
            
            # 更新参数
            self._update_params(current_params)
        
        # 通知回调
        self._notify_qos_change({
            "priority": mapped_priority.name,
            "degradation_level": level.name,
            "params": self.qos_params,
            "reason": "system_degradation",
            "timestamp": time.time()
        })
    
    def set_priority(self, priority: QoSPriority) -> bool:
        """设置QoS优先级策略
        
        Args:
            priority: 要设置的优先级策略
            
        Returns:
            bool: 设置是否成功
        """
        if priority not in self.priority_configs:
            logger.error("无效的优先级策略: %s", priority)
            return False
        
        # 更新当前优先级
        self.current_priority = priority
        
        # 获取优先级对应的配置
        priority_config = self.priority_configs[priority]
        
        # 更新参数
        self._update_params(priority_config)
        
        logger.info("QoS优先级已切换至: %s", priority.name)
        
        # 通知回调
        self._notify_qos_change({
            "priority": priority.name,
            "params": self.qos_params,
            "reason": "priority_change",
            "timestamp": time.time()
        })
        
        return True
    
    def _update_params(self, params: Dict[str, Any]):
        """更新QoS参数
        
        Args:
            params: 要更新的参数字典
        """
        for param, value in params.items():
            if param in self.qos_params:
                # 检查参数范围（如果有定义）
                if param in self.param_limits and isinstance(value, (int, float)):
                    min_val, max_val = self.param_limits[param]
                    value = max(min_val, min(value, max_val))
                
                # 更新参数
                self.qos_params[param] = value
    
    def get_qos_params(self) -> Dict[str, Any]:
        """获取当前QoS参数
        
        Returns:
            Dict: 当前QoS参数
        """
        return self.qos_params.copy()
    
    def set_param(self, param: str, value: Any) -> bool:
        """设置单个QoS参数
        
        Args:
            param: 参数名
            value: 参数值
            
        Returns:
            bool: 设置是否成功
        """
        if param not in self.qos_params:
            logger.error("未知的QoS参数: %s", param)
            return False
        
        # 检查参数范围（如果有定义）
        if param in self.param_limits and isinstance(value, (int, float)):
            min_val, max_val = self.param_limits[param]
            if value < min_val or value > max_val:
                logger.warning(
                    "参数 %s 的值 %s 超出范围 [%s, %s]，将被调整", 
                    param, value, min_val, max_val
                )
                value = max(min_val, min(value, max_val))
        
        # 更新参数
        old_value = self.qos_params[param]
        self.qos_params[param] = value
        
        logger.info("QoS参数 %s 从 %s 更新为 %s", param, old_value, value)
        
        # 通知回调
        self._notify_qos_change({
            "param": param,
            "old_value": old_value,
            "new_value": value,
            "reason": "manual_change",
            "timestamp": time.time()
        })
        
        return True
    
    def get_current_priority(self) -> QoSPriority:
        """获取当前QoS优先级策略
        
        Returns:
            QoSPriority: 当前优先级策略
        """
        return self.current_priority
    
    def update_metric(self, metric: str, value: Any):
        """更新性能指标
        
        Args:
            metric: 指标名
            value: 指标值
        """
        if metric in self.metrics:
            self.metrics[metric] = value
            self.metrics["last_update_time"] = time.time()
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            Dict: 当前性能指标
        """
        return self.metrics.copy()
    
    def register_qos_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """注册QoS变更回调函数
        
        Args:
            callback: 回调函数，接收变更信息字典作为参数
        """
        if callback not in self.qos_callbacks:
            self.qos_callbacks.append(callback)
            return True
        return False
    
    def _notify_qos_change(self, change_info: Dict[str, Any]):
        """通知QoS变更
        
        Args:
            change_info: 变更信息字典
        """
        # 更新调整计数
        self.metrics["qos_adjustments"] += 1
        
        for callback in self.qos_callbacks:
            try:
                callback(change_info)
            except Exception as e:
                logger.error("执行QoS回调函数时出错: %s", str(e))
    
    def start_monitoring(self, interval: int = 10) -> bool:
        """启动QoS监控
        
        Args:
            interval: 监控间隔（秒）
            
        Returns:
            bool: 启动是否成功
        """
        if self.monitoring:
            logger.warning("QoS监控已在运行中")
            return False
        
        self.monitor_interval = interval
        self.monitoring = True
        
        def monitor_loop():
            logger.info("QoS监控线程已启动，间隔: %d秒", interval)
            while self.monitoring:
                try:
                    self._check_qos()
                except Exception as e:
                    logger.error("QoS监控检查时出错: %s", str(e))
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(
            target=monitor_loop,
            name="QoSMonitorThread",
            daemon=True
        )
        self.monitor_thread.start()
        return True
    
    def stop_monitoring(self) -> bool:
        """停止QoS监控
        
        Returns:
            bool: 停止是否成功
        """
        if not self.monitoring:
            logger.warning("QoS监控未在运行")
            return False
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            logger.info("QoS监控线程已停止")
        
        return True
    
    def _check_qos(self):
        """检查服务质量状态并进行必要的调整"""
        # 计算关键指标
        success_rate = 0
        avg_response_time = self.metrics["avg_response_time"]
        
        total_requests = self.metrics["successful_requests"] + self.metrics["failed_requests"]
        if total_requests > 0:
            success_rate = (self.metrics["successful_requests"] / total_requests) * 100
        
        # 服务质量状态评估
        qos_status = "good"
        if success_rate < 90 or avg_response_time > self.qos_params["response_timeout"]:
            qos_status = "poor"
        elif success_rate < 95 or avg_response_time > (self.qos_params["response_timeout"] * 0.8):
            qos_status = "moderate"
        
        logger.debug(
            "QoS状态: %s, 成功率: %.2f%%, 平均响应时间: %.2f秒", 
            qos_status, success_rate, avg_response_time
        )
        
        # 根据服务质量状态进行调整
        if qos_status == "poor" and self.degradation_manager.current_level == DegradationLevel.NORMAL:
            # 如果服务质量较差但系统未降级，切换到效率优先策略
            if self.current_priority != QoSPriority.EFFICIENCY:
                logger.warning("服务质量较差，切换到效率优先模式")
                self.set_priority(QoSPriority.EFFICIENCY)
        elif qos_status == "good" and self.current_priority == QoSPriority.EFFICIENCY:
            # 如果服务质量良好，可以恢复到平衡模式
            degradation_level = self.degradation_manager.current_level
            if degradation_level == DegradationLevel.NORMAL:
                logger.info("服务质量良好，恢复到平衡模式")
                self.set_priority(QoSPriority.BALANCED)
    
    def get_recommended_params(self) -> Dict[str, Any]:
        """获取当前系统状态下推荐的QoS参数
        
        这个方法基于当前系统状态和降级级别，计算最优的QoS参数设置。
        
        Returns:
            Dict: 推荐的QoS参数
        """
        # 获取当前降级级别
        degradation_level = self.degradation_manager.current_level
        
        # 获取当前性能指标
        metrics = self.get_metrics()
        
        # 基于优先级策略的基础参数
        recommended = self.priority_configs[self.current_priority].copy()
        
        # 根据降级级别调整
        if degradation_level != DegradationLevel.NORMAL and degradation_level in self.degradation_adjustments:
            adjustments = self.degradation_adjustments[degradation_level]
            for param, adj_value in adjustments.items():
                if param in recommended and isinstance(adj_value, (int, float)) and param in self.param_limits:
                    # 对于数值型调整，视为增量调整
                    new_value = recommended[param] + adj_value
                    # 确保在参数范围内
                    min_val, max_val = self.param_limits[param]
                    recommended[param] = max(min_val, min(new_value, max_val))
                else:
                    # 对于非数值型调整，直接设置
                    recommended[param] = adj_value
        
        # 根据性能指标进行智能调整
        avg_response_time = metrics.get("avg_response_time", 0)
        if avg_response_time > recommended["response_timeout"] * 0.9:
            # 如果响应时间接近超时，降低批处理延迟
            recommended["max_batch_latency"] = max(
                self.param_limits["max_batch_latency"][0],
                recommended["max_batch_latency"] * 0.8
            )
        
        return recommended
    
    def apply_recommended_params(self) -> bool:
        """应用推荐的QoS参数
        
        Returns:
            bool: 应用是否成功
        """
        recommended = self.get_recommended_params()
        self._update_params(recommended)
        
        logger.info("已应用推荐的QoS参数: %s", recommended)
        
        # 通知回调
        self._notify_qos_change({
            "params": recommended,
            "reason": "auto_optimization",
            "timestamp": time.time()
        })
        
        return True
    
    def get_state(self) -> Dict[str, Any]:
        """获取QoS管理器的完整状态
        
        Returns:
            Dict: 包含当前优先级、参数和指标的状态字典
        """
        return {
            "priority": self.current_priority.name,
            "degradation_level": self.degradation_manager.current_level.name,
            "params": self.get_qos_params(),
            "metrics": self.get_metrics(),
            "timestamp": time.time()
        }
    
    def reset(self) -> bool:
        """重置QoS管理器到默认状态
        
        Returns:
            bool: 重置是否成功
        """
        # 重置到平衡策略
        self.set_priority(QoSPriority.BALANCED)
        
        # 重置性能指标
        for metric in self.metrics:
            if metric != "last_update_time":
                self.metrics[metric] = 0
        self.metrics["last_update_time"] = time.time()
        
        logger.info("QoS管理器已重置到默认状态")
        return True
    
    def export_config(self, file_path: str) -> bool:
        """导出当前QoS配置到文件
        
        Args:
            file_path: 要导出的文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            # 准备配置数据
            config = {
                "param_limits": self.param_limits,
                "priority_configs": {
                    priority.name.lower(): config 
                    for priority, config in self.priority_configs.items()
                },
                "degradation_adjustments": {
                    level.name.lower(): adjustments
                    for level, adjustments in self.degradation_adjustments.items()
                }
            }
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info("QoS配置已导出到文件: %s", file_path)
            return True
            
        except Exception as e:
            logger.error("导出QoS配置失败: %s", str(e))
            return False 