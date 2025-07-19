#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键场景保护演示脚本

此脚本演示如何使用VisionAI-ClipsMaster的关键场景保护功能，
包括如何识别关键场景、应用保护策略以及在编辑和压缩过程中验证保护效果。
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any
from pathlib import Path
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("key_scene_protection_demo")

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 直接导入关键场景保护模块
try:
    from src.timecode.key_scene_protector import KeySceneGuard, ProtectionRule, ProtectionLevel, ProtectionStrategy
    from src.timecode.key_scene_protector import mark_protected_scenes, verify_scene_protection
except ImportError:
    logger.error("无法导入关键场景保护模块，请确保项目目录结构正确")
    sys.exit(1)


def print_separator(title: str = None):
    """打印分隔符"""
    width = 70
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")


def load_sample_scenes() -> List[Dict[str, Any]]:
    """加载示例场景数据"""
    return [
        {
            "id": "scene_1",
            "text": "电影开场，主角走在街道上，环顾四周。",
            "emotion_score": 0.3,
            "duration": 10.5,
            "tags": ["opening", "建立场景"],
            "compressible": True,
        },
        {
            "id": "scene_2",
            "text": "主角遇到神秘人物，接收到一个任务。",
            "emotion_score": 0.5,
            "duration": 15.2,
            "characters": ["主角", "神秘人"],
            "compressible": True,
        },
        {
            "id": "scene_3",
            "text": "主角发现关键线索，情绪激动。",
            "emotion_score": 0.85,  # 高情感分数
            "duration": 8.3,
            "characters": ["主角"],
            "compressible": True,
        },
        {
            "id": "scene_4",
            "text": "主角与反派第一次交锋，险些丧命。",
            "emotion_score": 0.7,
            "duration": 20.1,
            "characters": ["主角", "反派"],
            "tags": ["action", "对抗"],
            "compressible": True,
        },
        {
            "id": "scene_5",
            "text": "主角找到关键道具，增强能力。",
            "emotion_score": 0.4,
            "duration": 12.5,
            "characters": ["主角"],
            "compressible": True,
        },
        {
            "id": "scene_6",
            "text": "剧情高潮，主角与反派最终决战。",
            "emotion_score": 0.9,  # 高情感分数
            "duration": 25.0,
            "characters": ["主角", "反派"],
            "tags": ["climax", "决战"],  # 关键标签
            "compressible": True,
        },
        {
            "id": "scene_7",
            "text": "结局，世界恢复和平，主角获得认可。",
            "emotion_score": 0.75,
            "duration": 15.8,
            "characters": ["主角", "配角"],
            "tags": ["ending", "结局"],  # 关键标签
            "narrative_position": "resolution",
            "compressible": True,
        },
    ]


def demonstrate_scene_protection():
    """演示场景保护功能"""
    print_separator("1. 加载原始场景")
    scenes = load_sample_scenes()
    print(f"加载了 {len(scenes)} 个场景")
    
    for i, scene in enumerate(scenes[:3]):  # 只显示前3个场景作为示例
        print(f"\n场景 {i+1}/{len(scenes)}: {scene['id']}")
        print(f"  文本: {scene['text']}")
        print(f"  情感分数: {scene['emotion_score']}")
        print(f"  时长: {scene['duration']}秒")
        print(f"  可压缩: {scene['compressible']}")
    
    if len(scenes) > 3:
        print(f"\n... 还有 {len(scenes) - 3} 个场景 ...")
    
    print_separator("2. 应用关键场景保护")
    protector = KeySceneGuard({
        "emotion_threshold": 0.8,  # 设置情感阈值
        "critical_tags": ["climax", "高潮", "结局", "开场", "关键"],  # 设置关键标签
    })
    
    # 添加自定义规则
    protector.add_protection_rule(
        ProtectionRule(
            name="long_scene_rule",
            criteria=lambda scene: scene.get("duration", 0) > 20.0,  # 保护长场景
            level=ProtectionLevel.MEDIUM,
            strategies=[ProtectionStrategy.NO_TRIM],
            description="保护长场景(>20秒)"
        )
    )
    
    # 应用保护
    protected_scenes = protector.mark_protected(scenes)
    
    print("标记保护后的场景:")
    for i, scene in enumerate(protected_scenes):
        is_protected = scene.get("protected", False)
        protection_info = scene.get("metadata", {}).get("_protection_info", {}) if is_protected else {}
        
        print(f"\n场景 {scene['id']}:")
        print(f"  文本: {scene['text'][:40]}..." if len(scene['text']) > 40 else f"  文本: {scene['text']}")
        print(f"  受保护: {is_protected}")
        print(f"  可压缩: {scene.get('compressible', True)}")
        
        if is_protected:
            print(f"  保护级别: {protection_info.get('level', 'N/A')}")
            print(f"  保护策略: {', '.join(protection_info.get('strategies', []))}")
            print(f"  应用规则: {', '.join(protection_info.get('applied_rules', []))}")
    
    print_separator("3. 获取保护统计")
    stats = protector.get_protection_stats(protected_scenes)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    print_separator("4. 模拟场景编辑和验证")
    
    # 模拟编辑操作
    edited_scenes = []
    for scene in protected_scenes:
        scene_copy = scene.copy()
        
        # 尝试编辑场景
        if "text" in scene_copy:
            # 添加编辑标记
            if scene_copy.get("protected", False):
                scene_copy["text"] += " [尝试编辑保护场景]"
            else:
                scene_copy["text"] += " [已编辑]"
        
        # 尝试修改时长
        if "duration" in scene_copy and not scene_copy.get("protected", False):
            scene_copy["duration"] *= 0.7  # 缩短30%
        
        # 尝试修改压缩标志
        if scene_copy.get("protected", False) and not scene_copy.get("compressible", True):
            # 尝试将不可压缩改为可压缩
            scene_copy["compressible"] = True
        
        edited_scenes.append(scene_copy)
    
    print("已尝试编辑所有场景")
    
    # 验证保护状态
    verified_scenes = verify_scene_protection(edited_scenes)
    
    print("\n保护验证结果:")
    for scene in verified_scenes:
        if scene.get("protected", False):
            original_compressible = scene.get("compressible", True)
            print(f"场景 {scene['id']}:")
            print(f"  保护状态: {'已保护' if not original_compressible else '部分保护'}")
            
            # 检查是否有校验和
            metadata_key = protector.config["protection_metadata_key"]
            if "metadata" in scene and metadata_key in scene["metadata"]:
                protection_info = scene["metadata"][metadata_key]
                if "checksum" in protection_info:
                    print(f"  校验状态: {'已验证' if protection_info.get('checksum') else '未验证'}")
    
    print_separator("5. 示例应用场景")
    print("""
关键场景保护可以应用于以下场景:

1. 编辑审核 - 确保重要情节不被意外删除或修改
2. 压缩优化 - 在空间优化时保护高情感或关键情节场景
3. 自动剪辑 - 防止自动剪辑算法移除剧情关键点
4. 数据完整性 - 在协作编辑环境中保护关键内容
5. 质量保证 - 确保高价值内容在处理过程中保持高质量
    """)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="关键场景保护演示")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n===== VisionAI-ClipsMaster 关键场景保护演示 =====\n")
    print("此演示将展示如何使用关键场景保护功能来标记和保护重要场景，防止在编辑和压缩过程中被不当修改。")
    
    demonstrate_scene_protection()
    
    print("\n===== 演示完成 =====\n")


if __name__ == "__main__":
    main() 