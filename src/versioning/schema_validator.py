#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模式验证器模块

提供根据XSD模式验证项目文件的功能。
"""

import os
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Tuple

# 配置日志
logger = logging.getLogger(__name__)

# 默认模式文件目录
DEFAULT_SCHEMA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "configs"
)

class SchemaValidator:
    """模式验证器类"""
    
    def __init__(self, schema_dir: str = None):
        """
        初始化模式验证器
        
        Args:
            schema_dir: XSD模式文件目录，默认为configs目录
        """
        self.schema_dir = schema_dir or DEFAULT_SCHEMA_DIR
        
        # 尝试导入依赖
        try:
            from lxml import etree
            self.etree = etree
            self.lxml_available = True
        except ImportError:
            self.lxml_available = False
            logger.warning("lxml 模块不可用，将使用有限的验证功能")
            
        # 导入版本特征模块
        try:
            from .version_features import get_version_features
            self.version_features = get_version_features()
        except ImportError:
            from src.versioning.version_features import get_version_features
            self.version_features = get_version_features()
    
    def validate_file(self, file_path: str, schema_file: str = None) -> Dict[str, Any]:
        """
        验证XML文件是否符合模式
        
        Args:
            file_path: 要验证的XML文件路径
            schema_file: XSD模式文件路径，如果为None则根据文件自动检测
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        if not os.path.exists(file_path):
            return {
                "valid": False,
                "error": f"文件不存在: {file_path}"
            }
            
        # 如果未指定模式文件，尝试自动检测
        if not schema_file:
            schema_file = self._auto_detect_schema(file_path)
            if not schema_file:
                return {
                    "valid": False,
                    "error": "无法确定适用的XSD模式文件"
                }
        
        # 确保模式文件存在
        if not os.path.exists(schema_file):
            return {
                "valid": False,
                "error": f"模式文件不存在: {schema_file}"
            }
            
        # 检查是否可以使用lxml
        if not self.lxml_available:
            return {
                "valid": False,
                "error": "lxml模块不可用，无法执行严格的XSD验证",
                "schema_file": schema_file
            }
            
        try:
            # 解析XSD模式
            with open(schema_file, 'rb') as f:
                schema_doc = self.etree.parse(f)
                schema = self.etree.XMLSchema(schema_doc)
            
            # 解析XML文件
            with open(file_path, 'rb') as f:
                doc = self.etree.parse(f)
            
            # 验证文档
            valid = schema.validate(doc)
            
            if valid:
                return {
                    "valid": True,
                    "schema_file": schema_file,
                    "message": "文件验证通过"
                }
            else:
                # 获取错误信息
                errors = []
                for error in schema.error_log:
                    errors.append({
                        "line": error.line,
                        "column": error.column,
                        "message": error.message,
                        "domain": error.domain_name
                    })
                
                return {
                    "valid": False,
                    "schema_file": schema_file,
                    "errors": errors,
                    "message": "文件验证失败"
                }
        except Exception as e:
            logger.error(f"验证文件时出错: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "schema_file": schema_file
            }
    
    def _auto_detect_schema(self, file_path: str) -> Optional[str]:
        """
        自动检测适用的XSD模式文件
        
        Args:
            file_path: XML文件路径
            
        Returns:
            Optional[str]: 模式文件路径，如果无法检测则返回None
        """
        try:
            # 导入版本检测器
            try:
                from .version_detector import detect_version
            except ImportError:
                from src.versioning.version_detector import detect_version
                
            # 检测文件版本
            version_info = detect_version(file_path)
            
            # 只有剪映格式才能使用我们的XSD模式
            if version_info.get('format_type') != 'jianying':
                return None
                
            # 获取版本号
            version = version_info.get('version')
            if version == 'unknown':
                return None
                
            # 获取对应的模式文件
            schema_name = self.version_features.get_schema_for_version(version)
            if not schema_name:
                return None
                
            # 构建完整路径
            schema_path = os.path.join(self.schema_dir, schema_name)
            
            # 确保文件存在
            if os.path.exists(schema_path):
                return schema_path
                
            return None
        except Exception as e:
            logger.error(f"自动检测模式文件时出错: {str(e)}")
            return None
    
    def get_schema_description(self, schema_file: str) -> Dict[str, Any]:
        """
        获取XSD模式文件的描述信息
        
        Args:
            schema_file: XSD模式文件路径
            
        Returns:
            Dict[str, Any]: 模式描述信息
        """
        try:
            schema_path = os.path.join(self.schema_dir, schema_file) if not os.path.isabs(schema_file) else schema_file
            
            if not os.path.exists(schema_path):
                return {
                    "error": f"模式文件不存在: {schema_path}"
                }
                
            # 解析XSD文件
            tree = ET.parse(schema_path)
            root = tree.getroot()
            
            # 获取命名空间
            ns = root.tag.split('}')[0] + '}' if '}' in root.tag else ''
            
            # 获取注释信息
            documentation = None
            for annotation in root.findall(f'{ns}annotation'):
                for doc in annotation.findall(f'{ns}documentation'):
                    documentation = doc.text.strip() if doc.text else None
                    break
                if documentation:
                    break
            
            # 获取根元素定义
            root_elem_name = None
            for element in root.findall(f'{ns}element'):
                root_elem_name = element.get('name')
                break
            
            # 获取文件名和版本信息
            file_name = os.path.basename(schema_path)
            version = None
            if file_name.startswith('jianying_v'):
                version = file_name.split('_v')[1].split('.')[0]
            
            # 返回描述信息
            return {
                "file_name": file_name,
                "version": version,
                "root_element": root_elem_name,
                "documentation": documentation,
                "supports_version": self._find_versions_for_schema(file_name)
            }
        except Exception as e:
            logger.error(f"获取模式描述时出错: {str(e)}")
            return {
                "error": str(e)
            }
    
    def _find_versions_for_schema(self, schema_file: str) -> List[str]:
        """
        查找使用指定模式文件的所有版本
        
        Args:
            schema_file: 模式文件名
            
        Returns:
            List[str]: 版本列表
        """
        versions = []
        
        for version_info in self.version_features.get_all_versions():
            if version_info.get('schema') == schema_file:
                versions.append(version_info.get('version'))
        
        return versions
    
    def list_all_schemas(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的XSD模式文件
        
        Returns:
            List[Dict[str, Any]]: 模式文件信息列表
        """
        schemas = []
        
        try:
            for file_name in os.listdir(self.schema_dir):
                if file_name.endswith('.xsd'):
                    schema_path = os.path.join(self.schema_dir, file_name)
                    schema_info = self.get_schema_description(schema_path)
                    schema_info['file_path'] = schema_path
                    schemas.append(schema_info)
        except Exception as e:
            logger.error(f"列出模式文件时出错: {str(e)}")
        
        return schemas


def validate_xml_file(file_path: str, schema_file: str = None) -> Dict[str, Any]:
    """
    验证XML文件是否符合模式
    
    Args:
        file_path: 要验证的XML文件路径
        schema_file: XSD模式文件路径，如果为None则根据文件自动检测
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    validator = SchemaValidator()
    return validator.validate_file(file_path, schema_file)


def get_schema_info(schema_file: str) -> Dict[str, Any]:
    """
    获取XSD模式文件的描述信息
    
    Args:
        schema_file: XSD模式文件路径
        
    Returns:
        Dict[str, Any]: 模式描述信息
    """
    validator = SchemaValidator()
    return validator.get_schema_description(schema_file)


def list_schemas() -> List[Dict[str, Any]]:
    """
    列出所有可用的XSD模式文件
    
    Returns:
        List[Dict[str, Any]]: 模式文件信息列表
    """
    validator = SchemaValidator()
    return validator.list_all_schemas()


if __name__ == "__main__":
    # 简单测试
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'validate' and len(sys.argv) > 2:
            file_path = sys.argv[2]
            schema_file = sys.argv[3] if len(sys.argv) > 3 else None
            
            result = validate_xml_file(file_path, schema_file)
            print("验证结果:")
            for key, value in result.items():
                if key == 'errors':
                    print("- 错误信息:")
                    for err in value:
                        print(f"  - 行 {err['line']}, 列 {err['column']}: {err['message']}")
                else:
                    print(f"- {key}: {value}")
        
        elif command == 'info' and len(sys.argv) > 2:
            schema_file = sys.argv[2]
            
            info = get_schema_info(schema_file)
            print("模式信息:")
            for key, value in info.items():
                print(f"- {key}: {value}")
        
        elif command == 'list':
            schemas = list_schemas()
            print("可用模式文件:")
            for schema in schemas:
                print(f"- {schema['file_name']} (版本: {schema['version']})")
                if 'documentation' in schema and schema['documentation']:
                    print(f"  描述: {schema['documentation']}")
                if 'supports_version' in schema and schema['supports_version']:
                    print(f"  支持版本: {', '.join(schema['supports_version'])}")
        
        else:
            print("未知命令")
    else:
        print("用法: python schema_validator.py <command> [args]")
        print("命令:")
        print("  validate <file_path> [schema_file] - 验证XML文件")
        print("  info <schema_file> - 获取模式信息")
        print("  list - 列出所有可用的模式文件") 