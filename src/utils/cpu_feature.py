"""CPU指令集检测模块

此模块负责检测CPU支持的指令集特性，主要功能包括：
1. 基础指令集检测
2. 高级指令集检测
3. CPU特性分析
4. 性能优化建议
"""

import platform
import cpuinfo
from typing import Dict, List, Set
from loguru import logger

class CPUFeatureDetector:
    """CPU特性检测器"""
    
    def __init__(self):
        """初始化CPU特性检测器"""
        self._cpu_info = None
        self._features = set()
        self._cache_info = {}
        
        # 初始化CPU信息
        self._init_cpu_info()
        
    def get_cpu_info(self) -> Dict:
        """获取CPU信息
        
        Returns:
            Dict: CPU信息字典
        """
        return self._cpu_info or {}
    
    def get_supported_features(self) -> Set[str]:
        """获取支持的CPU特性
        
        Returns:
            Set[str]: 特性集合
        """
        return self._features
    
    def has_feature(self, feature: str) -> bool:
        """检查是否支持特定特性
        
        Args:
            feature: 特性名称
            
        Returns:
            bool: 是否支持
        """
        return feature.lower() in self._features
    
    def get_cache_info(self) -> Dict:
        """获取CPU缓存信息
        
        Returns:
            Dict: 缓存信息字典
        """
        return self._cache_info
    
    def _init_cpu_info(self):
        """初始化CPU信息"""
        try:
            # 获取CPU信息
            info = cpuinfo.get_cpu_info()
            
            # 提取基本信息
            self._cpu_info = {
                'brand': info.get('brand_raw', ''),
                'vendor': info.get('vendor_id_raw', ''),
                'arch': info.get('arch', ''),
                'bits': info.get('bits', 0),
                'count': info.get('count', 0),
                'hz': info.get('hz_actual_friendly', ''),
                'l2_cache_size': info.get('l2_cache_size', 0),
                'l3_cache_size': info.get('l3_cache_size', 0)
            }
            
            # 提取特性集合
            flags = info.get('flags', [])
            self._features = {flag.lower() for flag in flags}
            
            # 提取缓存信息
            self._cache_info = {
                'l1_data': info.get('l1_data_cache_size', 0),
                'l1_instruction': info.get('l1_instruction_cache_size', 0),
                'l2': info.get('l2_cache_size', 0),
                'l3': info.get('l3_cache_size', 0)
            }
            
            logger.info(f"CPU信息初始化完成: {self._cpu_info['brand']}")
            
        except Exception as e:
            logger.warning(f"CPU信息初始化失败: {str(e)}")
            # 设置默认值
            self._cpu_info = {
                'brand': 'Unknown',
                'vendor': 'Unknown',
                'arch': 'Unknown',
                'bits': 64,
                'count': 1,
                'hz': 'Unknown',
                'l2_cache_size': 0,
                'l3_cache_size': 0
            }
            self._features = set()
            self._cache_info = {
                'l1_data': 0,
                'l1_instruction': 0,
                'l2': 0,
                'l3': 0
            }
    
    def estimate_performance_score(self) -> float:
        """估算CPU性能分数
        
        Returns:
            float: 性能分数(0-100)
        """
        score = 50.0  # 基础分数
        
        try:
            # 根据核心数加分
            core_count = self._cpu_info.get('count', 1)
            score += min(core_count * 2, 20)  # 最多加20分
            
            # 根据指令集支持加分
            if self.has_feature('avx2'):
                score += 10
            if self.has_feature('avx512f'):
                score += 15
            if self.has_feature('sse4_2'):
                score += 5
            
            # 根据缓存大小加分
            l3_cache = self._cache_info.get('l3', 0)
            score += min(l3_cache / (1024 * 1024), 5)  # 最多加5分
            
        except Exception as e:
            logger.warning(f"性能分数计算失败: {str(e)}")
        
        return min(max(score, 0), 100)  # 确保分数在0-100之间
    
    def check_instruction_sets(self) -> Dict[str, bool]:
        """检查CPU支持的指令集
        
        Returns:
            Dict[str, bool]: 指令集支持情况
        """
        try:
            flags = set(self._features)
            
            support_status = {
                "sse": "sse" in flags,
                "sse2": "sse2" in flags,
                "sse3": "sse3" in flags,
                "ssse3": "ssse3" in flags,
                "sse4_1": "sse4_1" in flags,
                "sse4_2": "sse4_2" in flags,
                "avx": "avx" in flags,
                "avx2": "avx2" in flags,
                "avx512f": "avx512f" in flags,
                "fma3": "fma3" in flags,
                "f16c": "f16c" in flags,
                "mmx": "mmx" in flags,
                "popcnt": "popcnt" in flags,
                "aes": "aes" in flags
            }
            
            return support_status
            
        except Exception as e:
            logger.error(f"指令集检测失败: {str(e)}")
            return {}
    
    def check_advanced_features(self) -> Dict[str, bool]:
        """检查高级CPU特性
        
        Returns:
            Dict[str, bool]: 高级特性支持情况
        """
        try:
            features = {
                "hyperthreading": self._check_hyperthreading(),
                "turbo_boost": self._check_turbo_boost(),
                "virtualization": self._check_virtualization(),
                "numa": self._check_numa(),
                "aes_ni": "aes" in self._features,
                "rdrand": "rdrand" in self._features
            }
            
            return features
            
        except Exception as e:
            logger.error(f"高级特性检测失败: {str(e)}")
            return {}
    
    def _check_hyperthreading(self) -> bool:
        """检查是否支持超线程"""
        try:
            physical_cores = self._cpu_info.get('count', 1)
            logical_cores = self._cpu_info.get('count', 1)
            return logical_cores > physical_cores
        except Exception:
            return False
    
    def _check_turbo_boost(self) -> bool:
        """检查是否支持睿频加速"""
        try:
            flags = self._features
            return 'ida' in flags or 'turbo' in flags
        except Exception:
            return False
    
    def _check_virtualization(self) -> bool:
        """检查是否支持虚拟化"""
        try:
            flags = self._features
            return 'vmx' in flags or 'svm' in flags
        except Exception:
            return False
    
    def _check_numa(self) -> bool:
        """检查是否支持NUMA架构"""
        try:
            if platform.system() == 'Linux':
                import os
                return os.path.exists('/sys/devices/system/node/node1')
            return False
        except Exception:
            return False
    
    def get_optimization_features(self) -> Set[str]:
        """获取可用于优化的CPU特性
        
        Returns:
            Set[str]: 可用于优化的特性集合
        """
        try:
            flags = set(self._features)
            
            # 定义优化特性
            optimization_features = {
                'sse4_1', 'sse4_2', 'avx', 'avx2', 'fma3',
                'f16c', 'popcnt', 'aes', 'avx512f'
            }
            
            # 返回支持的特性
            return flags.intersection(optimization_features)
            
        except Exception as e:
            logger.error(f"优化特性检测失败: {str(e)}")
            return set()
    
    def check_compatibility(self) -> Dict[str, bool]:
        """检查CPU兼容性
        
        Returns:
            Dict[str, bool]: 兼容性检查结果
        """
        try:
            flags = set(self._features)
            
            compatibility = {
                "meets_requirements": self._features.issubset(flags),
                "missing_features": list(set(self._features) - flags),
                "has_advanced_features": bool(self.check_advanced_features()),
                "optimization_level": self._get_optimization_level(flags)
            }
            
            return compatibility
            
        except Exception as e:
            logger.error(f"兼容性检查失败: {str(e)}")
            return {}
    
    def _get_optimization_level(self, flags: Set[str]) -> str:
        """获取CPU优化级别
        
        Args:
            flags: CPU特性标志集合
            
        Returns:
            str: 优化级别
        """
        if 'avx512f' in flags:
            return 'extreme'
        elif 'avx2' in flags and 'fma3' in flags:
            return 'high'
        elif 'avx' in flags:
            return 'medium'
        elif 'sse4_2' in flags:
            return 'basic'
        else:
            return 'minimal'
    
    def get_cpu_details(self) -> Dict:
        """获取CPU详细信息
        
        Returns:
            Dict: CPU详细信息
        """
        try:
            details = {
                "brand": self._cpu_info.get('brand', 'Unknown'),
                "architecture": self._cpu_info.get('arch', 'Unknown'),
                "bits": self._cpu_info.get('bits', 0),
                "frequency": self._cpu_info.get('hz', 'Unknown'),
                "cores": {
                    "physical": self._cpu_info.get('count', 1),
                    "logical": self._cpu_info.get('count', 1)
                },
                "cache": self._cache_info,
                "features": self.check_instruction_sets(),
                "advanced_features": self.check_advanced_features(),
                "optimization_features": list(self.get_optimization_features())
            }
            
            return details
            
        except Exception as e:
            logger.error(f"获取CPU详情失败: {str(e)}")
            return {}
    
    def suggest_optimizations(self) -> List[str]:
        """提供CPU优化建议
        
        Returns:
            List[str]: 优化建议列表
        """
        suggestions = []
        features = self.check_instruction_sets()
        advanced = self.check_advanced_features()
        
        try:
            # 检查基础优化
            if not features.get('avx2', False):
                suggestions.append("建议使用支持AVX2的CPU以获得更好的性能")
            
            if not features.get('fma3', False):
                suggestions.append("缺少FMA3指令集支持，可能影响深度学习性能")
            
            # 检查高级特性
            if not advanced.get('hyperthreading', False):
                suggestions.append("启用超线程技术可以提高并行处理能力")
            
            if not advanced.get('turbo_boost', False):
                suggestions.append("启用睿频加速可以提高峰值性能")
            
            # 内存相关
            if not advanced.get('numa', False):
                suggestions.append("对于大内存工作负载，建议使用支持NUMA的系统")
            
            # 安全特性
            if not advanced.get('aes_ni', False):
                suggestions.append("缺少AES-NI支持，可能影响加密性能")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成优化建议失败: {str(e)}")
            return ["无法生成优化建议"] 