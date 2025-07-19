#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全回退机制

当版本适配失败时，提供安全回退机制，确保导出过程不会中断。
主要功能：
1. 监测版本适配错误
2. 生成基础模板作为回退选项
3. 记录错误并通知用户
"""

import os
import sys
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Union, Tuple
from datetime import datetime

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.exporters.node_compat import validate_version_compatibility, get_version_specification
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)

# 设置日志记录器
logger = get_logger("version_fallback")

class VersionCompatibilityError(Exception):
    """版本兼容性错误异常类"""
    def __init__(self, message: str, version: str, issues: list = None):
        self.message = message
        self.version = version
        self.issues = issues or []
        super().__init__(self.message)

def safe_export(xml_content, target_version):
    """版本适配失败时回退到基准模板
    
    Args:
        xml_content: XML内容或ElementTree对象
        target_version: 目标版本
        
    Returns:
        处理后的XML内容
    """
    try:
        return version_specific_export(xml_content, target_version)
    except VersionCompatibilityError:
        logger.error(f"版本适配失败，启用基准模板")
        return generate_base_template(xml_content)

def version_specific_export(xml_content, target_version):
    """根据特定版本进行导出处理
    
    Args:
        xml_content: XML内容或ElementTree对象
        target_version: 目标版本
        
    Returns:
        处理后的XML内容
        
    Raises:
        VersionCompatibilityError: 当版本不兼容时抛出
    """
    # 解析XML内容
    if isinstance(xml_content, str):
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML解析错误: {e}")
            raise VersionCompatibilityError(f"XML解析错误: {e}", target_version)
    elif isinstance(xml_content, ET.Element):
        root = xml_content
    else:
        logger.error("不支持的XML内容类型")
        raise VersionCompatibilityError("不支持的XML内容类型", target_version)
    
    # 验证版本兼容性
    is_compatible, issues = validate_version_compatibility(root, target_version)
    
    if not is_compatible:
        error_msg = f"项目与版本 {target_version} 不兼容"
        logger.error(f"{error_msg}: {', '.join(issues)}")
        raise VersionCompatibilityError(error_msg, target_version, issues)
    
    # 获取版本规格
    version_spec = get_version_specification(target_version)
    if not version_spec:
        logger.warning(f"未找到版本 {target_version} 的规格，使用默认规格")
    
    # 执行版本特定的转换处理
    # 这里可以添加更多的处理逻辑...
    
    # 返回处理后的XML内容
    return ET.tostring(root, encoding='utf-8').decode('utf-8')

def generate_base_template(xml_content):
    """生成基础模板
    
    根据原始XML内容生成一个基础模板，确保最低限度的功能可用
    
    Args:
        xml_content: 原始XML内容或ElementTree对象
        
    Returns:
        基础模板XML内容
    """
    try:
        # 解析XML内容
        if isinstance(xml_content, str):
            try:
                root = ET.fromstring(xml_content)
            except ET.ParseError:
                # 如果无法解析，创建一个基本的XML结构
                root = ET.Element("project")
                info = ET.SubElement(root, "info")
                metadata = ET.SubElement(info, "metadata")
                ET.SubElement(metadata, "title").text = "项目"
                ET.SubElement(metadata, "creator").text = "VisionAI-ClipsMaster"
                project_settings = ET.SubElement(info, "project_settings")
                resolution = ET.SubElement(project_settings, "resolution")
                resolution.set("width", "1920")
                resolution.set("height", "1080")
                ET.SubElement(project_settings, "frame_rate").text = "30"
                ET.SubElement(root, "resources")
                timeline = ET.SubElement(root, "timeline")
                timeline.set("id", "main_timeline")
                timeline.set("duration", "00:00:00.000")
        elif isinstance(xml_content, ET.Element):
            root = xml_content
        else:
            # 创建一个基本的XML结构
            root = ET.Element("project")
            info = ET.SubElement(root, "info")
            metadata = ET.SubElement(info, "metadata")
            ET.SubElement(metadata, "title").text = "项目"
            ET.SubElement(metadata, "creator").text = "VisionAI-ClipsMaster"
            project_settings = ET.SubElement(info, "project_settings")
            resolution = ET.SubElement(project_settings, "resolution")
            resolution.set("width", "1920")
            resolution.set("height", "1080")
            ET.SubElement(project_settings, "frame_rate").text = "30"
            ET.SubElement(root, "resources")
            timeline = ET.SubElement(root, "timeline")
            timeline.set("id", "main_timeline")
            timeline.set("duration", "00:00:00.000")
        
        # 确保基本结构存在
        info = root.find("info")
        if info is None:
            info = ET.SubElement(root, "info")
        
        metadata = info.find("metadata")
        if metadata is None:
            metadata = ET.SubElement(info, "metadata")
        
        title = metadata.find("title")
        if title is None:
            ET.SubElement(metadata, "title").text = "项目"
        
        creator = metadata.find("creator")
        if creator is None:
            ET.SubElement(metadata, "creator").text = "VisionAI-ClipsMaster"
        
        project_settings = info.find("project_settings")
        if project_settings is None:
            project_settings = ET.SubElement(info, "project_settings")
        
        resolution = project_settings.find("resolution")
        if resolution is None:
            resolution = ET.SubElement(project_settings, "resolution")
            resolution.set("width", "1920")
            resolution.set("height", "1080")
        
        frame_rate = project_settings.find("frame_rate")
        if frame_rate is None:
            ET.SubElement(project_settings, "frame_rate").text = "30"
        
        resources = root.find("resources")
        if resources is None:
            ET.SubElement(root, "resources")
        
        timeline = root.find("timeline")
        if timeline is None:
            timeline = ET.SubElement(root, "timeline")
            timeline.set("id", "main_timeline")
            timeline.set("duration", "00:00:00.000")
        
        logger.info("已生成基础模板")
        
        # 返回处理后的XML内容
        return ET.tostring(root, encoding='utf-8').decode('utf-8')
    
    except Exception as e:
        logger.error(f"生成基础模板时出错: {e}")
        # 如果所有处理都失败，返回一个最小的有效XML
        minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <info>
    <metadata>
      <title>基础项目</title>
      <creator>VisionAI-ClipsMaster</creator>
    </metadata>
    <project_settings>
      <resolution width="1920" height="1080"/>
      <frame_rate>30</frame_rate>
    </project_settings>
  </info>
  <resources/>
  <timeline id="main_timeline" duration="00:00:00.000"/>
</project>
"""
        return minimal_xml

