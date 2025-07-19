#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练管理器模块

负责处理模型训练相关功能，实现"投喂训练"功能，
让模型学习用户提供的原片字幕和混剪字幕对应关系，
从而提高混剪质量和符合特定风格的能力。
"""

import os
import json
import logging
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 导入相关模块
from src.core.language_detector import LanguageDetector
from src.core.model_loader import ModelLoader
from src.utils.log_handler import get_logger

# 设置日志
logger = get_logger("train_manager")

class TrainManager:
    """训练管理器类"""
    
    def __init__(self, models_dir: str = "models", data_dir: str = "data/training"):
        """初始化训练管理器
        
        Args:
            models_dir: 模型目录路径
            data_dir: 训练数据目录路径
        """
        self.models_dir = Path(models_dir)
        self.data_dir = Path(data_dir)
        self.language_detector = LanguageDetector()
        self.model_loader = ModelLoader()
        
        # 创建必要的目录
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "zh").mkdir(exist_ok=True)
        (self.data_dir / "en").mkdir(exist_ok=True)
        
        # 训练记录文件
        self.training_log_path = self.data_dir / "training_history.json"
        self.training_history = self._load_training_history()
        
        logger.info("训练管理器初始化完成")
    
    def _load_training_history(self) -> List[Dict[str, Any]]:
        """加载训练历史记录"""
        if not self.training_log_path.exists():
            return []
        
        try:
            with open(self.training_log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载训练历史记录失败: {e}")
            return []
    
    def _save_training_history(self) -> None:
        """保存训练历史记录"""
        try:
            with open(self.training_log_path, 'w', encoding='utf-8') as f:
                json.dump(self.training_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存训练历史记录失败: {e}")
    
    def add_training_pair(self, original_subtitles: List[Dict[str, Any]],
                         remix_subtitles: List[Dict[str, Any]],
                         language: str,
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """添加训练数据对
        
        Args:
            original_subtitles: 原片字幕列表
            remix_subtitles: 混剪字幕列表
            language: 语言代码 ('zh'或'en')
            metadata: 元数据(可选)
            
        Returns:
            处理结果信息
        """
        try:
            # 生成唯一ID
            pair_id = f"pair_{int(time.time())}_{random.randint(1000, 9999)}"
            timestamp = datetime.now().isoformat()
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "timestamp": timestamp,
                "language": language,
                "original_count": len(original_subtitles),
                "remix_count": len(remix_subtitles)
            })
            
            # 准备训练数据
            training_data = {
                "id": pair_id,
                "metadata": metadata,
                "original_subtitles": original_subtitles,
                "remix_subtitles": remix_subtitles,
                "training_status": "pending"
            }
            
            # 保存训练数据
            data_path = self.data_dir / language / f"{pair_id}.json"
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            # 更新训练历史记录
            history_entry = {
                "id": pair_id,
                "timestamp": timestamp,
                "language": language,
                "original_count": len(original_subtitles),
                "remix_count": len(remix_subtitles),
                "status": "pending",
                "data_path": str(data_path)
            }
            
            self.training_history.append(history_entry)
            self._save_training_history()
            
            logger.info(f"成功添加训练数据对 {pair_id}, 语言: {language}")
            
            return {
                "status": "success",
                "pair_id": pair_id,
                "language": language,
                "data_path": str(data_path)
            }
            
        except Exception as e:
            logger.error(f"添加训练数据对失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def train_model(self, pair_id: Optional[str] = None, language: Optional[str] = None) -> Dict[str, Any]:
        """训练模型
        
        Args:
            pair_id: 特定训练数据对ID，如果为None则训练所有待处理数据
            language: 特定语言的模型，如果为None则处理所有语言
            
        Returns:
            训练结果信息
        """
        # 模拟训练过程（实际实现中需要接入模型训练逻辑）
        logger.info(f"开始训练模型, pair_id={pair_id}, language={language}")
        
        # 获取待训练数据
        if pair_id:
            # 查找特定训练数据对
            for entry in self.training_history:
                if entry["id"] == pair_id and entry["status"] == "pending":
                    training_entries = [entry]
                    break
            else:
                return {"status": "error", "error": f"找不到待处理的训练数据对: {pair_id}"}
        else:
            # 筛选待处理的训练数据
            training_entries = [
                entry for entry in self.training_history
                if entry["status"] == "pending" and (language is None or entry["language"] == language)
            ]
        
        if not training_entries:
            return {
                "status": "info",
                "message": "没有待处理的训练数据"
            }
        
        # 处理每个训练数据
        results = []
        for entry in training_entries:
            try:
                # 加载训练数据
                with open(entry["data_path"], 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                
                # 模拟训练过程
                logger.info(f"正在训练数据对 {entry['id']}, 语言: {entry['language']}")
                time.sleep(2)  # 实际训练中应替换为真正的训练代码
                
                # 更新训练状态
                entry["status"] = "completed"
                entry["completed_at"] = datetime.now().isoformat()
                
                # 更新训练数据文件
                training_data["training_status"] = "completed"
                training_data["completed_at"] = entry["completed_at"]
                
                with open(entry["data_path"], 'w', encoding='utf-8') as f:
                    json.dump(training_data, f, ensure_ascii=False, indent=2)
                
                results.append({
                    "pair_id": entry["id"],
                    "language": entry["language"],
                    "status": "success"
                })
                
                logger.info(f"训练数据对 {entry['id']} 处理完成")
                
            except Exception as e:
                logger.error(f"训练数据对 {entry['id']} 处理失败: {e}")
                entry["status"] = "failed"
                entry["error"] = str(e)
                
                results.append({
                    "pair_id": entry["id"],
                    "language": entry["language"],
                    "status": "error",
                    "error": str(e)
                })
        
        # 保存更新后的训练历史
        self._save_training_history()
        
        return {
            "status": "success",
            "processed_count": len(results),
            "results": results
        }
    
    def get_training_history(self, language: Optional[str] = None, 
                            status: Optional[str] = None,
                            limit: int = 50) -> List[Dict[str, Any]]:
        """获取训练历史
        
        Args:
            language: 筛选特定语言
            status: 筛选特定状态
            limit: 返回结果数量限制
            
        Returns:
            训练历史列表
        """
        # 筛选历史记录
        filtered_history = self.training_history
        
        if language:
            filtered_history = [entry for entry in filtered_history if entry["language"] == language]
        
        if status:
            filtered_history = [entry for entry in filtered_history if entry["status"] == status]
        
        # 按时间降序排序并限制数量
        sorted_history = sorted(filtered_history, key=lambda x: x["timestamp"], reverse=True)
        limited_history = sorted_history[:limit]
        
        return limited_history
    
    def get_training_stats(self) -> Dict[str, Any]:
        """获取训练统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total": len(self.training_history),
            "by_language": {"zh": 0, "en": 0},
            "by_status": {"pending": 0, "completed": 0, "failed": 0},
            "latest_timestamp": None
        }
        
        for entry in self.training_history:
            # 按语言统计
            lang = entry.get("language", "unknown")
            if lang in stats["by_language"]:
                stats["by_language"][lang] += 1
            else:
                stats["by_language"][lang] = 1
            
            # 按状态统计
            status = entry.get("status", "unknown")
            if status in stats["by_status"]:
                stats["by_status"][status] += 1
            else:
                stats["by_status"][status] = 1
            
            # 更新最新时间戳
            timestamp = entry.get("timestamp")
            if timestamp and (stats["latest_timestamp"] is None or timestamp > stats["latest_timestamp"]):
                stats["latest_timestamp"] = timestamp
        
        return stats


