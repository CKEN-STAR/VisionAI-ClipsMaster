#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练投喂器模块

处理和管理训练数据，支持原片字幕-爆款字幕对的收集和投喂
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

# 获取日志记录器
logger = logging.getLogger(__name__)

# 尝试导入相关依赖
try:
    from src.core.srt_parser import parse_srt
    CORE_AVAILABLE = True
except ImportError:
    logger.warning("无法导入SRT解析模块，部分功能可能不可用")
    CORE_AVAILABLE = False

class TrainingFeeder:
    """训练投喂器，用于管理训练数据"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """初始化训练投喂器
        
        Args:
            data_dir: 训练数据目录，默认为None使用临时目录
        """
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'training')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 训练数据对
        self.training_pairs = []
        # 当前语言
        self.current_language = None
        
        logger.info(f"训练投喂器初始化，数据目录: {self.data_dir}")
    
    def add_training_pair(self, original_files: List[str], viral_file: str) -> bool:
        """添加训练数据对
        
        Args:
            original_files: 原片字幕文件列表
            viral_file: 爆款字幕文件
            
        Returns:
            bool: 是否添加成功
        """
        try:
            if not CORE_AVAILABLE:
                logger.error("SRT解析模块不可用，无法添加训练数据")
                return False
                
            # 检查文件是否存在
            for file_path in original_files + [viral_file]:
                if not os.path.exists(file_path):
                    logger.error(f"文件不存在: {file_path}")
                    return False
            
            # 解析原片字幕
            original_subtitles = []
            for file_path in original_files:
                subtitles = parse_srt(file_path)
                if subtitles:
                    # 记录来源文件
                    for subtitle in subtitles:
                        subtitle["source_file"] = os.path.basename(file_path)
                    original_subtitles.extend(subtitles)
                    logger.info(f"已加载原片字幕: {file_path}, {len(subtitles)}条")
                else:
                    logger.warning(f"字幕文件为空: {file_path}")
            
            # 解析爆款字幕
            viral_subtitles = parse_srt(viral_file)
            if not viral_subtitles:
                logger.error(f"爆款字幕为空: {viral_file}")
                return False
                
            logger.info(f"已加载爆款字幕: {viral_file}, {len(viral_subtitles)}条")
            
            # 添加到训练数据对
            pair_id = len(self.training_pairs) + 1
            training_pair = {
                "id": pair_id,
                "original": {
                    "files": original_files,
                    "subtitles": original_subtitles
                },
                "viral": {
                    "file": viral_file,
                    "subtitles": viral_subtitles
                }
            }
            
            self.training_pairs.append(training_pair)
            logger.info(f"已添加训练数据对 #{pair_id}: {len(original_files)}个原片字幕文件 -> 1个爆款字幕文件")
            
            # 保存到文件
            self._save_training_pair(pair_id, training_pair)
            
            return True
            
        except Exception as e:
            logger.error(f"添加训练数据对失败: {str(e)}")
            return False
    
    def get_training_data(self) -> List[Dict[str, Any]]:
        """获取所有训练数据对
        
        Returns:
            List[Dict[str, Any]]: 训练数据对列表
        """
        return self.training_pairs
    
    def prepare_training(self) -> Dict[str, Any]:
        """准备训练数据，返回训练结果
        
        Returns:
            Dict[str, Any]: 训练准备结果
        """
        if not self.training_pairs:
            logger.error("没有训练数据，无法开始训练")
            return {"status": "error", "message": "没有训练数据"}
            
        # 统计数据
        total_original = sum(len(pair["original"]["subtitles"]) for pair in self.training_pairs)
        total_viral = sum(len(pair["viral"]["subtitles"]) for pair in self.training_pairs)
        
        # 检查语言
        self._detect_language()
        
        # 返回准备结果
        return {
            "status": "ready",
            "pairs_count": len(self.training_pairs),
            "original_subtitles": total_original,
            "viral_subtitles": total_viral,
            "language": self.current_language
        }
    
    def _detect_language(self) -> str:
        """检测训练数据的语言
        
        Returns:
            str: 语言代码 (zh/en)
        """
        if not self.training_pairs:
            return "unknown"
            
        try:
            # 尝试导入语言检测模块
            from src.core.language_detector import detect_language
            
            # 使用第一个训练数据对检测
            first_pair = self.training_pairs[0]
            
            # 原片字幕文件
            original_file = first_pair["original"]["files"][0]
            language = detect_language(original_file)
            
            self.current_language = language
            logger.info(f"检测到训练数据语言: {language}")
            
            return language
        except ImportError:
            logger.warning("语言检测模块不可用，使用默认语言 zh")
            self.current_language = "zh"
            return "zh"
    
    def _save_training_pair(self, pair_id: int, pair_data: Dict[str, Any]) -> bool:
        """保存训练数据对到文件
        
        Args:
            pair_id: 数据对ID
            pair_data: 数据对内容
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 创建保存目录
            save_dir = os.path.join(self.data_dir, f"pair_{pair_id}")
            os.makedirs(save_dir, exist_ok=True)
            
            # 保存元数据
            metadata = {
                "id": pair_id,
                "original_files": [os.path.basename(f) for f in pair_data["original"]["files"]],
                "viral_file": os.path.basename(pair_data["viral"]["file"]),
                "original_count": len(pair_data["original"]["subtitles"]),
                "viral_count": len(pair_data["viral"]["subtitles"])
            }
            
            with open(os.path.join(save_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"已保存训练数据对 #{pair_id} 到 {save_dir}")
            return True
            
        except Exception as e:
            logger.error(f"保存训练数据对失败: {str(e)}")
            return False
    
    def load_training_pairs(self) -> int:
        """从数据目录加载所有训练数据对
        
        Returns:
            int: 加载的数据对数量
        """
        try:
            self.training_pairs = []
            
            # 遍历目录查找训练数据对
            for item in os.listdir(self.data_dir):
                if item.startswith("pair_"):
                    pair_dir = os.path.join(self.data_dir, item)
                    if os.path.isdir(pair_dir):
                        # 读取元数据
                        metadata_path = os.path.join(pair_dir, "metadata.json")
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, "r", encoding="utf-8") as f:
                                    metadata = json.load(f)
                                
                                # 创建数据对
                                pair_id = metadata.get("id")
                                if pair_id:
                                    training_pair = {
                                        "id": pair_id,
                                        "original": {
                                            "files": metadata.get("original_files", []),
                                            "subtitles": []  # 暂不加载字幕内容
                                        },
                                        "viral": {
                                            "file": metadata.get("viral_file", ""),
                                            "subtitles": []  # 暂不加载字幕内容
                                        }
                                    }
                                    self.training_pairs.append(training_pair)
                                    logger.info(f"已加载训练数据对 #{pair_id} 元数据")
                            except Exception as e:
                                logger.error(f"加载训练数据对元数据失败: {str(e)}")
            
            # 按ID排序
            self.training_pairs.sort(key=lambda x: x["id"])
            
            logger.info(f"共加载了 {len(self.training_pairs)} 个训练数据对")
            return len(self.training_pairs)
            
        except Exception as e:
            logger.error(f"加载训练数据对失败: {str(e)}")
            return 0 