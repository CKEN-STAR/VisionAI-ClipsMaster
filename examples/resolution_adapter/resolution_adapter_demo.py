#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分辨率适配器示例

演示如何使用分辨率适配器处理不同分辨率的视频
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入分辨率处理模块
from src.export.resolution_handler import (
    get_video_dimensions,
    add_resolution_meta,
    adapt_xml_resolution
)

# 导入XML构建器模块
from src.export.xml_builder import (
    create_project_xml, 
    xml_to_string
)

# 导入导出器模块
from src.export.jianying_exporter import JianyingExporter
from src.export.fcpxml_exporter import FCPXMLExporter
from src.export.premiere_exporter import PremiereXMLExporter

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_separator(text: str = None):
    """打印分隔线"""
    width = 80
    if text:
        text = f" {text} "
        padding = (width - len(text)) // 2
        print("=" * padding + text + "=" * padding)
    else:
        print("=" * width)

def demo_get_dimensions(video_path: str):
    """演示获取视频分辨率"""
    print_separator("获取视频分辨率")
    width, height = get_video_dimensions(video_path)
    print(f"视频路径: {video_path}")
    print(f"视频分辨率: {width}x{height}")
    return width, height

def create_test_xml(width: int = 1920, height: int = 1080):
    """创建测试用XML"""
    root = create_project_xml("测试项目", width, height, 30.0)
    return xml_to_string(root)

def demo_add_resolution_node(video_path: str):
    """演示添加分辨率节点"""
    print_separator("添加分辨率节点")
    
    # 创建测试XML
    xml_content = create_test_xml()
    
    # 添加分辨率节点
    modified_xml = add_resolution_meta(xml_content, video_path)
    
    # 打印修改后的XML片段
    print("修改后的XML片段:")
    lines = modified_xml.split('\n')
    for i, line in enumerate(lines):
        if '<resolution' in line or '</project>' in line:
            print(f"{i+1}: {line}")
            if '</project>' in line:
                print(f"{i}: {lines[i-1]}")  # 显示resolution节点
    
    return modified_xml

def demo_adapt_resolution(video_path: str):
    """演示适配XML分辨率"""
    print_separator("适配XML分辨率")
    
    # 创建测试XML (固定为1080p)
    xml_content = create_test_xml(1920, 1080)
    print("原始XML分辨率: 1920x1080")
    
    # 获取视频分辨率
    width, height = get_video_dimensions(video_path)
    print(f"视频分辨率: {width}x{height}")
    
    # 适配XML分辨率
    modified_xml = adapt_xml_resolution(xml_content, video_path)
    
    # 打印修改后的XML片段
    print("适配后的XML片段:")
    for line in modified_xml.split('\n'):
        if '<width>' in line or '<height>' in line or 'width=' in line or 'height=' in line:
            print(line.strip())
    
    return modified_xml

def demo_exporters(video_path: str, output_dir: str):
    """演示使用导出器适配分辨率"""
    print_separator("使用导出器适配分辨率")
    
    # 准备测试数据
    test_version = {
        "version_id": "res_test",
        "video_path": video_path,
        "scenes": [
            {
                "scene_id": "scene_1",
                "start_time": 0.0,
                "duration": 5.0,
                "has_audio": True
            },
            {
                "scene_id": "scene_2",
                "start_time": 10.0,
                "duration": 8.0,
                "has_audio": True
            }
        ]
    }
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用剪映导出器
    print("1. 使用剪映导出器...")
    jy_exporter = JianyingExporter()
    jy_output = os.path.join(output_dir, "jianying_test.json")
    jy_exporter.export(test_version, jy_output)
    
    # 使用FCPXML导出器
    print("2. 使用FCPXML导出器...")
    fcp_exporter = FCPXMLExporter()
    fcp_output = os.path.join(output_dir, "fcpxml_test.fcpxml")
    fcp_exporter.export(test_version, fcp_output)
    
    # 使用Premiere导出器
    print("3. 使用Premiere导出器...")
    pr_exporter = PremiereXMLExporter()
    pr_output = os.path.join(output_dir, "premiere_test.xml")
    pr_exporter.export(test_version, pr_output)
    
    print(f"\n导出的文件保存在: {output_dir}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="分辨率适配器示例")
    parser.add_argument("--video", "-v", required=True, help="输入视频文件路径")
    parser.add_argument("--output", "-o", default="./output", help="输出文件夹路径")
    args = parser.parse_args()
    
    # 判断视频文件是否存在
    if not os.path.exists(args.video):
        logger.error(f"视频文件不存在: {args.video}")
        return
    
    # 执行演示
    print_separator("分辨率适配器演示")
    print(f"使用视频: {args.video}")
    
    # 1. 获取视频分辨率
    demo_get_dimensions(args.video)
    
    # 2. 添加分辨率节点
    demo_add_resolution_node(args.video)
    
    # 3. 适配XML分辨率
    demo_adapt_resolution(args.video)
    
    # 4. 使用导出器适配分辨率
    demo_exporters(args.video, args.output)
    
    print_separator("演示完成")
    
    
if __name__ == "__main__":
    main() 