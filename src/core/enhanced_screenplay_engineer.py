#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强剧本工程师
Enhanced Screenplay Engineer

修复内容：
1. 增强爆款SRT生成能力
2. 改进剧情理解和重构逻辑
3. 添加更多情感关键词和吸引力元素
4. 优化时间轴重新规划算法
"""

import re
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 导入增强的模型切换器
try:
    from .enhanced_model_switcher import EnhancedModelSwitcher
    from .enhanced_language_detector import EnhancedLanguageDetector
except ImportError:
    from src.core.enhanced_model_switcher import EnhancedModelSwitcher
    from src.core.enhanced_language_detector import EnhancedLanguageDetector

logger = logging.getLogger(__name__)

class EnhancedScreenplayEngineer:
    """增强剧本工程师"""
    
    def __init__(self):
        """初始化剧本工程师"""
        self.model_switcher = EnhancedModelSwitcher()
        self.language_detector = EnhancedLanguageDetector()
        
        # 爆款元素库
        self.viral_elements = {
            "zh": {
                "emotional_hooks": [
                    "震撼！", "惊呆了！", "不可思议！", "太震撼了！", "简直不敢相信！",
                    "这也太...", "居然...", "竟然...", "没想到...", "万万没想到..."
                ],
                "suspense_words": [
                    "秘密", "真相", "隐藏", "背后", "不为人知", "神秘", "惊天",
                    "爆料", "曝光", "揭秘", "内幕", "黑幕", "阴谋", "计划"
                ],
                "character_types": [
                    "霸道总裁", "灰姑娘", "白月光", "朱砂痣", "替身", "双胞胎",
                    "失忆", "重生", "穿越", "豪门", "世家", "继承人"
                ],
                "plot_devices": [
                    "身份互换", "误会重重", "命运安排", "意外相遇", "旧情复燃",
                    "三角恋", "复仇计划", "家族恩怨", "商战风云", "爱恨纠葛"
                ],
                "emotional_intensifiers": [
                    "心动", "心碎", "心痛", "撕心裂肺", "刻骨铭心", "难以忘怀",
                    "深深震撼", "无法自拔", "欲罢不能", "爱恨交织"
                ]
            },
            "en": {
                "emotional_hooks": [
                    "SHOCKING!", "UNBELIEVABLE!", "INCREDIBLE!", "AMAZING!", "WOW!",
                    "You won't believe...", "This is insane...", "OMG...", "Wait for it..."
                ],
                "suspense_words": [
                    "secret", "mystery", "hidden", "revealed", "exposed", "truth",
                    "conspiracy", "plot", "scheme", "betrayal", "scandal"
                ],
                "character_types": [
                    "CEO", "billionaire", "prince", "princess", "heir", "tycoon",
                    "mogul", "elite", "aristocrat", "royalty"
                ],
                "plot_devices": [
                    "love triangle", "revenge plot", "family feud", "corporate war",
                    "forbidden love", "second chance", "enemies to lovers", "fake dating"
                ],
                "emotional_intensifiers": [
                    "heartbreaking", "breathtaking", "mind-blowing", "soul-crushing",
                    "life-changing", "unforgettable", "devastating", "overwhelming"
                ]
            }
        }
        
        # 剧情模板
        self.plot_templates = {
            "romance": {
                "zh": [
                    "命运的安排让{character1}和{character2}意外相遇",
                    "{character1}的真实身份震撼了所有人",
                    "这段感情背后隐藏着惊天秘密",
                    "最终的选择改变了一切"
                ],
                "en": [
                    "Fate brings {character1} and {character2} together",
                    "The shocking truth about {character1}'s identity",
                    "A secret that changes everything",
                    "The ultimate choice that defines their destiny"
                ]
            },
            "suspense": {
                "zh": [
                    "看似平静的表面下暗流涌动",
                    "真相比想象中更加震撼",
                    "每个人都有不可告人的秘密",
                    "最后的反转让人措手不及"
                ],
                "en": [
                    "Beneath the calm surface lies a storm",
                    "The truth is more shocking than imagined",
                    "Everyone has a dark secret",
                    "The final twist changes everything"
                ]
            }
        }
        
        # 处理历史
        self.processing_history = []
        
    def analyze_plot_structure(self, srt_content: str) -> Dict[str, Any]:
        """分析剧情结构"""
        try:
            # 解析SRT内容
            subtitles = self.parse_srt_content(srt_content)
            
            if not subtitles:
                return {"error": "无法解析字幕内容"}
                
            # 检测语言
            language = self.language_detector.detect_language(srt_content)
            
            # 提取关键信息
            characters = self._extract_characters(subtitles, language)
            scenes = self._extract_scenes(subtitles)
            emotions = self._analyze_emotions(subtitles, language)
            plot_points = self._identify_plot_points(subtitles, language)
            
            analysis = {
                "language": language,
                "total_subtitles": len(subtitles),
                "duration": subtitles[-1].get("end_time", 0) if subtitles else 0,
                "characters": characters,
                "scenes": scenes,
                "emotions": emotions,
                "plot_points": plot_points,
                "genre": self._detect_genre(subtitles, language),
                "pacing": self._analyze_pacing(subtitles)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"剧情结构分析失败: {e}")
            return {"error": str(e)}
            
    def generate_viral_version(self, original_content: str, language: str = None) -> Dict[str, Any]:
        """生成爆款版本"""
        try:
            # 分析原始内容
            plot_analysis = self.analyze_plot_structure(original_content)
            
            if "error" in plot_analysis:
                return {"success": False, "error": plot_analysis["error"]}
                
            # 确定语言
            if not language:
                language = plot_analysis.get("language", "zh")
                
            # 提取关键情节点
            key_moments = self._extract_key_moments(plot_analysis)
            
            # 生成爆款字幕
            viral_subtitles = self._generate_viral_subtitles(key_moments, language, plot_analysis)
            
            # 生成SRT内容
            viral_srt_content = self._generate_srt_content(viral_subtitles)
            
            # 计算质量指标
            quality_metrics = self._calculate_quality_metrics(viral_subtitles, language)
            
            result = {
                "success": True,
                "viral_content": viral_srt_content,
                "subtitles": viral_subtitles,
                "original_analysis": plot_analysis,
                "quality_metrics": quality_metrics,
                "language": language,
                "compression_ratio": len(viral_subtitles) / plot_analysis.get("total_subtitles", 1),
                "generation_time": time.time()
            }
            
            # 记录处理历史
            self.processing_history.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "generate_viral_version",
                "language": language,
                "original_length": plot_analysis.get("total_subtitles", 0),
                "viral_length": len(viral_subtitles),
                "quality_score": quality_metrics.get("overall_score", 0)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"生成爆款版本失败: {e}")
            return {"success": False, "error": str(e)}
            
    def parse_srt_content(self, content: str) -> List[Dict[str, Any]]:
        """解析SRT内容"""
        try:
            subtitles = []
            blocks = re.split(r'\n\s*\n', content.strip())
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                    
                try:
                    # 序号
                    index = int(lines[0])
                    
                    # 时间轴
                    time_line = lines[1]
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
                    if not time_match:
                        continue
                        
                    start_time_str, end_time_str = time_match.groups()
                    start_time = self._time_str_to_seconds(start_time_str)
                    end_time = self._time_str_to_seconds(end_time_str)
                    
                    # 字幕文本
                    text = '\n'.join(lines[2:])
                    
                    subtitles.append({
                        'index': index,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': end_time - start_time,
                        'text': text
                    })
                    
                except (ValueError, IndexError):
                    continue
                    
            return subtitles
            
        except Exception as e:
            logger.error(f"SRT内容解析失败: {e}")
            return []
            
    def _time_str_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒数"""
        time_part, ms_part = time_str.split(',')
        hours, minutes, seconds = map(int, time_part.split(':'))
        milliseconds = int(ms_part)
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
        return total_seconds
        
    def _seconds_to_time_str(self, seconds: float) -> str:
        """将秒数转换为时间字符串"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
        
    def _extract_characters(self, subtitles: List[Dict[str, Any]], language: str) -> List[str]:
        """提取角色名"""
        characters = set()
        
        # 常见角色名模式
        if language == "zh":
            # 中文姓名模式
            name_patterns = [
                r'[王李张刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][一-龯]{1,2}',
                r'[A-Z][a-z]+',  # 英文名
            ]
        else:
            # 英文姓名模式
            name_patterns = [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # 全名
                r'\b[A-Z][a-z]+\b',  # 单名
            ]
            
        for subtitle in subtitles:
            text = subtitle.get("text", "")
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                characters.update(matches)
                
        return list(characters)[:10]  # 返回前10个角色
        
    def _extract_scenes(self, subtitles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取场景"""
        scenes = []
        current_scene = None
        scene_threshold = 10.0  # 10秒间隔认为是新场景
        
        for i, subtitle in enumerate(subtitles):
            if i == 0 or (subtitle["start_time"] - subtitles[i-1]["end_time"]) > scene_threshold:
                # 新场景
                if current_scene:
                    scenes.append(current_scene)
                    
                current_scene = {
                    "scene_id": len(scenes) + 1,
                    "start_time": subtitle["start_time"],
                    "end_time": subtitle["end_time"],
                    "subtitles": [subtitle]
                }
            else:
                # 继续当前场景
                if current_scene:
                    current_scene["end_time"] = subtitle["end_time"]
                    current_scene["subtitles"].append(subtitle)
                    
        if current_scene:
            scenes.append(current_scene)
            
        return scenes
        
    def _analyze_emotions(self, subtitles: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """分析情感"""
        emotions = {"positive": 0, "negative": 0, "neutral": 0, "intense": 0}
        
        # 情感词典
        if language == "zh":
            positive_words = ["开心", "高兴", "快乐", "幸福", "满意", "喜欢", "爱", "美好", "温暖", "甜蜜"]
            negative_words = ["伤心", "难过", "痛苦", "愤怒", "失望", "恐惧", "害怕", "绝望", "冷漠", "仇恨"]
            intense_words = ["震撼", "惊呆", "不可思议", "太", "非常", "极其", "超级", "巨", "狂", "疯"]
        else:
            positive_words = ["happy", "joy", "love", "wonderful", "amazing", "great", "fantastic", "beautiful", "sweet", "warm"]
            negative_words = ["sad", "angry", "hate", "terrible", "awful", "horrible", "disgusting", "painful", "fear", "despair"]
            intense_words = ["shocking", "incredible", "amazing", "unbelievable", "extremely", "super", "ultra", "mega", "crazy", "insane"]
            
        for subtitle in subtitles:
            text = subtitle.get("text", "").lower()
            
            for word in positive_words:
                if word in text:
                    emotions["positive"] += 1
                    
            for word in negative_words:
                if word in text:
                    emotions["negative"] += 1
                    
            for word in intense_words:
                if word in text:
                    emotions["intense"] += 1
                    
            # 如果没有明显情感词，归为中性
            if not any(word in text for word in positive_words + negative_words):
                emotions["neutral"] += 1
                
        return emotions

    def _identify_plot_points(self, subtitles: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """识别关键剧情点"""
        plot_points = []

        # 关键词模式
        if language == "zh":
            key_patterns = {
                "开始": ["开始", "第一次", "初次", "刚开始", "起初"],
                "转折": ["但是", "然而", "不过", "突然", "忽然", "没想到", "竟然"],
                "高潮": ["最终", "终于", "关键时刻", "决定性", "重要"],
                "结局": ["最后", "结束", "完成", "成功", "失败", "结果"]
            }
        else:
            key_patterns = {
                "beginning": ["start", "first", "begin", "initially", "at first"],
                "turning": ["but", "however", "suddenly", "unexpectedly", "then"],
                "climax": ["finally", "ultimately", "crucial", "decisive", "critical"],
                "ending": ["end", "finish", "complete", "success", "failure", "result"]
            }

        for i, subtitle in enumerate(subtitles):
            text = subtitle.get("text", "").lower()

            for point_type, keywords in key_patterns.items():
                for keyword in keywords:
                    if keyword in text:
                        plot_points.append({
                            "type": point_type,
                            "subtitle_index": i,
                            "time": subtitle["start_time"],
                            "text": subtitle["text"],
                            "keyword": keyword
                        })
                        break

        return plot_points

    def _detect_genre(self, subtitles: List[Dict[str, Any]], language: str) -> str:
        """检测剧情类型"""
        genre_keywords = {
            "romance": {
                "zh": ["爱", "喜欢", "心动", "表白", "约会", "结婚", "恋爱", "情侣", "男朋友", "女朋友"],
                "en": ["love", "like", "heart", "date", "marry", "romance", "couple", "boyfriend", "girlfriend"]
            },
            "suspense": {
                "zh": ["秘密", "神秘", "调查", "真相", "线索", "怀疑", "发现", "隐藏", "阴谋"],
                "en": ["secret", "mystery", "investigate", "truth", "clue", "suspect", "discover", "hidden", "conspiracy"]
            },
            "comedy": {
                "zh": ["搞笑", "有趣", "好玩", "幽默", "笑", "开心", "滑稽", "逗"],
                "en": ["funny", "hilarious", "comedy", "humor", "laugh", "joke", "amusing", "entertaining"]
            }
        }

        genre_scores = {}
        all_text = " ".join([sub.get("text", "") for sub in subtitles]).lower()

        for genre, keywords_dict in genre_keywords.items():
            keywords = keywords_dict.get(language, [])
            score = sum(1 for keyword in keywords if keyword in all_text)
            genre_scores[genre] = score

        # 返回得分最高的类型
        if genre_scores:
            return max(genre_scores, key=genre_scores.get)
        else:
            return "unknown"

    def _analyze_pacing(self, subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析节奏"""
        if not subtitles:
            return {"average_duration": 0, "rhythm": "unknown"}

        durations = [sub["duration"] for sub in subtitles]
        avg_duration = sum(durations) / len(durations)

        # 判断节奏
        if avg_duration < 2.0:
            rhythm = "fast"
        elif avg_duration > 4.0:
            rhythm = "slow"
        else:
            rhythm = "medium"

        return {
            "average_duration": avg_duration,
            "rhythm": rhythm,
            "total_duration": subtitles[-1]["end_time"] if subtitles else 0
        }

    def _extract_key_moments(self, plot_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取关键时刻"""
        key_moments = []

        # 从剧情点中选择关键时刻
        plot_points = plot_analysis.get("plot_points", [])

        # 按类型优先级排序
        priority_order = ["beginning", "turning", "climax", "ending", "开始", "转折", "高潮", "结局"]

        for point_type in priority_order:
            matching_points = [p for p in plot_points if p["type"] == point_type]
            if matching_points:
                # 选择第一个匹配的点
                key_moments.append(matching_points[0])

        # 如果关键时刻不足，从场景中补充
        scenes = plot_analysis.get("scenes", [])
        if len(key_moments) < 4 and scenes:
            # 选择场景的开始作为关键时刻
            for scene in scenes[:4-len(key_moments)]:
                if scene["subtitles"]:
                    key_moments.append({
                        "type": "scene_start",
                        "subtitle_index": 0,
                        "time": scene["start_time"],
                        "text": scene["subtitles"][0]["text"],
                        "scene_id": scene["scene_id"]
                    })

        return key_moments[:6]  # 最多6个关键时刻

    def _generate_viral_subtitles(self, key_moments: List[Dict[str, Any]], language: str, plot_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成爆款字幕"""
        viral_subtitles = []
        genre = plot_analysis.get("genre", "unknown")

        # 获取爆款元素
        viral_elements = self.viral_elements.get(language, self.viral_elements["zh"])

        current_time = 0.0
        subtitle_duration = 4.0  # 每个字幕4秒

        for i, moment in enumerate(key_moments):
            # 生成爆款文本
            viral_text = self._generate_viral_text(moment, language, genre, viral_elements)

            viral_subtitles.append({
                "index": i + 1,
                "start_time": current_time,
                "end_time": current_time + subtitle_duration,
                "duration": subtitle_duration,
                "text": viral_text,
                "original_moment": moment
            })

            current_time += subtitle_duration

        return viral_subtitles

    def _generate_viral_text(self, moment: Dict[str, Any], language: str, genre: str, viral_elements: Dict[str, List[str]]) -> str:
        """生成爆款文本"""
        original_text = moment.get("text", "")
        moment_type = moment.get("type", "")

        # 选择合适的爆款元素
        if moment_type in ["beginning", "开始"]:
            hook = viral_elements["emotional_hooks"][0]
            if language == "zh":
                viral_text = f"{hook}故事从这里开始改变一切！"
            else:
                viral_text = f"{hook} This is where everything changes!"

        elif moment_type in ["turning", "转折"]:
            suspense = viral_elements["suspense_words"][0]
            if language == "zh":
                viral_text = f"没想到{suspense}竟然是这样！"
            else:
                viral_text = f"The {suspense} behind this will shock you!"

        elif moment_type in ["climax", "高潮"]:
            intensifier = viral_elements["emotional_intensifiers"][0]
            if language == "zh":
                viral_text = f"最{intensifier}的时刻到了！"
            else:
                viral_text = f"The most {intensifier} moment arrives!"

        elif moment_type in ["ending", "结局"]:
            if language == "zh":
                viral_text = "结局让所有人都惊呆了！"
            else:
                viral_text = "The ending will blow your mind!"

        else:
            # 默认处理
            hook = viral_elements["emotional_hooks"][0]
            if language == "zh":
                viral_text = f"{hook}{original_text[:15]}..."
            else:
                viral_text = f"{hook} {original_text[:20]}..."

        return viral_text

    def _generate_srt_content(self, subtitles: List[Dict[str, Any]]) -> str:
        """生成SRT内容"""
        srt_lines = []

        for subtitle in subtitles:
            start_time_str = self._seconds_to_time_str(subtitle["start_time"])
            end_time_str = self._seconds_to_time_str(subtitle["end_time"])

            srt_lines.extend([
                str(subtitle["index"]),
                f"{start_time_str} --> {end_time_str}",
                subtitle["text"],
                ""
            ])

        return "\n".join(srt_lines)

    def _calculate_quality_metrics(self, viral_subtitles: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """计算质量指标"""
        if not viral_subtitles:
            return {"overall_score": 0}

        # 获取爆款元素
        viral_elements = self.viral_elements.get(language, self.viral_elements["zh"])

        # 计算各项指标
        emotional_score = 0
        suspense_score = 0
        viral_keyword_count = 0

        all_text = " ".join([sub["text"] for sub in viral_subtitles])

        # 情感钩子分数
        for hook in viral_elements["emotional_hooks"]:
            if hook in all_text:
                emotional_score += 1

        # 悬念分数
        for word in viral_elements["suspense_words"]:
            if word in all_text:
                suspense_score += 1

        # 爆款关键词计数
        all_keywords = (viral_elements["emotional_hooks"] +
                       viral_elements["suspense_words"] +
                       viral_elements["emotional_intensifiers"])

        for keyword in all_keywords:
            viral_keyword_count += all_text.count(keyword)

        # 计算综合分数
        max_possible_score = len(viral_subtitles) * 3  # 每个字幕最多3分
        actual_score = emotional_score + suspense_score + min(viral_keyword_count, max_possible_score)
        overall_score = min(actual_score / max_possible_score, 1.0) if max_possible_score > 0 else 0

        return {
            "overall_score": overall_score,
            "emotional_score": emotional_score,
            "suspense_score": suspense_score,
            "viral_keyword_count": viral_keyword_count,
            "subtitle_count": len(viral_subtitles),
            "average_length": sum(len(sub["text"]) for sub in viral_subtitles) / len(viral_subtitles)
        }


# 全局实例
_screenplay_engineer = EnhancedScreenplayEngineer()

# 向后兼容的函数接口
def analyze_plot_structure(srt_content: str) -> Dict[str, Any]:
    """向后兼容的剧情分析函数"""
    return _screenplay_engineer.analyze_plot_structure(srt_content)

def generate_viral_version(original_content: str, language: str = None) -> Dict[str, Any]:
    """向后兼容的爆款生成函数"""
    return _screenplay_engineer.generate_viral_version(original_content, language)

# 新增的类别名，保持兼容性
ScreenplayEngineer = EnhancedScreenplayEngineer
