#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径管理器 - 解决跨设备文件路径问题
确保素材文件访问路径在不同环境下自动适配
"""

import os
import sys
import json
import shutil
import platform
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse

class PathManager:
    """路径管理器 - 处理跨平台和跨设备的路径问题"""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        初始化路径管理器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.platform = platform.system().lower()
        self.logger = self._setup_logger()
        
        # 路径映射缓存
        self.path_cache = {}
        self.missing_files = set()
        
        # 标准目录结构
        self.standard_dirs = {
            "input": self.project_root / "data" / "input",
            "output": self.project_root / "data" / "output", 
            "temp": self.project_root / "temp_clips",
            "models": self.project_root / "models",
            "exports": self.project_root / "exports",
            "cache": self.project_root / "cache"
        }
        
        # 确保目录存在
        self._ensure_directories()
        
        self.logger.info("📁 路径管理器初始化完成")
        self.logger.info(f"🏠 项目根目录: {self.project_root}")
        self.logger.info(f"💻 平台: {self.platform}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("PathManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _ensure_directories(self):
        """确保标准目录存在"""
        for dir_name, dir_path in self.standard_dirs.items():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"✅ 目录确认: {dir_name} -> {dir_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ 创建目录失败 {dir_name}: {e}")
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """
        标准化路径
        
        Args:
            path: 输入路径
            
        Returns:
            标准化的Path对象
        """
        if not path:
            return Path()
        
        # 转换为Path对象
        path_obj = Path(path)
        
        # 处理相对路径
        if not path_obj.is_absolute():
            path_obj = self.project_root / path_obj
        
        # 解析路径
        try:
            path_obj = path_obj.resolve()
        except (OSError, RuntimeError):
            # 如果路径不存在，返回标准化但未解析的路径
            pass
        
        return path_obj
    
    def resolve_file_path(self, file_path: Union[str, Path], 
                         search_dirs: Optional[List[Union[str, Path]]] = None) -> Optional[Path]:
        """
        解析文件路径，支持多种查找策略
        
        Args:
            file_path: 文件路径
            search_dirs: 搜索目录列表
            
        Returns:
            解析后的文件路径，如果找不到返回None
        """
        if not file_path:
            return None
        
        # 缓存检查
        cache_key = str(file_path)
        if cache_key in self.path_cache:
            cached_path = self.path_cache[cache_key]
            if cached_path and cached_path.exists():
                return cached_path
        
        # 标准化输入路径
        normalized_path = self.normalize_path(file_path)
        
        # 策略1: 直接检查路径
        if normalized_path.exists():
            self.path_cache[cache_key] = normalized_path
            return normalized_path
        
        # 策略2: 在标准目录中搜索
        search_locations = search_dirs or []
        search_locations.extend([
            self.standard_dirs["input"],
            self.standard_dirs["output"],
            self.standard_dirs["temp"],
            self.standard_dirs["exports"]
        ])
        
        file_name = normalized_path.name
        for search_dir in search_locations:
            search_path = Path(search_dir)
            if search_path.exists():
                # 直接查找
                candidate = search_path / file_name
                if candidate.exists():
                    self.path_cache[cache_key] = candidate
                    return candidate
                
                # 递归查找
                for found_file in search_path.rglob(file_name):
                    if found_file.is_file():
                        self.path_cache[cache_key] = found_file
                        return found_file
        
        # 策略3: 模糊匹配
        fuzzy_result = self._fuzzy_search(file_name, search_locations)
        if fuzzy_result:
            self.path_cache[cache_key] = fuzzy_result
            return fuzzy_result
        
        # 记录缺失文件
        self.missing_files.add(str(normalized_path))
        self.logger.warning(f"❌ 文件未找到: {file_path}")
        
        return None
    
    def _fuzzy_search(self, filename: str, search_dirs: List[Path]) -> Optional[Path]:
        """模糊搜索文件"""
        base_name = Path(filename).stem.lower()
        extension = Path(filename).suffix.lower()
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            for file_path in search_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                file_stem = file_path.stem.lower()
                file_ext = file_path.suffix.lower()
                
                # 检查扩展名匹配
                if extension and file_ext == extension:
                    # 检查文件名相似度
                    if base_name in file_stem or file_stem in base_name:
                        self.logger.info(f"🔍 模糊匹配找到: {filename} -> {file_path}")
                        return file_path
        
        return None
    
    def create_portable_path(self, absolute_path: Union[str, Path]) -> str:
        """
        创建可移植的相对路径
        
        Args:
            absolute_path: 绝对路径
            
        Returns:
            相对于项目根目录的路径字符串
        """
        abs_path = self.normalize_path(absolute_path)
        
        try:
            # 尝试创建相对路径
            relative_path = abs_path.relative_to(self.project_root)
            return str(relative_path).replace("\\", "/")  # 使用正斜杠
        except ValueError:
            # 如果不在项目目录内，返回文件名
            return abs_path.name
    
    def resolve_portable_path(self, portable_path: str) -> Path:
        """
        解析可移植路径
        
        Args:
            portable_path: 可移植路径字符串
            
        Returns:
            解析后的绝对路径
        """
        # 标准化路径分隔符
        normalized = portable_path.replace("\\", "/")
        
        # 构建绝对路径
        absolute_path = self.project_root / normalized
        
        return absolute_path
    
    def copy_to_project(self, external_path: Union[str, Path], 
                       target_dir: str = "input") -> Optional[Path]:
        """
        将外部文件复制到项目目录
        
        Args:
            external_path: 外部文件路径
            target_dir: 目标目录名称
            
        Returns:
            复制后的文件路径
        """
        source_path = Path(external_path)
        
        if not source_path.exists():
            self.logger.error(f"❌ 源文件不存在: {external_path}")
            return None
        
        # 确定目标路径
        target_base = self.standard_dirs.get(target_dir, self.standard_dirs["input"])
        target_path = target_base / source_path.name
        
        # 避免重名
        counter = 1
        while target_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            target_path = target_base / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            # 复制文件
            shutil.copy2(source_path, target_path)
            self.logger.info(f"📋 文件已复制: {source_path.name} -> {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"❌ 复制文件失败: {e}")
            return None
    
    def validate_project_structure(self) -> Dict[str, Any]:
        """验证项目结构"""
        validation_result = {
            "valid": True,
            "missing_dirs": [],
            "missing_files": list(self.missing_files),
            "recommendations": []
        }
        
        # 检查标准目录
        for dir_name, dir_path in self.standard_dirs.items():
            if not dir_path.exists():
                validation_result["missing_dirs"].append(str(dir_path))
                validation_result["valid"] = False
        
        # 检查关键文件
        critical_files = [
            "simple_ui_fixed.py",
            "src/core/clip_generator.py",
            "src/exporters/jianying_pro_exporter.py"
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                validation_result["missing_files"].append(file_path)
                validation_result["valid"] = False
        
        # 生成建议
        if validation_result["missing_dirs"]:
            validation_result["recommendations"].append(
                "运行项目初始化脚本创建缺失目录"
            )
        
        if validation_result["missing_files"]:
            validation_result["recommendations"].append(
                "检查项目完整性，可能需要重新下载"
            )
        
        return validation_result
    
    def create_path_mapping(self, file_list: List[Union[str, Path]]) -> Dict[str, Dict[str, Any]]:
        """
        为文件列表创建路径映射
        
        Args:
            file_list: 文件路径列表
            
        Returns:
            路径映射字典
        """
        mapping = {}
        
        for file_path in file_list:
            original_path = str(file_path)
            resolved_path = self.resolve_file_path(file_path)
            portable_path = self.create_portable_path(file_path) if resolved_path else None
            
            mapping[original_path] = {
                "original": original_path,
                "resolved": str(resolved_path) if resolved_path else None,
                "portable": portable_path,
                "exists": resolved_path is not None,
                "accessible": resolved_path.exists() if resolved_path else False
            }
        
        return mapping
    
    def fix_project_paths(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        修复项目数据中的路径问题
        
        Args:
            project_data: 项目数据
            
        Returns:
            修复后的项目数据
        """
        fixed_data = project_data.copy()
        
        # 修复视频文件路径
        if "clips" in fixed_data:
            for clip in fixed_data["clips"]:
                if "file" in clip:
                    original_file = clip["file"]
                    resolved_file = self.resolve_file_path(original_file)
                    
                    if resolved_file:
                        clip["file"] = str(resolved_file)
                        clip["portable_path"] = self.create_portable_path(resolved_file)
                    else:
                        # 尝试创建占位符
                        clip["file"] = str(self.standard_dirs["temp"] / Path(original_file).name)
                        clip["missing"] = True
        
        # 修复素材库路径
        if "materials" in fixed_data:
            for material in fixed_data["materials"]:
                if "path" in material:
                    original_path = material["path"]
                    resolved_path = self.resolve_file_path(original_path)
                    
                    if resolved_path:
                        material["path"] = str(resolved_path)
                        material["portable_path"] = self.create_portable_path(resolved_path)
                    else:
                        material["missing"] = True
        
        return fixed_data
    
    def get_path_report(self) -> Dict[str, Any]:
        """获取路径管理报告"""
        return {
            "project_root": str(self.project_root),
            "platform": self.platform,
            "standard_dirs": {k: str(v) for k, v in self.standard_dirs.items()},
            "cache_size": len(self.path_cache),
            "missing_files_count": len(self.missing_files),
            "missing_files": list(self.missing_files),
            "validation": self.validate_project_structure()
        }
