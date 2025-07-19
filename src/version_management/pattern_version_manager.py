"""
模式版本管理器

负责管理和维护不同版本的叙事模式模型和配置，
支持版本之间的切换、比较和元数据管理。
"""

import os
import re
import json
import yaml
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from packaging import version
from loguru import logger

# 项目根目录
PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
PATTERNS_ROOT = PROJECT_ROOT / "models" / "narrative_patterns"
LATEST_SYMLINK = PATTERNS_ROOT / "latest"


class PatternVersionManager:
    """模式版本管理器类"""
    
    def __init__(self):
        """初始化版本管理器"""
        self.versions_cache = {}
        self.current_version = None
        self._ensure_directory_structure()
        self._init_version_cache()
        
    def _ensure_directory_structure(self) -> None:
        """确保版本目录结构存在"""
        if not PATTERNS_ROOT.exists():
            logger.info(f"创建模式版本根目录: {PATTERNS_ROOT}")
            PATTERNS_ROOT.mkdir(parents=True, exist_ok=True)
        
        # 确保至少有一个默认版本目录
        default_version = "v1.0"
        default_version_dir = PATTERNS_ROOT / default_version
        
        if not any(d.is_dir() for d in PATTERNS_ROOT.iterdir() if d.name.startswith("v")):
            logger.info(f"创建默认版本目录: {default_version}")
            default_version_dir.mkdir(exist_ok=True)
            
            # 创建默认版本的元数据
            self._create_default_metadata(default_version_dir)
        
        # 确保latest链接存在
        if not LATEST_SYMLINK.exists():
            latest_version = self._find_latest_version()
            if latest_version:
                self._update_latest_symlink(latest_version)
    
    def _create_default_metadata(self, version_dir: Path) -> None:
        """创建默认版本的元数据文件"""
        metadata = {
            "version": version_dir.name,
            "created_at": datetime.now().isoformat(),
            "description": "初始版本的叙事模式",
            "author": "系统",
            "models": {
                "fp-growth.model": {
                    "description": "频繁模式挖掘模型",
                    "algorithm": "FP-Growth",
                    "trained_on": "初始数据集",
                    "parameters": {
                        "min_support": 0.1,
                        "max_patterns": 100
                    }
                }
            },
            "compatible_app_versions": [">=1.0.0"],
            "data_size": "1.2TB",
            "coverage": {
                "zh": 0.89,
                "en": 0.76
            }
        }
        
        # 保存元数据
        metadata_path = version_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 创建默认配置
        config = {
            "pattern_types": [
                "opening", "climax", "transition", 
                "conflict", "resolution", "ending"
            ],
            "evaluation_weights": {
                "audience_retention": 0.25,
                "viral_coefficient": 0.2,
                "recommendation_weight": 0.15,
                "emotional_intensity": 0.25,
                "narrative_coherence": 0.15
            },
            "thresholds": {
                "min_impact_score": 0.6,
                "min_confidence": 0.65
            },
            "feature_importance": {
                "frequency": 0.3,
                "position": 0.15,
                "sentiment": 0.25,
                "duration": 0.1,
                "surprise_level": 0.2
            }
        }
        
        # 保存配置
        config_path = version_dir / "pattern_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
        # 创建模型占位文件
        model_path = version_dir / "fp-growth.model"
        with open(model_path, "w", encoding="utf-8") as f:
            f.write("# 模式挖掘模型占位文件\n")
            f.write("# 实际项目中，这里应该是序列化的模型数据\n")
    
    def _init_version_cache(self) -> None:
        """初始化版本缓存"""
        self.versions_cache = {}
        
        # 遍历所有版本目录
        for version_dir in PATTERNS_ROOT.iterdir():
            if version_dir.is_dir() and version_dir.name.startswith("v"):
                metadata_file = version_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        self.versions_cache[version_dir.name] = metadata
                    except Exception as e:
                        logger.error(f"读取版本元数据失败: {version_dir.name}, 错误: {e}")
        
        # 设置当前版本
        if self.versions_cache:
            self.current_version = self._find_latest_version()
        
        logger.info(f"已加载 {len(self.versions_cache)} 个模式版本")
    
    def _find_latest_version(self) -> Optional[str]:
        """查找最新版本号"""
        if not self.versions_cache:
            # 查找目录中的所有版本
            versions = []
            for version_dir in PATTERNS_ROOT.iterdir():
                if version_dir.is_dir() and re.match(r"v\d+\.\d+", version_dir.name):
                    versions.append(version_dir.name)
                    
            if not versions:
                return None
                
            # 按版本号排序
            versions.sort(key=lambda x: version.parse(x[1:]))  # 去掉'v'前缀进行版本比较
            return versions[-1]
        else:
            # 从缓存中获取最新版本
            versions = list(self.versions_cache.keys())
            versions.sort(key=lambda x: version.parse(x[1:]))
            return versions[-1] if versions else None
    
    def _update_latest_symlink(self, version_name: str) -> None:
        """更新latest符号链接"""
        target_dir = PATTERNS_ROOT / version_name
        if not target_dir.exists():
            logger.error(f"目标版本目录不存在: {version_name}")
            return
            
        # Windows不支持符号链接，使用复制代替
        if os.name == 'nt':
            if LATEST_SYMLINK.exists():
                if LATEST_SYMLINK.is_dir():
                    shutil.rmtree(LATEST_SYMLINK)
                else:
                    LATEST_SYMLINK.unlink()
            
            # 复制目录内容
            shutil.copytree(target_dir, LATEST_SYMLINK)
            
            # 创建指向当前版本的txt文件
            with open(LATEST_SYMLINK / "current_version.txt", "w") as f:
                f.write(version_name)
        else:
            # Unix系统使用符号链接
            if LATEST_SYMLINK.exists():
                LATEST_SYMLINK.unlink()
            os.symlink(target_dir, LATEST_SYMLINK, target_is_directory=True)
        
        logger.info(f"已更新latest链接指向版本: {version_name}")
    
    def get_available_versions(self) -> List[Dict[str, Any]]:
        """获取所有可用版本及其元数据"""
        if not self.versions_cache:
            self._init_version_cache()
            
        result = []
        for version_name, metadata in self.versions_cache.items():
            result.append({
                "version": version_name,
                "created_at": metadata.get("created_at", "未知"),
                "description": metadata.get("description", ""),
                "is_current": version_name == self.current_version
            })
            
        # 按版本排序
        result.sort(key=lambda x: version.parse(x["version"][1:]), reverse=True)
        return result
    
    def get_version_metadata(self, version_name: Optional[str] = None) -> Dict[str, Any]:
        """获取指定版本的元数据"""
        if not version_name:
            version_name = self.current_version
            
        if not version_name:
            logger.error("没有设置当前版本，无法获取元数据")
            return {}
            
        if version_name in self.versions_cache:
            return self.versions_cache[version_name]
            
        # 尝试从文件加载
        metadata_file = PATTERNS_ROOT / version_name / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                self.versions_cache[version_name] = metadata
                return metadata
            except Exception as e:
                logger.error(f"读取版本元数据失败: {version_name}, 错误: {e}")
                
        return {}
    
    def set_current_version(self, version_name: str) -> bool:
        """设置当前使用的版本"""
        version_dir = PATTERNS_ROOT / version_name
        if not version_dir.exists():
            logger.error(f"版本目录不存在: {version_name}")
            return False
            
        self.current_version = version_name
        self._update_latest_symlink(version_name)
        
        logger.info(f"当前版本已设置为: {version_name}")
        return True
    
    def create_new_version(self, 
                        version_name: str, 
                        description: str = "",
                        author: str = "系统",
                        base_version: Optional[str] = None) -> bool:
        """创建新版本"""
        if not version_name.startswith("v"):
            version_name = f"v{version_name}"
            
        # 检查版本名称是否符合规范
        if not re.match(r"v\d+\.\d+", version_name):
            logger.error(f"版本名称格式不正确: {version_name}，应为v1.0格式")
            return False
            
        # 检查是否已存在
        version_dir = PATTERNS_ROOT / version_name
        if version_dir.exists():
            logger.error(f"版本已存在: {version_name}")
            return False
            
        # 确定基础版本
        if not base_version:
            base_version = self._find_latest_version()
            
        if not base_version:
            # 创建全新版本
            version_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_metadata(version_dir)
        else:
            # 从基础版本复制
            base_dir = PATTERNS_ROOT / base_version
            if not base_dir.exists():
                logger.error(f"基础版本不存在: {base_version}")
                return False
                
            # 复制目录
            shutil.copytree(base_dir, version_dir)
            
            # 更新元数据
            metadata_file = version_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        
                    metadata["version"] = version_name
                    metadata["created_at"] = datetime.now().isoformat()
                    metadata["description"] = description
                    metadata["author"] = author
                    metadata["based_on"] = base_version
                    
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    logger.error(f"更新版本元数据失败: {version_name}, 错误: {e}")
                    return False
        
        # 刷新缓存
        self._init_version_cache()
        
        logger.info(f"已创建新版本: {version_name}, 基于: {base_version or '无'}")
        return True
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """比较两个版本之间的差异"""
        metadata1 = self.get_version_metadata(version1)
        metadata2 = self.get_version_metadata(version2)
        
        if not metadata1 or not metadata2:
            return {"error": "无法获取一个或多个版本的元数据"}
            
        # 获取配置文件
        config_file1 = PATTERNS_ROOT / version1 / "pattern_config.yaml"
        config_file2 = PATTERNS_ROOT / version2 / "pattern_config.yaml"
        
        config1 = {}
        config2 = {}
        
        if config_file1.exists():
            with open(config_file1, "r", encoding="utf-8") as f:
                config1 = yaml.safe_load(f)
                
        if config_file2.exists():
            with open(config_file2, "r", encoding="utf-8") as f:
                config2 = yaml.safe_load(f)
        
        # 比较结果
        result = {
            "metadata_diff": self._compare_dict(metadata1, metadata2),
            "config_diff": self._compare_dict(config1, config2),
            "version_info": {
                "newer": version1 if version.parse(version1[1:]) > version.parse(version2[1:]) else version2,
                "version1_date": metadata1.get("created_at", "未知"),
                "version2_date": metadata2.get("created_at", "未知")
            }
        }
        
        return result
    
    def _compare_dict(self, dict1: Dict, dict2: Dict) -> Dict[str, Any]:
        """比较两个字典的差异"""
        all_keys = set(dict1.keys()) | set(dict2.keys())
        diff = {}
        
        for key in all_keys:
            # 键只在dict1中
            if key in dict1 and key not in dict2:
                diff[key] = {"status": "removed", "value": dict1[key]}
            # 键只在dict2中
            elif key not in dict1 and key in dict2:
                diff[key] = {"status": "added", "value": dict2[key]}
            # 键在两者中都存在
            elif dict1[key] != dict2[key]:
                # 如果值是字典，则递归比较
                if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    diff[key] = {"status": "changed", "diff": self._compare_dict(dict1[key], dict2[key])}
                # 如果值是列表，找出添加和删除的项
                elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                    added = [item for item in dict2[key] if item not in dict1[key]]
                    removed = [item for item in dict1[key] if item not in dict2[key]]
                    if added or removed:
                        diff[key] = {
                            "status": "changed",
                            "added": added,
                            "removed": removed
                        }
                # 其他类型直接记录新旧值
                else:
                    diff[key] = {
                        "status": "changed",
                        "old_value": dict1[key],
                        "new_value": dict2[key]
                    }
        
        return diff
    
    def get_pattern_config(self, version_name: Optional[str] = None) -> Dict[str, Any]:
        """获取指定版本的模式配置"""
        if not version_name:
            version_name = self.current_version
            
        if not version_name:
            logger.error("没有设置当前版本，无法获取配置")
            return {}
            
        config_file = PATTERNS_ROOT / version_name / "pattern_config.yaml"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"读取版本配置失败: {version_name}, 错误: {e}")
                
        return {}
    
    def update_pattern_config(self, config: Dict[str, Any], version_name: Optional[str] = None) -> bool:
        """更新指定版本的模式配置"""
        if not version_name:
            version_name = self.current_version
            
        if not version_name:
            logger.error("没有设置当前版本，无法更新配置")
            return False
            
        version_dir = PATTERNS_ROOT / version_name
        if not version_dir.exists():
            logger.error(f"版本目录不存在: {version_name}")
            return False
            
        config_file = version_dir / "pattern_config.yaml"
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"已更新版本 {version_name} 的配置")
            return True
        except Exception as e:
            logger.error(f"更新版本配置失败: {version_name}, 错误: {e}")
            return False
    
    def get_model_path(self, model_name: str, version_name: Optional[str] = None) -> Optional[Path]:
        """获取指定版本中特定模型的路径"""
        if not version_name:
            version_name = self.current_version
            
        if not version_name:
            logger.error("没有设置当前版本，无法获取模型路径")
            return None
            
        model_path = PATTERNS_ROOT / version_name / model_name
        if model_path.exists():
            return model_path
            
        logger.warning(f"模型文件不存在: {model_path}")
        return None


