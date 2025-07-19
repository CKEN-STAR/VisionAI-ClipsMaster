"""量化校准集构建模块

此模块负责构建和管理量化校准数据集，包括：
1. 校准样本收集
2. 数据预处理
3. 特征提取
4. 校准集验证
5. 性能评估
"""

import os
import json
import random
from typing import Dict, List, Optional, Union, Tuple
from pathlib import Path
import numpy as np
from loguru import logger
from ..utils.text_processor import TextProcessor
from ..utils.file_handler import FileHandler

class CalibrationSetBuilder:
    """校准集构建器"""
    
    def __init__(self,
                 cache_dir: Optional[str] = None,
                 text_processor: Optional[TextProcessor] = None):
        """初始化校准集构建器
        
        Args:
            cache_dir: 缓存目录
            text_processor: 文本处理器实例
        """
        self.cache_dir = cache_dir or "data/calibration_cache"
        self.text_processor = text_processor or TextProcessor()
        self.file_handler = FileHandler()
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 校准参数
        self.calibration_params = {
            'min_samples': 500,          # 最小样本数
            'max_samples': 2000,         # 最大样本数
            'min_length': 10,            # 最小序列长度
            'max_length': 512,           # 最大序列长度
            'coverage_threshold': 0.8,    # 覆盖率阈值
            'diversity_threshold': 0.6,   # 多样性阈值
            'validation_split': 0.2      # 验证集比例
        }
        
        # 特征统计
        self.feature_stats = {
            'token_frequency': {},       # 词元频率
            'sequence_lengths': [],      # 序列长度
            'feature_coverage': {},      # 特征覆盖
            'domain_distribution': {}    # 领域分布
        }
    
    def build_calibration_set(self,
                            data_dir: str,
                            output_dir: str,
                            sample_size: Optional[int] = None) -> Tuple[List[str], Dict]:
        """构建校准数据集
        
        Args:
            data_dir: 原始数据目录
            output_dir: 输出目录
            sample_size: 采样大小
            
        Returns:
            Tuple[List[str], Dict]: (校准样本列表, 统计信息)
        """
        logger.info(f"开始构建校准集，数据目录: {data_dir}")
        
        try:
            # 收集原始样本
            raw_samples = self._collect_samples(data_dir)
            
            # 样本预处理
            processed_samples = self._preprocess_samples(raw_samples)
            
            # 特征提取和分析
            self._analyze_features(processed_samples)
            
            # 样本筛选
            selected_samples = self._select_samples(
                processed_samples,
                sample_size or self.calibration_params['min_samples']
            )
            
            # 验证校准集质量
            if not self._validate_calibration_set(selected_samples):
                logger.warning("校准集质量未达标，尝试重新采样")
                selected_samples = self._enhance_calibration_set(selected_samples)
            
            # 保存校准集
            self._save_calibration_set(selected_samples, output_dir)
            
            # 生成统计报告
            stats = self._generate_stats_report()
            
            logger.info(f"校准集构建完成，样本数: {len(selected_samples)}")
            return selected_samples, stats
            
        except Exception as e:
            logger.error(f"构建校准集失败: {str(e)}")
            raise
    
    def _collect_samples(self, data_dir: str) -> List[str]:
        """收集原始样本
        
        Args:
            data_dir: 数据目录
            
        Returns:
            List[str]: 原始样本列表
        """
        samples = []
        
        try:
            # 遍历所有支持的文件类型
            for ext in ['.txt', '.json', '.jsonl', '.csv']:
                for file_path in Path(data_dir).rglob(f"*{ext}"):
                    if ext == '.txt':
                        samples.extend(self._process_text_file(file_path))
                    elif ext in ['.json', '.jsonl']:
                        samples.extend(self._process_json_file(file_path))
                    elif ext == '.csv':
                        samples.extend(self._process_csv_file(file_path))
            
            logger.info(f"收集到原始样本: {len(samples)}条")
            return samples
            
        except Exception as e:
            logger.error(f"样本收集失败: {str(e)}")
            return []
    
    def _preprocess_samples(self, samples: List[str]) -> List[str]:
        """样本预处理
        
        Args:
            samples: 原始样本列表
            
        Returns:
            List[str]: 处理后的样本列表
        """
        processed = []
        
        for sample in samples:
            try:
                # 文本清理
                cleaned = self.text_processor.clean_text(sample)
                
                # 长度过滤
                if self.calibration_params['min_length'] <= len(cleaned) <= self.calibration_params['max_length']:
                    # 特征提取
                    features = self.text_processor.extract_features(cleaned)
                    
                    # 更新特征统计
                    self._update_feature_stats(features)
                    
                    processed.append(cleaned)
                    
            except Exception as e:
                logger.debug(f"样本处理失败: {str(e)}")
                continue
        
        return processed
    
    def _analyze_features(self, samples: List[str]):
        """分析样本特征
        
        Args:
            samples: 样本列表
        """
        for sample in samples:
            # 词元统计
            tokens = self.text_processor.tokenize(sample)
            for token in tokens:
                self.feature_stats['token_frequency'][token] = \
                    self.feature_stats['token_frequency'].get(token, 0) + 1
            
            # 序列长度统计
            self.feature_stats['sequence_lengths'].append(len(tokens))
            
            # 领域特征识别
            domain = self.text_processor.identify_domain(sample)
            self.feature_stats['domain_distribution'][domain] = \
                self.feature_stats['domain_distribution'].get(domain, 0) + 1
    
    def _select_samples(self, samples: List[str], target_size: int) -> List[str]:
        """选择代表性样本
        
        Args:
            samples: 候选样本列表
            target_size: 目标样本数
            
        Returns:
            List[str]: 选中的样本列表
        """
        if len(samples) <= target_size:
            return samples
        
        selected = []
        feature_coverage = set()
        
        # 计算样本重要性得分
        sample_scores = []
        for sample in samples:
            features = self.text_processor.extract_features(sample)
            coverage_score = len(set(features) - feature_coverage) / len(features) if features else 0
            diversity_score = self._calculate_diversity_score(sample, selected)
            
            score = coverage_score * 0.7 + diversity_score * 0.3
            sample_scores.append((sample, score))
        
        # 按得分排序并选择
        sample_scores.sort(key=lambda x: x[1], reverse=True)
        selected = [s[0] for s in sample_scores[:target_size]]
        
        return selected
    
    def _validate_calibration_set(self, samples: List[str]) -> bool:
        """验证校准集质量
        
        Args:
            samples: 校准样本列表
            
        Returns:
            bool: 是否满足质量要求
        """
        if not samples:
            return False
            
        # 检查样本数量
        if len(samples) < self.calibration_params['min_samples']:
            return False
        
        # 检查特征覆盖率
        total_features = set()
        for sample in samples:
            features = self.text_processor.extract_features(sample)
            total_features.update(features)
        
        coverage = len(total_features) / len(self.feature_stats['token_frequency'])
        if coverage < self.calibration_params['coverage_threshold']:
            return False
        
        # 检查多样性
        avg_diversity = np.mean([
            self._calculate_diversity_score(s, samples[:i] + samples[i+1:])
            for i, s in enumerate(samples)
        ])
        if avg_diversity < self.calibration_params['diversity_threshold']:
            return False
        
        return True
    
    def _enhance_calibration_set(self, samples: List[str]) -> List[str]:
        """增强校准集质量
        
        Args:
            samples: 原始校准样本列表
            
        Returns:
            List[str]: 增强后的样本列表
        """
        enhanced_samples = samples.copy()
        
        # 识别欠表达特征
        feature_freq = {}
        for sample in samples:
            features = self.text_processor.extract_features(sample)
            for f in features:
                feature_freq[f] = feature_freq.get(f, 0) + 1
        
        underrepresented = {
            f: count for f, count in feature_freq.items()
            if count < len(samples) * 0.1  # 出现频率低于10%的特征
        }
        
        # 添加补充样本
        if underrepresented:
            additional_samples = self._generate_complementary_samples(
                underrepresented,
                target_count=min(100, len(samples))
            )
            enhanced_samples.extend(additional_samples)
        
        return enhanced_samples
    
    def _calculate_diversity_score(self, sample: str, other_samples: List[str]) -> float:
        """计算样本多样性得分
        
        Args:
            sample: 待评估样本
            other_samples: 其他样本列表
            
        Returns:
            float: 多样性得分
        """
        if not other_samples:
            return 1.0
            
        features = set(self.text_processor.extract_features(sample))
        
        # 计算与其他样本的平均特征重叠
        overlaps = []
        for other in other_samples:
            other_features = set(self.text_processor.extract_features(other))
            if other_features:
                overlap = len(features & other_features) / len(features | other_features)
                overlaps.append(overlap)
        
        # 多样性得分 = 1 - 平均重叠度
        return 1.0 - (np.mean(overlaps) if overlaps else 0.0)
    
    def _generate_complementary_samples(self,
                                     target_features: Dict[str, int],
                                     target_count: int) -> List[str]:
        """生成补充样本
        
        Args:
            target_features: 目标特征及其频率
            target_count: 目标样本数
            
        Returns:
            List[str]: 生成的补充样本
        """
        # 这里应该实现实际的样本生成逻辑
        # 由于我们现在不下载英文模型，这里返回空列表
        return []
    
    def _save_calibration_set(self, samples: List[str], output_dir: str):
        """保存校准集
        
        Args:
            samples: 校准样本列表
            output_dir: 输出目录
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存样本
        samples_file = os.path.join(output_dir, "calibration_samples.txt")
        with open(samples_file, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(f"{sample}\n")
        
        # 保存统计信息
        stats_file = os.path.join(output_dir, "calibration_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self._generate_stats_report(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"校准集已保存到: {output_dir}")
    
    def _generate_stats_report(self) -> Dict:
        """生成统计报告
        
        Returns:
            Dict: 统计报告
        """
        return {
            "sample_stats": {
                "total_samples": len(self.feature_stats['sequence_lengths']),
                "avg_length": np.mean(self.feature_stats['sequence_lengths']),
                "length_distribution": {
                    "min": np.min(self.feature_stats['sequence_lengths']),
                    "max": np.max(self.feature_stats['sequence_lengths']),
                    "std": np.std(self.feature_stats['sequence_lengths'])
                }
            },
            "feature_stats": {
                "unique_tokens": len(self.feature_stats['token_frequency']),
                "top_tokens": dict(sorted(
                    self.feature_stats['token_frequency'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:100]),
                "domain_distribution": self.feature_stats['domain_distribution']
            },
            "quality_metrics": {
                "coverage": len(self.feature_stats['feature_coverage']) / len(self.feature_stats['token_frequency']),
                "diversity": np.mean([
                    len(set(self.text_processor.extract_features(s)))
                    for s in self.feature_stats['token_frequency'].keys()
                ])
            }
        }
    
    def _process_text_file(self, file_path: Path) -> List[str]:
        """处理文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 提取的样本列表
        """
        samples = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        samples.append(line.strip())
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
        return samples
    
    def _process_json_file(self, file_path: Path) -> List[str]:
        """处理JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 提取的样本列表
        """
        samples = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.jsonl':
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            if isinstance(data, dict):
                                samples.extend(self._extract_text_from_dict(data))
                else:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                samples.extend(self._extract_text_from_dict(item))
                    elif isinstance(data, dict):
                        samples.extend(self._extract_text_from_dict(data))
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
        return samples
    
    def _process_csv_file(self, file_path: Path) -> List[str]:
        """处理CSV文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 提取的样本列表
        """
        samples = []
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    samples.extend(row.values())
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
        return samples
    
    def _extract_text_from_dict(self, data: Dict) -> List[str]:
        """从字典中提取文本
        
        Args:
            data: 字典数据
            
        Returns:
            List[str]: 提取的文本列表
        """
        texts = []
        for value in data.values():
            if isinstance(value, str):
                texts.append(value)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, str):
                        texts.append(item)
                    elif isinstance(item, dict):
                        texts.extend(self._extract_text_from_dict(item))
            elif isinstance(value, dict):
                texts.extend(self._extract_text_from_dict(value))
        return texts 