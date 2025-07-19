"""
性能分级系统
根据硬件性能对设备进行分级
"""

import os
import platform
from typing import Dict, Any, Optional
from enum import Enum

class PerformanceTier(Enum):
    """性能等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class PerformanceTierClassifier:
    """性能分级分类器"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.performance_tier = self._classify_performance()
    
    def _get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        info = {
            'platform': platform.system(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'cpu_count': os.cpu_count() or 1,
            'memory_gb': 4  # 默认值
        }
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            info['memory_gb'] = memory.total // (1024**3)
            info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 2000
            info['cpu_percent'] = psutil.cpu_percent(interval=1)
        except ImportError:
            info['cpu_freq'] = 2000
            info['cpu_percent'] = 50
        
        return info
    
    def classify(self, system_info: Dict[str, Any] = None) -> PerformanceTier:
        """
        分类性能等级（公共方法）

        Args:
            system_info: 系统信息，如果为None则使用内部系统信息

        Returns:
            性能等级
        """
        if system_info is None:
            system_info = self.system_info

        try:
            cpu_count = system_info.get('cpu_count', 1)
            memory_gb = system_info.get('memory_gb', 4)
            cpu_freq = system_info.get('cpu_freq', 2000)

            # 基于CPU核心数、内存和频率进行分级
            score = 0

            # CPU核心数评分
            if cpu_count >= 8:
                score += 3
            elif cpu_count >= 4:
                score += 2
            elif cpu_count >= 2:
                score += 1

            # 内存评分
            if memory_gb >= 16:
                score += 3
            elif memory_gb >= 8:
                score += 2
            elif memory_gb >= 4:
                score += 1

            # CPU频率评分
            if cpu_freq >= 3000:
                score += 2
            elif cpu_freq >= 2500:
                score += 1

            # 根据总分确定等级
            if score >= 7:
                return PerformanceTier.ULTRA
            elif score >= 5:
                return PerformanceTier.HIGH
            elif score >= 3:
                return PerformanceTier.MEDIUM
            else:
                return PerformanceTier.LOW

        except Exception as e:
            print(f"[WARN] 性能分级失败: {e}")
            return PerformanceTier.LOW

    def _classify_performance(self) -> PerformanceTier:
        """分类性能等级"""
        try:
            cpu_count = self.system_info['cpu_count']
            memory_gb = self.system_info['memory_gb']
            cpu_freq = self.system_info.get('cpu_freq', 2000)
            
            # 计算性能分数
            score = 0
            
            # CPU核心数评分
            if cpu_count >= 8:
                score += 30
            elif cpu_count >= 4:
                score += 20
            elif cpu_count >= 2:
                score += 10
            
            # 内存评分
            if memory_gb >= 16:
                score += 30
            elif memory_gb >= 8:
                score += 20
            elif memory_gb >= 4:
                score += 10
            
            # CPU频率评分
            if cpu_freq >= 3000:
                score += 25
            elif cpu_freq >= 2500:
                score += 15
            elif cpu_freq >= 2000:
                score += 10
            
            # 检查GPU（简化检测）
            if self._has_dedicated_gpu():
                score += 15
            
            # 根据分数分级
            if score >= 80:
                return PerformanceTier.ULTRA
            elif score >= 60:
                return PerformanceTier.HIGH
            elif score >= 40:
                return PerformanceTier.MEDIUM
            else:
                return PerformanceTier.LOW
                
        except Exception as e:
            print(f"[WARN] 性能分级失败: {e}")
            return PerformanceTier.MEDIUM
    
    def _has_dedicated_gpu(self) -> bool:
        """检查是否有独立GPU"""
        try:
            import subprocess
            
            if platform.system() == "Windows":
                # 检查Windows GPU
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                      capture_output=True, text=True, timeout=10)
                gpu_info = result.stdout.lower()
                return any(brand in gpu_info for brand in ['nvidia', 'amd', 'radeon'])
            else:
                # Linux/Mac的简化检测
                return False
                
        except Exception:
            return False
    
    def get_tier(self) -> PerformanceTier:
        """获取性能等级"""
        return self.performance_tier
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return self.system_info.copy()
    
    def get_recommended_settings(self) -> Dict[str, Any]:
        """获取推荐设置"""
        tier = self.performance_tier
        
        settings = {
            PerformanceTier.LOW: {
                'max_threads': 1,
                'cache_size_mb': 64,
                'ui_animations': False,
                'preview_quality': 'low',
                'auto_save_interval': 300,  # 5分钟
                'memory_limit_mb': 512
            },
            PerformanceTier.MEDIUM: {
                'max_threads': 2,
                'cache_size_mb': 128,
                'ui_animations': True,
                'preview_quality': 'medium',
                'auto_save_interval': 180,  # 3分钟
                'memory_limit_mb': 1024
            },
            PerformanceTier.HIGH: {
                'max_threads': 4,
                'cache_size_mb': 256,
                'ui_animations': True,
                'preview_quality': 'high',
                'auto_save_interval': 120,  # 2分钟
                'memory_limit_mb': 2048
            },
            PerformanceTier.ULTRA: {
                'max_threads': 8,
                'cache_size_mb': 512,
                'ui_animations': True,
                'preview_quality': 'ultra',
                'auto_save_interval': 60,   # 1分钟
                'memory_limit_mb': 4096
            }
        }
        
        return settings.get(tier, settings[PerformanceTier.MEDIUM])

