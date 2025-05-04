#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
版本演化追踪器演示程序

该脚本展示如何使用版本演化追踪器跟踪和可视化不同版本之间的关系。
"""

import os
import sys
import logging
import webbrowser
from typing import Dict, Any, List, Optional
import argparse

# 添加项目根目录到sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

from src.versioning import (
    EvolutionTracker,
    generate_html_visualization
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("evolution_tracker_demo")

def create_demo_version_tree(tracker: EvolutionTracker) -> Dict[str, str]:
    """创建演示用的版本树
    
    Args:
        tracker: 版本演化追踪器实例
    
    Returns:
        版本ID到版本名称的映射字典
    """
    version_map = {}
    
    # 根版本：初始混剪
    root_version_id = "v1.0.0"
    tracker.add_version(root_version_id, None, {
        "name": "初始混剪版本",
        "description": "基本的混剪功能，简单场景切换",
        "emotion_intensity": 0.5,
        "features": ["基础混剪", "自动场景分割"]
    })
    version_map[root_version_id] = "初始混剪版本"
    
    # 第二层版本：两个不同方向
    emotion_version_id = "v1.1.0" 
    tracker.add_version(emotion_version_id, root_version_id, {
        "name": "情感增强版",
        "description": "增强情感表达和流畅度",
        "emotion_intensity": 0.8,
        "features": ["基础混剪", "自动场景分割", "情感强化", "音乐同步"]
    })
    version_map[emotion_version_id] = "情感增强版"
    
    perf_version_id = "v1.2.0"
    tracker.add_version(perf_version_id, root_version_id, {
        "name": "性能优化版",
        "description": "优化处理速度和资源占用",
        "emotion_intensity": 0.5,
        "features": ["基础混剪", "自动场景分割", "低资源消耗", "快速渲染"]
    })
    version_map[perf_version_id] = "性能优化版"
    
    # 第三层版本：多条分支路径
    emotion_fix_id = "v1.1.1"
    tracker.add_version(emotion_fix_id, emotion_version_id, {
        "name": "情感增强修复版",
        "description": "修复情感增强中的问题，提高稳定性",
        "emotion_intensity": 0.75,
        "features": ["基础混剪", "自动场景分割", "情感强化", "音乐同步", "错误修复"]
    })
    version_map[emotion_fix_id] = "情感增强修复版"
    
    adaptive_id = "v1.1.2"
    tracker.add_version(adaptive_id, emotion_version_id, {
        "name": "自适应情感版",
        "description": "基于内容自动调整情感强度",
        "emotion_intensity": 0.7,
        "features": ["基础混剪", "自动场景分割", "情感强化", "音乐同步", "自适应调节"]
    })
    version_map[adaptive_id] = "自适应情感版"
    
    mobile_id = "v1.2.1"
    tracker.add_version(mobile_id, perf_version_id, {
        "name": "移动设备优化版",
        "description": "专为移动设备优化的版本",
        "emotion_intensity": 0.5,
        "features": ["基础混剪", "自动场景分割", "低资源消耗", "移动优化", "快速渲染"]
    })
    version_map[mobile_id] = "移动设备优化版"
    
    # 第四层版本：融合两个分支的特性
    complete_id = "v2.0.0"
    tracker.add_version(complete_id, adaptive_id, {
        "name": "完整功能版",
        "description": "集成所有功能的完整版本",
        "emotion_intensity": 0.7,
        "features": [
            "基础混剪", "自动场景分割", "情感强化", "音乐同步", 
            "自适应调节", "低资源消耗", "快速渲染", "多平台支持"
        ]
    })
    version_map[complete_id] = "完整功能版"
    
    # 从性能分支合并到完整版
    tracker.add_version(complete_id, mobile_id, None)
    
    # 第五层版本：最终稳定版
    stable_id = "v2.1.0"
    tracker.add_version(stable_id, complete_id, {
        "name": "稳定发布版",
        "description": "全面测试并优化的稳定版本",
        "emotion_intensity": 0.7,
        "features": [
            "基础混剪", "自动场景分割", "情感强化", "音乐同步", 
            "自适应调节", "低资源消耗", "快速渲染", "多平台支持",
            "错误修复", "稳定性增强"
        ]
    })
    version_map[stable_id] = "稳定发布版"
    
    return version_map

def get_visualization_output_path() -> str:
    """获取可视化输出路径
    
    Returns:
        输出HTML文件的完整路径
    """
    output_dir = os.path.join(project_root, "output", "visualization")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "version_evolution.html")

def print_version_info(version_map: Dict[str, str]) -> None:
    """打印版本信息
    
    Args:
        version_map: 版本ID到版本名称的映射字典
    """
    print("\n版本演化追踪器演示 - 版本列表：")
    print("-" * 50)
    for version_id, version_name in version_map.items():
        print(f"- {version_id}: {version_name}")
    print("-" * 50)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="版本演化追踪器演示程序")
    parser.add_argument("--version", "-v", help="要查看谱系的版本ID", default="v2.1.0")
    parser.add_argument("--open", "-o", action="store_true", help="是否自动打开浏览器查看可视化结果")
    args = parser.parse_args()
    
    # 初始化临时DB路径
    db_path = os.path.join(project_root, "data", "demo_version_db.json")
    
    # 创建追踪器并构建版本树
    tracker = EvolutionTracker(db_path)
    version_map = create_demo_version_tree(tracker)
    
    # 打印版本信息
    print_version_info(version_map)
    
    # 选择要可视化的版本ID
    version_id = args.version
    if version_id not in version_map:
        logger.warning(f"版本 {version_id} 不存在，将使用默认版本 v2.1.0")
        version_id = "v2.1.0"
    
    # 生成谱系可视化
    output_path = get_visualization_output_path()
    tree_data = tracker.visualize_lineage(version_id)
    
    # 将树数据保存为HTML可视化
    html_path = generate_html_visualization(tree_data, output_path)
    logger.info(f"版本演化可视化已生成: {html_path}")
    
    # 是否自动打开浏览器
    if args.open and html_path:
        webbrowser.open(f"file://{os.path.abspath(html_path)}")
        logger.info("已在浏览器中打开可视化页面")

if __name__ == "__main__":
    main() 