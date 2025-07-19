#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据可视化模块

该模块提供数据可视化和报告生成功能，用于展示系统性能指标、
多维度数据源统计和混沌测试结果，支持多种输出格式，适合4GB RAM环境。
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

# 创建日志记录器
logger = logging.getLogger("visualizer")

# 尝试导入可视化依赖
try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端，避免显示依赖
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    has_matplotlib = True
except ImportError:
    has_matplotlib = False
    logger.warning("未安装matplotlib，图表生成功能将受限")

try:
    import pandas as pd
    has_pandas = True
except ImportError:
    has_pandas = False
    logger.warning("未安装pandas，数据处理功能将受限")

# 导入数据聚合器
from .data_integration import DataAggregator


def generate_system_report(output_format: str = "json", 
                         output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    生成系统状态报告
    
    Args:
        output_format: 输出格式 (json, html, md)
        output_path: 输出文件路径，None则仅返回数据
        
    Returns:
        Dict: 报告数据
    """
    # 初始化数据聚合器
    aggregator = DataAggregator()
    
    # 获取各数据源状态
    sources_status = {}
    for source_name in aggregator.SOURCES.keys():
        sources_status[source_name] = aggregator.get_source_status(source_name)
    
    # 获取健康状态
    health = aggregator.get_health_status()
    
    # 获取最新的缓存数据
    cache_data = aggregator.get_cached_data("cache")
    cache_metrics = cache_data.get("cache_metrics", {})
    
    # 获取系统指标
    system_data = aggregator.get_cached_data("system")
    system_metrics = system_data.get("system_metrics", {})
    
    # 构建报告数据
    report = {
        "timestamp": time.time(),
        "datetime": datetime.now().isoformat(),
        "health_status": health.get("status", "unknown"),
        "sources_status": sources_status,
        "system": {
            "memory_usage_percent": system_metrics.get("memory", {}).get("percent", 0),
            "cpu_usage_percent": system_metrics.get("cpu", {}).get("percent", 0),
            "disk_usage_percent": system_metrics.get("disk", {}).get("percent", 0)
        },
        "cache": {
            "hit_rate": cache_metrics.get("hit_rate", 0),
            "memory_usage_mb": cache_metrics.get("used_memory_mb", 0),
            "evicted_keys": cache_metrics.get("evicted_keys", 0)
        },
        "summary": {
            "status": health.get("status", "unknown"),
            "critical_issues": 0,
            "warnings": 0
        }
    }
    
    # 分析关键指标，确定问题级别
    warnings = 0
    critical = 0
    
    # 检查内存使用
    if system_metrics.get("memory", {}).get("percent", 0) > 90:
        critical += 1
        report["memory_alert"] = "内存使用率超过90%，系统可能不稳定"
    elif system_metrics.get("memory", {}).get("percent", 0) > 75:
        warnings += 1
        report["memory_alert"] = "内存使用率超过75%，请注意系统负载"
    
    # 检查CPU使用
    if system_metrics.get("cpu", {}).get("percent", 0) > 95:
        critical += 1
        report["cpu_alert"] = "CPU使用率超过95%，性能严重下降"
    elif system_metrics.get("cpu", {}).get("percent", 0) > 80:
        warnings += 1
        report["cpu_alert"] = "CPU使用率超过80%，系统负载较高"
    
    # 检查缓存命中率
    if 0 < cache_metrics.get("hit_rate", 0) < 0.5:
        warnings += 1
        report["cache_alert"] = "缓存命中率低于50%，性能可能受影响"
    
    # 更新汇总信息
    report["summary"]["critical_issues"] = critical
    report["summary"]["warnings"] = warnings
    
    # 基于问题更新状态
    if critical > 0:
        report["summary"]["status"] = "critical"
    elif warnings > 0:
        report["summary"]["status"] = "warning"
    
    # 输出到文件
    if output_path:
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if output_format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
            elif output_format == "html":
                _generate_html_report(report, output_path)
            elif output_format == "md":
                _generate_markdown_report(report, output_path)
            else:
                logger.warning(f"不支持的输出格式: {output_format}")
                
            logger.info(f"系统报告已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    return report


def create_metrics_chart(metric_type: str, 
                        time_range: str = "1h", 
                        output_path: Optional[str] = None) -> Optional[str]:
    """
    创建性能指标图表
    
    Args:
        metric_type: 指标类型 (memory, cpu, cache_hit_rate, model_latency)
        time_range: 时间范围 (10m, 1h, 6h, 1d)
        output_path: 输出文件路径，None则使用默认路径
        
    Returns:
        Optional[str]: 图表文件路径，失败返回None
    """
    if not has_matplotlib:
        logger.warning("未安装matplotlib，无法生成图表")
        return None
    
    # 解析时间范围
    minutes = _parse_time_range(time_range)
    start_time = datetime.now() - timedelta(minutes=minutes)
    
    # 获取指标数据
    data = _get_metrics_data(metric_type, start_time)
    if not data:
        logger.warning(f"无可用的{metric_type}指标数据")
        return None
    
    # 设置输出路径
    if not output_path:
        chart_dir = Path("logs/charts")
        chart_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(chart_dir / f"{metric_type}_{timestamp}.png")
    
    # 绘制图表
    try:
        fig, ax = plt.figure(figsize=(10, 6), dpi=100)
        
        x_values = [item["timestamp"] for item in data]
        y_values = [item["value"] for item in data]
        
        plt.plot(x_values, y_values, marker='o', markersize=3, linestyle='-')
        
        # 设置标题和标签
        title_map = {
            "memory": "内存使用率",
            "cpu": "CPU使用率",
            "cache_hit_rate": "缓存命中率",
            "model_latency": "模型推理延迟"
        }
        y_label_map = {
            "memory": "使用率 (%)",
            "cpu": "使用率 (%)",
            "cache_hit_rate": "命中率",
            "model_latency": "延迟 (ms)"
        }
        
        plt.title(title_map.get(metric_type, metric_type))
        plt.xlabel("时间")
        plt.ylabel(y_label_map.get(metric_type, "值"))
        
        # 设置网格
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # 格式化日期
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # 自动调整日期标签
        fig.autofmt_xdate()
        
        # 保存图表
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"已生成{title_map.get(metric_type, metric_type)}图表: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"生成图表失败: {e}")
        return None


def _parse_time_range(time_range: str) -> int:
    """解析时间范围到分钟数"""
    if time_range.endswith("m"):
        return int(time_range[:-1])
    elif time_range.endswith("h"):
        return int(time_range[:-1]) * 60
    elif time_range.endswith("d"):
        return int(time_range[:-1]) * 60 * 24
    else:
        # 默认1小时
        return 60


def _get_metrics_data(metric_type: str, start_time: datetime) -> List[Dict[str, Any]]:
    """获取指定时间范围的指标数据"""
    try:
        # 尝试从监控模块获取数据
        from src.monitoring.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        
        # 如果监控模块有历史数据，优先使用
        if metric_type == "memory":
            return collector.get_metric_values("system_metrics.total_memory", start_time=start_time)
        elif metric_type == "cpu":
            return collector.get_metric_values("system_metrics.cpu_usage", start_time=start_time)
        elif metric_type == "cache_hit_rate":
            return collector.get_metric_values("cache_metrics.cache_hit_rate", start_time=start_time)
        elif metric_type == "model_latency":
            # 可能有多个模型，获取第一个或主模型的数据
            return collector.get_metric_values("model_metrics.inference_latency", start_time=start_time)
    except Exception as e:
        logger.warning(f"从监控模块获取数据失败，使用模拟数据: {e}")
    
    # 如果无法获取真实数据，生成模拟数据
    return _generate_mock_data(metric_type, start_time)


def _generate_mock_data(metric_type: str, start_time: datetime) -> List[Dict[str, Any]]:
    """生成模拟数据用于图表展示"""
    import random
    
    data = []
    current_time = start_time
    end_time = datetime.now()
    
    # 根据指标类型设置基线值和波动范围
    if metric_type == "memory":
        base = 60.0
        variance = 15.0
    elif metric_type == "cpu":
        base = 45.0
        variance = 20.0
    elif metric_type == "cache_hit_rate":
        base = 0.85
        variance = 0.15
    elif metric_type == "model_latency":
        base = 250.0
        variance = 100.0
    else:
        base = 50.0
        variance = 10.0
    
    # 生成模拟数据点
    while current_time < end_time:
        # 添加随机波动
        value = base + (random.random() * 2 - 1) * variance
        
        # 限制数值范围
        if metric_type == "cache_hit_rate":
            value = max(0.0, min(1.0, value))
        else:
            value = max(0.0, value)
        
        data.append({
            "timestamp": current_time,
            "value": value
        })
        
        # 增加时间间隔
        current_time += timedelta(minutes=1)
    
    return data


def _generate_html_report(report: Dict[str, Any], output_path: str) -> None:
    """生成HTML格式的报告"""
    # 提取报告数据
    status = report["summary"]["status"]
    status_class = {"healthy": "success", "warning": "warning", "critical": "danger"}.get(status, "secondary")
    
    # 构建HTML内容
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统状态报告 - {report["datetime"]}</title>
    <style>
        body {{ font-family: "Segoe UI", Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .status-bar {{ padding: 10px; border-radius: 4px; margin-bottom: 20px; color: white; font-weight: bold; }}
        .status-healthy {{ background-color: #28a745; }}
        .status-warning {{ background-color: #ffc107; color: #333; }}
        .status-critical {{ background-color: #dc3545; }}
        .metric {{ display: flex; margin-bottom: 15px; }}
        .metric-name {{ width: 150px; font-weight: bold; }}
        .metric-value {{ flex-grow: 1; }}
        .progress {{ height: 20px; background-color: #e9ecef; border-radius: 4px; overflow: hidden; }}
        .progress-bar {{ height: 100%; line-height: 20px; text-align: center; color: white; }}
        .progress-memory {{ background-color: #007bff; }}
        .progress-cpu {{ background-color: #28a745; }}
        .progress-disk {{ background-color: #6f42c1; }}
        .alert {{ padding: 10px; border-radius: 4px; margin-top: 5px; }}
        .alert-warning {{ background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }}
        .alert-danger {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>系统状态报告</h1>
        <p>生成时间: {report["datetime"]}</p>
        
        <div class="status-bar status-{status_class}">
            系统状态: {status.upper()} 
            {'，警告: '+str(report["summary"]["warnings"]) if report["summary"]["warnings"] > 0 else ''}
            {'，严重问题: '+str(report["summary"]["critical_issues"]) if report["summary"]["critical_issues"] > 0 else ''}
        </div>
        
        <div class="card">
            <h2>系统资源</h2>
            
            <div class="metric">
                <div class="metric-name">内存使用率:</div>
                <div class="metric-value">
                    <div class="progress">
                        <div class="progress-bar progress-memory" style="width: {report["system"]["memory_usage_percent"]}%">
                            {report["system"]["memory_usage_percent"]}%
                        </div>
                    </div>
                    {"" if "memory_alert" not in report else f'<div class="alert alert-{"warning" if "警告" in report["memory_alert"] else "danger"}">{report["memory_alert"]}</div>'}
                </div>
            </div>
            
            <div class="metric">
                <div class="metric-name">CPU使用率:</div>
                <div class="metric-value">
                    <div class="progress">
                        <div class="progress-bar progress-cpu" style="width: {report["system"]["cpu_usage_percent"]}%">
                            {report["system"]["cpu_usage_percent"]}%
                        </div>
                    </div>
                    {"" if "cpu_alert" not in report else f'<div class="alert alert-{"warning" if "警告" in report["cpu_alert"] else "danger"}">{report["cpu_alert"]}</div>'}
                </div>
            </div>
            
            <div class="metric">
                <div class="metric-name">磁盘使用率:</div>
                <div class="metric-value">
                    <div class="progress">
                        <div class="progress-bar progress-disk" style="width: {report["system"]["disk_usage_percent"]}%">
                            {report["system"]["disk_usage_percent"]}%
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>缓存状态</h2>
            
            <div class="metric">
                <div class="metric-name">命中率:</div>
                <div class="metric-value">
                    <div class="progress">
                        <div class="progress-bar progress-memory" style="width: {report["cache"]["hit_rate"]*100}%">
                            {round(report["cache"]["hit_rate"]*100, 1)}%
                        </div>
                    </div>
                    {"" if "cache_alert" not in report else f'<div class="alert alert-warning">{report["cache_alert"]}</div>'}
                </div>
            </div>
            
            <div class="metric">
                <div class="metric-name">内存使用:</div>
                <div class="metric-value">{report["cache"]["memory_usage_mb"]:.2f} MB</div>
            </div>
            
            <div class="metric">
                <div class="metric-name">已淘汰键数:</div>
                <div class="metric-value">{report["cache"]["evicted_keys"]}</div>
            </div>
        </div>
        
        <div class="card">
            <h2>数据源状态</h2>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f8f9fa;">
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">数据源</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">状态</th>
                    <th style="text-align: left; padding: 8px; border: 1px solid #ddd;">详情</th>
                </tr>
"""
    
    # 添加数据源状态
    for source_name, status in report["sources_status"].items():
        status_text = status["status"]
        status_color = "#28a745" if status_text in ["ok", "healthy"] else "#ffc107" if status_text == "fallback" else "#dc3545"
        
        html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{source_name}</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: {status_color}; margin-right: 5px;"></span>
                        {status_text}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
"""
        
        # 添加详细信息
        if source_name == "memory" and "metrics_count" in status:
            html += f"监控 {status['metrics_count']} 项指标"
        elif source_name == "cache" and "hit_rate" in status:
            html += f"命中率 {status['hit_rate']*100:.1f}%, 内存使用 {status['memory_usage_mb']:.2f} MB"
        elif source_name == "models" and "models_count" in status:
            html += f"监控 {status['models_count']} 个模型"
        elif source_name == "system" and "cpu_percent" in status:
            html += f"CPU {status['cpu_percent']:.1f}%, 内存 {status['memory_percent']:.1f}%"
        else:
            html += "&nbsp;"
            
        html += """
                    </td>
                </tr>"""
    
    # 完成HTML
    html += """
            </table>
        </div>
    </div>
</body>
</html>
"""
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _generate_markdown_report(report: Dict[str, Any], output_path: str) -> None:
    """生成Markdown格式的报告"""
    md = f"""# 系统状态报告

**生成时间:** {report["datetime"]}

## 状态摘要

**系统状态:** {report["summary"]["status"].upper()}

"""
    
    if report["summary"]["warnings"] > 0:
        md += f"**警告:** {report['summary']['warnings']} 个\n"
    
    if report["summary"]["critical_issues"] > 0:
        md += f"**严重问题:** {report['summary']['critical_issues']} 个\n"
    
    md += """
## 系统资源

"""
    
    md += f"* **内存使用率:** {report['system']['memory_usage_percent']}%\n"
    if "memory_alert" in report:
        md += f"  * ⚠️ {report['memory_alert']}\n"
    
    md += f"* **CPU使用率:** {report['system']['cpu_usage_percent']}%\n"
    if "cpu_alert" in report:
        md += f"  * ⚠️ {report['cpu_alert']}\n"
    
    md += f"* **磁盘使用率:** {report['system']['disk_usage_percent']}%\n"
    
    md += """
## 缓存状态

"""
    
    md += f"* **命中率:** {report['cache']['hit_rate']*100:.1f}%\n"
    if "cache_alert" in report:
        md += f"  * ⚠️ {report['cache_alert']}\n"
    
    md += f"* **内存使用:** {report['cache']['memory_usage_mb']:.2f} MB\n"
    md += f"* **已淘汰键数:** {report['cache']['evicted_keys']}\n"
    
    md += """
## 数据源状态

| 数据源 | 状态 | 详情 |
|-------|------|------|
"""
    
    for source_name, status in report["sources_status"].items():
        status_text = status["status"]
        status_icon = "✅" if status_text in ["ok", "healthy"] else "⚠️" if status_text == "fallback" else "❌"
        
        details = ""
        if source_name == "memory" and "metrics_count" in status:
            details = f"监控 {status['metrics_count']} 项指标"
        elif source_name == "cache" and "hit_rate" in status:
            details = f"命中率 {status['hit_rate']*100:.1f}%, 内存使用 {status['memory_usage_mb']:.2f} MB"
        elif source_name == "models" and "models_count" in status:
            details = f"监控 {status['models_count']} 个模型"
        elif source_name == "system" and "cpu_percent" in status:
            details = f"CPU {status['cpu_percent']:.1f}%, 内存 {status['memory_percent']:.1f}%"
        
        md += f"| {source_name} | {status_icon} {status_text} | {details} |\n"
    
    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 生成报告
    output_dir = Path("logs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON格式
    json_path = str(output_dir / f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    report_data = generate_system_report(output_format="json", output_path=json_path)
    
    # HTML格式
    html_path = str(output_dir / f"system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    generate_system_report(output_format="html", output_path=html_path)
    
    # 生成图表
    if has_matplotlib:
        print("生成内存使用率图表...")
        chart_path = create_metrics_chart("memory", time_range="1h")
        if chart_path:
            print(f"图表已保存到: {chart_path}")
    else:
        print("未安装matplotlib，无法生成图表") 