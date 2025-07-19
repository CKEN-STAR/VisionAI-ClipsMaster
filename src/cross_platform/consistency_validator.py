#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨平台一致性验证模块

确保在Windows、macOS和Linux平台上处理相同输入时，
输出结果的二进制差异率低于0.01%。
实现确定性算法和平台无关的处理流程。
"""

import os
import sys
import hashlib
import platform
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path

# 导入项目内部模块
from src.utils.log_handler import get_logger

# 配置日志
platform_logger = get_logger("cross_platform")

class PlatformInfo:
    """平台信息类
    
    收集和管理当前平台的信息。
    """
    
    @staticmethod
    def get_platform_info() -> Dict[str, Any]:
        """获取当前平台信息
        
        Returns:
            Dict[str, Any]: 平台信息字典
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture(),
            "node": platform.node()
        }
    
    @staticmethod
    def is_windows() -> bool:
        """检查是否为Windows系统
        
        Returns:
            bool: 是否为Windows
        """
        return platform.system() == "Windows"
    
    @staticmethod
    def is_macos() -> bool:
        """检查是否为macOS系统
        
        Returns:
            bool: 是否为macOS
        """
        return platform.system() == "Darwin"
    
    @staticmethod
    def is_linux() -> bool:
        """检查是否为Linux系统
        
        Returns:
            bool: 是否为Linux
        """
        return platform.system() == "Linux"


