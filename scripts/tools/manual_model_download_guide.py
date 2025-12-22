#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 手动模型下载指南
提供完整的模型下载、安装和验证方案
"""

import os
import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelDownloadGuide:
    """模型下载指南"""
    
    def __init__(self):
        self.models_config = {
            "Qwen3-1.7B": {
                "name": "Qwen3-1.7B-Instruct",
                "description": "通义千问2.5-7B指令模型（中文优化）",
                "size": "14.4GB",
                "files": [
                    "model-00001-of-00008.safetensors",
                    "model-00002-of-00008.safetensors", 
                    "model-00003-of-00008.safetensors",
                    "model-00004-of-00008.safetensors",
                    "model-00005-of-00008.safetensors",
                    "model-00006-of-00008.safetensors",
                    "model-00007-of-00008.safetensors",
                    "model-00008-of-00008.safetensors",
                    "config.json",
                    "generation_config.json",
                    "tokenizer.json",
                    "tokenizer_config.json"
                ],
                "target_dir": "models/models/qwen/base",
                "download_sources": {
                    "modelscope": "https://modelscope.cn/models/Qwen/Qwen3-8B-Instruct",
                    "huggingface": "https://huggingface.co/Qwen/Qwen3-8B-Instruct",
                    "hf_mirror": "https://hf-mirror.com/Qwen/Qwen3-8B-Instruct"
                }
            },
            "mistral-7b": {
                "name": "Mistral-7B-Instruct-v0.1",
                "description": "Mistral-7B指令模型（英文优化）",
                "size": "13.5GB",
                "files": [
                    "pytorch_model-00001-of-00002.bin",
                    "pytorch_model-00002-of-00002.bin",
                    "config.json",
                    "generation_config.json",
                    "tokenizer.json",
                    "tokenizer_config.json"
                ],
                "target_dir": "models/mistral/base",
                "download_sources": {
                    "huggingface": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1",
                    "hf_mirror": "https://hf-mirror.com/mistralai/Mistral-7B-Instruct-v0.1",
                    "modelscope": "https://modelscope.cn/models/AI-ModelScope/Mistral-7B-Instruct-v0.1"
                }
            },
            "Qwen3-1.7B-gguf": {
                "name": "Qwen3-1.7B-Instruct-GGUF (量化版)",
                "description": "Qwen3-1.7B GGUF量化模型（推荐）",
                "size": "4.1GB",
                "files": [
                    "Qwen3-1.7B-instruct-q4_k_m.gguf"
                ],
                "target_dir": "models/models/qwen/quantized",
                "target_filename": "Q4_K_M.gguf",
                "download_sources": {
                    "modelscope": "https://modelscope.cn/models/Qwen/Qwen3-8B-Instruct-GGUF",
                    "huggingface": "https://huggingface.co/Qwen/Qwen3-8B-Instruct-GGUF"
                }
            },
            "mistral-7b-gguf": {
                "name": "Mistral-7B-Instruct-GGUF (量化版)",
                "description": "Mistral-7B GGUF量化模型（推荐）",
                "size": "4.1GB", 
                "files": [
                    "mistral-7b-instruct-v0.1.q4_k_m.gguf"
                ],
                "target_dir": "models/mistral/quantized",
                "target_filename": "Q4_K_M.gguf",
                "download_sources": {
                    "huggingface": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF",
                    "hf_mirror": "https://hf-mirror.com/TheBloke/Mistral-7B-Instruct-v0.1-GGUF"
                }
            }
        }
    
    def show_download_options(self):
        """显示下载选项"""
        print("🤖 VisionAI-ClipsMaster 模型下载指南")
        print("=" * 60)
        print()
        
        print("📋 可用模型选项:")
        for i, (key, config) in enumerate(self.models_config.items(), 1):
            print(f"  {i}. {config['name']}")
            print(f"     📝 {config['description']}")
            print(f"     📊 大小: {config['size']}")
            print(f"     📁 目标目录: {config['target_dir']}")
            print()
        
        print("💡 推荐下载策略:")
        print("  🥇 首选: GGUF量化版本 (选项3和4) - 体积小，性能好")
        print("  🥈 备选: 完整版本 (选项1和2) - 最佳质量，体积大")
        print()
        
        print("🌐 下载源优先级:")
        print("  1. ModelScope (国内) - 速度快，稳定")
        print("  2. HF-Mirror (国内镜像) - 备用选择")
        print("  3. HuggingFace (国外) - 官方源")
    
    def generate_download_commands(self, model_key: str):
        """生成下载命令"""
        if model_key not in self.models_config:
            print(f"❌ 未知模型: {model_key}")
            return
        
        config = self.models_config[model_key]
        print(f"📥 {config['name']} 下载方案")
        print("=" * 50)
        
        # 创建目标目录
        target_dir = Path(config['target_dir'])
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 目标目录已创建: {target_dir}")
        
        print("\n🔧 下载方法:")
        
        # 方法1: Git LFS (推荐)
        print("\n1️⃣ 使用Git LFS下载 (推荐):")
        for source_name, url in config['download_sources'].items():
            print(f"\n   📍 {source_name.upper()}:")
            print(f"   git lfs install")
            print(f"   git clone {url} temp_{model_key}")
            if 'target_filename' in config:
                original_file = config['files'][0]
                target_file = config['target_filename']
                print(f"   copy temp_{model_key}\\{original_file} {target_dir}\\{target_file}")
            else:
                print(f"   copy temp_{model_key}\\*.* {target_dir}\\")
            print(f"   rmdir /s temp_{model_key}")
        
        # 方法2: HuggingFace Hub
        print(f"\n2️⃣ 使用HuggingFace Hub:")
        print(f"   pip install huggingface_hub")
        print(f"   python -c \"")
        print(f"   from huggingface_hub import snapshot_download")
        if 'huggingface' in config['download_sources']:
            repo_id = config['download_sources']['huggingface'].split('/')[-2:]
            repo_id = '/'.join(repo_id)
            print(f"   snapshot_download(repo_id='{repo_id}', local_dir='{target_dir}')\"")
        
        # 方法3: 直接下载链接
        print(f"\n3️⃣ 直接下载 (适用于单文件):")
        if len(config['files']) == 1 and 'gguf' in model_key:
            for source_name, base_url in config['download_sources'].items():
                file_name = config['files'][0]
                if 'target_filename' in config:
                    target_name = config['target_filename']
                else:
                    target_name = file_name
                
                print(f"\n   📍 {source_name.upper()}:")
                if source_name == 'modelscope':
                    download_url = f"{base_url}/resolve/main/{file_name}"
                else:
                    download_url = f"{base_url}/resolve/main/{file_name}"
                
                print(f"   curl -L \"{download_url}\" -o \"{target_dir}\\{target_name}\"")
    
    def verify_installation(self, model_key: str):
        """验证模型安装"""
        if model_key not in self.models_config:
            return False
        
        config = self.models_config[model_key]
        target_dir = Path(config['target_dir'])
        
        print(f"🔍 验证 {config['name']} 安装...")
        
        missing_files = []
        total_size = 0
        
        for file_name in config['files']:
            if 'target_filename' in config and file_name == config['files'][0]:
                file_path = target_dir / config['target_filename']
            else:
                file_path = target_dir / file_name
            
            if file_path.exists():
                size = file_path.stat().st_size
                total_size += size
                size_mb = size / (1024 * 1024)
                print(f"  ✅ {file_path.name} ({size_mb:.1f}MB)")
            else:
                missing_files.append(file_name)
                print(f"  ❌ {file_name} (缺失)")
        
        if missing_files:
            print(f"⚠️ 缺失文件: {len(missing_files)} 个")
            return False
        else:
            total_gb = total_size / (1024 * 1024 * 1024)
            print(f"✅ 安装完成! 总大小: {total_gb:.1f}GB")
            return True
    
    def create_download_script(self, model_keys: List[str]):
        """创建下载脚本"""
        script_content = """@echo off
