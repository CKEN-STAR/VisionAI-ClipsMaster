#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
元叙事注释器演示脚本

演示如何使用元叙事注释器为场景添加结构角色和逻辑链标注
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import networkx as nx

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 导入必要的模块
from src.nonlinear.meta_annotator import (
    MetaAnnotator, StructuralRole, add_meta_comments,
    get_scene_structural_role, get_scene_connections, get_scene_logic_chain
)
from src.narrative.anchor_detector import detect_anchors
from src.narrative.anchor_types import AnchorInfo, AnchorType


# JSON序列化器，处理自定义类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, StructuralRole):
            return obj.value  # 将枚举转换为值
        if isinstance(obj, AnchorType):
            return obj.value  # 将枚举转换为值
        if hasattr(obj, '__dict__'):
            # 将对象转换为字典
            result = {}
            for key, val in obj.__dict__.items():
                if key.startswith('_'):
                    continue  # 跳过私有属性
                result[key] = val
            return result
        return super().default(obj)


def load_sample_scenes(story_type: str = "adventure") -> List[Dict[str, Any]]:
    """
    加载示例场景
    
    Args:
        story_type: 故事类型，可选值：adventure, romance, mystery
        
    Returns:
        场景列表
    """
    stories = {
        "adventure": [
            {
                "scene_id": "scene001",
                "text": "年轻冒险家李明站在峡谷边缘，远眺前方的神秘山洞。",
                "character": "李明",
                "duration": 5.0,
                "tags": ["开场"]
            },
            {
                "scene_id": "scene002",
                "text": "李明检查装备：地图、指南针、绳索和水壶，一切准备就绪。",
                "character": "李明",
                "duration": 4.0
            },
            {
                "scene_id": "scene003",
                "text": "当李明正要出发，一位当地向导王老出现，警告他山洞有危险。",
                "characters": ["李明", "王老"],
                "duration": 6.0
            },
            {
                "scene_id": "scene004",
                "text": "李明不顾警告，独自进入山洞，很快就被复杂的洞穴迷宫所困。",
                "character": "李明",
                "duration": 5.5,
                "tags": ["转折"]
            },
            {
                "scene_id": "scene005",
                "text": "黑暗中，李明听到奇怪的声音，突然遇到了另一位探险者张红。",
                "characters": ["李明", "张红"],
                "duration": 4.5
            },
            {
                "scene_id": "scene006",
                "text": "张红告诉李明她在寻找传说中的宝藏，并提出合作探索。",
                "characters": ["李明", "张红"],
                "duration": 5.0
            },
            {
                "scene_id": "scene007",
                "text": "他们一起深入洞穴，发现了古老的壁画，描绘着宝藏的线索。",
                "characters": ["李明", "张红"],
                "duration": 6.5
            },
            {
                "scene_id": "scene008",
                "text": "根据壁画提示，他们解开谜题，找到了通往宝藏室的暗门。",
                "characters": ["李明", "张红"],
                "duration": 7.0
            },
            {
                "scene_id": "scene009",
                "text": "宝藏室中央是一座金佛像，但随着他们靠近，整个洞穴开始震动。",
                "characters": ["李明", "张红"],
                "duration": 8.0,
                "tags": ["高潮"]
            },
            {
                "scene_id": "scene010",
                "text": "洞穴开始坍塌，李明和张红拿起金佛像，拼命向出口奔跑。",
                "characters": ["李明", "张红"],
                "duration": 9.0
            },
            {
                "scene_id": "scene011",
                "text": "千钧一发之际，王老出现在洞口，帮助他们逃出生天。",
                "characters": ["李明", "张红", "王老"],
                "duration": 7.5
            },
            {
                "scene_id": "scene012",
                "text": "三人在安全地带，分享了宝藏，承诺再一起开启下一段冒险。",
                "characters": ["李明", "张红", "王老"],
                "duration": 6.0,
                "tags": ["结局"]
            }
        ],
        "romance": [
            {
                "scene_id": "scene001",
                "text": "陈远在咖啡馆里专注地工作，丝毫没注意到窗外的雨已经下得很大。",
                "character": "陈远",
                "duration": 4.5,
                "tags": ["开场"]
            },
            {
                "scene_id": "scene002",
                "text": "林小雨匆忙冲进咖啡馆避雨，不小心撞到了陈远的桌子，打翻了他的咖啡。",
                "characters": ["陈远", "林小雨"],
                "duration": 5.0
            },
            {
                "scene_id": "scene003",
                "text": "在一片慌乱中，陈远帮林小雨擦干了被溅到的衣服，两人相视一笑。",
                "characters": ["陈远", "林小雨"],
                "duration": 4.0
            }
            # ... 更多场景
        ],
        "mystery": [
            {
                "scene_id": "scene001",
                "text": "侦探王亮接到电话，被告知城郊别墅发生了一起离奇的密室谋杀案。",
                "character": "王亮",
                "duration": 5.5,
                "tags": ["开场"]
            },
            {
                "scene_id": "scene002",
                "text": "王亮到达现场，发现死者是富商陈志明，房间内部的门窗全部锁死。",
                "characters": ["王亮", "陈志明"],
                "duration": 6.0
            },
            {
                "scene_id": "scene003",
                "text": "法医确认死亡时间是昨晚9点左右，死因是毒药，而非现场看到的外伤。",
                "characters": ["王亮", "法医"],
                "duration": 4.5
            }
            # ... 更多场景
        ]
    }
    
    return stories.get(story_type, stories["adventure"])


