#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
历史数据分析模块

为VisionAI-ClipsMaster提供历史性能数据分析功能，包括内存使用趋势、分片缓存命中率分析和OOM风险预测。
特别针对4GB RAM/无GPU的低资源环境优化设计。
"""

import os
import sys
import time
import json
import logging
import sqlite3
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from collections import defaultdict, deque
import matplotlib.pyplot as plt

# 设置日志
logger = logging.getLogger("history_analyzer")

# 数据库文件路径
DB_PATH = "data/metrics/history.db"

# 报告存储路径
REPORTS_DIR = "data/reports"

# 确保目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# 定义预警级别
class AlertLevel:
    INFO = "INFO"         # 信息级别（记录用）
    WARNING = "WARNING"   # 警告级别（需要注意）
    ERROR = "ERROR"       # 错误级别（需要通知用户）
    CRITICAL = "CRITICAL" # 严重级别（需要立即处理）

# 定义预警类别
class AlertCategory:
    MEMORY = "MEMORY"           # 内存相关
    MODEL = "MODEL"             # 模型相关
    VIDEO = "VIDEO"             # 视频处理相关
    SYSTEM = "SYSTEM"           # 系统相关
    PERFORMANCE = "PERFORMANCE" # 性能相关
    NETWORK = "NETWORK"         # 网络相关
    CACHE = "CACHE"             # 缓存相关
    SECURITY = "SECURITY"       # 安全相关

class MetricsStorage:
    """指标数据存储
    
    管理性能指标数据的持久化存储和检索，使用SQLite提供轻量级数据库功能。
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """初始化指标存储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.lock = threading.RLock()
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库结构"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建内存指标表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                datetime TEXT NOT NULL,
                process_memory REAL NOT NULL,
                system_memory REAL NOT NULL,
                memory_percent REAL NOT NULL
            )
            ''')
            
            # 创建缓存指标表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                datetime TEXT NOT NULL,
                hit_rate REAL NOT NULL,
                miss_rate REAL NOT NULL,
                eviction_rate REAL NOT NULL,
                shard_count INTEGER NOT NULL
            )
            ''')
            
            # 创建模型性能表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                datetime TEXT NOT NULL,
                model_name TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                tokens_per_second REAL,
                memory_used_mb REAL
            )
            ''')
            
            # 创建预警记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                datetime TEXT NOT NULL,
                level TEXT NOT NULL,
                category TEXT NOT NULL,
                resource TEXT NOT NULL,
                value REAL NOT NULL,
                details TEXT
            )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_timestamp ON cache_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_timestamp ON model_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_name ON model_metrics(model_name)')
            
            conn.commit()
    
    def _get_connection(self):
        """获取数据库连接（线程安全）"""
        with self.lock:
            if self.conn is None:
                # 确保目录存在
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                
                # 创建连接
                self.conn = sqlite3.connect(self.db_path)
                
                # 启用外键支持
                self.conn.execute("PRAGMA foreign_keys = ON")
                
                # 行工厂使用字典
                self.conn.row_factory = sqlite3.Row
            
            return self.conn
    
    def close(self):
        """关闭数据库连接"""
        with self.lock:
            if self.conn:
                self.conn.close()
                self.conn = None
    
    def store_memory_metrics(self, metrics: Dict[str, Any]):
        """存储内存指标数据
        
        Args:
            metrics: 内存指标数据字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            now = time.time()
            dt_str = datetime.fromtimestamp(now).isoformat()
            
            cursor.execute('''
            INSERT INTO memory_metrics 
            (timestamp, datetime, process_memory, system_memory, memory_percent)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                now,
                dt_str,
                metrics.get('process_memory', 0.0),
                metrics.get('system_memory', 0.0),
                metrics.get('memory_percent', 0.0)
            ))
            
            conn.commit()
    
    def store_cache_metrics(self, metrics: Dict[str, Any]):
        """存储缓存指标数据
        
        Args:
            metrics: 缓存指标数据字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            now = time.time()
            dt_str = datetime.fromtimestamp(now).isoformat()
            
            cursor.execute('''
            INSERT INTO cache_metrics 
            (timestamp, datetime, hit_rate, miss_rate, eviction_rate, shard_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                now,
                dt_str,
                metrics.get('hit_rate', 0.0),
                metrics.get('miss_rate', 0.0),
                metrics.get('eviction_rate', 0.0),
                metrics.get('shard_count', 0)
            ))
            
            conn.commit()
    
    def store_model_metrics(self, metrics: Dict[str, Any]):
        """存储模型性能指标数据
        
        Args:
            metrics: 模型性能指标数据字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            now = time.time()
            dt_str = datetime.fromtimestamp(now).isoformat()
            
            cursor.execute('''
            INSERT INTO model_metrics 
            (timestamp, datetime, model_name, latency_ms, tokens_per_second, memory_used_mb)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                now,
                dt_str,
                metrics.get('model_name', '未知'),
                metrics.get('latency_ms', 0.0),
                metrics.get('tokens_per_second', 0.0),
                metrics.get('memory_used_mb', 0.0)
            ))
            
            conn.commit()
    
    def store_alert(self, alert: Dict[str, Any]):
        """存储预警记录
        
        Args:
            alert: 预警数据字典
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 确保有时间戳
            if 'timestamp' not in alert:
                alert['timestamp'] = time.time()
                
            dt_str = datetime.fromtimestamp(alert['timestamp']).isoformat()
            details_str = json.dumps(alert.get('details', {})) if alert.get('details') else None
            
            cursor.execute('''
            INSERT INTO alerts 
            (timestamp, datetime, level, category, resource, value, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert['timestamp'],
                dt_str,
                alert.get('level', AlertLevel.INFO),
                alert.get('category', AlertCategory.SYSTEM),
                alert.get('resource', '未知'),
                alert.get('value', 0.0),
                details_str
            ))
            
            conn.commit()
    
    def get_memory_metrics(self, days: int = 1) -> pd.DataFrame:
        """获取内存指标数据
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            包含内存指标数据的DataFrame
        """
        with self._get_connection() as conn:
            # 计算时间范围
            start_time = time.time() - (days * 86400)
            
            # 查询数据
            query = '''
            SELECT * FROM memory_metrics 
            WHERE timestamp >= ? 
            ORDER BY timestamp
            '''
            
            # 使用pandas读取
            df = pd.read_sql_query(query, conn, params=(start_time,))
            
            return df
    
    def get_cache_metrics(self, days: int = 1) -> pd.DataFrame:
        """获取缓存指标数据
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            包含缓存指标数据的DataFrame
        """
        with self._get_connection() as conn:
            # 计算时间范围
            start_time = time.time() - (days * 86400)
            
            # 查询数据
            query = '''
            SELECT * FROM cache_metrics 
            WHERE timestamp >= ? 
            ORDER BY timestamp
            '''
            
            # 使用pandas读取
            df = pd.read_sql_query(query, conn, params=(start_time,))
            
            return df
    
    def get_model_metrics(self, days: int = 1, model_name: Optional[str] = None) -> pd.DataFrame:
        """获取模型性能指标数据
        
        Args:
            days: 获取最近几天的数据
            model_name: 如果指定，只获取特定模型的数据
            
        Returns:
            包含模型性能指标数据的DataFrame
        """
        with self._get_connection() as conn:
            # 计算时间范围
            start_time = time.time() - (days * 86400)
            
            # 构建查询
            if model_name:
                query = '''
                SELECT * FROM model_metrics 
                WHERE timestamp >= ? AND model_name = ?
                ORDER BY timestamp
                '''
                params = (start_time, model_name)
            else:
                query = '''
                SELECT * FROM model_metrics 
                WHERE timestamp >= ? 
                ORDER BY timestamp
                '''
                params = (start_time,)
            
            # 使用pandas读取
            df = pd.read_sql_query(query, conn, params=params)
            
            return df
    
    def get_alerts(self, days: int = 1, level: Optional[str] = None) -> pd.DataFrame:
        """获取预警记录
        
        Args:
            days: 获取最近几天的数据
            level: 如果指定，只获取特定级别的预警
            
        Returns:
            包含预警记录的DataFrame
        """
        with self._get_connection() as conn:
            # 计算时间范围
            start_time = time.time() - (days * 86400)
            
            # 构建查询
            if level:
                query = '''
                SELECT * FROM alerts 
                WHERE timestamp >= ? AND level = ?
                ORDER BY timestamp DESC
                '''
                params = (start_time, level)
            else:
                query = '''
                SELECT * FROM alerts 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
                '''
                params = (start_time,)
            
            # 使用pandas读取
            df = pd.read_sql_query(query, conn, params=params)
            
            return df
    
    def get_daily_memory_stats(self, days: int = 30) -> pd.DataFrame:
        """获取每日内存使用统计
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            包含每日内存统计的DataFrame
        """
        with self._get_connection() as conn:
            # 计算时间范围
            start_time = time.time() - (days * 86400)
            
            # 查询数据
            query = '''
            SELECT 
                date(datetime) as date,
                MAX(process_memory) as peak_process_memory,
                AVG(process_memory) as avg_process_memory,
                MAX(system_memory) as peak_system_memory,
                AVG(system_memory) as avg_system_memory,
                MAX(memory_percent) as peak_memory_percent,
                AVG(memory_percent) as avg_memory_percent,
                COUNT(*) as sample_count
            FROM memory_metrics 
            WHERE timestamp >= ? 
            GROUP BY date(datetime)
            ORDER BY date DESC
            '''
            
            # 使用pandas读取
            df = pd.read_sql_query(query, conn, params=(start_time,))
            
            return df


class HistoryAnalyzer:
    """历史数据分析器
    
    分析系统历史性能数据，生成报告，识别趋势和潜在问题。
    """
    
    def __init__(self, db_path: str = DB_PATH, reports_dir: str = REPORTS_DIR):
        """初始化历史分析器
        
        Args:
            db_path: 数据库文件路径
            reports_dir: 报告存储目录
        """
        self.db_path = db_path
        self.reports_dir = reports_dir
        
        # 确保报告目录存在
        os.makedirs(reports_dir, exist_ok=True)
        
        # 创建数据存储对象
        self.storage = MetricsStorage(db_path)
        
        # 数据采集线程
        self._collection_thread = None
        self._stop_collection = threading.Event()
        
        # 自动报告线程
        self._report_thread = None
        self._stop_reports = threading.Event()
        
        # 日志设置
        self.logger = logging.getLogger("history_analyzer")
        self.logger.info("历史数据分析器初始化完成")
    
    def start_collection(self, interval: int = 300):
        """启动数据采集
        
        定期从系统收集数据并存储到数据库
        
        Args:
            interval: 采集间隔（秒）
        """
        if self._collection_thread and self._collection_thread.is_alive():
            self.logger.warning("数据采集已在运行中")
            return
        
        self._stop_collection.clear()
        self._collection_thread = threading.Thread(
            target=self._collection_loop,
            args=(interval,),
            daemon=True,
            name="history_data_collector"
        )
        self._collection_thread.start()
        
        self.logger.info(f"已启动历史数据采集，间隔: {interval}秒")
    
    def _collection_loop(self, interval: int):
        """数据采集循环
        
        Args:
            interval: 采集间隔（秒）
        """
        while not self._stop_collection.is_set():
            try:
                # 采集当前指标
                self._collect_current_metrics()
                
            except Exception as e:
                self.logger.error(f"采集数据时出错: {e}")
            
            # 等待下一次采集
            self._stop_collection.wait(interval)
    
    def _collect_current_metrics(self):
        """采集当前系统指标"""
        try:
            # 1. 采集内存指标
            memory_metrics = {}
            
            try:
                # 使用psutil采集系统内存使用情况
                import psutil
                
                # 系统内存
                mem = psutil.virtual_memory()
                memory_percent = mem.percent
                memory_metrics["memory_percent"] = memory_percent
                
                # 进程内存
                process = psutil.Process()
                process_memory = process.memory_info().rss / (1024 * 1024)  # MB
                memory_metrics["process_memory"] = process_memory
                
                # 系统使用内存（MB）
                total_memory = mem.total / (1024 * 1024)  # MB
                used_memory = mem.used / (1024 * 1024)  # MB
                memory_metrics["system_memory"] = used_memory
                
                # 存储内存指标
                self.storage.store_memory_metrics(memory_metrics)
                
                self.logger.debug(f"已采集内存指标: {memory_percent:.1f}%, 进程: {process_memory:.1f}MB")
            except Exception as e:
                self.logger.error(f"采集内存指标失败: {e}")
            
            # 2. 采集模拟的缓存指标
            try:
                # 这里使用模拟数据，实际使用时应从缓存系统获取
                import random
                cache_metrics = {
                    "hit_rate": random.uniform(70, 95),  # 模拟70-95%的命中率
                    "miss_rate": random.uniform(5, 30),  # 模拟5-30%的未命中率
                    "eviction_rate": random.uniform(0.1, 2.0),  # 模拟每秒0.1-2个分片被驱逐
                    "shard_count": random.randint(50, 200)  # 模拟50-200个分片
                }
                
                self.storage.store_cache_metrics(cache_metrics)
                self.logger.debug(f"已采集缓存指标: 命中率 {cache_metrics['hit_rate']:.1f}%")
            except Exception as e:
                self.logger.error(f"采集缓存指标失败: {e}")
            
            # 3. 采集模拟的模型性能指标
            try:
                # 这里使用模拟数据，实际使用时应从模型性能监控系统获取
                model_perf = {
                    "model_name": "qwen2.5-7b-zh",  # 默认中文模型
                    "latency_ms": random.uniform(100, 500),  # 模拟100-500ms的延迟
                    "tokens_per_second": random.uniform(10, 30),  # 模拟10-30 token/s的吞吐量
                    "memory_used_mb": random.uniform(2200, 2800)  # 模拟2.2-2.8GB的内存使用
                }
                
                self.storage.store_model_metrics(model_perf)
                self.logger.debug(f"已采集模型性能指标: {model_perf['model_name']}, 延迟: {model_perf['latency_ms']:.1f}ms")
            except Exception as e:
                self.logger.error(f"采集模型性能指标失败: {e}")
            
            # 4. 生成模拟的预警（偶尔）
            try:
                # 有10%的概率生成预警
                if random.random() < 0.1:
                    alert_levels = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
                    alert_categories = [AlertCategory.MEMORY, AlertCategory.MODEL, AlertCategory.SYSTEM, AlertCategory.CACHE]
                    
                    # 随机选择预警级别和类别，INFO和WARNING更常见
                    weights = [0.4, 0.3, 0.2, 0.1]
                    level = random.choices(alert_levels, weights=weights, k=1)[0]
                    category = random.choice(alert_categories)
                    
                    # 创建预警
                    alert = {
                        "timestamp": time.time(),
                        "level": level,
                        "category": category,
                        "resource": "模拟资源",
                        "value": random.uniform(80, 99) if category == AlertCategory.MEMORY else random.uniform(10, 100),
                        "details": {
                            "message": f"模拟预警：{category} 资源使用过高",
                            "source": "history_analyzer"
                        }
                    }
                    
                    self.storage.store_alert(alert)
                    self.logger.debug(f"已生成模拟预警: {level} - {category}")
            except Exception as e:
                self.logger.error(f"生成模拟预警失败: {e}")
        
        except Exception as e:
            self.logger.error(f"采集当前指标失败: {e}")
    
    def stop_collection(self):
        """停止数据采集"""
        self._stop_collection.set()
        
        if self._collection_thread and self._collection_thread.is_alive():
            self._collection_thread.join(timeout=2.0)
            
        self.logger.info("已停止历史数据采集")
    
    def start_auto_reports(self, daily_interval: int = 86400, weekly_interval: int = 604800):
        """启动自动报告生成
        
        按指定的时间间隔自动生成日报和周报
        
        Args:
            daily_interval: 日报生成间隔（秒），默认为1天
            weekly_interval: 周报生成间隔（秒），默认为7天
        """
        if self._report_thread and self._report_thread.is_alive():
            self.logger.warning("自动报告生成已在运行中")
            return
        
        self._stop_reports.clear()
        self._report_thread = threading.Thread(
            target=self._report_loop,
            args=(daily_interval, weekly_interval),
            daemon=True,
            name="auto_report_generator"
        )
        self._report_thread.start()
        
        self.logger.info(f"已启动自动报告生成，日报间隔: {daily_interval}秒，周报间隔: {weekly_interval}秒")
    
    def _report_loop(self, daily_interval: int, weekly_interval: int):
        """报告生成循环
        
        Args:
            daily_interval: 日报生成间隔（秒）
            weekly_interval: 周报生成间隔（秒）
        """
        daily_counter = 0
        weekly_counter = 0
        
        while not self._stop_reports.is_set():
            try:
                # 更新计数器
                daily_counter += 1
                weekly_counter += 1
                
                # 检查是否需要生成日报
                if daily_counter >= daily_interval:
                    self.logger.info("正在生成每日报告...")
                    self.generate_daily_report()
                    daily_counter = 0
                
                # 检查是否需要生成周报
                if weekly_counter >= weekly_interval:
                    self.logger.info("正在生成每周报告...")
                    self.generate_weekly_report()
                    weekly_counter = 0
                
            except Exception as e:
                self.logger.error(f"自动生成报告时出错: {e}")
            
            # 每60秒检查一次
            self._stop_reports.wait(60)
    
    def stop_auto_reports(self):
        """停止自动报告生成"""
        self._stop_reports.set()
        
        if self._report_thread and self._report_thread.is_alive():
            self._report_thread.join(timeout=2.0)
            
        self.logger.info("已停止自动报告生成")
    
    def get_latest_reports(self, report_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最新报告列表
        
        Args:
            report_type: 报告类型，如"daily"或"weekly"，None表示所有类型
            limit: 最大返回数量
            
        Returns:
            报告列表
        """
        try:
            reports = []
            
            # 查找报告文件
            for file_name in os.listdir(self.reports_dir):
                if not file_name.endswith('.json'):
                    continue
                    
                # 检查报告类型
                if report_type and not file_name.startswith(f"{report_type}_report_"):
                    continue
                
                file_path = os.path.join(self.reports_dir, file_name)
                
                try:
                    # 加载报告
                    with open(file_path, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        
                    # 添加文件信息
                    report['file_name'] = file_name
                    report['file_path'] = file_path
                    
                    reports.append(report)
                except Exception as e:
                    self.logger.error(f"加载报告 {file_name} 失败: {e}")
            
            # 按时间戳排序
            reports.sort(key=lambda r: r.get('timestamp', 0), reverse=True)
            
            # 限制数量
            return reports[:limit]
            
        except Exception as e:
            self.logger.error(f"获取报告列表失败: {e}")
            return []
    
    def get_report_by_date(self, date_str: str, report_type: str = "daily") -> Optional[Dict[str, Any]]:
        """获取指定日期的报告
        
        Args:
            date_str: 日期字符串，格式为"YYYY-MM-DD"
            report_type: 报告类型，如"daily"或"weekly"
            
        Returns:
            报告数据，如果不存在则返回None
        """
        try:
            file_name = f"{report_type}_report_{date_str}.json"
            file_path = os.path.join(self.reports_dir, file_name)
            
            if not os.path.exists(file_path):
                return None
                
            # 加载报告
            with open(file_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                
            # 添加文件信息
            report['file_name'] = file_name
            report['file_path'] = file_path
            
            return report
            
        except Exception as e:
            self.logger.error(f"获取报告失败: {e}")
            return None
    
    def __del__(self):
        """析构函数"""
        # 停止所有线程
        if hasattr(self, '_stop_collection'):
            self.stop_collection()
        
        if hasattr(self, '_stop_reports'):
            self.stop_auto_reports()
        
        # 关闭数据库连接
        if hasattr(self, 'storage'):
            self.storage.close()
    
    def analyze_memory_trends(self, days: int = 7) -> Dict[str, Any]:
        """分析内存使用趋势
        
        Args:
            days: 分析最近几天的数据
            
        Returns:
            内存趋势分析结果
        """
        try:
            # 获取内存指标数据
            df = self.storage.get_memory_metrics(days)
            
            if df.empty:
                return {
                    "success": False,
                    "message": "没有可用的内存指标数据",
                    "data": {}
                }
            
            # 将时间戳转换为datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            
            # 计算每日统计
            daily_stats = df.groupby('date').agg({
                'process_memory': ['mean', 'max'],
                'system_memory': ['mean', 'max'],
                'memory_percent': ['mean', 'max']
            }).reset_index()
            
            # 格式化列名
            daily_stats.columns = [
                'date' if col == 'date' else f"{col[0]}_{col[1]}"
                for col in daily_stats.columns
            ]
            
            # 计算趋势线性回归
            if len(daily_stats) > 1 and 'memory_percent_mean' in daily_stats.columns:
                x = np.arange(len(daily_stats))
                y = daily_stats['memory_percent_mean'].values
                
                # 线性回归
                slope, intercept = np.polyfit(x, y, 1)
                
                # 预测30天后的内存使用率
                days_forward = 30
                future_usage = intercept + slope * (len(daily_stats) + days_forward - 1)
                future_usage = max(0, min(100, future_usage))  # 限制在0-100之间
                
                # 趋势类型
                if slope > 0.5:
                    trend_type = "显著上升"
                    trend_class = "high_risk"
                elif slope > 0.1:
                    trend_type = "缓慢上升"
                    trend_class = "medium_risk"
                elif slope < -0.5:
                    trend_type = "显著下降"
                    trend_class = "improving"
                elif slope < -0.1:
                    trend_type = "缓慢下降"
                    trend_class = "good"
                else:
                    trend_type = "稳定"
                    trend_class = "stable"
                
                # 平均值统计
                avg_system = daily_stats['system_memory_mean'].mean()
                avg_process = daily_stats['process_memory_mean'].mean()
                avg_percent = daily_stats['memory_percent_mean'].mean()
                
                # 内存峰值统计
                peak_system = daily_stats['system_memory_max'].max()
                peak_process = daily_stats['process_memory_max'].max()
                peak_percent = daily_stats['memory_percent_max'].max()
                
                # 返回分析结果
                return {
                    "success": True,
                    "data": {
                        "avg_system_memory_mb": round(avg_system, 2),
                        "avg_process_memory_mb": round(avg_process, 2),
                        "avg_memory_percent": round(avg_percent, 2),
                        "peak_system_memory_mb": round(peak_system, 2),
                        "peak_process_memory_mb": round(peak_process, 2),
                        "peak_memory_percent": round(peak_percent, 2),
                        "trend_slope": round(slope, 4),
                        "trend_type": trend_type,
                        "trend_class": trend_class,
                        "predicted_usage_30d": round(future_usage, 2),
                        "daily_data": daily_stats.to_dict(orient='records'),
                        "days_analyzed": len(daily_stats)
                    }
                }
            else:
                # 数据不足以进行趋势分析
                return {
                    "success": True,
                    "message": "数据点不足，无法进行趋势分析",
                    "data": {
                        "daily_data": daily_stats.to_dict(orient='records') if not daily_stats.empty else [],
                        "days_analyzed": len(daily_stats)
                    }
                }
                
        except Exception as e:
            self.logger.error(f"分析内存趋势失败: {e}")
            return {
                "success": False,
                "message": f"分析失败: {str(e)}",
                "data": {}
            }
    
    def analyze_cache_performance(self, days: int = 7) -> Dict[str, Any]:
        """分析缓存性能
        
        Args:
            days: 分析最近几天的数据
            
        Returns:
            缓存性能分析结果
        """
        try:
            # 获取缓存指标数据
            df = self.storage.get_cache_metrics(days)
            
            if df.empty:
                return {
                    "success": False,
                    "message": "没有可用的缓存指标数据",
                    "data": {}
                }
            
            # 将时间戳转换为datetime
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date
            
            # 计算每日统计
            daily_stats = df.groupby('date').agg({
                'hit_rate': ['mean', 'min', 'max'],
                'miss_rate': ['mean', 'max'],
                'eviction_rate': ['mean', 'max'],
                'shard_count': ['mean', 'max']
            }).reset_index()
            
            # 格式化列名
            daily_stats.columns = [
                'date' if col == 'date' else f"{col[0]}_{col[1]}"
                for col in daily_stats.columns
            ]
            
            # 计算整体统计
            avg_hit_rate = df['hit_rate'].mean()
            min_hit_rate = df['hit_rate'].min()
            max_hit_rate = df['hit_rate'].max()
            
            avg_eviction_rate = df['eviction_rate'].mean()
            avg_shard_count = df['shard_count'].mean()
            
            # 计算趋势
            if len(daily_stats) > 1 and 'hit_rate_mean' in daily_stats.columns:
                x = np.arange(len(daily_stats))
                y = daily_stats['hit_rate_mean'].values
                
                # 线性回归
                slope, intercept = np.polyfit(x, y, 1)
                
                # 趋势类型
                if slope > 1.0:
                    trend_type = "显著改善"
                    trend_class = "excellent"
                elif slope > 0.2:
                    trend_type = "逐步改善"
                    trend_class = "good"
                elif slope < -1.0:
                    trend_type = "显著恶化"
                    trend_class = "high_risk"
                elif slope < -0.2:
                    trend_type = "逐步恶化"
                    trend_class = "medium_risk"
                else:
                    trend_type = "稳定"
                    trend_class = "stable"
                
                # 返回分析结果
                return {
                    "success": True,
                    "data": {
                        "avg_hit_rate": round(avg_hit_rate, 2),
                        "min_hit_rate": round(min_hit_rate, 2),
                        "max_hit_rate": round(max_hit_rate, 2),
                        "avg_eviction_rate": round(avg_eviction_rate, 2),
                        "avg_shard_count": round(avg_shard_count, 2),
                        "trend_slope": round(slope, 4),
                        "trend_type": trend_type,
                        "trend_class": trend_class,
                        "cache_health": self._calculate_cache_health(avg_hit_rate, avg_eviction_rate),
                        "daily_data": daily_stats.to_dict(orient='records'),
                        "days_analyzed": len(daily_stats)
                    }
                }
            else:
                # 数据不足以进行趋势分析
                return {
                    "success": True,
                    "message": "数据点不足，无法进行趋势分析",
                    "data": {
                        "avg_hit_rate": round(avg_hit_rate, 2) if not np.isnan(avg_hit_rate) else 0,
                        "min_hit_rate": round(min_hit_rate, 2) if not np.isnan(min_hit_rate) else 0,
                        "max_hit_rate": round(max_hit_rate, 2) if not np.isnan(max_hit_rate) else 0,
                        "avg_eviction_rate": round(avg_eviction_rate, 2) if not np.isnan(avg_eviction_rate) else 0,
                        "avg_shard_count": round(avg_shard_count, 2) if not np.isnan(avg_shard_count) else 0,
                        "cache_health": self._calculate_cache_health(avg_hit_rate, avg_eviction_rate),
                        "daily_data": daily_stats.to_dict(orient='records') if not daily_stats.empty else [],
                        "days_analyzed": len(daily_stats)
                    }
                }
                
        except Exception as e:
            self.logger.error(f"分析缓存性能失败: {e}")
            return {
                "success": False,
                "message": f"分析失败: {str(e)}",
                "data": {}
            }
    
    def _calculate_cache_health(self, hit_rate: float, eviction_rate: float) -> Dict[str, Any]:
        """计算缓存健康状态
        
        Args:
            hit_rate: 命中率
            eviction_rate: 驱逐率
            
        Returns:
            缓存健康状态
        """
        # 命中率分数 (0-100)
        hit_score = min(100, max(0, hit_rate))
        
        # 驱逐率分数 (0-100, 驱逐率越低越好)
        eviction_score = min(100, max(0, 100 - eviction_rate * 10))
        
        # 综合健康分数 (0-100)
        health_score = int(0.7 * hit_score + 0.3 * eviction_score)
        
        # 健康状态
        if health_score >= 90:
            status = "优秀"
            class_name = "excellent"
        elif health_score >= 75:
            status = "良好"
            class_name = "good"
        elif health_score >= 60:
            status = "一般"
            class_name = "fair"
        elif health_score >= 40:
            status = "较差"
            class_name = "poor"
        else:
            status = "很差"
            class_name = "critical"
        
        return {
            "score": health_score,
            "status": status,
            "class": class_name,
            "hit_score": int(hit_score),
            "eviction_score": int(eviction_score)
        }
    
    def analyze_oom_risks(self, days: int = 7) -> Dict[str, Any]:
        """分析OOM风险
        
        基于内存使用历史和预警记录，分析系统发生OOM的风险。
        
        Args:
            days: 分析最近几天的数据
            
        Returns:
            OOM风险分析结果
        """
        try:
            # 获取内存指标数据
            memory_df = self.storage.get_memory_metrics(days)
            
            # 获取内存预警记录
            alerts_df = self.storage.get_alerts(days)
            memory_alerts = alerts_df[alerts_df['category'] == 'MEMORY'] if not alerts_df.empty else pd.DataFrame()
            
            if memory_df.empty:
                return {
                    "success": False,
                    "message": "没有可用的内存指标数据",
                    "data": {}
                }
            
            # 计算内存使用峰值
            peak_memory_percent = memory_df['memory_percent'].max()
            peak_process_memory = memory_df['process_memory'].max()
            
            # 计算内存使用超过90%的次数
            high_memory_count = len(memory_df[memory_df['memory_percent'] >= 90])
            
            # 计算内存预警次数
            warning_count = len(memory_alerts[memory_alerts['level'] == 'WARNING']) if not memory_alerts.empty else 0
            error_count = len(memory_alerts[memory_alerts['level'] == 'ERROR']) if not memory_alerts.empty else 0
            critical_count = len(memory_alerts[memory_alerts['level'] == 'CRITICAL']) if not memory_alerts.empty else 0
            
            # 预测OOM风险
            predictions = []
            
            # 如果内存曾经超过95%，属于高风险
            if peak_memory_percent >= 95:
                predictions.append({
                    "risk_level": "高",
                    "reason": f"内存使用率曾达到{peak_memory_percent:.1f}%，非常接近系统限制",
                    "recommendation": "建议增加系统内存或减少模型大小"
                })
            
            # 如果收到过严重预警，也属于高风险
            if critical_count > 0:
                predictions.append({
                    "risk_level": "高",
                    "reason": f"过去{days}天内收到过{critical_count}次严重内存预警",
                    "recommendation": "检查模型内存使用，考虑使用更强力的量化"
                })
            
            # 如果内存使用在90-95%之间且有错误预警，属于中高风险
            if peak_memory_percent >= 90 and peak_memory_percent < 95 or error_count > 0:
                predictions.append({
                    "risk_level": "中高",
                    "reason": f"内存使用率曾达到{peak_memory_percent:.1f}%，且收到过{error_count}次错误预警",
                    "recommendation": "监控内存使用，优化缓存配置"
                })
            
            # 如果内存使用在80-90%之间且有警告预警，属于中等风险
            if peak_memory_percent >= 80 and peak_memory_percent < 90 or warning_count > 0:
                predictions.append({
                    "risk_level": "中",
                    "reason": f"内存使用率曾达到{peak_memory_percent:.1f}%，且收到过{warning_count}次警告",
                    "recommendation": "关注内存使用趋势，避免长时间运行"
                })
            
            # 如果内存使用稳定在80%以下，属于低风险
            if peak_memory_percent < 80 and warning_count == 0:
                predictions.append({
                    "risk_level": "低",
                    "reason": f"内存使用率始终低于80%，没有收到过预警",
                    "recommendation": "当前配置适合长时间运行"
                })
            
            # 计算最终风险等级（取最高风险）
            risk_levels = [p["risk_level"] for p in predictions]
            if "高" in risk_levels:
                overall_risk = "高"
                risk_class = "high_risk"
            elif "中高" in risk_levels:
                overall_risk = "中高"
                risk_class = "medium_high_risk"
            elif "中" in risk_levels:
                overall_risk = "中"
                risk_class = "medium_risk"
            else:
                overall_risk = "低"
                risk_class = "low_risk"
            
            # 返回分析结果
            return {
                "success": True,
                "data": {
                    "peak_memory_percent": round(peak_memory_percent, 2),
                    "peak_process_memory_mb": round(peak_process_memory, 2),
                    "high_memory_count": high_memory_count,
                    "warning_count": warning_count,
                    "error_count": error_count,
                    "critical_count": critical_count,
                    "overall_risk": overall_risk,
                    "risk_class": risk_class,
                    "predictions": predictions,
                    "days_analyzed": days
                }
            }
                
        except Exception as e:
            self.logger.error(f"分析OOM风险失败: {e}")
            return {
                "success": False,
                "message": f"分析失败: {str(e)}",
                "data": {}
            }
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """生成内存使用日报
        
        分析最近24小时的内存使用情况，生成详细报告。
        
        Returns:
            包含报告内容的字典
        """
        # 获取过去24小时的数据
        memory_analysis = self.analyze_memory_trends(1)
        cache_analysis = self.analyze_cache_performance(1)
        oom_analysis = self.analyze_oom_risks(1)
        
        # 提取关键指标
        report = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "peak_usage": memory_analysis.get("data", {}).get("peak_memory_percent", 0),
            "avg_usage": memory_analysis.get("data", {}).get("avg_memory_percent", 0),
            "oom_risks": len(oom_analysis.get("data", {}).get("predictions", [])),
            "cache_hit_rate": cache_analysis.get("data", {}).get("avg_hit_rate", 0),
            "memory_trend": memory_analysis.get("data", {}).get("trend_type", "未知"),
            "process_memory_peak": memory_analysis.get("data", {}).get("peak_process_memory_mb", 0),
            "process_memory_avg": memory_analysis.get("data", {}).get("avg_process_memory_mb", 0),
            "system_memory_peak": memory_analysis.get("data", {}).get("peak_system_memory_mb", 0),
            "system_memory_avg": memory_analysis.get("data", {}).get("avg_system_memory_mb", 0),
            "warning_count": oom_analysis.get("data", {}).get("warning_count", 0),
            "error_count": oom_analysis.get("data", {}).get("error_count", 0),
            "critical_count": oom_analysis.get("data", {}).get("critical_count", 0)
        }
        
        # 保存报告
        self._save_report(report, "daily")
        
        return report
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """生成每周内存使用报告
        
        分析最近7天的内存使用情况，生成详细报告，包含趋势和预测。
        
        Returns:
            包含报告内容的字典
        """
        # 获取过去7天的数据
        memory_analysis = self.analyze_memory_trends(7)
        cache_analysis = self.analyze_cache_performance(7)
        oom_analysis = self.analyze_oom_risks(7)
        
        # 提取关键指标
        report = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "period": "weekly",
            "days_analyzed": 7,
            
            # 内存使用统计
            "memory": {
                "peak_percent": memory_analysis.get("data", {}).get("peak_memory_percent", 0),
                "avg_percent": memory_analysis.get("data", {}).get("avg_memory_percent", 0),
                "peak_process_mb": memory_analysis.get("data", {}).get("peak_process_memory_mb", 0),
                "avg_process_mb": memory_analysis.get("data", {}).get("avg_process_memory_mb", 0),
                "peak_system_mb": memory_analysis.get("data", {}).get("peak_system_memory_mb", 0),
                "avg_system_mb": memory_analysis.get("data", {}).get("avg_system_memory_mb", 0),
                "trend": memory_analysis.get("data", {}).get("trend_type", "未知"),
                "trend_slope": memory_analysis.get("data", {}).get("trend_slope", 0),
                "predicted_30d": memory_analysis.get("data", {}).get("predicted_usage_30d", 0),
                "daily_data": memory_analysis.get("data", {}).get("daily_data", [])
            },
            
            # 缓存性能统计
            "cache": {
                "avg_hit_rate": cache_analysis.get("data", {}).get("avg_hit_rate", 0),
                "min_hit_rate": cache_analysis.get("data", {}).get("min_hit_rate", 0),
                "max_hit_rate": cache_analysis.get("data", {}).get("max_hit_rate", 0),
                "avg_eviction_rate": cache_analysis.get("data", {}).get("avg_eviction_rate", 0),
                "health_score": cache_analysis.get("data", {}).get("cache_health", {}).get("score", 0),
                "health_status": cache_analysis.get("data", {}).get("cache_health", {}).get("status", "未知"),
                "trend": cache_analysis.get("data", {}).get("trend_type", "未知"),
                "daily_data": cache_analysis.get("data", {}).get("daily_data", [])
            },
            
            # OOM风险分析
            "oom_risk": {
                "level": oom_analysis.get("data", {}).get("overall_risk", "未知"),
                "warning_count": oom_analysis.get("data", {}).get("warning_count", 0),
                "error_count": oom_analysis.get("data", {}).get("error_count", 0),
                "critical_count": oom_analysis.get("data", {}).get("critical_count", 0),
                "high_memory_count": oom_analysis.get("data", {}).get("high_memory_count", 0),
                "predictions": oom_analysis.get("data", {}).get("predictions", [])
            },
            
            # 综合建议
            "recommendations": self._generate_recommendations(memory_analysis, cache_analysis, oom_analysis)
        }
        
        # 保存报告
        self._save_report(report, "weekly")
        
        return report
    
    def _generate_recommendations(self, memory_analysis, cache_analysis, oom_analysis) -> List[Dict[str, str]]:
        """根据分析结果生成建议
        
        Args:
            memory_analysis: 内存分析结果
            cache_analysis: 缓存分析结果
            oom_analysis: OOM风险分析结果
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 内存相关建议
        memory_trend = memory_analysis.get("data", {}).get("trend_type", "")
        predicted_usage = memory_analysis.get("data", {}).get("predicted_usage_30d", 0)
        
        if memory_trend in ["显著上升", "缓慢上升"] and predicted_usage > 90:
            recommendations.append({
                "category": "memory",
                "priority": "high",
                "title": "内存使用持续增长",
                "description": f"内存使用呈{memory_trend}趋势，预计30天后将达到{predicted_usage:.1f}%，建议检查内存泄漏并考虑增加内存资源。"
            })
        
        # 缓存相关建议
        cache_health = cache_analysis.get("data", {}).get("cache_health", {})
        cache_score = cache_health.get("score", 0)
        
        if cache_score < 60:
            recommendations.append({
                "category": "cache",
                "priority": "medium",
                "title": "缓存效率低下",
                "description": f"缓存健康评分为{cache_score}，状态为'{cache_health.get('status', '')}'，建议调整缓存策略，提高命中率。"
            })
        
        # OOM风险建议
        oom_risk = oom_analysis.get("data", {}).get("overall_risk", "")
        
        if oom_risk in ["高", "中高"]:
            for pred in oom_analysis.get("data", {}).get("predictions", []):
                if pred.get("risk_level") in ["高", "中高"]:
                    recommendations.append({
                        "category": "oom",
                        "priority": "high" if pred.get("risk_level") == "高" else "medium",
                        "title": f"OOM风险{pred.get('risk_level')}",
                        "description": f"{pred.get('reason')}。{pred.get('recommendation')}"
                    })
                    break
        
        # 如果没有严重问题，添加一般性建议
        if not recommendations:
            recommendations.append({
                "category": "general",
                "priority": "low",
                "title": "系统运行良好",
                "description": "当前系统内存使用和缓存效率处于正常水平，建议保持现有配置。"
            })
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any], report_type: str = "daily"):
        """保存报告到文件
        
        Args:
            report: 报告数据
            report_type: 报告类型，如"daily"或"weekly"
        """
        try:
            # 确保报告目录存在
            os.makedirs(self.reports_dir, exist_ok=True)
            
            # 生成报告文件名
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            file_name = f"{report_type}_report_{date_str}.json"
            file_path = os.path.join(self.reports_dir, file_name)
            
            # 保存报告
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"已保存{report_type}报告到 {file_path}")
            
            # 为周报生成图表
            if report_type == "weekly":
                self._generate_charts(report, date_str)
                
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
    
    def _generate_charts(self, report: Dict[str, Any], date_str: str):
        """为报告生成图表
        
        Args:
            report: 报告数据
            date_str: 日期字符串
        """
        try:
            # 确保图表目录存在
            charts_dir = os.path.join(self.reports_dir, "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            # 内存使用趋势图
            memory_data = report.get("memory", {}).get("daily_data", [])
            if memory_data:
                plt.figure(figsize=(10, 6))
                
                # 转换日期字符串
                dates = [d.get("date") for d in memory_data]
                peak_values = [d.get("memory_percent_max", 0) for d in memory_data]
                avg_values = [d.get("memory_percent_mean", 0) for d in memory_data]
                
                plt.plot(dates, peak_values, 'ro-', label='峰值内存使用率')
                plt.plot(dates, avg_values, 'bo-', label='平均内存使用率')
                
                plt.title('内存使用趋势')
                plt.xlabel('日期')
                plt.ylabel('内存使用率 (%)')
                plt.grid(True)
                plt.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # 保存图表
                memory_chart_path = os.path.join(charts_dir, f"memory_trend_{date_str}.png")
                plt.savefig(memory_chart_path)
                plt.close()
                
                self.logger.info(f"已生成内存趋势图: {memory_chart_path}")
            
            # 缓存命中率趋势图
            cache_data = report.get("cache", {}).get("daily_data", [])
            if cache_data:
                plt.figure(figsize=(10, 6))
                
                # 转换日期字符串
                dates = [d.get("date") for d in cache_data]
                hit_rates = [d.get("hit_rate_mean", 0) for d in cache_data]
                
                plt.plot(dates, hit_rates, 'go-', label='缓存命中率')
                
                plt.title('缓存命中率趋势')
                plt.xlabel('日期')
                plt.ylabel('命中率 (%)')
                plt.grid(True)
                plt.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # 保存图表
                cache_chart_path = os.path.join(charts_dir, f"cache_hit_rate_{date_str}.png")
                plt.savefig(cache_chart_path)
                plt.close()
                
                self.logger.info(f"已生成缓存命中率趋势图: {cache_chart_path}")
                
        except Exception as e:
            self.logger.error(f"生成图表失败: {e}") 


# 创建全局实例
_history_analyzer = None


def get_history_analyzer() -> HistoryAnalyzer:
    """获取历史分析器实例
    
    Returns:
        历史分析器实例
    """
    global _history_analyzer
    
    if _history_analyzer is None:
        _history_analyzer = HistoryAnalyzer()
        
    return _history_analyzer


def start_collection(interval: int = 300):
    """启动历史数据采集
    
    Args:
        interval: 采集间隔（秒）
    """
    analyzer = get_history_analyzer()
    analyzer.start_collection(interval)


def stop_collection():
    """停止历史数据采集"""
    analyzer = get_history_analyzer()
    analyzer.stop_collection()


def generate_daily_report() -> Dict[str, Any]:
    """生成内存使用日报
    
    Returns:
        报告数据
    """
    analyzer = get_history_analyzer()
    return analyzer.generate_daily_report()


def generate_weekly_report() -> Dict[str, Any]:
    """生成每周内存使用报告
    
    Returns:
        报告数据
    """
    analyzer = get_history_analyzer()
    return analyzer.generate_weekly_report()


def analyze_memory_trends(days: int = 7) -> Dict[str, Any]:
    """分析内存使用趋势
    
    Args:
        days: 分析最近几天的数据
        
    Returns:
        内存趋势分析结果
    """
    analyzer = get_history_analyzer()
    return analyzer.analyze_memory_trends(days)


def analyze_cache_performance(days: int = 7) -> Dict[str, Any]:
    """分析缓存性能
    
    Args:
        days: 分析最近几天的数据
        
    Returns:
        缓存性能分析结果
    """
    analyzer = get_history_analyzer()
    return analyzer.analyze_cache_performance(days)


def analyze_oom_risks(days: int = 7) -> Dict[str, Any]:
    """分析OOM风险
    
    Args:
        days: 分析最近几天的数据
        
    Returns:
        OOM风险分析结果
    """
    analyzer = get_history_analyzer()
    return analyzer.analyze_oom_risks(days)


def get_latest_reports(report_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """获取最新报告列表
    
    Args:
        report_type: 报告类型，如"daily"或"weekly"，None表示所有类型
        limit: 最大返回数量
        
    Returns:
        报告列表
    """
    analyzer = get_history_analyzer()
    return analyzer.get_latest_reports(report_type, limit)


def start_auto_reports(daily_interval: int = 86400, weekly_interval: int = 604800):
    """启动自动报告生成
    
    Args:
        daily_interval: 日报生成间隔（秒），默认为1天
        weekly_interval: 周报生成间隔（秒），默认为7天
    """
    analyzer = get_history_analyzer()
    analyzer.start_auto_reports(daily_interval, weekly_interval)


def stop_auto_reports():
    """停止自动报告生成"""
    analyzer = get_history_analyzer()
    analyzer.stop_auto_reports()


# 如果作为主程序运行，启动数据采集和自动报告生成
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 历史数据分析工具")
    parser.add_argument("--collect", action="store_true", help="启动数据采集")
    parser.add_argument("--interval", type=int, default=300, help="数据采集间隔（秒）")
    parser.add_argument("--daily", action="store_true", help="生成每日报告")
    parser.add_argument("--weekly", action="store_true", help="生成每周报告")
    parser.add_argument("--auto-reports", action="store_true", help="启动自动报告生成")
    parser.add_argument("--memory-analysis", type=int, nargs="?", const=7, help="分析内存趋势（天数）")
    parser.add_argument("--cache-analysis", type=int, nargs="?", const=7, help="分析缓存性能（天数）")
    parser.add_argument("--oom-analysis", type=int, nargs="?", const=7, help="分析OOM风险（天数）")
    parser.add_argument("--list-reports", action="store_true", help="列出最新报告")
    
    args = parser.parse_args()
    
    # 获取分析器实例
    analyzer = get_history_analyzer()
    
    # 根据参数执行操作
    if args.collect:
        print(f"启动数据采集，间隔: {args.interval}秒")
        analyzer.start_collection(args.interval)
    
    if args.daily:
        print("生成每日报告...")
        report = analyzer.generate_daily_report()
        print(f"报告已保存至: {analyzer.reports_dir}")
        
    if args.weekly:
        print("生成每周报告...")
        report = analyzer.generate_weekly_report()
        print(f"报告已保存至: {analyzer.reports_dir}")
        
    if args.auto_reports:
        print("启动自动报告生成...")
        analyzer.start_auto_reports()
        
    if args.memory_analysis is not None:
        print(f"分析最近{args.memory_analysis}天的内存趋势...")
        result = analyzer.analyze_memory_trends(args.memory_analysis)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    if args.cache_analysis is not None:
        print(f"分析最近{args.cache_analysis}天的缓存性能...")
        result = analyzer.analyze_cache_performance(args.cache_analysis)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    if args.oom_analysis is not None:
        print(f"分析最近{args.oom_analysis}天的OOM风险...")
        result = analyzer.analyze_oom_risks(args.oom_analysis)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    if args.list_reports:
        print("最新报告列表:")
        reports = analyzer.get_latest_reports()
        for i, report in enumerate(reports, 1):
            report_type = "日报" if "daily" in report.get('file_name', '') else "周报"
            date = report.get('datetime', '未知时间').split('T')[0]
            print(f"{i}. {report_type} {date} - {report.get('file_path', '')}")
    
    # 如果没有指定任何操作，打印帮助信息
    if not any(vars(args).values()):
        parser.print_help() 