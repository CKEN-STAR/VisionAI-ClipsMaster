"""
中文节拍分析器模块

专门针对中文短剧文本的叙事节拍分析，特性：
1. 基于中文语言特点的句式分析
2. 识别中文叙事风格的转折点
3. 基于词汇和语义的节拍分类
4. 使用轻量级模型进行情感和意图分析
"""

import os
import re
import json
import yaml
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

from src.nlp.sentiment_analyzer import analyze_text_sentiment
from src.utils.memory_guard import track_memory

# 常量定义
# 各节拍类型的特征词汇和标记
BEAT_FEATURES = {
    "exposition": {  # 铺垫
        "keywords": [
            "有一天", "从前", "曾经", "那一天", "这一天", "某天", "早上", "晚上", 
            "看到", "听到", "注意到", "发现", "是一个", "是一位", "在一个", 
            "住在", "生活在", "工作在", "平时", "一般", "通常", "习惯"
        ],
        "patterns": [
            r".*[是在有].*",  # 描述性状态
            r".*[\，\。\；].*[看见听到发现].*",  # 发现类句式
            r".*[名字叫做称为].*"  # 介绍性句式
        ],
        "sentiment_range": (-0.3, 0.3),  # 情感值范围，较为中性
        "intensity_threshold": 0.4  # 情感强度阈值
    },
    "rising_action": {  # 升级
        "keywords": [
            "突然", "忽然", "开始", "渐渐", "慢慢", "逐渐", "越来越", "不料",
            "没想到", "出乎意料", "意外", "却", "竟然", "居然", "试图", "打算",
            "想要", "决定", "必须", "一定要", "打算", "计划"
        ],
        "patterns": [
            r".*[但却而].*",  # 转折句式
            r".*[突然忽然].*",  # 突发事件
            r".*[开始准备打算].*"  # 行动开始
        ],
        "sentiment_range": (-0.7, 0.7),  # 较宽的情感变化
        "intensity_threshold": 0.5  # 中等情感强度
    },
    "climax": {  # 高潮
        "keywords": [
            "终于", "猛地", "猛然", "爆发", "冲", "打", "喊", "叫", "冲突",
            "争吵", "打斗", "厉声", "怒吼", "咆哮", "震惊", "大惊", "激动",
            "极度", "非常", "十分", "万分", "无比", "惊呆", "震惊", "崩溃"
        ],
        "patterns": [
            r".*[！\!]\s*[\」\"\'\]\s]*$",  # 感叹句结尾 
            r".*[？\?][？\?]+\s*[\」\"\'\]\s]*$",  # 多个问号结尾
            r".*[大猛狠狂疯].*"  # 强烈程度词
        ],
        "sentiment_range": (-1.0, 1.0),  # 全范围情感，可能很强烈
        "intensity_threshold": 0.7  # 高情感强度
    },
    "resolution": {  # 解决
        "keywords": [
            "最后", "终于", "最终", "总算", "结果", "于是", "因此", "所以", 
            "这样", "就这样", "从此", "从那以后", "之后", "从此以后", "明白了",
            "知道了", "理解了", "决定了", "成为", "变成", "回到", "离开"
        ],
        "patterns": [
            r".*[。\.]$",  # 以句号结尾，陈述性结束
            r".*[原来其实实际].*",  # 解释性内容
            r".*[这样于是所以因此].*"  # 结论性内容
        ],
        "sentiment_range": (-0.5, 0.8),  # 偏向积极的情感范围
        "intensity_threshold": 0.5  # 中等情感强度
    }
}


