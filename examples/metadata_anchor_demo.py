#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
元数据锚点系统演示

演示如何使用元数据锚点系统管理剧本的多个版本，
包括指纹标记、锚点创建和版本关系追踪。
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import shutil

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入元数据锚点系统
from src.versioning.metadata_anchor import (
    VersionAnnotator, 
    AnchorManager,
    get_version_annotator,
    get_anchor_manager
)

# 导入多策略生成引擎
from src.versioning.generation_engine import (
    MultiStrategyEngine,
    run_multi_strategy
)

# 导入多样性管理器
from src.versioning.diversity_manager import DiversityManager

# 导入快照管理器
from src.versioning.snapshot_manager import Snapshotter, SnapshotType

# 示例数据目录
DEMO_DATA_DIR = os.path.join(project_root, "output", "metadata_anchor_demo")

def create_demo_subtitles():
    """创建演示用的字幕数据"""
    return [
        {
            "start_time": 0.0,
            "end_time": 3.5,
            "text": "今天我们要讨论一个有趣的话题"
        },
        {
            "start_time": 3.6,
            "end_time": 7.2,
            "text": "关于如何使用元数据锚点系统管理剧本版本"
        },
        {
            "start_time": 7.3,
            "end_time": 12.0,
            "text": "这个系统可以帮助我们跟踪不同版本之间的关系"
        },
        {
            "start_time": 12.1,
            "end_time": 16.5,
            "text": "并标记重要的里程碑和关键点"
        },
        {
            "start_time": 16.6,
            "end_time": 22.0,
            "text": "让我们看看如何将它与多策略生成引擎结合使用"
        },
        {
            "start_time": 22.1,
            "end_time": 28.0,
            "text": "首先，我们会生成几个不同版本的剧本"
        },
        {
            "start_time": 28.1,
            "end_time": 33.5,
            "text": "然后使用元数据系统标记它们之间的关系"
        },
        {
            "start_time": 33.6,
            "end_time": 38.0,
            "text": "最后，我们将展示如何查询和分析这些版本"
        }
    ]

def setup_demo_environment():
    """设置演示环境"""
    # 清理现有演示目录
    if os.path.exists(DEMO_DATA_DIR):
        shutil.rmtree(DEMO_DATA_DIR)
    
    # 创建演示目录
    os.makedirs(DEMO_DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DEMO_DATA_DIR, "snapshots"), exist_ok=True)
    os.makedirs(os.path.join(DEMO_DATA_DIR, "metadata"), exist_ok=True)
    
    return {
        "snapshotter": Snapshotter(storage_dir=os.path.join(DEMO_DATA_DIR, "snapshots")),
        "annotator": VersionAnnotator(
            snapshotter=Snapshotter(storage_dir=os.path.join(DEMO_DATA_DIR, "snapshots")),
            metadata_dir=os.path.join(DEMO_DATA_DIR, "metadata")
        )
    }

def generate_version_variations(base_subtitles):
    """使用多策略生成引擎生成多个剧本版本变体"""
    print("\n=== 1. 使用多策略生成引擎创建不同版本 ===")
    
    # 初始化多策略引擎
    engine = MultiStrategyEngine()
    
    # 生成多个版本
    strategies = ["倒叙重构", "多线交织", "情感强化", "简约风格"]
    
    print(f"使用策略: {', '.join(strategies)}")
    versions = engine.generate(
        base_subtitles, 
        strategy_names=strategies,
        base_params={"pace": 1.0, "emotion_intensity": 0.7}
    )
    
    print(f"生成了 {len(versions)} 个不同版本")
    return versions

