import re
from typing import List, Set
from loguru import logger

# 可根据实际需求扩展为更复杂的NLP实体识别

def extract_entities(text: str) -> Set[str]:
    """抽取文本中的关键实体（人名、地名、专有名词等）"""
    # 简单示例：匹配中英文人名/专有名词（可用NLP库替换）
    zh_pattern = re.compile(r'[\u4e00-\u9fff]{2,4}')
    en_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b')
    entities = set(zh_pattern.findall(text)) | set(en_pattern.findall(text))
    return entities

def insert_entity(text: str, entity: str) -> str:
    """将缺失实体智能插入到文本合适位置（可根据上下文优化）"""
    # 简单策略：插入到文本末尾，避免破坏原有结构
    if text.endswith("\n"):
        return text + entity + "\n"
    else:
        return text + " " + entity

def align_context(origin_zh: str, origin_en: str, generated: str) -> str:
    """确保跨语言内容上下文连贯，补偿缺失实体"""
    try:
        zh_entities = extract_entities(origin_zh)
        en_entities = extract_entities(origin_en)
        all_entities = zh_entities.union(en_entities)
        for entity in all_entities:
            if entity not in generated:
                generated = insert_entity(generated, entity)
        return generated
    except Exception as e:
        logger.error(f"跨语言对齐补偿失败: {e}")
        return generated 