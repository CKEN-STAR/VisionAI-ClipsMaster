#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
道具线索追踪系统示例

演示如何使用道具追踪功能检测视频中的道具使用一致性问题。
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.logic import PropTracker, track_props


def main():
    """主函数，演示道具追踪功能"""
    print("===== 道具线索追踪系统示例 =====")
    
    # 创建测试场景数据
    scenes = [
        {
            "id": "scene1",
            "character": "张三",
            "location": "家中",
            "start": 0,
            "end": 15000,
            "text": "张三从抽屉里拿出一把钥匙和手机，准备出门。",
            "props": [
                {"name": "钥匙", "origin": "抽屉", "status": "obtained"},
                {"name": "手机", "origin": "抽屉", "status": "obtained"}
            ],
            "tags": ["origin"]
        },
        {
            "id": "scene2",
            "character": "张三",
            "location": "街道",
            "start": 15500,
            "end": 30000,
            "text": "张三走在街上，拿着手机看地图。",
            "props": ["手机", "钥匙"]
        },
        {
            "id": "scene3",
            "character": "李四",
            "location": "咖啡店",
            "start": 30500,
            "end": 45000,
            "text": "李四坐在咖啡店里，手里拿着一本书在等人。",
            "props": [{"name": "书", "origin": "从包里拿出"}]
        },
        {
            "id": "scene4",
            "character": "张三",
            "location": "咖啡店",
            "start": 45500,
            "end": 60000,
            "text": "张三进入咖啡店，看到李四并走向他。",
            "props": ["手机"]  # 钥匙丢失了
        },
        {
            "id": "scene5",
            "character": "李四",
            "location": "咖啡店",
            "start": 60500,
            "end": 75000,
            "text": "李四看到地上有一把钥匙，捡起来问张三是不是他的。",
            "props": ["书", {"name": "钥匙", "status": "found"}]
        },
        {
            "id": "scene6",
            "character": "张三",
            "location": "咖啡店",
            "start": 75500,
            "end": 90000,
            "text": "张三确认是自己的钥匙，感谢李四。",
            "props": ["手机", {"name": "钥匙", "status": "obtained"}]
        }
    ]
    
    # 使用道具追踪器
    print("\n1. 使用PropTracker类进行详细追踪")
    tracker = PropTracker()
    issues = tracker.track_prop_usage(scenes)
    
    # 输出问题
    if issues:
        print(f"\n发现 {len(issues)} 个道具使用问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  问题 {i}: {issue['message']}")
    else:
        print("\n没有发现道具使用问题。")
    
    # 输出角色持有的道具
    characters = set(scene.get("character") for scene in scenes if "character" in scene)
    print("\n各角色当前持有的道具:")
    for character in characters:
        props = tracker.get_character_props(character)
        print(f"  {character}: {', '.join(props) if props else '无'}")
    
    # 使用便捷函数
    print("\n2. 使用track_props便捷函数获取完整分析")
    result = track_props(scenes)
    
    # 输出统计信息
    stats = result["statistics"]
    print(f"\n道具统计信息:")
    print(f"  总道具数: {stats['total_props']}")
    print(f"  有问题的道具数: {stats['props_with_issues']}")
    
    # 输出道具详情
    print("\n道具详细信息:")
    for prop_name, details in stats["prop_details"].items():
        print(f"  {prop_name}:")
        print(f"    出现次数: {details['appearances']}")
        print(f"    来源: {details['origin']}")
        print(f"    最后状态: {details['last_status']}")
        print(f"    相关角色: {', '.join(set(details['characters']))}")
    
    # 输出钥匙的完整时间线
    print("\n钥匙的时间线:")
    key_timeline = tracker.get_prop_timeline("钥匙")
    for i, record in enumerate(key_timeline, 1):
        print(f"  {i}. 场景 {record['scene_id']} - " 
              f"状态: {record['status']}, " 
              f"角色: {record['character'] if record['character'] else '无'}")


if __name__ == "__main__":
    main() 