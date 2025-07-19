#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多维度比对命令行工具

此脚本提供了方便的命令行接口，用于执行视频和字幕的多维度比对。
可用于质量控制、回归测试和内容验证。
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# 导入比对引擎
try:
    from tests.golden_samples.compare_engine import compare_files, CompareResult
except ImportError:
    print("错误: 无法导入多维度比对引擎，请确保项目结构正确")
    sys.exit(1)

def format_time(seconds: float) -> str:
    """将秒数格式化为时分秒格式"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:05.2f}"

def get_dimensions_description() -> Dict[str, Dict[str, str]]:
    """获取各个维度的说明"""
    return {
        "video": {
            "duration": "视频时长匹配度，考虑两个视频的总时长差异",
            "resolution": "分辨率匹配度，考虑宽高和宽高比",
            "color_hist": "色彩分布相似度，基于HSV色彩直方图比较",
            "fingerprint": "视频指纹相似度，基于关键帧特征",
            "keyframe_psnr": "关键帧质量相似度，基于PSNR信噪比"
        },
        "subtitle": {
            "timecode": "时间码对齐度，考虑字幕时间点的匹配情况",
            "text_sim": "文本相似度，基于字幕文本内容比较",
            "entity_match": "实体匹配度，检测人名、地名等关键实体的匹配程度",
            "length_ratio": "长度比例，比较字幕总字符数的比例"
        }
    }

def create_html_report(result: CompareResult, test_output: str, golden_sample: str, elapsed_time: float) -> str:
    """
    创建HTML格式的比对报告
    
    Args:
        result: 比对结果
        test_output: 测试输出路径
        golden_sample: 黄金样本路径
        elapsed_time: 耗时(秒)
        
    Returns:
        str: HTML报告内容
    """
    # 获取维度说明
    dimensions_desc = get_dimensions_description()
    
    # 格式化得分为百分比
    def format_score(score):
        return f"{score*100:.1f}%"
    
    # 得分到颜色的映射
    def score_color(score):
        if score >= 0.9:
            return "#4CAF50"  # 绿色
        elif score >= 0.7:
            return "#FFC107"  # 黄色
        else:
            return "#F44336"  # 红色
    
    # 构建HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>多维度比对报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        h1 {{ color: #333; text-align: center; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary-item {{ margin-bottom: 10px; }}
        .score {{ font-weight: bold; }}
        .pass {{ color: #4CAF50; }}
        .fail {{ color: #F44336; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .dimension-name {{ width: 20%; }}
        .dimension-score {{ width: 15%; text-align: center; }}
        .dimension-desc {{ width: 65%; }}
        .bar-container {{ width: 100%; background-color: #f1f1f1; border-radius: 3px; }}
        .bar {{ height: 12px; border-radius: 3px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>多维度比对报告</h1>
        
        <div class="summary">
            <div class="summary-item">
                <strong>总体得分:</strong> 
                <span class="score" style="color: {score_color(result.total_score)}">
                    {format_score(result.total_score)} 
                    {'✓' if result.is_passed() else '✗'}
                </span>
            </div>
            <div class="summary-item">
                <strong>视频得分:</strong> 
                <span class="score" style="color: {score_color(result.video_score)}">{format_score(result.video_score)}</span>
            </div>
            <div class="summary-item">
                <strong>字幕得分:</strong> 
                <span class="score" style="color: {score_color(result.subtitle_score)}">{format_score(result.subtitle_score)}</span>
            </div>
            <div class="summary-item"><strong>测试文件:</strong> {os.path.basename(test_output)}</div>
            <div class="summary-item"><strong>黄金样本:</strong> {os.path.basename(golden_sample)}</div>
            <div class="summary-item"><strong>处理时间:</strong> {format_time(elapsed_time)}</div>
        </div>
        
        <h2>视频比对结果</h2>
        <table>
            <tr>
                <th class="dimension-name">维度</th>
                <th class="dimension-score">得分</th>
                <th class="dimension-desc">说明</th>
            </tr>"""
    
    # 添加视频维度
    for dim, score in result.scores["video"].items():
        desc = dimensions_desc["video"].get(dim, "")
        color = score_color(score)
        html += f"""
            <tr>
                <td class="dimension-name">{dim}</td>
                <td class="dimension-score" style="color: {color}">{format_score(score)}</td>
                <td class="dimension-desc">
                    {desc}
                    <div class="bar-container">
                        <div class="bar" style="width: {score*100}%; background-color: {color}"></div>
                    </div>
                </td>
            </tr>"""
    
    html += """
        </table>
        
        <h2>字幕比对结果</h2>
        <table>
            <tr>
                <th class="dimension-name">维度</th>
                <th class="dimension-score">得分</th>
                <th class="dimension-desc">说明</th>
            </tr>"""
    
    # 添加字幕维度
    for dim, score in result.scores["subtitle"].items():
        desc = dimensions_desc["subtitle"].get(dim, "")
        color = score_color(score)
        html += f"""
            <tr>
                <td class="dimension-name">{dim}</td>
                <td class="dimension-score" style="color: {color}">{format_score(score)}</td>
                <td class="dimension-desc">
                    {desc}
                    <div class="bar-container">
                        <div class="bar" style="width: {score*100}%; background-color: {color}"></div>
                    </div>
                </td>
            </tr>"""
    
    html += """
        </table>
        
        <div class="footer">
            <p>VisionAI-ClipsMaster 多维度比对引擎生成的报告</p>
        </div>
    </div>
</body>
</html>"""
    
    return html

