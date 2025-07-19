#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存压力与熔断集成
将内存压力检测与熔断管理系统集成
"""

import logging
import threading
from typing import Optional, Dict, List, Any

# 导入内存熔断管理器
from src.memory.fuse_manager import get_fuse_manager, FuseLevel
# 导入内存压力检测器
from src.fuse.pressure_detector import get_pressure_detector

# 设置日志
logger = logging.getLogger("memory_integration")

class MemoryIntegrationManager:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """
    内存压力与熔断集成管理器
    协调内存压力检测和熔断管理系统的协同工作
    """
    
    def __init__(self):
        """初始化集成管理器"""
        self._lock = threading.RLock()
        self._initialized = False
        
        # 默认压力阈值设置
        self._pressure_thresholds = {
            FuseLevel.WARNING: 70.0,    # 警告级别对应压力阈值
            FuseLevel.CRITICAL: 85.0,   # 临界级别对应压力阈值
            FuseLevel.EMERGENCY: 95.0   # 紧急级别对应压力阈值
        }
        
        # 是否启用自动熔断触发
        self._auto_trigger_enabled = True
        
        # 是否启用趋势预测
        self._prediction_enabled = True
        
        # 预测窗口（秒）
        self._prediction_window = 30
        
        # 内部标志
        self._last_trigger_level = FuseLevel.NORMAL
        
        logger.info("内存集成管理器初始化完成")
    
    def initialize(self) -> bool:
        """
        初始化集成
        
        Returns:
            是否成功初始化
        """
        with self._lock:
            if self._initialized:
                return True
            
            try:
                # 获取实例
                self._fuse_manager = get_fuse_manager()
                self._pressure_detector = get_pressure_detector()
                
                # 注册回调函数
                self._setup_callbacks()
                
                self._initialized = True
                logger.info("内存集成系统初始化成功")
                return True
            except Exception as e:
                logger.error(f"内存集成系统初始化失败: {str(e)}")
                return False
    
    def _setup_callbacks(self) -> None:
        """设置回调函数"""
        # 注册压力阈值回调
        for level, threshold in self._pressure_thresholds.items():
            self._pressure_detector.register_pressure_callback(
                threshold, 
                lambda p, lvl=level: self._on_pressure_threshold(p, lvl)
            )
        
        # 注册压力快速上升回调
        self._pressure_detector.register_escalation_callback(
            self._on_pressure_escalation
        )
    
    def _on_pressure_threshold(self, pressure: float, level: FuseLevel) -> None:
        """
        压力阈值回调处理
        
        Args:
            pressure: 当前压力值
            level: 对应的熔断级别
        """
        if not self._auto_trigger_enabled:
            logger.info(f"压力达到{level.name}级别阈值 ({pressure:.1f})，但自动触发已禁用")
            return
        
        # 只有当级别高于上次触发级别时才触发
        if level.value > self._last_trigger_level.value:
            logger.warning(f"压力达到{level.name}级别阈值 ({pressure:.1f})，触发熔断")
            self._fuse_manager.force_trigger(level)
            self._last_trigger_level = level
    
    def _on_pressure_escalation(self, pressure: float) -> None:
        """
        压力快速上升回调处理
        
        Args:
            pressure: 当前压力值
        """
        logger.warning(f"检测到内存压力快速上升 ({pressure:.1f})")
        
        # 如果启用预测
        if self._prediction_enabled:
            # 预测未来压力
            future_pressure = self._pressure_detector.predict_pressure(
                self._prediction_window
            )
            
            # 根据预测决定是否提前触发熔断
            for level, threshold in sorted(
                self._pressure_thresholds.items(), 
                key=lambda x: x[1],
                reverse=True
            ):
                if future_pressure >= threshold and level.value > self._last_trigger_level.value:
                    logger.warning(f"基于趋势预测({future_pressure:.1f})提前触发{level.name}级别熔断")
                    self._fuse_manager.force_trigger(level)
                    self._last_trigger_level = level
                    break
    
    def start(self) -> bool:
        """
        启动集成系统
        
        Returns:
            是否成功启动
        """
        with self._lock:
            if not self._initialized and not self.initialize():
                return False
            
            # 启动熔断管理器监控
            self._fuse_manager.start_monitoring()
            
            # 启动压力检测器监控
            self._pressure_detector.start_monitoring()
            
            logger.info("内存集成系统已启动")
            return True
    
    def stop(self) -> bool:
        """
        停止集成系统
        
        Returns:
            是否成功停止
        """
        with self._lock:
            if not self._initialized:
                return False
            
            # 停止监控
            self._fuse_manager.stop_monitoring()
            self._pressure_detector.stop_monitoring()
            
            logger.info("内存集成系统已停止")
            return True
    
    def set_pressure_threshold(self, level: FuseLevel, threshold: float) -> None:
        """
        设置压力阈值
        
        Args:
            level: 熔断级别
            threshold: 压力阈值 (0-100)
        """
        with self._lock:
            # 取消旧阈值的回调
            if level in self._pressure_thresholds:
                old_threshold = self._pressure_thresholds[level]
                self._pressure_detector.unregister_pressure_callback(
                    old_threshold,
                    lambda p, lvl=level: self._on_pressure_threshold(p, lvl)
                )
            
            # 设置新阈值
            self._pressure_thresholds[level] = threshold
            
            # 注册新阈值的回调
            if self._initialized:
                self._pressure_detector.register_pressure_callback(
                    threshold,
                    lambda p, lvl=level: self._on_pressure_threshold(p, lvl)
                )
            
            logger.info(f"设置{level.name}级别压力阈值为{threshold}")
    
    def enable_auto_trigger(self, enabled: bool = True) -> None:
        """
        启用/禁用自动触发熔断
        
        Args:
            enabled: 是否启用
        """
        self._auto_trigger_enabled = enabled
        logger.info(f"{'启用' if enabled else '禁用'}自动触发熔断")
    
    def enable_prediction(self, enabled: bool = True) -> None:
        """
        启用/禁用趋势预测
        
        Args:
            enabled: 是否启用
        """
        self._prediction_enabled = enabled
        logger.info(f"{'启用' if enabled else '禁用'}趋势预测")
    
    def set_prediction_window(self, seconds: int) -> None:
        """
        设置预测窗口
        
        Args:
            seconds: 预测窗口（秒）
        """
        self._prediction_window = max(5, seconds)  # 至少5秒
        logger.info(f"设置预测窗口为{self._prediction_window}秒")
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            状态信息字典
        """
        with self._lock:
            if not self._initialized:
                return {"initialized": False}
            
            current_pressure = self._pressure_detector.get_current_pressure()
            current_fuse_level = self._fuse_manager.get_current_level()
            
            slope, r_squared = self._pressure_detector.get_trend()
            trend_direction = "上升" if slope > 0 else "下降" if slope < 0 else "稳定"
            
            # 预测未来压力
            predicted_pressure = None
            if self._prediction_enabled:
                predicted_pressure = self._pressure_detector.predict_pressure(
                    self._prediction_window
                )
            
            return {
                "initialized": True,
                "current_pressure": current_pressure,
                "current_fuse_level": current_fuse_level.name,
                "auto_trigger_enabled": self._auto_trigger_enabled,
                "prediction_enabled": self._prediction_enabled,
                "trend_direction": trend_direction,
                "trend_slope": slope,
                "trend_confidence": r_squared,
                "predicted_pressure": predicted_pressure,
                "pressure_thresholds": {
                    level.name: threshold
                    for level, threshold in self._pressure_thresholds.items()
                }
            }
    
    def reset(self) -> None:
        """重置状态"""
        with self._lock:
            self._last_trigger_level = FuseLevel.NORMAL
            logger.info("内存集成系统状态已重置")


# 全局单例
_integration_manager = None

def get_integration_manager() -> MemoryIntegrationManager:
    """
    获取集成管理器单例
    
    Returns:
        集成管理器实例
    """
    global _integration_manager
    
    if _integration_manager is None:
        _integration_manager = MemoryIntegrationManager()
        
    return _integration_manager


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试集成管理器
    manager = get_integration_manager()
    
    # 初始化并启动
    if manager.initialize():
        manager.start()
        
        # 设置阈值
        from src.memory.fuse_manager import FuseLevel
        manager.set_pressure_threshold(FuseLevel.WARNING, 75.0)
        manager.set_pressure_threshold(FuseLevel.CRITICAL, 85.0)
        manager.set_pressure_threshold(FuseLevel.EMERGENCY, 95.0)
        
        # 启用预测
        manager.enable_prediction(True)
        manager.set_prediction_window(30)
        
        # 打印状态
        import json
        status = manager.get_status()
        print(json.dumps(status, indent=2))
        
        # 等待用户中断
        try:
            print("内存集成系统运行中，按Ctrl+C停止...")
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("停止集成系统")
            
        # 停止系统
        manager.stop() 