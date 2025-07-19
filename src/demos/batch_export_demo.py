#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量导出演示脚本

展示如何使用数据流分析功能进行批量视频导出过程的性能优化
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.log_handler import get_logger
from src.export.premiere_exporter import PremiereXMLExporter
from src.export.fcpxml_exporter import FCPXMLExporter
from src.export.jianying_exporter import JianyingXMLExporter
from src.exporters.dataflow_analyzer import (
    start_profiling, stop_profiling, get_memory_usage,
    summarize_performance, visualization_helper
)

# 配置日志
logger = get_logger("batch_export_demo")

def create_sample_data(count: int = 5) -> List[Dict[str, Any]]:
    """
    创建示例版本数据，用于导出测试
    
    Args:
        count: 生成的版本数量
        
    Returns:
        List: 版本数据列表
    """
    versions = []
    
    for i in range(count):
        # 创建一个测试版本
        version = {
            "version_id": f"test_v{i+1}",
            "video_path": f"test_video_{i+1}.mp4",
            "scenes": []
        }
        
        # 添加场景
        scene_count = 5 + (i % 5)  # 每个版本的场景数量不同
        
        for j in range(scene_count):
            scene = {
                "scene_id": f"scene_{j+1}",
                "start_time": j * 3.5,  # 起始时间
                "duration": 2.5 + (j % 3),  # 持续时间
                "has_audio": True if j % 3 != 0 else False  # 有些场景没有音频
            }
            version["scenes"].append(scene)
        
        versions.append(version)
    
    return versions


def export_batch(versions: List[Dict[str, Any]], output_dir: str, format_type: str = "premiere", 
                 enable_profiling: bool = True) -> List[str]:
    """
    批量导出版本
    
    Args:
        versions: 版本数据列表
        output_dir: 输出目录
        format_type: 导出格式类型
        enable_profiling: 是否启用性能分析
        
    Returns:
        List: 导出的文件路径列表
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 选择导出器
    if format_type.lower() == "premiere":
        exporter = PremiereXMLExporter()
    elif format_type.lower() == "fcpxml":
        exporter = FCPXMLExporter()
    elif format_type.lower() == "jianying":
        exporter = JianyingXMLExporter()
    else:
        raise ValueError(f"不支持的导出格式: {format_type}")
    
    # 如果启用了性能分析，开始收集批量处理的性能数据
    if enable_profiling:
        start_profiling("batch_export")
        initial_memory = get_memory_usage()
        start_time = time.time()
        logger.info(f"批量导出开始，当前内存使用量: {initial_memory:.2f}MB")
    
    # 导出的文件路径列表
    exported_files = []
    
    try:
        # 导出每个版本
        for i, version in enumerate(versions):
            version_id = version.get("version_id", f"unknown_{i}")
            output_path = os.path.join(output_dir, f"{version_id}.{format_type.lower()}")
            
            logger.info(f"导出版本 {i+1}/{len(versions)}: {version_id}")
            
            # 导出并启用单个文件的性能分析
            output_file = exporter.export(version, output_path, enable_profiling=True)
            exported_files.append(output_file)
            
            # 记录当前内存使用情况
            if enable_profiling:
                memory_usage = get_memory_usage()
                logger.info(f"  - 导出完成，当前内存使用量: {memory_usage:.2f}MB")
        
        return exported_files
        
    finally:
        # 如果启用了性能分析，停止收集并生成报告
        if enable_profiling:
            final_memory = get_memory_usage()
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info("=" * 50)
            logger.info("批量导出性能统计")
            logger.info(f"总耗时: {total_time:.2f}秒")
            logger.info(f"导出文件数量: {len(exported_files)}")
            logger.info(f"平均每个文件耗时: {total_time/len(versions):.2f}秒")
            logger.info(f"内存使用增长: {final_memory - initial_memory:.2f}MB")
            logger.info("=" * 50)
            
            # 停止批量处理性能分析
            profile_data = stop_profiling("batch_export")
            if profile_data:
                # 设置元数据
                profile_data.set_metadata('total_files', len(versions))
                profile_data.set_metadata('export_format', format_type)
                
                # 保存性能数据
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                report_path = os.path.join(output_dir, f"batch_export_perf_{timestamp}.json")
                profile_data.save_to_file(report_path)
                
                # 尝试生成可视化报告
                try:
                    viz_path = visualization_helper('batch_export', 
                                            os.path.join(output_dir, f"batch_export_viz_{timestamp}.png"))
                    if viz_path:
                        logger.info(f"性能可视化图表已生成: {viz_path}")
                except Exception as viz_error:
                    logger.warning(f"生成可视化报告失败: {viz_error}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量导出演示脚本")
    parser.add_argument("--count", type=int, default=3, help="导出的示例版本数量")
    parser.add_argument("--format", default="premiere", choices=["premiere", "fcpxml", "jianying"], 
                        help="导出格式类型")
    parser.add_argument("--output", default="outputs", help="输出目录")
    parser.add_argument("--no-profiling", action="store_true", help="禁用性能分析")
    
    args = parser.parse_args()
    
    # 创建一些示例数据
    logger.info(f"创建 {args.count} 个示例版本数据...")
    versions = create_sample_data(args.count)
    
    # 设置输出目录路径
    output_dir = args.output
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(project_root, output_dir)
    
    # 启动批量导出
    logger.info(f"开始批量导出到 {output_dir}...")
    exported_files = export_batch(
        versions, 
        output_dir, 
        format_type=args.format,
        enable_profiling=not args.no_profiling
    )
    
    # 输出结果
    logger.info(f"成功导出 {len(exported_files)} 个文件:")
    for file_path in exported_files:
        logger.info(f"  - {file_path}")


if __name__ == "__main__":
    main() 