#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时日志监控看板

提供系统运行状态的实时可视化监控界面，包括内存使用、成功率、异常检测等。
支持多种图表类型和实时更新机制。
"""

import os
import time
import datetime
import threading
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from collections import defaultdict, deque
import json
import re

from src.utils.logger import get_module_logger
from src.exporters.log_query import get_log_searcher, LogSearcher
from src.exporters.log_fingerprint import generate_log_fingerprint
from src.exporters.log_path import get_log_directory

# 模块日志记录器
logger = get_module_logger("log_dashboard")

# 定义图表类型
class ChartType:
    LINE = "line"
    BAR = "bar"
    GAUGE = "gauge"
    PIE = "pie"
    HEATMAP = "heatmap"
    TABLE = "table"
    METRIC = "metric"

# 定义警告级别
class AlertLevel:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Alert:
    """警报类"""
    
    def __init__(self, 
                 message: str, 
                 level: str = AlertLevel.INFO, 
                 source: str = None,
                 timestamp: float = None,
                 context: Dict[str, Any] = None):
        """
        初始化警报
        
        Args:
            message: 警报消息
            level: 警报级别
            source: 警报来源
            timestamp: 时间戳（如不提供则使用当前时间）
            context: 上下文信息
        """
        self.message = message
        self.level = level
        self.source = source
        self.timestamp = timestamp or time.time()
        self.context = context or {}
        self.acknowledged = False
        self.id = f"{int(self.timestamp)}-{hash(message) % 10000}"
    
    def acknowledge(self):
        """标记警报为已确认"""
        self.acknowledged = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "id": self.id,
            "message": self.message,
            "level": self.level,
            "source": self.source,
            "timestamp": self.timestamp,
            "datetime": datetime.datetime.fromtimestamp(self.timestamp).isoformat(),
            "context": self.context,
            "acknowledged": self.acknowledged
        }

class DashboardChart:
    """看板图表基类"""
    
    def __init__(self, 
                 name: str, 
                 chart_type: str,
                 title: str = None, 
                 description: str = None,
                 max_points: int = 100,
                 options: Dict[str, Any] = None):
        """
        初始化图表
        
        Args:
            name: 图表名称（标识符）
            chart_type: 图表类型
            title: 图表标题
            description: 图表描述
            max_points: 数据点最大数量
            options: 其他图表选项
        """
        self.name = name
        self.chart_type = chart_type
        self.title = title or name
        self.description = description
        self.max_points = max_points
        self.options = options or {}
        self.data = []
        self.last_update = time.time()
    
    def update(self, value):
        """更新图表数据
        
        Args:
            value: 新数据点
        """
        raise NotImplementedError("子类必须实现update方法")
    
    def clear(self):
        """清除图表数据"""
        self.data = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典表示"""
        return {
            "name": self.name,
            "type": self.chart_type,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "options": self.options,
            "last_update": self.last_update
        }

class LineChart(DashboardChart):
    """折线图"""
    
    def __init__(self, name: str, title: str = None, description: str = None, 
                 max_points: int = 100, options: Dict[str, Any] = None):
        """初始化折线图"""
        super().__init__(
            name=name,
            chart_type=ChartType.LINE,
            title=title,
            description=description,
            max_points=max_points,
            options=options
        )
        self.data = deque(maxlen=max_points)
    
    def update(self, value: Union[float, Tuple[float, float]]):
        """
        更新折线图数据
        
        Args:
            value: 新数据点，可以是单个值或(x,y)元组
        """
        self.last_update = time.time()
        
        if isinstance(value, tuple) and len(value) == 2:
            # 使用提供的X和Y值
            point = {"x": value[0], "y": value[1]}
        else:
            # 使用当前时间作为X值
            point = {"x": self.last_update, "y": value}
        
        self.data.append(point)
    
    def append(self, value: float):
        """添加新的数据点"""
        self.update(value)