def visualize_scene_structure(scenes: List[Dict[str, Any]], title: str = "场景结构图") -> None:
    """
    可视化场景结构
    
    Args:
        scenes: 场景列表
        title: 图表标题
    """
    if not scenes:
        print("没有场景可以可视化")
        return
    
    # 创建有向图
    G = nx.DiGraph()
    
    # 添加节点
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        role = scene.get("meta", {}).get("role_description", "未知")
        G.add_node(scene_id, role=role)
    
    # 添加边
    for scene in scenes:
        scene_id = scene.get("scene_id", "")
        connections = scene.get("meta", {}).get("connect_to", [])
        
        for conn in connections:
            G.add_edge(scene_id, conn, weight=1.0)
    
    # 绘图
    plt.figure(figsize=(12, 8))
    
    # 定义节点位置（使用圆形布局）
    pos = nx.spring_layout(G, seed=42)
    
    # 为不同角色的节点使用不同颜色
    role_colors = {
        "悬念铺垫": "#1f77b4",
        "背景设定": "#ff7f0e",
        "触发事件": "#2ca02c",
        "情节发展": "#d62728",
        "中点转折": "#9467bd",
        "情节复杂化": "#8c564b",
        "危机紧张": "#e377c2",
        "情节高潮": "#7f7f7f",
        "问题解决": "#bcbd22",
        "事件余波": "#17becf",
        "故事尾声": "#aec7e8"
    }
    
    # 为未知角色设置默认颜色
    default_color = "#cccccc"
    
    # 获取节点角色和颜色
    node_colors = []
    for node in G.nodes():
        role = G.nodes[node].get("role", "未知")
        node_colors.append(role_colors.get(role, default_color))
    
    # 绘制节点
    nx.draw_networkx_nodes(G, pos, 
                         node_size=500, 
                         node_color=node_colors, 
                         alpha=0.8)
    
    # 绘制边
    nx.draw_networkx_edges(G, pos, 
                         width=1.5, 
                         alpha=0.6, 
                         edge_color='gray',
                         arrows=True,
                         arrowsize=15)
    
    # 绘制节点标签
    node_labels = {}
    for node in G.nodes():
        if isinstance(node, str) and node.startswith("scene"):
            # 对于scene_id格式的，提取数字部分
            label = node.replace("scene", "场景")
        else:
            label = str(node)
        node_labels[node] = label
        
    nx.draw_networkx_labels(G, pos, 
                          labels=node_labels, 
                          font_size=10, 
                          font_family='SimHei')
    
    # 图例
    legend_elements = []
    for role, color in role_colors.items():
        from matplotlib.lines import Line2D
        legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                    label=role, markerfacecolor=color, markersize=10))
    
    plt.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # 设置标题和布局
    plt.title(title, fontsize=16, fontweight='bold', fontfamily='SimHei')
    plt.axis('off')
    
    # 保存图表
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, "scene_structure.png")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"场景结构图已保存至: {output_file}")
    plt.close()


