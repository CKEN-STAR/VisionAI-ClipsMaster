"""
VisionAI-ClipsMaster 多语言实体识别引擎

此模块实现了多语言实体识别功能，支持中英文环境下的实体提取。
可识别的实体类型包括：
- PERSON: 人物
- LOC/GPE: 地点/地理政治实体
- ORG: 组织机构
- TIME/DATE: 时间/日期
- EVENT: 事件
- PRODUCT: 产品
等

使用了spaCy的预训练模型，支持语言动态切换。
"""

import os
import re
import json
from typing import Dict, List, Optional, Union, Set, Tuple
from pathlib import Path
import importlib.util
from loguru import logger

# 检测spaCy是否已安装
try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Doc, Token, Span
    SPACY_AVAILABLE = True
except ImportError:
    logger.warning("spaCy未安装，将使用备用正则表达式模式进行实体识别")
    SPACY_AVAILABLE = False

# 定义实体类型映射，确保中英文模型的一致性
ENTITY_TYPE_MAPPING = {
    # 中文模型实体类型
    "PERSON": "PERSON",       # 人物
    "LOC": "LOCATION",        # 地点
    "GPE": "LOCATION",        # 地理政治实体，映射为地点
    "ORG": "ORGANIZATION",    # 组织
    "DATE": "DATE",           # 日期
    "TIME": "TIME",           # 时间
    "EVENT": "EVENT",         # 事件
    "PRODUCT": "PRODUCT",     # 产品
    "WORK_OF_ART": "WORK_OF_ART",  # 艺术作品
    # 英文模型可能有的额外实体类型
    "FAC": "LOCATION",        # 设施，映射为地点
    "NORP": "GROUP",          # 国籍/宗教/政治团体
    "MONEY": "QUANTITY",      # 货币
    "QUANTITY": "QUANTITY",   # 数量
    "CARDINAL": "QUANTITY",   # 基数
    "PERCENT": "QUANTITY",    # 百分比
    "ORDINAL": "QUANTITY",    # 序数
    "LANGUAGE": "MISC",       # 语言
    "LAW": "MISC",            # 法律
}

# 备用正则表达式模式，当spaCy不可用时使用
FALLBACK_PATTERNS = {
    "zh": {
        "PERSON": r'[\u4e00-\u9fff]{1,2}(?:先生|女士|老师|教授|医生|同志|博士)',  # 中文人名+称谓
        "LOCATION": r'(?:[\u4e00-\u9fff]{2,6}(?:省|市|县|区|镇|村|街道|路|大道))|(?:北京|上海|天津|重庆|香港|澳门)',  # 中文地名
        "ORGANIZATION": r'(?:[\u4e00-\u9fff]{2,10}(?:公司|集团|企业|工厂|学院|大学|医院|部门|中心))|(?:腾讯|阿里巴巴|华为|百度)',  # 中文组织
        "TIME": r'(?:\d{1,2}[点时]\d{1,2}分(?:\d{1,2}秒)?)|(?:上午|下午|晚上|凌晨)(?:\d{1,2}[点时](?:\d{1,2}分)?)?',  # 中文时间
        "DATE": r'(?:\d{4}年)?(?:\d{1,2}月)?(?:\d{1,2}[日号])?(?:上午|下午)?|(?:今天|明天|昨天|前天|后天)',  # 中文日期
        "EVENT": r'[\u4e00-\u9fff]{2,8}(?:大会|节日|会议|典礼|庆典|仪式|赛事)',  # 中文事件
        "PRODUCT": r'[\u4e00-\u9fff]{1,6}(?:[0-9A-Za-z]+)?(?:手机|电脑|产品|设备|装置)'  # 中文产品
    },
    "en": {
        "PERSON": r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)+\b',  # 英文人名
        "LOCATION": r'\b(?:[A-Z][a-z]+(?:,\s[A-Z][a-z]+)?|[A-Z]{2,})\b',  # 英文地名
        "ORGANIZATION": r'\b(?:[A-Z][a-z]*(?:\s[A-Z][a-z]*)*\s(?:Inc\.|Corp\.|Ltd\.|LLC|Company|Organization|Association|University|College))|(?:Google|Amazon|Microsoft|Apple|Facebook)\b',  # 英文组织
        "TIME": r'\b(?:\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?)\b',  # 英文时间
        "DATE": r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{1,2}(?:,\s\d{4})?\b|\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',  # 英文日期
        "EVENT": r'\b(?:[A-Z][a-z]+\s)*(?:Conference|Festival|Meeting|Ceremony|Celebration|Award|Summit|Olympics)\b',  # 英文事件
        "PRODUCT": r'\b(?:iPhone|iPad|Mac|Windows|Android|Galaxy|Surface|Pixel)(?:\s[A-Za-z0-9]+)*\b'  # 英文产品
    }
}

