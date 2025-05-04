"""
文化语境适配器模块

负责调整字幕表达以适应不同文化背景，确保内容在跨文化传播时保持原意并符合目标文化的表达习惯。
支持中文和西方表达方式的相互转换，包括：
1. 情感表达适配（直接/含蓄）
2. 文化参考替换（成语/谚语/流行梗）
3. 表达节奏调整（句式长度/复杂度）
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

from ..utils.config_loader import ConfigLoader
from ..nlp.language_detector import detect_language
from ..emotion.intensity_mapper import EmotionIntensityMapper

logger = logging.getLogger(__name__)

class CultureAdapter:
    """文化语境适配器类
    
    负责根据目标文化调整字幕表达，确保内容符合不同文化背景受众的期望。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化文化适配器
        
        Args:
            config_path: 文化适配配置文件路径，默认为None时使用内置配置
        """
        self.config = self._load_config(config_path)
        self.emotion_mapper = EmotionIntensityMapper()
        
        # 加载文化表达映射数据
        self.expression_maps = {
            'zh_to_en': self._load_expression_map('zh_to_en'),
            'en_to_zh': self._load_expression_map('en_to_zh')
        }
        
        # 加载文化特定成语/习语/梗
        self.idioms = {
            'zh': self._load_idioms('zh'),
            'en': self._load_idioms('en')
        }
        
        logger.info("文化语境适配器初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        default_config = {
            'enable_idiom_translation': True,
            'preserve_original_names': True,
            'emotion_adaptation_level': 0.7,  # 0-1，值越高转换越强烈
            'preserve_hashtags': True,
            'adapt_sentence_length': True
        }
        
        if config_path:
            try:
                config_loader = ConfigLoader()
                user_config = config_loader.load(config_path)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        
        return default_config
    
    def _load_expression_map(self, direction: str) -> Dict[str, str]:
        """加载表达方式映射
        
        Args:
            direction: 映射方向，'zh_to_en' 或 'en_to_zh'
            
        Returns:
            表达映射字典
        """
        # 基础映射，可从文件扩展
        if direction == 'zh_to_en':
            base_map = {
                '我爱你': 'I love you',
                '辛苦了': 'Thank you for your hard work',
                '加油': 'You can do it',
                '不好意思': 'I\'m sorry',
                '随便': 'Whatever you prefer',
                '慢用': 'Enjoy your meal',
                '考虑一下': 'I\'ll think about it (likely no)',
                '还行吧': 'It\'s pretty good actually',
                '一般般': 'It\'s not that great',
                '可以的': 'That\'s excellent',
                '看起来不错': 'This is amazing',
                '有缘再见': 'Goodbye forever',
                '下次一定': 'I probably won\'t do it',
                '差不多了': 'It\'s basically perfect now'
            }
        else:  # en_to_zh
            base_map = {
                'I love you': '我爱你',
                'Thank you': '谢谢',
                'You can do it': '加油',
                'I\'m sorry': '对不起',
                'Whatever': '随便吧',
                'Enjoy your meal': '慢用',
                'I\'ll think about it': '我考虑一下',
                'It\'s pretty good': '还行吧',
                'It\'s not great': '一般般',
                'That\'s excellent': '可以的',
                'This is amazing': '看起来不错',
                'Goodbye': '再见',
                'I promise I\'ll do it next time': '下次一定',
                'It\'s perfect now': '差不多了'
            }
        
        # 尝试从文件加载更多映射
        try:
            data_dir = Path(__file__).parent.parent.parent / 'data' / 'adaptation'
            file_path = data_dir / f'{direction}_expressions.json'
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    additional_map = json.load(f)
                base_map.update(additional_map)
                logger.info(f"从{file_path}加载了{len(additional_map)}个表达映射")
        except Exception as e:
            logger.warning(f"加载表达映射文件失败: {e}")
        
        return base_map
    
    def _load_idioms(self, language: str) -> Dict[str, Dict]:
        """加载特定语言的成语/习语数据
        
        Args:
            language: 语言代码 'zh' 或 'en'
            
        Returns:
            成语字典，包含成语及其解释和使用场景
        """
        default_idioms = {
            'zh': {
                '一箭双雕': {
                    'literal': 'one arrow, two vultures',
                    'meaning': 'kill two birds with one stone',
                    'contexts': ['efficiency', 'strategy']
                },
                '狐假虎威': {
                    'literal': 'the fox borrows the tiger\'s power',
                    'meaning': 'bully others by flaunting powerful connections',
                    'contexts': ['deception', 'power']
                },
                '水到渠成': {
                    'literal': 'when water flows, a channel is formed',
                    'meaning': 'things will naturally happen when conditions are right',
                    'contexts': ['patience', 'natural development']
                },
                '守株待兔': {
                    'literal': 'guard a tree stump waiting for rabbits',
                    'meaning': 'wait passively for opportunities',
                    'contexts': ['passivity', 'luck']
                }
            },
            'en': {
                'kill two birds with one stone': {
                    'meaning': 'achieve two goals with one action',
                    'zh_equivalent': '一箭双雕',
                    'contexts': ['efficiency', 'strategy']
                },
                'the ball is in your court': {
                    'meaning': 'it\'s your turn to take action',
                    'zh_equivalent': '该你表态了',
                    'contexts': ['responsibility', 'decision']
                },
                'break the ice': {
                    'meaning': 'overcome initial social awkwardness',
                    'zh_equivalent': '打破僵局',
                    'contexts': ['social', 'beginning']
                },
                'barking up the wrong tree': {
                    'meaning': 'pursuing a mistaken or misguided line of thought or course of action',
                    'zh_equivalent': '走错路了',
                    'contexts': ['mistake', 'misunderstanding']
                }
            }
        }
        
        # 尝试从文件加载完整成语库
        try:
            data_dir = Path(__file__).parent.parent.parent / 'data' / 'adaptation'
            file_path = data_dir / f'{language}_idioms.json'
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    idiom_data = json.load(f)
                logger.info(f"从{file_path}加载了{len(idiom_data)}个{language}成语/习语")
                return idiom_data
        except Exception as e:
            logger.warning(f"加载成语文件失败: {e}，使用内置成语库")
        
        return default_idioms.get(language, {})
    
    def adapt_expression(self, text: str, target_lang: Optional[str] = None) -> str:
        """根据目标语言文化调整表达方式
        
        Args:
            text: 原始文本
            target_lang: 目标语言，默认None时自动检测并转换为另一种语言
            
        Returns:
            调整后的文本
        """
        if not text.strip():
            return text
            
        # 自动检测语言
        source_lang = detect_language(text)
        
        # 如果没有指定目标语言，则自动转换为另一种语言
        if target_lang is None:
            target_lang = 'en' if source_lang == 'zh' else 'zh'
        
        # 如果源语言和目标语言相同，则无需转换
        if source_lang == target_lang:
            return text
            
        # 确定转换方向
        direction = f"{source_lang}_to_{target_lang}"
        
        # 选择相应的表达映射
        expression_map = self.expression_maps.get(direction, {})
        
        # 应用表达方式映射
        adapted_text = self._apply_expression_mapping(text, expression_map)
        
        # 调整情感表达强度
        adapted_text = self._adapt_emotion_intensity(adapted_text, source_lang, target_lang)
        
        # 调整句式长度和复杂度
        if self.config.get('adapt_sentence_length', True):
            adapted_text = self._adapt_sentence_structure(adapted_text, target_lang)
        
        return adapted_text
    
    def _apply_expression_mapping(self, text: str, expression_map: Dict[str, str]) -> str:
        """应用表达方式映射
        
        Args:
            text: 原始文本
            expression_map: 表达映射字典
            
        Returns:
            应用映射后的文本
        """
        result = text
        
        # 按长度排序确保优先替换长短语
        sorted_expressions = sorted(expression_map.keys(), key=len, reverse=True)
        
        for expr in sorted_expressions:
            if expr in result:
                result = result.replace(expr, expression_map[expr])
        
        return result
    
    def _adapt_emotion_intensity(self, text: str, source_lang: str, target_lang: str) -> str:
        """调整情感表达强度
        
        中文往往含蓄表达，西方往往直接表达
        
        Args:
            text: 原始文本
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            调整情感强度后的文本
        """
        adaptation_level = self.config.get('emotion_adaptation_level', 0.7)
        
        # 中文转英文：情感表达更直接
        if source_lang == 'zh' and target_lang == 'en':
            # 使用情感映射器增强情感表达
            return self.emotion_mapper.enhance_intensity(text, adaptation_level)
        
        # 英文转中文：情感表达更含蓄
        elif source_lang == 'en' and target_lang == 'zh':
            # 使用情感映射器降低情感表达
            return self.emotion_mapper.reduce_intensity(text, adaptation_level)
        
        return text
    
    def _adapt_sentence_structure(self, text: str, target_lang: str) -> str:
        """调整句式长度和复杂度
        
        英文偏好短句直接表达，中文偏好复杂句式和修饰
        
        Args:
            text: 原始文本
            target_lang: 目标语言
            
        Returns:
            调整句式后的文本
        """
        sentences = re.split(r'([.!?。！？])', text)
        result = []
        
        for i in range(0, len(sentences), 2):
            if i+1 < len(sentences):
                sent = sentences[i] + sentences[i+1]
            else:
                sent = sentences[i]
            
            # 对于英文目标，简化句式
            if target_lang == 'en' and len(sent) > 40:
                # 简单处理：根据逗号分割成更短的句子
                parts = sent.split(',')
                if len(parts) > 2:
                    new_sent = '. '.join(part.strip() for part in parts)
                    sent = new_sent
            
            # 对于中文目标，增加修饰词
            elif target_lang == 'zh' and 5 < len(sent) < 15:
                # 简单示例：在短句中增加一些修饰词
                modifiers = ['其实', '确实', '当然', '或许', '大概']
                if not any(m in sent for m in modifiers) and not sent.startswith(('我', '你', '他', '她', '我们')):
                    import random
                    sent = random.choice(modifiers) + '，' + sent
            
            result.append(sent)
        
        return ''.join(result)
    
    def _chinese_express(self, text: str) -> str:
        """将文本转换为中文表达方式
        
        Args:
            text: 原始文本
            
        Returns:
            中文化表达的文本
        """
        # 1. 替换直接的情感表达为更含蓄的表达
        text = re.sub(r'I love you', '我很喜欢你', text, flags=re.IGNORECASE)
        text = re.sub(r'I hate', '我不太喜欢', text, flags=re.IGNORECASE)
        text = re.sub(r'amazing!', '还不错', text, flags=re.IGNORECASE)
        text = re.sub(r'terrible!', '不太好', text, flags=re.IGNORECASE)
        
        # 2. 替换西方习语为中文习语
        text = re.sub(r'kill two birds with one stone', '一举两得', text, flags=re.IGNORECASE)
        text = re.sub(r'piece of cake', '小菜一碟', text, flags=re.IGNORECASE)
        
        # 3. 增加礼貌性词汇和谦虚表达
        text = re.sub(r'I know', '我觉得', text, flags=re.IGNORECASE)
        text = re.sub(r'definitely', '可能', text, flags=re.IGNORECASE)
        text = re.sub(r'absolutely', '或许', text, flags=re.IGNORECASE)
        
        # 4. 应用成语和流行表达
        for en_idiom, data in self.idioms['en'].items():
            if en_idiom.lower() in text.lower() and 'zh_equivalent' in data:
                text = re.sub(re.escape(en_idiom), data['zh_equivalent'], text, flags=re.IGNORECASE)
        
        return text
    
    def _western_express(self, text: str) -> str:
        """将文本转换为西方表达方式
        
        Args:
            text: 原始文本
            
        Returns:
            西化表达的文本
        """
        # 1. 替换含蓄的情感表达为更直接的表达
        text = re.sub(r'我很喜欢你', 'I love you', text)
        text = re.sub(r'不太喜欢', 'I don\'t like', text)
        text = re.sub(r'还不错', 'amazing!', text)
        text = re.sub(r'不太好', 'terrible!', text)
        
        # 2. 替换中文习语为西方习语
        text = re.sub(r'一举两得', 'kill two birds with one stone', text)
        text = re.sub(r'小菜一碟', 'piece of cake', text)
        
        # 3. 增加直接表达和自信陈述
        text = re.sub(r'我觉得', 'I know', text)
        text = re.sub(r'可能', 'definitely', text)
        text = re.sub(r'或许', 'absolutely', text)
        
        # 4. 应用西方成语和流行表达
        for zh_idiom, data in self.idioms['zh'].items():
            if zh_idiom in text and 'literal' in data:
                text = text.replace(zh_idiom, data['meaning'])
        
        return text
    
    def localize_cultural_references(self, text: str, source_lang: str, target_lang: str) -> str:
        """本地化文化参考
        
        Args:
            text: 原始文本
            source_lang: 源语言
            target_lang: 目标语言
            
        Returns:
            本地化后的文本
        """
        # 实现文化参考的本地化转换
        # 例如将中国节日参考转换为西方等价物，或相反
        cultural_references = {
            'zh_to_en': {
                '春节': 'Chinese New Year',
                '中秋节': 'Mid-Autumn Festival',
                '国庆': 'National Day',
                '高考': 'college entrance examination',
                '小龙虾': 'crayfish',
                '火锅': 'hot pot',
                '广场舞': 'public square dancing',
                '抖音': 'TikTok',
                '微信': 'WeChat',
                '支付宝': 'Alipay'
            },
            'en_to_zh': {
                'Christmas': '圣诞节',
                'Thanksgiving': '感恩节',
                'Independence Day': '独立日',
                'SAT': '美国高考',
                'hamburger': '汉堡',
                'pizza': '披萨',
                'Twitter': '推特',
                'Facebook': '脸书',
                'Instagram': '照片墙',
                'PayPal': '贝宝'
            }
        }
        
        direction = f"{source_lang}_to_{target_lang}"
        references = cultural_references.get(direction, {})
        
        for original, localized in references.items():
            text = re.sub(r'\b' + re.escape(original) + r'\b', localized, text, flags=re.IGNORECASE)
        
        return text


# 导出类
__all__ = ['CultureAdapter'] 