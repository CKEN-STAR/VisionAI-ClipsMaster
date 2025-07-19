#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理器

负责加载、验证和管理配置文件。提供统一的配置访问接口，
确保配置项符合预定义的模式。
"""

import os
import sys
import yaml
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Tuple

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.config.env_adapter import adapt_for_environment
    # 添加迁移器导入
    from src.config.migrator import migrate_legacy_config, get_config_migrator, ConfigMigrationError, VersionNotSupportedError
    # 添加安全存储导入
    from src.config.secure_storage import (
        encrypt_sensitive_fields, 
        decrypt_sensitive_fields,
        secure_load_config, 
        secure_save_config,
        SecureStorage,
        ConfigSecurityError
    )
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def adapt_for_environment(config):
        # 导入失败时的简单实现
        return config
    
    # 导入失败时的简单迁移函数
    def migrate_legacy_config(config, old_ver, target_ver=None):
        return config
    
    def get_config_migrator():
        return None
    
    # 导入失败时的简单安全存储函数
    def encrypt_sensitive_fields(config, sensitive_paths=None, master_key=None, key_file=None):
        return config
    
    def decrypt_sensitive_fields(config, master_key=None, key_file=None):
        return config
    
    def secure_load_config(config_file, master_key=None, key_file=None):
        return {}
    
    def secure_save_config(config, config_file, sensitive_paths=None, master_key=None, key_file=None):
        return False
    
    class SecureStorage:
        pass
    
    class ConfigSecurityError(Exception):
        pass

# 设置日志记录器
logger = get_logger("config_manager")

class ConfigValidationError(Exception):
    """配置验证错误异常"""
    pass

class ConfigNotFoundError(Exception):
    """配置未找到错误异常"""
    pass

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径，默认为项目根目录的 configs 文件夹
        """
        self.config_dir = config_dir or os.path.join(root_dir, "configs")
        
        # 确保配置目录存在
        if not os.path.exists(self.config_dir):
            logger.warning(f"配置目录不存在: {self.config_dir}，将尝试创建")
            try:
                os.makedirs(self.config_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"创建配置目录失败: {str(e)}")
        
        # 存储配置模式
        self.schemas = {}
        
        # 存储已加载的配置
        self.configs = {
            "user": {},
            "system": {},
            "version": {},
            "export": {},
            "app": {}
        }
        
        # 加载配置模式
        self._load_config_schemas()
    
    def _load_config_schemas(self) -> None:
        """加载所有配置模式"""
        schema_path = os.path.join(self.config_dir, "config_schema.yaml")
        if not os.path.exists(schema_path):
            logger.warning(f"配置模式文件不存在: {schema_path}")
            return
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = yaml.safe_load(f)
                if "schemas" in schema_data:
                    self.schemas = schema_data["schemas"]
                    logger.info(f"成功加载配置模式: {len(self.schemas)} 个模式")
        except Exception as e:
            logger.error(f"加载配置模式失败: {str(e)}")
    
    def load_all_configs(self) -> None:
        """加载所有配置文件"""
        self.load_user_config()
        self.load_system_config()
        self.load_version_config()
        self.load_export_config()
    
    def load_user_config(self) -> Dict[str, Any]:
        """
        加载用户配置
        
        Returns:
            Dict[str, Any]: 用户配置字典
        """
        try:
            config_path = os.path.join(self.config_dir, "user_settings.yaml")
            if not os.path.exists(config_path):
                logger.warning(f"用户配置文件不存在: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                if "default_settings" in config_data:
                    self.configs["user"] = config_data["default_settings"]
                    logger.debug("成功加载用户配置")
                    return self.configs["user"]
        except Exception as e:
            logger.error(f"加载用户配置失败: {str(e)}")
        
        return {}
    
    def load_system_config(self) -> Dict[str, Any]:
        """
        加载系统配置
        
        Returns:
            Dict[str, Any]: 系统配置字典
        """
        try:
            config_path = os.path.join(self.config_dir, "system_settings.yaml")
            if not os.path.exists(config_path):
                logger.warning(f"系统配置文件不存在: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                if "default_settings" in config_data:
                    self.configs["system"] = config_data["default_settings"]
                    logger.debug("成功加载系统配置")
                    return self.configs["system"]
        except Exception as e:
            logger.error(f"加载系统配置失败: {str(e)}")
        
        return {}
    
    def load_version_config(self) -> Dict[str, Any]:
        """
        加载版本配置
        
        Returns:
            Dict[str, Any]: 版本配置字典
        """
        try:
            config_path = os.path.join(self.config_dir, "version_settings.yaml")
            if not os.path.exists(config_path):
                logger.warning(f"版本配置文件不存在: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
                # 加载默认设置
                if "default_settings" in config_data:
                    self.configs["version"] = config_data["default_settings"]
                
                # 加载版本定义
                if "version_definitions" in config_data:
                    self.configs["version"]["definitions"] = config_data["version_definitions"]
                
                # 加载迁移路径
                if "migration_paths" in config_data:
                    self.configs["version"]["migration_paths"] = config_data["migration_paths"]
                
                logger.debug("成功加载版本配置")
                return self.configs["version"]
        except Exception as e:
            logger.error(f"加载版本配置失败: {str(e)}")
        
        return {}
    
    def load_export_config(self) -> Dict[str, Any]:
        """
        加载导出配置
        
        Returns:
            Dict[str, Any]: 导出配置字典
        """
        try:
            config_path = os.path.join(self.config_dir, "export_settings.yaml")
            if not os.path.exists(config_path):
                logger.warning(f"导出配置文件不存在: {config_path}")
                return {}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
                # 加载默认设置
                if "default_settings" in config_data:
                    self.configs["export"] = config_data["default_settings"]
                
                # 加载预设
                if "export_presets" in config_data:
                    self.configs["export"]["presets"] = config_data["export_presets"]
                
                # 加载版本特定输出设置
                if "version_output_settings" in config_data:
                    self.configs["export"]["version_output_settings"] = config_data["version_output_settings"]
                
                logger.debug("成功加载导出配置")
                return self.configs["export"]
        except Exception as e:
            logger.error(f"加载导出配置失败: {str(e)}")
        
        return {}
    
    def get_config(self, config_type: str, key: Optional[str] = None) -> Any:
        """
        获取配置值
        
        Args:
            config_type: 配置类型，可选值: "user", "system", "version", "export"
            key: 配置键，如果不提供则返回整个配置字典
            
        Returns:
            Any: 配置值
            
        Raises:
            ConfigNotFoundError: 配置不存在时抛出
        """
        if config_type not in self.configs:
            raise ConfigNotFoundError(f"未知的配置类型: {config_type}")
        
        if not self.configs[config_type]:
            self._load_config_by_type(config_type)
        
        if key is None:
            return self.configs[config_type]
        
        if "." in key:
            # 处理嵌套键
            parts = key.split(".")
            value = self.configs[config_type]
            for part in parts:
                if part not in value:
                    raise ConfigNotFoundError(f"配置 {config_type}.{key} 不存在")
                value = value[part]
            return value
        
        if key not in self.configs[config_type]:
            raise ConfigNotFoundError(f"配置 {config_type}.{key} 不存在")
        
        return self.configs[config_type][key]
    
    def set_config(self, config_type: str, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            config_type: 配置类型，可选值: "user", "system", "version", "export"
            key: 配置键
            value: 配置值
            
        Raises:
            ConfigValidationError: 配置验证失败时抛出
        """
        if config_type not in self.configs:
            raise ConfigNotFoundError(f"未知的配置类型: {config_type}")
        
        if "." in key:
            # 处理嵌套键
            parts = key.split(".")
            config = self.configs[config_type]
            for i, part in enumerate(parts[:-1]):
                if part not in config:
                    config[part] = {}
                config = config[part]
            
            # 设置最终值
            config[parts[-1]] = value
        else:
            self.configs[config_type][key] = value
        
        # 保存配置
        self._save_config_by_type(config_type)
    
    def reset_config(self, config_type: str = None, key: str = None) -> None:
        """
        重置配置值为默认值
        
        Args:
            config_type: 配置类型，若未提供则重置所有配置
            key: 配置键，若未提供则重置指定类型的所有配置
            
        Raises:
            ConfigNotFoundError: 配置不存在时抛出
        """
        # 重置所有配置
        if config_type is None:
            self.configs = {
                "user": {},
                "system": {},
                "version": {},
                "export": {},
                "app": {}
            }
            self.load_all_configs()
            return
        
        # 重置特定类型的所有配置
        if config_type not in self.configs:
            raise ConfigNotFoundError(f"未知的配置类型: {config_type}")
        
        # 获取默认配置
        default_config = {}
        config_file = self._get_config_file_by_type(config_type)
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if config_data and "default_settings" in config_data:
                        default_config = config_data["default_settings"]
            except Exception as e:
                logger.error(f"加载默认配置失败: {str(e)}")
                return
        
        if key is None:
            # 重置整个配置类型
            # 1. 保存回文件恢复默认值（这是关键修复）
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump({"default_settings": default_config}, f, default_flow_style=False, allow_unicode=True)
            except Exception as e:
                logger.error(f"恢复默认配置失败: {str(e)}")
                return
            
            # 2. 清空当前配置
            self.configs[config_type] = {}
            
            # 3. 根据类型重新加载配置
            if config_type == "user":
                self.load_user_config()
            elif config_type == "system":
                self.load_system_config()
            elif config_type == "version":
                self.load_version_config()
            elif config_type == "export":
                self.load_export_config()
            return
        
        # 重置特定配置项
        # 处理嵌套键
        if "." in key:
            parts = key.split(".")
            current_config = self.configs[config_type]
            default_value = default_config
            
            # 查找默认值
            try:
                for part in parts:
                    default_value = default_value[part]
            except (KeyError, TypeError):
                logger.warning(f"未找到默认配置值: {config_type}.{key}")
                return
            
            # 设置为默认值
            current = current_config
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    return
                current = current[part]
            
            current[parts[-1]] = default_value
        else:
            # 简单键直接重置
            if key in default_config:
                self.configs[config_type][key] = default_config[key]
        
        # 保存配置
        self._save_config_by_type(config_type)
    
    def _load_config_by_type(self, config_type: str) -> None:
        """
        根据类型加载配置
        
        Args:
            config_type: 配置类型
        """
        config_file = self._get_config_file_by_type(config_type)
        if os.path.exists(config_file):
            try:
                # 使用带有安全加载和迁移功能的方法
                config_data = self.load_and_migrate_config(config_file)
                
                # 处理从整个配置文件中提取default_settings部分
                if config_data and isinstance(config_data, dict):
                    if "default_settings" in config_data:
                        # 存储提取的默认设置部分
                        self.configs[config_type] = config_data["default_settings"]
                    else:
                        # 如果没有default_settings节点，直接使用整个配置
                        self.configs[config_type] = config_data
                else:
                    # 处理空配置或非字典情况
                    self.configs[config_type] = config_data or {}
                
                logger.debug(f"成功加载配置: {config_type}")
            except Exception as e:
                logger.error(f"加载配置失败 {config_type}: {str(e)}")
        else:
            logger.warning(f"配置文件不存在: {config_file}")
    
    def _save_config_by_type(self, config_type: str) -> None:
        """根据类型保存配置"""
        config_file_map = {
            "user": "user_settings.yaml",
            "system": "system_settings.yaml",
            "version": "version_settings.yaml",
            "export": "export_settings.yaml"
        }
        
        if config_type not in config_file_map:
            logger.error(f"未知的配置类型: {config_type}")
            return
        
        config_path = os.path.join(self.config_dir, config_file_map[config_type])
        
        try:
            # 先加载原始文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 更新配置
            if "default_settings" in config_data:
                config_data["default_settings"] = self.configs[config_type]
            else:
                # 如果不存在默认设置，直接保存当前配置
                config_data = {"default_settings": self.configs[config_type]}
            
            # 识别敏感配置类型
            sensitive_config_types = ["user", "system"]
            
            # 对于敏感配置类型，使用安全存储
            if config_type in sensitive_config_types:
                # 确定敏感字段路径
                sensitive_paths = self._get_sensitive_paths_for_type(config_type)
                
                # 安全保存配置
                success = self.secure_save_config(config_data, config_path, sensitive_paths)
                if success:
                    logger.debug(f"成功安全保存{config_type}配置")
                    return
                # 如果安全保存失败，会继续尝试普通保存
            
            # 普通保存
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.debug(f"成功保存{config_type}配置")
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
    
    def _get_sensitive_paths_for_type(self, config_type: str) -> List[str]:
        """
        获取指定配置类型的敏感字段路径
        
        Args:
            config_type: 配置类型
            
        Returns:
            List[str]: 敏感字段路径列表
        """
        if config_type == "user":
            return [
                "default_settings.cloud.api_key",
                "default_settings.cloud.secret_key",
                "default_settings.cloud.access_token",
                "default_settings.auth.token",
                "default_settings.auth.secret"
            ]
        elif config_type == "system":
            return [
                "default_settings.database.password",
                "default_settings.service.credentials",
                "default_settings.api.key"
            ]
        else:
            return []
    
    def validate_config(self, config_type: str, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证配置是否符合模式
        
        Args:
            config_type: 配置类型
            config_data: 配置数据
            
        Returns:
            Tuple[bool, List[str]]: 是否有效，错误信息列表
        """
        if config_type not in self.schemas:
            return False, [f"未找到{config_type}的配置模式"]
        
        schema = self.schemas[config_type]
        errors = []
        
        # 验证必需字段
        if "required" in schema:
            for field in schema["required"]:
                if field not in config_data:
                    errors.append(f"缺少必需字段: {field}")
        
        # 验证字段类型
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in config_data:
                    value = config_data[field]
                    
                    # 验证类型
                    if "type" in field_schema:
                        expected_type = field_schema["type"]
                        if expected_type == "string" and not isinstance(value, str):
                            errors.append(f"字段 {field} 类型错误: 期望字符串，实际为 {type(value).__name__}")
                        elif expected_type == "integer" and not isinstance(value, int):
                            errors.append(f"字段 {field} 类型错误: 期望整数，实际为 {type(value).__name__}")
                        elif expected_type == "number" and not isinstance(value, (int, float)):
                            errors.append(f"字段 {field} 类型错误: 期望数字，实际为 {type(value).__name__}")
                        elif expected_type == "boolean" and not isinstance(value, bool):
                            errors.append(f"字段 {field} 类型错误: 期望布尔值，实际为 {type(value).__name__}")
                        elif expected_type == "array" and not isinstance(value, list):
                            errors.append(f"字段 {field} 类型错误: 期望数组，实际为 {type(value).__name__}")
                        elif expected_type == "object" and not isinstance(value, dict):
                            errors.append(f"字段 {field} 类型错误: 期望对象，实际为 {type(value).__name__}")
                    
                    # 验证枚举值
                    if "enum" in field_schema and value not in field_schema["enum"]:
                        errors.append(f"字段 {field} 值错误: {value} 不在允许的值范围内 {field_schema['enum']}")
                    
                    # 验证最小值
                    if "minimum" in field_schema and value < field_schema["minimum"]:
                        errors.append(f"字段 {field} 值错误: {value} 小于最小值 {field_schema['minimum']}")
                    
                    # 验证最大值
                    if "maximum" in field_schema and value > field_schema["maximum"]:
                        errors.append(f"字段 {field} 值错误: {value} 大于最大值 {field_schema['maximum']}")
        
        return len(errors) == 0, errors
    
    def get_version_definition(self, version: str) -> Dict[str, Any]:
        """
        获取指定版本的定义
        
        Args:
            version: 版本号
            
        Returns:
            Dict[str, Any]: 版本定义字典
            
        Raises:
            ConfigNotFoundError: 版本定义不存在时抛出
        """
        if "version" not in self.configs or not self.configs["version"]:
            self.load_version_config()
        
        if "definitions" not in self.configs["version"]:
            raise ConfigNotFoundError(f"版本定义不存在")
        
        if version not in self.configs["version"]["definitions"]:
            raise ConfigNotFoundError(f"版本 {version} 的定义不存在")
        
        return self.configs["version"]["definitions"][version]
    
    def get_compatible_versions(self, version: str) -> List[str]:
        """
        获取与指定版本兼容的版本列表
        
        Args:
            version: 版本号
            
        Returns:
            List[str]: 兼容的版本列表
        """
        try:
            version_def = self.get_version_definition(version)
            return version_def.get("compatible_with", [])
        except ConfigNotFoundError:
            return []
    
    def find_migration_path(self, source_version: str, target_version: str) -> List[str]:
        """
        查找从源版本到目标版本的迁移路径
        
        Args:
            source_version: 源版本
            target_version: 目标版本
            
        Returns:
            List[str]: 迁移路径（版本序列）
        """
        # 如果直接兼容，返回直接路径
        compatible_versions = self.get_compatible_versions(source_version)
        if target_version in compatible_versions:
            return [source_version, target_version]
        
        # 检查是否有预定义的迁移路径
        if "version" in self.configs and "migration_paths" in self.configs["version"]:
            path_key = f"{source_version}-{target_version}"
            if path_key in self.configs["version"]["migration_paths"]:
                return self.configs["version"]["migration_paths"][path_key]
        
        # 广度优先搜索找出可能的路径
        queue = [(source_version, [source_version])]
        visited = {source_version}
        
        while queue:
            current, path = queue.pop(0)
            compatible_versions = self.get_compatible_versions(current)
            
            for next_version in compatible_versions:
                if next_version == target_version:
                    return path + [target_version]
                if next_version not in visited:
                    visited.add(next_version)
                    queue.append((next_version, path + [next_version]))
        
        # 没有找到路径
        return []
    
    def get_export_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        获取导出预设
        
        Args:
            preset_name: 预设名称
            
        Returns:
            Dict[str, Any]: 预设配置
            
        Raises:
            ConfigNotFoundError: 预设不存在时抛出
        """
        if "export" not in self.configs or not self.configs["export"]:
            self.load_export_config()
        
        if "presets" not in self.configs["export"]:
            raise ConfigNotFoundError("导出预设不存在")
        
        for preset in self.configs["export"]["presets"]:
            if preset.get("name") == preset_name:
                return preset
        
        raise ConfigNotFoundError(f"导出预设 {preset_name} 不存在")
    
    def get_version_output_settings(self, version: str) -> Dict[str, Any]:
        """
        获取指定版本的输出设置
        
        Args:
            version: 版本号
            
        Returns:
            Dict[str, Any]: 输出设置
        """
        if "export" not in self.configs or not self.configs["export"]:
            self.load_export_config()
        
        if "version_output_settings" not in self.configs["export"]:
            return {}
        
        if version not in self.configs["export"]["version_output_settings"]:
            # 返回默认设置
            return {
                "max_resolution": "1080p",
                "max_frame_rate": 30,
                "codecs": ["h264"]
            }
        
        return self.configs["export"]["version_output_settings"][version]

    def _get_config_file_by_type(self, config_type: str) -> str:
        """
        获取指定类型的配置文件路径
        
        Args:
            config_type: 配置类型
            
        Returns:
            str: 配置文件路径
        """
        config_files = {
            "user": os.path.join(self.config_dir, "user_settings.yaml"),
            "system": os.path.join(self.config_dir, "system_settings.yaml"),
            "version": os.path.join(self.config_dir, "version_settings.yaml"),
            "export": os.path.join(self.config_dir, "export_settings.yaml"),
            "app": os.path.join(self.config_dir, "app_settings.yaml"),
            "model": os.path.join(self.config_dir, "model_config.yaml"),
            "storage": os.path.join(self.config_dir, "storage.json")
        }
        
        return config_files.get(config_type, "")

    def load_and_migrate_config(self, config_path: str, expected_version: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件并自动迁移到指定版本
        
        Args:
            config_path: 配置文件路径
            expected_version: 期望的配置版本，如果为None则使用当前默认版本
            
        Returns:
            Dict[str, Any]: 迁移后的配置
        """
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            return {}
        
        try:
            # 安全加载配置文件（自动解密敏感字段）
            config_data = self.secure_load_config(config_path)
            
            if not config_data:
                # 如果安全加载失败，尝试普通加载
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.endswith('.json'):
                        config_data = json.load(f)
                    elif config_path.endswith(('.yaml', '.yml')):
                        config_data = yaml.safe_load(f)
                    else:
                        logger.error(f"不支持的配置文件格式: {config_path}")
                        return {}
            
            # 检查配置版本
            config_version = self._get_config_version(config_data)
            target_version = expected_version or self._get_default_version()
            
            if config_version != target_version:
                logger.info(f"配置版本需要迁移: {config_version} -> {target_version}")
                try:
                    # 尝试迁移配置
                    migrated_config = migrate_legacy_config(config_data, config_version, target_version)
                    
                    # 应用环境适配
                    adapted_config = adapt_for_environment(migrated_config)
                    
                    logger.info(f"成功将配置从版本 {config_version} 迁移到 {target_version}")
                    return adapted_config
                except (ConfigMigrationError, VersionNotSupportedError) as e:
                    logger.error(f"配置迁移失败: {str(e)}")
                    return config_data
            else:
                # 版本已经是最新的，只应用环境适配
                return adapt_for_environment(config_data)
        
        except Exception as e:
            logger.error(f"加载配置文件失败: {config_path}, 错误: {str(e)}")
            return {}

    def _get_config_version(self, config: Dict[str, Any]) -> str:
        """
        获取配置的版本号
        
        Args:
            config: 配置字典
            
        Returns:
            str: 版本号，如果没有指定则返回"1.0"
        """
        # 首先尝试从_meta字段获取
        if "_meta" in config and "version" in config["_meta"]:
            return config["_meta"]["version"]
        
        # 然后尝试从version字段获取
        if "version" in config:
            return config["version"]
        
        # 如果都没有，假设是1.0版本
        return "1.0"

    def _get_default_version(self) -> str:
        """
        获取当前默认版本
        
        Returns:
            str: 默认版本号
        """
        # 从版本设置中获取当前目标版本
        try:
            if "version" in self.configs and self.configs["version"]:
                if "compatibility" in self.configs["version"] and "target_version" in self.configs["version"]["compatibility"]:
                    return self.configs["version"]["compatibility"]["target_version"]
        except Exception:
            pass
        
        # 默认返回3.0
        return "3.0"

    def migrate_config(self, config: Dict[str, Any], source_version: str, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        迁移配置到指定版本
        
        Args:
            config: 要迁移的配置
            source_version: 源版本号
            target_version: 目标版本号，如果为None则使用当前默认版本
            
        Returns:
            Dict[str, Any]: 迁移后的配置
        """
        if target_version is None:
            target_version = self._get_default_version()
        
        try:
            return migrate_legacy_config(config, source_version, target_version)
        except Exception as e:
            logger.error(f"配置迁移失败: {str(e)}")
            return config

    def secure_load_config(self, config_path: str, key_file: Optional[str] = None) -> Dict[str, Any]:
        """
        安全加载配置文件，自动解密敏感字段
        
        Args:
            config_path: 配置文件路径
            key_file: 可选的密钥文件路径
            
        Returns:
            Dict[str, Any]: 加载并解密后的配置
        """
        try:
            # 尝试使用安全存储加载
            master_key = os.environ.get("VISIONAI_MASTER_KEY")
            
            if not key_file:
                # 尝试从默认位置加载密钥文件
                default_key_file = os.path.join(self.config_dir, "encryption_key.json")
                if os.path.exists(default_key_file):
                    key_file = default_key_file
            
            return secure_load_config(config_path, master_key=master_key, key_file=key_file)
        except Exception as e:
            logger.warning(f"安全加载配置失败，将尝试普通加载: {str(e)}")
            return {}
    
    def secure_save_config(self, config: Dict[str, Any], config_path: str, 
                          sensitive_paths: Optional[List[str]] = None,
                          key_file: Optional[str] = None) -> bool:
        """
        安全保存配置文件，自动加密敏感字段
        
        Args:
            config: 配置字典
            config_path: 配置文件路径
            sensitive_paths: 敏感字段路径列表
            key_file: 可选的密钥文件路径
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 获取主密钥
            master_key = os.environ.get("VISIONAI_MASTER_KEY")
            
            if not key_file:
                # 尝试从默认位置加载密钥文件
                default_key_file = os.path.join(self.config_dir, "encryption_key.json")
                if os.path.exists(default_key_file):
                    key_file = default_key_file
            
            # 如果未指定敏感路径，使用默认的敏感字段列表
            if not sensitive_paths:
                sensitive_paths = [
                    "cloud.api_key",
                    "cloud.secret_key",
                    "cloud.access_token",
                    "database.password",
                    "auth.secret",
                    "api.key",
                    "service.credentials"
                ]
            
            # 安全保存配置
            return secure_save_config(
                config, 
                config_path, 
                sensitive_paths=sensitive_paths,
                master_key=master_key,
                key_file=key_file
            )
        except Exception as e:
            logger.error(f"安全保存配置失败: {str(e)}")
            
            # 如果安全保存失败，尝试普通保存
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    if config_path.endswith('.json'):
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    elif config_path.endswith(('.yaml', '.yml')):
                        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                    else:
                        logger.error(f"不支持的配置文件格式: {config_path}")
                        return False
                return True
            except Exception as e2:
                logger.error(f"普通保存配置也失败: {str(e2)}")
                return False

# 创建全局配置管理器实例
config_manager = ConfigManager()

if __name__ == "__main__":
    # 简单测试
    config_manager.load_all_configs()
    
    try:
        user_config = config_manager.get_config("user")
        print("用户配置:", json.dumps(user_config, indent=2, ensure_ascii=False))
        
        version_config = config_manager.get_config("version")
        print("版本配置:", json.dumps(version_config, indent=2, ensure_ascii=False))
        
        # 获取版本定义
        version_def = config_manager.get_version_definition("3.0")
        print("版本3.0定义:", json.dumps(version_def, indent=2, ensure_ascii=False))
        
        # 获取迁移路径
        path = config_manager.find_migration_path("3.0", "1.0")
        print("从3.0到1.0的迁移路径:", path)
    except Exception as e:
        print(f"测试出错: {str(e)}") 