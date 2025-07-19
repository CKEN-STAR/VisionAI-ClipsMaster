#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网络故障注入模块 - 提供各类网络问题模拟功能
用于测试系统在网络不稳定或断网情况下的恢复能力
"""

import os
import time
import random
import socket
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from unittest.mock import patch

import logging
logger = logging.getLogger(__name__)

from .core import FaultInjector


class NetworkLatencyInjector(FaultInjector):
    """网络延迟注入器"""
    
    def __init__(self, 
                 min_latency: float = 0.1, 
                 max_latency: float = 2.0, 
                 jitter: bool = True,
                 probability: float = 0.2, 
                 enabled: bool = True):
        """
        初始化网络延迟注入器
        
        Args:
            min_latency: 最小延迟时间(秒)
            max_latency: 最大延迟时间(秒)
            jitter: 是否添加抖动(随机延迟)
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.min_latency = min_latency
        self.max_latency = max_latency
        self.jitter = jitter
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入网络延迟
        
        Args:
            context: 上下文信息
        """
        base_latency = random.uniform(self.min_latency, self.max_latency)
        
        if self.jitter:
            jitter_value = base_latency * random.uniform(0.1, 0.3) * (1 if random.random() > 0.5 else -1)
            latency = max(0, base_latency + jitter_value)
        else:
            latency = base_latency
            
        logger.debug(f"注入网络延迟: {latency:.2f}秒 - {context}")
        time.sleep(latency)
    
    @classmethod
    def as_socket_decorator(cls, min_latency=0.1, max_latency=1.0, jitter=True, probability=0.3):
        """
        创建Socket操作的延迟装饰器
        
        Args:
            min_latency: 最小延迟时间(秒)
            max_latency: 最大延迟时间(秒)
            jitter: 是否添加抖动
            probability: 应用延迟的概率
            
        Returns:
            Callable: 装饰器函数
        """
        injector = cls(min_latency, max_latency, jitter, probability)
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                injector.try_inject({"socket_op": func.__name__})
                return func(*args, **kwargs)
            return wrapper
        
        return decorator


class PacketLossInjector(FaultInjector):
    """数据包丢失注入器"""
    
    def __init__(self, 
                 loss_rate: float = 0.1, 
                 burst_loss: bool = False,
                 burst_loss_size: int = 3,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化数据包丢失注入器
        
        Args:
            loss_rate: 丢包率 (0.0到1.0之间)
            burst_loss: 是否启用突发丢包
            burst_loss_size: 突发丢包大小(连续丢弃的包数)
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.loss_rate = loss_rate
        self.burst_loss = burst_loss
        self.burst_loss_size = burst_loss_size
        self.current_burst = 0
    
    def should_drop_packet(self) -> bool:
        """
        判断是否应该丢弃当前数据包
        
        Returns:
            bool: 是否应该丢弃
        """
        if self.burst_loss:
            if self.current_burst > 0:
                self.current_burst -= 1
                return True
            elif random.random() < self.loss_rate:
                self.current_burst = self.burst_loss_size - 1
                return True
        else:
            return random.random() < self.loss_rate
        
        return False
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入数据包丢失
        
        Args:
            context: 上下文信息
            
        Raises:
            ConnectionError: 当模拟数据包丢失时抛出
        """
        if self.should_drop_packet():
            logger.debug(f"注入数据包丢失 - {context}")
            raise ConnectionError("Simulated packet loss")
    
    @classmethod
    def patch_socket_methods(cls, loss_rate=0.1, burst_loss=False, duration=30):
        """
        临时替换Socket方法以模拟丢包
        
        Args:
            loss_rate: 丢包率
            burst_loss: 是否启用突发丢包
            duration: 持续时间(秒)
            
        Returns:
            Callable: 上下文管理器
        """
        injector = cls(loss_rate=loss_rate, burst_loss=burst_loss)
        
        # 保存原始方法
        original_sendall = socket.socket.sendall
        original_send = socket.socket.send
        original_recv = socket.socket.recv
        
        def patched_sendall(self, data, *args, **kwargs):
            if injector.should_drop_packet():
                logger.debug("模拟sendall丢包")
                return None
            return original_sendall(self, data, *args, **kwargs)
        
        def patched_send(self, data, *args, **kwargs):
            if injector.should_drop_packet():
                logger.debug("模拟send丢包")
                return len(data)  # 假装发送成功
            return original_send(self, data, *args, **kwargs)
        
        def patched_recv(self, bufsize, *args, **kwargs):
            if injector.should_drop_packet():
                logger.debug("模拟recv丢包")
                return b""  # 返回空数据
            return original_recv(self, bufsize, *args, **kwargs)
        
        # 应用补丁
        socket.socket.sendall = patched_sendall
        socket.socket.send = patched_send
        socket.socket.recv = patched_recv
        
        # 设置定时器来恢复原始方法
        def restore_methods():
            logger.debug("恢复Socket原始方法")
            socket.socket.sendall = original_sendall
            socket.socket.send = original_send
            socket.socket.recv = original_recv
        
        timer = threading.Timer(duration, restore_methods)
        timer.daemon = True
        timer.start()
        
        logger.debug(f"应用Socket补丁模拟丢包，持续{duration}秒")


