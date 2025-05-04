"""系统资源熔断降级管理模块

该模块负责在系统资源紧张时实施服务降级策略，以确保系统稳定性。
主要功能包括：
1. 多级别的服务降级策略
2. 自动根据系统资源状态触发降级
3. 与系统监控组件集成
4. 优雅的服务恢复机制
"""

import os
import json
import threading
import time
from enum import Enum
from typing import Dict, List, Optional, Callable, Union, Any
from loguru import logger

# 导入相关模块
from src.utils.memory_guard import MemoryGuard
from src.utils.resource_predictor import ResourcePredictor
try:
    import psutil
except ImportError:
    psutil = None

# 定义降级级别枚举
class DegradationLevel(Enum):
    """服务降级级别"""
    NORMAL = "normal"       # 正常服务级别
    WARNING = "warning"     # 警告级别 - 轻微降级
    CRITICAL = "critical"   # 危险级别 - 中度降级
    EMERGENCY = "emergency" # 紧急级别 - 最大降级

# 配置各级别对应的资源阈值
DEFAULT_THRESHOLDS = {
    "memory": {
        DegradationLevel.WARNING.value: 0.75,    # 75%
        DegradationLevel.CRITICAL.value: 0.85,   # 85%
        DegradationLevel.EMERGENCY.value: 0.95,  # 95%
    },
    "gpu": {
        DegradationLevel.WARNING.value: 0.70,    # 70%
        DegradationLevel.CRITICAL.value: 0.80,   # 80%
        DegradationLevel.EMERGENCY.value: 0.90,  # 90%
    },
    "cpu": {
        DegradationLevel.WARNING.value: 0.80,    # 80%
        DegradationLevel.CRITICAL.value: 0.90,   # 90%
        DegradationLevel.EMERGENCY.value: 0.95,  # 95%
    },
    "disk": {
        DegradationLevel.WARNING.value: 0.85,    # 85%
        DegradationLevel.CRITICAL.value: 0.90,   # 90%
        DegradationLevel.EMERGENCY.value: 0.95,  # 95%
    }
}

# 定义各级别的降级配置
DEFAULT_DEGRADATION_CONFIGS = {
    # 正常级别配置
    DegradationLevel.NORMAL.value: {
        "video_quality": "high",       # 1080p
        "model_precision": "q4_k_m",   # Q4_K_M
        "batch_size": 8,               # 正常批处理大小
        "max_concurrent": 4,           # 最大并发数
        "context_length": 8192,        # 上下文长度
        "timeout": 30,                 # 超时时间(秒)
    },
    
    # 警告级别配置
    DegradationLevel.WARNING.value: {
        "video_quality": "medium",     # 720p
        "model_precision": "q4_k_m",   # 保持Q4_K_M
        "batch_size": 4,               # 减小批处理大小
        "max_concurrent": 2,           # 减少并发
        "context_length": 4096,        # 减少上下文长度
        "timeout": 45,                 # 增加超时时间
    },
    
    # 危险级别配置
    DegradationLevel.CRITICAL.value: {
        "video_quality": "medium",     # 720p
        "model_precision": "q3_k",     # 降级到Q3_K
        "batch_size": 2,               # 进一步减小批处理
        "max_concurrent": 1,           # 单一并发
        "context_length": 2048,        # 进一步减少上下文
        "timeout": 60,                 # 进一步增加超时
    },
    
    # 紧急级别配置
    DegradationLevel.EMERGENCY.value: {
        "video_quality": "low",        # 480p
        "model_precision": "q2_k",     # 最低精度Q2_K
        "batch_size": 1,               # 最小批处理
        "max_concurrent": 1,           # 单一并发
        "context_length": 1024,        # 最小上下文
        "timeout": 120,                # 最长超时
    }
}

# 定义服务恢复策略
RECOVERY_DELAY = {
    DegradationLevel.WARNING.value: 30,    # 警告级别恢复延迟30秒
    DegradationLevel.CRITICAL.value: 60,   # 危险级别恢复延迟60秒
    DegradationLevel.EMERGENCY.value: 180, # 紧急级别恢复延迟180秒
}

