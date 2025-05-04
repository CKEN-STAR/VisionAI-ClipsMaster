#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TimelineArchiver独立测试脚本

这个脚本直接导入TimelineArchiver类，而不是通过src.timecode包导入，
避免了其他模块依赖问题。
"""

import os
import sys
import json
import time
import hashlib
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# 导入TimelineArchiver类代码
from version_archiver import TimelineArchiver

def run_basic_test():
    """运行基本功能测试"""
    print("=" * 80)
    print("TimelineArchiver基础功能测试")
    print("=" * 80)
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    print(f"测试目录: {test_dir}")
    
    try:
        # 初始化存档器
        project_id = f"test_project_{int(time.time())}"
        archiver = TimelineArchiver(project_id, test_dir)
        print(f"✓ 初始化项目: {project_id}")
        
        # 准备测试数据
        scenes = [
            {
                "id": "scene_001",
                "start_time": 10.5,
                "end_time": 20.0,
                "duration": 9.5,
                "text": "这是第一个测试场景",
                "emotion": "neutral"
            },
            {
                "id": "scene_002",
                "start_time": 30.5,
                "end_time": 45.2,
                "duration": 14.7,
                "text": "这是第二个测试场景",
                "emotion": "happy"
            }
        ]
        
        # 测试版本保存
        version1_id = archiver.save_version(scenes, "测试版本1")
        print(f"\n✓ 保存版本: {version1_id}")
        
        # 查看版本列表
        version_list = archiver.get_version_list()
        print(f"\n版本列表({len(version_list)}个):")
        print(f"{'版本ID':<15} {'时间':<22} {'场景数':<8} {'说明'}")
        print("-" * 80)
        for version in version_list:
            print(f"{version['version_id']:<15} {version['formatted_time']:<22} "
                  f"{version['scene_count']:<8} {version['note']}")
        
        # 测试加载版本
        loaded_scenes = archiver.load_version(version1_id)
        print("\n✓ 加载版本成功")
        print(f"加载的场景数量: {len(loaded_scenes)}")
        
        # 测试保存修改版本
        modified_scenes = scenes.copy()
        modified_scenes.append({
            "id": "scene_003",
            "start_time": 50.0,
            "end_time": 65.0,
            "duration": 15.0,
            "text": "这是新增的场景",
            "emotion": "excited"
        })
        
        version2_id = archiver.save_version(modified_scenes, "测试版本2-添加场景")
        print(f"\n✓ 保存修改版本: {version2_id}")
        
        # 比较两个版本
        comparison = archiver.compare_versions(version1_id, version2_id)
        print("\n版本比较结果:")
        print(f"版本1: {comparison['version1']['id']} - {comparison['version1']['scene_count']}个场景")
        print(f"版本2: {comparison['version2']['id']} - {comparison['version2']['scene_count']}个场景")
        print(f"场景数量变化: {comparison['scene_diff']:+d}")
        print(f"总时长变化: {comparison['total_duration_diff']:+.1f}秒")
        
        # 导出版本
        export_path = os.path.join(test_dir, "exported_version.json")
        archiver.export_version(version2_id, export_path)
        print(f"\n✓ 导出版本至: {export_path}")
        
        # 删除版本
        archiver.delete_version(version1_id)
        print(f"\n✓ 删除版本: {version1_id}")
        
        # 再次查看版本列表
        version_list = archiver.get_version_list()
        print(f"\n当前版本列表({len(version_list)}个):")
        for version in version_list:
            print(f"{version['version_id']} - {version['note']}")
        
        print("\n✅ 测试完成!")
    
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir)
        print(f"✓ 清理测试目录: {test_dir}")

if __name__ == "__main__":
    run_basic_test() 