def annotate_versions(versions, demo_env):
    """为生成的版本添加元数据注解"""
    print("\n=== 2. 为生成的版本添加元数据注解 ===")
    
    annotator = demo_env["annotator"]
    anchor_manager = AnchorManager(
        snapshotter=demo_env["snapshotter"],
        annotator=annotator
    )
    
    # 创建基础版本
    base_id = annotator.annotate_version(
        {"subtitles": create_demo_subtitles()},
        {
            "description": "原始字幕版本",
            "type": "base",
            "created_at": datetime.now().isoformat()
        },
        version_id="base_version"
    )
    
    print(f"创建基础版本: {base_id}")
    
    # 标记基础版本为里程碑
    milestone_id = anchor_manager.create_milestone(
        {"subtitles": create_demo_subtitles()},
        "基础版本里程碑",
        "这是演示的起点",
        ["base", "milestone", "demo"]
    )
    
    print(f"创建基础里程碑: {milestone_id}")
    
    # 为每个生成的版本添加注解
    version_ids = []
    for i, version in enumerate(versions):
        # 获取策略名称
        strategy_name = version.get("strategy_name", f"策略{i+1}")
        
        # 添加元数据注解
        metadata = {
            "strategy": strategy_name,
            "parent_version": base_id,
            "generation_params": version.get("params", {}),
            "created_at": datetime.now().isoformat(),
            "version_number": i+1
        }
        
        # 注解版本
        version_id = annotator.annotate_version(version, metadata)
        version_ids.append(version_id)
        
        print(f"注解版本 {i+1} ({strategy_name}): {version_id}")
    
    return {
        "base_id": base_id,
        "milestone_id": milestone_id,
        "version_ids": version_ids
    }

def create_version_relationships(versions_info, demo_env):
    """创建版本间的关系"""
    print("\n=== 3. 创建版本间的关系 ===")
    
    annotator = demo_env["annotator"]
    anchor_manager = AnchorManager(
        snapshotter=demo_env["snapshotter"],
        annotator=annotator
    )
    
    # 标记某个版本为特别重要的
    if versions_info["version_ids"]:
        best_version_id = versions_info["version_ids"][0]
        
        # 标记为关键版本
        critical_id = anchor_manager.mark_critical_version(
            annotator._get_version_metadata(best_version_id),
            importance=9,
            reason="这是经过评估后最佳的版本"
        )
        
        print(f"标记关键版本: {critical_id}")
        
        # 创建改进版本
        improved_version = annotator._get_version_metadata(best_version_id).copy()
        
        # 添加一些额外修改标记
        improved_version["modified_at"] = datetime.now().isoformat()
        improved_version["modifications"] = ["调整字幕时间", "修正标点符号", "优化情感表达"]
        
        # 注解为子版本
        child_id = annotator.annotate_version(
            improved_version,
            {
                "parent_version": best_version_id,
                "description": "基于最佳版本的改进版",
                "version_type": "refined",
                "created_at": datetime.now().isoformat()
            }
        )
        
        print(f"创建改进版本: {child_id}")
        
        # 创建参考点
        reference_id = anchor_manager.create_reference_point(
            annotator._get_version_metadata(child_id),
            "refined_reference",
            {
                "description": "精细调整参考点",
                "refinement_level": "high",
                "notes": "这个版本可以作为未来改进的参考"
            }
        )
        
        print(f"创建参考点: {reference_id}")
        
        # 添加到返回信息
        versions_info["critical_id"] = critical_id
        versions_info["child_id"] = child_id
        versions_info["reference_id"] = reference_id
    
    return versions_info

def query_version_relationships(versions_info, demo_env):
    """查询版本间的关系"""
    print("\n=== 4. 查询版本间的关系 ===")
    
    annotator = demo_env["annotator"]
    anchor_manager = AnchorManager(
        snapshotter=demo_env["snapshotter"],
        annotator=annotator
    )
    
    # 列出所有里程碑
    milestones = anchor_manager.list_milestones()
    print(f"找到 {len(milestones)} 个里程碑")
    
    # 列出所有关键版本
    criticals = anchor_manager.list_critical_versions()
    print(f"找到 {len(criticals)} 个关键版本")
    
    # 查询版本继承关系
    if "child_id" in versions_info:
        ancestry = annotator.find_version_ancestry(versions_info["child_id"])
        print(f"版本 {versions_info['child_id']} 的祖先链:")
        
        for i, ancestor in enumerate(ancestry):
            print(f"  {i+1}. {ancestor['id']} - {ancestor['metadata'].get('description', 'N/A')}")
    
    # 构建关系图
    version_ids = [
        versions_info.get("base_id", ""),
        versions_info.get("milestone_id", ""),
    ]
    
    if "version_ids" in versions_info:
        version_ids.extend(versions_info["version_ids"])
    
    if "child_id" in versions_info:
        version_ids.append(versions_info["child_id"])
    
    # 只保留有效的ID
    version_ids = [vid for vid in version_ids if vid]
    
    graph = anchor_manager.build_ancestry_graph(version_ids)
    print(f"版本关系图: {len(graph['nodes'])} 个节点, {len(graph['edges'])} 条边")
    
    # 保存关系图到文件
    graph_path = os.path.join(DEMO_DATA_DIR, "version_graph.json")
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
        
    print(f"版本关系图已保存到: {graph_path}")