# 单例模式实现
_train_manager_instance = None

def get_train_manager() -> TrainManager:
    """获取训练管理器实例"""
    global _train_manager_instance
    if _train_manager_instance is None:
        _train_manager_instance = TrainManager()
    return _train_manager_instance


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    original_subtitles = [
        {"id": 1, "start_time": 0.0, "end_time": 5.0, "text": "这是原片字幕1"},
        {"id": 2, "start_time": 5.5, "end_time": 10.0, "text": "这是原片字幕2"},
        {"id": 3, "start_time": 10.5, "end_time": 15.0, "text": "这是原片字幕3"}
    ]
    
    remix_subtitles = [
        {"id": 1, "start_time": 0.0, "end_time": 7.0, "text": "这是混剪字幕1"},
        {"id": 2, "start_time": 8.0, "end_time": 15.0, "text": "这是混剪字幕2"}
    ]
    
    # 初始化训练管理器
    train_manager = TrainManager()
    
    # 添加训练数据对
    result = train_manager.add_training_pair(
        original_subtitles,
        remix_subtitles,
        language="zh",
        metadata={"source": "测试", "style": "幽默"}
    )
    
    print(f"添加训练数据对结果: {result}")
    
    # 开始训练
    train_result = train_manager.train_model(pair_id=result.get("pair_id"))
    print(f"训练结果: {train_result}")
    
    # 获取训练历史
    history = train_manager.get_training_history()
    print(f"训练历史: {history}")
    
    # 获取统计信息
    stats = train_manager.get_training_stats()
    print(f"统计信息: {stats}") 