class GaugeChart(DashboardChart):
    """仪表盘图表"""
    
    def __init__(self, name: str, title: str = None, description: str = None,
                 min_value: float = 0, max_value: float = 100, 
                 options: Dict[str, Any] = None):
        """
        初始化仪表盘
        
        Args:
            name: 图表名称
            title: 图表标题
            description: 图表描述
            min_value: 最小值
            max_value: 最大值
            options: 其他图表选项
        """
        super().__init__(
            name=name,
            chart_type=ChartType.GAUGE,
            title=title,
            description=description,
            options=options
        )
        self.min_value = min_value
        self.max_value = max_value
        self.value = 0
    
    def update(self, value: float):
        """
        更新仪表盘值
        
        Args:
            value: 新值
        """
        self.last_update = time.time()
        self.value = max(self.min_value, min(value, self.max_value))
        
    @property
    def data(self):
        """获取当前数据"""
        return {
            "value": self.value,
            "min": self.min_value,
            "max": self.max_value
        }

class BarChart(DashboardChart):
    """柱状图"""
    
    def __init__(self, name: str, title: str = None, description: str = None,
                categories: List[str] = None, options: Dict[str, Any] = None):
        """
        初始化柱状图
        
        Args:
            name: 图表名称
            title: 图表标题
            description: 图表描述
            categories: 分类标签
            options: 其他图表选项
        """
        super().__init__(
            name=name,
            chart_type=ChartType.BAR,
            title=title,
            description=description,
            options=options
        )
        self.categories = categories or []
        self.values = [0] * len(self.categories)
    
    def update(self, values: Dict[str, float]):
        """
        更新柱状图数据
        
        Args:
            values: 分类-值字典
        """
        self.last_update = time.time()
        
        # 处理新的分类
        for category in values:
            if category not in self.categories:
                self.categories.append(category)
                self.values.append(0)
        
        # 更新值
        for i, category in enumerate(self.categories):
            if category in values:
                self.values[i] = values[category]
    
    @property
    def data(self):
        """获取当前数据"""
        return {
            "categories": self.categories,
            "values": self.values
        }

class MetricValue(DashboardChart):
    """指标值显示"""
    
    def __init__(self, name: str, title: str = None, description: str = None,
                 unit: str = "", precision: int = 2, options: Dict[str, Any] = None):
        """
        初始化指标值
        
        Args:
            name: 指标名称
            title: 指标标题
            description: 指标描述
            unit: 单位
            precision: 精度（小数位数）
            options: 其他选项
        """
        super().__init__(
            name=name,
            chart_type=ChartType.METRIC,
            title=title,
            description=description,
            options=options
        )
        self.unit = unit
        self.precision = precision
        self.value = 0
        self.previous_value = 0
        self.history = deque(maxlen=10)  # 保存最近10个值
    
    def update(self, value: float):
        """
        更新指标值
        
        Args:
            value: 新值
        """
        self.last_update = time.time()
        self.previous_value = self.value
        self.value = value
        self.history.append((self.last_update, value))
    
    @property
    def data(self):
        """获取当前数据"""
        return {
            "value": round(self.value, self.precision),
            "previous": round(self.previous_value, self.precision),
            "unit": self.unit,
            "change": round(self.value - self.previous_value, self.precision) if self.previous_value else 0,
            "change_percent": round((self.value - self.previous_value) / max(0.0001, abs(self.previous_value)) * 100, 1) if self.previous_value else 0
        }

