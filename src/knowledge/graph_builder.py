#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识图谱构建模块

根据剧本内容构建知识图谱，用于角色关系分析、事件关联和逻辑矛盾检测等。
支持实体提取、关系推断和图谱可视化功能。
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple

# 获取日志记录器
logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """知识图谱类，用于存储和分析剧本中的实体和关系"""
    
    def __init__(self):
        """初始化知识图谱"""
        # 实体字典：名称 -> 属性
        self.entities = {}
        
        # 关系列表：(源实体, 关系类型, 目标实体, 属性)
        self.relations = []
        
        # 事件列表
        self.events = []
        
        # 角色出现次数
        self.character_occurrences = {}
        
        logger.info("初始化知识图谱")
    
    def add_entity(self, name: str, entity_type: str, attributes: Dict[str, Any] = None) -> None:
        """
        添加实体
        
        Args:
            name: 实体名称
            entity_type: 实体类型（人物、地点、物品等）
            attributes: 实体属性
        """
        if attributes is None:
            attributes = {}
            
        self.entities[name] = {
            "type": entity_type,
            "attributes": attributes
        }
    
    def add_relation(self, source: str, relation_type: str, target: str, 
                    attributes: Dict[str, Any] = None) -> None:
        """
        添加关系
        
        Args:
            source: 源实体名称
            relation_type: 关系类型
            target: 目标实体名称
            attributes: 关系属性
        """
        if attributes is None:
            attributes = {}
            
        self.relations.append((source, relation_type, target, attributes))
    
    def add_event(self, event_type: str, participants: List[str], 
                 scene_idx: int, description: str) -> None:
        """
        添加事件
        
        Args:
            event_type: 事件类型
            participants: 参与者列表
            scene_idx: 场景索引
            description: 事件描述
        """
        self.events.append({
            "type": event_type,
            "participants": participants,
            "scene_idx": scene_idx,
            "description": description
        })
    
    def get_character_importance(self) -> Dict[str, float]:
        """
        获取角色重要性评分
        
        Returns:
            角色名称到重要性评分的映射
        """
        # 根据出现次数和关系数量计算重要性
        importance = {}
        
        # 出现次数因素
        total_occurrences = sum(self.character_occurrences.values()) or 1
        for character, count in self.character_occurrences.items():
            importance[character] = count / total_occurrences
        
        # 关系因素
        character_relations = {}
        for source, _, target, _ in self.relations:
            character_relations[source] = character_relations.get(source, 0) + 1
            character_relations[target] = character_relations.get(target, 0) + 1
        
        # 合并评分
        for character, rel_count in character_relations.items():
            if character in importance:
                # 出现频率和关系数量各占50%权重
                importance[character] = 0.5 * importance[character] + 0.5 * (rel_count / (len(self.relations) or 1))
        
        return importance
    
    def get_events(self) -> List[Dict[str, Any]]:
        """
        获取事件列表
        
        Returns:
            事件列表
        """
        return self.events
    
    def find_contradictions(self) -> List[Dict[str, Any]]:
        """
        检测知识图谱中的逻辑矛盾
        
        Returns:
            矛盾列表，每个矛盾包含位置和描述
        """
        contradictions = []
        
        # 检查属性矛盾
        attribute_values = {}
        
        # 收集所有实体的属性值
        for entity, details in self.entities.items():
            for attr, value in details.get("attributes", {}).items():
                key = (entity, attr)
                if key in attribute_values and attribute_values[key] != value:
                    contradictions.append({
                        "type": "attribute_contradiction",
                        "entity": entity,
                        "attribute": attr,
                        "values": [attribute_values[key], value],
                        "description": f"实体 '{entity}' 的属性 '{attr}' 有矛盾值: {attribute_values[key]} 和 {value}",
                        "position": 0  # 由于无法确定位置，设为0
                    })
                attribute_values[key] = value
        
        # 检查关系矛盾
        relation_exclusions = {
            # 互斥关系类型列表
            ("爱", "恨"),
            ("信任", "怀疑"),
            ("朋友", "敌人")
        }
        
        # 收集所有实体对之间的关系
        entity_relations = {}
        for source, rel_type, target, attrs in self.relations:
            key = tuple(sorted([source, target]))
            if key not in entity_relations:
                entity_relations[key] = []
            entity_relations[key].append(rel_type)
        
        # 检查互斥关系
        for (entity1, entity2), rel_types in entity_relations.items():
            for rel_type1, rel_type2 in relation_exclusions:
                if rel_type1 in rel_types and rel_type2 in rel_types:
                    # 找出关系发生的场景位置
                    position = 0
                    for event in self.events:
                        if entity1 in event["participants"] and entity2 in event["participants"]:
                            position = event["scene_idx"]
                            break
                    
                    contradictions.append({
                        "type": "relation_contradiction",
                        "entities": [entity1, entity2],
                        "relations": [rel_type1, rel_type2],
                        "description": f"实体 '{entity1}' 和 '{entity2}' 之间存在矛盾关系: '{rel_type1}' 和 '{rel_type2}'",
                        "position": position
                    })
        
        return contradictions
    
    def visualize(self, output_path: Optional[str] = None) -> None:
        """
        可视化知识图谱
        
        Args:
            output_path: 输出文件路径，如果为None则显示图形
        """
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            
            # 创建有向图
            G = nx.DiGraph()
            
            # 添加节点
            for entity, details in self.entities.items():
                G.add_node(entity, type=details["type"])
            
            # 添加边
            for source, rel_type, target, _ in self.relations:
                G.add_edge(source, target, type=rel_type)
            
            # 设置节点颜色
            node_colors = []
            for node in G.nodes():
                if G.nodes[node].get("type") == "character":
                    node_colors.append("skyblue")
                elif G.nodes[node].get("type") == "location":
                    node_colors.append("lightgreen")
                else:
                    node_colors.append("lightgray")
            
            # 绘制图形
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G)
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500)
            nx.draw_networkx_labels(G, pos, font_size=10)
            nx.draw_networkx_edges(G, pos, arrowsize=15, width=1.5)
            
            # 绘制边标签
            edge_labels = {(source, target): rel_type for source, rel_type, target, _ in self.relations}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
            
            plt.title("剧本知识图谱")
            plt.axis('off')
            
            if output_path:
                plt.savefig(output_path)
                logger.info(f"知识图谱已保存到 {output_path}")
            else:
                plt.show()
                
        except ImportError:
            logger.warning("无法可视化知识图谱，缺少networkx或matplotlib库")


