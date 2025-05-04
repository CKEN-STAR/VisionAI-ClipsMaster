#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键场景保护测试脚本

测试关键场景保护机制的功能，包括场景标记、检验和校验功能。
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("key_scene_protection_test")

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入关键场景保护模块，不通过主模块导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 从timecode目录直接导入，避免加载其他依赖
from timecode.key_scene_protector import KeySceneGuard


def create_test_scenes() -> List[Dict[str, Any]]:
    """创建测试场景数据"""
    return [
        {
            "id": "scene_1",
            "text": "电影开场，主角走在街道上，环顾四周。",
            "emotion_score": 0.3,
            "duration": 10.5,
            "tags": ["opening", "建立场景"],
        },
        {
            "id": "scene_2",
            "text": "主角遇到神秘人物，接收到一个任务。",
            "emotion_score": 0.5,
            "duration": 15.2,
            "characters": ["主角", "神秘人"],
        },
        {
            "id": "scene_3",
            "text": "主角发现关键线索，情绪激动。",
            "emotion_score": 0.85,  # 高情感分数
            "duration": 8.3,
            "characters": ["主角"],
        },
        {
            "id": "scene_4",
            "text": "主角与反派第一次交锋，险些丧命。",
            "emotion_score": 0.7,
            "duration": 20.1,
            "characters": ["主角", "反派"],
            "tags": ["action", "对抗"],
        },
        {
            "id": "scene_5",
            "text": "主角找到关键道具，增强能力。",
            "emotion_score": 0.4,
            "duration": 12.5,
            "characters": ["主角"],
        },
        {
            "id": "scene_6",
            "text": "剧情高潮，主角与反派最终决战。",
            "emotion_score": 0.9,  # 高情感分数
            "duration": 25.0,
            "characters": ["主角", "反派"],
            "tags": ["climax", "决战"],  # 关键标签
        },
        {
            "id": "scene_7",
            "text": "结局，世界恢复和平，主角获得认可。",
            "emotion_score": 0.75,
            "duration": 15.8,
            "characters": ["主角", "配角"],
            "tags": ["ending", "结局"],  # 关键标签
            "narrative_position": "resolution",
        },
    ]


def test_scene_protection_marking():
    """测试场景保护标记功能"""
    logger.info("开始测试场景保护标记功能")
    
    # 创建测试场景
    scenes = create_test_scenes()
    logger.info(f"创建了 {len(scenes)} 个测试场景")
    
    # 创建保护器并标记场景
    protector = KeySceneGuard()
    protected_scenes = protector.mark_protected(scenes)
    
    # 统计受保护的场景
    protected_count = 0
    for scene in protected_scenes:
        if scene.get("protected", False):
            protected_count += 1
            logger.info(f"场景 {scene['id']} 被保护，理由: {scene.get('metadata', {}).get('_protection_info', {}).get('applied_rules', [])}")
    
    logger.info(f"共有 {protected_count} 个场景被标记为受保护")
    
    # 获取保护统计信息
    stats = protector.get_protection_stats(protected_scenes)
    logger.info(f"保护统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    return protected_scenes


def test_scene_protection_verification(protected_scenes: List[Dict[str, Any]]):
    """测试场景保护验证功能"""
    logger.info("开始测试场景保护验证功能")
    
    # 创建修改版本的场景
    modified_scenes = []
    for scene in protected_scenes:
        scene_copy = scene.copy()
        
        # 尝试修改受保护的场景
        if scene_copy.get("protected", False):
            # 修改文本
            if "text" in scene_copy:
                scene_copy["text"] += " [被修改]"
            
            # 修改时长
            if "duration" in scene_copy:
                scene_copy["duration"] *= 0.8
        
        modified_scenes.append(scene_copy)
    
    # 验证修改后的场景
    protector = KeySceneGuard()
    verified_scenes = protector.verify_protected_scenes(modified_scenes)
    
    # 检查校验和验证结果
    restored_count = 0
    for scene in verified_scenes:
        if scene.get("protected", False):
            metadata_key = protector.config["protection_metadata_key"]
            if "metadata" in scene and metadata_key in scene["metadata"]:
                if "checksum" in scene["metadata"][metadata_key]:
                    restored_count += 1
    
    logger.info(f"验证完成，检测到 {restored_count} 个受保护场景的修改")
    
    return verified_scenes


def main():
    """主测试函数"""
    logger.info("========== 关键场景保护测试 ==========")
    
    # 测试场景保护标记
    protected_scenes = test_scene_protection_marking()
    
    logger.info("\n")
    
    # 测试场景保护验证
    verified_scenes = test_scene_protection_verification(protected_scenes)
    
    logger.info("\n========== 测试完成 ==========")


if __name__ == "__main__":
    main() 