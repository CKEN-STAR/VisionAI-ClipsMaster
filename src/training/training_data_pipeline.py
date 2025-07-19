#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
训练数据管道
构建爆款视频字幕的训练数据收集、清洗和标注流程
"""

import os
import json
import time
import logging
import hashlib
import requests
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 尝试导入数据处理库
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logger = logging.getLogger(__name__)

class TrainingDataPipeline:
    """训练数据管道"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化训练数据管道
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.db_path = self.config.get("database_path", "data/training/training_data.db")
        self.data_dir = Path(self.config.get("data_dir", "data/training"))
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
        # 数据质量评估器
        self.quality_assessor = DataQualityAssessor()
        
        # 线程锁
        self._lock = threading.Lock()
        
        logger.info("训练数据管道初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "database_path": "data/training/training_data.db",
            "data_dir": "data/training",
            "collection": {
                "max_workers": 4,
                "timeout": 30,
                "retry_attempts": 3
            },
            "quality": {
                "min_subtitle_length": 10,
                "max_subtitle_length": 1000,
                "min_segments": 5,
                "max_segments": 200,
                "similarity_threshold": 0.8
            },
            "annotation": {
                "viral_indicators": [
                    "悬疑", "反转", "震惊", "想不到", "太甜了", "心疼", "气死了",
                    "笑不活了", "泪目", "绝了", "太好哭了", "上头", "破防了"
                ],
                "emotion_categories": [
                    "惊讶", "愤怒", "悲伤", "快乐", "恐惧", "厌恶", "期待"
                ]
            },
            "export": {
                "formats": ["json", "csv", "txt"],
                "batch_size": 1000
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return default_config
    
    def _init_database(self):
        """初始化数据库"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建原始数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS raw_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_type TEXT NOT NULL,
                        source_url TEXT,
                        title TEXT,
                        original_subtitles TEXT NOT NULL,
                        viral_subtitles TEXT,
                        language TEXT NOT NULL,
                        duration REAL,
                        view_count INTEGER,
                        like_count INTEGER,
                        comment_count INTEGER,
                        collection_date TEXT NOT NULL,
                        data_hash TEXT UNIQUE NOT NULL,
                        status TEXT DEFAULT 'raw'
                    )
                ''')
                
                # 创建清洗后数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cleaned_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        raw_data_id INTEGER NOT NULL,
                        original_subtitles TEXT NOT NULL,
                        viral_subtitles TEXT NOT NULL,
                        language TEXT NOT NULL,
                        quality_score REAL NOT NULL,
                        viral_score REAL NOT NULL,
                        emotion_labels TEXT,
                        narrative_structure TEXT,
                        processing_date TEXT NOT NULL,
                        FOREIGN KEY (raw_data_id) REFERENCES raw_data (id)
                    )
                ''')
                
                # 创建标注数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS annotated_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cleaned_data_id INTEGER NOT NULL,
                        annotation_type TEXT NOT NULL,
                        annotation_data TEXT NOT NULL,
                        annotator TEXT,
                        annotation_date TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        FOREIGN KEY (cleaned_data_id) REFERENCES cleaned_data (id)
                    )
                ''')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    def collect_training_data(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        收集训练数据
        
        Args:
            data_sources: 数据源列表
            
        Returns:
            Dict[str, Any]: 收集结果
        """
        try:
            logger.info(f"开始收集训练数据，数据源数量: {len(data_sources)}")
            start_time = time.time()
            
            collected_count = 0
            failed_count = 0
            duplicate_count = 0
            
            max_workers = self.config["collection"]["max_workers"]
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有收集任务
                future_to_source = {
                    executor.submit(self._collect_single_source, source): source
                    for source in data_sources
                }
                
                # 处理完成的任务
                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        result = future.result()
                        if result["success"]:
                            if result["is_duplicate"]:
                                duplicate_count += 1
                            else:
                                collected_count += 1
                        else:
                            failed_count += 1
                            logger.warning(f"收集失败: {source.get('url', 'unknown')}, {result.get('error')}")
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"处理数据源失败: {source.get('url', 'unknown')}, {str(e)}")
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "collected_count": collected_count,
                "failed_count": failed_count,
                "duplicate_count": duplicate_count,
                "total_sources": len(data_sources),
                "processing_time": processing_time
            }
            
            logger.info(f"数据收集完成: 成功 {collected_count}, 失败 {failed_count}, 重复 {duplicate_count}")
            return result
            
        except Exception as e:
            logger.error(f"收集训练数据失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _collect_single_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """收集单个数据源"""
        try:
            # 提取数据
            data = self._extract_data_from_source(source)
            if not data:
                return {"success": False, "error": "无法提取数据"}
            
            # 计算数据哈希
            data_hash = self._calculate_data_hash(data)
            
            # 检查是否重复
            if self._is_duplicate(data_hash):
                return {"success": True, "is_duplicate": True}
            
            # 保存到数据库
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO raw_data (
                        source_type, source_url, title, original_subtitles, viral_subtitles,
                        language, duration, view_count, like_count, comment_count,
                        collection_date, data_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get("source_type", "unknown"),
                    data.get("source_url", ""),
                    data.get("title", ""),
                    data.get("original_subtitles", ""),
                    data.get("viral_subtitles", ""),
                    data.get("language", "zh"),
                    data.get("duration", 0.0),
                    data.get("view_count", 0),
                    data.get("like_count", 0),
                    data.get("comment_count", 0),
                    datetime.now().isoformat(),
                    data_hash
                ))
                conn.commit()
            
            return {"success": True, "is_duplicate": False}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_data_from_source(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从数据源提取数据"""
        try:
            source_type = source.get("type", "file")
            
            if source_type == "file":
                return self._extract_from_file(source)
            elif source_type == "url":
                return self._extract_from_url(source)
            elif source_type == "api":
                return self._extract_from_api(source)
            else:
                logger.warning(f"不支持的数据源类型: {source_type}")
                return None
                
        except Exception as e:
            logger.error(f"提取数据失败: {str(e)}")
            return None
    
    def _extract_from_file(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从文件提取数据"""
        try:
            file_path = source.get("path")
            if not file_path or not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 根据文件格式解析
            if file_path.endswith('.json'):
                data = json.loads(content)
            elif file_path.endswith('.srt'):
                data = {
                    "original_subtitles": content,
                    "viral_subtitles": "",
                    "language": source.get("language", "zh")
                }
            else:
                data = {
                    "original_subtitles": content,
                    "viral_subtitles": "",
                    "language": source.get("language", "zh")
                }
            
            # 添加元数据
            data.update({
                "source_type": "file",
                "source_url": file_path,
                "title": os.path.basename(file_path)
            })
            
            return data
            
        except Exception as e:
            logger.error(f"从文件提取数据失败: {str(e)}")
            return None
    
    def _extract_from_url(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从URL提取数据"""
        try:
            url = source.get("url")
            if not url:
                return None
            
            timeout = self.config["collection"]["timeout"]
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # 根据内容类型解析
            content_type = response.headers.get('content-type', '')
            
            if 'application/json' in content_type:
                data = response.json()
            else:
                data = {
                    "original_subtitles": response.text,
                    "viral_subtitles": "",
                    "language": source.get("language", "zh")
                }
            
            # 添加元数据
            data.update({
                "source_type": "url",
                "source_url": url,
                "title": source.get("title", url)
            })
            
            return data
            
        except Exception as e:
            logger.error(f"从URL提取数据失败: {str(e)}")
            return None
    
    def _extract_from_api(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从API提取数据"""
        try:
            # 这里可以实现各种API的数据提取逻辑
            # 例如：YouTube API, TikTok API等
            
            api_type = source.get("api_type")
            if api_type == "youtube":
                return self._extract_from_youtube_api(source)
            elif api_type == "tiktok":
                return self._extract_from_tiktok_api(source)
            else:
                logger.warning(f"不支持的API类型: {api_type}")
                return None
                
        except Exception as e:
            logger.error(f"从API提取数据失败: {str(e)}")
            return None
    
    def _extract_from_youtube_api(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从YouTube API提取数据（示例实现）"""
        # 这里需要实现YouTube API的具体调用逻辑
        # 由于需要API密钥，这里只提供框架
        logger.info("YouTube API提取功能需要配置API密钥")
        return None
    
    def _extract_from_tiktok_api(self, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从TikTok API提取数据（示例实现）"""
        # 这里需要实现TikTok API的具体调用逻辑
        logger.info("TikTok API提取功能需要配置API密钥")
        return None
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """计算数据哈希值"""
        try:
            # 使用关键字段计算哈希
            key_fields = [
                data.get("original_subtitles", ""),
                data.get("viral_subtitles", ""),
                data.get("title", "")
            ]
            
            content = "|".join(key_fields)
            return hashlib.md5(content.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"计算数据哈希失败: {str(e)}")
            return ""
    
    def _is_duplicate(self, data_hash: str) -> bool:
        """检查是否重复数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM raw_data WHERE data_hash = ?', (data_hash,))
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"检查重复数据失败: {str(e)}")
            return False

    def clean_training_data(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        清洗训练数据

        Args:
            batch_size: 批处理大小

        Returns:
            Dict[str, Any]: 清洗结果
        """
        try:
            logger.info("开始清洗训练数据")
            start_time = time.time()

            # 获取待清洗的原始数据
            raw_data = self._get_raw_data_for_cleaning(batch_size)
            if not raw_data:
                return {"success": True, "message": "没有待清洗的数据"}

            cleaned_count = 0
            failed_count = 0

            for data_item in raw_data:
                try:
                    # 清洗单条数据
                    cleaned_result = self._clean_single_data_item(data_item)

                    if cleaned_result["success"]:
                        # 保存清洗后的数据
                        self._save_cleaned_data(data_item["id"], cleaned_result["data"])
                        cleaned_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"清洗数据失败: ID {data_item['id']}, {cleaned_result.get('error')}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"处理数据项失败: ID {data_item.get('id')}, {str(e)}")

            processing_time = time.time() - start_time

            result = {
                "success": True,
                "cleaned_count": cleaned_count,
                "failed_count": failed_count,
                "total_processed": len(raw_data),
                "processing_time": processing_time
            }

            logger.info(f"数据清洗完成: 成功 {cleaned_count}, 失败 {failed_count}")
            return result

        except Exception as e:
            logger.error(f"清洗训练数据失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_raw_data_for_cleaning(self, batch_size: int) -> List[Dict[str, Any]]:
        """获取待清洗的原始数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, original_subtitles, viral_subtitles, language, title
                    FROM raw_data
                    WHERE status = 'raw'
                    LIMIT ?
                ''', (batch_size,))

                rows = cursor.fetchall()

                data_items = []
                for row in rows:
                    data_items.append({
                        "id": row[0],
                        "original_subtitles": row[1],
                        "viral_subtitles": row[2],
                        "language": row[3],
                        "title": row[4]
                    })

                return data_items

        except Exception as e:
            logger.error(f"获取待清洗数据失败: {str(e)}")
            return []

    def _clean_single_data_item(self, data_item: Dict[str, Any]) -> Dict[str, Any]:
        """清洗单条数据"""
        try:
            original_subtitles = data_item.get("original_subtitles", "")
            viral_subtitles = data_item.get("viral_subtitles", "")
            language = data_item.get("language", "zh")

            # 基本验证
            if not original_subtitles.strip():
                return {"success": False, "error": "原始字幕为空"}

            # 清洗原始字幕
            cleaned_original = self._clean_subtitle_text(original_subtitles)
            cleaned_viral = self._clean_subtitle_text(viral_subtitles) if viral_subtitles else ""

            # 质量评估
            quality_score = self.quality_assessor.assess_quality(cleaned_original, cleaned_viral, language)

            # 病毒式评分
            viral_score = self.quality_assessor.assess_viral_potential(cleaned_viral, language)

            # 情感标注
            emotion_labels = self.quality_assessor.extract_emotions(cleaned_viral, language)

            # 叙事结构分析
            narrative_structure = self.quality_assessor.analyze_narrative_structure(cleaned_original, cleaned_viral)

            # 质量阈值检查
            min_quality = self.config["quality"]["min_subtitle_length"]
            if len(cleaned_original) < min_quality:
                return {"success": False, "error": f"字幕长度不足: {len(cleaned_original)}"}

            cleaned_data = {
                "original_subtitles": cleaned_original,
                "viral_subtitles": cleaned_viral,
                "language": language,
                "quality_score": quality_score,
                "viral_score": viral_score,
                "emotion_labels": json.dumps(emotion_labels, ensure_ascii=False),
                "narrative_structure": json.dumps(narrative_structure, ensure_ascii=False)
            }

            return {"success": True, "data": cleaned_data}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _clean_subtitle_text(self, text: str) -> str:
        """清洗字幕文本"""
        try:
            if not text:
                return ""

            # 移除多余的空白字符
            text = ' '.join(text.split())

            # 移除特殊字符（保留中英文、数字、基本标点）
            import re
            text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()""''""【】（）。，！？；：]', '', text)

            # 移除过长的重复字符
            text = re.sub(r'(.)\1{3,}', r'\1\1', text)

            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)

            # 移除时间戳格式
            text = re.sub(r'\d{2}:\d{2}:\d{2}[,\.]\d{3}', '', text)
            text = re.sub(r'\d+\s*-->\s*\d+', '', text)

            return text.strip()

        except Exception as e:
            logger.error(f"清洗字幕文本失败: {str(e)}")
            return text

    def _save_cleaned_data(self, raw_data_id: int, cleaned_data: Dict[str, Any]):
        """保存清洗后的数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 插入清洗后的数据
                cursor.execute('''
                    INSERT INTO cleaned_data (
                        raw_data_id, original_subtitles, viral_subtitles, language,
                        quality_score, viral_score, emotion_labels, narrative_structure,
                        processing_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    raw_data_id,
                    cleaned_data["original_subtitles"],
                    cleaned_data["viral_subtitles"],
                    cleaned_data["language"],
                    cleaned_data["quality_score"],
                    cleaned_data["viral_score"],
                    cleaned_data["emotion_labels"],
                    cleaned_data["narrative_structure"],
                    datetime.now().isoformat()
                ))

                # 更新原始数据状态
                cursor.execute(
                    'UPDATE raw_data SET status = ? WHERE id = ?',
                    ('cleaned', raw_data_id)
                )

                conn.commit()

        except Exception as e:
            logger.error(f"保存清洗数据失败: {str(e)}")
            raise


class DataQualityAssessor:
    """数据质量评估器"""

    def __init__(self):
        """初始化质量评估器"""
        self.viral_keywords = {
            "zh": [
                "震惊", "想不到", "太甜了", "心疼", "气死了", "笑不活了", "泪目",
                "绝了", "太好哭了", "上头", "破防了", "悬疑", "反转", "揭秘"
            ],
            "en": [
                "shocking", "unbelievable", "amazing", "incredible", "stunning",
                "heartbreaking", "hilarious", "emotional", "plot twist", "reveal"
            ]
        }

        self.emotion_patterns = {
            "zh": {
                "惊讶": ["震惊", "想不到", "没想到", "居然", "竟然"],
                "愤怒": ["气死", "生气", "愤怒", "讨厌", "恶心"],
                "悲伤": ["心疼", "难过", "伤心", "哭了", "泪目"],
                "快乐": ["开心", "高兴", "快乐", "笑", "哈哈"],
                "恐惧": ["害怕", "恐怖", "可怕", "吓人", "惊悚"],
                "期待": ["期待", "想看", "好奇", "等不及", "迫不及待"]
            },
            "en": {
                "surprise": ["shocking", "unbelievable", "amazing", "incredible"],
                "anger": ["angry", "mad", "furious", "annoying", "hate"],
                "sadness": ["sad", "heartbreaking", "crying", "tears", "emotional"],
                "happiness": ["happy", "funny", "hilarious", "laugh", "joy"],
                "fear": ["scary", "terrifying", "frightening", "horror", "afraid"],
                "anticipation": ["excited", "can't wait", "curious", "eager", "anticipate"]
            }
        }

    def assess_quality(self, original: str, viral: str, language: str) -> float:
        """评估数据质量"""
        try:
            score = 0.0

            # 长度评分 (0-0.3)
            if 10 <= len(original) <= 1000:
                score += 0.3
            elif len(original) > 1000:
                score += 0.2
            else:
                score += 0.1

            # 内容丰富度评分 (0-0.3)
            if viral:
                # 检查是否有实质性改写
                if len(viral) > len(original) * 0.5:
                    score += 0.3
                else:
                    score += 0.2
            else:
                score += 0.1

            # 语言质量评分 (0-0.4)
            language_score = self._assess_language_quality(original, language)
            score += language_score * 0.4

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"质量评估失败: {str(e)}")
            return 0.5

    def assess_viral_potential(self, viral_text: str, language: str) -> float:
        """评估病毒式传播潜力"""
        try:
            if not viral_text:
                return 0.0

            score = 0.0
            keywords = self.viral_keywords.get(language, [])

            # 关键词匹配评分
            keyword_count = sum(1 for keyword in keywords if keyword in viral_text)
            keyword_score = min(keyword_count / len(keywords), 1.0)
            score += keyword_score * 0.5

            # 情感强度评分
            emotion_score = self._assess_emotion_intensity(viral_text, language)
            score += emotion_score * 0.3

            # 互动元素评分
            interaction_score = self._assess_interaction_elements(viral_text, language)
            score += interaction_score * 0.2

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"病毒式潜力评估失败: {str(e)}")
            return 0.0

    def extract_emotions(self, text: str, language: str) -> List[str]:
        """提取情感标签"""
        try:
            emotions = []
            patterns = self.emotion_patterns.get(language, {})

            for emotion, keywords in patterns.items():
                if any(keyword in text for keyword in keywords):
                    emotions.append(emotion)

            return emotions

        except Exception as e:
            logger.error(f"情感提取失败: {str(e)}")
            return []

    def analyze_narrative_structure(self, original: str, viral: str) -> Dict[str, Any]:
        """分析叙事结构"""
        try:
            structure = {
                "has_hook": False,
                "has_conflict": False,
                "has_resolution": False,
                "transformation_type": "none"
            }

            if not viral:
                return structure

            # 检查开头钩子
            hook_patterns = ["你绝对想不到", "震惊", "万万没想到", "看到这里", "注意"]
            structure["has_hook"] = any(pattern in viral[:50] for pattern in hook_patterns)

            # 检查冲突元素
            conflict_patterns = ["但是", "然而", "突然", "没想到", "竟然"]
            structure["has_conflict"] = any(pattern in viral for pattern in conflict_patterns)

            # 检查结局
            resolution_patterns = ["最后", "结果", "原来", "真相", "答案"]
            structure["has_resolution"] = any(pattern in viral[-100:] for pattern in resolution_patterns)

            # 判断转换类型
            if len(viral) > len(original) * 1.5:
                structure["transformation_type"] = "expansion"
            elif len(viral) < len(original) * 0.7:
                structure["transformation_type"] = "compression"
            else:
                structure["transformation_type"] = "rewrite"

            return structure

        except Exception as e:
            logger.error(f"叙事结构分析失败: {str(e)}")
            return {"transformation_type": "unknown"}

    def _assess_language_quality(self, text: str, language: str) -> float:
        """评估语言质量"""
        try:
            # 简单的语言质量评估
            score = 0.5

            # 检查重复字符
            import re
            repeated_chars = len(re.findall(r'(.)\1{2,}', text))
            if repeated_chars == 0:
                score += 0.2

            # 检查标点符号使用
            punctuation_count = len(re.findall(r'[.,!?;:]', text))
            if punctuation_count > 0:
                score += 0.2

            # 检查长度合理性
            if 50 <= len(text) <= 500:
                score += 0.1

            return min(score, 1.0)

        except Exception as e:
            logger.error(f"语言质量评估失败: {str(e)}")
            return 0.5

    def _assess_emotion_intensity(self, text: str, language: str) -> float:
        """评估情感强度"""
        try:
            # 检查感叹号和问号
            import re
            exclamation_count = len(re.findall(r'[!！]', text))
            question_count = len(re.findall(r'[?？]', text))

            intensity_score = min((exclamation_count + question_count) / 10, 1.0)
            return intensity_score

        except Exception as e:
            logger.error(f"情感强度评估失败: {str(e)}")
            return 0.0

    def _assess_interaction_elements(self, text: str, language: str) -> float:
        """评估互动元素"""
        try:
            interaction_patterns = {
                "zh": ["你们觉得", "大家认为", "评论区", "点赞", "关注"],
                "en": ["what do you think", "comment below", "like and subscribe", "your thoughts"]
            }

            patterns = interaction_patterns.get(language, [])
            interaction_count = sum(1 for pattern in patterns if pattern in text)

            return min(interaction_count / len(patterns), 1.0)

        except Exception as e:
            logger.error(f"互动元素评估失败: {str(e)}")
            return 0.0