echo VisionAI-ClipsMaster 模型下载脚本
echo =====================================

"""
        
        for model_key in model_keys:
            if model_key in self.models_config:
                config = self.models_config[model_key]
                script_content += f"""
echo.
echo 下载 {config['name']}...
mkdir "{config['target_dir']}" 2>nul

"""
                # 添加Git LFS下载命令
                if 'modelscope' in config['download_sources']:
                    url = config['download_sources']['modelscope']
                    script_content += f"""git lfs install
git clone {url} temp_{model_key}
"""
                    if 'target_filename' in config:
                        original_file = config['files'][0]
                        target_file = config['target_filename']
                        script_content += f"""copy "temp_{model_key}\\{original_file}" "{config['target_dir']}\\{target_file}"
"""
                    else:
                        script_content += f"""xcopy "temp_{model_key}\\*.*" "{config['target_dir']}\\" /E /Y
"""
                    script_content += f"""rmdir /s /q temp_{model_key}
"""
        
        script_content += """
echo.
echo 下载完成! 请运行验证脚本检查安装结果。
pause
"""
        
        script_file = Path("download_models.bat")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 下载脚本已创建: {script_file}")
        print("💡 运行方法: 双击 download_models.bat")

def main():
    """主函数"""
    guide = ModelDownloadGuide()
    
    while True:
        guide.show_download_options()
        
        print("\n🎯 请选择操作:")
        print("  1-4: 查看具体模型下载方案")
        print("  5: 创建自动下载脚本")
        print("  6: 验证已安装模型")
        print("  0: 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice in ["1", "2", "3", "4"]:
            model_keys = list(guide.models_config.keys())
            model_key = model_keys[int(choice) - 1]
            guide.generate_download_commands(model_key)
            input("\n按回车继续...")
        elif choice == "5":
            print("\n选择要下载的模型 (多选用逗号分隔，如: 3,4):")
            selections = input("输入选择: ").strip().split(',')
            model_keys = []
            for sel in selections:
                try:
                    idx = int(sel.strip()) - 1
                    if 0 <= idx < len(guide.models_config):
                        model_keys.append(list(guide.models_config.keys())[idx])
                except:
                    continue
            
            if model_keys:
                guide.create_download_script(model_keys)
            else:
                print("❌ 无效选择")
            input("\n按回车继续...")
        elif choice == "6":
            print("\n🔍 验证模型安装状态:")
            for model_key in guide.models_config:
                guide.verify_installation(model_key)
            input("\n按回车继续...")
        else:
            print("❌ 无效选择，请重新输入")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
