#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 用户自定义法律文本处理模块

此模块允许用户定义自己的法律文本替换规则，可用于：
1. 替换默认法律声明中的特定内容（如公司名称、版权年份）
2. 自定义完整的法律声明模板
3. 使用变量插值功能动态生成内容
4. 保存和加载自定义规则

支持的变量示例：
- {company_name} - 公司名称
- {app_name} - 应用名称 
- {current_year} - 当前年份
- {author} - 作者名称
- {contact_email} - 联系邮箱
"""

import os
import re
import json
import logging
import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

try:
    from src.utils.log_handler import get_logger
    logger = get_logger("custom_legal")
except ImportError:
    # 简易日志设置
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("custom_legal")

# 默认用户配置目录
USER_CONFIG_DIR = Path.home() / ".visionai_clips"
DEFAULT_CUSTOM_CONFIG = USER_CONFIG_DIR / "custom_legal_rules.json"


def apply_custom_rules(text: str, user_config: Dict[str, Any]) -> str:
    """
    应用用户自定义替换规则

    Args:
        text: 原始文本内容
        user_config: 用户配置字典，包含替换规则

    Returns:
        str: 应用规则后的文本
    """
    if not text or not user_config:
        return text

    result = text
    
    # 1. 应用简单替换规则
    for key, value in user_config.get("simple_replacements", {}).items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    
    # 2. 应用正则表达式替换规则
    for pattern, replacement in user_config.get("regex_replacements", {}).items():
        try:
            result = re.sub(pattern, replacement, result)
        except re.error as e:
            logger.error(f"正则表达式替换错误: {str(e)}, 模式: {pattern}")
    
    # 3. 应用动态变量（如当前日期等）
    dynamic_vars = _get_dynamic_variables()
    for key, value in dynamic_vars.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            result = result.replace(placeholder, str(value))
    
    # 4. 应用完整替换（如果配置中完全匹配了原始文本）
    full_replacements = user_config.get("full_replacements", {})
    if text in full_replacements:
        result = full_replacements[text]
    
    # 5. 应用模板（如果指定了模板名称）
    template_name = user_config.get("active_template")
    templates = user_config.get("templates", {})
    if template_name and template_name in templates:
        template = templates[template_name]
        for pattern, replacement in template.items():
            if pattern in result:
                result = result.replace(pattern, replacement)
    
    return result


def _get_dynamic_variables() -> Dict[str, str]:
    """
    获取动态变量值，例如当前日期

    Returns:
        Dict[str, str]: 变量名和值的字典
    """
    now = datetime.datetime.now()
    return {
        "current_year": str(now.year),
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "timestamp": now.strftime("%Y%m%d%H%M%S"),
    }


def load_user_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载用户自定义配置

    Args:
        config_path: 配置文件路径，默认为用户目录下的配置文件

    Returns:
        Dict[str, Any]: 用户配置字典
    """
    # 确定配置文件路径
    if config_path is None:
        config_path = DEFAULT_CUSTOM_CONFIG
    
    # 确保配置目录存在
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 如果配置文件不存在，创建默认配置
    if not os.path.exists(config_path):
        default_config = _create_default_config()
        save_user_config(default_config, config_path)
        return default_config
    
    # 读取配置文件
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            logger.info(f"已加载用户自定义规则: {config_path}")
            return user_config
    except Exception as e:
        logger.error(f"加载用户配置失败: {str(e)}")
        # 返回默认配置
        return _create_default_config()