class AlertManager:
    """警报管理器"""
    
    def __init__(self, max_alerts: int = 100):
        """
        初始化警报管理器
        
        Args:
            max_alerts: 最大警报数量
        """
        self.alerts = deque(maxlen=max_alerts)
        self.alert_counts = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 0,
            AlertLevel.ERROR: 0,
            AlertLevel.CRITICAL: 0
        }
    
    def add_alert(self, alert: Alert) -> str:
        """
        添加新警报
        
        Args:
            alert: 警报对象
            
        Returns:
            警报ID
        """
        self.alerts.append(alert)
        self.alert_counts[alert.level] = self.alert_counts.get(alert.level, 0) + 1
        return alert.id
    
    def add(self, message: str, level: str = AlertLevel.INFO, source: str = None, 
            context: Dict[str, Any] = None) -> str:
        """
        创建并添加新警报
        
        Args:
            message: 警报消息
            level: 警报级别
            source: 警报来源
            context: 上下文信息
            
        Returns:
            警报ID
        """
        alert = Alert(message=message, level=level, source=source, context=context)
        return self.add_alert(alert)
    
    def acknowledge(self, alert_id: str) -> bool:
        """
        确认警报
        
        Args:
            alert_id: 警报ID
            
        Returns:
            是否成功确认
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledge()
                return True
        return False
    
    def get_active_alerts(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取活跃（未确认）的警报
        
        Args:
            level: 可选的警报级别过滤
            
        Returns:
            警报字典列表
        """
        active_alerts = []
        for alert in self.alerts:
            if alert.acknowledged:
                continue
                
            if level and alert.level != level:
                continue
                
            active_alerts.append(alert.to_dict())
        
        return active_alerts
    
    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """
        获取所有警报
        
        Returns:
            警报字典列表
        """
        return [alert.to_dict() for alert in self.alerts]
    
    def clear(self):
        """清除所有警报"""
        self.alerts.clear()
        for level in self.alert_counts:
            self.alert_counts[level] = 0
    
    def update(self, new_alerts: List[Alert]):
        """
        批量更新警报
        
        Args:
            new_alerts: 新警报列表
        """
        for alert in new_alerts:
            self.add_alert(alert)

