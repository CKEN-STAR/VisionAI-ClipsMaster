#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时错误监控看板

提供实时错误统计、分类、可视化和告警功能，用于在导出过程中监控错误状态
集成到UI界面，实现错误的实时反馈
"""

import os
import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from collections import defaultdict, Counter

# 尝试导入异常模块
try:
    from src.utils.exceptions import ClipMasterError, ErrorCode
except ImportError:
    # 如果无法导入，则使用基本异常
    ClipMasterError = Exception
    class ErrorCode:
        """简单的错误代码枚举"""
        GENERAL_ERROR = "GENERAL_ERROR"

# 设置日志记录器
logger = logging.getLogger("error_dashboard")


class LiveErrorMonitor:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """实时错误监控器
    
    实现错误的实时统计、分类和可视化功能
    支持与UI界面的集成，实现错误的实时反馈
    提供错误处理建议和自动恢复选项
    """
    
    def __init__(self):
        """初始化实时错误监控器"""
        # 错误统计数据
        self.errors = defaultdict(int)
        
        # 错误历史记录
        self.error_history = []
        
        # 错误类型分析
        self.error_categories = defaultdict(int)
        
        # 组件错误统计
        self.component_errors = defaultdict(int)
        
        # 时间序列数据
        self.time_series = []
        
        # 告警配置
        self.alert_thresholds = {
            "total": 10,       # 错误总数阈值
            "rate": 0.05,      # 错误率阈值(5%)
            "critical": 1       # 严重错误阈值
        }
        
        # 监控状态
        self.monitoring_active = False
        self.start_time = None
        self.update_time = None
        
        # 回调函数
        self.update_callbacks = []
        
        # 错误严重程度
        self.severity_levels = {
            "INFO": 0,
            "WARNING": 1,
            "ERROR": 2,
            "CRITICAL": 3
        }
        
        # 错误恢复建议
        self.recovery_suggestions = {
            "MODEL_ERROR": "检查模型文件完整性或尝试重新加载模型",
            "MEMORY_ERROR": "关闭其他应用释放内存或降低批处理大小",
            "FILE_NOT_FOUND": "检查文件路径或恢复缺失文件",
            "PERMISSION_DENIED": "检查文件权限或以管理员身份运行",
            "VALIDATION_ERROR": "检查输入数据格式是否符合要求",
            "TIMEOUT_ERROR": "增加超时时间或检查系统负载",
            "NETWORK_ERROR": "检查网络连接或稍后重试",
            "GENERAL_ERROR": "查看详细日志获取更多信息"
        }
        
        # 更新锁
        self._lock = threading.RLock()
        
        # 配置加载
        self._load_config()
        
        logger.info("实时错误监控器初始化完成")
    
    def _load_config(self) -> None:
        """加载配置
        
        从配置文件加载错误监控相关配置
        """
        config_path = os.path.join("configs", "error_dashboard.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # 更新告警阈值
                if "alert_thresholds" in config:
                    self.alert_thresholds.update(config["alert_thresholds"])
                
                # 更新错误恢复建议
                if "recovery_suggestions" in config:
                    self.recovery_suggestions.update(config["recovery_suggestions"])
                
                logger.info(f"已加载错误监控配置: {config_path}")
            except Exception as e:
                logger.warning(f"加载错误监控配置失败: {e}")
    
    def start_monitoring(self) -> None:
        """启动监控
        
        开始收集和分析错误数据
        """
        with self._lock:
            self.monitoring_active = True
            self.start_time = time.time()
            self.update_time = self.start_time
            logger.info("错误监控已启动")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """停止监控
        
        Returns:
            Dict[str, Any]: 监控统计结果
        """
        with self._lock:
            if self.monitoring_active:
                self.monitoring_active = False
                end_time = time.time()
                duration = end_time - self.start_time
                
                stats = {
                    "start_time": self.start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "total_errors": sum(self.errors.values()),
                    "error_types": dict(self.errors),
                    "error_categories": dict(self.error_categories),
                    "component_errors": dict(self.component_errors),
                    "error_rate": self._calculate_error_rate()
                }
                
                logger.info(f"错误监控已停止，持续时间: {duration:.2f}秒，总错误数: {stats['total_errors']}")
                return stats
            return {}
    
    def update_dashboard(self, error: Union[Exception, ClipMasterError, Dict[str, Any]]) -> None:
        """实时更新错误统计
        
        处理新的错误并更新统计数据
        
        Args:
            error: 错误对象或错误信息字典
        """
        with self._lock:
            # 确保监控处于活动状态
            if not self.monitoring_active:
                self.start_monitoring()
            
            # 更新时间
            current_time = time.time()
            self.update_time = current_time
            
            # 提取错误代码
            error_code = self._extract_error_code(error)
            error_phase = self._extract_error_phase(error)
            error_component = self._extract_error_component(error)
            error_severity = self._extract_error_severity(error)
            error_message = self._extract_error_message(error)
            
            # 更新错误计数
            self.errors[error_code] += 1
            
            # 更新组件错误统计
            if error_component:
                self.component_errors[error_component] += 1
            
            # 更新错误类别统计
            error_category = self._categorize_error(error_code)
            self.error_categories[error_category] += 1
            
            # 添加到时间序列
            self.time_series.append({
                "timestamp": current_time,
                "error_code": error_code,
                "phase": error_phase,
                "component": error_component,
                "severity": error_severity,
                "message": error_message
            })
            
            # 添加到错误历史
            self.error_history.append({
                "timestamp": current_time,
                "error_code": error_code,
                "phase": error_phase,
                "component": error_component,
                "severity": error_severity,
                "message": error_message,
                "suggestion": self._get_recovery_suggestion(error_code)
            })
            
            # 限制历史记录大小
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
            
            # 发送监控数据给UI
            self._send_metrics({
                "error_code": error_code,
                "phase": error_phase,
                "component": error_component,
                "severity": error_severity,
                "count": self.errors[error_code],
                "total": sum(self.errors.values()),
                "message": error_message,
                "suggestion": self._get_recovery_suggestion(error_code)
            })
            
            # 检查是否需要触发告警
            self._check_alerts()
            
            # 调用更新回调
            self._notify_callbacks()
    
    def _extract_error_code(self, error: Union[Exception, ClipMasterError, Dict[str, Any]]) -> str:
        """提取错误代码
        
        Args:
            error: 错误对象或错误信息字典
            
        Returns:
            str: 错误代码
        """
        if isinstance(error, dict) and "code" in error:
            return str(error["code"])
        
        if hasattr(error, "code"):
            code = getattr(error, "code")
            if hasattr(code, "name"):
                return code.name
            return str(code)
        
        if isinstance(error, ClipMasterError):
            return "GENERAL_ERROR"
        
        return error.__class__.__name__
    
    def _extract_error_phase(self, error: Union[Exception, ClipMasterError, Dict[str, Any]]) -> str:
        """提取错误阶段
        
        Args:
            error: 错误对象或错误信息字典
            
        Returns:
            str: 错误发生阶段
        """
        if isinstance(error, dict) and "phase" in error:
            return error["phase"]
        
        if hasattr(error, "phase"):
            return getattr(error, "phase")
        
        return "unknown"
    
    def _extract_error_component(self, error: Union[Exception, ClipMasterError, Dict[str, Any]]) -> str:
        """提取错误组件
        
        Args:
            error: 错误对象或错误信息字典
            
        Returns:
            str: 错误发生组件
        """
        if isinstance(error, dict) and "component" in error:
            return error["component"]
        
        if hasattr(error, "component"):
            return getattr(error, "component")
        
        return "unknown"
    
    def _extract_error_severity(self, error: Union[Exception, ClipMasterError, Dict[str, Any]]) -> str:
        """提取错误严重程度
        
        Args:
            error: 错误对象或错误信息字典
            
        Returns:
            str: 错误严重程度
        """
        if isinstance(error, dict) and "severity" in error:
            return error["severity"]
        
        if hasattr(error, "critical") and getattr(error, "critical"):
            return "CRITICAL"
        
        if hasattr(error, "severity"):
            return getattr(error, "severity")
        
        return "ERROR"
    
    def _extract_error_message(self, error: Union[Exception, ClipMasterError, Dict[str, Any]]) -> str:
        """提取错误消息
        
        Args:
            error: 错误对象或错误信息字典
            
        Returns:
            str: 错误消息
        """
        if isinstance(error, dict) and "message" in error:
            return error["message"]
        
        if hasattr(error, "message"):
            return getattr(error, "message")
        
        return str(error)
    
    def _categorize_error(self, error_code: str) -> str:
        """对错误进行分类
        
        Args:
            error_code: 错误代码
            
        Returns:
            str: 错误类别
        """
        if "MODEL" in error_code:
            return "MODEL"
        elif "MEMORY" in error_code:
            return "MEMORY"
        elif "FILE" in error_code:
            return "FILE"
        elif "NETWORK" in error_code:
            return "NETWORK"
        elif "PERMISSION" in error_code:
            return "PERMISSION"
        elif "TIMEOUT" in error_code:
            return "TIMEOUT"
        elif "VALIDATION" in error_code:
            return "VALIDATION"
        else:
            return "OTHER"
    
    def _get_recovery_suggestion(self, error_code: str) -> str:
        """获取错误恢复建议
        
        Args:
            error_code: 错误代码
            
        Returns:
            str: 恢复建议
        """
        # 尝试匹配完整错误代码
        if error_code in self.recovery_suggestions:
            return self.recovery_suggestions[error_code]
        
        # 尝试匹配错误类别
        for category, suggestion in self.recovery_suggestions.items():
            if category in error_code:
                return suggestion
        
        # 返回通用建议
        return self.recovery_suggestions.get("GENERAL_ERROR", "查看详细日志获取更多信息")
    
    def _calculate_error_rate(self) -> float:
        """计算错误率
        
        Returns:
            float: 错误率(0-1)
        """
        # TODO: 实现基于总处理数量的错误率计算
        return 0.0
    
    def _check_alerts(self) -> None:
        """检查是否需要触发告警"""
        total_errors = sum(self.errors.values())
        
        # 检查总错误数
        if total_errors >= self.alert_thresholds["total"]:
            self._trigger_alert("total_errors", f"错误总数({total_errors})超过阈值({self.alert_thresholds['total']})")
        
        # 检查错误率
        error_rate = self._calculate_error_rate()
        if error_rate >= self.alert_thresholds["rate"]:
            self._trigger_alert("error_rate", f"错误率({error_rate:.2%})超过阈值({self.alert_thresholds['rate']:.2%})")
        
        # 检查严重错误
        critical_errors = sum(1 for error in self.error_history if error["severity"] == "CRITICAL")
        if critical_errors >= self.alert_thresholds["critical"]:
            self._trigger_alert("critical_errors", f"严重错误数({critical_errors})超过阈值({self.alert_thresholds['critical']})")
    
    def _trigger_alert(self, alert_type: str, message: str) -> None:
        """触发告警
        
        Args:
            alert_type: 告警类型
            message: 告警消息
        """
        logger.warning(f"错误监控告警: {alert_type} - {message}")
        
        # TODO: 实现告警通知机制(UI弹窗、系统通知等)
    
    def _send_metrics(self, metrics: Dict[str, Any]) -> None:
        """发送指标数据
        
        将错误监控数据发送到UI或其他监控系统
        
        Args:
            metrics: 指标数据
        """
        # 这里实际应该集成到UI更新机制中
        # 示例仅记录日志，实际实现应根据具体UI框架选择合适的方式
        logger.debug(f"错误监控指标更新: {metrics}")
    
    def register_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册更新回调函数
        
        Args:
            callback: 回调函数，接收指标数据作为参数
        """
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """取消注册更新回调函数
        
        Args:
            callback: 已注册的回调函数
        """
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def _notify_callbacks(self) -> None:
        """通知所有回调函数"""
        metrics = self.get_dashboard_data()
        for callback in self.update_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"调用错误监控回调函数失败: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据
        
        Returns:
            Dict[str, Any]: 当前错误监控数据
        """
        with self._lock:
            current_time = time.time()
            uptime = current_time - self.start_time if self.start_time else 0
            last_update = current_time - self.update_time if self.update_time else 0
            
            # 错误趋势数据
            time_buckets = defaultdict(int)
            if self.time_series:
                # 按分钟分组
                for entry in self.time_series:
                    minute = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
                    time_buckets[minute] += 1
            
            # 最常见的错误
            top_errors = Counter({k: v for k, v in self.errors.items()}).most_common(5)
            
            # 最常见的错误组件
            top_components = Counter(self.component_errors).most_common(5)
            
            return {
                "monitoring_active": self.monitoring_active,
                "uptime": uptime,
                "last_update": last_update,
                "total_errors": sum(self.errors.values()),
                "error_types": dict(self.errors),
                "error_categories": dict(self.error_categories),
                "component_errors": dict(self.component_errors),
                "error_trend": dict(time_buckets),
                "top_errors": top_errors,
                "top_components": top_components,
                "recent_errors": self.error_history[-10:] if self.error_history else [],
                "error_rate": self._calculate_error_rate()
            }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要
        
        Returns:
            Dict[str, Any]: 错误摘要信息
        """
        with self._lock:
            total_errors = sum(self.errors.values())
            if not total_errors:
                return {"total_errors": 0, "status": "正常", "message": "未检测到错误"}
            
            # 查找最常见错误
            most_common_error, count = Counter(self.errors).most_common(1)[0] if self.errors else (None, 0)
            most_common_component, _ = Counter(self.component_errors).most_common(1)[0] if self.component_errors else ("unknown", 0)
            
            # 获取最新错误
            latest_error = self.error_history[-1] if self.error_history else None
            
            # 确定状态
            if any(error["severity"] == "CRITICAL" for error in self.error_history[-10:] if "severity" in error):
                status = "严重"
            elif total_errors > self.alert_thresholds["total"]:
                status = "警告"
            else:
                status = "注意"
            
            return {
                "total_errors": total_errors,
                "status": status,
                "most_common_error": most_common_error,
                "most_common_error_count": count,
                "most_common_component": most_common_component,
                "latest_error": latest_error,
                "suggestion": self._get_recovery_suggestion(most_common_error) if most_common_error else "",
                "message": f"检测到{total_errors}个错误，最常见: {most_common_error}" if most_common_error else f"检测到{total_errors}个错误"
            }


