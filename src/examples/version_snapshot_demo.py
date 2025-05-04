#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本快照系统演示脚本

演示如何使用多版本快照系统管理不同版本的剧本和场景。
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 导入版本快照系统
from src.versioning import (
    Snapshotter,
    SnapshotType,
    take_snapshot,
    restore_snapshot,
    compare_snapshots,
    list_snapshots,
    SceneVersionManager
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("version_demo")


def create_sample_scenes() -> List[Dict[str, Any]]:
    """创建示例场景"""
    return [
        {
            "scene_id": "scene1",
            "text": "主角小明走在街上，突然看到一个神秘的信封。",
            "duration": 5.0,
            "character": "小明"
        },
        {
            "scene_id": "scene2",
            "text": "小明打开信封，发现里面是一张神秘地图。",
            "duration": 4.0,
            "character": "小明"
        },
        {
            "scene_id": "scene3",
            "text": "小明决定跟随地图指引，踏上了冒险之旅。",
            "duration": 6.0,
            "character": "小明"
        }
    ]


def create_linear_version(manager: SceneVersionManager) -> str:
    """创建线性版本"""
    scenes = create_sample_scenes()
    
    return manager.save_scene_version(
        scenes,
        "创建初始线性版本",
        SnapshotType.LINEAR,
        {
            "description": "故事的初始线性版本",
            "tags": ["demo", "linear"]
        }
    )


def create_restructured_version(manager: SceneVersionManager, base_snapshot_id: str) -> str:
    """创建倒叙重构版本"""
    # 加载原始场景
    scenes = manager.load_scene_version(base_snapshot_id)
    if not scenes:
        raise ValueError("无法加载基础场景")
    
    # 重新排序场景（倒序）
    restructured_scenes = list(reversed(scenes))
    
    # 更新描述文本
    for scene in restructured_scenes:
        scene["text"] = f"【倒叙】{scene['text']}"
    
    return manager.save_scene_version(
        restructured_scenes,
        "创建倒序重构版本",
        SnapshotType.RESTRUCTURED,
        {
            "description": "故事的倒叙版本",
            "tags": ["demo", "restructured"],
            "base_version": base_snapshot_id
        }
    )


def create_experimental_version(manager: SceneVersionManager, base_snapshot_id: str) -> str:
    """创建多线实验版本"""
    # 加载原始场景
    scenes = manager.load_scene_version(base_snapshot_id)
    if not scenes:
        raise ValueError("无法加载基础场景")
    
    # 复制场景并修改
    experimental_scenes = scenes.copy()
    
    # 添加新角色和新场景
    experimental_scenes.append({
        "scene_id": "scene4",
        "text": "小红看到小明拿着地图，好奇地跟了上去。",
        "duration": 3.5,
        "character": "小红"
    })
    
    experimental_scenes.append({
        "scene_id": "scene5",
        "text": "小明和小红一起解开了地图的谜题，找到了宝藏。",
        "duration": 7.0,
        "characters": ["小明", "小红"]
    })
    
    return manager.save_scene_version(
        experimental_scenes,
        "创建多线实验版本",
        SnapshotType.EXPERIMENTAL,
        {
            "description": "添加多角色的实验版本",
            "tags": ["demo", "experimental"],
            "base_version": base_snapshot_id
        }
    )


def create_optimized_version(manager: SceneVersionManager, experimental_id: str) -> str:
    """创建最终优化版本"""
    # 加载实验版场景
    scenes = manager.load_scene_version(experimental_id)
    if not scenes:
        raise ValueError("无法加载实验版场景")
    
    # 优化场景
    optimized_scenes = scenes.copy()
    
    # 修改细节和优化描述
    for scene in optimized_scenes:
        # 优化文本描述
        text = scene.get("text", "")
        scene["text"] = text.replace("突然", "忽然").replace("决定", "选择").replace("神秘", "奇怪")
        
        # 延长关键场景时长
        if "宝藏" in text:
            scene["duration"] = scene.get("duration", 0) * 1.2
    
    # 添加最终场景
    optimized_scenes.append({
        "scene_id": "scene6",
        "text": "小明和小红带着宝藏回到了城市，成为了好朋友。",
        "duration": 5.0,
        "characters": ["小明", "小红"]
    })
    
    return manager.save_scene_version(
        optimized_scenes,
        "创建最终优化版本",
        SnapshotType.OPTIMIZED,
        {
            "description": "最终优化的完整故事版本",
            "tags": ["demo", "optimized", "final"],
            "base_version": experimental_id
        }
    )


def demo_version_management(temp_dir: str = "demo_snapshots"):
    """演示版本管理功能"""
    print("\n===== 多版本快照系统演示 =====\n")
    
    # 初始化版本管理器
    manager = SceneVersionManager("demo_project")
    
    try:
        # 1. 创建初始线性版本
        print("1. 创建初始线性版本...")
        linear_id = create_linear_version(manager)
        print(f"   - 已创建线性版本: {linear_id}")
        
        # 2. 创建倒叙重构版本
        print("\n2. 创建倒叙重构版本...")
        restructured_id = create_restructured_version(manager, linear_id)
        print(f"   - 已创建倒叙重构版本: {restructured_id}")
        
        # 3. 创建多线实验版本
        print("\n3. 创建多线实验版本...")
        experimental_id = create_experimental_version(manager, linear_id)
        print(f"   - 已创建多线实验版本: {experimental_id}")
        
        # 4. 创建最终优化版本
        print("\n4. 创建最终优化版本...")
        optimized_id = create_optimized_version(manager, experimental_id)
        print(f"   - 已创建最终优化版本: {optimized_id}")
        
        # 5. 列出所有版本
        print("\n5. 所有版本列表:")
        versions = manager.list_versions()
        for v in versions:
            print(f"   - {v['id']}: {v.get('operation')} ({v.get('type')})")
        
        # 6. 版本比较
        print("\n6. 比较线性版本和实验版本:")
        comparison = compare_snapshots(linear_id, experimental_id)
        if comparison:
            print(f"   - 线性版本场景数: {comparison['differences']['scene_count']['snapshot1']}")
            print(f"   - 实验版本场景数: {comparison['differences']['scene_count']['snapshot2']}")
            print(f"   - 场景数变化: {comparison['differences']['scene_count']['difference']}")
        
        # 7. 查看优化版本的历史路径
        print("\n7. 优化版本的历史路径:")
        history = manager.get_version_history(optimized_id)
        for item in history:
            print(f"   - {item['id']}: {item['metadata'].get('operation', 'N/A')}")
        
        # 8. 恢复一个版本并查看
        print("\n8. 恢复并查看实验版本内容:")
        scenes = manager.load_scene_version(experimental_id)
        if scenes:
            print(f"   - 成功加载 {len(scenes)} 个场景")
            for scene in scenes:
                print(f"     * {scene['scene_id']}: {scene['text']}")
        
        print("\n===== 演示完成 =====")
        
    except Exception as e:
        print(f"演示过程中出错: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            import shutil
            print(f"\n清理临时文件...")
            # shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="版本快照系统演示")
    parser.add_argument("--temp-dir", default="demo_snapshots", help="临时目录路径")
    parser.add_argument("--keep-files", action="store_true", help="保留临时文件")
    
    args = parser.parse_args()
    
    demo_version_management(args.temp_dir)


if __name__ == "__main__":
    main() 