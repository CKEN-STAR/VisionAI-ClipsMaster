#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映工程包生成模块

提供剪映工程包的创建和管理功能，支持导出符合剪映格式的工程文件。
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Union, Optional, Tuple

# 导入相关模块
from src.exporters.xml_template import XMLTemplateProcessor
from src.exporters.timeline_converter import TimelineConverter
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("jianying_project")

class JianyingProject:
    """剪映工程类"""
    
    def __init__(self, project_name: str, base_dir: Optional[Union[str, Path]] = None):
        """
        初始化剪映工程
        
        Args:
            project_name: 工程名称
            base_dir: 工程基础目录，如果不提供则使用临时目录
        """
        self.project_name = project_name
        
        # 设置工程目录
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.base_dir = Path(self.temp_dir.name)
        
        # 创建工程目录结构
        self.project_dir = self.base_dir / project_name
        self.resources_dir = self.project_dir / "resources"
        self.draft_dir = self.project_dir / "draft"
        
        # 创建XML模板处理器
        self.xml_processor = XMLTemplateProcessor()
        
        # 创建时间轴转换器
        self.timeline_converter = TimelineConverter()
        
        # 资源列表
        self.resources = []
        
        # 初始化目录
        self._init_directories()
    
    def _init_directories(self) -> None:
        """初始化工程目录结构"""
        # 创建主要目录
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.resources_dir.mkdir(parents=True, exist_ok=True)
        self.draft_dir.mkdir(parents=True, exist_ok=True)
    
    def set_project_info(self, project_info: Dict[str, Any]) -> None:
        """
        设置工程信息
        
        Args:
            project_info: 工程信息字典
        """
        # 更新工程名称（如果提供）
        if "name" in project_info:
            self.project_name = project_info["name"]
        
        # 填充XML模板中的项目元数据
        self.xml_processor.fill_project_meta(project_info)
    
    def set_timeline(self, timeline_data: Dict[str, Any]) -> None:
        """
        设置时间轴
        
        Args:
            timeline_data: 时间轴数据字典
        """
        # 设置帧率
        if "attributes" in timeline_data and "fps" in timeline_data["attributes"]:
            fps = float(timeline_data["attributes"]["fps"])
            self.timeline_converter.set_fps(fps)
        
        # 填充XML模板中的时间轴
        self.xml_processor.fill_timeline(timeline_data)
    
    def add_resource(self, resource_id: str, resource_type: str, file_path: Union[str, Path], 
                   copy_file: bool = True, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加资源
        
        Args:
            resource_id: 资源ID
            resource_type: 资源类型（video, audio, image等）
            file_path: 资源文件路径
            copy_file: 是否复制文件到工程目录
            metadata: 资源元数据
            
        Returns:
            是否成功添加
        """
        file_path = Path(file_path)
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"资源文件不存在: {file_path}")
            return False
        
        # 创建资源类型目录
        resource_type_dir = self.resources_dir / resource_type
        resource_type_dir.mkdir(exist_ok=True)
        
        # 目标文件路径
        target_filename = file_path.name
        target_path = resource_type_dir / target_filename
        
        # 如果需要，复制文件到资源目录
        if copy_file:
            try:
                shutil.copy2(file_path, target_path)
                logger.info(f"已复制资源文件: {file_path} -> {target_path}")
            except Exception as e:
                logger.error(f"复制资源文件失败: {str(e)}")
                return False
        
        # 构建资源信息
        resource_info = {
            "id": resource_id,
            "type": resource_type,
            "path": str(target_path.relative_to(self.project_dir)),
        }
        
        # 添加元数据
        if metadata:
            resource_info["metadata"] = metadata
        
        # 添加到资源列表
        self.resources.append(resource_info)
        
        return True
    
    def set_export_settings(self, export_settings: Dict[str, Any]) -> None:
        """
        设置导出设置
        
        Args:
            export_settings: 导出设置字典
        """
        self.xml_processor.fill_export_settings(export_settings)
    
    def set_legal_info(self, legal_info: Dict[str, str]) -> None:
        """
        设置法律声明信息
        
        Args:
            legal_info: 法律声明信息字典
        """
        self.xml_processor.inject_legal_info(legal_info)
    
    def validate(self) -> bool:
        """
        验证工程
        
        Returns:
            是否验证通过
        """
        # 填充资源数据到XML
        self.xml_processor.fill_resources(self.resources)
        
        # 验证XML
        return self.xml_processor.validate()
    
    def save_project_file(self) -> bool:
        """
        保存工程文件
        
        Returns:
            是否成功保存
        """
        # 填充资源数据到XML
        self.xml_processor.fill_resources(self.resources)
        
        # 保存主工程文件
        project_file_path = self.draft_dir / f"{self.project_name}.xml"
        return self.xml_processor.save(project_file_path)
    
    def export_project_package(self, output_path: Union[str, Path]) -> bool:
        """
        导出工程包
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功导出
        """
        output_path = Path(output_path)
        
        # 保存工程文件
        if not self.save_project_file():
            logger.error("保存工程文件失败，无法导出工程包")
            return False
        
        # 创建工程包目录
        project_info_path = self.project_dir / "project_info.json"
        
        # 保存工程信息
        try:
            with open(project_info_path, "w", encoding="utf-8") as f:
                json.dump({
                    "name": self.project_name,
                    "version": "1.0",
                    "creation_time": self.xml_processor.root.find("project_meta/creation_time").text
                    if self.xml_processor.root.find("project_meta/creation_time") is not None
                    else "",
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存工程信息失败: {str(e)}")
            return False
        
        # 创建工程包
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # 添加工程文件
                for root, dirs, files in os.walk(self.project_dir):
                    root_path = Path(root)
                    for file in files:
                        file_path = root_path / file
                        zipf.write(
                            file_path,
                            file_path.relative_to(self.base_dir)
                        )
            
            logger.info(f"已导出工程包: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出工程包失败: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """清理临时文件"""
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()


# 模块函数

def create_project(project_name: str, base_dir: Optional[Union[str, Path]] = None) -> JianyingProject:
    """
    创建剪映工程
    
    Args:
        project_name: 工程名称
        base_dir: 工程基础目录
        
    Returns:
        剪映工程实例
    """
    return JianyingProject(project_name, base_dir)

def export_project(
    project_name: str,
    timeline_data: Dict[str, Any],
    resources: List[Dict[str, Any]],
    output_path: Union[str, Path],
    project_info: Optional[Dict[str, Any]] = None,
    export_settings: Optional[Dict[str, Any]] = None,
    legal_info: Optional[Dict[str, str]] = None,
) -> bool:
    """
    导出剪映工程
    
    Args:
        project_name: 工程名称
        timeline_data: 时间轴数据
        resources: 资源列表
        output_path: 输出文件路径
        project_info: 工程信息
        export_settings: 导出设置
        legal_info: 法律声明信息
        
    Returns:
        是否成功导出
    """
    # 创建工程
    project = JianyingProject(project_name)
    
    # 设置工程信息
    if project_info:
        project.set_project_info(project_info)
    else:
        project.set_project_info({"name": project_name})
    
    # 设置时间轴
    project.set_timeline(timeline_data)
    
    # 添加资源
    for resource in resources:
        if "id" in resource and "type" in resource and "path" in resource:
            metadata = resource.get("metadata", {})
            project.add_resource(
                resource["id"],
                resource["type"],
                resource["path"],
                copy_file=True,
                metadata=metadata
            )
    
    # 设置导出设置
    if export_settings:
        project.set_export_settings(export_settings)
    
    # 设置法律声明
    if legal_info:
        project.set_legal_info(legal_info)
    else:
        # 默认法律声明
        project.set_legal_info({
            "copyright": f"© {project_name}",
            "data_processing": "本导出内容符合GDPR和中国个人信息保护法规定。"
        })
    
    # 验证工程
    if not project.validate():
        logger.error("工程验证失败")
        project.cleanup()
        return False
    
    # 导出工程包
    success = project.export_project_package(output_path)
    
    # 清理临时文件
    project.cleanup()
    
    return success


if __name__ == "__main__":
    # 测试代码
    project = JianyingProject("测试工程")
    
    # 设置工程信息
    project.set_project_info({
        "name": "测试工程",
        "author": "测试用户",
        "description": "这是一个测试工程"
    })
    
    # 设置时间轴
    project.set_timeline({
        "attributes": {"fps": "30", "duration": "60.0"},
        "tracks": [
            {
                "type": "video",
                "id": "track_video_1",
                "clips": [
                    {
                        "id": "clip_1",
                        "start": "0.0",
                        "duration": "30.0",
                        "media_id": "media_1"
                    }
                ]
            }
        ]
    })
    
    # 设置法律声明
    project.set_legal_info({
        "copyright": "© 2023 测试工程",
        "license": "仅供测试使用",
        "data_processing": "本导出内容符合GDPR和中国个人信息保护法规定。"
    })
    
    # 验证工程
    if project.validate():
        print("工程验证通过")
        
        # 导出工程包
        output_path = Path("测试工程.zip")
        if project.export_project_package(output_path):
            print(f"已导出工程包: {output_path}")
    else:
        print("工程验证失败")
    
    # 清理临时文件
    project.cleanup() 