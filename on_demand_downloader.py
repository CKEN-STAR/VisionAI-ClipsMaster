#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 按需下载器
实现核心组件的智能下载和缓存管理
"""

import os
import sys
import json
import hashlib
import requests
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timedelta
import threading
import time

class OnDemandDownloader:
    def __init__(self):
        self.cache_dir = Path("cache/downloads")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.cache_dir / "download_config.json"
        self.load_config()
        
        # 下载源配置 (支持多镜像)
        self.download_sources = {
            "ffmpeg": {
                "primary": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
                "mirrors": [
                    "https://mirrors.tuna.tsinghua.edu.cn/github-release/BtbN/FFmpeg-Builds/latest/ffmpeg-master-latest-win64-gpl.zip"
                ],
                "target_path": "tools/ffmpeg",
                "extract": True,
                "size_mb": 120,
                "description": "FFmpeg视频处理工具"
            },
            "pytorch": {
                "primary": "https://download.pytorch.org/whl/cpu/torch-2.0.0%2Bcpu-cp311-cp311-win_amd64.whl",
                "mirrors": [
                    "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/torch/torch-2.0.0%2Bcpu-cp311-cp311-win_amd64.whl"
                ],
                "target_path": "cache/wheels",
                "extract": False,
                "size_mb": 166,
                "description": "PyTorch深度学习框架"
            },
            "spacy_model": {
                "primary": "https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.5.0/zh_core_web_sm-3.5.0-py3-none-any.whl",
                "mirrors": [],
                "target_path": "cache/spacy_models",
                "extract": False,
                "size_mb": 46,
                "description": "中文NLP模型"
            }
        }
    
    def load_config(self):
        """加载下载配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "downloaded_components": {},
                "last_check": None,
                "cache_expiry_days": 30
            }
    
    def save_config(self):
        """保存下载配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_file_hash(self, filepath):
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
    
    def check_component_exists(self, component_name):
        """检查组件是否已存在且有效"""
        if component_name not in self.download_sources:
            return False
        
        config = self.download_sources[component_name]
        target_path = Path(config["target_path"])
        
        # 检查目标路径是否存在
        if not target_path.exists():
            return False
        
        # 检查是否在配置中记录
        if component_name in self.config["downloaded_components"]:
            component_info = self.config["downloaded_components"][component_name]
            
            # 检查是否过期
            download_date = datetime.fromisoformat(component_info["download_date"])
            expiry_date = download_date + timedelta(days=self.config["cache_expiry_days"])
            
            if datetime.now() > expiry_date:
                print(f"⏰ 组件 {component_name} 已过期，需要重新下载")
                return False
            
            # 检查文件完整性
            if config.get("extract", False):
                # 对于解压的文件，检查关键文件是否存在
                if component_name == "ffmpeg":
                    key_file = target_path / "bin" / "ffmpeg.exe"
                    return key_file.exists()
            else:
                # 对于单文件，检查哈希值
                expected_hash = component_info.get("file_hash")
                if expected_hash:
                    actual_hash = self.get_file_hash(target_path / component_info["filename"])
                    return actual_hash == expected_hash
        
        return True
    
    def download_with_progress(self, url, filepath, description=""):
        """带进度条的文件下载"""
        print(f"📥 下载 {description}: {url}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\r  进度: {progress:.1f}% ({downloaded_size/1024/1024:.1f}MB/{total_size/1024/1024:.1f}MB)", end="")
            
            print(f"\n  ✅ 下载完成: {filepath}")
            return True
            
        except Exception as e:
            print(f"\n  ❌ 下载失败: {e}")
            if filepath.exists():
                filepath.unlink()
            return False
    
    def extract_archive(self, archive_path, target_dir):
        """解压压缩文件"""
        print(f"📦 解压文件: {archive_path}")
        
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            else:
                print(f"❌ 不支持的压缩格式: {archive_path.suffix}")
                return False
            
            print(f"  ✅ 解压完成: {target_dir}")
            return True
            
        except Exception as e:
            print(f"  ❌ 解压失败: {e}")
            return False
    
    def download_component(self, component_name, force=False):
        """下载指定组件"""
        if component_name not in self.download_sources:
            print(f"❌ 未知组件: {component_name}")
            return False
        
        if not force and self.check_component_exists(component_name):
            print(f"✅ 组件 {component_name} 已存在，跳过下载")
            return True
        
        config = self.download_sources[component_name]
        target_path = Path(config["target_path"])
        
        print(f"🚀 开始下载组件: {component_name}")
        print(f"📝 描述: {config['description']}")
        print(f"📏 预计大小: {config['size_mb']}MB")
        
        # 尝试主要下载源
        urls_to_try = [config["primary"]] + config.get("mirrors", [])
        
        for i, url in enumerate(urls_to_try):
            print(f"\n🔗 尝试下载源 {i+1}/{len(urls_to_try)}")
            
            # 确定下载文件名
            filename = Path(urlparse(url).path).name
            if not filename:
                filename = f"{component_name}_download"
            
            download_path = self.cache_dir / filename
            
            # 下载文件
            if self.download_with_progress(url, download_path, config["description"]):
                # 处理下载的文件
                if config.get("extract", False):
                    # 需要解压
                    if self.extract_archive(download_path, target_path):
                        # 记录下载信息
                        self.config["downloaded_components"][component_name] = {
                            "download_date": datetime.now().isoformat(),
                            "source_url": url,
                            "filename": filename,
                            "extracted": True,
                            "target_path": str(target_path)
                        }
                        self.save_config()
                        
                        # 清理下载的压缩文件
                        download_path.unlink()
                        
                        print(f"🎉 组件 {component_name} 安装完成!")
                        return True
                else:
                    # 直接移动文件
                    target_path.mkdir(parents=True, exist_ok=True)
                    final_path = target_path / filename
                    
                    if final_path.exists():
                        final_path.unlink()
                    
                    download_path.rename(final_path)
                    
                    # 记录下载信息
                    file_hash = self.get_file_hash(final_path)
                    self.config["downloaded_components"][component_name] = {
                        "download_date": datetime.now().isoformat(),
                        "source_url": url,
                        "filename": filename,
                        "file_hash": file_hash,
                        "target_path": str(final_path)
                    }
                    self.save_config()
                    
                    print(f"🎉 组件 {component_name} 下载完成!")
                    return True
        
        print(f"❌ 所有下载源都失败，组件 {component_name} 下载失败")
        return False
    
    def ensure_component(self, component_name):
        """确保组件可用，不存在则自动下载"""
        if not self.check_component_exists(component_name):
            print(f"🔍 检测到缺失组件: {component_name}")
            return self.download_component(component_name)
        return True
    
    def list_components(self):
        """列出所有可用组件"""
        print("📋 可用组件列表:")
        for name, config in self.download_sources.items():
            status = "✅ 已安装" if self.check_component_exists(name) else "❌ 未安装"
            print(f"  {name:15} {status:10} {config['description']} ({config['size_mb']}MB)")
    
    def clean_cache(self):
        """清理过期缓存"""
        print("🧹 清理下载缓存...")
        
        if self.cache_dir.exists():
            for file_path in self.cache_dir.iterdir():
                if file_path.is_file() and file_path != self.config_file:
                    try:
                        file_path.unlink()
                        print(f"  🗑️  删除缓存文件: {file_path.name}")
                    except:
                        pass
        
        print("✅ 缓存清理完成")

def main():
    """命令行接口"""
    downloader = OnDemandDownloader()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python on_demand_downloader.py list                    # 列出组件")
        print("  python on_demand_downloader.py download <component>    # 下载组件")
        print("  python on_demand_downloader.py ensure <component>      # 确保组件存在")
        print("  python on_demand_downloader.py clean                   # 清理缓存")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        downloader.list_components()
    elif command == "download" and len(sys.argv) > 2:
        component = sys.argv[2]
        downloader.download_component(component, force=True)
    elif command == "ensure" and len(sys.argv) > 2:
        component = sys.argv[2]
        downloader.ensure_component(component)
    elif command == "clean":
        downloader.clean_cache()
    else:
        print("❌ 无效命令")

if __name__ == "__main__":
    main()