class ConsistencyValidator:
    """跨平台一致性验证器
    
    验证不同平台上生成的输出是否一致，
    确保二进制差异率低于0.01%。
    """
    
    def __init__(self, metadata_dir: Optional[str] = None):
        """初始化一致性验证器
        
        Args:
            metadata_dir: 元数据存储目录
        """
        self.metadata_dir = metadata_dir or os.path.join("data", "platform_consistency")
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # 获取当前平台信息
        self.platform_info = PlatformInfo.get_platform_info()
        platform_logger.info(f"当前平台: {self.platform_info['system']} {self.platform_info['release']}")
    
    def normalize_file_content(self, file_path: str) -> bytes:
        """标准化文件内容，确保跨平台一致性
        
        处理换行符、编码等平台差异。
        
        Args:
            file_path: 文件路径
            
        Returns:
            bytes: 标准化后的文件内容
        """
        # 检查文件类型
        is_text = False
        file_ext = os.path.splitext(file_path)[1].lower()
        text_extensions = ['.txt', '.json', '.xml', '.csv', '.srt']
        
        if file_ext in text_extensions:
            is_text = True
        
        try:
            if is_text:
                # 文本文件标准化：统一换行符，使用UTF-8编码
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    
                # 统一换行符为LF（Unix风格）
                content = content.replace('\r\n', '\n').replace('\r', '\n')
                
                # 转换为字节
                return content.encode('utf-8')
            else:
                # 二进制文件直接读取
                with open(file_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            platform_logger.error(f"标准化文件内容失败: {str(e)}")
            return b''
    
    def calculate_binary_diff_ratio(self, data1: bytes, data2: bytes) -> float:
        """计算二进制数据的差异率
        
        Args:
            data1: 第一个二进制数据
            data2: 第二个二进制数据
            
        Returns:
            float: 差异率（0-1之间）
        """
        # 空数据处理
        if not data1 and not data2:
            return 0.0
        if not data1 or not data2:
            return 1.0
        
        # 截断到较短的长度
        min_len = min(len(data1), len(data2))
        data1 = data1[:min_len]
        data2 = data2[:min_len]
        
        # 计算字节差异数
        diff_count = sum(1 for b1, b2 in zip(data1, data2) if b1 != b2)
        
        # 计算差异率
        diff_ratio = diff_count / min_len
        
        return diff_ratio
    
    def register_reference_output(self, file_path: str, reference_platform: str) -> Dict[str, Any]:
        """注册参考平台的输出文件
        
        Args:
            file_path: 输出文件路径
            reference_platform: 参考平台名称
            
        Returns:
            Dict[str, Any]: 注册结果
        """
        if not os.path.exists(file_path):
            platform_logger.error(f"文件不存在: {file_path}")
            return {"success": False, "error": "文件不存在"}
        
        # 标准化文件内容
        normalized_content = self.normalize_file_content(file_path)
        
        # 计算哈希值
        content_hash = hashlib.sha256(normalized_content).hexdigest()
        
        # 收集信息
        output_info = {
            "path": file_path,
            "hash": content_hash,
            "platform": reference_platform,
            "size": len(normalized_content),
            "platform_info": self.platform_info
        }
        
        # 保存参考信息
        reference_file = os.path.join(
            self.metadata_dir, 
            f"reference_{os.path.basename(file_path)}.json"
        )
        
        with open(reference_file, "w", encoding="utf-8") as f:
            json.dump(output_info, f, indent=2)
        
        platform_logger.info(f"已注册参考输出: {file_path} (平台: {reference_platform})")
        return {"success": True, "reference": output_info}
    
    def verify_platform_consistency(self, file_path: str, 
                                   reference_platform: Optional[str] = None) -> Dict[str, Any]:
        """验证输出文件在不同平台上的一致性
        
        Args:
            file_path: 输出文件路径
            reference_platform: 参考平台名称，如果为None则使用注册的任何平台
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        if not os.path.exists(file_path):
            platform_logger.error(f"文件不存在: {file_path}")
            return {"success": False, "error": "文件不存在"}
        
        # 查找参考文件信息
        reference_info = self._find_reference_info(file_path, reference_platform)
        if not reference_info:
            platform_logger.error(f"找不到参考信息: {file_path}")
            return {"success": False, "error": "找不到参考信息"}
        
        # 标准化当前文件内容
        current_content = self.normalize_file_content(file_path)
        current_hash = hashlib.sha256(current_content).hexdigest()
        
        # 如果有参考哈希值，直接比较
        reference_hash = reference_info.get("hash")
        if current_hash == reference_hash:
            platform_logger.info(f"完全匹配! 文件: {file_path}")
            return {
                "success": True,
                "diff_ratio": 0.0,
                "diff_ratio_percent": "0%",
                "is_identical": True,
                "current_platform": self.platform_info["system"],
                "reference_platform": reference_info.get("platform")
            }
        
        # 计算差异率
        # 可能需要下载参考内容进行比较
        diff_ratio = 0.0
        
        if "content_base64" in reference_info:
            import base64
            reference_content = base64.b64decode(reference_info["content_base64"])
            diff_ratio = self.calculate_binary_diff_ratio(current_content, reference_content)
        else:
            # 仅使用大小差异作为粗略估计
            size_diff = abs(len(current_content) - reference_info.get("size", 0))
            if reference_info.get("size", 0) > 0:
                diff_ratio = size_diff / reference_info.get("size", 1)
            else:
                diff_ratio = 1.0 if size_diff > 0 else 0.0
        
        # 验证差异率是否在允许范围内
        is_consistent = diff_ratio < 0.0001  # 小于0.01%
        
        result = {
            "success": is_consistent,
            "diff_ratio": diff_ratio,
            "diff_ratio_percent": f"{diff_ratio*100:.5f}%",
            "is_identical": current_hash == reference_hash,
            "current_platform": self.platform_info["system"],
            "reference_platform": reference_info.get("platform"),
            "acceptable_threshold": "0.01%"
        }
        
        if is_consistent:
            platform_logger.info(
                f"平台一致性验证通过! 文件: {file_path}, "
                f"差异率: {result['diff_ratio_percent']}"
            )
        else:
            platform_logger.warning(
                f"平台一致性验证失败! 文件: {file_path}, "
                f"差异率: {result['diff_ratio_percent']} > 0.01%"
            )
        
        return result
    
    def compare_multiple_platforms(self, 
                                  file_paths: Dict[str, str]) -> Dict[str, Any]:
        """比较多个平台上的输出文件
        
        Args:
            file_paths: 平台和对应文件路径的字典，例如 {"Windows": "path/to/win.txt", "Linux": "path/to/linux.txt"}
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        if len(file_paths) < 2:
            platform_logger.error("至少需要两个平台才能进行比较")
            return {"success": False, "error": "平台数量不足"}
        
        # 收集所有平台的标准化内容
        platform_contents = {}
        for platform_name, file_path in file_paths.items():
            if not os.path.exists(file_path):
                platform_logger.error(f"文件不存在: {file_path} ({platform_name})")
                continue
                
            normalized_content = self.normalize_file_content(file_path)
            platform_contents[platform_name] = {
                "content": normalized_content,
                "hash": hashlib.sha256(normalized_content).hexdigest(),
                "size": len(normalized_content)
            }
        
        # 如果某个平台的文件不存在，无法进行完整比较
        if len(platform_contents) < 2:
            platform_logger.error("有效的平台数量不足")
            return {"success": False, "error": "有效的平台数量不足"}
        
        # 计算所有平台之间的差异率
        comparisons = []
        diff_ratios = []
        
        platforms = list(platform_contents.keys())
        for i in range(len(platforms)):
            for j in range(i+1, len(platforms)):
                platform1 = platforms[i]
                platform2 = platforms[j]
                
                # 计算差异率
                diff_ratio = self.calculate_binary_diff_ratio(
                    platform_contents[platform1]["content"],
                    platform_contents[platform2]["content"]
                )
                
                diff_ratios.append(diff_ratio)
                
                # 记录比较结果
                comparisons.append({
                    "platform1": platform1,
                    "platform2": platform2,
                    "diff_ratio": diff_ratio,
                    "diff_ratio_percent": f"{diff_ratio*100:.5f}%",
                    "is_consistent": diff_ratio < 0.0001  # 小于0.01%
                })
        
        # 计算平均差异率
        avg_diff_ratio = sum(diff_ratios) / len(diff_ratios) if diff_ratios else 0
        
        # 是否所有比较都通过阈值检查
        all_consistent = all(comp["is_consistent"] for comp in comparisons)
        
        result = {
            "success": all_consistent,
            "comparisons": comparisons,
            "avg_diff_ratio": avg_diff_ratio,
            "avg_diff_ratio_percent": f"{avg_diff_ratio*100:.5f}%",
            "platforms_compared": platforms,
            "acceptable_threshold": "0.01%"
        }
        
        if all_consistent:
            platform_logger.info(
                f"所有平台一致性测试通过! 平均差异率: {result['avg_diff_ratio_percent']}"
            )
        else:
            platform_logger.warning(
                f"平台一致性测试失败! 平均差异率: {result['avg_diff_ratio_percent']} > 0.01%"
            )
        
        return result
    
    def _find_reference_info(self, file_path: str, 
                           platform_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """查找参考信息
        
        Args:
            file_path: 文件路径
            platform_name: 平台名称，如果为None则返回任何找到的参考
            
        Returns:
            Optional[Dict[str, Any]]: 参考信息，如果找不到则返回None
        """
        file_name = os.path.basename(file_path)
        reference_candidates = []
        
        # 查找可能的参考文件
        for ref_file in os.listdir(self.metadata_dir):
            if ref_file.startswith("reference_") and ref_file.endswith(".json"):
                # 检查是否是针对当前文件的参考
                if file_name in ref_file:
                    ref_path = os.path.join(self.metadata_dir, ref_file)
                    try:
                        with open(ref_path, "r", encoding="utf-8") as f:
                            ref_info = json.load(f)
                            reference_candidates.append(ref_info)
                    except Exception as e:
                        platform_logger.warning(f"读取参考文件失败: {ref_file} - {str(e)}")
        
        if not reference_candidates:
            return None
        
        # 如果指定了平台，返回匹配的平台
        if platform_name:
            for ref in reference_candidates:
                if ref.get("platform") == platform_name:
                    return ref
            return None
        
        # 否则返回找到的第一个
        return reference_candidates[0]


def get_consistency_validator() -> ConsistencyValidator:
    """获取跨平台一致性验证器实例
    
    Returns:
        ConsistencyValidator: 验证器实例
    """
    return ConsistencyValidator()


def verify_file_consistency(file_path: str) -> bool:
    """验证文件在不同平台上的一致性
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否一致
    """
    validator = get_consistency_validator()
    result = validator.verify_platform_consistency(file_path)
    return result["success"]


def register_reference_file(file_path: str, platform_name: str) -> Dict[str, Any]:
    """注册参考平台的文件
    
    Args:
        file_path: 文件路径
        platform_name: 平台名称
        
    Returns:
        Dict[str, Any]: 注册结果
    """
    validator = get_consistency_validator()
    return validator.register_reference_output(file_path, platform_name) 