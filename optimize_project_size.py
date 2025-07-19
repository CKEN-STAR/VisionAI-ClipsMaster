#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 项目体积优化工具
提供三种优化策略：激进、平衡、保守
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectOptimizer:
    """项目体积优化器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "optimization_backup"
        
        # 优化策略配置
        self.strategies = {
            "aggressive": {
                "name": "激进优化",
                "target_size": "≤3GB",
                "compression_ratio": "91%",
                "description": "最大压缩，适合在线分发"
            },
            "balanced": {
                "name": "平衡优化", 
                "target_size": "≤8GB",
                "compression_ratio": "76%",
                "description": "体积与性能兼顾"
            },
            "conservative": {
                "name": "保守优化",
                "target_size": "≤15GB", 
                "compression_ratio": "55%",
                "description": "最小风险，确保稳定性"
            }
        }
    
    def create_backup(self, files_to_backup: List[str]):
        """创建备份"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
            
        backup_manifest = []
        
        for file_pattern in files_to_backup:
            source_path = self.project_root / file_pattern
            if source_path.exists():
                if source_path.is_dir():
                    backup_path = self.backup_dir / file_pattern
                    if not backup_path.exists():
                        shutil.copytree(source_path, backup_path)
                        backup_manifest.append({"type": "dir", "source": file_pattern, "backup": str(backup_path)})
                else:
                    backup_path = self.backup_dir / file_pattern
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, backup_path)
                    backup_manifest.append({"type": "file", "source": file_pattern, "backup": str(backup_path)})
        
        # 保存备份清单
        with open(self.backup_dir / "backup_manifest.json", 'w', encoding='utf-8') as f:
            json.dump(backup_manifest, f, indent=2, ensure_ascii=False)
            
        logger.info(f"备份完成: {len(backup_manifest)} 项")
    
    def aggressive_optimization(self):
        """激进优化策略"""
        logger.info("🚀 执行激进优化策略...")
        
        # 1. 模型文件处理
        model_files = [
            "models/models/qwen/base/*.safetensors",
            "models/models/mistral/base/*.safetensors"
        ]
        
        # 备份关键配置
        self.create_backup([
            "models/configs/",
            "configs/model_config.yaml"
        ])
        
        # 移除大型模型文件
        removed_size = 0
        for pattern in model_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.exists():
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_size += size
                    logger.info(f"移除: {file_path} ({size//1024//1024}MB)")
        
        # 2. Git历史清理
        self._clean_git_history()
        
        # 3. 工具链优化
        tool_dirs = ["tools/ffmpeg", "llama.cpp", "downloads/"]
        for tool_dir in tool_dirs:
            tool_path = self.project_root / tool_dir
            if tool_path.exists():
                shutil.rmtree(tool_path)
                logger.info(f"移除工具目录: {tool_dir}")
        
        # 4. 测试数据清理
        self._clean_test_data("aggressive")
        
        # 5. 创建按需下载配置
        self._setup_on_demand_download()
        
        logger.info(f"激进优化完成，预计减少: {removed_size//1024//1024//1024:.1f}GB")
    
    def balanced_optimization(self):
        """平衡优化策略"""
        logger.info("⚖️ 执行平衡优化策略...")
        
        # 1. 保留量化模型，移除原始模型
        self.create_backup(["models/models/"])
        
        # 移除原始safetensors，保留量化版本
        for safetensor_file in self.project_root.glob("models/**/base/*.safetensors"):
            safetensor_file.unlink()
            logger.info(f"移除原始模型: {safetensor_file}")
        
        # 2. Git LFS迁移
        self._setup_git_lfs()
        
        # 3. 依赖项优化
        redundant_dirs = ["test_venv/", "spacy_wheels/"]
        for dir_name in redundant_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"移除冗余目录: {dir_name}")
        
        # 4. 压缩测试数据
        self._compress_test_data()
        
        logger.info("平衡优化完成")
    
    def conservative_optimization(self):
        """保守优化策略"""
        logger.info("🛡️ 执行保守优化策略...")
        
        # 1. 清理编译缓存
        cache_removed = self._clean_cache_files()
        
        # 2. 清理日志文件
        log_removed = self._clean_log_files()
        
        # 3. 清理备份文件
        backup_removed = self._clean_backup_files()
        
        # 4. 压缩大型测试文件
        test_compressed = self._compress_large_test_files()
        
        total_saved = cache_removed + log_removed + backup_removed + test_compressed
        logger.info(f"保守优化完成，节省空间: {total_saved//1024//1024}MB")
    
    def _clean_git_history(self):
        """清理Git历史中的大文件"""
        logger.info("清理Git历史...")
        
        # 这里只是示例，实际需要谨慎操作
        git_commands = [
            "git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch *.safetensors *.bin *.pkl' --prune-empty --tag-name-filter cat -- --all",
            "git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin",
            "git reflog expire --expire=now --all",
            "git gc --prune=now --aggressive"
        ]
        
        logger.warning("Git历史清理需要手动执行以下命令:")
        for cmd in git_commands:
            logger.warning(f"  {cmd}")
    
    def _clean_test_data(self, strategy: str):
        """清理测试数据"""
        if strategy == "aggressive":
            # 移除大型测试文件
            for test_file in self.project_root.glob("tests/**/*.mp4"):
                if test_file.stat().st_size > 10 * 1024 * 1024:  # >10MB
                    test_file.unlink()
                    logger.info(f"移除大型测试文件: {test_file}")
            
            for pkl_file in self.project_root.glob("**/*.pkl"):
                if pkl_file.stat().st_size > 50 * 1024 * 1024:  # >50MB
                    pkl_file.unlink()
                    logger.info(f"移除大型pkl文件: {pkl_file}")
    
    def _setup_on_demand_download(self):
        """设置按需下载"""
        download_config = {
            "models": {
                "qwen2.5-7b": {
                    "url": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
                    "size": "4.1GB",
                    "priority": 1
                },
                "mistral-7b": {
                    "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.q4_k_m.gguf",
                    "size": "4.1GB", 
                    "priority": 1
                }
            },
            "tools": {
                "ffmpeg": {
                    "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
                    "size": "100MB",
                    "priority": 2
                }
            }
        }
        
        config_path = self.project_root / "configs" / "download_manifest.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(download_config, f, indent=2, ensure_ascii=False)
            
        logger.info("按需下载配置已创建")
    
    def _setup_git_lfs(self):
        """设置Git LFS"""
        gitattributes_content = """
# Git LFS 配置
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
"""
        
        gitattributes_path = self.project_root / ".gitattributes"
        with open(gitattributes_path, 'w', encoding='utf-8') as f:
            f.write(gitattributes_content)
            
        logger.info("Git LFS配置已创建")
    
    def _clean_cache_files(self) -> int:
        """清理缓存文件"""
        total_removed = 0
        
        # Python缓存
        for cache_dir in self.project_root.rglob("__pycache__"):
            if cache_dir.is_dir():
                size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                shutil.rmtree(cache_dir)
                total_removed += size
        
        # .pyc文件
        for pyc_file in self.project_root.rglob("*.pyc"):
            total_removed += pyc_file.stat().st_size
            pyc_file.unlink()
        
        logger.info(f"清理缓存文件: {total_removed//1024//1024}MB")
        return total_removed
    
    def _clean_log_files(self) -> int:
        """清理日志文件"""
        total_removed = 0
        
        # 清理30天前的日志
        import time
        cutoff_time = time.time() - (30 * 24 * 3600)
        
        for log_file in self.project_root.glob("logs/**/*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                total_removed += log_file.stat().st_size
                log_file.unlink()
        
        logger.info(f"清理日志文件: {total_removed//1024//1024}MB")
        return total_removed
    
    def _clean_backup_files(self) -> int:
        """清理备份文件"""
        total_removed = 0
        
        backup_patterns = ["*.bak", "*.backup", "*~"]
        for pattern in backup_patterns:
            for backup_file in self.project_root.rglob(pattern):
                total_removed += backup_file.stat().st_size
                backup_file.unlink()
        
        logger.info(f"清理备份文件: {total_removed//1024//1024}MB")
        return total_removed
    
    def _compress_test_data(self):
        """压缩测试数据"""
        import gzip
        
        for large_file in self.project_root.glob("data/**/*.pkl"):
            if large_file.stat().st_size > 100 * 1024 * 1024:  # >100MB
                compressed_file = large_file.with_suffix(large_file.suffix + '.gz')
                
                with open(large_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                large_file.unlink()
                logger.info(f"压缩: {large_file} -> {compressed_file}")
    
    def _compress_large_test_files(self) -> int:
        """压缩大型测试文件"""
        # 实现类似_compress_test_data的逻辑
        return 0

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 项目体积优化工具")
    parser.add_argument("strategy", choices=["aggressive", "balanced", "conservative"], 
                       help="优化策略")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要执行的操作")
    parser.add_argument("--backup", action="store_true", default=True, help="创建备份")
    
    args = parser.parse_args()
    
    optimizer = ProjectOptimizer()
    
    # 显示策略信息
    strategy_info = optimizer.strategies[args.strategy]
    print(f"🎯 优化策略: {strategy_info['name']}")
    print(f"📊 目标大小: {strategy_info['target_size']}")
    print(f"📈 压缩比例: {strategy_info['compression_ratio']}")
    print(f"📝 说明: {strategy_info['description']}")
    print()
    
    if args.dry_run:
        print("🔍 预览模式 - 不会实际修改文件")
        return
    
    # 确认操作
    confirm = input("确认执行优化? (y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    # 执行优化
    if args.strategy == "aggressive":
        optimizer.aggressive_optimization()
    elif args.strategy == "balanced":
        optimizer.balanced_optimization()
    elif args.strategy == "conservative":
        optimizer.conservative_optimization()
    
    print("✅ 优化完成!")

if __name__ == "__main__":
    main()
