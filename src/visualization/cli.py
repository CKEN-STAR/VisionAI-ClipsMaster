#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化模块命令行接口 - 提供从命令行直接调用可视化功能
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

# 导入可视化模块
from src.visualization.standalone_test import (
    generate_test_data,
    export_visualization_report
)

def setup_logger() -> None:
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='剧本分析可视化工具')
    
    parser.add_argument('--input', '-i', type=str, default=None,
                        help='输入JSON文件路径，指定剧本数据源')
    
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出文件路径，指定报告保存位置')
    
    parser.add_argument('--format', '-f', type=str, default='html',
                        choices=['html', 'png', 'pdf'],
                        help='输出格式，支持html/png/pdf')
    
    parser.add_argument('--open', '-p', action='store_true',
                        help='生成后自动打开报告')
    
    parser.add_argument('--sample', '-s', action='store_true',
                        help='生成示例数据用于测试')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 配置日志
    setup_logger()
    logger = logging.getLogger("visualization_cli")
    
    # 解析参数
    args = parse_arguments()
    
    try:
        # 处理输入参数
        script_data = None
        
        # 读取输入文件
        if args.input:
            # 从JSON文件加载
            logger.info(f"从文件加载数据: {args.input}")
            try:
                with open(args.input, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
            except Exception as e:
                logger.error(f"读取JSON文件失败: {str(e)}")
                return 1
        elif args.sample:
            # 生成示例数据
            logger.info("生成示例数据...")
            script_data = generate_test_data()
            
            # 保存示例数据
            sample_dir = os.path.join(ROOT_DIR, "data", "test")
            os.makedirs(sample_dir, exist_ok=True)
            sample_path = os.path.join(sample_dir, "sample_script_data.json")
            
            with open(sample_path, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"示例数据已保存到: {sample_path}")
        else:
            # 如果没有指定输入也没有生成示例，尝试使用默认测试数据
            default_test_data = os.path.join(ROOT_DIR, "data", "test", "test_script_data.json")
            if os.path.exists(default_test_data):
                logger.info(f"使用默认测试数据: {default_test_data}")
                with open(default_test_data, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
            else:
                logger.error("未指定输入文件且无法找到默认测试数据")
                logger.info("请使用 --input 指定输入文件或 --sample 生成示例数据")
                return 1
        
        # 处理输出参数
        if args.output:
            output_path = args.output
        else:
            # 使用默认输出路径
            process_id = script_data.get("process_id", "report")
            output_dir = os.path.join(ROOT_DIR, "data", "output", "reports")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{process_id}_report.{args.format}")
        
        # 生成报告
        logger.info(f"生成可视化报告: {output_path}")
        report_path = export_visualization_report(script_data, output_path)
        
        logger.info(f"报告已生成: {report_path}")
        
        # 是否打开报告
        if args.open:
            import webbrowser
            report_url = f"file://{os.path.abspath(report_path)}"
            logger.info(f"正在打开报告: {report_url}")
            webbrowser.open(report_url)
        
        return 0
    
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 