def get_fallback_templates():
    """获取可用的回退模板列表
    
    Returns:
        Dict[str, str]: 模板名称和文件路径的字典
    """
    templates_dir = os.path.join(root_dir, 'templates')
    templates = {}
    
    if os.path.exists(templates_dir):
        for filename in os.listdir(templates_dir):
            if filename.endswith('.xml'):
                template_name = os.path.splitext(filename)[0]
                templates[template_name] = os.path.join(templates_dir, filename)
    
    return templates

def load_template(template_name):
    """加载指定的模板
    
    Args:
        template_name: 模板名称
        
    Returns:
        str: 模板内容，如果找不到则返回None
    """
    templates = get_fallback_templates()
    
    if template_name in templates:
        try:
            with open(templates[template_name], 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"加载模板 {template_name} 时出错: {e}")
    
    return None

def generate_error_report(error, xml_content=None):
    """生成错误报告
    
    Args:
        error: 错误对象
        xml_content: 可选的XML内容
        
    Returns:
        Dict: 错误报告
    """
    report = {
        'error_type': type(error).__name__,
        'message': str(error),
        'timestamp': datetime.now().isoformat(),
    }
    
    if isinstance(error, VersionCompatibilityError):
        report['version'] = error.version
        report['issues'] = error.issues
    
    if xml_content:
        # 只保存XML头部以减少报告大小
        if isinstance(xml_content, str):
            report['xml_preview'] = xml_content[:500] + '...' if len(xml_content) > 500 else xml_content
        elif isinstance(xml_content, ET.Element):
            xml_str = ET.tostring(xml_content, encoding='utf-8').decode('utf-8')
            report['xml_preview'] = xml_str[:500] + '...' if len(xml_str) > 500 else xml_str
    
    return report

if __name__ == "__main__":
    # 测试代码
    test_xml = """<?xml version="1.0" encoding="UTF-8"?>
<project>
  <info>
    <metadata>
      <title>测试项目</title>
    </metadata>
    <project_settings>
      <resolution width="3840" height="2160"/>
    </project_settings>
  </info>
  <resources/>
  <timeline id="main_timeline"/>
</project>
"""
    
    print("测试安全导出功能...")
    try:
        result = safe_export(test_xml, "2.0.0")
        print("安全导出成功")
    except Exception as e:
        print(f"测试失败: {e}") 