class PolyglotNER:
    """多语言实体识别器，支持中英文，使用spaCy模型"""
    
    def __init__(self, load_models: bool = True, cache_dir: Optional[str] = None):
        """
        初始化多语言实体识别器
        
        Args:
            load_models: 是否立即加载模型，False则延迟加载
            cache_dir: 模型缓存目录，默认为None（使用spaCy默认目录）
        """
        self.models = {}
        self.cache_dir = cache_dir
        self.available_languages = ["zh", "en"]
        self.model_names = {
            "zh": "zh_core_web_trf",  # 中文模型
            "en": "en_core_web_trf"   # 英文模型
        }
        self.loaded_models = set()
        
        # 记录实体类型映射
        self.entity_mapping = ENTITY_TYPE_MAPPING
        
        # 如果指定立即加载模型，且spaCy可用
        if load_models and SPACY_AVAILABLE:
            self._load_models()
    
    def _load_models(self) -> None:
        """加载可用的spaCy模型"""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy不可用，将使用备用方法")
            return
        
        for lang in self.available_languages:
            try:
                # 首先检查模型是否已经下载
                model_name = self.model_names[lang]
                if not spacy.util.is_package(model_name):
                    # 记录未找到模型的信息
                    logger.warning(f"{lang}语言模型({model_name})未安装，跳过加载")
                    continue
                
                # 加载模型
                self.models[lang] = spacy.load(model_name)
                self.loaded_models.add(lang)
                logger.info(f"成功加载{lang}语言模型: {model_name}")
            except Exception as e:
                logger.error(f"加载{lang}语言模型失败: {str(e)}")
    
    def _load_model_for_language(self, lang: str) -> bool:
        """按需加载特定语言的模型
        
        Args:
            lang: 语言代码('zh'或'en')
            
        Returns:
            bool: 是否成功加载模型
        """
        if not SPACY_AVAILABLE:
            return False
            
        if lang in self.loaded_models:
            return True
            
        try:
            model_name = self.model_names.get(lang)
            if not model_name or not spacy.util.is_package(model_name):
                logger.warning(f"{lang}语言模型({model_name})未安装")
                return False
                
            self.models[lang] = spacy.load(model_name)
            self.loaded_models.add(lang)
            logger.info(f"成功加载{lang}语言模型: {model_name}")
            return True
        except Exception as e:
            logger.error(f"加载{lang}语言模型失败: {str(e)}")
            return False
    
    def recognize(self, text: str, lang: str) -> Dict[str, List[str]]:
        """
        识别文本中的命名实体
        
        Args:
            text: 要分析的文本
            lang: 语言代码 ('zh'或'en')
            
        Returns:
            Dict[str, List[str]]: 按实体类型分类的实体列表
        """
        # 检查语言是否支持
        if lang not in self.available_languages:
            logger.warning(f"不支持的语言: {lang}，将使用英文作为默认语言")
            lang = "en"
        
        # 如果spaCy可用，尝试使用spaCy模型
        if SPACY_AVAILABLE:
            # 如果模型未加载，尝试加载
            if lang not in self.loaded_models:
                if not self._load_model_for_language(lang):
                    return self._fallback_recognition(text, lang)
            
            try:
                # 使用spaCy识别实体
                doc = self.models[lang](text)
                
                # 按类型整理实体
                entities = {}
                for ent in doc.ents:
                    # 映射实体类型
                    normalized_type = self.entity_mapping.get(ent.label_, "MISC")
                    
                    # 添加到对应类型的列表
                    if normalized_type not in entities:
                        entities[normalized_type] = []
                    
                    # 确保不重复添加
                    if ent.text not in entities[normalized_type]:
                        entities[normalized_type].append(ent.text)
                
                return entities
            except Exception as e:
                logger.error(f"spaCy实体识别失败: {str(e)}")
                return self._fallback_recognition(text, lang)
        else:
            # spaCy不可用，使用备用方法
            return self._fallback_recognition(text, lang)
    
    def _fallback_recognition(self, text: str, lang: str) -> Dict[str, List[str]]:
        """
        使用正则表达式备用方法识别实体
        
        Args:
            text: 要分析的文本
            lang: 语言代码 ('zh'或'en')
            
        Returns:
            Dict[str, List[str]]: 按实体类型分类的实体列表
        """
        entities = {}
        
        # 使用对应语言的正则表达式模式
        patterns = FALLBACK_PATTERNS.get(lang, FALLBACK_PATTERNS["en"])
        
        # 对每种实体类型应用正则表达式
        for entity_type, pattern in patterns.items():
            # 映射实体类型
            normalized_type = self.entity_mapping.get(entity_type, "MISC")
            
            # 查找所有匹配项
            matches = re.findall(pattern, text)
            
            if matches:
                if normalized_type not in entities:
                    entities[normalized_type] = []
                
                # 添加非重复实体
                for match in matches:
                    if match.strip() and match not in entities[normalized_type]:
                        entities[normalized_type].append(match)
        
        # 对于中文文本，尝试提取更精确的人名
        if lang == "zh":
            # 尝试匹配常见的中文姓氏+名字模式
            chinese_names = re.findall(r'[\u4e00-\u9fff]{1,2}[\u4e00-\u9fff]{1,2}', text)
            for name in chinese_names:
                # 如果名字不是已经识别的实体的一部分，考虑添加
                is_part_of_existing = False
                for entity_list in entities.values():
                    for entity in entity_list:
                        if name in entity and name != entity:
                            is_part_of_existing = True
                            break
                    if is_part_of_existing:
                        break
                
                # 如果不是现有实体的一部分，添加为人物
                if not is_part_of_existing and len(name) <= 3:  # 中文名通常不超过3个字
                    if "PERSON" not in entities:
                        entities["PERSON"] = []
                    if name not in entities["PERSON"]:
                        entities["PERSON"].append(name)
        
        return entities
    
    def extract_specific_entities(self, text: str, lang: str, entity_types: List[str]) -> List[str]:
        """
        提取指定类型的实体
        
        Args:
            text: 要分析的文本
            lang: 语言代码 ('zh'或'en')
            entity_types: 要提取的实体类型列表
            
        Returns:
            List[str]: 提取的实体列表
        """
        # 获取所有实体
        all_entities = self.recognize(text, lang)
        
        # 筛选指定类型的实体
        result = []
        for entity_type in entity_types:
            normalized_type = self.entity_mapping.get(entity_type, entity_type)
            if normalized_type in all_entities:
                result.extend(all_entities[normalized_type])
        
        return result
    
    def is_model_available(self, lang: str) -> bool:
        """
        检查特定语言的模型是否可用
        
        Args:
            lang: 语言代码 ('zh'或'en')
            
        Returns:
            bool: 模型是否可用
        """
        # 如果spaCy不可用，始终返回False
        if not SPACY_AVAILABLE:
            return False
        
        # 如果模型已加载，返回True
        if lang in self.loaded_models:
            return True
        
        # 检查模型是否已安装但未加载
        model_name = self.model_names.get(lang)
        if model_name and spacy.util.is_package(model_name):
            return True
        
        return False
    
    def get_loaded_model_info(self) -> Dict[str, Dict]:
        """
        获取已加载模型的信息
        
        Returns:
            Dict[str, Dict]: 按语言代码索引的模型信息
        """
        info = {}
        
        for lang in self.loaded_models:
            if lang in self.models:
                model = self.models[lang]
                info[lang] = {
                    "name": model.meta.get("name", "unknown"),
                    "version": model.meta.get("version", "unknown"),
                    "description": model.meta.get("description", ""),
                    "pipeline": list(model.pipe_names),
                    "entity_types": [self.entity_mapping.get(label, label) 
                                    for label in model.get_pipe("ner").labels]
                }
        
        return info