def build_knowledge_graph(script: List[Dict[str, Any]]) -> KnowledgeGraph:
    """
    从脚本构建知识图谱
    
    Args:
        script: 剧本场景列表
        
    Returns:
        构建的知识图谱
    """
    graph = KnowledgeGraph()
    
    # 提取角色、地点和物品
    characters = set()
    locations = set()
    items = set()
    
    # 正则表达式模式
    character_pattern = r'([A-Z一-龥]{2,})[:：]'
    location_pattern = r'在([\u4e00-\u9fa5]{2,}[厅|室|区|地|店|场|家|园|馆])'
    item_pattern = r'([一个|一只|一把|一件][^\s,，.。:：]{1,5})'
    
    # 分析每个场景
    for i, scene in enumerate(script):
        text = scene.get('text', '')
        
        # 提取角色
        found_characters = re.findall(character_pattern, text)
        characters.update(found_characters)
        
        # 更新角色出现次数
        for character in found_characters:
            graph.character_occurrences[character] = graph.character_occurrences.get(character, 0) + 1
        
        # 提取地点
        found_locations = re.findall(location_pattern, text)
        locations.update(found_locations)
        
        # 提取物品
        found_items = re.findall(item_pattern, text)
        items.update(found_items)
        
        # 从标签中提取信息
        tags = scene.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        # 处理场景中的事件
        event_type = "unknown"
        for tag in tags:
            if tag in ["冲突", "争吵", "打斗"]:
                event_type = "conflict"
            elif tag in ["相遇", "会面"]:
                event_type = "meeting"
            elif tag in ["表白", "告白", "求婚"]:
                event_type = "confession"
            elif tag in ["发现", "揭露"]:
                event_type = "revelation"
            elif tag in ["决定", "选择"]:
                event_type = "decision"
        
        # 添加事件
        if found_characters and event_type != "unknown":
            graph.add_event(event_type, found_characters, i, text[:50] + "...")
    
    # 添加实体
    for character in characters:
        graph.add_entity(character, "character")
    
    for location in locations:
        graph.add_entity(location, "location")
    
    for item in items:
        graph.add_entity(item, "item")
    
    # 推断角色之间的关系
    for i, scene in enumerate(script):
        text = scene.get('text', '')
        
        # 寻找当前场景中出现的角色
        scene_characters = []
        for character in characters:
            if character in text:
                scene_characters.append(character)
        
        # 如果场景中有多个角色，添加它们之间的可能关系
        if len(scene_characters) >= 2:
            # 分析情感
            sentiment = scene.get('sentiment', {}).get('label', 'NEUTRAL')
            intensity = scene.get('sentiment', {}).get('intensity', 0.5)
            
            # 根据情感推断关系
            relation_type = "相识"  # 默认关系
            if sentiment == "POSITIVE":
                relation_type = "友好" if intensity < 0.7 else "亲密"
            elif sentiment == "NEGATIVE":
                relation_type = "紧张" if intensity < 0.7 else "敌对"
            
            # 添加角色之间的关系
            for j, char1 in enumerate(scene_characters):
                for char2 in scene_characters[j+1:]:
                    graph.add_relation(char1, relation_type, char2, {"scene_idx": i})
    
    logger.info(f"知识图谱构建完成，包含 {len(characters)} 个角色，{len(graph.relations)} 个关系，{len(graph.events)} 个事件")
    return graph


if __name__ == "__main__":
    # 示例测试
    from src.utils.sample_data import get_sample_script
    
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 获取示例脚本
    sample_script = get_sample_script()
    
    # 构建知识图谱
    graph = build_knowledge_graph(sample_script)
    
    # 输出角色重要性
    print("角色重要性:")
    for character, importance in graph.get_character_importance().items():
        print(f"  {character}: {importance:.2f}")
    
    # 输出事件
    print("\n事件:")
    for i, event in enumerate(graph.get_events()):
        print(f"  事件 {i+1}: {event['type']} - {event['description']}")
    
    # 检测矛盾
    contradictions = graph.find_contradictions()
    print(f"\n检测到 {len(contradictions)} 个逻辑矛盾")
    
    # 可视化
    try:
        graph.visualize()
    except Exception as e:
        print(f"可视化失败: {e}") 