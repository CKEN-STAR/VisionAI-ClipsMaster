#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
审计可视化模块

提供审计数据的图表展示功能，包括操作统计、时间分布、安全事件分析等。
支持多种图表类型和交互式数据探索。
"""

import os
import json
import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import logging
import re

# 导入审计追踪模块
from src.dashboard.audit_trail import get_audit_trail, AuditCategory, AuditLevel

# 导入可视化库
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# 获取模块日志记录器
logger = logging.getLogger(__name__)

class ChartType(str, Enum):
    """图表类型枚举"""
    BAR = "bar"           # 柱状图
    LINE = "line"         # 折线图
    PIE = "pie"           # 饼图
    HEATMAP = "heatmap"   # 热力图
    SCATTER = "scatter"   # 散点图

class AuditVisualizer:
    """审计数据可视化类"""
    
    def __init__(self):
        """初始化审计可视化类"""
        self.audit_trail = get_audit_trail()
        
        # 检查可视化依赖项
        if not HAS_MATPLOTLIB:
            logger.warning("未找到 matplotlib 库，部分可视化功能将不可用")
        
        if not HAS_PANDAS:
            logger.warning("未找到 pandas 库，部分数据处理功能将不可用")
    
    def create_operation_chart(self, 
                              start_date: Optional[datetime.datetime] = None,
                              end_date: Optional[datetime.datetime] = None,
                              chart_type: str = ChartType.BAR) -> Optional[Figure]:
        """
        创建操作统计图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            chart_type: 图表类型
            
        Returns:
            matplotlib图表对象
        """
        if not HAS_MATPLOTLIB:
            logger.error("未安装matplotlib，无法创建图表")
            return None
        
        # 获取审计数据
        logs = self.audit_trail.search_logs({}, start_date, end_date, limit=10000)
        
        if not logs:
            logger.warning("未找到审计数据，无法创建图表")
            return None
        
        # 统计各种操作类型
        operation_counts = {}
        for log in logs:
            action = log.get("action", "unknown")
            if action in operation_counts:
                operation_counts[action] += 1
            else:
                operation_counts[action] = 1
        
        # 排序，取前10个最常见的操作
        sorted_ops = sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)
        top_ops = sorted_ops[:10]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == ChartType.BAR:
            # 创建柱状图
            actions = [op[0] for op in top_ops]
            counts = [op[1] for op in top_ops]
            ax.bar(actions, counts, color='skyblue')
            ax.set_xlabel('操作类型')
            ax.set_ylabel('次数')
            ax.set_title('操作类型统计 (Top 10)')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
        elif chart_type == ChartType.PIE:
            # 创建饼图
            actions = [op[0] for op in top_ops]
            counts = [op[1] for op in top_ops]
            ax.pie(counts, labels=actions, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('操作类型分布 (Top 10)')
            
        return fig
    
    def create_time_distribution_chart(self,
                                     start_date: Optional[datetime.datetime] = None,
                                     end_date: Optional[datetime.datetime] = None) -> Optional[Figure]:
        """
        创建时间分布图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            matplotlib图表对象
        """
        if not HAS_MATPLOTLIB or not HAS_PANDAS:
            logger.error("未安装必要的依赖库，无法创建图表")
            return None
        
        # 获取审计数据
        logs = self.audit_trail.search_logs({}, start_date, end_date, limit=10000)
        
        if not logs:
            logger.warning("未找到审计数据，无法创建图表")
            return None
        
        # 提取时间戳
        timestamps = []
        for log in logs:
            try:
                if "timestamp" in log:
                    timestamp = datetime.datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                    timestamps.append(timestamp)
            except (ValueError, TypeError):
                continue
        
        if not timestamps:
            logger.warning("未找到有效的时间戳数据，无法创建图表")
            return None
        
        # 转换为Pandas Series
        ts_series = pd.Series(timestamps)
        
        # 按小时分组统计
        hourly_counts = ts_series.groupby(ts_series.dt.floor('H')).size()
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(hourly_counts.index, hourly_counts.values, marker='o', linestyle='-')
        ax.set_xlabel('时间')
        ax.set_ylabel('操作次数')
        ax.set_title('操作时间分布')
        
        # 设置X轴日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig
    
    def create_security_events_chart(self,
                                   start_date: Optional[datetime.datetime] = None,
                                   end_date: Optional[datetime.datetime] = None) -> Optional[Figure]:
        """
        创建安全事件分析图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            matplotlib图表对象
        """
        if not HAS_MATPLOTLIB:
            logger.error("未安装matplotlib，无法创建图表")
            return None
        
        # 查询安全事件相关的日志
        security_logs = self.audit_trail.search_logs(
            {"level": AuditLevel.HIGH}, start_date, end_date, limit=1000
        )
        
        if not security_logs:
            logger.warning("未找到安全事件数据，无法创建图表")
            return None
        
        # 按类型分类安全事件
        event_types = {}
        for log in security_logs:
            # 从action或category中提取事件类型
            event_type = log.get("action", "unknown")
            if event_type in event_types:
                event_types[event_type] += 1
            else:
                event_types[event_type] = 1
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 绘制柱状图
        event_labels = list(event_types.keys())
        event_counts = list(event_types.values())
        
        bars = ax.bar(event_labels, event_counts, color='salmon')
        ax.set_xlabel('事件类型')
        ax.set_ylabel('次数')
        ax.set_title('安全事件分布')
        plt.xticks(rotation=45, ha='right')
        
        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.0f}',
                    ha='center', va='bottom')
        
        plt.tight_layout()
        return fig
    
    def create_user_activity_chart(self,
                                 start_date: Optional[datetime.datetime] = None,
                                 end_date: Optional[datetime.datetime] = None) -> Optional[Figure]:
        """
        创建用户活动图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            matplotlib图表对象
        """
        if not HAS_MATPLOTLIB:
            logger.error("未安装matplotlib，无法创建图表")
            return None
        
        # 获取审计数据
        logs = self.audit_trail.search_logs({}, start_date, end_date, limit=10000)
        
        if not logs:
            logger.warning("未找到审计数据，无法创建图表")
            return None
        
        # 按用户分组统计活动
        user_activity = {}
        for log in logs:
            user = log.get("user", "unknown")
            if user in user_activity:
                user_activity[user] += 1
            else:
                user_activity[user] = 1
        
        # 排序，获取活动最多的用户
        sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)
        top_users = sorted_users[:10]  # 取前10名用户
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        users = [user[0] for user in top_users]
        activity_counts = [user[1] for user in top_users]
        
        ax.bar(users, activity_counts, color='lightgreen')
        ax.set_xlabel('用户')
        ax.set_ylabel('活动次数')
        ax.set_title('用户活动统计 (Top 10)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig
    
    def create_category_distribution_chart(self,
                                         start_date: Optional[datetime.datetime] = None,
                                         end_date: Optional[datetime.datetime] = None) -> Optional[Figure]:
        """
        创建操作类别分布图表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            matplotlib图表对象
        """
        if not HAS_MATPLOTLIB:
            logger.error("未安装matplotlib，无法创建图表")
            return None
        
        # 获取审计数据
        logs = self.audit_trail.search_logs({}, start_date, end_date, limit=10000)
        
        if not logs:
            logger.warning("未找到审计数据，无法创建图表")
            return None
        
        # 按类别分组统计
        category_counts = {}
        for log in logs:
            category = log.get("category", "unknown")
            if category in category_counts:
                category_counts[category] += 1
            else:
                category_counts[category] = 1
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 绘制饼图
        categories = list(category_counts.keys())
        counts = list(category_counts.values())
        
        ax.pie(counts, labels=categories, autopct='%1.1f%%', startangle=90, 
               shadow=True, explode=[0.05] * len(categories))
        ax.axis('equal')
        ax.set_title('操作类别分布')
        
        plt.tight_layout()
        return fig

# 创建审计可视化实例
_audit_visualizer_instance = None

def get_audit_visualizer() -> AuditVisualizer:
    """
    获取审计可视化实例（单例模式）
    
    Returns:
        AuditVisualizer实例
    """
    global _audit_visualizer_instance
    if _audit_visualizer_instance is None:
        _audit_visualizer_instance = AuditVisualizer()
    return _audit_visualizer_instance

# 便捷函数
def create_operation_chart(start_date=None, end_date=None, chart_type=ChartType.BAR):
    """创建操作统计图表"""
    return get_audit_visualizer().create_operation_chart(start_date, end_date, chart_type)

def create_time_distribution_chart(start_date=None, end_date=None):
    """创建时间分布图表"""
    return get_audit_visualizer().create_time_distribution_chart(start_date, end_date)

def create_security_events_chart(start_date=None, end_date=None):
    """创建安全事件分析图表"""
    return get_audit_visualizer().create_security_events_chart(start_date, end_date)

def create_user_activity_chart(start_date=None, end_date=None):
    """创建用户活动图表"""
    return get_audit_visualizer().create_user_activity_chart(start_date, end_date)

def create_category_distribution_chart(start_date=None, end_date=None):
    """创建操作类别分布图表"""
    return get_audit_visualizer().create_category_distribution_chart(start_date, end_date) 