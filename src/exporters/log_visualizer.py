#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志可视化模块

提供结构化日志的可视化功能，生成交互式图表和仪表板。
支持性能监控、资源使用分析和错误情况展示。
"""

import os
import json
import datetime
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.exporters.log_analyzer import LogAnalyzer
from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory

# 模块日志记录器
logger = get_module_logger("log_visualizer")

class LogVisualizer:
    """
    日志可视化类
    
    生成结构化日志的可视化图表和仪表板。
    """
    
    def __init__(self, analyzer: Optional[LogAnalyzer] = None, log_dir: Optional[Union[str, Path]] = None):
        """
        初始化日志可视化器
        
        Args:
            analyzer: 日志分析器实例，如果为None则创建新实例
            log_dir: 日志目录（默认使用跨平台日志目录）
        """
        if log_dir is not None:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = get_log_directory() / "structured"
            
        self.analyzer = analyzer or LogAnalyzer(log_dir=self.log_dir)
        
    def load_data(self, **kwargs) -> bool:
        """
        加载日志数据
        
        Args:
            **kwargs: 传递给LogAnalyzer.load_logs的参数
            
        Returns:
            是否成功加载数据
        """
        return self.analyzer.load_logs(**kwargs)
        
    def create_operation_summary(self) -> go.Figure:
        """
        创建操作统计图表
        
        Returns:
            操作统计图表
        """
        # 获取操作数据
        ops_df = self.analyzer.get_operations()
        
        if len(ops_df) == 0:
            logger.warning("没有操作数据")
            # 返回空图表
            return go.Figure().update_layout(
                title="操作统计 (无数据)",
                annotations=[dict(
                    text="无操作数据",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )]
            )
            
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "操作类型分布", 
                "操作结果分布",
                "每日操作统计",
                "操作时长统计"
            ),
            specs=[
                [{"type": "pie"}, {"type": "pie"}],
                [{"type": "bar"}, {"type": "bar"}]
            ]
        )
        
        # 1. 操作类型分布
        op_counts = ops_df["operation"].value_counts()
        fig.add_trace(
            go.Pie(
                labels=op_counts.index,
                values=op_counts.values,
                textinfo="percent+label",
                hole=0.3,
                name="操作类型"
            ),
            row=1, col=1
        )
        
        # 2. 操作结果分布
        if "result" in ops_df.columns:
            result_counts = ops_df["result"].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=result_counts.index,
                    values=result_counts.values,
                    textinfo="percent+label",
                    hole=0.3,
                    marker_colors=["green", "orange", "red"],
                    name="操作结果"
                ),
                row=1, col=2
            )
        
        # 3. 每日操作统计
        if "timestamp" in ops_df.columns:
            ops_df["date"] = ops_df["timestamp"].dt.date
            daily_counts = ops_df.groupby("date")["operation"].count().reset_index()
            daily_counts.columns = ["date", "count"]
            
            fig.add_trace(
                go.Bar(
                    x=daily_counts["date"],
                    y=daily_counts["count"],
                    name="每日操作数"
                ),
                row=2, col=1
            )
        
        # 4. 操作时长统计
        if "stats_processing_time" in ops_df.columns:
            op_times = ops_df.groupby("operation")["stats_processing_time"].mean().reset_index()
            op_times.columns = ["operation", "avg_time"]
            
            fig.add_trace(
                go.Bar(
                    x=op_times["operation"],
                    y=op_times["avg_time"],
                    name="平均处理时间(秒)"
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title_text="操作统计",
            height=700,
            showlegend=False
        )
        
        return fig
        
    def create_resource_usage_chart(self) -> go.Figure:
        """
        创建资源使用图表
        
        Returns:
            资源使用图表
        """
        # 获取操作数据
        ops_df = self.analyzer.get_operations()
        
        if len(ops_df) == 0 or "timestamp" not in ops_df.columns:
            logger.warning("没有资源使用数据")
            # 返回空图表
            return go.Figure().update_layout(
                title="资源使用 (无数据)",
                annotations=[dict(
                    text="无资源使用数据",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )]
            )
            
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("内存使用趋势", "CPU使用趋势"),
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # 按时间排序
        ops_df = ops_df.sort_values("timestamp")
        
        # 1. 内存使用趋势
        if "memory_mb" in ops_df.columns:
            # 为每种操作类型添加一条线
            for operation, group in ops_df.groupby("operation"):
                fig.add_trace(
                    go.Scatter(
                        x=group["timestamp"],
                        y=group["memory_mb"],
                        mode="lines+markers",
                        name=f"{operation} - 内存",
                        line=dict(width=1),
                        marker=dict(size=5)
                    ),
                    row=1, col=1
                )
        
        # 2. CPU使用趋势
        if "cpu_percent" in ops_df.columns:
            # 为每种操作类型添加一条线
            for operation, group in ops_df.groupby("operation"):
                fig.add_trace(
                    go.Scatter(
                        x=group["timestamp"],
                        y=group["cpu_percent"],
                        mode="lines+markers",
                        name=f"{operation} - CPU",
                        line=dict(width=1),
                        marker=dict(size=5)
                    ),
                    row=2, col=1
                )
        
        # 更新布局
        fig.update_layout(
            title_text="资源使用趋势",
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="内存使用 (MB)", row=1, col=1)
        fig.update_yaxes(title_text="CPU使用 (%)", row=2, col=1)
        
        return fig
        
    def create_performance_chart(self) -> go.Figure:
        """
        创建性能分析图表
        
        Returns:
            性能分析图表
        """
        # 获取操作数据
        ops_df = self.analyzer.get_operations()
        
        if len(ops_df) == 0:
            logger.warning("没有性能数据")
            # 返回空图表
            return go.Figure().update_layout(
                title="性能分析 (无数据)",
                annotations=[dict(
                    text="无性能数据",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )]
            )
            
        # 检查是否有处理时间数据
        if "stats_processing_time" not in ops_df.columns:
            logger.warning("没有处理时间数据")
            # 返回空图表
            return go.Figure().update_layout(
                title="性能分析 (无处理时间数据)",
                annotations=[dict(
                    text="无处理时间数据",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )]
            )
            
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "操作处理时间分布", 
                "各操作平均处理时间",
                "处理时间vs.内存使用",
                "处理时间变化趋势"
            ),
            specs=[
                [{"type": "box"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "scatter"}]
            ]
        )
        
        # 1. 操作处理时间分布
        fig.add_trace(
            go.Box(
                x=ops_df["operation"],
                y=ops_df["stats_processing_time"],
                name="处理时间分布"
            ),
            row=1, col=1
        )
        
        # 2. 各操作平均处理时间
        avg_times = ops_df.groupby("operation")["stats_processing_time"].mean().reset_index()
        fig.add_trace(
            go.Bar(
                x=avg_times["operation"],
                y=avg_times["stats_processing_time"],
                name="平均处理时间"
            ),
            row=1, col=2
        )
        
        # 3. 处理时间vs.内存使用
        if "memory_mb" in ops_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=ops_df["stats_processing_time"],
                    y=ops_df["memory_mb"],
                    mode="markers",
                    marker=dict(
                        color=ops_df["operation"].astype("category").cat.codes,
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title="操作类型")
                    ),
                    name="内存使用"
                ),
                row=2, col=1
            )
        
        # 4. 处理时间变化趋势
        if "timestamp" in ops_df.columns:
            # 按时间排序
            time_df = ops_df.sort_values("timestamp")
            
            # 为每种操作类型添加一条线
            for operation, group in time_df.groupby("operation"):
                fig.add_trace(
                    go.Scatter(
                        x=group["timestamp"],
                        y=group["stats_processing_time"],
                        mode="lines+markers",
                        name=f"{operation} - 时间趋势",
                        line=dict(width=1),
                        marker=dict(size=5)
                    ),
                    row=2, col=2
                )
        
        # 更新布局
        fig.update_layout(
            title_text="性能分析",
            height=700,
            showlegend=False
        )
        
        fig.update_yaxes(title_text="处理时间 (秒)", row=1, col=1)
        fig.update_yaxes(title_text="平均处理时间 (秒)", row=1, col=2)
        fig.update_xaxes(title_text="处理时间 (秒)", row=2, col=1)
        fig.update_yaxes(title_text="内存使用 (MB)", row=2, col=1)
        fig.update_yaxes(title_text="处理时间 (秒)", row=2, col=2)
        
        return fig
        
    def create_error_analysis_chart(self) -> go.Figure:
        """
        创建错误分析图表
        
        Returns:
            错误分析图表
        """
        # 获取错误数据
        errors_df = self.analyzer.get_errors()
        
        if len(errors_df) == 0:
            logger.warning("没有错误数据")
            # 返回空图表
            return go.Figure().update_layout(
                title="错误分析 (无数据)",
                annotations=[dict(
                    text="无错误数据",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5
                )]
            )
            
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "错误类型分布", 
                "各操作错误数量",
                "错误时间分布",
                "错误时内存使用"
            ),
            specs=[
                [{"type": "pie"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "box"}]
            ]
        )
        
        # 1. 错误类型分布
        if "error_code" in errors_df.columns:
            error_counts = errors_df["error_code"].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=error_counts.index,
                    values=error_counts.values,
                    textinfo="percent+label",
                    hole=0.3,
                    name="错误类型"
                ),
                row=1, col=1
            )
        
        # 2. 各操作错误数量
        if "operation" in errors_df.columns:
            op_error_counts = errors_df["operation"].value_counts().reset_index()
            op_error_counts.columns = ["operation", "count"]
            
            fig.add_trace(
                go.Bar(
                    x=op_error_counts["operation"],
                    y=op_error_counts["count"],
                    name="错误数量"
                ),
                row=1, col=2
            )
        
        # 3. 错误时间分布
        if "timestamp" in errors_df.columns:
            # 按日期分组
            errors_df["date"] = errors_df["timestamp"].dt.date
            date_error_counts = errors_df.groupby("date").size().reset_index()
            date_error_counts.columns = ["date", "count"]
            
            fig.add_trace(
                go.Bar(
                    x=date_error_counts["date"],
                    y=date_error_counts["count"],
                    name="每日错误数"
                ),
                row=2, col=1
            )
        
        # 4. 错误时内存使用
        # 获取操作数据中的内存信息
        ops_df = self.analyzer.get_operations()
        
        if "memory_mb" in ops_df.columns and "result" in ops_df.columns:
            # 分组为成功和错误
            success_mem = ops_df[ops_df["result"] == "success"]["memory_mb"]
            error_mem = ops_df[ops_df["result"] == "error"]["memory_mb"]
            
            fig.add_trace(
                go.Box(
                    y=success_mem,
                    name="成功操作",
                    marker_color="green"
                ),
                row=2, col=2
            )
            
            fig.add_trace(
                go.Box(
                    y=error_mem,
                    name="失败操作",
                    marker_color="red"
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            title_text="错误分析",
            height=700,
            showlegend=False
        )
        
        fig.update_yaxes(title_text="错误数量", row=1, col=2)
        fig.update_yaxes(title_text="错误数量", row=2, col=1)
        fig.update_yaxes(title_text="内存使用 (MB)", row=2, col=2)
        
        return fig
        
    def create_dashboard(self, output_path: Union[str, Path] = None) -> str:
        """
        创建可视化仪表板
        
        Args:
            output_path: 输出文件路径（默认使用跨平台日志目录）
            
        Returns:
            仪表板HTML文件路径
        """
        # 使用跨平台日志目录
        if output_path is None:
            output_dir = get_log_directory() / "dashboard"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "dashboard.html"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建HTML页面
        html = "<html>\n<head>\n"
        html += "<title>日志分析仪表板</title>\n"
        html += "<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>\n"
        html += "<style>\n"
        html += "body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }\n"
        html += ".dashboard { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }\n"
        html += "h1 { color: #333; text-align: center; }\n"
        html += ".chart { margin-bottom: 30px; }\n"
        html += ".summary { display: flex; justify-content: space-between; margin-bottom: 20px; }\n"
        html += ".summary-box { flex: 1; margin: 0 10px; padding: 15px; background-color: #e8f4f8; border-radius: 5px; text-align: center; }\n"
        html += ".chart-title { font-weight: bold; margin-bottom: 10px; }\n"
        html += "</style>\n"
        html += "</head>\n<body>\n"
        
        html += "<div class='dashboard'>\n"
        html += f"<h1>日志分析仪表板 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})</h1>\n"
        
        # 添加摘要信息
        stats = self.analyzer.get_statistics()
        html += "<div class='summary'>\n"
        html += f"<div class='summary-box'><div class='chart-title'>总操作数</div>{stats.get('total_operations', 0)}</div>\n"
        html += f"<div class='summary-box'><div class='chart-title'>成功率</div>{stats.get('success_rate', 0):.1f}%</div>\n"
        html += f"<div class='summary-box'><div class='chart-title'>平均处理时间</div>{stats.get('avg_processing_time', 0):.2f} 秒</div>\n"
        html += f"<div class='summary-box'><div class='chart-title'>错误数</div>{stats.get('error_count', 0)}</div>\n"
        html += "</div>\n"
        
        # 添加图表
        # 1. 操作统计
        html += "<div class='chart'>\n"
        html += "<div class='chart-title'>操作统计</div>\n"
        fig = self.create_operation_summary()
        html += fig.to_html(full_html=False, include_plotlyjs=False)
        html += "</div>\n"
        
        # 2. 资源使用
        html += "<div class='chart'>\n"
        html += "<div class='chart-title'>资源使用</div>\n"
        fig = self.create_resource_usage_chart()
        html += fig.to_html(full_html=False, include_plotlyjs=False)
        html += "</div>\n"
        
        # 3. 性能监控
        html += "<div class='chart'>\n"
        html += "<div class='chart-title'>性能监控</div>\n"
        fig = self.create_performance_chart()
        html += fig.to_html(full_html=False, include_plotlyjs=False)
        html += "</div>\n"
        
        # 4. 错误分析
        html += "<div class='chart'>\n"
        html += "<div class='chart-title'>错误分析</div>\n"
        fig = self.create_error_analysis_chart()
        html += fig.to_html(full_html=False, include_plotlyjs=False)
        html += "</div>\n"
        
        html += "</div>\n"
        html += "</body>\n</html>"
        
        # 写入文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
            
        logger.info(f"仪表板已保存至: {output_path}")
        return str(output_path)

    def generate_dashboard(self, session_id: Optional[str] = None,
                         date: Optional[Union[str, datetime.date]] = None,
                         output_path: Union[str, Path] = None) -> str:
        """
        生成日志仪表盘
        
        Args:
            session_id: 会话ID
            date: 日期
            output_path: 输出文件路径（默认使用跨平台日志目录）
            
        Returns:
            仪表盘HTML文件路径
        """
        # 加载数据
        success = self.load_data(
            session_id=session_id,
            date=date,
            recursive=True
        )
        
        if not success:
            logger.warning("加载日志失败，无法生成仪表盘")
            return ""
            
        # 创建仪表盘
        return self.create_dashboard(output_path=output_path)

if __name__ == "__main__":
    # 测试代码
    analyzer = LogAnalyzer(log_dir="logs/structured")
    visualizer = LogVisualizer(analyzer)
    
    # 加载日志
    success = visualizer.load_data(recursive=True)
    
    if success:
        # 创建仪表板
        dashboard_path = visualizer.create_dashboard("logs/test_dashboard.html")
        if dashboard_path:
            print(f"仪表板已生成: {dashboard_path}") 