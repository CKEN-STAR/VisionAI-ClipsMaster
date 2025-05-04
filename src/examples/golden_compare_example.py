#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
黄金标准对比引擎使用示例

演示如何使用黄金标准对比引擎对生成的视频进行质量评估。
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from src.quality import (
    GoldenComparator,
    load_golden_dataset,
    QualityReport
)
from src.utils.logger import get_module_logger

# 设置日志
logger = get_module_logger("golden_compare")

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="黄金标准对比引擎使用示例")
    
    parser.add_argument(
        "--video",
        type=str,
        help="要评估的视频文件路径"
    )
    
    parser.add_argument(
        "--sample",
        type=str,
        default=None,
        help="黄金样本ID (可选，如不指定则自动匹配最佳样本)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./reports",
        help="报告输出目录"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "html", "text", "all"],
        default="all",
        help="报告输出格式"
    )
    
    parser.add_argument(
        "--list-samples",
        action="store_true",
        help="列出所有可用的黄金样本"
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.list_samples and not args.video:
        parser.error("必须指定 --video 参数或使用 --list-samples 参数")
    
    return args

def list_golden_samples():
    """列出所有可用的黄金样本"""
    samples = load_golden_dataset()
    
    if not samples:
        print("未找到黄金样本")
        return
    
    print(f"\n找到 {len(samples)} 个黄金样本:\n")
    print(f"{'ID':<12} {'标题':<30} {'类别':<10} {'时长(秒)':<10} {'标签'}")
    print("-" * 80)
    
    for sample_id, sample_data in samples.items():
        title = sample_data.get("title", "N/A")
        category = sample_data.get("category", "N/A")
        duration = sample_data.get("duration", 0)
        tags = ", ".join(sample_data.get("tags", []))
        
        print(f"{sample_id:<12} {title[:30]:<30} {category:<10} {duration:<10.1f} {tags}")
    
    print("\n使用示例: python golden_compare_example.py --video your_video.mp4 --sample sample_001\n")

def evaluate_video(video_path, sample_id=None, output_dir="./reports", format_type="all"):
    """使用黄金标准对比引擎评估视频质量
    
    Args:
        video_path: 视频文件路径
        sample_id: 黄金样本ID (可选)
        output_dir: 报告输出目录
        format_type: 报告输出格式
    """
    # 检查视频文件是否存在
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        return

    try:
        logger.info(f"开始评估视频: {os.path.basename(video_path)}")
        logger.info(f"样本ID: {sample_id if sample_id else '自动匹配'}")
        
        # 初始化黄金标准对比器
        comparator = GoldenComparator()
        
        # 使用黄金标准评估
        logger.info("正在进行评估...")
        result = comparator.evaluate_quality(video_path, sample_id)
        
        # 检查评估结果
        if result["status"] == "error":
            logger.error(f"评估失败: {result.get('message', '未知错误')}")
            return
        
        # 打印简要结果
        print("\n=== 评估结果摘要 ===")
        print(f"质量评级: {result['quality_rating']}")
        print(f"匹配分数: {result['match_score']:.4f}")
        print(f"质量检验: {'通过' if result['passed'] else '未通过'}")
        
        # 打印指标详情
        print("\n指标详情:")
        comparison = result.get("comparison", {})
        thresholds = result.get("thresholds", {})
        passed_criteria = result.get("passed_criteria", {})
        
        for metric, value in comparison.items():
            threshold = thresholds.get(metric, "N/A")
            passed = passed_criteria.get(metric, False)
            status = "✓" if passed else "✗"
            
            if metric == "ssim":
                print(f"  结构相似度(SSIM): {value:.4f} [阈值: {threshold}] {status}")
            elif metric == "psnr":
                print(f"  峰值信噪比(PSNR): {value:.2f} dB [阈值: {threshold}] {status}")
            elif metric == "motion_consistency":
                print(f"  运动一致性: {value:.4f} [阈值: {threshold}] {status}")
            else:
                print(f"  {metric}: {value} [阈值: {threshold}] {status}")
        
        # 生成完整报告
        logger.info("生成评估报告...")
        report = QualityReport(result, f"视频质量评估报告 - {os.path.basename(video_path)}")
        
        # 保存报告
        saved_paths = report.save_report(output_dir, format_type)
        
        print(f"\n已生成报告:")
        for fmt, path in saved_paths.items():
            print(f"  {fmt.upper()} 报告: {path}")
        
        return result
        
    except Exception as e:
        logger.error(f"评估过程中发生错误: {str(e)}")
        raise

def main():
    """主函数"""
    args = parse_arguments()
    
    # 列出所有黄金样本
    if args.list_samples:
        list_golden_samples()
        return
    
    # 评估视频
    evaluate_video(
        args.video,
        args.sample,
        args.output_dir,
        args.format
    )

if __name__ == "__main__":
    main() 