# 全局单例
_pattern_version_manager = PatternVersionManager()


def get_latest_version() -> str:
    """获取最新版本号"""
    global _pattern_version_manager
    return _pattern_version_manager._find_latest_version() or "v1.0"


def get_available_versions() -> List[Dict[str, Any]]:
    """获取所有可用版本"""
    global _pattern_version_manager
    return _pattern_version_manager.get_available_versions()


def set_current_version(version_name: str) -> bool:
    """设置当前使用的版本"""
    global _pattern_version_manager
    return _pattern_version_manager.set_current_version(version_name)


def get_version_metadata(version_name: Optional[str] = None) -> Dict[str, Any]:
    """获取版本元数据"""
    global _pattern_version_manager
    return _pattern_version_manager.get_version_metadata(version_name)


def create_new_version(version_name: str, description: str = "", author: str = "系统", base_version: Optional[str] = None) -> bool:
    """创建新版本"""
    global _pattern_version_manager
    return _pattern_version_manager.create_new_version(version_name, description, author, base_version)


def compare_versions(version1: str, version2: str) -> Dict[str, Any]:
    """比较两个版本之间的差异"""
    global _pattern_version_manager
    return _pattern_version_manager.compare_versions(version1, version2)


def get_pattern_config(version_name: Optional[str] = None) -> Dict[str, Any]:
    """获取模式配置"""
    global _pattern_version_manager
    return _pattern_version_manager.get_pattern_config(version_name)


def get_model_path(model_name: str, version_name: Optional[str] = None) -> Optional[Path]:
    """获取模型路径"""
    global _pattern_version_manager
    return _pattern_version_manager.get_model_path(model_name, version_name) 