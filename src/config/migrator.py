#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置版本迁移器

负责处理不同版本的配置文件之间的转换，确保向后兼容性，
同时支持配置结构的演进。提供字段映射、值转换和结构重组等功能。
"""

import os
import sys
import json
import yaml
import copy
import logging
import re
from typing import Dict, List, Any, Callable, Tuple, Optional, Union, Set
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.config.path_resolver import resolve_special_path, normalize_path
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def resolve_special_path(path):
        return os.path.abspath(os.path.expanduser(path))
    
    def normalize_path(path):
        return os.path.abspath(path)

# 设置日志记录器
logger = get_logger("config_migrator")

# 定义变换器类型
TransformerFunc = Callable[[Any], Any]

# 路径切分正则模式
PATH_SPLIT_PATTERN = re.compile(r'\.(?![^\[]*\])')

class ConfigMigrationError(Exception):
    """配置迁移错误"""
    pass

class ConfigKeyNotFoundError(Exception):
    """配置键不存在错误"""
    pass

class VersionNotSupportedError(Exception):
    """版本不支持错误"""
    pass

class ConfigTransformer:
    """配置转换器，负责单个配置项的转换"""
    
    def __init__(self, 
                 source_key: str, 
                 target_key: str, 
                 transform_func: Optional[TransformerFunc] = None,
                 default_value: Any = None,
                 required: bool = False):
        """
        初始化配置转换器
        
        Args:
            source_key: 源配置键路径（点分隔，如"storage.path"）
            target_key: 目标配置键路径
            transform_func: 转换函数，接收原值返回新值
            default_value: 源键不存在时的默认值
            required: 是否是必需项，如果为True且源键不存在，将抛出异常
        """
        self.source_key = source_key
        self.target_key = target_key
        self.transform_func = transform_func or (lambda x: x)  # 默认转换函数为恒等函数
        self.default_value = default_value
        self.required = required
    
    def transform(self, source_config: Dict[str, Any]) -> Tuple[str, Any]:
        """
        执行转换
        
        Args:
            source_config: 源配置字典
            
        Returns:
            Tuple[str, Any]: 目标键和转换后的值
            
        Raises:
            ConfigKeyNotFoundError: 当required=True且源键不存在时抛出
        """
        try:
            source_value = self._get_value_by_path(source_config, self.source_key)
            transformed_value = self.transform_func(source_value)
            return self.target_key, transformed_value
        except KeyError:
            if self.required:
                raise ConfigKeyNotFoundError(f"必需的配置键不存在: {self.source_key}")
            return self.target_key, self.default_value
    
    def _get_value_by_path(self, config: Dict[str, Any], path: str) -> Any:
        """
        根据路径获取嵌套字典中的值
        
        Args:
            config: 配置字典
            path: 键路径，如"storage.path"
            
        Returns:
            Any: 找到的值
            
        Raises:
            KeyError: 当键不存在时抛出
        """
        if not path:
            return config
        
        parts = PATH_SPLIT_PATTERN.split(path)
        value = config
        
        for part in parts:
            # 处理数组索引，如items[0]
            array_match = re.match(r'(.+)\[(\d+)\]$', part)
            if array_match:
                key, index = array_match.groups()
                index = int(index)
                value = value[key][index]
            else:
                value = value[part]
        
        return value


class ConfigStructureBuilder:
    """配置结构构建器，负责创建嵌套的配置结构"""
    
    @staticmethod
    def set_value_by_path(config: Dict[str, Any], path: str, value: Any) -> None:
        """
        根据路径在配置中设置值，自动创建所需的嵌套结构
        
        Args:
            config: 配置字典
            path: 键路径，如"storage.path"
            value: 要设置的值
        """
        if not path:
            return
        
        parts = PATH_SPLIT_PATTERN.split(path)
        current = config
        
        # 处理除最后一个部分外的所有路径部分
        for i, part in enumerate(parts[:-1]):
            # 处理数组索引，如items[0]
            array_match = re.match(r'(.+)\[(\d+)\]$', part)
            if array_match:
                key, index = array_match.groups()
                index = int(index)
                
                # 确保键存在
                if key not in current:
                    current[key] = []
                
                # 确保数组足够长
                while len(current[key]) <= index:
                    current[key].append({})
                
                current = current[key][index]
            else:
                # 普通键
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        # 处理最后一个部分
        last_part = parts[-1]
        array_match = re.match(r'(.+)\[(\d+)\]$', last_part)
        if array_match:
            key, index = array_match.groups()
            index = int(index)
            
            # 确保键存在
            if key not in current:
                current[key] = []
            
            # 确保数组足够长
            while len(current[key]) <= index:
                current[key].append(None)
            
            current[key][index] = value
        else:
            # 普通键
            current[last_part] = value


class ConfigMigrationRule:
    """配置迁移规则，定义从一个版本到另一个版本的配置转换规则"""
    
    def __init__(self, source_version: str, target_version: str):
        """
        初始化迁移规则
        
        Args:
            source_version: 源配置版本
            target_version: 目标配置版本
        """
        self.source_version = source_version
        self.target_version = target_version
        self.transformers: List[ConfigTransformer] = []
        self.preprocessors: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
        self.postprocessors: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []
    
    def add_field_mapping(self, 
                         source_key: str, 
                         target_key: Optional[str] = None, 
                         transform_func: Optional[TransformerFunc] = None,
                         default_value: Any = None,
                         required: bool = False) -> 'ConfigMigrationRule':
        """
        添加字段映射规则
        
        Args:
            source_key: 源配置键
            target_key: 目标配置键，如果为None则使用source_key
            transform_func: 转换函数
            default_value: 默认值
            required: 是否必需
            
        Returns:
            ConfigMigrationRule: 自身，支持链式调用
        """
        target_key = target_key or source_key
        transformer = ConfigTransformer(
            source_key=source_key,
            target_key=target_key,
            transform_func=transform_func,
            default_value=default_value,
            required=required
        )
        self.transformers.append(transformer)
        return self
    
    def add_value_transformer(self, 
                             key: str, 
                             transform_func: TransformerFunc,
                             default_value: Any = None,
                             required: bool = False) -> 'ConfigMigrationRule':
        """
        添加值转换规则，源和目标键相同，只转换值
        
        Args:
            key: 配置键
            transform_func: 转换函数
            default_value: 默认值
            required: 是否必需
            
        Returns:
            ConfigMigrationRule: 自身，支持链式调用
        """
        return self.add_field_mapping(
            source_key=key,
            target_key=key,
            transform_func=transform_func,
            default_value=default_value,
            required=required
        )
    
    def add_preprocessor(self, processor: Callable[[Dict[str, Any]], Dict[str, Any]]) -> 'ConfigMigrationRule':
        """
        添加前置处理器，在应用转换规则前预处理配置
        
        Args:
            processor: 处理函数
            
        Returns:
            ConfigMigrationRule: 自身，支持链式调用
        """
        self.preprocessors.append(processor)
        return self
    
    def add_postprocessor(self, processor: Callable[[Dict[str, Any]], Dict[str, Any]]) -> 'ConfigMigrationRule':
        """
        添加后置处理器，在应用转换规则后处理结果配置
        
        Args:
            processor: 处理函数
            
        Returns:
            ConfigMigrationRule: 自身，支持链式调用
        """
        self.postprocessors.append(processor)
        return self
    
    def apply(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用迁移规则转换配置
        
        Args:
            config: 源配置
            
        Returns:
            Dict[str, Any]: 转换后的配置
        """
        # 1. 创建配置副本，避免修改原始配置
        result_config = {}
        
        # 2. 应用前置处理器
        processed_config = copy.deepcopy(config)
        for processor in self.preprocessors:
            processed_config = processor(processed_config)
        
        # 3. 应用所有转换器
        for transformer in self.transformers:
            try:
                target_key, value = transformer.transform(processed_config)
                ConfigStructureBuilder.set_value_by_path(result_config, target_key, value)
            except ConfigKeyNotFoundError as e:
                logger.warning(f"迁移配置项失败: {str(e)}")
        
        # 4. 应用后置处理器
        for processor in self.postprocessors:
            result_config = processor(result_config)
        
        # 5. 添加迁移元数据
        if "_meta" not in result_config:
            result_config["_meta"] = {}
        
        result_config["_meta"]["version"] = self.target_version
        result_config["_meta"]["migrated_from"] = self.source_version
        result_config["_meta"]["migration_date"] = datetime.now().isoformat()
        
        return result_config


