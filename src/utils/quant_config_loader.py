#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
量化配置加载器
负责加载和管理量化级别配置
"""

import os
import yaml
import psutil
from typing import Dict, List, Any, Optional, Union
from loguru import logger

# 配置文件路径
QUANT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'configs', 'quant_levels.yaml')

class QuantConfigLoader:
    """量化配置加载器类，用于加载和查询量化配置"""
    
    def __init__(self, config_path: str = QUANT_CONFIG_PATH):
        """
        初始化量化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为预设路径
        """
        self.config_path = config_path
        self._config = None
        self._load_config()
        
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"量化配置文件不存在: {self.config_path}")
                raise FileNotFoundError(f"量化配置文件不存在: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                
            logger.info(f"成功加载量化配置，版本: {self.get_version()}")
            
        except Exception as e:
            logger.error(f"加载量化配置失败: {str(e)}")
            raise
    
    def reload_config(self) -> bool:
        """重新加载配置文件"""
        try:
            self._load_config()
            return True
        except Exception as e:
            logger.error(f"重新加载量化配置失败: {str(e)}")
            return False
    
    def get_config(self) -> Dict:
        """获取完整配置"""
        return self._config or {}
    
    def get_version(self) -> str:
        """获取配置版本"""
        return self._config.get('version', 'unknown')
    
    def get_default_level(self) -> str:
        """获取默认量化级别"""
        return self._config.get('default_level', 'Q4_K_M')
    
    def is_auto_select_enabled(self) -> bool:
        """是否启用自动选择量化级别"""
        return self._config.get('auto_select', True)
    
    def get_quant_levels(self) -> List[Dict[str, Any]]:
        """获取所有量化级别信息"""
        return self._config.get('quant_levels', [])
    
    def get_quant_level_names(self) -> List[str]:
        """获取所有量化级别名称"""
        return [level.get('name') for level in self.get_quant_levels()]
    
    def get_level_info(self, level_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定量化级别的详细信息
        
        Args:
            level_name: 量化级别名称，如 'Q4_K_M'
        
        Returns:
            Dict 或 None: 量化级别信息
        """
        for level in self.get_quant_levels():
            if level.get('name') == level_name:
                return level
        return None
    
    def get_model_specific_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取特定模型的量化配置
        
        Args:
            model_name: 模型名称，如 'qwen2.5-7b-zh'
            
        Returns:
            Dict: 模型特定配置
        """
        model_specific = self._config.get('model_specific', {})
        return model_specific.get(model_name, {})
    
    def get_model_default_level(self, model_name: str) -> str:
        """获取特定模型的默认量化级别"""
        model_config = self.get_model_specific_config(model_name)
        return model_config.get('default_level', self.get_default_level())
    
    def get_auto_select_thresholds(self) -> Dict[str, Optional[int]]:
        """获取自动选择量化级别的内存阈值"""
        return self._config.get('auto_select_thresholds', {})
    
    def select_optimal_quant_level(self, available_memory_mb: Optional[float] = None) -> str:
        """
        根据可用内存选择最佳量化级别
        
        Args:
            available_memory_mb: 可用内存(MB)，如果为None则自动获取
            
        Returns:
            str: 最适合的量化级别名称
        """
        if not self.is_auto_select_enabled():
            return self.get_default_level()
        
        # 如果未提供可用内存，则自动获取
        if available_memory_mb is None:
            mem = psutil.virtual_memory()
            available_memory_mb = mem.available / (1024 * 1024)  # 转换为MB
        
        # 获取阈值
        thresholds = self.get_auto_select_thresholds()
        
        # 从低到高判断
        if available_memory_mb < thresholds.get('emergency', 3500):
            return "Q2_K"
        elif available_memory_mb < thresholds.get('low', 4500):
            return "Q3_K_M"
        elif available_memory_mb < thresholds.get('normal', 6500):
            return "Q4_K_M"
        elif available_memory_mb < thresholds.get('high', 9000):
            return "Q5_K_M"
        else:
            return "Q6_K"
    
    def get_optimal_quant_params(self, model_name: str, available_memory_mb: Optional[float] = None) -> Dict[str, Any]:
        """
        获取最佳量化参数组合
        
        Args:
            model_name: 模型名称
            available_memory_mb: 可用内存(MB)，如果为None则自动获取
            
        Returns:
            Dict: 包含量化级别和参数的字典
        """
        # 选择最佳量化级别
        quant_level = self.select_optimal_quant_level(available_memory_mb)
        
        # 获取量化级别基本信息
        level_info = self.get_level_info(quant_level) or {}
        
        # 获取模型特定参数
        model_config = self.get_model_specific_config(model_name)
        quant_params = model_config.get('quant_params', {}).get(quant_level, {})
        
        # 合并结果
        result = {
            'level': quant_level,
            'memory_usage_mb': level_info.get('memory_usage'),
            'description': level_info.get('desc'),
            'quality_score': level_info.get('quality_score'),
            'parameters': quant_params
        }
        
        return result
    
    def get_memory_requirement(self, level_name: str) -> int:
        """获取指定量化级别的内存需求(MB)"""
        level_info = self.get_level_info(level_name)
        if level_info:
            return level_info.get('memory_usage', 4100)  # 默认返回4100MB
        return 4100  # 默认Q4_K_M的内存需求

    def compare_levels(self, level1: str, level2: str, metric: str = 'quality_score') -> Dict[str, Any]:
        """
        比较两个量化级别
        
        Args:
            level1: 第一个量化级别名称
            level2: 第二个量化级别名称
            metric: 比较指标，如'quality_score', 'memory_usage', 'precision_loss'等
            
        Returns:
            Dict: 比较结果
        """
        info1 = self.get_level_info(level1) or {}
        info2 = self.get_level_info(level2) or {}
        
        value1 = info1.get(metric)
        value2 = info2.get(metric)
        
        if value1 is None or value2 is None:
            return {
                'error': f"指标 {metric} 不存在于一个或多个量化级别中"
            }
        
        difference = value1 - value2
        percentage = difference / value2 * 100 if value2 != 0 else float('inf')
        
        return {
            'level1': level1,
            'level2': level2,
            'metric': metric,
            'value1': value1,
            'value2': value2,
            'difference': difference,
            'percentage': percentage,
            'better': level1 if (metric == 'quality_score' and value1 > value2) or 
                              (metric != 'quality_score' and value1 < value2) else level2
        }
    
    def get_recommendations(self, system_memory_gb: float) -> List[Dict[str, Any]]:
        """
        获取系统配置下的量化级别推荐
        
        Args:
            system_memory_gb: 系统总内存(GB)
            
        Returns:
            List[Dict]: 推荐的量化级别列表，按适合程度排序
        """
        system_memory_mb = system_memory_gb * 1024
        recommendations = []
        
        for level in self.get_quant_levels():
            level_name = level.get('name')
            memory_usage = level.get('memory_usage', 0)
            recommended_min_ram = level.get('recommended_min_ram', 0)
            
            # 计算适合度分数 (0-100)
            # 如果系统内存低于推荐最小值，则降低适合度
            if system_memory_mb < recommended_min_ram:
                suitability = max(0, 50 - (recommended_min_ram - system_memory_mb) / 100)
            else:
                # 如果系统内存足够，则根据内存富余量计算适合度
                # 过高的富余量(使用不到一半的内存)也会降低分数
                usage_ratio = memory_usage / system_memory_mb
                if usage_ratio < 0.2:
                    # 使用太少内存，浪费资源
                    suitability = 70
                elif usage_ratio > 0.8:
                    # 使用太多内存，可能不稳定
                    suitability = 60
                else:
                    # 适中的使用比例
                    suitability = 100 - abs(0.5 - usage_ratio) * 100
            
            recommendations.append({
                'level': level_name,
                'description': level.get('desc'),
                'memory_usage_mb': memory_usage,
                'quality_score': level.get('quality_score', 0),
                'stability': level.get('stability', 'unknown'),
                'suitability_score': suitability,
                'suitable_for': level.get('suitable_for'),
                'use_case': level.get('use_case')
            })
        
        # 按适合度排序
        recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
        return recommendations


# 创建全局实例
quant_config = QuantConfigLoader()


def get_quant_config() -> QuantConfigLoader:
    """获取量化配置加载器实例"""
    return quant_config


if __name__ == "__main__":
    # 简单测试
    try:
        config = QuantConfigLoader()
        
        print(f"配置版本: {config.get_version()}")
        print(f"默认量化级别: {config.get_default_level()}")
        print(f"自动选择: {'启用' if config.is_auto_select_enabled() else '禁用'}")
        
        print("\n量化级别列表:")
        for level in config.get_quant_levels():
            print(f"- {level['name']}: {level['desc']} ({level['memory_usage']}MB)")
        
        print("\n自动选择阈值:")
        for name, threshold in config.get_auto_select_thresholds().items():
            print(f"- {name}: {threshold}MB")
        
        # 获取系统内存信息
        mem = psutil.virtual_memory()
        available_mb = mem.available / (1024 * 1024)
        total_gb = mem.total / (1024 * 1024 * 1024)
        
        print(f"\n系统总内存: {total_gb:.1f}GB")
        print(f"当前可用内存: {available_mb:.1f}MB")
        
        optimal_level = config.select_optimal_quant_level()
        print(f"\n当前推荐量化级别: {optimal_level}")
        
        print("\nQwen模型最佳配置:")
        params = config.get_optimal_quant_params("qwen2.5-7b-zh")
        print(params)
        
        print("\n系统配置推荐:")
        recommendations = config.get_recommendations(total_gb)
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"{i}. {rec['level']} - {rec['description']}")
            print(f"   适合度: {rec['suitability_score']:.1f}/100")
            print(f"   内存: {rec['memory_usage_mb']}MB, 质量: {rec['quality_score']}/100")
            print(f"   适用于: {rec['suitable_for']}")
            print()
        
    except Exception as e:
        print(f"测试失败: {str(e)}") 