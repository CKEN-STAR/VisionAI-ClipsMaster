#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告可视化工具 - 为内存和线程安全测试生成图表
"""

import os
import sys
import time
import glob
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("report_visualizer")

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    from matplotlib.ticker import MaxNLocator
    from datetime import datetime, timedelta
    HAS_MATPLOTLIB = True
except ImportError:
    logger.warning("未安装matplotlib，将无法生成图表。请使用pip install matplotlib安装。")
    HAS_MATPLOTLIB = False

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ReportVisualizer:
    """报告可视化工具"""
    
    def __init__(self):
        """初始化可视化工具"""
        # 创建报告目录
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # 创建可视化目录
        self.viz_dir = self.reports_dir / "visualizations"
        self.viz_dir.mkdir(exist_ok=True)
        
        # 设置图表样式
        if HAS_MATPLOTLIB:
            plt.style.use('ggplot')
        
        logger.info("报告可视化工具初始化完成")
    
    def collect_memory_reports(self) -> List[Dict[str, Any]]:
        """收集所有内存报告
        
        Returns:
            List[Dict[str, Any]]: 内存报告列表
        """
        reports = []
        
        # 查找所有内存报告文件
        memory_files = glob.glob(str(self.reports_dir / "*memory*report*.txt"))
        memory_files += glob.glob(str(self.reports_dir / "memory" / "*.txt"))
        
        for file_path in memory_files:
            try:
                # 读取报告文件
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 解析报告内容
                report_data = self._parse_memory_report(content)
                report_data["file"] = file_path
                
                # 提取时间戳
                try:
                    if "timestamp" in report_data and report_data["timestamp"]:
                        dt = datetime.strptime(report_data["timestamp"], "%Y-%m-%d %H:%M:%S")
                        report_data["datetime"] = dt
                except Exception as e:
                    logger.warning(f"无法解析时间戳: {e}")
                
                reports.append(report_data)
                
            except Exception as e:
                logger.error(f"解析内存报告 {file_path} 时出错: {str(e)}")
        
        # 按时间排序
        reports.sort(key=lambda x: x.get("datetime", datetime.min))
        
        return reports
    
    def _parse_memory_report(self, content: str) -> Dict[str, Any]:
        """解析内存报告内容
        
        Args:
            content: 报告内容
            
        Returns:
            Dict[str, Any]: 解析后的报告数据
        """
        report_data = {
            "timestamp": None,
            "duration": None,
            "memory_start": None,
            "memory_end": None,
            "memory_min": None,
            "memory_max": None,
            "growth_rate": None,
            "risk_level": None,
            "objects_start": None,
            "objects_end": None,
            "objects_change": None,
        }
        
        # 解析时间戳
        for line in content.split("\n"):
            if line.startswith("生成时间:"):
                report_data["timestamp"] = line.split(":", 1)[1].strip()
            elif line.startswith("监控时长:"):
                try:
                    report_data["duration"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "开始:" in line and "MB" in line:
                try:
                    report_data["memory_start"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "结束:" in line and "MB" in line:
                try:
                    report_data["memory_end"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "最小:" in line and "MB" in line:
                try:
                    report_data["memory_min"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "最大:" in line and "MB" in line:
                try:
                    report_data["memory_max"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "每小时增长率:" in line:
                try:
                    report_data["growth_rate"] = float(line.split(":", 1)[1].strip().rstrip("%"))
                except:
                    pass
            elif "泄漏风险:" in line:
                report_data["risk_level"] = line.split(":", 1)[1].strip()
            elif "对象计数" in line and "开始:" in line:
                try:
                    report_data["objects_start"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
            elif "对象计数" in line and "结束:" in line:
                try:
                    report_data["objects_end"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
            elif "对象计数" in line and "变化:" in line:
                try:
                    report_data["objects_change"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
        
        return report_data
    
    def collect_thread_reports(self) -> List[Dict[str, Any]]:
        """收集所有线程安全测试报告
        
        Returns:
            List[Dict[str, Any]]: 线程报告列表
        """
        reports = []
        
        # 查找所有安全测试汇总报告
        thread_files = glob.glob(str(self.reports_dir / "*safety_test_summary*.md"))
        thread_files += glob.glob(str(self.reports_dir / "thread" / "*.md"))
        
        for file_path in thread_files:
            try:
                # 读取报告文件
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 解析报告内容
                report_data = self._parse_thread_report(content)
                report_data["file"] = file_path
                
                # 提取时间戳
                try:
                    if "timestamp" in report_data and report_data["timestamp"]:
                        dt = datetime.strptime(report_data["timestamp"], "%Y-%m-%d %H:%M:%S")
                        report_data["datetime"] = dt
                except Exception as e:
                    logger.warning(f"无法解析时间戳: {e}")
                
                reports.append(report_data)
                
            except Exception as e:
                logger.error(f"解析线程报告 {file_path} 时出错: {str(e)}")
        
        # 按时间排序
        reports.sort(key=lambda x: x.get("datetime", datetime.min))
        
        return reports
    
    def _parse_thread_report(self, content: str) -> Dict[str, Any]:
        """解析线程报告内容
        
        Args:
            content: 报告内容
            
        Returns:
            Dict[str, Any]: 解析后的报告数据
        """
        report_data = {
            "timestamp": None,
            "thread_tests": [],
            "worker_tests": [],
            "thread_success_rate": 0,
            "worker_success_rate": 0,
        }
        
        # 解析时间戳
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("生成时间:"):
                report_data["timestamp"] = line.split(":", 1)[1].strip()
            
            # 查找线程安全测试结果表格
            if "## 线程安全测试结果" in line and i + 3 < len(lines):
                # 跳过表头和分隔行
                j = i + 3
                while j < len(lines) and lines[j].strip() and "----" not in lines[j]:
                    cells = [cell.strip() for cell in lines[j].split("|") if cell.strip()]
                    if len(cells) >= 6:
                        test_type = cells[0]
                        thread_count = int(cells[1]) if cells[1].isdigit() else 0
                        duration = cells[2]
                        all_terminated = cells[3] == "是"
                        active_threads = int(cells[4]) if cells[4].isdigit() else 0
                        success = cells[5] == "通过"
                        
                        test_data = {
                            "thread_count": thread_count,
                            "duration": duration,
                            "all_terminated": all_terminated,
                            "active_threads": active_threads,
                            "success": success
                        }
                        
                        if "线程安全测试" in test_type:
                            report_data["thread_tests"].append(test_data)
                        elif "工作线程测试" in test_type:
                            report_data["worker_tests"].append(test_data)
                    
                    j += 1
        
        # 计算成功率
        if report_data["thread_tests"]:
            success_count = sum(1 for test in report_data["thread_tests"] if test["success"])
            report_data["thread_success_rate"] = success_count / len(report_data["thread_tests"]) * 100
        
        if report_data["worker_tests"]:
            success_count = sum(1 for test in report_data["worker_tests"] if test["success"])
            report_data["worker_success_rate"] = success_count / len(report_data["worker_tests"]) * 100
        
        return report_data
    
    def generate_memory_trend_chart(self, reports: List[Dict[str, Any]]) -> str:
        """生成内存趋势图
        
        Args:
            reports: 内存报告列表
            
        Returns:
            str: 图表文件路径
        """
        if not HAS_MATPLOTLIB:
            logger.error("未安装matplotlib，无法生成图表")
            return ""
        
        if not reports:
            logger.warning("没有内存报告数据，无法生成图表")
            return ""
        
        # 提取数据
        dates = [r.get("datetime", datetime.now()) for r in reports if "datetime" in r]
        memory_start = [r.get("memory_start", 0) for r in reports]
        memory_end = [r.get("memory_end", 0) for r in reports]
        growth_rates = [r.get("growth_rate", 0) for r in reports]
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        
        # 内存使用图
        ax1.plot(dates, memory_start, 'o-', label='初始内存 (MB)')
        ax1.plot(dates, memory_end, 's-', label='最终内存 (MB)')
        ax1.set_title('内存使用趋势')
        ax1.set_ylabel('内存使用 (MB)')
        ax1.legend()
        ax1.grid(True)
        
        # 增长率图
        ax2.bar(dates, growth_rates, width=0.5, alpha=0.7)
        ax2.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='警告阈值 (1%/小时)')
        ax2.axhline(y=5.0, color='red', linestyle='--', alpha=0.7, label='危险阈值 (5%/小时)')
        ax2.set_title('内存增长率趋势')
        ax2.set_ylabel('增长率 (%/小时)')
        ax2.set_xlabel('测试日期')
        ax2.legend()
        ax2.grid(True)
        
        # 设置x轴日期格式
        fig.autofmt_xdate()
        
        # 保存图表
        chart_path = self.viz_dir / f"memory_trend_{time.strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
        
        logger.info(f"内存趋势图已生成: {chart_path}")
        
        return str(chart_path)
    
    def generate_thread_safety_chart(self, reports: List[Dict[str, Any]]) -> str:
        """生成线程安全测试图表
        
        Args:
            reports: 线程报告列表
            
        Returns:
            str: 图表文件路径
        """
        if not HAS_MATPLOTLIB:
            logger.error("未安装matplotlib，无法生成图表")
            return ""
        
        if not reports:
            logger.warning("没有线程报告数据，无法生成图表")
            return ""
        
        # 提取数据
        dates = [r.get("datetime", datetime.now()) for r in reports if "datetime" in r]
        thread_success_rates = [r.get("thread_success_rate", 0) for r in reports]
        worker_success_rates = [r.get("worker_success_rate", 0) for r in reports]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 成功率图
        ax.plot(dates, thread_success_rates, 'o-', label='标准线程成功率 (%)')
        ax.plot(dates, worker_success_rates, 's-', label='工作线程成功率 (%)')
        ax.set_title('线程安全测试成功率趋势')
        ax.set_ylabel('成功率 (%)')
        ax.set_xlabel('测试日期')
        ax.set_ylim(0, 105)  # 设置y轴范围为0-105%
        ax.legend()
        ax.grid(True)
        
        # 设置x轴日期格式
        fig.autofmt_xdate()
        
        # 保存图表
        chart_path = self.viz_dir / f"thread_safety_{time.strftime('%Y%m%d_%H%M%S')}.png"
        plt.tight_layout()
        plt.savefig(chart_path)
        plt.close()
        
        logger.info(f"线程安全测试图表已生成: {chart_path}")
        
        return str(chart_path)
    
    def generate_combined_report(self) -> str:
        """生成综合报告
        
        Returns:
            str: 报告文件路径
        """
        # 收集报告数据
        memory_reports = self.collect_memory_reports()
        thread_reports = self.collect_thread_reports()
        
        # 生成图表
        memory_chart = None
        thread_chart = None
        
        if HAS_MATPLOTLIB:
            memory_chart = self.generate_memory_trend_chart(memory_reports)
            thread_chart = self.generate_thread_safety_chart(thread_reports)
        
        # 生成HTML报告
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html lang="zh-CN">')
        html.append('<head>')
        html.append('    <meta charset="UTF-8">')
        html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('    <title>VisionAI-ClipsMaster 安全测试可视化报告</title>')
        html.append('    <style>')
        html.append('        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }')
        html.append('        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }')
        html.append('        h2 { color: #2980b9; margin-top: 30px; }')
        html.append('        .container { max-width: 1200px; margin: 0 auto; }')
        html.append('        .chart-container { margin: 20px 0; text-align: center; }')
        html.append('        .chart-container img { max-width: 100%; height: auto; border: 1px solid #ddd; }')
        html.append('        table { border-collapse: collapse; width: 100%; margin: 20px 0; }')
        html.append('        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }')
        html.append('        th { background-color: #f2f2f2; }')
        html.append('        tr:nth-child(even) { background-color: #f9f9f9; }')
        html.append('        .success { color: green; }')
        html.append('        .warning { color: orange; }')
        html.append('        .danger { color: red; }')
        html.append('        .summary { background-color: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 20px 0; }')
        html.append('    </style>')
        html.append('</head>')
        html.append('<body>')
        html.append('    <div class="container">')
        html.append('        <h1>VisionAI-ClipsMaster 安全测试可视化报告</h1>')
        html.append(f'        <p>生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>')
        
        # 内存测试部分
        html.append('        <h2>内存泄漏测试结果</h2>')
        
        if memory_chart and os.path.exists(memory_chart):
            html.append('        <div class="chart-container">')
            html.append(f'            <img src="{os.path.relpath(memory_chart, self.reports_dir)}" alt="内存趋势图">')
            html.append('        </div>')
        
        if memory_reports:
            html.append('        <table>')
            html.append('            <tr>')
            html.append('                <th>测试时间</th>')
            html.append('                <th>持续时间(秒)</th>')
            html.append('                <th>初始内存(MB)</th>')
            html.append('                <th>最终内存(MB)</th>')
            html.append('                <th>增长率(%/小时)</th>')
            html.append('                <th>风险级别</th>')
            html.append('            </tr>')
            
            for report in memory_reports:
                timestamp = report.get("timestamp", "未知")
                duration = report.get("duration", 0) or 0
                mem_start = report.get("memory_start", 0) or 0
                mem_end = report.get("memory_end", 0) or 0
                growth = report.get("growth_rate", 0) or 0
                risk = report.get("risk_level", "未知")
                
                # 设置风险级别样式
                risk_class = ""
                if "低" in risk:
                    risk_class = "success"
                elif "中" in risk:
                    risk_class = "warning"
                elif "高" in risk:
                    risk_class = "danger"
                
                html.append('            <tr>')
                html.append(f'                <td>{timestamp}</td>')
                html.append(f'                <td>{duration:.1f}</td>')
                html.append(f'                <td>{mem_start:.2f}</td>')
                html.append(f'                <td>{mem_end:.2f}</td>')
                html.append(f'                <td>{growth:.2f}</td>')
                html.append(f'                <td class="{risk_class}">{risk}</td>')
                html.append('            </tr>')
            
            html.append('        </table>')
            
            # 内存测试总结
            avg_growth = sum(r.get("growth_rate", 0) or 0 for r in memory_reports) / len(memory_reports)
            
            html.append('        <div class="summary">')
            html.append('            <h3>内存测试总结</h3>')
            html.append(f'            <p>测试报告数量: {len(memory_reports)}</p>')
            html.append(f'            <p>平均内存增长率: {avg_growth:.2f}%/小时</p>')
            
            if avg_growth < 1:
                html.append('            <p class="success">整体内存泄漏风险: 低</p>')
                html.append('            <p>应用内存使用稳定，没有明显的内存泄漏迹象。</p>')
            elif avg_growth < 5:
                html.append('            <p class="warning">整体内存泄漏风险: 中</p>')
                html.append('            <p>应用存在轻微内存增长，建议关注内存管理。</p>')
            else:
                html.append('            <p class="danger">整体内存泄漏风险: 高</p>')
                html.append('            <p>应用存在明显内存泄漏风险，需要立即处理。</p>')
            
            html.append('        </div>')
        else:
            html.append('        <p>未找到内存测试报告</p>')
        
        # 线程安全测试部分
        html.append('        <h2>线程安全测试结果</h2>')
        
        if thread_chart and os.path.exists(thread_chart):
            html.append('        <div class="chart-container">')
            html.append(f'            <img src="{os.path.relpath(thread_chart, self.reports_dir)}" alt="线程安全测试图表">')
            html.append('        </div>')
        
        if thread_reports:
            html.append('        <table>')
            html.append('            <tr>')
            html.append('                <th>测试时间</th>')
            html.append('                <th>标准线程成功率(%)</th>')
            html.append('                <th>工作线程成功率(%)</th>')
            html.append('            </tr>')
            
            for report in thread_reports:
                timestamp = report.get("timestamp", "未知")
                thread_rate = report.get("thread_success_rate", 0)
                worker_rate = report.get("worker_success_rate", 0)
                
                html.append('            <tr>')
                html.append(f'                <td>{timestamp}</td>')
                html.append(f'                <td>{thread_rate:.1f}%</td>')
                html.append(f'                <td>{worker_rate:.1f}%</td>')
                html.append('            </tr>')
            
            html.append('        </table>')
            
            # 线程测试总结
            avg_thread_rate = sum(r.get("thread_success_rate", 0) for r in thread_reports) / len(thread_reports)
            avg_worker_rate = sum(r.get("worker_success_rate", 0) for r in thread_reports) / len(thread_reports)
            
            html.append('        <div class="summary">')
            html.append('            <h3>线程安全测试总结</h3>')
            html.append(f'            <p>测试报告数量: {len(thread_reports)}</p>')
            html.append(f'            <p>平均标准线程成功率: {avg_thread_rate:.1f}%</p>')
            html.append(f'            <p>平均工作线程成功率: {avg_worker_rate:.1f}%</p>')
            
            if avg_thread_rate >= 95 and avg_worker_rate >= 95:
                html.append('            <p class="success">线程安全状态: 良好</p>')
                html.append('            <p>应用线程管理表现良好，几乎所有线程都能正确终止。</p>')
            elif avg_thread_rate >= 80 and avg_worker_rate >= 80:
                html.append('            <p class="warning">线程安全状态: 一般</p>')
                html.append('            <p>应用线程管理存在一些问题，部分线程可能无法正确终止。</p>')
            else:
                html.append('            <p class="danger">线程安全状态: 差</p>')
                html.append('            <p>应用线程管理存在严重问题，多数线程无法正确终止。</p>')
            
            html.append('        </div>')
        else:
            html.append('        <p>未找到线程安全测试报告</p>')
        
        # 结束HTML
        html.append('    </div>')
        html.append('</body>')
        html.append('</html>')
        
        # 保存HTML报告
        report_path = self.reports_dir / f"visual_report_{time.strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html))
        
        logger.info(f"可视化报告已生成: {report_path}")
        
        return str(report_path)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 报告可视化工具")
    parser.add_argument("--memory-chart", action="store_true", help="生成内存趋势图")
    parser.add_argument("--thread-chart", action="store_true", help="生成线程安全测试图表")
    parser.add_argument("--html-report", action="store_true", help="生成HTML综合报告")
    
    args = parser.parse_args()
    
    print("\n===== VisionAI-ClipsMaster 报告可视化工具 =====\n")
    
    visualizer = ReportVisualizer()
    
    # 收集报告数据
    memory_reports = visualizer.collect_memory_reports()
    thread_reports = visualizer.collect_thread_reports()
    
    print(f"找到 {len(memory_reports)} 个内存报告")
    print(f"找到 {len(thread_reports)} 个线程安全测试报告")
    
    if not HAS_MATPLOTLIB:
        print("\n警告: 未安装matplotlib，无法生成图表。请使用pip install matplotlib安装。")
    
    # 生成内存趋势图
    if args.memory_chart and HAS_MATPLOTLIB:
        chart_path = visualizer.generate_memory_trend_chart(memory_reports)
        if chart_path:
            print(f"\n内存趋势图已生成: {chart_path}")
    
    # 生成线程安全测试图表
    if args.thread_chart and HAS_MATPLOTLIB:
        chart_path = visualizer.generate_thread_safety_chart(thread_reports)
        if chart_path:
            print(f"\n线程安全测试图表已生成: {chart_path}")
    
    # 生成HTML综合报告
    if args.html_report or not (args.memory_chart or args.thread_chart):
        report_path = visualizer.generate_combined_report()
        if report_path:
            print(f"\nHTML综合报告已生成: {report_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 