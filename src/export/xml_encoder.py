#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML编码器模块

处理XML特殊字符转义，确保生成的XML内容符合标准规范。
主要功能：
1. 字符串特殊字符转义
2. XML属性值处理
3. CDATA内容处理
"""

import re
import os
import sys
from typing import Dict, List, Any, Optional, Union

def sanitize_xml(text: str) -> str:
    """处理XML保留字符
    
    将XML中的特殊字符转换为对应的实体引用
    
    Args:
        text: 原始文本
        
    Returns:
        str: 处理后的文本
    """
    if text is None:
        return ""
    
    # 处理XML保留字符
    # & 必须首先处理，否则会影响后续的实体引用
    result = text.replace("&", "&amp;")  # 替换&为对应的实体引用
    result = result.replace("<", "&lt;")  # 替换<为对应的实体引用
    result = result.replace(">", "&gt;")  # 替换>为对应的实体引用
    result = result.replace("\"", "&quot;")  # 替换"为对应的实体引用
    result = result.replace("'", "&apos;")  # 替换'为对应的实体引用
    
    return result

def encode_xml_attribute(value: str) -> str:
    """编码XML属性值
    
    处理XML属性值中的特殊字符
    
    Args:
        value: 属性值
        
    Returns:
        str: 处理后的属性值
    """
    # 属性值需要确保所有特殊字符被正确转义
    return sanitize_xml(str(value))

def encode_xml_content(content: str) -> str:
    """编码XML内容文本
    
    处理XML元素内容中的特殊字符
    
    Args:
        content: 内容文本
        
    Returns:
        str: 处理后的内容文本
    """
    # 内容文本需要确保所有特殊字符被正确转义
    return sanitize_xml(str(content))

def wrap_cdata(content: str) -> str:
    """使用CDATA包装内容
    
    对于包含大量特殊字符的内容，使用CDATA包装避免大量转义
    
    Args:
        content: 原始内容
        
    Returns:
        str: CDATA包装后的内容
    """
    # 确保内容不包含CDATA结束标记
    if "]]>" in content:
        # 将CDATA结束标记分割，避免冲突
        content = content.replace("]]>", "]]]]><![CDATA[>")
    
    # 使用CDATA包装
    return f"<![CDATA[{content}]]>"

def escape_control_chars(text: str) -> str:
    """转义控制字符
    
    转义文本中的XML控制字符
    
    Args:
        text: 原始文本
        
    Returns:
        str: 转义后的文本
    """
    # 转义XML控制字符 (ASCII 0-31，除了9, 10, 13)
    result = ""
    for char in text:
        code = ord(char)
        if (code < 32 and code not in (9, 10, 13)) or code == 0xFFFE or code == 0xFFFF:
            # 使用XML字符引用替换无效字符
            result += f"&#x{code:04X};"
        else:
            result += char
    
    return result

def process_xml_string(xml_string: str) -> str:
    """处理XML字符串
    
    全面处理XML字符串，包括特殊字符处理
    
    Args:
        xml_string: 原始XML字符串
        
    Returns:
        str: 处理后的XML字符串
    """
    # 确保XML声明正确
    if not xml_string.strip().startswith("<?xml"):
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_string
    
    # 转义内容中的特殊字符
    content_pattern = r'>([^<]+)<'
    
    def escape_content(match):
        content = match.group(1)
        # 只有当内容不是纯空白时才进行处理
        if content.strip():
            return '>' + sanitize_xml(content) + '<'
        return match.group(0)
    
    # 处理标签之间的内容
    return re.sub(content_pattern, escape_content, xml_string)

def create_xml_element(tag: str, 
                      attributes: Optional[Dict[str, str]] = None, 
                      content: Optional[str] = None, 
                      use_cdata: bool = False) -> str:
    """创建XML元素
    
    生成包含标签、属性和内容的XML元素
    
    Args:
        tag: 标签名称
        attributes: 属性字典，默认为None
        content: 元素内容，默认为None
        use_cdata: 是否使用CDATA包装内容，默认为False
        
    Returns:
        str: 生成的XML元素
    """
    # 处理标签名，确保符合XML标准
    tag = tag.strip()
    if not re.match(r'^[a-zA-Z_][\w\-\.]*$', tag):
        raise ValueError(f"无效的XML标签名: '{tag}'")
    
    # 构建开始标签
    element = f"<{tag}"
    
    # 添加属性
    if attributes:
        for key, value in attributes.items():
            if key and value is not None:  # 确保键和值不为空
                # 编码属性值
                encoded_value = encode_xml_attribute(str(value))
                element += f' {key}="{encoded_value}"'
    
    # 处理内容
    if content is not None:
        element += ">"
        if use_cdata:
            # 使用CDATA包装内容
            element += wrap_cdata(content)
        else:
            # 编码内容
            element += encode_xml_content(str(content))
        
        # 添加结束标签
        element += f"</{tag}>"
    else:
        # 自闭合标签
        element += " />"
    
    return element

def normalize_file_path(file_path: str) -> str:
    """标准化文件路径用于XML
    
    确保文件路径符合XML格式要求，尤其是跨平台环境中
    
    Args:
        file_path: 原始文件路径
        
    Returns:
        str: 标准化后的文件路径
    """
    # 替换路径分隔符为正斜杠(适用于XML)
    normalized_path = file_path.replace('\\', '/')
    
    # 处理路径中的特殊字符
    normalized_path = sanitize_xml(normalized_path)
    
    # 处理URL编码(如果需要)
    # 这里可以根据实际需求添加URL编码
    
    return normalized_path 