"""量化方法选型评估模块

此模块负责评估和选择最适合的量化方法，包括:
1. 模型类型分析
2. 量化方法评分
3. 硬件兼容性检查
4. 性能影响评估
5. 精度损失评估
"""

import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger
from ..utils.device_manager import HybridDevice
from ..utils.memory_manager import MemoryManager

class QuantizationSelector:
    """量化方法选择器"""
    
    def __init__(self, 
                 device_manager: Optional[HybridDevice] = None,
                 memory_manager: Optional[MemoryManager] = None):
        """初始化量化选择器
        
        Args:
            device_manager: 设备管理器实例
            memory_manager: 内存管理器实例
        """
        self.device_manager = device_manager or HybridDevice()
        self.memory_manager = memory_manager or MemoryManager()
        
        # 量化方法评分表
        self.method_scores = {
            'GPTQ': {  # GPT-Q量化方法
                'en': 0.92,
                'zh': 0.89,
                'performance_impact': 0.15,  # 性能影响(越小越好)
                'memory_reduction': 0.75,    # 内存减少比例
                'hardware_compatibility': ['cuda', 'cpu'],
                'min_bits': 4,
                'max_bits': 8
            },
            'AWQ': {   # Activation-aware Weight Quantization
                'en': 0.83,
                'zh': 0.81,
                'performance_impact': 0.20,
                'memory_reduction': 0.80,
                'hardware_compatibility': ['cuda', 'cpu'],
                'min_bits': 4,
                'max_bits': 8
            },
            'LLM.int8': {  # LLM.int8量化
                'en': 0.88,
                'zh': 0.86,
                'performance_impact': 0.10,
                'memory_reduction': 0.65,
                'hardware_compatibility': ['cuda', 'cpu', 'mps'],
                'min_bits': 8,
                'max_bits': 8
            },
            'Dynamic': {  # 动态量化
                'en': 0.85,
                'zh': 0.83,
                'performance_impact': 0.25,
                'memory_reduction': 0.70,
                'hardware_compatibility': ['cuda', 'cpu', 'mps'],
                'min_bits': 4,
                'max_bits': 8
            }
        }
        
        # 硬件兼容性权重
        self.hardware_weights = {
            'cuda': 1.0,
            'cpu': 0.8,
            'mps': 0.9
        }
    
    def select_quant_method(self, 
                          model_type: str,
                          target_device: Optional[str] = None,
                          memory_constraint: Optional[float] = None,
                          min_accuracy: Optional[float] = None) -> Tuple[str, Dict]:
        """选择最佳量化方法
        
        Args:
            model_type: 模型类型 ('en'/'zh')
            target_device: 目标设备类型
            memory_constraint: 内存限制 (GB)
            min_accuracy: 最低精度要求
            
        Returns:
            Tuple[str, Dict]: (选中的方法名称, 方法详细信息)
        """
        if target_device is None:
            target_device = self.device_manager.select_device()
        
        scores = {}
        for method, info in self.method_scores.items():
            # 检查硬件兼容性
            if target_device not in info['hardware_compatibility']:
                continue
                
            # 检查内存约束
            if memory_constraint and info['memory_reduction'] * memory_constraint > self.memory_manager.get_available_memory():
                continue
                
            # 检查精度要求
            if min_accuracy and info[model_type] < min_accuracy:
                continue
            
            # 计算综合得分
            base_score = info[model_type]
            hardware_score = self.hardware_weights.get(target_device, 0.5)
            performance_score = 1 - info['performance_impact']
            
            # 综合评分计算
            final_score = (
                base_score * 0.4 +          # 精度权重
                hardware_score * 0.3 +      # 硬件兼容性权重
                performance_score * 0.3     # 性能权重
            )
            
            scores[method] = final_score
            
        if not scores:
            logger.warning("没有找到符合要求的量化方法")
            return "Dynamic", self.method_scores["Dynamic"]
        
        # 选择得分最高的方法
        selected_method = max(scores.items(), key=lambda x: x[1])[0]
        return selected_method, self.method_scores[selected_method]
    
    def analyze_quant_impact(self, method: str, model_type: str) -> Dict:
        """分析量化影响
        
        Args:
            method: 量化方法名称
            model_type: 模型类型
            
        Returns:
            Dict: 影响分析结果
        """
        if method not in self.method_scores:
            raise ValueError(f"未知的量化方法: {method}")
            
        info = self.method_scores[method]
        
        return {
            "accuracy_impact": 1 - info[model_type],
            "performance_impact": info['performance_impact'],
            "memory_reduction": info['memory_reduction'],
            "hardware_compatibility": info['hardware_compatibility'],
            "bit_range": {
                "min": info['min_bits'],
                "max": info['max_bits']
            }
        }
    
    def get_supported_methods(self) -> List[str]:
        """获取支持的量化方法列表"""
        return list(self.method_scores.keys())
    
    def export_method_configs(self, output_path: str):
        """导出量化方法配置
        
        Args:
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.method_scores, f, indent=4, ensure_ascii=False)
            logger.info(f"量化方法配置已导出到: {output_path}")
        except Exception as e:
            logger.error(f"导出配置失败: {str(e)}")
            
    def validate_method_compatibility(self, method: str, model_config: Dict) -> bool:
        """验证量化方法与模型的兼容性
        
        Args:
            method: 量化方法名称
            model_config: 模型配置信息
            
        Returns:
            bool: 是否兼容
        """
        if method not in self.method_scores:
            return False
            
        method_info = self.method_scores[method]
        
        # 检查位宽兼容性
        if 'quantization' in model_config:
            required_bits = model_config['quantization'].get('bits', 8)
            if not (method_info['min_bits'] <= required_bits <= method_info['max_bits']):
                return False
        
        # 检查硬件兼容性
        if 'hardware' in model_config:
            required_device = model_config['hardware'].get('device', 'cpu')
            if required_device not in method_info['hardware_compatibility']:
                return False
        
        return True 