#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量导出流水线模块

批量导出多个版本到不同格式的文件
"""

import os
import json
import logging
import tempfile
import zipfile
import shutil
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.export.base_exporter import BaseExporter
from src.export.jianying_exporter import JianyingExporter
from src.export.premiere_exporter import PremiereXMLExporter
from src.export.fcpxml_exporter import FCPXMLExporter
from src.export.srt_exporter import SRTExporter
from src.utils.log_handler import get_logger

# 配置日志
logger = get_logger("batch_exporter")

def create_temp_folder() -> str:
    """
    创建临时文件夹
    
    Returns:
        临时文件夹路径
    """
    temp_dir = os.path.join(tempfile.gettempdir(), f"visionai_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

class BatchExportPipeline:
    """
    批量导出流水线
    
    批量导出多个版本到不同格式
    """
    
    def __init__(self):
        """初始化批量导出流水线"""
        self.formats = {
            "剪映": JianyingExporter,
            "Premiere": PremiereXMLExporter,
            "FCPX": FCPXMLExporter,
            "SRT": SRTExporter
        }
    
    def mass_export(self, versions: List[Dict[str, Any]], format_names: List[str]) -> str:
        """
        批量导出多个版本到多个格式
        
        Args:
            versions: 版本列表
            format_names: 要导出的格式名称列表
            
        Returns:
            导出的压缩包路径
        """
        # 创建临时文件夹
        output_dir = create_temp_folder()
        
        try:
            # 检查格式是否支持
            for fmt in format_names:
                if fmt not in self.formats:
                    logger.error(f"不支持的导出格式: {fmt}")
                    raise ValueError(f"不支持的导出格式: {fmt}")
            
            # 对每个格式和每个版本进行导出
            for fmt in format_names:
                # 创建格式对应的目录
                fmt_dir = os.path.join(output_dir, fmt)
                os.makedirs(fmt_dir, exist_ok=True)
                
                # 获取导出器类
                exporter_class = self.formats[fmt]
                # 创建导出器实例
                exporter = exporter_class()
                
                # 使用线程池并行导出多个版本
                with ThreadPoolExecutor(max_workers=min(8, len(versions))) as executor:
                    futures = []
                    
                    # 提交导出任务
                    for v in versions:
                        # 获取版本ID
                        version_id = v.get('version_id', 'unknown')
                        
                        # 构建输出路径
                        ext = '.json' if fmt == '剪映' else '.xml' if fmt in ['Premiere', 'FCPX'] else '.srt'
                        output_path = os.path.join(fmt_dir, f"{version_id}{ext}")
                        
                        # 提交任务
                        future = executor.submit(exporter.export, v, output_path)
                        futures.append((future, version_id, fmt))
                    
                    # 等待所有任务完成
                    for future, version_id, fmt_name in futures:
                        try:
                            result = future.result()
                            logger.info(f"成功导出 版本 {version_id} 为 {fmt_name} 格式")
                        except Exception as e:
                            logger.error(f"导出 版本 {version_id} 为 {fmt_name} 格式失败: {str(e)}")
            
            # 创建压缩包
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(os.path.dirname(output_dir), f"export_result_{timestamp}.zip")
            
            # 压缩整个输出目录
            return compress_folder(output_dir, zip_path)
            
        except Exception as e:
            logger.error(f"批量导出失败: {str(e)}")
            raise
            
        finally:
            # 清理临时目录
            try:
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
            except Exception as e:
                logger.warning(f"清理临时目录失败: {str(e)}")
    
    def export_single_version(self, version: Dict[str, Any], format_names: List[str], 
                            output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        导出单个版本到多个格式
        
        Args:
            version: 版本数据
            format_names: 要导出的格式名称列表
            output_dir: 输出目录，如果为None则使用临时目录
            
        Returns:
            各格式的输出路径字典
        """
        # 使用提供的输出目录或创建临时目录
        if output_dir is None:
            output_dir = create_temp_folder()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 结果字典
        result_paths = {}
        
        # 获取版本ID
        version_id = version.get('version_id', 'unknown')
        
        # 对每个格式进行导出
        for fmt in format_names:
            if fmt not in self.formats:
                logger.warning(f"跳过不支持的格式: {fmt}")
                continue
            
            try:
                # 获取导出器类并创建实例
                exporter_class = self.formats[fmt]
                exporter = exporter_class()
                
                # 构建输出路径
                ext = '.json' if fmt == '剪映' else '.xml' if fmt in ['Premiere', 'FCPX'] else '.srt'
                output_path = os.path.join(output_dir, f"{version_id}_{fmt}{ext}")
                
                # 导出文件
                result_path = exporter.export(version, output_path)
                
                # 记录结果
                result_paths[fmt] = result_path
                
                logger.info(f"成功导出 版本 {version_id} 为 {fmt} 格式: {result_path}")
                
            except Exception as e:
                logger.error(f"导出 版本 {version_id} 为 {fmt} 格式失败: {str(e)}")
        
        return result_paths


def compress_folder(folder_path: str, output_path: str) -> str:
    """
    压缩文件夹为ZIP文件
    
    Args:
        folder_path: 要压缩的文件夹路径
        output_path: 输出的ZIP文件路径
        
    Returns:
        输出的ZIP文件路径
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建ZIP文件
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 遍历文件夹中的所有文件
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径
                    rel_path = os.path.relpath(file_path, folder_path)
                    # 添加到ZIP
                    zipf.write(file_path, rel_path)
        
        logger.info(f"已创建压缩包: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"创建压缩包失败: {str(e)}")
        raise


# 创建全局单例
batch_exporter = BatchExportPipeline()

def export_versions(versions: List[Dict[str, Any]], format_names: List[str]) -> str:
    """
    便捷函数：批量导出多个版本
    
    Args:
        versions: 版本列表
        format_names: 要导出的格式名称列表
        
    Returns:
        导出的压缩包路径
    """
    return batch_exporter.mass_export(versions, format_names)

def export_version(version: Dict[str, Any], format_names: List[str], 
                 output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    便捷函数：导出单个版本到多个格式
    
    Args:
        version: 版本数据
        format_names: 要导出的格式名称列表
        output_dir: 输出目录，如果为None则使用临时目录
        
    Returns:
        各格式的输出路径字典
    """
    return batch_exporter.export_single_version(version, format_names, output_dir)


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试版本
    test_version = {
        "version_id": "test_v1",
        "scenes": [
            {
                "scene_id": "scene_1",
                "text": "这是第一个场景",
                "start_time": 0,
                "duration": 5
            },
            {
                "scene_id": "scene_2",
                "text": "这是第二个场景",
                "start_time": 10,
                "duration": 8
            }
        ],
        "video_path": "D:/test_video.mp4"  # 假设的视频路径
    }
    
    # 导出测试
    try:
        output_dir = "./test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        result = export_version(test_version, ["SRT", "剪映"], output_dir)
        
        for fmt, path in result.items():
            print(f"已导出 {fmt} 格式: {path}")
            
    except Exception as e:
        print(f"测试失败: {str(e)}") 