class DegradationManager:
    """降级服务管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化降级管理器
        
        Args:
            config_path: 配置文件路径，默认为None使用内置默认配置
        """
        # 加载配置
        self._load_config(config_path)
        
        # 当前降级状态
        self.current_level = DegradationLevel.NORMAL
        self.states = self.configs[self.current_level.value].copy()
        
        # 降级历史
        self.degradation_history = []
        
        # 自动监控状态
        self.monitoring = False
        self.monitor_thread = None
        self.last_degradation_time = 0
        
        # 资源监控相关
        self.memory_guard = None
        self.resource_predictor = ResourcePredictor()
        
        # 降级回调函数
        self.callbacks = {}
        
        # 恢复定时器
        self.recovery_timer = None
        
        # 初始化资源监控
        self._init_resource_monitoring()
        
        logger.info("降级服务管理器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> None:
        """加载配置
        
        Args:
            config_path: 配置文件路径
        """
        # 默认配置
        self.thresholds = DEFAULT_THRESHOLDS
        self.configs = DEFAULT_DEGRADATION_CONFIGS
        
        # 尝试从配置文件加载
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新阈值配置
                if 'thresholds' in config:
                    self.thresholds.update(config['thresholds'])
                
                # 更新降级配置
                if 'degradation_configs' in config:
                    self.configs.update(config['degradation_configs'])
                
                logger.info(f"已从 {config_path} 加载降级配置")
            except Exception as e:
                logger.error(f"加载降级配置失败: {e}，使用默认配置")
    
    def _init_resource_monitoring(self) -> None:
        """初始化资源监控"""
        try:
            # 初始化内存守卫
            self.memory_guard = MemoryGuard()
            
            # 注册回调函数
            if hasattr(self.memory_guard, 'register_callback'):
                self.memory_guard.register_callback("warning", 
                    lambda stats: self.degrade(DegradationLevel.WARNING))
                self.memory_guard.register_callback("critical", 
                    lambda stats: self.degrade(DegradationLevel.CRITICAL))
                self.memory_guard.register_callback("emergency", 
                    lambda stats: self.degrade(DegradationLevel.EMERGENCY))
                
                logger.info("已注册内存监控回调函数")
        except Exception as e:
            logger.warning(f"初始化资源监控失败: {e}")
    
    def get_state(self) -> Dict:
        """获取当前服务状态
        
        Returns:
            Dict: 当前状态配置
        """
        return {
            "level": self.current_level.value,
            "config": self.states.copy(),
            "timestamp": time.time(),
            "monitoring": self.monitoring
        }
    
    def degrade(self, level: Union[DegradationLevel, str]) -> bool:
        """根据指定级别降级服务
        
        Args:
            level: 降级级别，可以是DegradationLevel枚举或字符串
            
        Returns:
            bool: 降级是否成功
        """
        # 转换字符串为枚举
        if isinstance(level, str):
            try:
                level = DegradationLevel(level)
            except ValueError:
                logger.error(f"无效的降级级别: {level}")
                return False
        
        # 检查是否需要降级
        current_level_value = DegradationLevel[self.current_level.name].value
        target_level_value = DegradationLevel[level.name].value
        
        # 只有在目标级别低于当前级别时才降级
        # NORMAL > WARNING > CRITICAL > EMERGENCY
        if level.value not in self.configs:
            logger.error(f"未找到级别 {level.value} 的配置")
            return False
        
        # 更新状态
        previous_level = self.current_level
        self.current_level = level
        self.states = self.configs[level.value].copy()
        
        # 记录降级历史
        self.degradation_history.append({
            "timestamp": time.time(),
            "from_level": previous_level,
            "to_level": level,
            "reason": f"手动触发降级到 {level.value} 级别"
        })
        
        # 记录降级时间
        self.last_degradation_time = time.time()
        
        # 取消正在进行的恢复定时器
        if self.recovery_timer:
            self.recovery_timer.cancel()
            self.recovery_timer = None
        
        # 触发回调
        self._trigger_callbacks(level.value)
        
        logger.warning(f"服务降级: {previous_level.value} -> {level.value}")
        return True
    
    def register_callback(self, level: Union[str, DegradationLevel], callback: Callable[[Dict], None]) -> None:
        """注册降级回调函数
        
        Args:
            level: 降级级别
            callback: 回调函数，接收当前状态字典
        """
        if isinstance(level, DegradationLevel):
            level = level.value
        
        if level not in self.callbacks:
            self.callbacks[level] = []
        
        self.callbacks[level].append(callback)
        logger.info(f"已注册 {level} 级别的降级回调函数")
    
    def _trigger_callbacks(self, level: str) -> None:
        """触发指定级别的回调函数
        
        Args:
            level: 降级级别
        """
        if level in self.callbacks:
            current_state = self.get_state()
            for callback in self.callbacks[level]:
                try:
                    callback(current_state)
                except Exception as e:
                    logger.error(f"执行降级回调函数失败: {e}")
    
    def recover(self, force: bool = False) -> bool:
        """恢复服务到正常级别
        
        Args:
            force: 是否强制恢复，忽略冷却时间
            
        Returns:
            bool: 恢复是否成功
        """
        # 已经是正常级别
        if self.current_level == DegradationLevel.NORMAL:
            logger.info("服务已经处于正常级别，无需恢复")
            return True
        
        # 检查恢复冷却时间
        if not force:
            elapsed = time.time() - self.last_degradation_time
            required_delay = RECOVERY_DELAY.get(self.current_level.value, 60)
            
            if elapsed < required_delay:
                logger.info(f"恢复冷却中，还需等待 {required_delay - elapsed:.1f} 秒")
                return False
        
        # 记录恢复前的级别
        previous_level = self.current_level
        
        # 执行恢复
        self.current_level = DegradationLevel.NORMAL
        self.states = self.configs[DegradationLevel.NORMAL.value].copy()
        
        # 记录恢复历史
        self.degradation_history.append({
            "timestamp": time.time(),
            "from_level": previous_level.value,
            "to_level": DegradationLevel.NORMAL.value,
            "reason": "手动恢复服务" if force else "自动恢复服务"
        })
        
        # 触发回调
        self._trigger_callbacks(DegradationLevel.NORMAL.value)
        
        logger.info(f"服务已恢复: {previous_level.value} -> {DegradationLevel.NORMAL.value}")
        return True
    
    def start_monitoring(self, interval: int = 30) -> bool:
        """启动自动监控
        
        Args:
            interval: 监控间隔（秒）
            
        Returns:
            bool: 是否成功启动
        """
        if self.monitoring:
            logger.warning("监控已在运行")
            return False
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self._check_resources()
                    self._check_auto_recovery()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"资源监控异常: {e}")
                    time.sleep(5)  # 出错后短暂等待
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"已启动资源监控，间隔 {interval} 秒")
        return True
    
    def stop_monitoring(self) -> bool:
        """停止自动监控
        
        Returns:
            bool: 是否成功停止
        """
        if not self.monitoring:
            logger.warning("监控未运行")
            return False
        
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
        
        logger.info("已停止资源监控")
        return True
    
    def _check_resources(self) -> None:
        """检查系统资源使用情况"""
        if not psutil:
            return
        
        try:
            # 获取系统资源使用情况
            memory = psutil.virtual_memory()
            memory_usage = memory.percent / 100
            
            cpu_usage = psutil.cpu_percent() / 100
            
            # 获取GPU使用情况（如果有）
            gpu_usage = 0
            try:
                import torch
                if torch.cuda.is_available():
                    # 使用nvidia-smi或其他方式获取GPU使用率
                    # 这里简化处理
                    gpu_usage = 0.7  # 默认值
            except (ImportError, Exception):
                pass
            
            # 获取磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent / 100
            
            # 确定应该的降级级别
            target_level = DegradationLevel.NORMAL
            
            # 根据内存使用率确定级别
            if memory_usage >= self.thresholds["memory"][DegradationLevel.EMERGENCY.value]:
                target_level = DegradationLevel.EMERGENCY
            elif memory_usage >= self.thresholds["memory"][DegradationLevel.CRITICAL.value]:
                target_level = DegradationLevel.CRITICAL
            elif memory_usage >= self.thresholds["memory"][DegradationLevel.WARNING.value]:
                target_level = DegradationLevel.WARNING
            
            # 根据CPU使用率调整级别（只考虑升级，不考虑降级）
            if cpu_usage >= self.thresholds["cpu"][DegradationLevel.EMERGENCY.value]:
                if target_level.value > DegradationLevel.EMERGENCY.value:
                    target_level = DegradationLevel.EMERGENCY
            elif cpu_usage >= self.thresholds["cpu"][DegradationLevel.CRITICAL.value]:
                if target_level.value > DegradationLevel.CRITICAL.value:
                    target_level = DegradationLevel.CRITICAL
            elif cpu_usage >= self.thresholds["cpu"][DegradationLevel.WARNING.value]:
                if target_level.value > DegradationLevel.WARNING.value:
                    target_level = DegradationLevel.WARNING
            
            # 执行降级（如果需要）
            if target_level != DegradationLevel.NORMAL and target_level != self.current_level:
                self.degrade(target_level)
                reason = f"系统资源使用率过高: 内存={memory_usage:.1%}, CPU={cpu_usage:.1%}"
                logger.warning(f"自动降级触发: {reason}")
                
                # 更新最后一次降级历史的原因
                if self.degradation_history:
                    self.degradation_history[-1]["reason"] = reason
            
        except Exception as e:
            logger.error(f"资源检查失败: {e}")
    
    def _check_auto_recovery(self) -> None:
        """检查是否可以自动恢复"""
        # 如果当前不是正常级别，检查是否可以恢复
        if self.current_level != DegradationLevel.NORMAL:
            elapsed = time.time() - self.last_degradation_time
            required_delay = RECOVERY_DELAY.get(self.current_level.value, 60)
            
            if elapsed >= required_delay:
                # 检查当前资源使用情况
                try:
                    if psutil:
                        memory = psutil.virtual_memory()
                        memory_usage = memory.percent / 100
                        
                        # 只有当资源使用率低于警告阈值时才恢复
                        warning_threshold = self.thresholds["memory"][DegradationLevel.WARNING.value]
                        if memory_usage < warning_threshold * 0.9:  # 添加10%的缓冲区
                            # 安排恢复
                            if self.recovery_timer is None:
                                logger.info("资源使用率正常，准备恢复服务")
                                self.recovery_timer = threading.Timer(5, self.recover)
                                self.recovery_timer.daemon = True
                                self.recovery_timer.start()
                except Exception as e:
                    logger.error(f"自动恢复检查失败: {e}")
    
    def get_history(self) -> List[Dict]:
        """获取降级历史记录
        
        Returns:
            List[Dict]: 降级历史记录
        """
        return self.degradation_history.copy()
    
    def reset(self) -> None:
        """重置管理器状态"""
        self.current_level = DegradationLevel.NORMAL
        self.states = self.configs[DegradationLevel.NORMAL.value].copy()
        
        if self.recovery_timer:
            self.recovery_timer.cancel()
            self.recovery_timer = None
        
        logger.info("降级管理器已重置")
    
    def force_degrade(self, level: Union[str, DegradationLevel], reason: str) -> bool:
        """强制降级服务，用于调试和测试
        
        Args:
            level: 降级级别
            reason: 降级原因
            
        Returns:
            bool: 降级是否成功
        """
        if isinstance(level, str):
            try:
                level = DegradationLevel(level)
            except ValueError:
                logger.error(f"无效的降级级别: {level}")
                return False
        
        if level.value not in self.configs:
            logger.error(f"未找到级别 {level.value} 的配置")
            return False
        
        # 记录上一级别
        previous_level = self.current_level
        
        # 更新状态
        self.current_level = level
        self.states = self.configs[level.value].copy()
        
        # 记录降级历史
        self.degradation_history.append({
            "timestamp": time.time(),
            "from_level": previous_level.value,
            "to_level": level.value,
            "reason": reason
        })
        
        # 记录降级时间
        self.last_degradation_time = time.time()
        
        # 触发回调
        self._trigger_callbacks(level.value)
        
        logger.warning(f"强制服务降级: {previous_level.value} -> {level.value}, 原因: {reason}")
        return True
    
    def get_degradation_config(self, level: Union[str, DegradationLevel] = None) -> Dict:
        """获取指定级别的降级配置
        
        Args:
            level: 降级级别，默认为当前级别
            
        Returns:
            Dict: 降级配置
        """
        if level is None:
            return self.states.copy()
        
        if isinstance(level, DegradationLevel):
            level = level.value
        
        if level in self.configs:
            return self.configs[level].copy()
        
        logger.error(f"未找到级别 {level} 的配置")
        return {} 