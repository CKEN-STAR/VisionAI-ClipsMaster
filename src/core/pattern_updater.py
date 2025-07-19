"""
模式实时更新器

实时处理新命中的模式数据，挖掘新模式，并更新模式数据库
支持流式处理和版本管理
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import uuid

from loguru import logger

from src.algorithms.pattern_mining import PatternMiner
from src.data.hit_pattern_lake import HitPatternLake
from src.version_management.pattern_version_manager import PatternVersionManager
from src.evaluation.pattern_evaluator import PatternEvaluator


class PatternUpdater:
    """模式实时更新器，处理流式数据并更新模式库"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化模式更新器
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认配置
        """
        self.pattern_miner = PatternMiner()
        self.pattern_lake = HitPatternLake()
        self.version_manager = PatternVersionManager()
        self.pattern_evaluator = PatternEvaluator(config_path)
        
        # 记录状态
        self.last_update_time = None
        self.update_count = 0
        self.pending_patterns = []
        
        # 配置
        self._load_config(config_path)
        
        logger.info("模式实时更新器初始化完成")
    
    def _load_config(self, config_path: Optional[str] = None) -> None:
        """
        加载配置
        
        Args:
            config_path: 配置文件路径，如果为None，使用默认配置
        """
        # 默认配置
        self.config = {
            "batch_size": 50,                # 批处理大小
            "update_threshold": 0.6,         # 模式更新阈值
            "min_patterns_for_version": 10,  # 创建新版本所需的最小模式数量
            "auto_version": True,            # 是否自动创建新版本
            "version_interval": 24 * 60 * 60,  # 版本更新间隔（秒）
            "pattern_types": [               # 支持的模式类型
                "opening", "climax", "transition", 
                "conflict", "resolution", "ending"
            ],
        }
        
        # 加载外部配置（如果有）
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    import yaml
                    external_config = yaml.safe_load(f)
                    self.config.update(external_config)
                logger.info(f"从 {config_path} 加载配置成功")
            except Exception as e:
                logger.warning(f"加载配置失败: {e}，使用默认配置")
    
    def streaming_update(self, new_hit_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理流式输入的命中数据，更新模式库
        
        Args:
            new_hit_data: 新的命中数据列表，每项包含原始字幕和命中字幕数据
            
        Returns:
            Dict: 包含更新结果的字典
        """
        start_time = time.time()
        
        # 1. 记录更新状态
        self.update_count += 1
        self.last_update_time = datetime.now().isoformat()
        
        # 2. 处理命中数据
        for hit_item in new_hit_data:
            try:
                # 将命中数据导入数据湖
                origin_srt = hit_item.get("origin_srt", "")
                hit_srt = hit_item.get("hit_srt", "")
                
                if origin_srt and hit_srt:
                    self.pattern_lake.ingest_data(origin_srt, hit_srt)
                    logger.debug(f"命中数据导入成功，原始长度: {len(origin_srt)}, 命中长度: {len(hit_srt)}")
            except Exception as e:
                logger.error(f"处理命中数据失败: {e}")
        
        # 3. 挖掘新模式
        try:
            # 从数据湖中查询最新数据创建scripts参数
            recent_patterns = self.pattern_lake.query_patterns(limit=self.config["batch_size"])
            scripts = recent_patterns.to_dict('records') if not recent_patterns.empty else []
            
            # 挖掘模式
            mined_patterns = self.pattern_miner.extract_patterns(scripts)
            
            # 过滤模式类型
            filtered_patterns = self.pattern_miner.filter_patterns(
                mined_patterns, 
                pattern_types=self.config["pattern_types"]
            )
            
            logger.info(f"挖掘出 {len(filtered_patterns)} 个新模式")
            
            # 将新挖掘的模式添加到待处理列表
            self.pending_patterns.extend(filtered_patterns)
        except Exception as e:
            logger.error(f"挖掘模式失败: {e}")
            
        # 4. 评估模式重要性
        significant_patterns = []
        if self.pending_patterns:
            try:
                # 评估所有待处理模式
                evaluated_patterns = self.pattern_evaluator.evaluate_multiple_patterns(self.pending_patterns)
                
                # 筛选出重要的模式
                significant_patterns = [
                    p for p in evaluated_patterns 
                    if p["impact_score"] >= self.config["update_threshold"]
                ]
                
                # 更新待处理列表，移除已处理的模式
                self.pending_patterns = []
                
                logger.info(f"筛选出 {len(significant_patterns)} 个重要模式")
            except Exception as e:
                logger.error(f"评估模式失败: {e}")
        
        # 5. 合并模式到数据库
        merged_count = 0
        if significant_patterns:
            try:
                # 获取当前模式配置
                current_config = self.version_manager.get_pattern_config()
                
                # 将重要模式添加到顶级模式列表
                top_patterns = current_config.get("top_patterns", [])
                
                # 按影响力排序
                significant_patterns.sort(key=lambda x: x["impact_score"], reverse=True)
                
                # 合并模式（简单追加，实际应用中可能需要更复杂的合并逻辑）
                for pattern in significant_patterns:
                    # 检查模式是否已存在
                    if not any(p.get("pattern_id") == pattern["pattern_id"] for p in top_patterns):
                        top_patterns.append({
                            "pattern_id": pattern["pattern_id"],
                            "pattern_type": pattern["pattern_type"],
                            "impact_score": pattern["impact_score"],
                            "updated_at": datetime.now().isoformat()
                        })
                        merged_count += 1
                
                # 更新配置
                current_config["top_patterns"] = top_patterns
                self.version_manager.update_pattern_config(current_config)
                
                logger.info(f"合并了 {merged_count} 个新模式到数据库")
            except Exception as e:
                logger.error(f"合并模式失败: {e}")
        
        # 6. 创建新版本（如果需要）
        version_created = False
        if self.config["auto_version"] and merged_count >= self.config["min_patterns_for_version"]:
            try:
                # 获取当前版本
                current_version = self.version_manager.get_latest_version()
                
                # 解析版本号
                import re
                version_match = re.match(r"v(\d+)\.(\d+)", current_version)
                if version_match:
                    major, minor = map(int, version_match.groups())
                    new_version = f"v{major}.{minor + 1}"
                else:
                    new_version = "v1.0"
                
                # 创建新版本
                description = f"自动更新版本，包含 {merged_count} 个新模式"
                self.version_manager.create_new_version(
                    new_version,
                    description=description,
                    author="PatternUpdater",
                    base_version=current_version
                )
                
                # 设置为当前版本
                self.version_manager.set_current_version(new_version)
                
                version_created = True
                logger.info(f"创建了新版本: {new_version}")
            except Exception as e:
                logger.error(f"创建新版本失败: {e}")
        
        # 7. 准备返回结果
        elapsed_time = time.time() - start_time
        result = {
            "update_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "processed_items": len(new_hit_data),
                "mined_patterns": len(filtered_patterns) if 'filtered_patterns' in locals() else 0,
                "significant_patterns": len(significant_patterns),
                "merged_patterns": merged_count,
                "version_created": version_created,
                "processing_time": elapsed_time
            }
        }
        
        return result 