class ConnectionResetInjector(FaultInjector):
    """连接重置注入器"""
    
    def __init__(self, 
                 reset_type: str = "random",
                 probability: float = 0.05, 
                 enabled: bool = True):
        """
        初始化连接重置注入器
        
        Args:
            reset_type: 重置类型，可选["random", "after_receive", "during_send"]
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.reset_type = reset_type
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入连接重置故障
        
        Args:
            context: 上下文信息，包含操作类型
            
        Raises:
            ConnectionResetError: 当模拟连接重置时抛出
        """
        op_type = context.get("op_type", "unknown") if context else "unknown"
        
        should_reset = False
        if self.reset_type == "random":
            should_reset = True
        elif self.reset_type == "after_receive" and op_type in ["recv", "recvfrom"]:
            should_reset = True
        elif self.reset_type == "during_send" and op_type in ["send", "sendall", "sendto"]:
            should_reset = True
        
        if should_reset:
            logger.debug(f"注入连接重置: {self.reset_type} - {op_type}")
            raise ConnectionResetError("Connection reset by peer (simulated)")


class DNSFailureInjector(FaultInjector):
    """DNS解析失败注入器"""
    
    def __init__(self, 
                 failure_mode: str = "timeout",
                 failure_domains: List[str] = None,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化DNS解析失败注入器
        
        Args:
            failure_mode: 失败模式，可选["timeout", "not_found", "temporary"]
            failure_domains: 特定失败的域名列表，如果为None则应用于所有域名
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.failure_mode = failure_mode
        self.failure_domains = failure_domains or []
    
    def should_affect_domain(self, hostname: str) -> bool:
        """
        判断是否应该影响指定域名
        
        Args:
            hostname: 主机名
            
        Returns:
            bool: 是否应该影响
        """
        if not self.failure_domains:
            return True
        
        return any(domain in hostname for domain in self.failure_domains)
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入DNS解析失败
        
        Args:
            context: 上下文信息，必须包含hostname键
            
        Raises:
            socket.gaierror: 当模拟DNS失败时抛出
            socket.timeout: 当模拟DNS超时时抛出
        """
        if not context or "hostname" not in context:
            raise ValueError("上下文必须包含hostname键")
        
        hostname = context["hostname"]
        if not self.should_affect_domain(hostname):
            return
        
        logger.debug(f"注入DNS解析失败: {self.failure_mode} - {hostname}")
        
        if self.failure_mode == "timeout":
            raise socket.timeout("DNS lookup timed out (simulated)")
        elif self.failure_mode == "not_found":
            raise socket.gaierror(socket.EAI_NONAME, f"Name or service {hostname} not found (simulated)")
        elif self.failure_mode == "temporary":
            raise socket.gaierror(socket.EAI_AGAIN, f"Temporary failure in name resolution for {hostname} (simulated)")
        else:
            raise socket.gaierror(socket.EAI_FAIL, f"DNS server failure for {hostname} (simulated)")


class NetworkDisconnectInjector(FaultInjector):
    """网络断开注入器"""
    
    def __init__(self, 
                 disconnect_duration: float = 10.0,
                 connection_behavior: str = "fail",
                 probability: float = 0.05, 
                 enabled: bool = True):
        """
        初始化网络断开注入器
        
        Args:
            disconnect_duration: 断开持续时间(秒)
            connection_behavior: 连接行为，可选["fail", "timeout", "partial"]
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.disconnect_duration = disconnect_duration
        self.connection_behavior = connection_behavior
        self._disconnected = False
        self._disconnect_until = 0
        self._lock = threading.RLock()
    
    def is_disconnected(self) -> bool:
        """
        检查当前是否处于断开状态
        
        Returns:
            bool: 是否处于断开状态
        """
        with self._lock:
            if self._disconnected and time.time() > self._disconnect_until:
                self._disconnected = False
                logger.debug("网络连接已恢复")
            return self._disconnected
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入网络断开故障
        
        Args:
            context: 上下文信息
        """
        with self._lock:
            self._disconnected = True
            self._disconnect_until = time.time() + self.disconnect_duration
            
        logger.debug(f"注入网络断开故障: 持续{self.disconnect_duration}秒 - {context}")
        
        if self.connection_behavior == "fail":
            raise ConnectionError("Network disconnected (simulated)")
        elif self.connection_behavior == "timeout":
            raise socket.timeout("Network timeout (simulated)")
        elif self.connection_behavior == "partial":
            # 部分连接不抛出异常，但会在检查时表现为断开
            pass
    
    @classmethod
    def apply_patch(cls, disconnect_duration=10.0, behavior="fail", probability=0.1):
        """
        应用网络断开补丁
        
        Args:
            disconnect_duration: 断开持续时间(秒)
            behavior: 连接行为
            probability: 概率
            
        Returns:
            NetworkDisconnectInjector: 注入器实例
        """
        injector = cls(disconnect_duration, behavior, probability)
        
        # 保存原始方法
        original_socket = socket.socket
        original_connect = socket.socket.connect
        original_getaddrinfo = socket.getaddrinfo
        
        def patched_socket(*args, **kwargs):
            sock = original_socket(*args, **kwargs)
            if injector.should_trigger() and injector.try_inject():
                logger.debug("模拟网络断开: socket创建")
            return sock
        
        def patched_connect(self, *args, **kwargs):
            if injector.is_disconnected():
                if behavior == "fail":
                    raise ConnectionError("Network disconnected (simulated)")
                elif behavior == "timeout":
                    raise socket.timeout("Network timeout (simulated)")
            return original_connect(self, *args, **kwargs)
        
        def patched_getaddrinfo(*args, **kwargs):
            if injector.is_disconnected():
                raise socket.gaierror(socket.EAI_AGAIN, "Temporary failure in name resolution (simulated)")
            return original_getaddrinfo(*args, **kwargs)
        
        # 应用补丁
        socket.socket = patched_socket
        socket.socket.connect = patched_connect
        socket.getaddrinfo = patched_getaddrinfo
        
        # 设置定时器来恢复原始方法
        def restore_methods():
            logger.debug("恢复Socket原始方法")
            socket.socket = original_socket
            socket.socket.connect = original_connect
            socket.getaddrinfo = original_getaddrinfo
        
        timer = threading.Timer(disconnect_duration * 2, restore_methods)
        timer.daemon = True
        timer.start()
        
        return injector


class HTTPErrorInjector(FaultInjector):
    """HTTP错误注入器"""
    
    def __init__(self, 
                 error_codes: List[int] = None,
                 error_urls: List[str] = None,
                 probability: float = 0.1, 
                 enabled: bool = True):
        """
        初始化HTTP错误注入器
        
        Args:
            error_codes: HTTP错误代码列表
            error_urls: 特定会出错的URL列表，如果为None则应用于所有URL
            probability: 故障触发概率
            enabled: 是否启用故障注入器
        """
        super().__init__(probability, enabled)
        self.error_codes = error_codes or [400, 401, 403, 404, 500, 502, 503, 504]
        self.error_urls = error_urls or []
    
    def should_affect_url(self, url: str) -> bool:
        """
        判断是否应该影响指定URL
        
        Args:
            url: URL
            
        Returns:
            bool: 是否应该影响
        """
        if not self.error_urls:
            return True
        
        return any(pattern in url for pattern in self.error_urls)
    
    def inject_fault(self, context: Optional[Dict[str, Any]] = None) -> None:
        """
        注入HTTP错误
        
        Args:
            context: 上下文信息，必须包含url键
            
        Raises:
            ValueError: 如果上下文中没有url键
        """
        if not context or "url" not in context:
            raise ValueError("上下文必须包含url键")
        
        url = context["url"]
        if not self.should_affect_url(url):
            return
        
        error_code = random.choice(self.error_codes)
        logger.debug(f"注入HTTP错误: {error_code} - {url}")
        
        # 修改响应上下文
        response_ctx = context.get("response", {})
        response_ctx["status_code"] = error_code
        response_ctx["reason"] = f"Simulated HTTP Error: {error_code}"
        response_ctx["body"] = f"<html><body><h1>Error {error_code}</h1><p>Simulated error response.</p></body></html>"
        
        context["response"] = response_ctx
        context["simulated_error"] = True


class NetworkSimulator:
    """网络故障模拟器，组合多种网络故障注入器"""
    
    def __init__(self):
        """初始化网络故障模拟器"""
        self.injectors = {}
        
        # 默认创建所有注入器但禁用
        self.injectors["latency"] = NetworkLatencyInjector(enabled=False)
        self.injectors["packet_loss"] = PacketLossInjector(enabled=False)
        self.injectors["connection_reset"] = ConnectionResetInjector(enabled=False)
        self.injectors["dns_failure"] = DNSFailureInjector(enabled=False)
        self.injectors["disconnect"] = NetworkDisconnectInjector(enabled=False)
        self.injectors["http_error"] = HTTPErrorInjector(enabled=False)
    
    def configure(self, injector_name: str, **kwargs) -> None:
        """
        配置特定的注入器
        
        Args:
            injector_name: 注入器名称
            **kwargs: 配置参数
        
        Raises:
            ValueError: 如果注入器名称无效
        """
        if injector_name not in self.injectors:
            raise ValueError(f"无效的注入器名称: {injector_name}")
        
        # 创建新的注入器实例
        if injector_name == "latency":
            self.injectors[injector_name] = NetworkLatencyInjector(**kwargs)
        elif injector_name == "packet_loss":
            self.injectors[injector_name] = PacketLossInjector(**kwargs)
        elif injector_name == "connection_reset":
            self.injectors[injector_name] = ConnectionResetInjector(**kwargs)
        elif injector_name == "dns_failure":
            self.injectors[injector_name] = DNSFailureInjector(**kwargs)
        elif injector_name == "disconnect":
            self.injectors[injector_name] = NetworkDisconnectInjector(**kwargs)
        elif injector_name == "http_error":
            self.injectors[injector_name] = HTTPErrorInjector(**kwargs)
    
    def enable(self, injector_name: str) -> None:
        """
        启用特定的注入器
        
        Args:
            injector_name: 注入器名称
        
        Raises:
            ValueError: 如果注入器名称无效
        """
        if injector_name not in self.injectors:
            raise ValueError(f"无效的注入器名称: {injector_name}")
        
        self.injectors[injector_name].enabled = True
    
    def disable(self, injector_name: str) -> None:
        """
        禁用特定的注入器
        
        Args:
            injector_name: 注入器名称
        
        Raises:
            ValueError: 如果注入器名称无效
        """
        if injector_name not in self.injectors:
            raise ValueError(f"无效的注入器名称: {injector_name}")
        
        self.injectors[injector_name].enabled = False
    
    def enable_all(self) -> None:
        """启用所有注入器"""
        for name in self.injectors:
            self.injectors[name].enabled = True
    
    def disable_all(self) -> None:
        """禁用所有注入器"""
        for name in self.injectors:
            self.injectors[name].enabled = False
    
    def try_inject(self, context: Dict[str, Any]) -> bool:
        """
        尝试注入网络故障
        
        Args:
            context: 上下文信息
            
        Returns:
            bool: 是否注入了故障
        """
        injected = False
        for injector in self.injectors.values():
            if injector.enabled and injector.try_inject(context.copy()):
                injected = True
                break
        
        return injected


# 全局网络模拟器实例
network_simulator = NetworkSimulator()


def configure_poor_network():
    """配置低质量网络环境"""
    network_simulator.configure("latency", min_latency=0.5, max_latency=3.0, jitter=True, probability=0.7, enabled=True)
    network_simulator.configure("packet_loss", loss_rate=0.1, burst_loss=True, probability=0.3, enabled=True)
    network_simulator.configure("connection_reset", reset_type="random", probability=0.05, enabled=True)
    logger.info("已配置低质量网络环境")


def configure_intermittent_network():
    """配置间歇性网络环境"""
    network_simulator.configure("disconnect", disconnect_duration=5.0, probability=0.1, enabled=True)
    network_simulator.configure("latency", min_latency=0.1, max_latency=1.0, jitter=True, probability=0.3, enabled=True)
    network_simulator.configure("dns_failure", failure_mode="temporary", probability=0.1, enabled=True)
    logger.info("已配置间歇性网络环境")


def configure_offline_simulation():
    """配置离线模拟环境"""
    network_simulator.configure("disconnect", disconnect_duration=3600.0, connection_behavior="fail", probability=1.0, enabled=True)
    NetworkDisconnectInjector.apply_patch(disconnect_duration=3600.0, behavior="fail", probability=1.0)
    logger.info("已配置离线模拟环境") 