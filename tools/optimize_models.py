#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VisionAI-ClipsMaster 模型优化脚本
移除大模型文件，实现按需下载
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List
import yaml

class ModelOptimizer:
    """模型优化器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(".")
        self.models_dir = self.project_root / "models"
        self.backup_dir = self.project_root / "models_backup"
        
    def analyze_current_models(self) -> Dict:
        """分析当前模型文件"""
        analysis = {
            "total_size": 0,
            "model_files": [],
            "directories": []
        }
        
        if not self.models_dir.exists():
            return analysis
        
        for item in self.models_dir.rglob("*"):
            if item.is_file():
                size = item.stat().st_size
                analysis["total_size"] += size
                
                if size > 100 * 1024 * 1024:  # >100MB
                    analysis["model_files"].append({
                        "path": str(item.relative_to(self.project_root)),
                        "size": size,
                        "size_formatted": self._format_size(size)
                    })
            elif item.is_dir():
                analysis["directories"].append(str(item.relative_to(self.project_root)))
        
        return analysis
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def backup_models(self) -> bool:
        """备份模型文件"""
        try:
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            if self.models_dir.exists():
                shutil.copytree(self.models_dir, self.backup_dir)
                print(f"✅ 模型文件已备份到: {self.backup_dir}")
                return True
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False
    
    def remove_large_models(self, size_threshold: int = 100 * 1024 * 1024) -> List[str]:
        """移除大模型文件"""
        removed_files = []
        
        if not self.models_dir.exists():
            return removed_files
        
        for item in self.models_dir.rglob("*"):
            if item.is_file() and item.stat().st_size > size_threshold:
                try:
                    # 保留文件信息
                    file_info = {
                        "original_path": str(item.relative_to(self.project_root)),
                        "size": item.stat().st_size,
                        "removed_at": str(item.stat().st_mtime)
                    }
                    
                    # 删除文件
                    item.unlink()
                    removed_files.append(file_info)
                    print(f"🗑️ 已移除: {item.relative_to(self.project_root)} "
                          f"({self._format_size(file_info['size'])})")
                    
                except Exception as e:
                    print(f"❌ 移除失败 {item}: {e}")
        
        return removed_files
    
    def create_download_configs(self, removed_files: List[Dict]) -> bool:
        """创建下载配置文件"""
        try:
            config_dir = self.project_root / "configs" / "downloads"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建模型下载配置
            download_config = {
                "version": "1.0",
                "removed_models": removed_files,
                "download_sources": {
                    "qwen": {
                        "modelscope": "https://modelscope.cn/models/qwen/Qwen2.5-7B-Instruct-GGUF",
                        "huggingface": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF"
                    },
                    "mistral": {
                        "modelscope": "https://modelscope.cn/models/mistralai/Mistral-7B-Instruct-v0.3-GGUF", 
                        "huggingface": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3-GGUF"
                    }
                },
                "quantization_options": {
                    "Q2_K": {"size_mb": 1800, "quality": 0.75},
                    "Q4_K_M": {"size_mb": 2600, "quality": 0.88},
                    "Q5_K": {"size_mb": 3800, "quality": 0.94}
                }
            }
            
            config_file = config_dir / "model_downloads.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(download_config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 下载配置已创建: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 创建配置失败: {e}")
            return False
    
    def update_model_config(self) -> bool:
        """更新模型配置文件"""
        try:
            config_file = self.project_root / "configs" / "model_config.yaml"
            
            if not config_file.exists():
                print(f"⚠️ 配置文件不存在: {config_file}")
                return False
            
            # 读取现有配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 更新配置
            if 'models' in config:
                for model_name, model_config in config['models'].items():
                    # 设置为按需下载
                    model_config['auto_download'] = True
                    model_config['preload'] = False
                    
                    # 更新路径为相对路径
                    if 'path' in model_config:
                        path = model_config['path']
                        if not path.startswith('models/'):
                            model_config['path'] = f"models/{path}"
            
            # 添加优化配置
            if 'optimization' not in config:
                config['optimization'] = {
                    "deployment_mode": "lightweight",
                    "auto_download": True,
                    "cache_management": True,
                    "max_cache_size": "8GB",
                    "cleanup_policy": "lru"
                }
            
            # 写回配置
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ 模型配置已更新: {config_file}")
            return True
            
        except Exception as e:
            print(f"❌ 更新配置失败: {e}")
            return False
    
    def create_placeholder_files(self) -> bool:
        """创建占位符文件"""
        try:
            placeholder_dirs = [
                "models/qwen/base",
                "models/qwen/quantized", 
                "models/mistral/base",
                "models/mistral/quantized"
            ]
            
            for dir_path in placeholder_dirs:
                full_path = self.project_root / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                
                # 创建README文件
                readme_file = full_path / "README.md"
                readme_content = f"""# {dir_path.split('/')[-2].title()} 模型目录

此目录用于存放 {dir_path.split('/')[-2]} 模型文件。

## 自动下载

模型文件将在首次使用时自动下载。您也可以手动触发下载：

```bash
python scripts/download_models.py --model {dir_path.split('/')[-2]}
```

## 量化选项

- Q2_K: 1.8GB (极致压缩)
- Q4_K_M: 2.6GB (推荐)  
- Q5_K: 3.8GB (高质量)

## 下载源

- 国内用户推荐：ModelScope
- 国外用户推荐：HuggingFace
"""
                
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
            
            print("✅ 占位符文件已创建")
            return True
            
        except Exception as e:
            print(f"❌ 创建占位符失败: {e}")
            return False
    
    def optimize(self, backup: bool = True) -> Dict:
        """执行完整优化"""
        print("🚀 开始模型优化...")
        
        # 分析当前状态
        analysis = self.analyze_current_models()
        print(f"📊 当前模型总大小: {self._format_size(analysis['total_size'])}")
        print(f"📄 大文件数量: {len(analysis['model_files'])}")
        
        results = {
            "success": False,
            "original_size": analysis['total_size'],
            "removed_files": [],
            "space_saved": 0
        }
        
        # 备份
        if backup and not self.backup_models():
            return results
        
        # 移除大文件
        removed_files = self.remove_large_models()
        results["removed_files"] = removed_files
        results["space_saved"] = sum(f["size"] for f in removed_files)
        
        # 创建配置
        if not self.create_download_configs(removed_files):
            return results
        
        # 更新配置
        if not self.update_model_config():
            return results
        
        # 创建占位符
        if not self.create_placeholder_files():
            return results
        
        results["success"] = True
        print(f"✅ 优化完成，节省空间: {self._format_size(results['space_saved'])}")
        
        return results

def main():
    """主函数"""
    optimizer = ModelOptimizer()
    
    print("🔍 VisionAI-ClipsMaster 模型优化工具")
    print("=" * 60)
    
    # 执行优化
    results = optimizer.optimize()
    
    if results["success"]:
        print("\n📊 优化结果:")
        print(f"  原始大小: {optimizer._format_size(results['original_size'])}")
        print(f"  节省空间: {optimizer._format_size(results['space_saved'])}")
        print(f"  移除文件: {len(results['removed_files'])} 个")
        
        print("\n🎯 下一步:")
        print("  1. 测试核心功能是否正常")
        print("  2. 运行智能下载器测试")
        print("  3. 验证UI启动和模型加载")
    else:
        print("❌ 优化失败，请检查错误信息")

if __name__ == "__main__":
    main()
