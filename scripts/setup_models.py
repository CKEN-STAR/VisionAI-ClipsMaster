#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 模型下载和配置脚本

支持多种下载方式：
1. 自动下载（推荐）
2. 手动下载链接
3. 本地模型导入
4. 量化模型选择
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from tqdm import tqdm

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class ModelDownloader:
    """模型下载管理器"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # 模型配置
        self.model_configs = {
            "mistral-7b": {
                "name": "Mistral-7B-Instruct-v0.2",
                "language": "en",
                "size_gb": 14.4,
                "quantized_versions": {
                    "Q2_K": {"size_gb": 2.8, "quality": "低"},
                    "Q4_K_M": {"size_gb": 4.1, "quality": "中"},
                    "Q5_K": {"size_gb": 5.1, "quality": "高"},
                    "Q8_0": {"size_gb": 7.2, "quality": "极高"}
                },
                "download_urls": {
                    "huggingface": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2",
                    "gguf_q4": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
                    "gguf_q5": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q5_K.gguf"
                }
            },
            "qwen2.5-7b": {
                "name": "Qwen2.5-7B-Instruct",
                "language": "zh",
                "size_gb": 13.5,
                "quantized_versions": {
                    "Q2_K": {"size_gb": 2.7, "quality": "低"},
                    "Q4_K_M": {"size_gb": 4.0, "quality": "中"},
                    "Q5_K": {"size_gb": 5.0, "quality": "高"},
                    "Q8_0": {"size_gb": 7.1, "quality": "极高"}
                },
                "download_urls": {
                    "huggingface": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct",
                    "gguf_q4": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                    "gguf_q5": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k.gguf"
                }
            }
        }
        
    def check_available_space(self) -> float:
        """检查可用磁盘空间（GB）"""
        statvfs = os.statvfs(self.models_dir)
        return (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        
    def check_memory_limit(self) -> float:
        """检查系统内存（GB）"""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            return 8.0  # 默认假设8GB
            
    def recommend_quantization(self, model_name: str) -> str:
        """根据系统配置推荐量化级别"""
        memory_gb = self.check_memory_limit()
        
        if memory_gb <= 4:
            return "Q2_K"  # 最小内存占用
        elif memory_gb <= 6:
            return "Q4_K_M"  # 平衡性能和内存
        elif memory_gb <= 8:
            return "Q5_K"  # 较高质量
        else:
            return "Q8_0"  # 最高质量
            
    def download_file(self, url: str, filepath: Path, chunk_size: int = 8192) -> bool:
        """下载文件并显示进度"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=filepath.name,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        
            return True
            
        except Exception as e:
            print(f"下载失败: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
            
    def verify_file_integrity(self, filepath: Path, expected_hash: Optional[str] = None) -> bool:
        """验证文件完整性"""
        if not filepath.exists():
            return False
            
        # 检查文件大小
        file_size = filepath.stat().st_size
        if file_size < 1024 * 1024:  # 小于1MB可能是错误文件
            return False
            
        # 如果提供了哈希值，验证哈希
        if expected_hash:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest() == expected_hash
            
        return True
        
    def download_model(self, model_name: str, quantization: Optional[str] = None, force: bool = False) -> bool:
        """下载指定模型"""
        if model_name not in self.model_configs:
            print(f"错误: 未知模型 {model_name}")
            return False
            
        config = self.model_configs[model_name]
        
        # 自动推荐量化级别
        if quantization is None:
            quantization = self.recommend_quantization(model_name)
            print(f"推荐量化级别: {quantization}")
            
        # 检查磁盘空间
        required_space = config["quantized_versions"][quantization]["size_gb"]
        available_space = self.check_available_space()
        
        if available_space < required_space + 1:  # 预留1GB空间
            print(f"错误: 磁盘空间不足。需要 {required_space:.1f}GB，可用 {available_space:.1f}GB")
            return False
            
        # 创建模型目录
        model_dir = self.models_dir / model_name
        model_dir.mkdir(exist_ok=True)
        
        # 确定下载URL和文件名
        if quantization == "Q4_K_M":
            url_key = "gguf_q4"
        elif quantization == "Q5_K":
            url_key = "gguf_q5"
        else:
            print(f"警告: {quantization} 量化版本需要手动下载")
            self.show_manual_download_instructions(model_name, quantization)
            return False
            
        download_url = config["download_urls"][url_key]
        filename = download_url.split("/")[-1]
        filepath = model_dir / filename
        
        # 检查文件是否已存在
        if filepath.exists() and not force:
            if self.verify_file_integrity(filepath):
                print(f"模型已存在: {filepath}")
                return True
            else:
                print("文件损坏，重新下载...")
                filepath.unlink()
                
        # 下载模型
        print(f"开始下载 {config['name']} ({quantization})")
        print(f"大小: {required_space:.1f}GB")
        print(f"URL: {download_url}")
        
        success = self.download_file(download_url, filepath)
        
        if success and self.verify_file_integrity(filepath):
            print(f"✓ 下载完成: {filepath}")
            self.create_model_config(model_name, quantization, filepath)
            return True
        else:
            print("✗ 下载失败或文件损坏")
            return False
            
    def create_model_config(self, model_name: str, quantization: str, filepath: Path):
        """创建模型配置文件"""
        config = {
            "model_name": model_name,
            "quantization": quantization,
            "file_path": str(filepath),
            "language": self.model_configs[model_name]["language"],
            "size_gb": self.model_configs[model_name]["quantized_versions"][quantization]["size_gb"],
            "quality": self.model_configs[model_name]["quantized_versions"][quantization]["quality"]
        }
        
        config_file = filepath.parent / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
    def show_manual_download_instructions(self, model_name: str, quantization: str):
        """显示手动下载说明"""
        config = self.model_configs[model_name]
        
        print(f"\n=== {model_name} 手动下载说明 ===")
        print(f"模型: {config['name']}")
        print(f"量化级别: {quantization}")
        print(f"大小: {config['quantized_versions'][quantization]['size_gb']:.1f}GB")
        print(f"质量: {config['quantized_versions'][quantization]['quality']}")
        print("\n下载链接:")
        print(f"HuggingFace: {config['download_urls']['huggingface']}")
        print("\n下载后请将文件放置在:")
        print(f"{self.models_dir / model_name}/")
        print("\n支持的文件格式: .gguf, .bin, .safetensors")
        
    def list_models(self):
        """列出所有可用模型"""
        print("=== 可用模型列表 ===")
        for model_name, config in self.model_configs.items():
            print(f"\n{model_name}:")
            print(f"  名称: {config['name']}")
            print(f"  语言: {config['language']}")
            print(f"  原始大小: {config['size_gb']:.1f}GB")
            print("  量化版本:")
            for quant, info in config["quantized_versions"].items():
                print(f"    {quant}: {info['size_gb']:.1f}GB ({info['quality']}质量)")
                
    def check_installed_models(self):
        """检查已安装的模型"""
        print("=== 已安装模型 ===")
        found_models = False
        
        for model_name in self.model_configs.keys():
            model_dir = self.models_dir / model_name
            if model_dir.exists():
                config_file = model_dir / "config.json"
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    print(f"✓ {model_name}: {config['quantization']} ({config['size_gb']:.1f}GB)")
                    found_models = True
                else:
                    # 检查是否有模型文件
                    model_files = list(model_dir.glob("*.gguf")) + list(model_dir.glob("*.bin"))
                    if model_files:
                        print(f"? {model_name}: 发现文件但缺少配置")
                        found_models = True
                        
        if not found_models:
            print("未找到已安装的模型")
            
    def setup_recommended_models(self):
        """设置推荐的模型配置"""
        memory_gb = self.check_memory_limit()
        
        print(f"检测到系统内存: {memory_gb:.1f}GB")
        
        if memory_gb <= 4:
            print("推荐配置: 轻量化模式")
            models_to_download = [
                ("mistral-7b", "Q2_K"),
                ("qwen2.5-7b", "Q2_K")
            ]
        elif memory_gb <= 8:
            print("推荐配置: 平衡模式")
            models_to_download = [
                ("mistral-7b", "Q4_K_M"),
                ("qwen2.5-7b", "Q4_K_M")
            ]
        else:
            print("推荐配置: 高质量模式")
            models_to_download = [
                ("mistral-7b", "Q5_K"),
                ("qwen2.5-7b", "Q5_K")
            ]
            
        print("\n将下载以下模型:")
        total_size = 0
        for model_name, quantization in models_to_download:
            size = self.model_configs[model_name]["quantized_versions"][quantization]["size_gb"]
            total_size += size
            print(f"  {model_name} ({quantization}): {size:.1f}GB")
            
        print(f"总大小: {total_size:.1f}GB")
        
        # 检查磁盘空间
        available_space = self.check_available_space()
        if available_space < total_size + 2:
            print(f"错误: 磁盘空间不足。需要 {total_size + 2:.1f}GB，可用 {available_space:.1f}GB")
            return False
            
        # 确认下载
        response = input("\n是否继续下载? (y/N): ")
        if response.lower() != 'y':
            print("取消下载")
            return False
            
        # 开始下载
        success_count = 0
        for model_name, quantization in models_to_download:
            if self.download_model(model_name, quantization):
                success_count += 1
            else:
                print(f"模型 {model_name} 下载失败，显示手动下载说明")
                self.show_manual_download_instructions(model_name, quantization)
                
        print(f"\n下载完成: {success_count}/{len(models_to_download)} 个模型")
        return success_count == len(models_to_download)

def main():
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 模型下载工具")
    parser.add_argument("--models-dir", default="models", help="模型存储目录")
    parser.add_argument("--list", action="store_true", help="列出所有可用模型")
    parser.add_argument("--check", action="store_true", help="检查已安装的模型")
    parser.add_argument("--setup", action="store_true", help="自动设置推荐模型")
    parser.add_argument("--download", help="下载指定模型")
    parser.add_argument("--quantization", help="指定量化级别")
    parser.add_argument("--force", action="store_true", help="强制重新下载")
    
    args = parser.parse_args()
    
    downloader = ModelDownloader(args.models_dir)
    
    if args.list:
        downloader.list_models()
    elif args.check:
        downloader.check_installed_models()
    elif args.setup:
        downloader.setup_recommended_models()
    elif args.download:
        downloader.download_model(args.download, args.quantization, args.force)
    else:
        print("VisionAI-ClipsMaster 模型下载工具")
        print("使用 --help 查看所有选项")
        print("\n快速开始:")
        print("  python setup_models.py --setup    # 自动设置推荐模型")
        print("  python setup_models.py --list     # 列出可用模型")
        print("  python setup_models.py --check    # 检查已安装模型")

if __name__ == "__main__":
    main()
