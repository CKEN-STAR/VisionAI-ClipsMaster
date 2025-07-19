#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志分析器模块

提供结构化日志的分析功能，包括日志查询、统计和可视化。
用于支持应用程序性能监控、错误分析和使用情况跟踪。
"""

import os
import json
import datetime
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple
import matplotlib.pyplot as plt
from collections import Counter, defaultdict

from src.exporters.log_schema import EXPORT_LOG_SCHEMA
from src.utils.logger import get_module_logger

# 模块日志记录器
logger = get_module_logger("log_analyzer")

class LogAnalyzer:
    """
    日志分析器类
    
    分析结构化日志数据，提供统计分析和可视化功能。
    """
    
    def __init__(self, log_dir: Union[str, Path] = "logs/structured"):
        """
        初始化日志分析器
        
        Args:
            log_dir: 日志文件目录
        """
        self.log_dir = Path(log_dir)
        self.df = None  # 数据帧，用于分析
        
    def load_logs(self, session_id: Optional[str] = None, 
                 date: Optional[Union[str, datetime.date]] = None,
                 recursive: bool = False) -> bool:
        """
        加载日志文件
        
        Args:
            session_id: 会话ID，如果提供则只加载该会话的日志
            date: 日期，如果提供则只加载该日期的日志
            recursive: 是否递归加载所有子目录的日志
            
        Returns:
            是否成功加载日志
        """
        try:
            # 构建日志文件路径模式
            if date is None:
                date_pattern = "*"
            elif isinstance(date, datetime.date):
                date_pattern = date.strftime("%Y-%m-%d")
            else:
                date_pattern = date
                
            if session_id is None:
                session_pattern = "*"
            else:
                session_pattern = session_id
                
            # 构建文件查找模式
            if recursive:
                pattern = str(self.log_dir / "**" / date_pattern / session_pattern / "*.jsonl")
                log_files = glob.glob(pattern, recursive=True)
            else:
                pattern = str(self.log_dir / date_pattern / session_pattern / "*.jsonl")
                log_files = glob.glob(pattern)
                
            if not log_files:
                logger.warning(f"未找到匹配的日志文件: {pattern}")
                return False
                
            # 读取所有日志文件
            all_logs = []
            for log_file in log_files:
                logs = self._read_log_file(log_file)
                all_logs.extend(logs)
                
            if not all_logs:
                logger.warning("日志文件为空")
                return False
                
            # 转换为DataFrame
            self.df = pd.DataFrame(all_logs)
            
            # 转换时间戳列为日期时间类型
            if "timestamp" in self.df.columns:
                self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
                
            logger.info(f"成功加载 {len(self.df)} 条日志记录")
            return True
        except Exception as e:
            logger.error(f"加载日志失败: {str(e)}")
            return False
            
    def _read_log_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        读取单个日志文件
        
        Args:
            file_path: 日志文件路径
            
        Returns:
            日志记录列表
        """
        logs = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
            return logs
        except Exception as e:
            logger.error(f"读取日志文件 {file_path} 失败: {str(e)}")
            return []
            
    def get_sessions(self) -> pd.DataFrame:
        """
        获取所有会话信息
        
        Returns:
            会话信息DataFrame
        """
        if self.df is None or len(self.df) == 0:
            logger.warning("没有加载日志数据")
            return pd.DataFrame()
            
        # 筛选会话开始和结束记录
        session_starts = self.df[self.df["event_type"] == "session_start"]
        session_ends = self.df[self.df["event_type"] == "session_end"]
        
        sessions = []
        
        # 处理会话开始记录
        for _, row in session_starts.iterrows():
            session_id = row.get("session_id")
            start_time = row.get("timestamp")
            system_info = row.get("system_info", {})
            
            # 查找对应的会话结束记录
            end_row = session_ends[session_ends["session_id"] == session_id]
            
            if len(end_row) > 0:
                end_time = end_row.iloc[0].get("timestamp")
                duration = end_row.iloc[0].get("session_duration", 0)
            else:
                end_time = None
                duration = None
                
            sessions.append({
                "session_id": session_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "os": system_info.get("os", ""),
                "os_version": system_info.get("os_version", ""),
                "cpu_count": system_info.get("cpu_count", 0),
                "total_memory_mb": system_info.get("total_memory_mb", 0)
            })
            
        return pd.DataFrame(sessions)
        
    def get_operations(self) -> pd.DataFrame:
        """
        获取所有操作记录
        
        Returns:
            操作记录DataFrame
        """
        if self.df is None or len(self.df) == 0:
            logger.warning("没有加载日志数据")
            return pd.DataFrame()
            
        # 筛选包含operation字段的记录
        ops_df = self.df[self.df["operation"].notna()].copy()
        
        if len(ops_df) == 0:
            return pd.DataFrame()
            
        # 提取资源使用信息
        def extract_resource(row):
            resource = row.get("resource_usage", {})
            if isinstance(resource, dict):
                row["memory_mb"] = resource.get("memory_mb", 0)
                row["cpu_percent"] = resource.get("cpu_percent", 0)
                row["gpu_util"] = resource.get("gpu_util", 0)
            return row
            
        # 应用提取函数
        ops_df = ops_df.apply(extract_resource, axis=1)
        
        # 提取处理统计信息
        def extract_stats(row):
            stats = row.get("processing_stats", {})
            if isinstance(stats, dict):
                for key, value in stats.items():
                    row[f"stats_{key}"] = value
            return row
            
        # 应用提取函数
        ops_df = ops_df.apply(extract_stats, axis=1)
        
        # 选择感兴趣的列
        columns = ["timestamp", "operation", "result", "event_type", 
                  "memory_mb", "cpu_percent", "gpu_util",
                  "session_id"]
        
        # 添加处理统计列（如果存在）
        stats_cols = [col for col in ops_df.columns if col.startswith("stats_")]
        columns.extend(stats_cols)
        
        # 筛选存在的列
        existing_cols = [col for col in columns if col in ops_df.columns]
        
        return ops_df[existing_cols]
        
    def get_errors(self) -> pd.DataFrame:
        """
        获取所有错误记录
        
        Returns:
            错误记录DataFrame
        """
        if self.df is None or len(self.df) == 0:
            logger.warning("没有加载日志数据")
            return pd.DataFrame()
            
        # 筛选错误记录
        errors_df = self.df[(self.df["result"] == "error") | 
                          (self.df["error"].notna())].copy()
        
        if len(errors_df) == 0:
            return pd.DataFrame()
            
        # 提取错误信息
        def extract_error(row):
            error = row.get("error", {})
            if isinstance(error, dict):
                row["error_code"] = error.get("code", "")
                row["error_message"] = error.get("message", "")
            return row
            
        # 应用提取函数
        errors_df = errors_df.apply(extract_error, axis=1)
        
        # 选择感兴趣的列
        columns = ["timestamp", "operation", "event_type", "error_code", 
                  "error_message", "session_id"]
        
        # 筛选存在的列
        existing_cols = [col for col in columns if col in errors_df.columns]
        
        return errors_df[existing_cols]
        
    def analyze_performance(self) -> Dict[str, Any]:
        """
        分析性能数据
        
        Returns:
            性能分析结果
        """
        if self.df is None or len(self.df) == 0:
            logger.warning("没有加载日志数据")
            return {}
            
        ops_df = self.get_operations()
        
        if len(ops_df) == 0:
            return {}
            
        # 按操作类型分组
        grouped = ops_df.groupby("operation")
        
        results = {}
        
        # 内存使用
        if "memory_mb" in ops_df.columns:
            results["memory"] = {
                "overall_avg": ops_df["memory_mb"].mean(),
                "overall_max": ops_df["memory_mb"].max(),
                "by_operation": grouped["memory_mb"].agg(['mean', 'max']).to_dict('index')
            }
            
        # CPU使用
        if "cpu_percent" in ops_df.columns:
            results["cpu"] = {
                "overall_avg": ops_df["cpu_percent"].mean(),
                "overall_max": ops_df["cpu_percent"].max(),
                "by_operation": grouped["cpu_percent"].agg(['mean', 'max']).to_dict('index')
            }
            
        # 处理时间
        if "stats_processing_time" in ops_df.columns:
            results["processing_time"] = {
                "overall_avg": ops_df["stats_processing_time"].mean(),
                "overall_max": ops_df["stats_processing_time"].max(),
                "by_operation": grouped["stats_processing_time"].agg(['mean', 'max']).to_dict('index')
            }
            
        # 操作结果统计
        if "result" in ops_df.columns:
            results["results"] = dict(ops_df["result"].value_counts())
            results["success_rate"] = (ops_df["result"] == "success").mean() * 100
            
            # 按操作类型统计成功率
            success_by_op = {}
            for op, group in grouped:
                success_by_op[op] = (group["result"] == "success").mean() * 100
            results["success_rate_by_operation"] = success_by_op
            
        return results
        
    def generate_report(self, output_dir: Union[str, Path] = "logs/reports",
                      title: str = "日志分析报告") -> str:
        """
        生成分析报告
        
        Args:
            output_dir: 输出目录
            title: 报告标题
            
        Returns:
            报告文件路径
        """
        if self.df is None or len(self.df) == 0:
            logger.warning("没有加载日志数据")
            return ""
            
        # 创建输出目录
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建报告文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"log_report_{timestamp}.html"
        
        # 生成报告内容
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import jinja2
            
            # 获取数据
            sessions_df = self.get_sessions()
            ops_df = self.get_operations()
            errors_df = self.get_errors()
            perf_data = self.analyze_performance()
            
            # 创建图形
            figures = []
            
            # 1. 操作统计图
            if len(ops_df) > 0:
                op_counts = ops_df["operation"].value_counts().reset_index()
                op_counts.columns = ["operation", "count"]
                
                fig = px.bar(op_counts, x="operation", y="count", 
                           title="操作类型统计",
                           labels={"operation": "操作类型", "count": "操作次数"})
                figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                
                # 操作结果统计
                if "result" in ops_df.columns:
                    result_counts = ops_df["result"].value_counts().reset_index()
                    result_counts.columns = ["result", "count"]
                    
                    fig = px.pie(result_counts, names="result", values="count",
                               title="操作结果统计",
                               labels={"result": "结果", "count": "次数"},
                               color="result",
                               color_discrete_map={"success": "green", "warning": "orange", "error": "red"})
                    figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                    
            # 2. 内存使用趋势
            if len(ops_df) > 0 and "memory_mb" in ops_df.columns:
                fig = px.line(ops_df.sort_values("timestamp"), 
                            x="timestamp", y="memory_mb", 
                            color="operation",
                            title="内存使用趋势",
                            labels={"timestamp": "时间", "memory_mb": "内存使用 (MB)", "operation": "操作类型"})
                figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                
            # 3. CPU使用趋势
            if len(ops_df) > 0 and "cpu_percent" in ops_df.columns:
                fig = px.line(ops_df.sort_values("timestamp"), 
                            x="timestamp", y="cpu_percent", 
                            color="operation",
                            title="CPU使用趋势",
                            labels={"timestamp": "时间", "cpu_percent": "CPU使用 (%)", "operation": "操作类型"})
                figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                
            # 4. 处理时间统计
            if len(ops_df) > 0 and "stats_processing_time" in ops_df.columns:
                fig = px.box(ops_df, x="operation", y="stats_processing_time",
                           title="操作处理时间统计",
                           labels={"operation": "操作类型", "stats_processing_time": "处理时间 (秒)"})
                figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                
            # 5. 错误统计
            if len(errors_df) > 0:
                error_counts = errors_df["error_code"].value_counts().reset_index()
                error_counts.columns = ["error_code", "count"]
                
                fig = px.bar(error_counts, x="error_code", y="count",
                           title="错误类型统计",
                           labels={"error_code": "错误类型", "count": "错误次数"})
                figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                
            # 6. 会话统计
            if len(sessions_df) > 0 and "duration" in sessions_df.columns:
                fig = px.bar(sessions_df, x="session_id", y="duration",
                           title="会话持续时间",
                           labels={"session_id": "会话ID", "duration": "持续时间 (秒)"})
                figures.append(fig.to_html(full_html=False, include_plotlyjs=False))
                
            # 创建HTML报告
            template_str = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{{ title }}</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
                    .section { margin-bottom: 30px; }
                    .chart { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{{ title }}</h1>
                        <p>生成时间: {{ timestamp }}</p>
                        <p>分析日志: {{ log_count }} 条</p>
                    </div>
                    
                    {% if sessions_df is not none and sessions_df|length > 0 %}
                    <div class="section">
                        <h2>会话统计</h2>
                        <p>共发现 {{ sessions_df|length }} 个会话</p>
                        <table>
                            <tr>
                                <th>会话ID</th>
                                <th>开始时间</th>
                                <th>结束时间</th>
                                <th>持续时间(秒)</th>
                                <th>操作系统</th>
                                <th>内存(MB)</th>
                            </tr>
                            {% for _, row in sessions_df.iterrows() %}
                            <tr>
                                <td>{{ row.session_id }}</td>
                                <td>{{ row.start_time }}</td>
                                <td>{{ row.end_time or '进行中' }}</td>
                                <td>{{ row.duration or '-' }}</td>
                                <td>{{ row.os }} {{ row.os_version }}</td>
                                <td>{{ row.total_memory_mb }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                    {% endif %}
                    
                    {% if perf_data %}
                    <div class="section">
                        <h2>性能分析</h2>
                        
                        {% if perf_data.memory %}
                        <div class="subsection">
                            <h3>内存使用</h3>
                            <p>平均内存使用: {{ "%.2f"|format(perf_data.memory.overall_avg) }} MB</p>
                            <p>最大内存使用: {{ "%.2f"|format(perf_data.memory.overall_max) }} MB</p>
                            
                            <h4>按操作类型统计</h4>
                            <table>
                                <tr>
                                    <th>操作类型</th>
                                    <th>平均内存(MB)</th>
                                    <th>最大内存(MB)</th>
                                </tr>
                                {% for op, stats in perf_data.memory.by_operation.items() %}
                                <tr>
                                    <td>{{ op }}</td>
                                    <td>{{ "%.2f"|format(stats.mean) }}</td>
                                    <td>{{ "%.2f"|format(stats.max) }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </div>
                        {% endif %}
                        
                        {% if perf_data.cpu %}
                        <div class="subsection">
                            <h3>CPU使用</h3>
                            <p>平均CPU使用: {{ "%.2f"|format(perf_data.cpu.overall_avg) }}%</p>
                            <p>最大CPU使用: {{ "%.2f"|format(perf_data.cpu.overall_max) }}%</p>
                            
                            <h4>按操作类型统计</h4>
                            <table>
                                <tr>
                                    <th>操作类型</th>
                                    <th>平均CPU(%)</th>
                                    <th>最大CPU(%)</th>
                                </tr>
                                {% for op, stats in perf_data.cpu.by_operation.items() %}
                                <tr>
                                    <td>{{ op }}</td>
                                    <td>{{ "%.2f"|format(stats.mean) }}</td>
                                    <td>{{ "%.2f"|format(stats.max) }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </div>
                        {% endif %}
                        
                        {% if perf_data.processing_time %}
                        <div class="subsection">
                            <h3>处理时间</h3>
                            <p>平均处理时间: {{ "%.2f"|format(perf_data.processing_time.overall_avg) }} 秒</p>
                            <p>最大处理时间: {{ "%.2f"|format(perf_data.processing_time.overall_max) }} 秒</p>
                            
                            <h4>按操作类型统计</h4>
                            <table>
                                <tr>
                                    <th>操作类型</th>
                                    <th>平均时间(秒)</th>
                                    <th>最大时间(秒)</th>
                                </tr>
                                {% for op, stats in perf_data.processing_time.by_operation.items() %}
                                <tr>
                                    <td>{{ op }}</td>
                                    <td>{{ "%.2f"|format(stats.mean) }}</td>
                                    <td>{{ "%.2f"|format(stats.max) }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </div>
                        {% endif %}
                        
                        {% if perf_data.results %}
                        <div class="subsection">
                            <h3>操作结果统计</h3>
                            <p>总体成功率: {{ "%.2f"|format(perf_data.success_rate) }}%</p>
                            
                            <h4>结果分布</h4>
                            <table>
                                <tr>
                                    <th>结果类型</th>
                                    <th>次数</th>
                                </tr>
                                {% for result, count in perf_data.results.items() %}
                                <tr>
                                    <td>{{ result }}</td>
                                    <td>{{ count }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                            
                            <h4>按操作类型的成功率</h4>
                            <table>
                                <tr>
                                    <th>操作类型</th>
                                    <th>成功率(%)</th>
                                </tr>
                                {% for op, rate in perf_data.success_rate_by_operation.items() %}
                                <tr>
                                    <td>{{ op }}</td>
                                    <td>{{ "%.2f"|format(rate) }}</td>
                                </tr>
                                {% endfor %}
                            </table>
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    {% if figures %}
                    <div class="section">
                        <h2>图表分析</h2>
                        {% for figure in figures %}
                        <div class="chart">
                            {{ figure }}
                        </div>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if errors_df is not none and errors_df|length > 0 %}
                    <div class="section">
                        <h2>错误分析</h2>
                        <p>共发现 {{ errors_df|length }} 个错误</p>
                        <table>
                            <tr>
                                <th>时间</th>
                                <th>操作</th>
                                <th>错误类型</th>
                                <th>错误信息</th>
                            </tr>
                            {% for _, row in errors_df.iterrows() %}
                            <tr>
                                <td>{{ row.timestamp }}</td>
                                <td>{{ row.operation }}</td>
                                <td>{{ row.error_code }}</td>
                                <td>{{ row.error_message }}</td>
                            </tr>
                            {% endfor %}
                        </table>
                    </div>
                    {% endif %}
                </div>
            </body>
            </html>
            """
            
            # 渲染模板
            template = jinja2.Template(template_str)
            html_content = template.render(
                title=title,
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                log_count=len(self.df),
                sessions_df=sessions_df,
                ops_df=ops_df,
                errors_df=errors_df,
                perf_data=perf_data,
                figures=figures
            )
            
            # 写入报告文件
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            logger.info(f"生成报告: {report_path}")
            return str(report_path)
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return ""

    def export_logs(self, output_path: Union[str, Path], 
                   format: str = "json") -> bool:
        """
        导出日志数据
        
        Args:
            output_path: 输出文件路径
            format: 输出格式（json, csv）
            
        Returns:
            导出是否成功
        """
        if self.df is None or len(self.df) == 0:
            logger.warning("没有加载日志数据")
            return False
            
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == "json":
                # 导出为JSON，先将时间戳转换为字符串
                # 创建一个副本以避免修改原始数据
                df_copy = self.df.copy()
                
                # 处理时间戳列
                if "timestamp" in df_copy.columns:
                    df_copy["timestamp"] = df_copy["timestamp"].astype(str)
                
                # 获取记录
                records = df_copy.to_dict(orient="records")
                
                # 写入JSON文件
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
            elif format.lower() == "csv":
                # 导出为CSV
                self.df.to_csv(output_path, index=False, encoding="utf-8")
            else:
                logger.error(f"不支持的导出格式: {format}")
                return False
                
            logger.info(f"成功导出日志: {output_path}")
            return True
        except Exception as e:
            logger.error(f"导出日志失败: {str(e)}")
            return False


if __name__ == "__main__":
    # 测试代码
    analyzer = LogAnalyzer(log_dir="logs/structured")
    
    # 加载日志
    success = analyzer.load_logs(recursive=True)
    
    if success:
        # 输出会话信息
        sessions = analyzer.get_sessions()
        print(f"发现 {len(sessions)} 个会话")
        
        # 输出性能分析
        perf_data = analyzer.analyze_performance()
        print("性能分析结果:")
        print(perf_data)
        
        # 生成报告
        report_path = analyzer.generate_report(title="测试日志分析报告")
        if report_path:
            print(f"报告已生成: {report_path}") 