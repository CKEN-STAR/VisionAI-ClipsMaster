#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存测试结果可视化工具

分析内存测试报告，生成可视化图表，便于直观评估系统性能。
支持多种图表类型和比较模式。
"""

import os
import sys
import json
import csv
import argparse
import glob
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))


class MemoryVisualizer:
    """内存测试结果可视化工具"""
    
    def __init__(self, reports_dir="logs/memory_tests", output_dir="logs/memory_tests/reports"):
        """
        初始化可视化工具
        
        Args:
            reports_dir: 测试报告目录
            output_dir: 可视化报告输出目录
        """
        self.reports_dir = reports_dir
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置图表样式
        plt.style.use('ggplot')
        
    def load_json_report(self, report_path):
        """
        加载JSON格式测试报告
        
        Args:
            report_path: 报告文件路径
            
        Returns:
            报告数据字典
        """
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载报告文件失败: {report_path}, 错误: {str(e)}")
            return None
    
    def load_csv_reports(self, pattern="*memory_test.csv"):
        """
        加载目录中所有符合模式的CSV报告
        
        Args:
            pattern: 文件匹配模式
            
        Returns:
            DataFrame: 合并后的报告数据
        """
        csv_files = glob.glob(os.path.join(self.reports_dir, pattern))
        
        if not csv_files:
            print(f"未找到匹配的CSV报告文件: {pattern}")
            return None
        
        # 读取所有CSV文件并合并
        dfs = []
        for file in csv_files:
            try:
                df = pd.read_csv(file)
                df['report_file'] = os.path.basename(file)  # 添加文件名列
                dfs.append(df)
            except Exception as e:
                print(f"读取CSV文件失败: {file}, 错误: {str(e)}")
        
        if not dfs:
            return None
            
        return pd.concat(dfs, ignore_index=True)
    
    def visualize_single_test(self, report_path, save=True):
        """
        可视化单个测试报告
        
        Args:
            report_path: 报告文件路径
            save: 是否保存图表
            
        Returns:
            保存的图表文件路径
        """
        report = self.load_json_report(report_path)
        if not report:
            return None
        
        # 提取基本信息
        test_mode = report.get("test_mode", "unknown")
        model_id = report.get("model_id", "none")
        timestamp = report.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        # 创建图表
        fig, axs = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f"内存压力测试报告 - {test_mode}", fontsize=16)
        
        # 提取内存使用数据
        if "memory_statistics" in report:
            stats = report["memory_statistics"]
            memory_percent = [report["start_memory"]["memory_percent"]]
            if "peak_memory" in report:
                memory_percent.append(report["peak_memory"])
            memory_percent.append(report["end_memory"]["memory_percent"])
            
            # 内存使用率图表
            axs[0].bar(["开始", "峰值", "结束"], memory_percent, color=['green', 'red', 'blue'])
            axs[0].set_title("内存使用率变化")
            axs[0].set_ylabel("内存使用率 (%)")
            axs[0].yaxis.set_major_formatter(PercentFormatter(100))
            axs[0].grid(True, linestyle='--', alpha=0.7)
            
            # 在柱状图上显示具体数值
            for i, v in enumerate(memory_percent):
                axs[0].text(i, v + 2, f"{v:.1f}%", ha='center')
            
            # 可用内存图表
            if "min_available_gb" in stats and "avg_available_gb" in stats:
                available = [
                    report["start_memory"]["available_gb"],
                    stats["min_available_gb"],
                    stats["avg_available_gb"],
                    report["end_memory"]["available_gb"]
                ]
                
                axs[1].bar(["开始", "最小", "平均", "结束"], available, color=['green', 'orange', 'blue', 'purple'])
                axs[1].set_title("可用内存变化")
                axs[1].set_ylabel("可用内存 (GB)")
                axs[1].grid(True, linestyle='--', alpha=0.7)
                
                # 在柱状图上显示具体数值
                for i, v in enumerate(available):
                    axs[1].text(i, v + 0.1, f"{v:.2f}GB", ha='center')
        
        # 添加模型信息和附加说明
        if model_id != "none":
            model_load_time = report.get("model_load_time", 0)
            fig.text(0.5, 0.02, 
                    f"模型: {model_id} | 加载时间: {model_load_time:.2f}秒 | 波动率: {stats.get('volatility', 0):.4f}", 
                    ha='center', fontsize=12)
        
        plt.tight_layout()
        
        # 保存图表
        if save:
            base_name = os.path.basename(report_path).replace(".json", "").replace(".csv", "")
            output_path = os.path.join(self.output_dir, f"{base_name}_visual.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"可视化报告已保存: {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def visualize_multiple_tests(self, test_type=None, model_id=None, save=True):
        """
        可视化比较多个测试报告
        
        Args:
            test_type: 测试类型过滤
            model_id: 模型ID过滤
            save: 是否保存图表
            
        Returns:
            保存的图表文件路径
        """
        # 加载所有CSV报告
        df = self.load_csv_reports()
        if df is None or df.empty:
            print("没有找到可用的测试报告数据")
            return None
        
        # 根据条件过滤
        if test_type:
            df = df[df['test_mode'] == test_type]
        if model_id:
            df = df[df['model_id'] == model_id]
        
        if df.empty:
            print(f"没有找到符合条件的测试报告数据: type={test_type}, model={model_id}")
            return None
        
        # 创建图表
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f"内存测试比较报告", fontsize=16)
        
        # 按测试模式分组比较峰值内存
        test_modes = df['test_mode'].unique()
        if len(test_modes) > 1:
            peak_by_mode = df.groupby('test_mode')['peak_memory_percent'].mean()
            axs[0, 0].bar(peak_by_mode.index, peak_by_mode.values, color='crimson')
            axs[0, 0].set_title("不同测试模式的峰值内存使用率")
            axs[0, 0].set_xlabel("测试模式")
            axs[0, 0].set_ylabel("平均峰值内存使用率 (%)")
            axs[0, 0].tick_params(axis='x', rotation=45)
            axs[0, 0].yaxis.set_major_formatter(PercentFormatter(100))
            axs[0, 0].grid(True, linestyle='--', alpha=0.7)
            
            # 显示具体数值
            for i, v in enumerate(peak_by_mode.values):
                axs[0, 0].text(i, v + 2, f"{v:.1f}%", ha='center')
        
        # 模型加载时间对比(如果有)
        if 'model_load_time' in df.columns and df['model_load_time'].notna().any():
            if 'model_id' in df.columns and df['model_id'].nunique() > 1:
                # 按模型分组比较加载时间
                load_by_model = df.groupby('model_id')['model_load_time'].mean()
                axs[0, 1].bar(load_by_model.index, load_by_model.values, color='blue')
                axs[0, 1].set_title("不同模型的平均加载时间")
                axs[0, 1].set_xlabel("模型ID")
                axs[0, 1].set_ylabel("平均加载时间 (秒)")
                axs[0, 1].tick_params(axis='x', rotation=45)
                axs[0, 1].grid(True, linestyle='--', alpha=0.7)
                
                # 显示具体数值
                for i, v in enumerate(load_by_model.values):
                    axs[0, 1].text(i, v + 0.5, f"{v:.2f}s", ha='center')
            else:
                # 按测试模式比较加载时间
                load_by_mode = df.groupby('test_mode')['model_load_time'].mean()
                axs[0, 1].bar(load_by_mode.index, load_by_mode.values, color='blue')
                axs[0, 1].set_title("不同测试模式下的平均加载时间")
                axs[0, 1].set_xlabel("测试模式")
                axs[0, 1].set_ylabel("平均加载时间 (秒)")
                axs[0, 1].tick_params(axis='x', rotation=45)
                axs[0, 1].grid(True, linestyle='--', alpha=0.7)
                
                # 显示具体数值
                for i, v in enumerate(load_by_mode.values):
                    axs[0, 1].text(i, v + 0.5, f"{v:.2f}s", ha='center')
        
        # 内存使用趋势对比
        if 'start_memory_percent' in df.columns and 'peak_memory_percent' in df.columns and 'end_memory_percent' in df.columns:
            # 准备数据
            categories = ['开始', '峰值', '结束']
            
            # 如果测试模式多于1种，按模式分组比较
            if len(test_modes) > 1:
                data = []
                for mode in test_modes:
                    mode_df = df[df['test_mode'] == mode]
                    avg_start = mode_df['start_memory_percent'].mean()
                    avg_peak = mode_df['peak_memory_percent'].mean()
                    avg_end = mode_df['end_memory_percent'].mean()
                    data.append([avg_start, avg_peak, avg_end])
                
                # 绘制分组柱状图
                x = np.arange(len(categories))
                width = 0.8 / len(test_modes)
                
                for i, mode in enumerate(test_modes):
                    axs[1, 0].bar(x + i*width - 0.4 + width/2, data[i], width, label=mode)
                
                axs[1, 0].set_title("不同测试模式的内存使用趋势")
                axs[1, 0].set_ylabel("内存使用率 (%)")
                axs[1, 0].set_xticks(x)
                axs[1, 0].set_xticklabels(categories)
                axs[1, 0].legend()
                axs[1, 0].yaxis.set_major_formatter(PercentFormatter(100))
                axs[1, 0].grid(True, linestyle='--', alpha=0.7)
            else:
                # 单一测试模式，显示所有测试的均值和标准差
                avg_start = df['start_memory_percent'].mean()
                avg_peak = df['peak_memory_percent'].mean()
                avg_end = df['end_memory_percent'].mean()
                
                std_start = df['start_memory_percent'].std()
                std_peak = df['peak_memory_percent'].std()
                std_end = df['end_memory_percent'].std()
                
                axs[1, 0].bar(categories, [avg_start, avg_peak, avg_end], 
                              yerr=[std_start, std_peak, std_end],
                              color='green', alpha=0.7)
                
                axs[1, 0].set_title("内存使用趋势 (均值±标准差)")
                axs[1, 0].set_ylabel("内存使用率 (%)")
                axs[1, 0].yaxis.set_major_formatter(PercentFormatter(100))
                axs[1, 0].grid(True, linestyle='--', alpha=0.7)
                
                # 显示具体数值
                for i, v in enumerate([avg_start, avg_peak, avg_end]):
                    axs[1, 0].text(i, v + 2, f"{v:.1f}%", ha='center')
        
        # 可用内存对比
        if 'min_available_gb' in df.columns:
            # 如果测试模式多于1种，按模式分组比较
            if len(test_modes) > 1:
                min_by_mode = df.groupby('test_mode')['min_available_gb'].mean()
                axs[1, 1].bar(min_by_mode.index, min_by_mode.values, color='orange')
                axs[1, 1].set_title("不同测试模式下的最小可用内存")
                axs[1, 1].set_xlabel("测试模式")
                axs[1, 1].set_ylabel("平均最小可用内存 (GB)")
                axs[1, 1].tick_params(axis='x', rotation=45)
                axs[1, 1].grid(True, linestyle='--', alpha=0.7)
                
                # 显示具体数值
                for i, v in enumerate(min_by_mode.values):
                    axs[1, 1].text(i, v + 0.1, f"{v:.2f}GB", ha='center')
            else:
                # 单一测试模式，比较不同样本
                samples = min(10, len(df))  # 最多显示10个样本
                sample_df = df.sample(samples) if len(df) > samples else df
                
                axs[1, 1].bar(range(len(sample_df)), sample_df['min_available_gb'], color='orange')
                axs[1, 1].set_title(f"样本最小可用内存对比 (随机{samples}个)")
                axs[1, 1].set_xlabel("样本ID")
                axs[1, 1].set_ylabel("最小可用内存 (GB)")
                axs[1, 1].grid(True, linestyle='--', alpha=0.7)
                
                # 显示均值线
                mean_val = sample_df['min_available_gb'].mean()
                axs[1, 1].axhline(y=mean_val, color='r', linestyle='-', label=f'均值: {mean_val:.2f}GB')
                axs[1, 1].legend()
        
        plt.tight_layout()
        
        # 保存图表
        if save:
            filter_str = ""
            if test_type:
                filter_str += f"_{test_type}"
            if model_id:
                filter_str += f"_{model_id}"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"{timestamp}{filter_str}_comparison.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"比较报告已保存: {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def visualize_quantization_tests(self, report_path=None, save=True):
        """
        可视化量化级别测试结果
        
        Args:
            report_path: 量化测试报告路径，如果为None则搜索最新的
            save: 是否保存图表
            
        Returns:
            保存的图表文件路径
        """
        # 如果未指定报告，查找包含quantization_comparison的最新报告
        if report_path is None:
            json_files = glob.glob(os.path.join(self.reports_dir, "*quantization_comparison*.json"))
            if not json_files:
                print("未找到量化测试报告")
                return None
            report_path = max(json_files, key=os.path.getctime)  # 获取最新的文件
        
        # 加载报告
        report = self.load_json_report(report_path)
        if not report or "results" not in report:
            print("无效的量化测试报告")
            return None
        
        # 提取量化测试数据
        results = report["results"]
        quant_levels = [r.get("quantization_level", "unknown") for r in results]
        peak_memory = [r.get("peak_memory", 0) for r in results]
        load_times = [r.get("model_load_time", 0) for r in results]
        
        # 创建图表
        fig, axs = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle(f"量化级别测试比较 - {report.get('model_id', 'unknown')}", fontsize=16)
        
        # 峰值内存对比
        axs[0].bar(quant_levels, peak_memory, color='crimson')
        axs[0].set_title("不同量化级别的峰值内存使用率")
        axs[0].set_xlabel("量化级别")
        axs[0].set_ylabel("峰值内存使用率 (%)")
        axs[0].tick_params(axis='x', rotation=45)
        axs[0].yaxis.set_major_formatter(PercentFormatter(100))
        axs[0].grid(True, linestyle='--', alpha=0.7)
        
        # 显示具体数值
        for i, v in enumerate(peak_memory):
            axs[0].text(i, v + 2, f"{v:.1f}%", ha='center')
        
        # 加载时间对比
        axs[1].bar(quant_levels, load_times, color='blue')
        axs[1].set_title("不同量化级别的模型加载时间")
        axs[1].set_xlabel("量化级别")
        axs[1].set_ylabel("加载时间 (秒)")
        axs[1].tick_params(axis='x', rotation=45)
        axs[1].grid(True, linestyle='--', alpha=0.7)
        
        # 显示具体数值
        for i, v in enumerate(load_times):
            axs[1].text(i, v + 0.5, f"{v:.2f}s", ha='center')
        
        plt.tight_layout()
        
        # 保存图表
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, 
                                      f"{timestamp}_{report.get('model_id', 'unknown')}_quant_comparison.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"量化比较报告已保存: {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None
    
    def visualize_stability_test(self, report_path=None, save=True):
        """
        可视化长时间稳定性测试结果
        
        Args:
            report_path: 稳定性测试报告路径，如果为None则搜索最新的
            save: 是否保存图表
            
        Returns:
            保存的图表文件路径
        """
        # 如果未指定报告，查找包含stability_test的最新报告
        if report_path is None:
            json_files = glob.glob(os.path.join(self.reports_dir, "*stability_test*.json"))
            if not json_files:
                print("未找到稳定性测试报告")
                return None
            report_path = max(json_files, key=os.path.getctime)  # 获取最新的文件
        
        # 加载报告
        report = self.load_json_report(report_path)
        if not report or "results" not in report:
            print("无效的稳定性测试报告")
            return None
        
        # 提取稳定性测试数据
        results = report["results"]
        cycles = [r.get("cycle", i+1) for i, r in enumerate(results)]
        elapsed_hours = [r.get("elapsed_hours", 0) for r in results]
        peak_memory = [r.get("peak_memory", 0) for r in results]
        load_times = [r.get("model_load_time", 0) for r in results if "model_load_time" in r]
        
        # 创建图表
        fig, axs = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle(f"长时间稳定性测试 - {report.get('duration_hours', 0)}小时", fontsize=16)
        
        # 内存使用趋势
        axs[0].plot(elapsed_hours, peak_memory, 'o-', color='crimson', linewidth=2)
        axs[0].set_title("内存使用率随时间变化")
        axs[0].set_xlabel("运行时间 (小时)")
        axs[0].set_ylabel("峰值内存使用率 (%)")
        axs[0].yaxis.set_major_formatter(PercentFormatter(100))
        axs[0].grid(True, linestyle='--', alpha=0.7)
        
        # 添加趋势线
        if len(elapsed_hours) > 2:
            z = np.polyfit(elapsed_hours, peak_memory, 1)
            p = np.poly1d(z)
            axs[0].plot(elapsed_hours, p(elapsed_hours), "r--", alpha=0.8, 
                       label=f"趋势: {z[0]:.2f}%/小时")
            axs[0].legend()
        
        # 加载时间趋势(如果有)
        if load_times:
            axs[1].plot(elapsed_hours[:len(load_times)], load_times, 'o-', color='blue', linewidth=2)
            axs[1].set_title("模型加载时间随时间变化")
            axs[1].set_xlabel("运行时间 (小时)")
            axs[1].set_ylabel("加载时间 (秒)")
            axs[1].grid(True, linestyle='--', alpha=0.7)
            
            # 添加趋势线
            if len(load_times) > 2:
                z = np.polyfit(elapsed_hours[:len(load_times)], load_times, 1)
                p = np.poly1d(z)
                axs[1].plot(elapsed_hours[:len(load_times)], p(elapsed_hours[:len(load_times)]), 
                           "b--", alpha=0.8, label=f"趋势: {z[0]:.2f}秒/小时")
                axs[1].legend()
        else:
            # 如果没有加载时间数据，显示每个循环的测试模式
            test_modes = [r.get("test_mode", "unknown") for r in results]
            unique_modes = list(set(test_modes))
            mode_colors = plt.cm.tab10(np.linspace(0, 1, len(unique_modes)))
            
            mode_counts = {}
            for mode in test_modes:
                if mode in mode_counts:
                    mode_counts[mode] += 1
                else:
                    mode_counts[mode] = 1
            
            # 绘制测试模式分布饼图
            axs[1].pie([mode_counts[mode] for mode in unique_modes], 
                      labels=unique_modes,
                      colors=mode_colors,
                      autopct='%1.1f%%',
                      shadow=True, 
                      startangle=90)
            axs[1].axis('equal')
            axs[1].set_title("测试模式分布")
        
        plt.tight_layout()
        
        # 保存图表
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_str = f"_{report.get('model_id', 'nomodel')}" if report.get('model_id') else ""
            output_path = os.path.join(self.output_dir, 
                                     f"{timestamp}{model_str}_stability_{report.get('duration_hours', 0)}h.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"稳定性测试报告已保存: {output_path}")
            plt.close()
            return output_path
        else:
            plt.show()
            return None


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description="内存测试可视化工具")
    parser.add_argument("--report-dir", type=str, default="logs/memory_tests", 
                       help="测试报告目录")
    parser.add_argument("--output-dir", type=str, default="logs/memory_tests/reports", 
                       help="可视化输出目录")
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 单个报告可视化
    single_parser = subparsers.add_parser("single", help="可视化单个测试报告")
    single_parser.add_argument("--report", type=str, required=True, help="报告文件路径")
    
    # 比较可视化
    compare_parser = subparsers.add_parser("compare", help="比较多个测试报告")
    compare_parser.add_argument("--test-type", type=str, help="测试类型过滤")
    compare_parser.add_argument("--model-id", type=str, help="模型ID过滤")
    
    # 量化测试可视化
    quant_parser = subparsers.add_parser("quant", help="可视化量化级别测试")
    quant_parser.add_argument("--report", type=str, help="量化测试报告路径(可选)")
    
    # 稳定性测试可视化
    stability_parser = subparsers.add_parser("stability", help="可视化稳定性测试")
    stability_parser.add_argument("--report", type=str, help="稳定性测试报告路径(可选)")
    
    args = parser.parse_args()
    
    # 创建可视化工具
    visualizer = MemoryVisualizer(reports_dir=args.report_dir, output_dir=args.output_dir)
    
    # 根据命令执行对应任务
    if args.command == "single":
        visualizer.visualize_single_test(args.report)
    elif args.command == "compare":
        visualizer.visualize_multiple_tests(test_type=args.test_type, model_id=args.model_id)
    elif args.command == "quant":
        visualizer.visualize_quantization_tests(report_path=args.report)
    elif args.command == "stability":
        visualizer.visualize_stability_test(report_path=args.report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 