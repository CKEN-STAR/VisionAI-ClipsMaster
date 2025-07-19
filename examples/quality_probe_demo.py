#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态质量探针系统演示程序

这个示例展示了如何使用动态质量探针系统来评估视频质量，并生成质量报告。
"""

import os
import sys
import argparse
import json
from datetime import datetime

# 确保src目录在路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.quality.quality_controller import QualityController
from src.core.srt_parser import parse_subtitle
from src.utils.log_handler import configure_logging, get_logger

# 配置日志
configure_logging({
    "level": "info",
    "console_enabled": True,
    "file_enabled": True,
    "file_path": "logs",
    "file_prefix": "quality_demo"
})

logger = get_logger("quality_demo")

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="动态质量探针系统演示程序")
    parser.add_argument("--video", required=True, help="视频文件路径")
    parser.add_argument("--subtitle", required=True, help="字幕文件路径 (SRT格式)")
    parser.add_argument("--output-dir", default="output/quality_reports", help="输出目录路径")
    parser.add_argument("--config", help="质量配置文件路径")
    parser.add_argument("--html", action="store_true", help="生成HTML报告")
    parser.add_argument("--verbose", action="store_true", help="输出详细日志信息")
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not os.path.exists(args.video):
        logger.error(f"视频文件不存在: {args.video}")
        return 1
        
    if not os.path.exists(args.subtitle):
        logger.error(f"字幕文件不存在: {args.subtitle}")
        return 1
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # 解析字幕文件
    try:
        logger.info(f"正在解析字幕文件: {args.subtitle}")
        subtitle_segments = parse_subtitle(args.subtitle)
        logger.info(f"成功解析字幕，共 {len(subtitle_segments)} 个片段")
    except Exception as e:
        logger.error(f"解析字幕文件失败: {str(e)}")
        return 1
    
    # 初始化质量控制器
    try:
        logger.info("正在初始化质量控制器")
        controller = QualityController(args.config)
        logger.info("质量控制器初始化成功")
    except Exception as e:
        logger.error(f"初始化质量控制器失败: {str(e)}")
        return 1
    
    # 处理视频质量评估
    try:
        logger.info(f"开始处理视频质量评估: {args.video}")
        formats = ['json']
        if args.html:
            formats.append('html')
            
        start_time = datetime.now()
        
        result = controller.process_video(
            args.video,
            subtitle_segments,
            check_threshold=True,
            generate_report=True
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"视频质量评估完成，耗时: {processing_time:.2f}秒")
        
        # 输出结果
        if result.get('success', False):
            quality = result.get('quality', {})
            overall_score = quality.get('overall_quality', 0)
            
            logger.info(f"总体质量评分: {overall_score:.2f}")
            
            # 输出质量指标
            metrics = quality.get('metrics', {})
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    logger.info(f"- {metric}: {value:.2f}")
            
            # 输出问题和建议
            issues = quality.get('issues', [])
            if issues:
                logger.info("发现的问题:")
                for issue in issues:
                    logger.info(f"- {issue}")
            
            recommendations = result.get('recommendations', [])
            if recommendations:
                logger.info("质量改进建议:")
                for recommendation in recommendations:
                    logger.info(f"- {recommendation}")
            
            # 输出报告路径
            reports = result.get('reports', {})
            if reports:
                logger.info("生成的报告:")
                for format_type, path in reports.items():
                    logger.info(f"- {format_type}: {path}")
            
            # 保存结果摘要
            summary_path = os.path.join(args.output_dir, f"summary_{controller.session_id}.json")
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            logger.info(f"结果摘要已保存至: {summary_path}")
            
            return 0
        else:
            logger.error(f"视频质量评估失败: {result.get('error', '未知错误')}")
            return 1
    except Exception as e:
        logger.error(f"处理视频质量评估时出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 