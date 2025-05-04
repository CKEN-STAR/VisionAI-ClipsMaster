from typing import List, Dict, Tuple
import os
import json
from loguru import logger
from src.core.language_detector import LanguageDetector

class ContaminationError(Exception):
    pass

def check_cross_contamination(dataset: List[Dict], isolate: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """训练前数据污染检测，发现混合语言样本自动隔离并报错
    
    Args:
        dataset: 待检查的数据集
        isolate: 是否隔离污染样本（默认True）
        
    Returns:
        Tuple[List[Dict], List[Dict]]: (清洁样本, 污染样本)
        
    Raises:
        ContaminationError: 当检测到混合语言且isolate=False时抛出
    """
    detector = LanguageDetector()
    clean_samples = []
    contaminated_samples = []
    
    for sample in dataset:
        # 假设每个样本有 'origin' 字段，内容为原始文本，和 'id' 字段
        ratios = detector.detect_hybrid(sample['origin'])
        is_hybrid = (ratios['zh_ratio'] > 0.2 and ratios['en_ratio'] > 0.2)
        
        if is_hybrid:
            logger.warning(f"检测到混合语言训练样本: {sample['id']}")
            contaminated_samples.append(sample)
        else:
            clean_samples.append(sample)
    
    # 处理污染样本
    if contaminated_samples:
        if isolate:
            # 将污染样本保存到隔离文件
            isolation_dir = "data/training/isolated"
            os.makedirs(isolation_dir, exist_ok=True)
            isolation_file = os.path.join(isolation_dir, f"contaminated_{len(contaminated_samples)}.json")
            
            try:
                with open(isolation_file, 'w', encoding='utf-8') as f:
                    json.dump(contaminated_samples, f, ensure_ascii=False, indent=2)
                logger.info(f"已隔离 {len(contaminated_samples)} 个污染样本到 {isolation_file}")
            except Exception as e:
                logger.error(f"样本隔离失败: {e}")
        else:
            # 不隔离则抛出异常
            raise ContaminationError(f"检测到 {len(contaminated_samples)} 个污染样本")
    
    return clean_samples, contaminated_samples 