def create_json_report(result: CompareResult, test_output: str, golden_sample: str, elapsed_time: float) -> str:
    """
    创建JSON格式的比对报告
    
    Args:
        result: 比对结果
        test_output: 测试输出路径
        golden_sample: 黄金样本路径
        elapsed_time: 耗时(秒)
        
    Returns:
        str: JSON报告内容
    """
    report = {
        "summary": {
            "total_score": result.total_score,
            "video_score": result.video_score,
            "subtitle_score": result.subtitle_score,
            "passed": result.is_passed(),
            "test_file": os.path.basename(test_output),
            "golden_sample": os.path.basename(golden_sample),
            "elapsed_time": elapsed_time
        },
        "details": result.scores
    }
    
    return json.dumps(report, indent=2)

def run_comparison(test_output: str, golden_sample: str = None, threshold: float = 0.8,
                 output_format: str = "text", output_file: str = None) -> int:
    """
    运行比对并生成报告
    
    Args:
        test_output: 测试输出路径
        golden_sample: 黄金样本路径
        threshold: 通过阈值
        output_format: 输出格式 (text, json, html)
        output_file: 输出文件路径
        
    Returns:
        int: 0表示成功，其他值表示失败
    """
    # 移除文件扩展名（如果有）
    test_output = os.path.splitext(test_output)[0]
    if golden_sample:
        golden_sample = os.path.splitext(golden_sample)[0]
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 执行比对
        result = compare_files(test_output, golden_sample, threshold)
        
        # 计算耗时
        elapsed_time = time.time() - start_time
        
        # 根据输出格式生成报告
        if output_format == "json":
            report = create_json_report(result, test_output, golden_sample or "自动推断", elapsed_time)
        elif output_format == "html":
            report = create_html_report(result, test_output, golden_sample or "自动推断", elapsed_time)
        else:  # text
            report = str(result)
        
        # 输出报告
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"比对报告已保存到: {output_file}")
        else:
            print(report)
        
        # 返回是否通过的状态码
        return 0 if result.is_passed() else 1
    
    except Exception as e:
        print(f"比对过程出错: {str(e)}")
        return 2

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="多维度比对命令行工具")
    
    parser.add_argument("test_output", help="测试输出文件前缀(不含扩展名)")
    parser.add_argument("--golden", "-g", help="黄金样本文件前缀(不含扩展名)，若不提供则自动推断")
    parser.add_argument("--threshold", "-t", type=float, default=0.8,
                       help="通过阈值 (0-1 之间，默认 0.8)")
    parser.add_argument("--format", "-f", choices=["text", "json", "html"], default="text",
                       help="输出格式 (text, json, html)")
    parser.add_argument("--output", "-o", help="输出文件路径，若不提供则输出到控制台")
    
    args = parser.parse_args()
    
    # 运行比对
    exit_code = run_comparison(
        args.test_output,
        args.golden,
        args.threshold,
        args.format,
        args.output
    )
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 