# 全局分类器实例
_classifier: Optional[PerformanceTierClassifier] = None

def get_performance_tier() -> str:
    """获取性能等级字符串"""
    global _classifier
    if _classifier is None:
        _classifier = PerformanceTierClassifier()
    return _classifier.get_tier().value

def get_performance_tier_enum() -> PerformanceTier:
    """获取性能等级枚举"""
    global _classifier
    if _classifier is None:
        _classifier = PerformanceTierClassifier()
    return _classifier.get_tier()

def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    global _classifier
    if _classifier is None:
        _classifier = PerformanceTierClassifier()
    return _classifier.get_system_info()

def get_recommended_settings() -> Dict[str, Any]:
    """获取推荐设置"""
    global _classifier
    if _classifier is None:
        _classifier = PerformanceTierClassifier()
    return _classifier.get_recommended_settings()

def refresh_performance_classification():
    """刷新性能分类"""
    global _classifier
    _classifier = PerformanceTierClassifier()

def get_performance_report() -> str:
    """获取性能报告"""
    global _classifier
    if _classifier is None:
        _classifier = PerformanceTierClassifier()
    
    tier = _classifier.get_tier()
    info = _classifier.get_system_info()
    settings = _classifier.get_recommended_settings()
    
    report = [
        "=== 性能分级报告 ===",
        f"性能等级: {tier.value.upper()}",
        "",
        "系统信息:",
        f"  平台: {info['platform']}",
        f"  架构: {info['architecture']}",
        f"  CPU核心数: {info['cpu_count']}",
        f"  内存: {info['memory_gb']}GB",
        f"  CPU频率: {info.get('cpu_freq', 'N/A')}MHz",
        "",
        "推荐设置:",
        f"  最大线程数: {settings['max_threads']}",
        f"  缓存大小: {settings['cache_size_mb']}MB",
        f"  UI动画: {'启用' if settings['ui_animations'] else '禁用'}",
        f"  预览质量: {settings['preview_quality']}",
        f"  自动保存间隔: {settings['auto_save_interval']}秒"
    ]
    
    return "\n".join(report)

__all__ = [
    'PerformanceTier',
    'PerformanceTierClassifier',
    'get_performance_tier',
    'get_performance_tier_enum',
    'get_system_info',
    'get_recommended_settings',
    'refresh_performance_classification',
    'get_performance_report'
]