# 单例模式，全局实体识别器
_global_ner = None

def get_global_ner() -> PolyglotNER:
    """
    获取全局PolyglotNER实例（单例模式）
    
    Returns:
        PolyglotNER: 实体识别器实例
    """
    global _global_ner
    if _global_ner is None:
        _global_ner = PolyglotNER(load_models=False)  # 默认不立即加载模型，按需加载
    return _global_ner


def extract_entities(text: str, lang: str = None, entity_types: List[str] = None) -> List[str]:
    """
    从文本中提取实体的便捷函数
    
    Args:
        text: 要分析的文本
        lang: 语言代码，如果为None则自动检测
        entity_types: 要提取的实体类型列表，如果为None则提取所有类型
        
    Returns:
        List[str]: 提取的实体列表
    """
    # 如果未指定语言，尝试自动检测
    if lang is None:
        # 简单的语言检测：包含中文字符则判定为中文
        if re.search(r'[\u4e00-\u9fff]', text):
            lang = "zh"
        else:
            lang = "en"
    
    ner = get_global_ner()
    
    if entity_types:
        return ner.extract_specific_entities(text, lang, entity_types)
    else:
        # 提取所有类型的实体并扁平化
        all_entities = ner.recognize(text, lang)
        return [entity for sublist in all_entities.values() for entity in sublist]


if __name__ == "__main__":
    # 示例代码
    test_texts = {
        "zh": "昨天，张三和李四在北京人民大会堂参加了会议。他们讨论了中国移动与华为公司的最新合作项目。",
        "en": "Yesterday, John Smith and Mary Johnson attended a meeting at the White House in Washington DC. They discussed the latest partnership project between Apple Inc. and Microsoft Corporation."
    }
    
    ner = PolyglotNER(load_models=False)
    
    for lang, text in test_texts.items():
        print(f"\n===== {lang} 测试 =====")
        print(f"文本: {text}")
        entities = ner.recognize(text, lang)
        print("识别的实体:")
        for entity_type, entity_list in entities.items():
            print(f"  {entity_type}: {', '.join(entity_list)}") 