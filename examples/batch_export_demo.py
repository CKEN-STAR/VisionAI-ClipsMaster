#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量导出演示程序

演示如何使用批量导出流水线将多个版本导出为不同格式。
"""

import os
import sys
import json
import logging
from pathlib import Path
import random
from datetime import datetime

# 将项目根目录添加到导入路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 导入所需模块
from src.export.batch_exporter import (
    export_versions,
    export_version,
    BatchExportPipeline
)
from src.utils.log_handler import get_logger

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger("batch_export_demo")

def create_test_versions(count: int = 3) -> list:
    """
    创建测试版本数据
    
    Args:
        count: 要创建的版本数量
        
    Returns:
        版本列表
    """
    versions = []
    
    for i in range(count):
        # 生成随机场景数
        scene_count = random.randint(5, 10)
        
        # 创建场景
        scenes = []
        for j in range(scene_count):
            scene = {
                "scene_id": f"scene_{i+1}_{j+1}",
                "text": f"这是版本{i+1}的第{j+1}个场景",
                "start_time": j * 5,
                "duration": random.randint(3, 8),
                "has_audio": random.choice([True, True, False])  # 大部分场景有音频
            }
            scenes.append(scene)
        
        # 创建版本
        version = {
            "version_id": f"version_{i+1}",
            "title": f"测试版本 {i+1}",
            "description": f"这是用于测试批量导出功能的版本 {i+1}",
            "created_at": datetime.now().isoformat(),
            "video_path": f"D:/videos/test_video_{i+1}.mp4",  # 假设的视频路径
            "scenes": scenes
        }
        
        versions.append(version)
    
    return versions

def main():
    """主函数"""
    logger.info("开始批量导出演示")
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "exports")
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建测试版本
    versions = create_test_versions(3)
    logger.info(f"已创建 {len(versions)} 个测试版本")
    
    # 保存版本数据以便查看
    versions_json_path = os.path.join(output_dir, "test_versions.json")
    with open(versions_json_path, "w", encoding="utf-8") as f:
        json.dump(versions, f, ensure_ascii=False, indent=2)
    logger.info(f"版本数据已保存到: {versions_json_path}")
    
    # 定义要导出的格式
    export_formats = ["SRT", "剪映", "Premiere", "FCPX"]
    
    # 演示单个版本导出
    logger.info("开始导出单个版本...")
    single_output_dir = os.path.join(output_dir, "single_version")
    os.makedirs(single_output_dir, exist_ok=True)
    
    single_results = export_version(versions[0], export_formats, single_output_dir)
    
    logger.info("单个版本导出结果:")
    for fmt, path in single_results.items():
        logger.info(f"  {fmt}: {path}")
    
    # 演示批量导出
    logger.info("开始批量导出所有版本...")
    try:
        # 批量导出所有版本为所有格式
        batch_output = export_versions(versions, export_formats)
        logger.info(f"批量导出完成，压缩包路径: {batch_output}")
        
        # 将压缩包复制到输出目录
        import shutil
        batch_output_copy = os.path.join(output_dir, os.path.basename(batch_output))
        shutil.copy2(batch_output, batch_output_copy)
        logger.info(f"批量导出结果已复制到: {batch_output_copy}")
        
    except Exception as e:
        logger.error(f"批量导出失败: {str(e)}")
    
    logger.info("批量导出演示完成")
    
    # 打印摘要
    print("\n导出摘要:")
    print(f"- 导出版本数量: {len(versions)}")
    print(f"- 导出格式: {', '.join(export_formats)}")
    print(f"- 单个版本导出目录: {single_output_dir}")
    print(f"- 批量导出结果: {batch_output_copy if 'batch_output_copy' in locals() else 'Failed'}")
    print(f"\n所有导出内容已保存在: {output_dir}")

if __name__ == "__main__":
    main() 