class ConfigMigrator:
    """配置迁移器，负责整个迁移过程"""
    
    def __init__(self):
        """初始化迁移器"""
        self.migration_rules: Dict[str, Dict[str, ConfigMigrationRule]] = {}
        self.version_graph: Dict[str, Set[str]] = {}  # 版本图，用于查找迁移路径
        
        # 初始化内置迁移规则
        self._init_migration_rules()
    
    def _init_migration_rules(self) -> None:
        """初始化内置的迁移规则"""
        # 添加1.0到2.0的迁移规则
        self.add_rule(self._create_v1_to_v2_rule())
        
        # 添加2.0到2.5的迁移规则
        self.add_rule(self._create_v2_to_v2_5_rule())
        
        # 添加2.5到3.0的迁移规则
        self.add_rule(self._create_v2_5_to_v3_rule())
    
    def _create_v1_to_v2_rule(self) -> ConfigMigrationRule:
        """创建从1.0到2.0版本的迁移规则"""
        rule = ConfigMigrationRule("1.0", "2.0")
        
        # 字段重命名示例
        rule.add_field_mapping("video.quality", "export.resolution")
        rule.add_field_mapping("save_folder", "storage.output_path")
        
        # 添加默认值示例
        rule.add_field_mapping(
            "processing.threads", 
            "performance.cpu_threads", 
            default_value=4
        )
        
        # 值转换示例：调整分辨率格式
        def transform_resolution(value):
            if isinstance(value, str):
                # 如果已经是字符串格式，直接返回
                return value
            
            # 假设value是整数表示的高度
            if value <= 480:
                return "480p"
            elif value <= 720:
                return "720p"
            elif value <= 1080:
                return "1080p"
            elif value <= 1440:
                return "1440p"
            else:
                return "4K"
        
        rule.add_field_mapping(
            "video_height", 
            "output.resolution", 
            transform_func=transform_resolution,
            default_value="1080p"
        )
        
        # 复杂结构转换示例：将平铺的配置转换为嵌套结构
        def audio_preprocessor(config):
            # 收集所有音频相关配置并整合到audio字段下
            result = copy.deepcopy(config)
            audio_config = {}
            
            # 收集并移除原始键
            for key in list(result.keys()):
                if key.startswith("audio_"):
                    # 移除前缀，放入audio字段
                    new_key = key.replace("audio_", "")
                    audio_config[new_key] = result.pop(key)
            
            # 设置新的audio字段
            if audio_config:
                result["audio"] = audio_config
            
            return result
        
        rule.add_preprocessor(audio_preprocessor)
        
        return rule
    
    def _create_v2_to_v2_5_rule(self) -> ConfigMigrationRule:
        """创建从2.0到2.5版本的迁移规则"""
        rule = ConfigMigrationRule("2.0", "2.5")
        
        # 添加元数据支持
        rule.add_field_mapping(
            "project.name", 
            "metadata.project_name"
        )
        rule.add_field_mapping(
            "project.description", 
            "metadata.description",
            default_value=""
        )
        
        # 添加创建日期
        def get_current_date():
            return datetime.now().isoformat()
        
        rule.add_field_mapping(
            "project.created", 
            "metadata.created_at",
            transform_func=lambda x: x or get_current_date(),
            default_value=get_current_date()
        )
        
        # 转换标签格式
        def transform_tags(tags):
            if not tags:
                return []
            
            if isinstance(tags, str):
                # 如果是逗号分隔的字符串
                return [tag.strip() for tag in tags.split(",") if tag.strip()]
            
            if isinstance(tags, list):
                return tags
            
            return []
        
        rule.add_field_mapping(
            "project.tags", 
            "metadata.tags",
            transform_func=transform_tags,
            default_value=[]
        )
        
        # 添加分辨率和帧率设置
        def transform_video_settings(config):
            result = copy.deepcopy(config)
            
            # 确保export节点存在
            if "export" not in result:
                result["export"] = {}
            
            # 从其他地方收集视频设置
            if "output" in result and "resolution" in result["output"]:
                result["export"]["resolution"] = result["output"]["resolution"]
            
            if "video" in result and "frame_rate" in result["video"]:
                result["export"]["frame_rate"] = result["video"]["frame_rate"]
            elif "frame_rate" in result:
                result["export"]["frame_rate"] = result["frame_rate"]
            else:
                result["export"]["frame_rate"] = 30
            
            return result
        
        rule.add_preprocessor(transform_video_settings)
        
        return rule
    
    def _create_v2_5_to_v3_rule(self) -> ConfigMigrationRule:
        """创建从2.5到3.0版本的迁移规则"""
        rule = ConfigMigrationRule("2.5", "3.0")
        
        # 添加高级效果支持
        rule.add_field_mapping(
            "effects.enabled", 
            "effects.advanced_enabled",
            default_value=False
        )
        
        # 转换效果配置
        def transform_effects(effects_config):
            if not effects_config or not isinstance(effects_config, dict):
                return {"basic": {}, "advanced": {}}
            
            result = {
                "basic": {},
                "advanced": {}
            }
            
            # 处理基本效果
            for key, value in effects_config.items():
                if key not in ["enabled", "advanced_enabled"]:
                    result["basic"][key] = value
            
            return result
        
        rule.add_field_mapping(
            "effects", 
            "effects",
            transform_func=transform_effects,
            default_value={"basic": {}, "advanced": {}}
        )
        
        # 添加嵌套序列支持
        rule.add_field_mapping(
            "sequence", 
            "sequences.main",
            default_value={}
        )
        
        # 处理4K支持
        def add_4k_support(config):
            result = copy.deepcopy(config)
            
            # 添加分辨率选项
            if "export" not in result:
                result["export"] = {}
            
            if "resolution" in result["export"]:
                current_res = result["export"]["resolution"]
                
                # 为3.0版本添加更高分辨率选项
                result["export"]["available_resolutions"] = ["480p", "720p", "1080p", "1440p", "4K"]
                
                # 如果当前分辨率是4K以下，添加4K作为可选项
                if current_res not in ["4K", "2160p"]:
                    result["export"]["resolution"] = current_res
                else:
                    result["export"]["resolution"] = "4K"
            
            return result
        
        rule.add_postprocessor(add_4k_support)
        
        return rule
    
    def add_rule(self, rule: ConfigMigrationRule) -> None:
        """
        添加迁移规则
        
        Args:
            rule: 配置迁移规则
        """
        source_version = rule.source_version
        target_version = rule.target_version
        
        # 添加到规则字典
        if source_version not in self.migration_rules:
            self.migration_rules[source_version] = {}
        
        self.migration_rules[source_version][target_version] = rule
        
        # 更新版本图
        if source_version not in self.version_graph:
            self.version_graph[source_version] = set()
        if target_version not in self.version_graph:
            self.version_graph[target_version] = set()
        
        self.version_graph[source_version].add(target_version)
    
    def migrate_legacy_config(self, config: Dict[str, Any], source_version: str, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        迁移旧版本配置到指定版本
        
        Args:
            config: 要迁移的配置
            source_version: 源版本号
            target_version: 目标版本号，如果不提供则使用最新版本
            
        Returns:
            Dict[str, Any]: 迁移后的配置
            
        Raises:
            VersionNotSupportedError: 如果版本不受支持
            ConfigMigrationError: 如果迁移失败
        """
        if not target_version:
            # 寻找最新版本
            all_versions = set(self.migration_rules.keys()).union(*[set(rules.keys()) for rules in self.migration_rules.values()])
            if not all_versions:
                raise VersionNotSupportedError("没有可用的版本定义")
            
            # 按语义版本排序（简化实现，假设版本格式为x.y或x.y.z）
            def version_key(v):
                return [int(x) for x in v.split(".")]
            
            target_version = sorted(all_versions, key=version_key)[-1]
        
        # 检查源版本和目标版本是否相同
        if source_version == target_version:
            return copy.deepcopy(config)
        
        # 找出迁移路径
        migration_path = self.find_migration_path(source_version, target_version)
        
        if not migration_path:
            raise VersionNotSupportedError(f"无法从 {source_version} 迁移到 {target_version}，找不到迁移路径")
        
        # 沿着路径执行迁移
        current_config = copy.deepcopy(config)
        current_version = source_version
        
        for next_version in migration_path[1:]:  # 跳过第一个（源版本）
            try:
                rule = self.migration_rules[current_version][next_version]
                current_config = rule.apply(current_config)
                current_version = next_version
            except KeyError:
                raise ConfigMigrationError(f"缺少从 {current_version} 到 {next_version} 的迁移规则")
            except Exception as e:
                raise ConfigMigrationError(f"从 {current_version} 迁移到 {next_version} 时出错: {str(e)}")
        
        return current_config
    
    def find_migration_path(self, source_version: str, target_version: str) -> List[str]:
        """
        查找从源版本到目标版本的迁移路径
        
        Args:
            source_version: 源版本
            target_version: 目标版本
            
        Returns:
            List[str]: 迁移路径，如果不存在则返回空列表
        """
        # 如果源版本和目标版本相同，直接返回
        if source_version == target_version:
            return [source_version]
        
        # 如果有直接的迁移规则，使用它
        if source_version in self.migration_rules and target_version in self.migration_rules[source_version]:
            return [source_version, target_version]
        
        # 使用广度优先搜索找出最短路径
        queue = [(source_version, [source_version])]
        visited = {source_version}
        
        while queue:
            current, path = queue.pop(0)
            
            # 获取当前版本可直接迁移到的所有版本
            if current in self.version_graph:
                for next_version in self.version_graph[current]:
                    if next_version == target_version:
                        return path + [next_version]
                    
                    if next_version not in visited:
                        visited.add(next_version)
                        queue.append((next_version, path + [next_version]))
        
        # 没有找到路径
        return []


# 创建全局迁移器单例
_instance = None

def get_config_migrator() -> ConfigMigrator:
    """
    获取全局配置迁移器实例
    
    Returns:
        ConfigMigrator: 配置迁移器实例
    """
    global _instance
    if _instance is None:
        _instance = ConfigMigrator()
    return _instance


def migrate_legacy_config(config: Dict[str, Any], old_ver: str, target_ver: Optional[str] = None) -> Dict[str, Any]:
    """
    迁移旧版本配置到指定版本（便捷函数）
    
    Args:
        config: 要迁移的配置
        old_ver: 源版本号
        target_ver: 目标版本号，如果不提供则使用最新版本
        
    Returns:
        Dict[str, Any]: 迁移后的配置
    """
    migrator = get_config_migrator()
    return migrator.migrate_legacy_config(config, old_ver, target_ver)


def apply_rules(rules: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    应用一组迁移规则变换配置中的字段
    
    Args:
        rules: 规则列表，每个规则是(源键, 目标键)的元组
        
    Returns:
        Dict[str, Any]: 转换后的配置
    """
    # 这里是简化版实现，仅演示如何使用上述API
    migrator = get_config_migrator()
    
    # 创建一个临时规则
    temp_rule = ConfigMigrationRule("temp", "temp")
    
    # 添加所有字段映射规则
    for source_key, target_key in rules:
        temp_rule.add_field_mapping(source_key, target_key)
    
    # 创建一个空配置，由于没有源配置，这个函数主要是演示API
    empty_config = {}
    
    # 返回规则应用后的结果
    return temp_rule.apply(empty_config)


# 如果直接运行此模块，执行演示
if __name__ == "__main__":
    # 简单演示
    
    # 创建一个1.0版本的旧配置
    old_config = {
        "video_height": 720,
        "video.quality": "high",
        "save_folder": "D:/Videos/Output",
        "audio_volume": 1.0,
        "audio_normalize": True,
        "project": {
            "name": "测试项目",
            "description": "这是一个测试项目",
            "tags": "视频,测试,演示"
        }
    }
    
    print("原始配置 (1.0版本):")
    print(json.dumps(old_config, indent=2, ensure_ascii=False))
    print("\n" + "-" * 60 + "\n")
    
    # 迁移到2.0版本
    try:
        migrator = get_config_migrator()
        v2_config = migrator.migrate_legacy_config(old_config, "1.0", "2.0")
        
        print("迁移到2.0版本后:")
        print(json.dumps(v2_config, indent=2, ensure_ascii=False))
        print("\n" + "-" * 60 + "\n")
        
        # 迁移到3.0版本
        v3_config = migrator.migrate_legacy_config(old_config, "1.0", "3.0")
        
        print("直接迁移到3.0版本后:")
        print(json.dumps(v3_config, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"迁移失败: {str(e)}") 