def compare_version_metadata(versions_info, demo_env):
    """比较不同版本的元数据"""
    print("\n=== 5. 比较版本元数据 ===")
    
    annotator = demo_env["annotator"]
    
    # 选择两个版本进行比较
    version_ids = versions_info.get("version_ids", [])
    
    if len(version_ids) >= 2:
        version_id1 = version_ids[0]
        version_id2 = version_ids[1]
        
        # 比较元数据
        comparison = annotator.compare_version_metadata(version_id1, version_id2)
        
        print(f"比较版本 {version_id1} 和 {version_id2}:")
        print(f"  共同键: {len(comparison['common_keys'])} 个")
        print(f"  仅在版本1中: {len(comparison['only_in_version1'])} 个特有键")
        print(f"  仅在版本2中: {len(comparison['only_in_version2'])} 个特有键")
        print(f"  有差异的键: {len(comparison['differences'])} 个")
        
        # 保存比较结果到文件
        comparison_path = os.path.join(DEMO_DATA_DIR, "version_comparison.json")
        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
            
        print(f"版本比较结果已保存到: {comparison_path}")

def search_similar_versions(versions_info, demo_env):
    """搜索相似版本"""
    print("\n=== 6. 搜索相似版本 ===")
    
    annotator = demo_env["annotator"]
    anchor_manager = AnchorManager(
        snapshotter=demo_env["snapshotter"],
        annotator=annotator
    )
    
    # 获取原始版本
    base_version = annotator._get_version_metadata(versions_info["base_id"])
    
    if base_version:
        # 搜索相似版本
        similars = anchor_manager.find_similar_versions(base_version, threshold=0.7)
        
        print(f"找到 {len(similars)} 个与基础版本相似的版本")
        
        # 如果找到相似版本，打印详情
        if similars:
            print("相似版本详情:")
            for i, similar in enumerate(similars):
                anchor = similar.get("anchor", {})
                anchor_type = anchor.get("type", "unknown")
                created_at = anchor.get("created_at", "unknown")
                print(f"  {i+1}. 类型: {anchor_type}, 创建时间: {created_at}")

def run_full_demo():
    """运行完整演示"""
    print("=== 元数据锚点系统演示 ===\n")
    
    # 确保演示目录存在
    os.makedirs(os.path.dirname(DEMO_DATA_DIR), exist_ok=True)
    
    # 设置演示环境
    demo_env = setup_demo_environment()
    
    # 创建基础字幕
    base_subtitles = create_demo_subtitles()
    
    # 1. 生成版本变体
    versions = generate_version_variations(base_subtitles)
    
    # 2. 注解版本
    versions_info = annotate_versions(versions, demo_env)
    
    # 3. 创建版本关系
    versions_info = create_version_relationships(versions_info, demo_env)
    
    # 4. 查询版本关系
    query_version_relationships(versions_info, demo_env)
    
    # 5. 比较版本元数据
    compare_version_metadata(versions_info, demo_env)
    
    # 6. 搜索相似版本
    search_similar_versions(versions_info, demo_env)
    
    print("\n演示完成! 结果保存在:", DEMO_DATA_DIR)

if __name__ == "__main__":
    run_full_demo() 