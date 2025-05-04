#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model verification system for ensuring model integrity and system compatibility
"""

import os
import json
import yaml
import hashlib
import logging
import psutil
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ModelChecker:
    """模型完整性和兼容性检查器"""
    
    def __init__(self, models_dir: Optional[Path] = None):
        """
        初始化模型检查器
        
        Args:
            models_dir: 模型目录路径，默认为 ./models
        """
        self.models_dir = models_dir or Path("./models")
        self.required_files = [
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json"
        ]
        
    def _verify_model_files(self, model_dir: Path) -> bool:
        """
        验证模型目录中的必要文件是否存在且完整
        
        Args:
            model_dir: 模型目录路径
            
        Returns:
            bool: 验证是否通过
        """
        try:
            for file in self.required_files:
                file_path = model_dir / file
                if not file_path.is_file():
                    logger.error(f"Missing required file: {file}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Error verifying model files: {e}")
            return False
            
    def _verify_metadata(self, model_name: str) -> bool:
        """
        验证模型的元数据是否有效
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 验证是否通过
        """
        try:
            model_family = model_name.split("-")[0]
            meta_path = self.models_dir / model_family / "model_meta.yaml"
            
            if not meta_path.exists():
                logger.error(f"Metadata file not found: {meta_path}")
                return False
                
            with open(meta_path) as f:
                metadata = yaml.safe_load(f)
                
            # 验证必要的元数据字段
            required_fields = ["format_version", "model_info", "quantization_levels"]
            for field in required_fields:
                if field not in metadata:
                    logger.error(f"Missing required metadata field: {field}")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Error verifying metadata: {e}")
            return False
            
    def _generate_checksums(self, model_dir: Path, checksum_file: Path) -> bool:
        """
        生成模型文件的校验和
        
        Args:
            model_dir: 模型目录路径
            checksum_file: 校验和文件路径
            
        Returns:
            bool: 是否成功生成校验和
        """
        try:
            checksums = {}
            for file in model_dir.glob("**/*"):
                if file.is_file():
                    with open(file, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        checksums[str(file.relative_to(model_dir))] = file_hash
                        
            checksum_file.parent.mkdir(parents=True, exist_ok=True)
            with open(checksum_file, "w") as f:
                json.dump(checksums, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error generating checksums: {e}")
            return False
            
    def _verify_memory_requirements(self, model_name: str) -> bool:
        """
        验证系统内存是否满足模型要求
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 验证是否通过
        """
        try:
            model_family = model_name.split("-")[0]
            meta_path = self.models_dir / model_family / "model_meta.yaml"
            
            with open(meta_path) as f:
                metadata = yaml.safe_load(f)
                
            # 获取推荐的量化级别
            recommended_quant = next(
                (q for q in metadata["quantization_levels"] if q.get("recommended")),
                metadata["quantization_levels"][0]
            )
            
            # 解析内存需求
            memory_str = recommended_quant["memory_usage"]
            memory_value = float(memory_str.rstrip("GB"))
            required_bytes = memory_value * 1024 * 1024 * 1024
            
            # 检查系统内存
            system_memory = psutil.virtual_memory().total
            if system_memory < required_bytes * 1.2:  # 需要额外20%的缓冲
                logger.error(f"Insufficient memory: {memory_str} required, {system_memory / 1024**3:.1f}GB available")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error verifying memory requirements: {e}")
            return False
            
    def _verify_quantized_versions(self, model_name: str) -> bool:
        """
        验证量化版本是否存在且完整
        
        Args:
            model_name: 模型名称
            
        Returns:
            bool: 验证是否通过
        """
        try:
            model_family = model_name.split("-")[0]
            quant_dir = self.models_dir / model_family / "quantized"
            
            if not quant_dir.exists():
                logger.error(f"Quantized directory not found: {quant_dir}")
                return False
                
            # 检查是否存在至少一个量化版本
            gguf_files = list(quant_dir.glob("*.gguf"))
            if not gguf_files:
                logger.error("No quantized versions found")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error verifying quantized versions: {e}")
            return False

def verify_model_integrity(model_name: str) -> bool:
    """
    验证模型的完整性和系统兼容性
    
    Args:
        model_name: 模型名称
        
    Returns:
        bool: 验证是否全部通过
    """
    try:
        checker = ModelChecker()
        model_family = model_name.split("-")[0]
        model_dir = checker.models_dir / model_family / "base"
        
        # 执行所有验证步骤
        verifications = [
            checker._verify_model_files(model_dir),
            checker._verify_metadata(model_name),
            checker._verify_memory_requirements(model_name),
            checker._verify_quantized_versions(model_name)
        ]
        
        # 生成新的校验和
        checksum_file = checker.models_dir / "checksums" / f"{model_family}_checksums.json"
        checker._generate_checksums(model_dir, checksum_file)
        
        return all(verifications)
    except Exception as e:
        logger.error(f"Error during model verification: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 验证中文模型
    verify_model_integrity("qwen2.5-7b-zh") 