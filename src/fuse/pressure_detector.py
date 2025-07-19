#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存压力检测器 - VisionAI-ClipsMaster
实时检测内存压力和快速上升趋势
"""

import os
import time
import threading
import logging
import numpy as np
import psutil
from collections import deque
from typing import List, Optional, Tuple, Dict, Any, Callable

# 设置日志
logger = logging.getLogger("memory_pressure")

class MemoryPressureDetector:
    """内存压力检测器，计算实时内存压力指数，检测快速上升趋势"""
    
    def __init__(self, maxlen: int = 60):
        """
        初始化内存压力检测器
        
        Args:
            maxlen: 采样窗口大小，默认保存60个样本（秒）
        """
        self.samples = deque(maxlen=maxlen)  # 60秒滑动窗口
        self._lock = threading.RLock()
        self._stop_monitor = threading.Event()
        self._monitor_thread = None
        self._callback = None
        self._last_pressure = 0
        self._escalation_callbacks = []
        self._pressure_callbacks = {}  # 按压力阈值注册回调
        
        # 填充初始值
        current_usage = self._get_memory_usage()
        for _ in range(maxlen):
            self.samples.append(current_usage)
            
        logger.info(f"内存压力检测器初始化完成，窗口大小: {maxlen}秒")
        
    def _get_memory_usage(self) -> float:
        """
        获取当前内存使用率
        
        Returns:
            内存使用百分比 (0-100)
        """
        return psutil.virtual_memory().percent
    
    def update(self) -> float:
        """
        更新内存使用率样本
        
        Returns:
            当前内存压力指数
        """
        with self._lock:
            current_usage = self._get_memory_usage()
            self.samples.append(current_usage)
            pressure = self.calculate_pressure()
            
            # 检查并触发压力阈值回调
            self._check_pressure_callbacks(pressure)
            
            # 检查压力升高
            if self.is_escalating():
                self._trigger_escalation_callbacks(pressure)
                
            self._last_pressure = pressure
            return pressure
    
    def calculate_pressure(self) -> float:
        """
        计算内存压力指数 (0-100)
        
        使用加权算法，近期样本权重更高，返回0-100的指数值
        
        Returns:
            内存压力指数，范围0-100
        """
        if not self.samples:
            return 0
        
        # 当前内存使用率
        current_usage = self.samples[-1]
        
        # 最近5秒的平均使用率
        recent_samples = list(self.samples)[-5:] if len(self.samples) >= 5 else list(self.samples)
        recent_avg = sum(recent_samples) / len(recent_samples)
        
        # 压力指数 = 当前内存使用率 × 0.4 + 5秒钟平均 × 0.6
        pressure = current_usage * 0.4 + recent_avg * 0.6
        
        # 对压力值进行指数加权，突出高压力区域的差异
        if pressure > 80:
            # 在高内存区域，压力增长更快
            pressure = 80 + (pressure - 80) * 1.5
        
        # 确保范围在0-100之间
        pressure = min(max(pressure, 0), 100)
        
        return pressure
    
    def is_escalating(self) -> bool:
        """
        检测压力是否快速上升
        
        使用最近5个样本进行趋势分析，检测内存使用是否快速增长
        
        Returns:
            如果在短时间内增长超过5%，返回True
        """
        if len(self.samples) < 5:
            return False
        
        # 获取最近5个样本
        recent = list(self.samples)[-5:]
        
        # 使用多项式拟合检测趋势
        x = np.arange(5)
        coeffs = np.polyfit(x, recent, 1)
        
        # 斜率系数，正值表示上升趋势
        slope = coeffs[0]
        
        # 检查5秒内是否上升超过5%
        return slope * 5 > 5  # 5秒内斜率>5%
    
    def get_trend(self, window: int = 30) -> Tuple[float, float]:
        """
        计算内存使用趋势
        
        Args:
            window: 趋势计算窗口大小（秒）
            
        Returns:
            (斜率, 拟合度R^2值)
        """
        with self._lock:
            if len(self.samples) < window:
                window = len(self.samples)
                
            if window < 2:
                return 0.0, 0.0
                
            # 获取最近的样本
            recent = list(self.samples)[-window:]
            x = np.arange(window)
            
            # 线性拟合
            coeffs = np.polyfit(x, recent, 1)
            slope = coeffs[0]  # 斜率
            
            # 计算R^2拟合度
            p = np.poly1d(coeffs)
            y_pred = p(x)
            y_mean = np.mean(recent)
            ssreg = np.sum((y_pred - y_mean) ** 2)
            sstot = np.sum((recent - y_mean) ** 2)
            r_squared = ssreg / sstot if sstot != 0 else 0
            
            return slope, r_squared
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        启动定期监控线程
        
        Args:
            interval: 更新间隔（秒）
        """
        with self._lock:
            if self._monitor_thread is None or not self._monitor_thread.is_alive():
                self._stop_monitor.clear()
                self._monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    args=(interval,),
                    daemon=True
                )
                self._monitor_thread.start()
                logger.info(f"内存压力监控已启动，更新间隔: {interval}秒")
    
    def stop_monitoring(self) -> None:
        """停止监控线程"""
        with self._lock:
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._stop_monitor.set()
                self._monitor_thread.join(timeout=5.0)
                logger.info("内存压力监控已停止")
    
    def _monitor_loop(self, interval: float) -> None:
        """
        监控循环
        
        Args:
            interval: 更新间隔（秒）
        """
        while not self._stop_monitor.is_set():
            try:
                pressure = self.update()
                if self._callback:
                    self._callback(pressure)
            except Exception as e:
                logger.error(f"内存压力监控异常: {str(e)}")
            
            # 等待下一次更新
            time.sleep(interval)
    
    def set_callback(self, callback: Callable[[float], None]) -> None:
        """
        设置压力更新回调函数
        
        Args:
            callback: 接收压力值的回调函数
        """
        self._callback = callback
    
    def register_escalation_callback(self, callback: Callable[[float], None]) -> None:
        """
        注册压力快速上升回调
        
        Args:
            callback: 当检测到压力快速上升时调用的回调函数
        """
        if callback not in self._escalation_callbacks:
            self._escalation_callbacks.append(callback)
    
    def unregister_escalation_callback(self, callback: Callable[[float], None]) -> bool:
        """
        注销压力快速上升回调
        
        Args:
            callback: 要注销的回调函数
            
        Returns:
            是否成功注销
        """
        if callback in self._escalation_callbacks:
            self._escalation_callbacks.remove(callback)
            return True
        return False
    
    def _trigger_escalation_callbacks(self, pressure: float) -> None:
        """
        触发压力快速上升回调
        
        Args:
            pressure: 当前压力值
        """
        for callback in self._escalation_callbacks:
            try:
                callback(pressure)
            except Exception as e:
                logger.error(f"执行压力上升回调异常: {str(e)}")
    
    def register_pressure_callback(self, threshold: float, callback: Callable[[float], None]) -> None:
        """
        注册压力阈值回调
        
        Args:
            threshold: 压力阈值 (0-100)
            callback: 当压力超过阈值时调用的回调函数
        """
        if threshold not in self._pressure_callbacks:
            self._pressure_callbacks[threshold] = []
        
        if callback not in self._pressure_callbacks[threshold]:
            self._pressure_callbacks[threshold].append(callback)
    
    def unregister_pressure_callback(self, threshold: float, callback: Callable[[float], None]) -> bool:
        """
        注销压力阈值回调
        
        Args:
            threshold: 压力阈值
            callback: 要注销的回调函数
            
        Returns:
            是否成功注销
        """
        if threshold in self._pressure_callbacks and callback in self._pressure_callbacks[threshold]:
            self._pressure_callbacks[threshold].remove(callback)
            if not self._pressure_callbacks[threshold]:
                del self._pressure_callbacks[threshold]
            return True
        return False
    
    def _check_pressure_callbacks(self, pressure: float) -> None:
        """
        检查并触发压力阈值回调
        
        Args:
            pressure: 当前压力值
        """
        for threshold, callbacks in self._pressure_callbacks.items():
            # 只有当压力从低于阈值变为高于阈值时触发
            if pressure >= threshold and self._last_pressure < threshold:
                for callback in callbacks:
                    try:
                        callback(pressure)
                    except Exception as e:
                        logger.error(f"执行压力阈值回调异常: {str(e)}")
    
    def get_pressure_history(self, seconds: int = None) -> List[float]:
        """
        获取压力历史数据
        
        Args:
            seconds: 获取的历史数据秒数，默认全部
            
        Returns:
            压力历史数据列表
        """
        with self._lock:
            samples = list(self.samples)
            if seconds is not None and seconds < len(samples):
                samples = samples[-seconds:]
            return samples
    
    def get_current_pressure(self) -> float:
        """
        获取当前压力值
        
        Returns:
            当前内存压力指数
        """
        with self._lock:
            return self.calculate_pressure()
    
    def predict_pressure(self, seconds_ahead: int = 30) -> float:
        """
        预测未来压力
        
        基于当前趋势预测未来压力值
        
        Args:
            seconds_ahead: 预测未来多少秒的压力
            
        Returns:
            预测的压力值
        """
        with self._lock:
            slope, r_squared = self.get_trend()
            
            # 如果拟合度太低，不进行预测
            if r_squared < 0.5:
                return self.calculate_pressure()
            
            # 基于斜率预测未来压力
            current = self.calculate_pressure()
            predicted = current + slope * seconds_ahead
            
            # 确保预测值在有效范围内
            predicted = min(max(predicted, 0), 100)
            
            return predicted


# 全局单例
_pressure_detector = None

def get_pressure_detector() -> MemoryPressureDetector:
    """
    获取压力检测器单例
    
    Returns:
        压力检测器实例
    """
    global _pressure_detector
    
    if _pressure_detector is None:
        _pressure_detector = MemoryPressureDetector()
        
    return _pressure_detector


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 测试压力检测器
    detector = get_pressure_detector()
    
    # 定义回调函数
    def pressure_callback(pressure):
        print(f"当前内存压力指数: {pressure:.1f}")
    
    def high_pressure_callback(pressure):
        print(f"警告：内存压力过高 ({pressure:.1f})")
    
    def escalation_callback(pressure):
        print(f"警告：内存压力快速上升 ({pressure:.1f})")
    
    # 注册回调
    detector.set_callback(pressure_callback)
    detector.register_pressure_callback(80, high_pressure_callback)
    detector.register_escalation_callback(escalation_callback)
    
    # 启动监控
    detector.start_monitoring(interval=1.0)
    
    # 等待一段时间
    print("监控内存压力，按Ctrl+C停止...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("停止监控")
    
    # 停止监控
    detector.stop_monitoring() 