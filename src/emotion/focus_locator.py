#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
情感焦点定位器

检测和定位文本/剧本中的情感焦点，包括高情感强度段落、
肢体动作描述片段以及关键对话中的情感句等。
用于辅助视频混剪时精准定位情感核心内容。
"""

import re
import os
import yaml
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union
from loguru import logger

# 导入NLP相关功能
from src.nlp.sentiment_analyzer import analyze_sentiment
from src.nlp.text_processor import process_text

# 默认配置路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                  "configs", "emotion_focus.yaml")

class EmotionFocusLocator:
    """情感焦点定位器，识别文本中的情感焦点"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """
        初始化情感焦点定位器
        
        Args:
            config: 配置参数字典，包含情感焦点定位参数
            config_path: 配置文件路径，如不提供则使用默认路径
        """
        # 加载配置
        self.config = self._load_config(config, config_path)
        
        # 日志记录
        logger.info("情感焦点定位器初始化完成")
    
    def _load_config(self, config: Optional[Dict[str, Any]], config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        if config:
            return config
        
        # 确定配置文件路径
        if not config_path:
            config_path = DEFAULT_CONFIG_PATH
        
        # 尝试从文件加载配置
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        
        # 返回默认配置
        return {
            "focus_detection": {
                "emotion_score_threshold": 0.7,
                "body_language_weight": 0.2,
                "dialogue_weight": 0.15,
                "exclamation_weight": 0.1
            },
            "body_language_patterns": [
                "摇头", "点头", "皱眉", "微笑", "大笑", "哭泣", "叹气",
                "颤抖", "拥抱", "握手", "举手", "挥手", "跺脚", "跳起",
                "后退", "前进", "转身", "倒下", "站起", "推开", "拉近"
            ],
            "emotional_dialogue_markers": [
                "!", "?!", "...", "？！", "。。。", 
                "啊", "哎", "哦", "唉", "呀", "哇"
            ]
        }
    
    def locate_emotional_cores(self, scene_text: str) -> List[Tuple[int, int]]:
        """
        定位文本中的情感焦点核心
        
        Args:
            scene_text: 场景文本内容
            
        Returns:
            情感焦点位置列表，每项为(开始位置, 结束位置)的元组
        """
        if not scene_text:
            return []
        
        # 获取配置参数
        config = self.config.get("focus_detection", {})
        emotion_threshold = config.get("emotion_score_threshold", 0.7)
        
        # 将文本分割为句子
        sentences = self._split_into_sentences(scene_text)
        
        # 分析每个句子的情感强度
        emotional_cores = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # 计算句子的情感得分
            emotion_score = self._calculate_emotion_score(sentence)
            
            # 判断是否为情感焦点
            if emotion_score >= emotion_threshold:
                # 查找句子在原文中的位置
                start_pos = scene_text.find(sentence)
                if start_pos != -1:
                    end_pos = start_pos + len(sentence)
                    emotional_cores.append((start_pos, end_pos))
        
        return emotional_cores
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割为句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        # 中文句子分割模式
        pattern = r'([^。！？\!\?]+[。！？\!\?]+)'
        sentences = re.findall(pattern, text)
        
        # 处理最后可能没有标点的句子
        last_end = 0
        for s in sentences:
            last_end = text.find(s, last_end) + len(s)
        
        if last_end < len(text.strip()):
            remaining = text[last_end:].strip()
            if remaining:
                sentences.append(remaining)
        
        return sentences
    
    def _calculate_emotion_score(self, sentence: str) -> float:
        """
        计算句子的情感得分
        
        综合考虑情感强度、肢体动作描述和对话特征
        
        Args:
            sentence: 输入句子
            
        Returns:
            情感得分 (0.0-1.0)
        """
        # 分析基础情感强度
        sentiment_result = analyze_sentiment(sentence)
        base_score = sentiment_result.get('intensity', 0.5)
        
        # 增加额外得分
        extra_score = 0.0
        
        # 1. 检测肢体动作描述
        body_language_score = self._detect_body_language(sentence) * \
                             self.config.get("focus_detection", {}).get("body_language_weight", 0.2)
                             
        # 2. 检测对话中的情感标记
        dialogue_score = self._detect_emotional_dialogue(sentence) * \
                        self.config.get("focus_detection", {}).get("dialogue_weight", 0.15)
                        
        # 3. 检测感叹词和强调
        exclamation_score = self._detect_exclamations(sentence) * \
                           self.config.get("focus_detection", {}).get("exclamation_weight", 0.1)
        
        # 综合得分，但不超过1.0
        total_score = min(1.0, base_score + body_language_score + dialogue_score + exclamation_score)
        
        return total_score
    
    def _detect_body_language(self, text: str) -> float:
        """
        检测文本中的肢体动作描述
        
        Args:
            text: 输入文本
            
        Returns:
            肢体动作强度得分 (0.0-1.0)
        """
        body_language_patterns = self.config.get("body_language_patterns", [])
        if not body_language_patterns:
            return 0.0
        
        # 统计肢体动作描述出现次数
        count = 0
        for pattern in body_language_patterns:
            count += len(re.findall(pattern, text))
        
        # 归一化分数
        return min(1.0, count * 0.2)
    
    def _detect_emotional_dialogue(self, text: str) -> float:
        """
        检测文本中的情感对话特征
        
        Args:
            text: 输入文本
            
        Returns:
            情感对话特征得分 (0.0-1.0)
        """
        emotional_markers = self.config.get("emotional_dialogue_markers", [])
        if not emotional_markers:
            return 0.0
        
        # 1. 检测引号内的对话
        dialogue_matches = re.findall(r'[""][^""]+[""]', text)
        
        # 如果没有对话，返回较低分数
        if not dialogue_matches:
            return 0.0
        
        # 2. 检测对话中的情感标记
        score = 0.0
        for dialogue in dialogue_matches:
            marker_count = 0
            for marker in emotional_markers:
                marker_count += dialogue.count(marker)
            
            # 每个对话中的情感标记得分
            dialogue_score = min(1.0, marker_count * 0.3)
            score = max(score, dialogue_score)
        
        return score
    
    def _detect_exclamations(self, text: str) -> float:
        """
        检测文本中的感叹词和强调表达
        
        Args:
            text: 输入文本
            
        Returns:
            感叹强调得分 (0.0-1.0)
        """
        # 检测感叹号、问号等标点
        exclamation_count = len(re.findall(r'[!！]', text))
        question_count = len(re.findall(r'[?？]', text))
        
        # 检测重复标点
        repeated_marks = len(re.findall(r'[!！]{2,}|[?？]{2,}|[.。]{3,}', text))
        
        # 检测全大写字母(英文)或强调标记
        emphasis_marks = len(re.findall(r'[A-Z]{2,}|【.+】|「.+」|『.+』', text))
        
        # 计算得分
        score = min(1.0, (exclamation_count * 0.2 + 
                         question_count * 0.1 + 
                         repeated_marks * 0.4 + 
                         emphasis_marks * 0.3))
        
        return score
    
    def find_emotion_focus_ranges(self, scene_text: str, window_size: int = 20) -> List[Dict[str, Any]]:
        """
        查找情感焦点范围，并增加上下文
        
        Args:
            scene_text: 场景文本内容
            window_size: 上下文窗口大小(字符数)
            
        Returns:
            情感焦点列表，包含位置、文本和得分信息
        """
        # 定位基础情感核心
        cores = self.locate_emotional_cores(scene_text)
        
        # 处理重叠的情感核心
        merged_cores = self._merge_overlapping_cores(cores)
        
        # 构建带有上下文的焦点范围
        focus_ranges = []
        
        for start, end in merged_cores:
            # 扩展上下文
            context_start = max(0, start - window_size)
            context_end = min(len(scene_text), end + window_size)
            
            # 提取焦点文本
            focus_text = scene_text[start:end]
            context_text = scene_text[context_start:context_end]
            
            # 计算情感得分
            focus_score = self._calculate_emotion_score(focus_text)
            
            # 构建焦点信息
            focus_info = {
                "start": start,
                "end": end,
                "focus_text": focus_text,
                "context_text": context_text,
                "context_start": context_start,
                "context_end": context_end,
                "emotion_score": focus_score
            }
            
            focus_ranges.append(focus_info)
        
        # 按情感得分排序
        focus_ranges.sort(key=lambda x: x["emotion_score"], reverse=True)
        
        return focus_ranges
    
    def _merge_overlapping_cores(self, cores: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        合并重叠的情感核心
        
        Args:
            cores: 情感核心位置列表
            
        Returns:
            合并后的核心位置列表
        """
        if not cores:
            return []
        
        # 按开始位置排序
        sorted_cores = sorted(cores)
        
        merged = []
        current_start, current_end = sorted_cores[0]
        
        for start, end in sorted_cores[1:]:
            # 如果当前区间与上一个重叠
            if start <= current_end:
                # 扩展当前区间
                current_end = max(current_end, end)
            else:
                # 添加上一个区间并开始新区间
                merged.append((current_start, current_end))
                current_start, current_end = start, end
        
        # 添加最后一个区间
        merged.append((current_start, current_end))
        
        return merged
    
    def analyze_scene_emotion_focus(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析场景的情感焦点
        
        Args:
            scene: 场景数据，包含文本等信息
            
        Returns:
            带有情感焦点信息的场景数据
        """
        scene_text = scene.get("text", "")
        if not scene_text:
            return scene
        
        # 查找情感焦点
        focus_ranges = self.find_emotion_focus_ranges(scene_text)
        
        # 更新场景数据
        scene_with_focus = scene.copy()
        scene_with_focus["emotion_focus"] = {
            "ranges": focus_ranges,
            "count": len(focus_ranges),
            "highest_score": max([f["emotion_score"] for f in focus_ranges]) if focus_ranges else 0
        }
        
        return scene_with_focus


def locate_emotional_cores(scene_text: str) -> List[Tuple[int, int]]:
    """
    定位文本中的情感焦点核心的便捷函数
    
    Args:
        scene_text: 场景文本内容
        
    Returns:
        情感焦点位置列表，每项为(开始位置, 结束位置)的元组
    """
    locator = EmotionFocusLocator()
    return locator.locate_emotional_cores(scene_text)


def find_emotion_focus_ranges(scene_text: str, window_size: int = 20) -> List[Dict[str, Any]]:
    """
    查找情感焦点范围的便捷函数
    
    Args:
        scene_text: 场景文本内容
        window_size: 上下文窗口大小
        
    Returns:
        情感焦点列表，包含位置、文本和得分信息
    """
    locator = EmotionFocusLocator()
    return locator.find_emotion_focus_ranges(scene_text, window_size) 