class LiveLogMonitor:
    """实时日志监控器"""
    
    def __init__(self, refresh_interval: float = 5.0):
        """
        初始化监控器
        
        Args:
            refresh_interval: 刷新间隔（秒）
        """
        self.refresh_interval = refresh_interval
        
        # 初始化日志搜索器
        self._searcher = get_log_searcher()
        
        # 初始化图表
        self.charts = {}
        self.gauges = {}
        self.metrics = {}
        
        # 初始化警报管理器
        self.alerts = AlertManager()
        
        # 监控状态
        self.running = False
        self.last_update = 0
        self.error_count = 0
        self.start_time = time.time()
        self.monitor_thread = None
        
        # 初始化所有图表
        self._initialize_charts()
    
    def _initialize_charts(self):
        """初始化所有图表和指标"""
        # 成功率仪表盘
        self.gauges['success_rate'] = GaugeChart(
            name="success_rate",
            title="操作成功率",
            description="任务执行成功率",
            min_value=0,
            max_value=100,
            options={"unit": "%", "format": "0.0"}
        )
        
        # 内存使用折线图
        self.charts['memory_usage'] = LineChart(
            name="memory_usage",
            title="内存使用",
            description="系统内存使用情况",
            max_points=100,
            options={"unit": "MB", "yaxis": {"min": 0}}
        )
        
        # 日志级别分布
        self.charts['log_levels'] = BarChart(
            name="log_levels",
            title="日志级别分布",
            description="不同级别日志的数量分布",
            categories=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        
        # 响应时间折线图
        self.charts['response_time'] = LineChart(
            name="response_time",
            title="响应时间",
            description="API响应时间趋势",
            max_points=60,
            options={"unit": "ms", "yaxis": {"min": 0}}
        )
        
        # 关键指标
        # CPU使用率
        self.metrics['cpu_usage'] = MetricValue(
            name="cpu_usage",
            title="CPU使用率",
            description="系统CPU使用率",
            unit="%",
            precision=1
        )
        
        # 活跃用户数
        self.metrics['active_users'] = MetricValue(
            name="active_users",
            title="活跃用户",
            description="当前活跃用户数",
            unit="人",
            precision=0
        )
        
        # 处理速度
        self.metrics['processing_rate'] = MetricValue(
            name="processing_rate",
            title="处理速度",
            description="每秒处理的任务数",
            unit="任务/秒",
            precision=2
        )
        
        # 磁盘使用
        self.metrics['disk_usage'] = MetricValue(
            name="disk_usage", 
            title="磁盘使用",
            description="日志占用磁盘空间",
            unit="MB",
            precision=1
        )
    
    def update_dashboard(self):
        """实时计算关键指标"""
        # 更新成功率
        self.gauges['success_rate'].value = self._calculate_success_rate()
        
        # 更新内存使用
        self.charts['memory_usage'].append(self._get_current_memory())
        
        # 更新日志级别分布
        level_distribution = self._get_log_level_distribution()
        self.charts['log_levels'].update(level_distribution)
        
        # 更新响应时间
        self.charts['response_time'].append(self._get_recent_response_time())
        
        # 更新关键指标
        self.metrics['cpu_usage'].update(self._get_cpu_usage())
        self.metrics['active_users'].update(self._get_active_users())
        self.metrics['processing_rate'].update(self._get_processing_rate())
        self.metrics['disk_usage'].update(self._get_disk_usage())
        
        # 更新警报
        anomalies = self._detect_anomalies()
        self.alerts.update(anomalies)
        
        # 更新时间戳
        self.last_update = time.time()
    
    def _calculate_success_rate(self) -> float:
        """
        计算操作成功率
        
        Returns:
            成功率百分比
        """
        try:
            # 搜索最近的操作日志
            recent_operations = self._searcher.search("操作 OR operation", limit=100)
            
            if not recent_operations:
                return 100.0  # 默认值
            
            # 计算成功和失败的操作
            success_count = 0
            total_count = len(recent_operations)
            
            for op in recent_operations:
                # 检查消息是否包含成功标识
                message = op.get("message", "").lower()
                if "成功" in message or "success" in message:
                    success_count += 1
                # 也可以检查日志级别
                elif op.get("level") == "INFO":
                    success_count += 1
            
            # 计算成功率
            success_rate = (success_count / max(1, total_count)) * 100
            return round(success_rate, 1)
            
        except Exception as e:
            logger.error(f"计算成功率出错: {e}")
            return 95.0  # 出错时的默认值
    
    def _get_current_memory(self) -> float:
        """
        获取当前内存使用
        
        Returns:
            内存使用（MB）
        """
        try:
            import psutil
            # 获取当前进程的内存使用
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            # 转换为MB
            memory_mb = memory_info.rss / (1024 * 1024)
            return round(memory_mb, 2)
        except ImportError:
            # 如果psutil不可用，使用Python的内置内存统计
            import resource
            memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            memory_mb = memory_kb / 1024
            return round(memory_mb, 2)
        except Exception as e:
            logger.error(f"获取内存使用出错: {e}")
            return 200.0  # 出错时的默认值
    
    def _get_log_level_distribution(self) -> Dict[str, int]:
        """
        获取日志级别分布
        
        Returns:
            各级别日志数量的字典
        """
        try:
            # 获取日志统计
            stats = get_log_statistics()
            
            # 提取级别分布
            level_distribution = stats.get("level_distribution", {})
            
            # 确保所有级别都有值
            result = {
                "DEBUG": level_distribution.get("DEBUG", 0),
                "INFO": level_distribution.get("INFO", 0),
                "WARNING": level_distribution.get("WARNING", 0),
                "ERROR": level_distribution.get("ERROR", 0),
                "CRITICAL": level_distribution.get("CRITICAL", 0)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取日志级别分布出错: {e}")
            # 出错时返回默认值
            return {
                "DEBUG": 10,
                "INFO": 50,
                "WARNING": 5,
                "ERROR": 2,
                "CRITICAL": 0
            }
    
    def _get_recent_response_time(self) -> float:
        """
        获取最近的API响应时间
        
        Returns:
            平均响应时间（毫秒）
        """
        try:
            # 搜索API响应时间日志
            response_logs = self._searcher.search("响应时间 OR response time", limit=10)
            
            if not response_logs:
                return 50.0  # 默认值
            
            # 提取响应时间
            times = []
            pattern = r'(\d+(?:\.\d+)?)\s*(?:ms|毫秒)'
            
            for log in response_logs:
                message = log.get("message", "")
                match = re.search(pattern, message)
                if match:
                    try:
                        times.append(float(match.group(1)))
                    except ValueError:
                        pass
            
            # 计算平均响应时间
            if times:
                return sum(times) / len(times)
            else:
                return 50.0  # 默认值
                
        except Exception as e:
            logger.error(f"获取响应时间出错: {e}")
            return 50.0  # 出错时的默认值
    
    def _get_cpu_usage(self) -> float:
        """
        获取CPU使用率
        
        Returns:
            CPU使用率百分比
        """
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return cpu_percent
        except ImportError:
            # 如果psutil不可用，返回默认值
            return 30.0
        except Exception as e:
            logger.error(f"获取CPU使用率出错: {e}")
            return 30.0  # 出错时的默认值
    
    def _get_active_users(self) -> int:
        """
        获取活跃用户数
        
        Returns:
            活跃用户数
        """
        try:
            # 这里应该根据实际情况获取活跃用户数
            # 例如，从会话管理器或数据库中获取
            
            # 示例实现：从日志中获取最近的用户活动
            user_logs = self._searcher.search("user OR 用户", limit=50)
            
            # 提取用户ID
            unique_users = set()
            user_pattern = r'user(?:_id|ID)?[=:]\s*([a-zA-Z0-9_-]+)'
            
            for log in user_logs:
                message = log.get("message", "")
                match = re.search(user_pattern, message, re.IGNORECASE)
                if match:
                    unique_users.add(match.group(1))
            
            return len(unique_users) or 1  # 至少返回1
                
        except Exception as e:
            logger.error(f"获取活跃用户数出错: {e}")
            return 1  # 出错时的默认值
    
    def _get_processing_rate(self) -> float:
        """
        获取处理速度
        
        Returns:
            每秒处理的任务数
        """
        try:
            # 获取最近的处理任务日志
            start_time = time.time() - 300  # 最近5分钟
            task_logs = self._searcher.search("处理 OR process OR task", limit=100)
            
            # 只保留最近5分钟的日志
            recent_tasks = []
            for log in task_logs:
                timestamp = log.get("timestamp")
                if timestamp:
                    try:
                        log_time = datetime.datetime.fromisoformat(timestamp).timestamp()
                        if log_time >= start_time:
                            recent_tasks.append(log)
                    except (ValueError, TypeError):
                        pass
            
            # 计算处理速度
            num_tasks = len(recent_tasks)
            elapsed_time = 300  # 5分钟 = 300秒
            
            return num_tasks / elapsed_time
            
        except Exception as e:
            logger.error(f"获取处理速度出错: {e}")
            return 0.5  # 出错时的默认值
    
    def _get_disk_usage(self) -> float:
        """
        获取日志占用的磁盘空间
        
        Returns:
            磁盘使用（MB）
        """
        try:
            # 获取日志目录
            log_dir = get_log_directory()
            
            # 计算目录大小
            total_size = 0
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            # 转换为MB
            size_mb = total_size / (1024 * 1024)
            return round(size_mb, 1)
            
        except Exception as e:
            logger.error(f"获取磁盘使用出错: {e}")
            return 100.0  # 出错时的默认值
    
    def _detect_anomalies(self) -> List[Alert]:
        """
        检测日志中的异常情况
        
        Returns:
            异常警报列表
        """
        anomalies = []
        
        try:
            # 检测错误率异常
            error_logs = self._searcher.search("ERROR OR CRITICAL", limit=50)
            recent_errors = [log for log in error_logs if self._is_recent(log, hours=1)]
            
            if len(recent_errors) > 5:
                # 错误数量过多
                anomalies.append(Alert(
                    message=f"最近1小时内发现{len(recent_errors)}个错误",
                    level=AlertLevel.WARNING,
                    source="错误监控",
                    context={"error_count": len(recent_errors)}
                ))
            
            # 检测内存使用异常
            memory_usage = self._get_current_memory()
            if memory_usage > 500:  # 超过500MB
                anomalies.append(Alert(
                    message=f"内存使用过高: {memory_usage:.1f}MB",
                    level=AlertLevel.WARNING,
                    source="资源监控",
                    context={"memory_usage": memory_usage}
                ))
            
            # 检测CPU使用异常
            cpu_usage = self._get_cpu_usage()
            if cpu_usage > 80:  # 超过80%
                anomalies.append(Alert(
                    message=f"CPU使用率过高: {cpu_usage:.1f}%",
                    level=AlertLevel.WARNING,
                    source="资源监控",
                    context={"cpu_usage": cpu_usage}
                ))
            
            # 检测响应时间异常
            response_time = self._get_recent_response_time()
            if response_time > 200:  # 超过200ms
                anomalies.append(Alert(
                    message=f"响应时间过长: {response_time:.1f}ms",
                    level=AlertLevel.WARNING,
                    source="性能监控",
                    context={"response_time": response_time}
                ))
            
            # 检测日志完整性异常
            integrity_logs = self._searcher.search("完整性 OR integrity OR fingerprint OR 指纹", limit=10)
            for log in integrity_logs:
                message = log.get("message", "").lower()
                if "失败" in message or "错误" in message or "error" in message or "failed" in message:
                    anomalies.append(Alert(
                        message="日志完整性检查失败",
                        level=AlertLevel.ERROR,
                        source="完整性监控",
                        context={"log_message": log.get("message")}
                    ))
                    break
            
            return anomalies
            
        except Exception as e:
            logger.error(f"检测异常出错: {e}")
            return []
    
    def _is_recent(self, log_entry: Dict[str, Any], hours: int = 24) -> bool:
        """
        检查日志是否是最近的
        
        Args:
            log_entry: 日志条目
            hours: 小时数
            
        Returns:
            是否是最近的日志
        """
        try:
            if not log_entry.get("timestamp"):
                return False
                
            log_time = datetime.datetime.fromisoformat(log_entry["timestamp"])
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
            
            return log_time >= cutoff_time
        except (ValueError, TypeError):
            return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取看板数据
        
        Returns:
            看板数据字典
        """
        return {
            "charts": {name: chart.to_dict() for name, chart in self.charts.items()},
            "gauges": {name: gauge.to_dict() for name, gauge in self.gauges.items()},
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "alerts": {
                "active": self.alerts.get_active_alerts(),
                "counts": self.alerts.alert_counts
            },
            "status": {
                "running": self.running,
                "last_update": self.last_update,
                "uptime": time.time() - self.start_time,
                "error_count": self.error_count
            }
        }
    
    def start_monitoring(self):
        """开始实时监控"""
        if self.running:
            return
            
        self.running = True
        self.start_time = time.time()
        
        # 创建并启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("实时日志监控已启动")
    
    def stop_monitoring(self):
        """停止实时监控"""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=3.0)
            
        logger.info("实时日志监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.running:
            try:
                # 更新看板
                self.update_dashboard()
                
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                self.error_count += 1
                
                # 添加监控错误警报
                self.alerts.add(
                    message=f"监控过程出错: {str(e)}",
                    level=AlertLevel.ERROR,
                    source="监控系统"
                )
            
            # 等待下一次更新
            time.sleep(self.refresh_interval)

# 全局监控实例
_live_monitor = None

def get_live_monitor() -> LiveLogMonitor:
    """
    获取全局日志监控器实例
    
    Returns:
        日志监控器实例
    """
    global _live_monitor
    
    if _live_monitor is None:
        _live_monitor = LiveLogMonitor()
        # 自动启动监控
        _live_monitor.start_monitoring()
        
    return _live_monitor

# 便捷函数
def get_dashboard_data() -> Dict[str, Any]:
    """
    获取看板数据
    
    Returns:
        看板数据字典
    """
    monitor = get_live_monitor()
    return monitor.get_dashboard_data()

def add_dashboard_alert(message: str, level: str = AlertLevel.INFO) -> str:
    """
    添加看板警报
    
    Args:
        message: 警报消息
        level: 警报级别
        
    Returns:
        警报ID
    """
    monitor = get_live_monitor()
    return monitor.alerts.add(message=message, level=level, source="外部系统")

if __name__ == "__main__":
    # 如果直接运行此模块，执行简单的演示
    monitor = LiveLogMonitor()
    monitor.start_monitoring()
    
    print("实时日志监控已启动，按Ctrl+C停止...")
    
    try:
        # 运行一段时间
        for i in range(10):
            # 获取看板数据
            data = monitor.get_dashboard_data()
            
            # 打印部分状态信息
            print(f"\n--- 监控状态更新 {i+1}/10 ---")
            print(f"成功率: {data['gauges']['success_rate']['data']['value']}%")
            print(f"内存使用: {data['metrics']['memory_usage']['data']['value']} MB")
            print(f"活跃用户: {data['metrics']['active_users']['data']['value']}")
            print(f"活跃警报: {len(data['alerts']['active'])}")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n监控停止中...")
    finally:
        monitor.stop_monitoring()
        print("监控已停止") 