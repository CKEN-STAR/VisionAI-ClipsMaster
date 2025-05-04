"""主语言判定策略模块

此模块实现语言判定策略，包括：
1. 阈值配置管理
2. 语言判定规则
3. 混合语言处理
4. 策略优化
5. 规则验证
"""

import os
import yaml
from typing import Dict, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from .language_detector import LanguageDetector
import numpy as np

@dataclass
class LanguageConfig:
    """语言配置数据类"""
    dominant_threshold: Dict[str, float]
    hybrid_fallback: str
    min_text_length: int = 1
    confidence_threshold: float = 0.6
    enable_auto_adjust: bool = True

class LanguageRules:
    """语言规则管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化规则管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.detector = LanguageDetector()
        self.config = self._load_config(config_path)
        self.stats = {
            'total_processed': 0,
            'zh_count': 0,
            'en_count': 0,
            'hybrid_count': 0,
            'confidence_scores': []
        }

    def determine_main_lang(self,
                          text: str,
                          update_stats: bool = True) -> Tuple[str, float]:
        """判定主要语言
        
        Args:
            text: 输入文本
            update_stats: 是否更新统计信息
            
        Returns:
            Tuple[str, float]: (语言代码, 置信度)
        """
        try:
            # 文本长度检查
            if len(text) < self.config.min_text_length:
                return self.config.hybrid_fallback, 0.0
            
            # 检测语言比例
            ratios = self.detector.detect_hybrid(text)
            
            # 计算置信度
            confidence = max(ratios['zh_ratio'], ratios['en_ratio'])
            
            # 应用判定规则
            main_lang = self._apply_rules(ratios)
            
            # 更新统计信息
            if update_stats:
                self._update_stats(main_lang, confidence)
            
            # 自动调整阈值
            if self.config.enable_auto_adjust:
                self._adjust_thresholds()
            
            return main_lang, confidence
            
        except Exception as e:
            logger.error(f"语言判定失败: {str(e)}")
            return self.config.hybrid_fallback, 0.0

    def validate_rules(self, test_cases: Dict[str, str]) -> Dict[str, Dict]:
        """验证判定规则
        
        Args:
            test_cases: 测试用例
            
        Returns:
            Dict[str, Dict]: 验证结果
        """
        results = {
            'total': len(test_cases),
            'passed': 0,
            'failed': [],
            'details': {}
        }
        
        try:
            for case_id, text in test_cases.items():
                # 判定语言
                lang, confidence = self.determine_main_lang(
                    text,
                    update_stats=False
                )
                
                # 记录结果
                results['details'][case_id] = {
                    'text': text,
                    'detected_lang': lang,
                    'confidence': confidence,
                    'ratios': self.detector.detect_hybrid(text)
                }
                
                # 验证置信度
                if confidence >= self.config.confidence_threshold:
                    results['passed'] += 1
                else:
                    results['failed'].append(case_id)
            
            return results
            
        except Exception as e:
            logger.error(f"规则验证失败: {str(e)}")
            return results

    def optimize_thresholds(self,
                          training_data: Dict[str, str],
                          target_accuracy: float = 0.95) -> Dict[str, float]:
        """优化判定阈值
        
        Args:
            training_data: 训练数据
            target_accuracy: 目标准确率
            
        Returns:
            Dict[str, float]: 优化后的阈值
        """
        try:
            # 初始化参数空间
            param_space = {
                'zh': np.arange(0.5, 1.0, 0.05),
                'en': np.arange(0.5, 1.0, 0.05)
            }
            
            best_thresholds = self.config.dominant_threshold.copy()
            best_accuracy = 0.0
            
            # 网格搜索
            for zh_threshold in param_space['zh']:
                for en_threshold in param_space['en']:
                    # 临时更新阈值
                    self.config.dominant_threshold.update({
                        'zh': zh_threshold,
                        'en': en_threshold
                    })
                    
                    # 验证效果
                    results = self.validate_rules(training_data)
                    accuracy = results['passed'] / results['total']
                    
                    # 更新最佳阈值
                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_thresholds = {
                            'zh': zh_threshold,
                            'en': en_threshold
                        }
                    
                    # 达到目标准确率则停止
                    if accuracy >= target_accuracy:
                        break
            
            # 恢复最佳阈值
            self.config.dominant_threshold = best_thresholds
            return best_thresholds
            
        except Exception as e:
            logger.error(f"阈值优化失败: {str(e)}")
            return self.config.dominant_threshold

    def get_rule_stats(self) -> Dict:
        """获取规则统计信息
        
        Returns:
            Dict: 统计信息
        """
        total = self.stats['total_processed']
        if total > 0:
            return {
                'total_processed': total,
                'language_distribution': {
                    'zh': self.stats['zh_count'] / total,
                    'en': self.stats['en_count'] / total,
                    'hybrid': self.stats['hybrid_count'] / total
                },
                'avg_confidence': np.mean(self.stats['confidence_scores']),
                'current_thresholds': self.config.dominant_threshold
            }
        return {
            'total_processed': 0,
            'language_distribution': {'zh': 0, 'en': 0, 'hybrid': 0},
            'avg_confidence': 0.0,
            'current_thresholds': self.config.dominant_threshold
        }

    def _load_config(self, config_path: Optional[str] = None) -> LanguageConfig:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            LanguageConfig: 配置对象
        """
        default_config = {
            'dominant_threshold': {'zh': 0.6, 'en': 0.6},
            'hybrid_fallback': 'zh',
            'min_text_length': 1,
            'confidence_threshold': 0.6,
            'enable_auto_adjust': True
        }
        
        try:
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    
                    # 合并配置
                    default_config.update(config_data)
            
            return LanguageConfig(**default_config)
            
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return LanguageConfig(**default_config)

    def _apply_rules(self, ratios: Dict[str, float]) -> str:
        """应用判定规则
        
        Args:
            ratios: 语言比例
            
        Returns:
            str: 主要语言
        """
        # 检查中文比例
        if ratios['zh_ratio'] >= self.config.dominant_threshold['zh']:
            return 'zh'
        
        # 检查英文比例
        if ratios['en_ratio'] >= self.config.dominant_threshold['en']:
            return 'en'
        
        # 返回默认语言
        return self.config.hybrid_fallback

    def _update_stats(self, lang: str, confidence: float):
        """更新统计信息
        
        Args:
            lang: 语言代码
            confidence: 置信度
        """
        self.stats['total_processed'] += 1
        self.stats['confidence_scores'].append(confidence)
        
        if lang == 'zh':
            self.stats['zh_count'] += 1
        elif lang == 'en':
            self.stats['en_count'] += 1
        else:
            self.stats['hybrid_count'] += 1
        
        # 限制历史记录大小
        max_history = 1000
        if len(self.stats['confidence_scores']) > max_history:
            self.stats['confidence_scores'] = \
                self.stats['confidence_scores'][-max_history:]

    def _adjust_thresholds(self):
        """自动调整阈值"""
        if self.stats['total_processed'] < 100:
            return
        
        try:
            # 计算平均置信度
            avg_confidence = np.mean(self.stats['confidence_scores'])
            
            # 根据置信度调整阈值
            if avg_confidence > 0.8:
                # 提高阈值以增加准确性
                for lang in self.config.dominant_threshold:
                    self.config.dominant_threshold[lang] = min(
                        0.9,
                        self.config.dominant_threshold[lang] + 0.05
                    )
            elif avg_confidence < 0.4:
                # 降低阈值以增加容忍度
                for lang in self.config.dominant_threshold:
                    self.config.dominant_threshold[lang] = max(
                        0.3,
                        self.config.dominant_threshold[lang] - 0.05
                    )
                    
        except Exception as e:
            logger.error(f"阈值调整失败: {str(e)}")

    def save_config(self, config_path: str) -> bool:
        """保存配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            config_data = {
                'dominant_threshold': self.config.dominant_threshold,
                'hybrid_fallback': self.config.hybrid_fallback,
                'min_text_length': self.config.min_text_length,
                'confidence_threshold': self.config.confidence_threshold,
                'enable_auto_adjust': self.config.enable_auto_adjust
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True)
            
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False 