# 全局单例
_monitor_instance = None
_monitor_lock = threading.Lock()

def get_error_monitor() -> LiveErrorMonitor:
    """获取错误监控器实例
    
    Returns:
        LiveErrorMonitor: 错误监控器实例
    """
    global _monitor_instance
    
    if _monitor_instance is None:
        with _monitor_lock:
            if _monitor_instance is None:
                _monitor_instance = LiveErrorMonitor()
    
    return _monitor_instance


# 简单使用示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 获取监控器实例
    monitor = get_error_monitor()
    
    # 启动监控
    monitor.start_monitoring()
    
    # 模拟一些错误
    for i in range(5):
        # 模拟不同类型的错误
        if i % 3 == 0:
            # 使用异常对象
            try:
                raise ValueError("测试值错误")
            except ValueError as e:
                monitor.update_dashboard(e)
        elif i % 3 == 1:
            # 使用ClipMasterError
            error = type('ClipMasterError', (Exception,), {
                "code": "MODEL_ERROR",
                "phase": "loading",
                "component": "model_loader"
            })("模型加载失败")
            monitor.update_dashboard(error)
        else:
            # 使用字典
            monitor.update_dashboard({
                "code": "NETWORK_ERROR",
                "phase": "download",
                "component": "network",
                "severity": "WARNING",
                "message": "网络连接超时"
            })
        
        # 等待一秒
        time.sleep(1)
    
    # 获取仪表盘数据
    dashboard_data = monitor.get_dashboard_data()
    print("---- 错误监控仪表盘 ----")
    print(f"总错误数: {dashboard_data['total_errors']}")
    print(f"错误类型: {dashboard_data['error_types']}")
    print(f"组件错误: {dashboard_data['component_errors']}")
    
    # 停止监控
    stats = monitor.stop_monitoring()
    print(f"监控统计: {stats}") 