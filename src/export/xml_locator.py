#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
XML元数据节点定位器

专门处理XML文件中元数据节点的定位与处理，支持多种格式的项目文件，
如Premiere Pro、FCPXML、剪映等。

主要功能：
1. 定位元数据节点
2. 创建或修改元数据节点
3. 在不同XML格式间提供统一的元数据访问API
4. 支持批量元数据操作
"""

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime

# 添加项目根目录到路径，确保可以在不同环境下导入模块
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.log_handler import get_logger
    from src.export.xml_encoder import sanitize_xml, normalize_file_path
    from src.export.xml_builder import xml_to_string
except ImportError:
    # 尝试直接导入
    sys.path.append(str(current_dir.parent))
    try:
        from utils.log_handler import get_logger
        from export.xml_encoder import sanitize_xml, normalize_file_path
        from export.xml_builder import xml_to_string
    except ImportError:
        print("无法导入必要模块，确保当前目录结构正确。")
        # 简单日志替代
        import logging
        logging.basicConfig(level=logging.INFO)
        def get_logger(name):
            return logging.getLogger(name)

# 配置日志
logger = get_logger("xml_locator")


class XMLLocator:
    """XML元数据节点定位器类"""
    
    def __init__(self):
        """初始化XML元数据定位器"""
        self.logger = logger
        # 支持的XML格式和对应的元数据路径模式
        self.format_patterns = {
            "premiere": "./meta",
            "fcpxml": "./resources/format",
            "davinci": "./project/metadata",
            "jianying": "./info/metadata",
            "default": "./meta"
        }
    
    def find_meta_node(self, xml_root: ET.Element) -> Optional[ET.Element]:
        """
        定位或查找XML的元数据节点
        
        Args:
            xml_root: XML根元素
            
        Returns:
            Optional[ET.Element]: 找到的元数据节点，如果不存在则返回None
        """
        self.logger.debug("开始定位XML元数据节点")
        
        # 尝试各种格式的元数据路径模式
        for format_name, pattern in self.format_patterns.items():
            meta_node = xml_root.find(pattern)
            if meta_node is not None:
                self.logger.info(f"在'{format_name}'格式模式下找到元数据节点")
                return meta_node
                
        # 尝试在项目节点直接寻找
        meta_node = xml_root.find(".//meta")
        if meta_node is not None:
            self.logger.info("找到<meta>元数据节点")
            return meta_node
            
        # 尝试在项目中查找metadata节点
        meta_node = xml_root.find(".//metadata")
        if meta_node is not None:
            self.logger.info("找到<metadata>元数据节点")
            return meta_node
        
        self.logger.warning("未找到元数据节点")
        return None
    
    def create_meta_node(self, xml_root: ET.Element, format_type: str = "default") -> ET.Element:
        """
        创建元数据节点
        
        如果节点不存在，则创建一个新的元数据节点并返回；如果已存在，则直接返回现有节点
        
        Args:
            xml_root: XML根元素
            format_type: XML格式类型，如"premiere", "fcpxml"等
            
        Returns:
            ET.Element: 元数据节点
        """
        # 先尝试查找现有节点
        meta_node = self.find_meta_node(xml_root)
        if meta_node is not None:
            return meta_node
        
        self.logger.info(f"创建新的元数据节点，格式类型: {format_type}")
        
        # 根据不同格式创建节点
        if format_type == "premiere" or format_type == "default":
            # 在根节点下直接创建meta节点
            meta_node = ET.SubElement(xml_root, "meta")
        elif format_type == "fcpxml":
            # 在resources下创建format节点
            resources = xml_root.find("./resources")
            if resources is None:
                resources = ET.SubElement(xml_root, "resources")
            meta_node = ET.SubElement(resources, "format")
        elif format_type == "davinci":
            # DaVinci Resolve格式
            project = xml_root.find("./project")
            if project is None:
                project = ET.SubElement(xml_root, "project")
            meta_node = ET.SubElement(project, "metadata")
        elif format_type == "jianying":
            # 剪映格式
            info = xml_root.find("./info")
            if info is None:
                info = ET.SubElement(xml_root, "info")
            meta_node = ET.SubElement(info, "metadata")
        else:
            # 默认在根节点创建meta节点
            meta_node = ET.SubElement(xml_root, "meta")
        
        return meta_node
    
    def get_meta_attribute(self, xml_root: ET.Element, attribute_name: str) -> Optional[str]:
        """
        获取元数据节点中的指定属性值
        
        Args:
            xml_root: XML根元素
            attribute_name: 属性名称
            
        Returns:
            Optional[str]: 属性值，如果不存在则返回None
        """
        meta_node = self.find_meta_node(xml_root)
        if meta_node is None:
            self.logger.warning(f"未找到元数据节点，无法获取属性 '{attribute_name}'")
            return None
        
        # 尝试查找作为子元素的属性
        attr_elem = meta_node.find(f"./{attribute_name}")
        if attr_elem is not None and attr_elem.text:
            return attr_elem.text
        
        # 尝试查找作为XML属性的属性
        if attribute_name in meta_node.attrib:
            return meta_node.attrib[attribute_name]
        
        self.logger.debug(f"未找到属性 '{attribute_name}'")
        return None
    
    def set_meta_attribute(self, xml_root: ET.Element, attribute_name: str, 
                          attribute_value: str, format_type: str = "default") -> bool:
        """
        设置元数据节点中的指定属性值
        
        Args:
            xml_root: XML根元素
            attribute_name: 属性名称
            attribute_value: 属性值
            format_type: XML格式类型
            
        Returns:
            bool: 操作是否成功
        """
        # 确保有元数据节点
        meta_node = self.find_meta_node(xml_root)
        if meta_node is None:
            meta_node = self.create_meta_node(xml_root, format_type)
        
        if meta_node is None:
            self.logger.error(f"无法创建元数据节点，设置属性 '{attribute_name}' 失败")
            return False
        
        # 根据不同格式处理属性设置
        if format_type == "fcpxml":
            # FCPXML使用XML属性
            meta_node.set(attribute_name, attribute_value)
        elif format_type == "premiere" or format_type == "default":
            # Premiere使用子元素
            attr_elem = meta_node.find(f"./{attribute_name}")
            if attr_elem is not None:
                attr_elem.text = attribute_value
            else:
                attr_elem = ET.SubElement(meta_node, attribute_name)
                attr_elem.text = attribute_value
        else:
            # 默认使用子元素
            attr_elem = meta_node.find(f"./{attribute_name}")
            if attr_elem is not None:
                attr_elem.text = attribute_value
            else:
                attr_elem = ET.SubElement(meta_node, attribute_name)
                attr_elem.text = attribute_value
        
        self.logger.info(f"成功设置属性 '{attribute_name}' = '{attribute_value}'")
        return True
    
    def get_all_meta_attributes(self, xml_root: ET.Element) -> Dict[str, str]:
        """
        获取元数据节点中的所有属性
        
        Args:
            xml_root: XML根元素
            
        Returns:
            Dict[str, str]: 属性名称和值的字典
        """
        meta_node = self.find_meta_node(xml_root)
        if meta_node is None:
            self.logger.warning("未找到元数据节点，无法获取属性")
            return {}
        
        attributes = {}
        
        # 收集XML属性
        for key, value in meta_node.attrib.items():
            attributes[key] = value
        
        # 收集子元素作为属性
        for child in meta_node:
            if child.text:
                attributes[child.tag] = child.text
        
        return attributes
    
    def update_meta_attributes(self, xml_root: ET.Element, 
                              attributes: Dict[str, str], 
                              format_type: str = "default") -> bool:
        """
        批量更新元数据属性
        
        Args:
            xml_root: XML根元素
            attributes: 属性字典
            format_type: XML格式类型
            
        Returns:
            bool: 操作是否成功
        """
        success = True
        for attr_name, attr_value in attributes.items():
            if not self.set_meta_attribute(xml_root, attr_name, attr_value, format_type):
                success = False
        
        return success
    
    def remove_meta_attribute(self, xml_root: ET.Element, 
                             attribute_name: str) -> bool:
        """
        移除元数据节点中的指定属性
        
        Args:
            xml_root: XML根元素
            attribute_name: 属性名称
            
        Returns:
            bool: 操作是否成功
        """
        meta_node = self.find_meta_node(xml_root)
        if meta_node is None:
            self.logger.warning(f"未找到元数据节点，无法移除属性 '{attribute_name}'")
            return False
        
        # 尝试移除XML属性
        if attribute_name in meta_node.attrib:
            del meta_node.attrib[attribute_name]
            self.logger.info(f"已移除XML属性 '{attribute_name}'")
            return True
        
        # 尝试移除子元素
        attr_elem = meta_node.find(f"./{attribute_name}")
        if attr_elem is not None:
            meta_node.remove(attr_elem)
            self.logger.info(f"已移除子元素 '{attribute_name}'")
            return True
        
        self.logger.warning(f"属性 '{attribute_name}' 不存在，无需移除")
        return False
    
    def detect_xml_format(self, xml_root: ET.Element) -> str:
        """
        检测XML的格式类型
        
        Args:
            xml_root: XML根元素
            
        Returns:
            str: 检测到的格式类型
        """
        # 检查根节点名称
        root_tag = xml_root.tag
        
        if root_tag == "fcpxml" or xml_root.find(".//fcpxml") is not None:
            return "fcpxml"
        elif root_tag == "Project" or xml_root.find(".//Project") is not None:
            return "davinci"
        elif xml_root.find(".//jianying") is not None or xml_root.find(".//capcut") is not None:
            return "jianying"
        elif xml_root.find(".//project") is not None and xml_root.find(".//timeline") is not None:
            return "premiere"
        else:
            # 默认格式
            return "default"
    
    def check_has_meta(self, xml_root: ET.Element) -> bool:
        """
        检查XML是否包含元数据节点
        
        Args:
            xml_root: XML根元素
            
        Returns:
            bool: 是否包含元数据节点
        """
        return self.find_meta_node(xml_root) is not None
    
    def update_xml_meta(self, xml_string: str, 
                       attributes: Dict[str, str]) -> str:
        """
        更新XML字符串中的元数据
        
        Args:
            xml_string: XML字符串
            attributes: 要更新的属性字典
            
        Returns:
            str: 更新后的XML字符串
        """
        try:
            # 解析XML字符串
            root = ET.fromstring(xml_string)
            
            # 检测XML格式
            format_type = self.detect_xml_format(root)
            
            # 更新元数据
            self.update_meta_attributes(root, attributes, format_type)
            
            # 转换回字符串
            return xml_to_string(root)
        except Exception as e:
            self.logger.error(f"更新XML元数据失败: {str(e)}")
            return xml_string  # 返回原始字符串


# 提供便捷的静态方法接口

def find_meta_node(xml_root: ET.Element) -> Optional[ET.Element]:
    """
    定位XML的元数据节点
    
    Args:
        xml_root: XML根元素
        
    Returns:
        Optional[ET.Element]: 找到的元数据节点，如果不存在则返回None
    """
    locator = XMLLocator()
    return locator.find_meta_node(xml_root)


def find_meta_node_or_create(xml_root: ET.Element) -> ET.Element:
    """
    定位期望XML中的元数据节点，如果不存在则创建
    
    Args:
        xml_root: XML根元素
        
    Returns:
        ET.Element: 元数据节点（现有的或新创建的）
    """
    # 先尝试查找meta节点
    meta_node = xml_root.find("./meta")
    if meta_node is not None:
        return meta_node
    
    # 尝试查找project节点并添加meta
    project_node = xml_root.find("./project")
    if project_node is not None:
        meta_node = ET.Element("meta")
        project_node.insert(0, meta_node)
        return meta_node
    
    # 如果没有project节点，在根节点添加meta
    meta_node = ET.Element("meta")
    xml_root.insert(0, meta_node)
    return meta_node


def create_meta_node(xml_root: ET.Element, format_type: str = "default") -> ET.Element:
    """
    创建元数据节点
    
    Args:
        xml_root: XML根元素
        format_type: XML格式类型
        
    Returns:
        ET.Element: 创建的元数据节点
    """
    locator = XMLLocator()
    return locator.create_meta_node(xml_root, format_type)


def get_meta_attribute(xml_root: ET.Element, attribute_name: str) -> Optional[str]:
    """
    获取元数据属性
    
    Args:
        xml_root: XML根元素
        attribute_name: 属性名称
        
    Returns:
        Optional[str]: 属性值
    """
    locator = XMLLocator()
    return locator.get_meta_attribute(xml_root, attribute_name)


def set_meta_attribute(xml_root: ET.Element, attribute_name: str, 
                     attribute_value: str, format_type: str = "default") -> bool:
    """
    设置元数据属性
    
    Args:
        xml_root: XML根元素
        attribute_name: 属性名称
        attribute_value: 属性值
        format_type: XML格式类型
        
    Returns:
        bool: 操作是否成功
    """
    locator = XMLLocator()
    return locator.set_meta_attribute(xml_root, attribute_name, attribute_value, format_type)


def update_meta_attributes(xml_root: ET.Element, 
                          attributes: Dict[str, str], 
                          format_type: str = "default") -> bool:
    """
    批量更新元数据属性
    
    Args:
        xml_root: XML根元素
        attributes: 属性字典
        format_type: XML格式类型
        
    Returns:
        bool: 操作是否成功
    """
    locator = XMLLocator()
    return locator.update_meta_attributes(xml_root, attributes, format_type)


# 测试与示例代码
if __name__ == "__main__":
    # 创建测试XML
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <resources>
    <video id="video1" path="test.mp4"/>
  </resources>
  <timeline>
    <track type="video">
      <clip name="测试片段" resourceId="video1" start="0" duration="10"/>
    </track>
  </timeline>
</project>"""
    
    # 创建XML定位器
    locator = XMLLocator()
    
    # 解析XML字符串
    root = ET.fromstring(test_xml)
    
    # 测试创建元数据节点
    print("\n===== 测试创建元数据节点 =====")
    meta_node = locator.create_meta_node(root)
    print(f"元数据节点: {meta_node.tag}")
    
    # 测试设置属性
    print("\n===== 测试设置属性 =====")
    locator.set_meta_attribute(root, "copyright", "由VisionAI-ClipsMaster生成")
    locator.set_meta_attribute(root, "generator", "VisionAI-ClipsMaster v1.0")
    locator.set_meta_attribute(root, "created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 测试获取属性
    print("\n===== 测试获取属性 =====")
    copyright_text = locator.get_meta_attribute(root, "copyright")
    generator = locator.get_meta_attribute(root, "generator")
    print(f"版权信息: {copyright_text}")
    print(f"生成器: {generator}")
    
    # 测试获取所有属性
    print("\n===== 测试获取所有属性 =====")
    all_attrs = locator.get_all_meta_attributes(root)
    for name, value in all_attrs.items():
        print(f"{name}: {value}")
    
    # 测试更新XML字符串
    print("\n===== 测试更新XML字符串 =====")
    updated_xml = locator.update_xml_meta(test_xml, {
        "legal": "本内容由AI生成，仅用于技术演示",
        "version": "1.0.0",
        "app": "VisionAI-ClipsMaster"
    })
    print(updated_xml) 