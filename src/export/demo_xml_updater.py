#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML更新器演示脚本

展示如何使用XMLUpdater向已有工程文件增量添加新片段
"""

import os
import sys
from pathlib import Path
import logging
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.export.xml_updater import XMLUpdater
from src.export.xml_builder import create_project_xml, xml_to_string
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("demo_xml_updater")

def create_sample_project(output_file: str) -> bool:
    """
    创建示例项目文件
    
    Args:
        output_file: 输出文件路径
        
    Returns:
        bool: 创建是否成功
    """
    logger.info(f"创建示例项目文件: {output_file}")
    
    try:
        # 创建项目根节点
        root = create_project_xml("示例项目", 1920, 1080, 30.0)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # 保存项目
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_to_string(root))
            
        logger.info(f"示例项目文件创建成功: {output_file}")
        return True
    
    except Exception as e:
        logger.error(f"创建示例项目文件失败: {str(e)}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="XML更新器演示")
    parser.add_argument('--create', action='store_true', help="创建示例项目文件")
    parser.add_argument('--add', action='store_true', help="添加新片段")
    parser.add_argument('--batch', action='store_true', help="批量添加多个片段")
    parser.add_argument('--file', default="demo_project.xml", help="XML文件路径")
    args = parser.parse_args()
    
    # 默认文件路径
    xml_file = args.file
    
    # 创建示例项目
    if args.create:
        if not create_sample_project(xml_file):
            logger.error("示例项目创建失败，退出")
            return
    
    # 初始化XML更新器
    updater = XMLUpdater()
    
    # 检查文件是否存在
    if not os.path.exists(xml_file):
        logger.error(f"文件不存在: {xml_file}")
        logger.info("请先使用 --create 参数创建示例项目")
        return
    
    # 添加单个片段
    if args.add:
        # 创建新片段信息
        new_clip = {
            'resource_id': 'video_1',
            'start_time': 10.0,
            'duration': 5.0,
            'name': f"新片段_{datetime.now().strftime('%H%M%S')}",
            'has_audio': True
        }
        
        # 添加片段到项目
        result = updater.append_clip(xml_file, new_clip)
        if result:
            logger.info("片段添加成功")
        else:
            logger.error("片段添加失败")
    
    # 批量添加多个片段
    if args.batch:
        # 创建多个片段
        clips = [
            {
                'resource_id': 'video_1',
                'start_time': 15.0,
                'duration': 3.0,
                'name': f"批量片段_1_{datetime.now().strftime('%H%M%S')}",
                'has_audio': True
            },
            {
                'resource_id': 'video_1',
                'start_time': 20.0,
                'duration': 4.0,
                'name': f"批量片段_2_{datetime.now().strftime('%H%M%S')}",
                'has_audio': True
            },
            {
                'resource_id': 'video_1',
                'start_time': 25.0,
                'duration': 2.5,
                'name': f"批量片段_3_{datetime.now().strftime('%H%M%S')}",
                'has_audio': False  # 这个片段没有音频
            }
        ]
        
        # 批量添加片段
        result = updater.append_clips(xml_file, clips)
        if result:
            logger.info(f"成功批量添加{len(clips)}个片段")
        else:
            logger.error("批量添加片段失败")
    
    # 如果没有指定操作，显示帮助
    if not (args.create or args.add or args.batch):
        parser.print_help()

if __name__ == "__main__":
    main() 