class ZhBeatAnalyzer:
    """中文节拍分析器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化中文节拍分析器
        
        Args:
            config_path: 配置文件路径，为None时使用默认配置
        """
        self.config = self._load_config(config_path)
        self._init_resources()
        logger.info("中文节拍分析器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        # 默认配置
        default_config = {
            "beat_features": BEAT_FEATURES,
            "similarity_threshold": 0.6,
            "context_window": 2,  # 上下文窗口大小
            "position_weight": 0.3,  # 位置因素权重
            "sentiment_weight": 0.3,  # 情感因素权重
            "keyword_weight": 0.4,  # 关键词因素权重
            "minimum_beat_length": 5,  # 最小节拍文本长度
            "combine_threshold": 0.7  # 合并相似节拍的阈值
        }
        
        # 如果提供了配置路径，尝试加载自定义配置
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = yaml.safe_load(f)
                    # 递归合并配置
                    default_config = self._merge_configs(default_config, custom_config)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        
        return default_config
    
    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """递归合并配置字典"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _init_resources(self):
        """初始化资源"""
        # 从配置加载节拍特征
        self.beat_features = self.config.get("beat_features", BEAT_FEATURES)
        
        # 预编译正则表达式模式
        for beat_type, features in self.beat_features.items():
            if "patterns" in features:
                compiled_patterns = []
                for pattern in features["patterns"]:
                    try:
                        compiled_patterns.append(re.compile(pattern))
                    except re.error as e:
                        logger.error(f"正则表达式编译错误: {pattern}, {e}")
                features["compiled_patterns"] = compiled_patterns
        
        # 初始化词汇索引
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """构建节拍关键词索引"""
        self.keyword_to_beat = {}
        for beat_type, features in self.beat_features.items():
            if "keywords" in features:
                for keyword in features["keywords"]:
                    if keyword in self.keyword_to_beat:
                        self.keyword_to_beat[keyword].append(beat_type)
                    else:
                        self.keyword_to_beat[keyword] = [beat_type]
    
    @track_memory("zh_beat_analysis")
    def predict_beats(self, text: str) -> List[Dict[str, Any]]:
        """
        预测文本的叙事节拍
        
        Args:
            text: 待分析的中文文本
            
        Returns:
            节拍列表，每个节拍包含类型、文本、位置和置信度
        """
        # 分割句子
        sentences = self._split_sentences(text)
        if not sentences:
            logger.warning("输入文本无法分割为句子")
            return []
        
        # 分析每个句子的特征
        sentence_features = []
        for i, sentence in enumerate(sentences):
            features = self._analyze_sentence(sentence, i / len(sentences))
            sentence_features.append(features)
        
        # 初步分配节拍类型
        initial_beats = []
        for i, features in enumerate(sentence_features):
            # 获取上下文窗口
            context_start = max(0, i - self.config.get("context_window", 2))
            context_end = min(len(sentence_features), i + self.config.get("context_window", 2) + 1)
            context = sentence_features[context_start:context_end]
            
            # 考虑上下文分类
            beat_type, confidence = self._classify_with_context(features, context, i / len(sentence_features))
            
            # 构建节拍对象
            beat = {
                "text": sentences[i],
                "type": beat_type,
                "position": i / len(sentences),
                "confidence": confidence,
                "emotion": features["emotion"]
            }
            initial_beats.append(beat)
        
        # 合并相似连续节拍
        merged_beats = self._merge_similar_beats(initial_beats)
        
        # 修正不合理的节拍序列
        final_beats = self._fix_beat_sequence(merged_beats)
        
        return final_beats
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        将文本分割为句子
        
        Args:
            text: 待分割的文本
            
        Returns:
            句子列表
        """
        text = text.strip()
        
        # 中文句子分隔符
        pattern = r'([。！？…；;!?]+)([^。！？…；;!?]*)'
        
        # 分割文本
        sentences = []
        result = re.findall(pattern, text)
        
        if result:
            # 处理正则匹配结果
            temp_text = text
            for r in result:
                parts = re.split(re.escape(r[0] + r[1]), temp_text, 1)
                if parts[0]:
                    sentences.append(parts[0] + r[0])
                temp_text = r[1] + (parts[1] if len(parts) > 1 else "")
            
            # 处理剩余部分
            if temp_text:
                sentences.append(temp_text)
        else:
            # 如果没有分隔符，尝试按换行分割
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    sentences.append(line)
        
        # 如果仍然没有分割结果，直接返回原文作为一个句子
        if not sentences:
            sentences = [text]
        
        # 清理句子
        clean_sentences = []
        for s in sentences:
            s = s.strip()
            if s:
                clean_sentences.append(s)
        
        return clean_sentences
    
    def _analyze_sentence(self, sentence: str, position: float) -> Dict[str, Any]:
        """
        分析句子特征
        
        Args:
            sentence: 待分析的句子
            position: 句子在文本中的位置
            
        Returns:
            句子的特征字典
        """
        features = {
            "text": sentence,
            "position": position,
            "keywords": [],
            "matched_patterns": [],
            "beat_scores": {
                "exposition": 0.0,
                "rising_action": 0.0,
                "climax": 0.0,
                "resolution": 0.0
            }
        }
        
        # 情感分析
        features["emotion"] = analyze_text_sentiment(sentence)
        
        # 关键词匹配
        for keyword, beat_types in self.keyword_to_beat.items():
            if keyword in sentence:
                features["keywords"].append(keyword)
                for beat_type in beat_types:
                    features["beat_scores"][beat_type] += 1.0
        
        # 正则模式匹配
        for beat_type, beat_feature in self.beat_features.items():
            if "compiled_patterns" in beat_feature:
                for pattern in beat_feature["compiled_patterns"]:
                    if pattern.search(sentence):
                        features["matched_patterns"].append(beat_type)
                        features["beat_scores"][beat_type] += 1.5  # 模式匹配权重更高
        
        # 情感特征评估
        sentiment = features["emotion"].get("sentiment", 0)
        intensity = features["emotion"].get("intensity", 0.5)
        
        for beat_type, beat_feature in self.beat_features.items():
            sentiment_range = beat_feature.get("sentiment_range", (-1, 1))
            intensity_threshold = beat_feature.get("intensity_threshold", 0.5)
            
            # 检查情感值是否在该节拍类型的范围内
            if sentiment_range[0] <= sentiment <= sentiment_range[1]:
                # 检查情感强度
                if intensity >= intensity_threshold:
                    # 情感匹配该节拍类型
                    features["beat_scores"][beat_type] += 0.8
        
        # 位置评估
        if position < 0.25:
            features["beat_scores"]["exposition"] += 2.0
        elif position < 0.6:
            features["beat_scores"]["rising_action"] += 1.5
        elif position < 0.85:
            features["beat_scores"]["climax"] += 1.5
        else:
            features["beat_scores"]["resolution"] += 2.0
        
        # 归一化分数
        total_score = sum(features["beat_scores"].values())
        if total_score > 0:
            for beat_type in features["beat_scores"]:
                features["beat_scores"][beat_type] /= total_score
        
        return features
    
    def _classify_with_context(self, features: Dict[str, Any], context: List[Dict[str, Any]], 
                           position: float) -> Tuple[str, float]:
        """
        考虑上下文的节拍分类
        
        Args:
            features: 当前句子特征
            context: 上下文句子特征
            position: 位置比例
            
        Returns:
            (节拍类型, 置信度)
        """
        # 获取配置权重
        position_weight = self.config.get("position_weight", 0.3)
        sentiment_weight = self.config.get("sentiment_weight", 0.3)
        keyword_weight = self.config.get("keyword_weight", 0.4)
        
        # 初始化总分数
        total_scores = {
            "exposition": 0.0,
            "rising_action": 0.0,
            "climax": 0.0,
            "resolution": 0.0
        }
        
        # 位置因素
        if position < 0.25:
            total_scores["exposition"] += position_weight
        elif position < 0.6:
            total_scores["rising_action"] += position_weight
        elif position < 0.85:
            total_scores["climax"] += position_weight
        else:
            total_scores["resolution"] += position_weight
        
        # 情感因素
        emotion = features["emotion"]
        sentiment = emotion.get("sentiment", 0)
        intensity = emotion.get("intensity", 0.5)
        
        if intensity > 0.7:  # 高情感强度
            total_scores["climax"] += sentiment_weight
        elif abs(sentiment) < 0.3:  # 中性情感
            total_scores["exposition"] += sentiment_weight * 0.8
        elif sentiment > 0.5:  # 积极情感
            total_scores["resolution"] += sentiment_weight * 0.7
        elif sentiment < -0.3:  # 消极情感
            total_scores["rising_action"] += sentiment_weight * 0.6
        
        # 关键词和模式因素
        for beat_type, score in features["beat_scores"].items():
            total_scores[beat_type] += score * keyword_weight
        
        # 找出得分最高的类型
        best_type = max(total_scores.items(), key=lambda x: x[1])
        
        # 计算置信度（最高分与次高分的差距）
        scores = list(total_scores.values())
        scores.sort(reverse=True)
        confidence = scores[0] - scores[1] if len(scores) > 1 else scores[0]
        
        # 归一化置信度到0-1
        confidence = min(1.0, max(0.1, confidence))
        
        return best_type[0], confidence
    
    def _merge_similar_beats(self, beats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并相似连续节拍
        
        Args:
            beats: 初始节拍列表
            
        Returns:
            合并后的节拍列表
        """
        if not beats:
            return []
        
        threshold = self.config.get("combine_threshold", 0.7)
        merged = []
        current_group = [beats[0]]
        
        for beat in beats[1:]:
            # 检查是否与当前组相同类型
            if beat["type"] == current_group[0]["type"]:
                current_group.append(beat)
            else:
                # 检查置信度
                current_confidence = current_group[0]["confidence"]
                new_confidence = beat["confidence"]
                
                # 如果当前节拍置信度低且新节拍与前面的不同，可能需要合并
                if current_confidence < threshold and new_confidence > current_confidence:
                    # 改变整个组的类型
                    for b in current_group:
                        b["type"] = beat["type"]
                    current_group.append(beat)
                else:
                    # 合并当前组
                    merged.append(self._combine_beat_group(current_group))
                    # 开始新组
                    current_group = [beat]
        
        # 合并最后一组
        if current_group:
            merged.append(self._combine_beat_group(current_group))
        
        return merged
    
    def _combine_beat_group(self, beat_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并一组相同类型的节拍
        
        Args:
            beat_group: 同类型节拍组
            
        Returns:
            合并后的节拍
        """
        if not beat_group:
            return {}
        
        # 合并文本
        texts = [beat["text"] for beat in beat_group]
        combined_text = " ".join(texts)
        
        # 取平均位置
        avg_position = sum([beat["position"] for beat in beat_group]) / len(beat_group)
        
        # 取最高置信度
        max_confidence = max([beat["confidence"] for beat in beat_group])
        
        # 合并情感，取强度最高的
        emotions = [beat["emotion"] for beat in beat_group]
        max_intensity_idx = np.argmax([e.get("intensity", 0) for e in emotions])
        strongest_emotion = emotions[max_intensity_idx]
        
        # 创建合并节拍
        return {
            "text": combined_text,
            "type": beat_group[0]["type"],  # 使用组中第一个节拍的类型
            "position": avg_position,
            "confidence": max_confidence,
            "emotion": strongest_emotion,
            "merged_count": len(beat_group)
        }
    
    def _fix_beat_sequence(self, beats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        修复不合理的节拍序列
        
        Args:
            beats: 节拍列表
            
        Returns:
            修复后的节拍列表
        """
        if len(beats) <= 1:
            return beats
        
        # 理想节拍顺序
        ideal_sequence = ["exposition", "rising_action", "climax", "resolution"]
        
        fixed_beats = beats.copy()
        
        # 修复明显违反顺序的情况
        for i in range(1, len(fixed_beats)):
            current_type = fixed_beats[i]["type"]
            prev_type = fixed_beats[i-1]["type"]
            
            current_idx = ideal_sequence.index(current_type) if current_type in ideal_sequence else -1
            prev_idx = ideal_sequence.index(prev_type) if prev_type in ideal_sequence else -1
            
            # 检测逆序（如resolution后面跟exposition）
            if current_idx >= 0 and prev_idx >= 0 and current_idx < prev_idx:
                # 低置信度时修复
                if fixed_beats[i]["confidence"] < 0.7:
                    # 将当前节拍改为前一节拍类型或下一个合理类型
                    if prev_idx + 1 < len(ideal_sequence):
                        fixed_beats[i]["type"] = ideal_sequence[prev_idx]  # 保持相同类型
                        fixed_beats[i]["confidence"] *= 0.8  # 降低置信度
        
        # 确保开头有exposition
        if len(fixed_beats) >= 3 and fixed_beats[0]["type"] != "exposition":
            if fixed_beats[0]["position"] < 0.2 and fixed_beats[0]["confidence"] < 0.8:
                fixed_beats[0]["type"] = "exposition"
                fixed_beats[0]["confidence"] *= 0.8
        
        # 确保结尾有resolution
        if len(fixed_beats) >= 3 and fixed_beats[-1]["type"] != "resolution":
            if fixed_beats[-1]["position"] > 0.8 and fixed_beats[-1]["confidence"] < 0.8:
                fixed_beats[-1]["type"] = "resolution"
                fixed_beats[-1]["confidence"] *= 0.8
        
        return fixed_beats


if __name__ == "__main__":
    # 测试代码
    analyzer = ZhBeatAnalyzer()
    
    test_text = """
    张三走进房间，环顾四周。"有人在吗？"他轻声问道。
    屋子里一片寂静，只有窗外的雨声滴答作响。
    突然，一个黑影从角落里闪过，张三猛地转身。
    "谁？"他厉声喊道，手不自觉地握成了拳头。
    "是我。"李四从阴影中走出来，脸上带着神秘的微笑。
    "你吓死我了！"张三松了口气，"你怎么会在这里？"
    李四慢慢走近，眼神复杂："我一直在等你，我们需要谈谈。"
    张三感到一阵不安："谈什么？"
    "关于那天晚上发生的事。"李四严肃地说。
    """
    
    beats = analyzer.predict_beats(test_text)
    for i, beat in enumerate(beats):
        print(f"节拍 {i+1} ({beat['type']}): {beat['text']}")
        print(f"  置信度: {beat['confidence']:.2f}, 位置: {beat['position']:.2f}")
        print(f"  情感: {beat['emotion']}")
        print("---") 