#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Metadata Validator for VisionAI-ClipsMaster
Validates model metadata configuration files
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any

class MetaValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_meta(self, meta_path: str) -> bool:
        """验证模型元数据文件"""
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)
                
            # 验证基本结构
            required_sections = [
                'format_version',
                'model_info',
                'quantization_levels',
                'runtime_settings',
                'memory_management',
                'optimization',
                'error_handling',
                'monitoring'
            ]
            
            for section in required_sections:
                if section not in meta:
                    self.logger.error(f"Missing required section: {section}")
                    return False
                    
            # 验证量化配置
            if not self._validate_quantization(meta['quantization_levels']):
                return False
                
            # 验证内存管理配置
            if not self._validate_memory_management(meta['memory_management']):
                return False
                
            # 验证运行时设置
            if not self._validate_runtime_settings(meta['runtime_settings']):
                return False
                
            self.logger.info(f"Successfully validated metadata: {meta_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate metadata: {str(e)}")
            return False
            
    def _validate_quantization(self, quant_levels: List[Dict[str, Any]]) -> bool:
        """验证量化配置"""
        required_fields = ['name', 'memory_usage', 'compatible_devices']
        
        for level in quant_levels:
            for field in required_fields:
                if field not in level:
                    self.logger.error(f"Missing field in quantization level: {field}")
                    return False
                    
            # 验证内存使用值
            try:
                memory = float(level['memory_usage'].replace('GB', ''))
                if memory <= 0:
                    self.logger.error("Invalid memory usage value")
                    return False
            except ValueError:
                self.logger.error("Invalid memory usage format")
                return False
                
        return True
        
    def _validate_memory_management(self, memory_config: Dict[str, Any]) -> bool:
        """验证内存管理配置"""
        required_fields = ['min_free_memory', 'max_memory_usage', 'dynamic_unload']
        
        for field in required_fields:
            if field not in memory_config:
                self.logger.error(f"Missing memory management field: {field}")
                return False
                
        # 验证内存值
        if memory_config['min_free_memory'] <= 0:
            self.logger.error("Invalid min_free_memory value")
            return False
            
        if memory_config['max_memory_usage'] <= memory_config['min_free_memory']:
            self.logger.error("max_memory_usage must be greater than min_free_memory")
            return False
            
        return True
        
    def _validate_runtime_settings(self, runtime_config: Dict[str, Any]) -> bool:
        """验证运行时设置"""
        required_fields = ['default_batch_size', 'max_batch_size', 'context_size']
        
        for field in required_fields:
            if field not in runtime_config:
                self.logger.error(f"Missing runtime setting: {field}")
                return False
                
        # 验证批处理大小
        if runtime_config['default_batch_size'] > runtime_config['max_batch_size']:
            self.logger.error("default_batch_size cannot be greater than max_batch_size")
            return False
            
        return True

def validate_all_models():
    """验证所有模型的元数据"""
    validator = MetaValidator()
    models_path = Path("models")
    
    # 验证中文模型
    qwen_meta = models_path / "qwen" / "model_meta.yaml"
    if qwen_meta.exists():
        if not validator.validate_meta(str(qwen_meta)):
            raise ValueError("Qwen model metadata validation failed")
            
    # 验证英文模型（如果存在）
    mistral_meta = models_path / "mistral" / "model_meta.yaml"
    if mistral_meta.exists():
        if not validator.validate_meta(str(mistral_meta)):
            raise ValueError("Mistral model metadata validation failed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_all_models() 