#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感强度图谱构建演示

展示如何使用情感强度图谱构建模块分析视频/剧本的情感曲线。
包括基础曲线构建、可视化和流程质量分析功能。
"""

import os
import sys
import json
import logging
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入情感强度映射器
from src.emotion.intensity_mapper import EmotionMapper, build_intensity_curve
from src.emotion.visualizer import visualize_intensity_curve

# 导入样本数据生成器
from src.utils.sample_data import generate_sample_script

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='情感强度图谱构建演示')
    parser.add_argument('--output-dir', type=str, default='reports/emotion_intensity',
                      help='输出目录')
    parser.add_argument('--script-type', type=str, default='standard',
                      choices=['standard', 'emotional', 'flat', 'rollercoaster'],
                      help='剧本类型')
    parser.add_argument('--scene-count', type=int, default=15,
                      help='场景数量')
    parser.add_argument('--visualize', action='store_true',
                      help='显示可视化结果')
    parser.add_argument('--interactive', action='store_true',
                      help='生成交互式图表')
    parser.add_argument('--seed', type=int, default=None,
                      help='随机种子')
    parser.add_argument('--verbose', action='store_true',
                      help='显示详细信息')
    
    args = parser.parse_args()
    
    # 设置随机种子
    if args.seed is not None:
        random.seed(args.seed)
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 生成样本剧本
    logger.info(f"生成{args.script_type}类型的样本剧本，包含{args.scene_count}个场景")
    sample_script = generate_sample_script(
        scene_count=args.scene_count,
        script_type=args.script_type
    )
    
    # 保存样本剧本
    script_path = os.path.join(args.output_dir, 'sample_script.json')
    with open(script_path, 'w', encoding='utf-8') as f:
        json.dump(sample_script, f, ensure_ascii=False, indent=2)
    logger.info(f"样本剧本已保存至: {script_path}")
    
    # 初始化情感强度映射器
    mapper = EmotionMapper()
    
    # 构建情感强度曲线
    logger.info("构建情感强度曲线")
    start_time = logger.info("开始构建情感强度曲线")
    curve_data = mapper.build_intensity_curve(sample_script)
    logger.info("情感强度曲线构建完成")
    
    # 保存情感曲线数据
    curve_path = os.path.join(args.output_dir, 'emotion_curve.json')
    with open(curve_path, 'w', encoding='utf-8') as f:
        json.dump(curve_data, f, ensure_ascii=False, indent=2)
    logger.info(f"情感强度曲线数据已保存至: {curve_path}")
    
    # 分析情感流程质量
    flow_analysis = mapper.analyze_emotion_flow(curve_data)
    
    # 输出分析结果
    logger.info(f"情感流程质量分析结果:")
    logger.info(f"  质量评分: {flow_analysis['quality']:.2f}/1.0")
    logger.info(f"  情感范围: {flow_analysis['emotion_range']:.2f}")
    logger.info(f"  转折点数量: {flow_analysis['turning_points']}")
    logger.info(f"  存在明显高潮: {'是' if flow_analysis['has_climax'] else '否'}")
    
    if flow_analysis['issues']:
        logger.info("检测到的问题:")
        for issue in flow_analysis['issues']:
            logger.info(f"  - {issue}")
    
    # 保存分析结果
    analysis_path = os.path.join(args.output_dir, 'flow_analysis.json')
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(flow_analysis, f, ensure_ascii=False, indent=2)
    logger.info(f"情感流程分析结果已保存至: {analysis_path}")
    
    # 可视化情感曲线
    logger.info("生成情感强度可视化图表")
    outputs = visualize_intensity_curve(
        curve_data, 
        output_dir=args.output_dir,
        show_fig=args.visualize
    )
    
    if args.verbose:
        # 输出曲线的详细信息
        logger.info(f"情感曲线详情:")
        for i, point in enumerate(curve_data):
            special_marks = []
            if point.get("is_peak", False):
                special_marks.append("峰值")
            if point.get("is_valley", False):
                special_marks.append("低谷")
            if point.get("is_global_peak", False):
                special_marks.append("全局峰值")
            if point.get("is_global_valley", False):
                special_marks.append("全局低谷")
                
            mark_text = f" ({', '.join(special_marks)})" if special_marks else ""
            logger.info(f"  场景 {i+1}: 强度={point['peak_value']:.2f}{mark_text}")
            if args.verbose:
                text = point.get("raw_text", "")
                if len(text) > 50:
                    text = text[:47] + "..."
                logger.info(f"    文本: {text}")
    
    logger.info(f"情感强度图谱演示完成，所有输出已保存至: {args.output_dir}")
    
    # 创建完整的报告
    create_report(args.output_dir, sample_script, curve_data, flow_analysis)


def create_report(output_dir: str, 
                script: List[Dict[str, Any]], 
                curve_data: List[Dict[str, Any]], 
                analysis: Dict[str, Any]) -> None:
    """
    创建完整的情感分析报告
    
    Args:
        output_dir: 输出目录
        script: 剧本数据
        curve_data: 情感曲线数据
        analysis: 情感流程分析结果
    """
    report = {
        'script': script,
        'emotion_curve': curve_data,
        'analysis': analysis
    }
    
    # 保存报告
    report_path = os.path.join(output_dir, 'emotion_analysis_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"完整情感分析报告已保存至: {report_path}")
    
    try:
        # 尝试创建HTML报告
        html_report_path = os.path.join(output_dir, 'emotion_analysis_report.html')
        
        # HTML模板
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>情感强度分析报告</title>
    <style>
        body {font-family: Arial, sans-serif; margin: 0; padding: 20px;}
        .container {max-width: 1200px; margin: 0 auto;}
        .header {text-align: center; margin-bottom: 30px;}
        .section {margin-bottom: 40px; border: 1px solid #ddd; padding: 20px; border-radius: 5px;}
        .charts {display: flex; flex-wrap: wrap; justify-content: space-between;}
        .chart {width: 48%; margin-bottom: 20px;}
        .chart img {max-width: 100%;}
        .metrics {display: flex; flex-wrap: wrap;}
        .metric {width: 48%; margin-bottom: 15px;}
        h1, h2, h3 {color: #333;}
        .score {font-size: 24px; font-weight: bold;}
        .good {color: green;}
        .average {color: orange;}
        .poor {color: red;}
        table {width: 100%; border-collapse: collapse;}
        table, th, td {border: 1px solid #ddd;}
        th, td {padding: 8px; text-align: left;}
        th {background-color: #f2f2f2;}
        tr:nth-child(even) {background-color: #f9f9f9;}
        .issues {margin-top: 20px;}
        .issue {background-color: #fff3cd; padding: 8px; margin-bottom: 5px; border-left: 3px solid #ffc107;}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>情感强度分析报告</h1>
        </div>
        
        <div class="section">
            <h2>情感质量评分</h2>
            <div class="metrics">
                <div class="metric">
                    <h3>总体质量</h3>
                    <div class="score {score_class}">{quality:.2f}/1.0</div>
                </div>
                <div class="metric">
                    <h3>情感变化幅度</h3>
                    <div>{emotion_range:.2f}</div>
                </div>
                <div class="metric">
                    <h3>情感转折点</h3>
                    <div>{turning_points} 个</div>
                </div>
                <div class="metric">
                    <h3>存在明显高潮</h3>
                    <div>{has_climax}</div>
                </div>
            </div>
            
            <div class="issues">
                <h3>检测到的问题</h3>
                {issues_html}
            </div>
        </div>
        
        <div class="section">
            <h2>情感曲线可视化</h2>
            <div class="charts">
                <div class="chart">
                    <h3>情感强度曲线</h3>
                    <img src="emotion_intensity_curve.png" alt="情感强度曲线">
                </div>
                <div class="chart">
                    <h3>情感强度热力图</h3>
                    <img src="emotion_intensity_heatmap.png" alt="情感强度热力图">
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>场景情感数据</h2>
            <table>
                <tr>
                    <th>场景</th>
                    <th>情感强度</th>
                    <th>特征</th>
                    <th>文本片段</th>
                </tr>
                {table_rows}
            </table>
        </div>
    </div>
</body>
</html>"""
        
        # 准备HTML数据
        score_class = "good" if analysis['quality'] >= 0.7 else "average" if analysis['quality'] >= 0.4 else "poor"
        
        issues_html = ""
        if analysis['issues']:
            for issue in analysis['issues']:
                issues_html += f'<div class="issue">{issue}</div>'
        else:
            issues_html = '<div>未检测到明显问题</div>'
        
        table_rows = ""
        for i, point in enumerate(curve_data):
            special_marks = []
            if point.get("is_peak", False):
                special_marks.append("峰值")
            if point.get("is_valley", False):
                special_marks.append("低谷")
            if point.get("is_global_peak", False):
                special_marks.append("全局峰值")
            if point.get("is_global_valley", False):
                special_marks.append("全局低谷")
                
            features = ", ".join(special_marks) if special_marks else "普通点"
            
            text = point.get("raw_text", "")
            if len(text) > 50:
                text = text[:47] + "..."
            
            row = f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{point['peak_value']:.2f}</td>
                    <td>{features}</td>
                    <td>{text}</td>
                </tr>"""
            table_rows += row
        
        # 填充模板
        html_content = html_template.format(
            quality=analysis['quality'],
            score_class=score_class,
            emotion_range=analysis['emotion_range'],
            turning_points=analysis['turning_points'],
            has_climax="是" if analysis['has_climax'] else "否",
            issues_html=issues_html,
            table_rows=table_rows
        )
        
        # 保存HTML报告
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML分析报告已保存至: {html_report_path}")
        
    except Exception as e:
        logger.error(f"创建HTML报告失败: {e}")


if __name__ == "__main__":
    main() 