def save_user_config(user_config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    保存用户自定义配置

    Args:
        user_config: 用户配置字典
        config_path: 配置文件路径，默认为用户目录下的配置文件

    Returns:
        bool: 是否成功保存
    """
    if config_path is None:
        config_path = DEFAULT_CUSTOM_CONFIG
    
    # 确保配置目录存在
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(user_config, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存用户自定义规则: {config_path}")
        return True
    except Exception as e:
        logger.error(f"保存用户配置失败: {str(e)}")
        return False


def _create_default_config() -> Dict[str, Any]:
    """
    创建默认用户配置

    Returns:
        Dict[str, Any]: 默认配置字典
    """
    return {
        "simple_replacements": {
            "company_name": "我的公司",
            "app_name": "VisionAI-ClipsMaster",
            "author": "AI视频创作者",
            "contact_email": "support@example.com"
        },
        "regex_replacements": {
            "版权所有\\s*©\\s*\\d{4}": f"版权所有 © {datetime.datetime.now().year}",
            "Copyright\\s*©\\s*\\d{4}": f"Copyright © {datetime.datetime.now().year}"
        },
        "full_replacements": {
            "AI Generated Content by ClipsMaster v1.0": "由{company_name}提供的AI生成内容",
            "本视频仅用于技术演示，不代表任何观点。内容由AI生成，可能存在不准确之处。": "本内容由{company_name}的AI系统生成，仅供参考，不代表{company_name}官方观点。"
        },
        "templates": {
            "default": {
                "ClipsMaster AI": "{company_name} AI",
                "仅用于技术演示": "仅供参考，请勿用于商业目的"
            },
            "commercial": {
                "ClipsMaster AI": "{company_name}",
                "仅用于技术演示": "保留所有权利，未经授权不得使用"
            }
        },
        "active_template": "default"
    }


def apply_to_legal_injector(injector, user_config: Optional[Dict[str, Any]] = None):
    """
    将用户自定义规则应用到法律注入器

    Args:
        injector: LegalInjector实例
        user_config: 用户配置，如果为None则自动加载
    """
    if user_config is None:
        user_config = load_user_config()
    
    # 适配注入器的默认声明
    if hasattr(injector, 'DEFAULT_COPYRIGHT'):
        injector.DEFAULT_COPYRIGHT = apply_custom_rules(injector.DEFAULT_COPYRIGHT, user_config)
    
    if hasattr(injector, 'DEFAULT_DISCLAIMER'):
        injector.DEFAULT_DISCLAIMER = apply_custom_rules(injector.DEFAULT_DISCLAIMER, user_config)


def create_user_template(template_name: str, rules: Dict[str, str], 
                        user_config: Optional[Dict[str, Any]] = None,
                        set_active: bool = True) -> Dict[str, Any]:
    """
    创建新的用户自定义模板

    Args:
        template_name: 模板名称
        rules: 替换规则字典
        user_config: 用户配置，如果为None则自动加载
        set_active: 是否将新模板设为活动模板

    Returns:
        Dict[str, Any]: 更新后的用户配置
    """
    if user_config is None:
        user_config = load_user_config()
    
    # 确保模板部分存在
    if "templates" not in user_config:
        user_config["templates"] = {}
    
    # 添加或更新模板
    user_config["templates"][template_name] = rules
    
    # 如果需要，设置为活动模板
    if set_active:
        user_config["active_template"] = template_name
    
    # 保存配置
    save_user_config(user_config)
    
    return user_config


def batch_process_legal_text(texts: List[str], user_config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    批量处理多个法律文本

    Args:
        texts: 要处理的文本列表
        user_config: 用户配置，如果为None则自动加载

    Returns:
        List[str]: 处理后的文本列表
    """
    if user_config is None:
        user_config = load_user_config()
    
    return [apply_custom_rules(text, user_config) for text in texts]


def get_user_variables(user_config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    """
    获取当前可用的所有用户变量

    Args:
        user_config: 用户配置，如果为None则自动加载

    Returns:
        Dict[str, str]: 变量名和值的字典
    """
    if user_config is None:
        user_config = load_user_config()
    
    # 合并简单替换规则和动态变量
    variables = {}
    variables.update(user_config.get("simple_replacements", {}))
    variables.update(_get_dynamic_variables())
    
    return variables


def apply_custom_legal(content: str, content_type: str = "text", 
                      user_config: Optional[Dict[str, Any]] = None) -> str:
    """
    综合处理法律内容的简便函数

    Args:
        content: 原始内容
        content_type: 内容类型 ("text", "xml", "json", "srt")
        user_config: 用户配置，如果为None则自动加载

    Returns:
        str: 处理后的内容
    """
    if user_config is None:
        user_config = load_user_config()
    
    # 对特定类型内容进行特殊处理
    if content_type == "xml":
        # XML内容可能需要处理CDATA和特殊字符
        return _process_xml_content(content, user_config)
    elif content_type == "json":
        # JSON内容需要解析和重新序列化
        return _process_json_content(content, user_config)
    elif content_type == "srt":
        # SRT字幕可能需要特殊处理
        return _process_srt_content(content, user_config)
    else:
        # 普通文本直接应用规则
        return apply_custom_rules(content, user_config)


def _process_xml_content(xml_content: str, user_config: Dict[str, Any]) -> str:
    """处理XML内容中的法律文本"""
    try:
        import xml.etree.ElementTree as ET
        
        # 正则表达式替换法律相关XML节点内容
        patterns = [
            (r'<copyright>(.*?)</copyright>', lambda m: f'<copyright>{apply_custom_rules(m.group(1), user_config)}</copyright>'),
            (r'<disclaimer>(.*?)</disclaimer>', lambda m: f'<disclaimer>{apply_custom_rules(m.group(1), user_config)}</disclaimer>'),
            (r'<legal>(.*?)</legal>', lambda m: f'<legal>{apply_custom_rules(m.group(1), user_config)}</legal>')
        ]
        
        result = xml_content
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.DOTALL)
        
        return result
    except Exception as e:
        logger.error(f"处理XML内容时出错: {str(e)}")
        return xml_content


def _process_json_content(json_content: str, user_config: Dict[str, Any]) -> str:
    """处理JSON内容中的法律文本"""
    try:
        data = json.loads(json_content)
        
        # 处理可能包含法律文本的字段
        legal_fields = ["copyright", "disclaimer", "legal", "terms", "attribution"]
        
        def process_obj(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in legal_fields and isinstance(value, str):
                        obj[key] = apply_custom_rules(value, user_config)
                    elif isinstance(value, (dict, list)):
                        process_obj(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        process_obj(item)
        
        process_obj(data)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"处理JSON内容时出错: {str(e)}")
        return json_content


def _process_srt_content(srt_content: str, user_config: Dict[str, Any]) -> str:
    """处理SRT字幕内容中的法律文本"""
    try:
        lines = srt_content.split('\n')
        result_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 空行直接添加
            if not line.strip():
                result_lines.append(line)
                i += 1
                continue
            
            # 如果是数字，可能是字幕编号
            if line.strip().isdigit():
                result_lines.append(line)
                i += 1
                
                # 如果下一行是时间码
                if i < len(lines) and '-->' in lines[i]:
                    result_lines.append(lines[i])
                    i += 1
                    
                    # 接下来的行是字幕内容，直到空行或下一个编号
                    subtitle_content = []
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                        subtitle_content.append(lines[i])
                        i += 1
                    
                    # 检查字幕内容是否包含法律文本
                    subtitle_text = '\n'.join(subtitle_content)
                    if any(term in subtitle_text.lower() for term in ['copyright', 'disclaimer', '版权', '声明', '免责']):
                        # 处理法律文本
                        processed_text = apply_custom_rules(subtitle_text, user_config)
                        result_lines.extend(processed_text.split('\n'))
                    else:
                        # 不是法律文本，保持原样
                        result_lines.extend(subtitle_content)
            else:
                # 其他行直接添加
                result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
    except Exception as e:
        logger.error(f"处理SRT内容时出错: {str(e)}")
        return srt_content


# 直接使用的简便函数，当其他模块导入时直接可用
def apply_direct(text: str, company_name: str, **kwargs) -> str:
    """
    直接替换文本中的变量（无需加载配置文件）

    Args:
        text: 原始文本
        company_name: 公司名称
        **kwargs: 其他替换变量

    Returns:
        str: 替换变量后的文本
    """
    # 创建简单的配置字典
    config = {
        "simple_replacements": {
            "company_name": company_name,
            **kwargs
        }
    }
    
    return apply_custom_rules(text, config)


if __name__ == "__main__":
    # 测试代码
    test_text = "AI Generated Content by {company_name} v{version}"
    user_config = load_user_config()
    
    print("原始文本:", test_text)
    print("处理后文本:", apply_custom_rules(test_text, user_config))
    
    # 测试XML处理
    test_xml = """<project>
<meta>
    <copyright>Copyright © 2023 by ClipsMaster AI</copyright>
    <disclaimer>本视频仅用于技术演示，不代表任何观点。</disclaimer>
</meta>
</project>"""
    
    print("\n处理XML:")
    print(apply_custom_legal(test_xml, "xml")) 