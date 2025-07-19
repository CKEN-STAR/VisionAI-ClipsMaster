#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时监控看板

为VisionAI-ClipsMaster提供系统资源和应用性能的实时监控看板。
结合了内存、CPU、模型加载和视频处理的关键指标，支持低资源环境。
"""

import os
import sys
import time
import json
import psutil
import logging
import threading
import matplotlib
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

# 默认使用非交互式后端，适用于服务器环境
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

# 导入监控组件
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.analyzer import MetricsAnalyzer

logger = logging.getLogger(__name__)

class MonitorDashboard:

    # 内存使用警告阈值（百分比）
    memory_warning_threshold = 80
    """实时资源监控看板
    
    集成系统和应用程序指标，提供可视化界面和API数据支持。
    """
    
    def __init__(self, 
                 config_path: str = "configs/dashboard_config.yaml",
                 update_interval: float = 5.0,
                 max_history: int = 60):
        """初始化监控看板
        
        Args:
            config_path: 看板配置文件路径
            update_interval: 更新间隔（秒）
            max_history: 历史数据最大保存点数
        """
        self.config_path = config_path
        self.update_interval = update_interval
        self.max_history = max_history
        
        # 载入配置
        self.config = self._load_config()
        
        # 初始化指标收集器
        self.metrics_collector = MetricsCollector()
        
        # 初始化指标分析器
        self.analyzer = MetricsAnalyzer()
        
        # 数据存储
        self.metrics_history = {}
        self.system_info = {}
        self.model_info = {}
        self.processing_info = {}
        self.timestamps = []
        
        # 运行状态
        self.running = False
        self.update_thread = None
        self.last_update = 0
        
        # 创建输出目录
        self._init_output_dirs()
    
    def _load_config(self) -> Dict:
        """加载看板配置
        
        Returns:
            配置字典
        """
        try:
            # 检查配置文件是否存在
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                        import yaml
                        return yaml.safe_load(f)
                    else:
                        return json.load(f)
            else:
                # 使用默认配置
                return {
                    "enabled_metrics": [
                        "memory_usage", "cpu_usage", "model_memory", 
                        "processing_time", "cache_hit_rate"
                    ],
                    "charts": {
                        "memory_chart": {
                            "title": "内存使用",
                            "y_label": "使用百分比 (%)",
                            "color": "blue"
                        },
                        "cpu_chart": {
                            "title": "CPU使用",
                            "y_label": "使用百分比 (%)",
                            "color": "green"
                        },
                        "model_memory_chart": {
                            "title": "模型内存",
                            "y_label": "内存 (MB)",
                            "color": "red"
                        }
                    },
                    "thresholds": {
                        "memory_warning": 75,
                        "memory_critical": 90,
                        "cpu_warning": 80,
                        "cpu_critical": 95
                    },
                    "output": {
                        "charts_dir": "output/dashboard/charts",
                        "data_dir": "output/dashboard/data"
                    }
                }
        except Exception as e:
            logger.error(f"加载配置文件错误: {e}")
            # 返回简单的默认配置
            return {
                "enabled_metrics": ["memory_usage", "cpu_usage"],
                "output": {
                    "charts_dir": "output/dashboard/charts",
                    "data_dir": "output/dashboard/data"
                }
            }
    
    def _init_output_dirs(self):
        """初始化输出目录"""
        output_config = self.config.get("output", {})
        self.charts_dir = output_config.get("charts_dir", "output/dashboard/charts")
        self.data_dir = output_config.get("data_dir", "output/dashboard/data")
        
        # 创建目录
        os.makedirs(self.charts_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def start(self):
        """启动监控看板"""
        if self.running:
            return
        
        self.running = True
        
        # 启动指标收集
        self.metrics_collector.start_collection()
        
        # 启动更新线程
        self.update_thread = threading.Thread(target=self._update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        logger.info("监控看板已启动")
    
    def stop(self):
        """停止监控看板"""
        self.running = False
        
        # 停止指标收集
        self.metrics_collector.stop_collection()
        
        # 等待更新线程结束
        if self.update_thread:
            self.update_thread.join(timeout=10.0)
        
        logger.info("监控看板已停止")
    
    def _update_loop(self):
        """更新循环，定期收集和更新指标"""
        while self.running:
            try:
                # 收集当前时间戳
                current_time = time.time()
                self.timestamps.append(current_time)
                
                # 保持时间戳列表在限定长度内
                if len(self.timestamps) > self.max_history:
                    self.timestamps = self.timestamps[-self.max_history:]
                
                # 收集系统指标
                self._collect_system_metrics()
                
                # 收集模型指标
                self._collect_model_metrics()
                
                # 收集处理指标
                self._collect_processing_metrics()
                
                # 更新指标历史
                self._update_metrics_history()
                
                # 生成可视化图表
                self._generate_charts()
                
                # 导出最新数据
                self._export_latest_data()
                
                # 更新最后更新时间
                self.last_update = current_time
                
                # 等待下一个更新间隔
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"监控看板更新错误: {e}")
                time.sleep(5)  # 出错后等待一段时间再重试
    
    def _collect_system_metrics(self):
        """收集系统指标"""
        # 内存使用
        memory = psutil.virtual_memory()
        self.system_info["memory_percent"] = memory.percent
        self.system_info["memory_available"] = memory.available / (1024 * 1024)  # MB
        self.system_info["memory_total"] = memory.total / (1024 * 1024)  # MB
        
        # CPU使用
        self.system_info["cpu_percent"] = psutil.cpu_percent(interval=0.5)
        self.system_info["cpu_count"] = psutil.cpu_count()
        
        # 磁盘使用
        disk = psutil.disk_usage('/')
        self.system_info["disk_percent"] = disk.percent
        self.system_info["disk_free"] = disk.free / (1024 * 1024 * 1024)  # GB
        
        # 进程信息
        process = psutil.Process()
        self.system_info["process_memory"] = process.memory_info().rss / (1024 * 1024)  # MB
        self.system_info["process_cpu"] = process.cpu_percent(interval=0.1)
        self.system_info["process_threads"] = process.num_threads()
    
    def _collect_model_metrics(self):
        """收集模型相关指标"""
        # 这里应该集成ModelSwitcher或相关组件以获取真实数据
        # 目前使用模拟数据示例
        
        # 从MetricsCollector获取数据
        try:
            model_memory = self.metrics_collector.collect_on_demand("model_metrics.active_model_memory")
            if model_memory is None:
                # 模拟数据
                model_memory = 2048  # MB
                
            self.model_info["model_memory"] = model_memory
            self.model_info["model_type"] = "Chinese"  # 当前只使用中文模型
            self.model_info["model_loaded"] = True
            
        except Exception as e:
            logger.warning(f"收集模型指标错误: {e}")
            # 使用默认值
            self.model_info["model_memory"] = self.model_info.get("model_memory", 0)
            self.model_info["model_type"] = self.model_info.get("model_type", "Unknown")
            self.model_info["model_loaded"] = False
    
    def _collect_processing_metrics(self):
        """收集处理相关指标"""
        # 从MetricsCollector获取数据或集成相关组件
        # 目前使用模拟数据示例
        
        # 缓存命中率
        try:
            cache_hit_rate = self.metrics_collector.collect_on_demand("cache_metrics.cache_hit_rate")
            if cache_hit_rate is None:
                cache_hit_rate = 85.0  # 默认/模拟值
                
            self.processing_info["cache_hit_rate"] = cache_hit_rate
        except:
            self.processing_info["cache_hit_rate"] = self.processing_info.get("cache_hit_rate", 0)
        
        # 其他处理指标...
        # 在真实实现中，这里应集成VideoProcessor等组件，获取实际处理时间和性能指标
    
    def _update_metrics_history(self):
        """更新指标历史数据"""
        # 系统指标历史
        for key, value in self.system_info.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []
            
            self.metrics_history[key].append(value)
            
            # 保持历史数据在限定长度内
            if len(self.metrics_history[key]) > self.max_history:
                self.metrics_history[key] = self.metrics_history[key][-self.max_history:]
        
        # 模型指标历史
        for key, value in self.model_info.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []
            
            self.metrics_history[key].append(value)
            
            # 保持历史数据在限定长度内
            if len(self.metrics_history[key]) > self.max_history:
                self.metrics_history[key] = self.metrics_history[key][-self.max_history:]
        
        # 处理指标历史
        for key, value in self.processing_info.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []
            
            self.metrics_history[key].append(value)
            
            # 保持历史数据在限定长度内
            if len(self.metrics_history[key]) > self.max_history:
                self.metrics_history[key] = self.metrics_history[key][-self.max_history:]
    
    def _generate_charts(self):
        """生成监控图表"""
        charts_config = self.config.get("charts", {})
        
        # 生成内存使用图表
        if self.metrics_history.get("memory_percent"):
            self._generate_metric_chart(
                "memory_chart", 
                "内存使用率", 
                "memory_percent", 
                "使用百分比 (%)",
                "blue"
            )
        
        # 生成CPU使用图表
        if self.metrics_history.get("cpu_percent"):
            self._generate_metric_chart(
                "cpu_chart", 
                "CPU使用率", 
                "cpu_percent", 
                "使用百分比 (%)",
                "green"
            )
        
        # 生成模型内存图表
        if self.metrics_history.get("model_memory"):
            self._generate_metric_chart(
                "model_memory_chart", 
                "模型内存使用", 
                "model_memory", 
                "内存 (MB)",
                "red"
            )
        
        # 生成进程内存图表
        if self.metrics_history.get("process_memory"):
            self._generate_metric_chart(
                "process_memory_chart", 
                "进程内存使用", 
                "process_memory", 
                "内存 (MB)",
                "purple"
            )
        
        # 生成缓存命中率图表
        if self.metrics_history.get("cache_hit_rate"):
            self._generate_metric_chart(
                "cache_hit_rate_chart", 
                "缓存命中率", 
                "cache_hit_rate", 
                "命中率 (%)",
                "orange"
            )
    
    def _generate_metric_chart(self, chart_id: str, title: str, metric_key: str, 
                              y_label: str, color: str):
        """生成单个指标图表
        
        Args:
            chart_id: 图表ID
            title: 图表标题
            metric_key: 指标键
            y_label: Y轴标签
            color: 图表颜色
        """
        try:
            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 获取数据
            values = self.metrics_history[metric_key]
            
            # 设置x轴为时间
            if len(self.timestamps) == len(values):
                x_values = [datetime.fromtimestamp(ts) for ts in self.timestamps]
            else:
                # 处理长度不匹配的情况
                min_len = min(len(self.timestamps), len(values))
                x_values = [datetime.fromtimestamp(ts) for ts in self.timestamps[-min_len:]]
                values = values[-min_len:]
            
            # 绘制图表
            ax.plot(x_values, values, color=color, marker='o', linestyle='-', linewidth=2, markersize=3)
            
            # 添加阈值线（如果有）
            thresholds = self.config.get("thresholds", {})
            warning_key = f"{metric_key.split('_')[0]}_warning"
            critical_key = f"{metric_key.split('_')[0]}_critical"
            
            if warning_key in thresholds:
                ax.axhline(y=thresholds[warning_key], color='yellow', linestyle='--', alpha=0.7)
            
            if critical_key in thresholds:
                ax.axhline(y=thresholds[critical_key], color='red', linestyle='--', alpha=0.7)
            
            # 设置图表属性
            ax.set_title(title)
            ax.set_xlabel('时间')
            ax.set_ylabel(y_label)
            ax.grid(True, alpha=0.3)
            
            # 格式化x轴日期
            fig.autofmt_xdate()
            
            # 保存图表
            chart_path = os.path.join(self.charts_dir, f"{chart_id}.png")
            fig.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            
            logger.debug(f"已生成图表: {chart_path}")
            
        except Exception as e:
            logger.error(f"生成图表错误 ({chart_id}): {e}")
    
    def _export_latest_data(self):
        """导出最新的监控数据"""
        try:
            # 准备导出数据
            export_data = {
                "timestamp": time.time(),
                "system": self.system_info,
                "model": self.model_info,
                "processing": self.processing_info,
                "status": {
                    "running": self.running,
                    "last_update": self.last_update,
                    "uptime": time.time() - self.last_update if self.last_update > 0 else 0
                }
            }
            
            # 导出为JSON文件
            data_path = os.path.join(self.data_dir, "latest_metrics.json")
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            # 导出为CSV文件（仅主要指标）
            csv_path = os.path.join(self.data_dir, "metrics_history.csv")
            
            # 选择要导出的指标
            export_metrics = [
                "memory_percent", "cpu_percent", "model_memory",
                "process_memory", "cache_hit_rate"
            ]
            
            # 创建CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题行
                header = ["timestamp"] + export_metrics
                writer.writerow(header)
                
                # 写入数据行
                for i in range(min(len(self.timestamps), self.max_history)):
                    idx = -min(len(self.timestamps), self.max_history) + i
                    row = [datetime.fromtimestamp(self.timestamps[idx]).strftime("%Y-%m-%d %H:%M:%S")]
                    
                    for metric in export_metrics:
                        if metric in self.metrics_history and abs(idx) <= len(self.metrics_history[metric]):
                            row.append(self.metrics_history[metric][idx])
                        else:
                            row.append("")
                    
                    writer.writerow(row)
            
        except Exception as e:
            logger.error(f"导出数据错误: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取监控看板数据
        
        Returns:
            看板数据字典
        """
        # 获取图表文件列表
        charts = {}
        for file in os.listdir(self.charts_dir):
            if file.endswith('.png'):
                chart_id = file[:-4]  # 移除 .png 扩展名
                charts[chart_id] = os.path.join(self.charts_dir, file)
        
        # 收集指标摘要
        metrics_summary = {}
        for category, data in [
            ("system", self.system_info),
            ("model", self.model_info),
            ("processing", self.processing_info)
        ]:
            for key, value in data.items():
                metrics_summary[f"{category}.{key}"] = value
        
        # 构建完整数据
        return {
            "timestamp": time.time(),
            "charts": charts,
            "metrics": metrics_summary,
            "status": {
                "running": self.running,
                "last_update": self.last_update,
                "uptime": time.time() - self.last_update if self.last_update > 0 else 0
            }
        }
    
    def get_chart_image(self, chart_id: str) -> Optional[bytes]:
        """获取图表图像数据
        
        Args:
            chart_id: 图表ID
            
        Returns:
            图表图像数据或None
        """
        chart_path = os.path.join(self.charts_dir, f"{chart_id}.png")
        if os.path.exists(chart_path):
            with open(chart_path, 'rb') as f:
                return f.read()
        return None
    
    def get_metrics_history(self, metric_key: str = None) -> Dict[str, List]:
        """获取指标历史数据
        
        Args:
            metric_key: 指标键（可选）
            
        Returns:
            指标历史数据字典
        """
        if metric_key:
            if metric_key in self.metrics_history:
                return {
                    metric_key: self.metrics_history[metric_key],
                    "timestamps": self.timestamps[-len(self.metrics_history[metric_key]):]
                }
            return {}
        else:
            return {
                "metrics": self.metrics_history,
                "timestamps": self.timestamps
            }

# 全局单例
_dashboard_instance = None

def get_dashboard() -> MonitorDashboard:
    """获取监控看板单例
    
    Returns:
        MonitorDashboard实例
    """
    global _dashboard_instance
    if _dashboard_instance is None:
        _dashboard_instance = MonitorDashboard()
    return _dashboard_instance

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动监控看板
    dashboard = get_dashboard()
    dashboard.start()
    
    try:
        # 运行10分钟后停止
        time.sleep(600)
    except KeyboardInterrupt:
        print("用户中断，停止监控看板")
    finally:
        dashboard.stop() 