#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练数据导出管理器
提供多种格式的训练数据导出功能
"""

import os
import json
import csv
import time
import logging
import sqlite3
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class DataExportManager:
    """训练数据导出管理器"""
    
    def __init__(self, db_path: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化导出管理器
        
        Args:
            db_path: 数据库路径
            config: 配置信息
        """
        self.db_path = db_path
        self.config = config or {}
        self.export_dir = Path(self.config.get("export_dir", "data/exports"))
        
        # 确保导出目录存在
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("数据导出管理器初始化完成")
    
    def export_training_data(self, 
                           export_format: str = "json",
                           language: Optional[str] = None,
                           quality_threshold: float = 0.5,
                           viral_threshold: float = 0.3,
                           max_records: Optional[int] = None) -> Dict[str, Any]:
        """
        导出训练数据
        
        Args:
            export_format: 导出格式 (json, csv, txt, huggingface)
            language: 语言过滤 (zh, en, None表示全部)
            quality_threshold: 质量阈值
            viral_threshold: 病毒式传播阈值
            max_records: 最大记录数
            
        Returns:
            Dict[str, Any]: 导出结果
        """
        try:
            logger.info(f"开始导出训练数据，格式: {export_format}")
            start_time = time.time()
            
            # 获取数据
            data = self._get_filtered_data(language, quality_threshold, viral_threshold, max_records)
            if not data:
                return {"success": False, "error": "没有符合条件的数据"}
            
            # 根据格式导出
            if export_format == "json":
                result = self._export_json(data, language)
            elif export_format == "csv":
                result = self._export_csv(data, language)
            elif export_format == "txt":
                result = self._export_txt(data, language)
            elif export_format == "huggingface":
                result = self._export_huggingface(data, language)
            else:
                return {"success": False, "error": f"不支持的导出格式: {export_format}"}
            
            if result["success"]:
                processing_time = time.time() - start_time
                result.update({
                    "record_count": len(data),
                    "processing_time": processing_time,
                    "filters": {
                        "language": language,
                        "quality_threshold": quality_threshold,
                        "viral_threshold": viral_threshold,
                        "max_records": max_records
                    }
                })
                
                logger.info(f"数据导出完成: {len(data)} 条记录，耗时 {processing_time:.2f} 秒")
            
            return result
            
        except Exception as e:
            logger.error(f"导出训练数据失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_filtered_data(self, 
                          language: Optional[str],
                          quality_threshold: float,
                          viral_threshold: float,
                          max_records: Optional[int]) -> List[Dict[str, Any]]:
        """获取过滤后的数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                conditions = ["quality_score >= ?", "viral_score >= ?"]
                params = [quality_threshold, viral_threshold]
                
                if language:
                    conditions.append("language = ?")
                    params.append(language)
                
                where_clause = " AND ".join(conditions)
                
                # 构建查询语句
                query = f'''
                    SELECT 
                        original_subtitles, viral_subtitles, language,
                        quality_score, viral_score, emotion_labels,
                        narrative_structure, processing_date
                    FROM cleaned_data 
                    WHERE {where_clause}
                    ORDER BY viral_score DESC, quality_score DESC
                '''
                
                if max_records:
                    query += f" LIMIT {max_records}"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # 转换为字典列表
                data = []
                for row in rows:
                    data.append({
                        "original_subtitles": row[0],
                        "viral_subtitles": row[1],
                        "language": row[2],
                        "quality_score": row[3],
                        "viral_score": row[4],
                        "emotion_labels": json.loads(row[5]) if row[5] else [],
                        "narrative_structure": json.loads(row[6]) if row[6] else {},
                        "processing_date": row[7]
                    })
                
                return data
                
        except Exception as e:
            logger.error(f"获取过滤数据失败: {str(e)}")
            return []
    
    def _export_json(self, data: List[Dict[str, Any]], language: Optional[str]) -> Dict[str, Any]:
        """导出为JSON格式"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            language_suffix = f"_{language}" if language else "_all"
            filename = f"training_data{language_suffix}_{timestamp}.json"
            filepath = self.export_dir / filename
            
            # 准备导出数据
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "record_count": len(data),
                    "language": language,
                    "format": "json"
                },
                "data": data
            }
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "format": "json"
            }
            
        except Exception as e:
            logger.error(f"JSON导出失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _export_csv(self, data: List[Dict[str, Any]], language: Optional[str]) -> Dict[str, Any]:
        """导出为CSV格式"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            language_suffix = f"_{language}" if language else "_all"
            filename = f"training_data{language_suffix}_{timestamp}.csv"
            filepath = self.export_dir / filename
            
            # 准备CSV字段
            fieldnames = [
                "original_subtitles", "viral_subtitles", "language",
                "quality_score", "viral_score", "emotion_labels",
                "narrative_structure", "processing_date"
            ]
            
            # 写入CSV文件
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in data:
                    # 转换复杂字段为字符串
                    csv_item = item.copy()
                    csv_item["emotion_labels"] = json.dumps(item["emotion_labels"], ensure_ascii=False)
                    csv_item["narrative_structure"] = json.dumps(item["narrative_structure"], ensure_ascii=False)
                    writer.writerow(csv_item)
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "format": "csv"
            }
            
        except Exception as e:
            logger.error(f"CSV导出失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _export_txt(self, data: List[Dict[str, Any]], language: Optional[str]) -> Dict[str, Any]:
        """导出为TXT格式（适用于简单文本训练）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            language_suffix = f"_{language}" if language else "_all"
            filename = f"training_data{language_suffix}_{timestamp}.txt"
            filepath = self.export_dir / filename
            
            # 写入TXT文件
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, item in enumerate(data):
                    f.write(f"=== 样本 {i+1} ===\n")
                    f.write(f"原始字幕:\n{item['original_subtitles']}\n\n")
                    f.write(f"爆款字幕:\n{item['viral_subtitles']}\n\n")
                    f.write(f"语言: {item['language']}\n")
                    f.write(f"质量评分: {item['quality_score']:.3f}\n")
                    f.write(f"病毒式评分: {item['viral_score']:.3f}\n")
                    f.write("-" * 50 + "\n\n")
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "format": "txt"
            }
            
        except Exception as e:
            logger.error(f"TXT导出失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _export_huggingface(self, data: List[Dict[str, Any]], language: Optional[str]) -> Dict[str, Any]:
        """导出为HuggingFace数据集格式"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            language_suffix = f"_{language}" if language else "_all"
            filename = f"hf_dataset{language_suffix}_{timestamp}.json"
            filepath = self.export_dir / filename
            
            # 转换为HuggingFace格式
            hf_data = []
            for item in data:
                hf_item = {
                    "instruction": "将以下普通字幕改写为具有病毒式传播潜力的爆款字幕：",
                    "input": item["original_subtitles"],
                    "output": item["viral_subtitles"],
                    "language": item["language"],
                    "quality_score": item["quality_score"],
                    "viral_score": item["viral_score"]
                }
                hf_data.append(hf_item)
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in hf_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "format": "huggingface"
            }
            
        except Exception as e:
            logger.error(f"HuggingFace格式导出失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总体统计
                cursor.execute('SELECT COUNT(*) FROM raw_data')
                total_raw = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM cleaned_data')
                total_cleaned = cursor.fetchone()[0]
                
                # 语言分布
                cursor.execute('''
                    SELECT language, COUNT(*) 
                    FROM cleaned_data 
                    GROUP BY language
                ''')
                language_dist = dict(cursor.fetchall())
                
                # 质量分布
                cursor.execute('''
                    SELECT 
                        AVG(quality_score) as avg_quality,
                        MIN(quality_score) as min_quality,
                        MAX(quality_score) as max_quality,
                        AVG(viral_score) as avg_viral,
                        MIN(viral_score) as min_viral,
                        MAX(viral_score) as max_viral
                    FROM cleaned_data
                ''')
                quality_stats = cursor.fetchone()
                
                return {
                    "total_raw_data": total_raw,
                    "total_cleaned_data": total_cleaned,
                    "language_distribution": language_dist,
                    "quality_statistics": {
                        "avg_quality_score": quality_stats[0] or 0,
                        "min_quality_score": quality_stats[1] or 0,
                        "max_quality_score": quality_stats[2] or 0,
                        "avg_viral_score": quality_stats[3] or 0,
                        "min_viral_score": quality_stats[4] or 0,
                        "max_viral_score": quality_stats[5] or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"获取数据统计失败: {str(e)}")
            return {}
    
    def create_training_splits(self, 
                             train_ratio: float = 0.8,
                             val_ratio: float = 0.1,
                             test_ratio: float = 0.1,
                             language: Optional[str] = None) -> Dict[str, Any]:
        """创建训练/验证/测试数据集分割"""
        try:
            if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.001:
                return {"success": False, "error": "数据集比例之和必须等于1.0"}
            
            # 获取所有数据
            data = self._get_filtered_data(language, 0.0, 0.0, None)
            if not data:
                return {"success": False, "error": "没有可用数据"}
            
            # 随机打乱数据
            import random
            random.shuffle(data)
            
            # 计算分割点
            total_count = len(data)
            train_count = int(total_count * train_ratio)
            val_count = int(total_count * val_ratio)
            
            # 分割数据
            train_data = data[:train_count]
            val_data = data[train_count:train_count + val_count]
            test_data = data[train_count + val_count:]
            
            # 导出各个分割
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            language_suffix = f"_{language}" if language else "_all"
            
            results = {}
            
            # 导出训练集
            train_result = self._export_split_data(train_data, f"train{language_suffix}_{timestamp}")
            results["train"] = train_result
            
            # 导出验证集
            val_result = self._export_split_data(val_data, f"val{language_suffix}_{timestamp}")
            results["validation"] = val_result
            
            # 导出测试集
            test_result = self._export_split_data(test_data, f"test{language_suffix}_{timestamp}")
            results["test"] = test_result
            
            return {
                "success": True,
                "splits": results,
                "statistics": {
                    "total_count": total_count,
                    "train_count": len(train_data),
                    "val_count": len(val_data),
                    "test_count": len(test_data)
                }
            }
            
        except Exception as e:
            logger.error(f"创建数据集分割失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _export_split_data(self, data: List[Dict[str, Any]], filename_prefix: str) -> Dict[str, Any]:
        """导出分割数据"""
        try:
            filename = f"{filename_prefix}.json"
            filepath = self.export_dir / filename
            
            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "record_count": len(data),
                    "split_type": filename_prefix.split('_')[0]
                },
                "data": data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "record_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"导出分割数据失败: {str(e)}")
            return {"success": False, "error": str(e)}
