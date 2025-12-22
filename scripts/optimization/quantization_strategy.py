#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 模型量化策略
实现多级量化和智能选择
"""

import os
import json
import psutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class QuantizationConfig:
    """量化配置类"""
    name: str
    level: str
    size_mb: int
    memory_required_mb: int
    quality_score: float
    description: str

class QuantizationManager:
    """量化管理器"""
    
    def __init__(self):
        self.configs = {
            "aggressive": QuantizationConfig(
                name="Q2_K",
                level="aggressive",
                size_mb=1800,
                memory_required_mb=2200,
                quality_score=0.75,
                description="极致压缩，适合2-3GB内存设备"
            ),
            "balanced": QuantizationConfig(
                name="Q4_K_M",
                level="balanced",
                size_mb=2600,
                memory_required_mb=3200,
                quality_score=0.88,
                description="平衡配置，推荐4GB内存设备"
            ),
            "quality": QuantizationConfig(
                name="Q5_K",
                level="quality",
                size_mb=3800,
                memory_required_mb=4500,
                quality_score=0.94,
                description="高质量，适合6GB+内存设备"
            ),
            "original": QuantizationConfig(
                name="FP16",
                level="original",
                size_mb=14400,
                memory_required_mb=16000,
                quality_score=1.0,
                description="原始精度，需要16GB+内存"
            )
        }
    
    def detect_optimal_config(self) -> str:
        """检测最佳量化配置"""
        available_memory = psutil.virtual_memory().total // (1024**3)  # GB

        if available_memory >= 16:
            return "quality"
        elif available_memory >= 6:
            return "balanced"
        elif available_memory >= 4:
            return "balanced"
        else:
            return "aggressive"
    
    def get_config(self, level: str) -> QuantizationConfig:
        """获取量化配置"""
        return self.configs.get(level, self.configs["balanced"])
    
    def estimate_download_size(self, models: List[str], level: str) -> int:
        """估算下载大小"""
        config = self.get_config(level)
        return len(models) * config.size_mb
    
    def generate_download_plan(self, 
                             target_languages: List[str],
                             memory_limit_gb: int = None) -> Dict:
        """生成下载计划"""
        if memory_limit_gb is None:
            memory_limit_gb = psutil.virtual_memory().total // (1024**3)
        
        # 选择最佳量化级别
        optimal_level = self.detect_optimal_config()
        config = self.get_config(optimal_level)
        
        plan = {
            "quantization_level": optimal_level,
            "config": config.__dict__,
            "models": [],
            "total_size_mb": 0,
            "estimated_memory_mb": 0
        }
        
        # 添加模型到计划
        for lang in target_languages:
            model_info = {
                "language": lang,
                "model_name": f"{'qwen' if lang == 'zh' else 'mistral'}-{config.name}",
                "size_mb": config.size_mb,
                "memory_required_mb": config.memory_required_mb,
                "download_url": self._get_download_url(lang, config.name)
            }
            plan["models"].append(model_info)
            plan["total_size_mb"] += config.size_mb
            plan["estimated_memory_mb"] += config.memory_required_mb
        
        return plan
    
    def _get_download_url(self, language: str, quantization: str) -> str:
        """获取下载URL"""
        base_urls = {
            "zh": "https://modelscope.cn/models/Qwen/Qwen3-8B-Instruct-GGUF/resolve/main",
            "en": "https://huggingface.co/microsoft/DialoGPT-medium/resolve/main"
        }
        
        filename = f"model-{quantization.lower()}.gguf"
        return f"{base_urls[language]}/{filename}"

class CompressionManager:
    """压缩管理器"""
    
    @staticmethod
    def compress_directory(source_dir: Path, 
                          target_file: Path,
                          compression_level: int = 6) -> bool:
        """压缩目录"""
        try:
            import zipfile
            
            with zipfile.ZipFile(target_file, 'w', zipfile.ZIP_DEFLATED, 
                               compresslevel=compression_level) as zipf:
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(source_dir)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            print(f"压缩失败: {e}")
            return False
    
    @staticmethod
    def estimate_compression_ratio(file_types: List[str]) -> float:
        """估算压缩比"""
        ratios = {
            '.py': 0.3,      # Python代码压缩比很高
            '.json': 0.2,    # JSON压缩比很高
            '.yaml': 0.25,   # YAML压缩比高
            '.md': 0.3,      # Markdown压缩比高
            '.txt': 0.3,     # 文本压缩比高
            '.bin': 0.9,     # 二进制文件压缩比低
            '.gguf': 0.95,   # 模型文件压缩比很低
            '.mp4': 0.98,    # 视频文件几乎不压缩
            '.dll': 0.8,     # 动态库中等压缩比
            '.exe': 0.7      # 可执行文件中等压缩比
        }
        
        if not file_types:
            return 0.6  # 默认压缩比
        
        avg_ratio = sum(ratios.get(ext, 0.6) for ext in file_types) / len(file_types)
        return avg_ratio

def main():
    """主函数 - 演示量化策略"""
    manager = QuantizationManager()
    
    print("🔍 VisionAI-ClipsMaster 量化策略分析")
    print("=" * 60)
    
    # 检测系统配置
    memory_gb = psutil.virtual_memory().total // (1024**3)
    optimal_level = manager.detect_optimal_config()
    
    print(f"💾 系统内存: {memory_gb} GB")
    print(f"🎯 推荐量化级别: {optimal_level}")
    print()
    
    # 显示所有配置选项
    print("📊 可用量化配置:")
    for level, config in manager.configs.items():
        marker = "👉" if level == optimal_level else "  "
        print(f"{marker} {level:12} | {config.name:8} | "
              f"{config.size_mb:5}MB | 质量:{config.quality_score:.2f} | "
              f"{config.description}")
    print()
    
    # 生成下载计划
    plan = manager.generate_download_plan(["zh", "en"])
    print("📋 推荐下载计划:")
    print(f"  量化级别: {plan['quantization_level']}")
    print(f"  总大小: {plan['total_size_mb']} MB")
    print(f"  预估内存: {plan['estimated_memory_mb']} MB")
    print()
    
    for model in plan["models"]:
        print(f"  📦 {model['language'].upper()}模型: {model['model_name']} "
              f"({model['size_mb']}MB)")

if __name__ == "__main__":
    main()