def print_meta_info(scenes: List[Dict[str, Any]], max_scenes: Optional[int] = None) -> None:
    """
    打印场景元信息
    
    Args:
        scenes: 场景列表
        max_scenes: 最大显示场景数
    """
    if not scenes:
        print("没有场景可以显示")
        return
    
    if max_scenes is None:
        max_scenes = len(scenes)
    else:
        max_scenes = min(max_scenes, len(scenes))
    
    print("\n==== 场景元叙事注释 ====")
    
    for i in range(max_scenes):
        scene = scenes[i]
        scene_id = scene.get("scene_id", f"scene{i+1}")
        
        print(f"\n场景 {i+1} ({scene_id}):")
        print(f"内容: {scene.get('text', '')}")
        
        # 显示元数据注释
        if "meta" in scene:
            meta = scene["meta"]
            
            # 结构角色
            if "structural_role" in meta:
                role = meta["structural_role"]
                description = meta.get("role_description", "")
                print(f"结构角色: {role} ({description})")
            
            # 关联场景
            if "connect_to" in meta:
                connects = meta["connect_to"]
                if connects:
                    print(f"关联场景: {', '.join(connects)}")
                else:
                    print("关联场景: 无")
            
            # 逻辑链
            if "logic_chain" in meta:
                print(f"逻辑链: {meta['logic_chain']}")
        
        print("-" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='元叙事注释器演示')
    parser.add_argument('--type', '-t', choices=['adventure', 'romance', 'mystery'], 
                      default='adventure', help='故事类型')
    parser.add_argument('--visualize', '-v', action='store_true', 
                      help='可视化场景结构')
    parser.add_argument('--max', '-m', type=int, default=None,
                      help='显示的最大场景数')
    parser.add_argument('--save', '-s', action='store_true',
                      help='保存注释结果到JSON文件')
    
    args = parser.parse_args()
    
    print(f"===== 元叙事注释器演示 - {args.type}类型故事 =====")
    
    # 加载示例场景
    scenes = load_sample_scenes(args.type)
    print(f"加载了 {len(scenes)} 个场景")
    
    # 检测叙事锚点
    try:
        anchors = detect_anchors(scenes)
        print(f"检测到 {len(anchors)} 个叙事锚点")
    except Exception as e:
        print(f"锚点检测失败: {e}")
        anchors = None
    
    # 应用元叙事注释
    annotated_scenes = add_meta_comments(scenes, anchors)
    print("已添加元叙事注释")
    
    # 打印元信息
    print_meta_info(annotated_scenes, args.max)
    
    # 可视化场景结构
    if args.visualize:
        try:
            visualize_scene_structure(annotated_scenes, f"{args.type.capitalize()}故事场景结构")
        except Exception as e:
            print(f"可视化失败: {e}")
    
    # 保存结果
    if args.save:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f"meta_annotated_{args.type}.json")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(annotated_scenes, f, ensure_ascii=False, indent=2, cls=CustomJSONEncoder)
            print(f"注释结果已保存至: {output_file}")
        except Exception as e:
            print(f"保存结果失败: {e}")


if __name__ == "__main__":
    main() 