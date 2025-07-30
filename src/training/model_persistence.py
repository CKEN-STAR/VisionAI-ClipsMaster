#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型持久化
负责模型的保存和加载
"""

import logging
import pickle
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelPersistence:
    """模型持久化管理器"""
    
    def __init__(self):
        """初始化模型持久化管理器"""
        logger.info("模型持久化管理器初始化完成")
    
    def save_model(self, model_data: Dict[str, Any], file_path: str) -> bool:
        """
        保存模型
        
        Args:
            model_data: 模型数据
            file_path: 保存路径
            
        Returns:
            是否保存成功
        """
        try:
            logger.info(f"保存模型到: {file_path}")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 根据文件扩展名选择保存格式
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(model_data, f, ensure_ascii=False, indent=2)
            else:
                # 默认使用pickle
                with open(file_path, 'wb') as f:
                    pickle.dump(model_data, f)
            
            logger.info(f"模型保存成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
            return False
    
    def load_model(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        加载模型
        
        Args:
            file_path: 模型文件路径
            
        Returns:
            模型数据，如果加载失败返回None
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"模型文件不存在: {file_path}")
                return None
            
            logger.info(f"加载模型: {file_path}")
            
            # 根据文件扩展名选择加载格式
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    model_data = json.load(f)
            else:
                # 默认使用pickle
                with open(file_path, 'rb') as f:
                    model_data = pickle.load(f)
            
            logger.info(f"模型加载成功: {file_path}")
            return model_data
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return None
    
    def list_saved_models(self, models_dir: str) -> list:
        """
        列出已保存的模型
        
        Args:
            models_dir: 模型目录
            
        Returns:
            模型文件列表
        """
        try:
            if not os.path.exists(models_dir):
                return []
            
            model_files = []
            for file_name in os.listdir(models_dir):
                if file_name.endswith(('.pkl', '.json', '.pt', '.pth')):
                    file_path = os.path.join(models_dir, file_name)
                    file_info = {
                        "name": file_name,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "modified_time": os.path.getmtime(file_path)
                    }
                    model_files.append(file_info)
            
            return model_files
            
        except Exception as e:
            logger.error(f"列出模型文件失败: {e}")
            return []
    
    def delete_model(self, file_path: str) -> bool:
        """
        删除模型文件
        
        Args:
            file_path: 模型文件路径
            
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"模型文件已删除: {file_path}")
                return True
            else:
                logger.warning(f"模型文件不存在: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"删除模型文件失败: {e}")
            return False
