import yaml
import os
from typing import Dict
from loguru import logger

def load_culture_rules(config_path: str = "configs/culture_rules.yaml") -> Dict:
    """加载文化表达转换规则"""
    if not os.path.exists(config_path):
        logger.warning(f"文化规则配置文件不存在: {config_path}")
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载文化规则失败: {e}")
        return {}

def adapt_culture(text: str, target_lang: str, config_path: str = "configs/culture_rules.yaml") -> str:
    """根据目标语言进行文化表达适配"""
    rules = load_culture_rules(config_path)
    if target_lang == 'zh':
        mapping = rules.get('en_to_zh', {})
        for k, v in mapping.items():
            text = text.replace(k, v)
    else:
        mapping = rules.get('zh_to_en', {})
        for k, v in mapping.items():
            text = text.replace(k, v)
    return text 