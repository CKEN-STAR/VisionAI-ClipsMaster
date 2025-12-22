#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 模型路径管理器
确保所有AI模型存储在整合包内部，实现完全自包含
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, List
import tempfile

class ModelPathManager:
    """模型路径管理器 - 确保完全自包含"""
    
    def __init__(self):
        # 获取应用根目录
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件环境
            self.app_root = Path(sys.executable).parent
        else:
            # 开发环境
            self.app_root = Path(__file__).parent.parent
        
        # 内部模型存储路径
        self.models_root = self.app_root / "models"
        self.downloaded_models = self.models_root / "downloaded"
        self.cache_dir = self.models_root / "cache"
        self.temp_dir = self.models_root / "temp"
        
        # 配置文件
        self.config_file = self.models_root / "path_config.json"
        
        # 确保目录存在
        self._ensure_directories()
        
        # 重定向环境变量
        self._setup_environment_variables()
    
    def _ensure_directories(self):
        """确保所有必要目录存在"""
        directories = [
            self.models_root,
            self.downloaded_models,
            self.cache_dir,
            self.temp_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_environment_variables(self):
        """设置环境变量，重定向模型缓存到内部目录"""
        # HuggingFace缓存目录
        os.environ['HF_HOME'] = str(self.cache_dir)
        os.environ['HUGGINGFACE_HUB_CACHE'] = str(self.cache_dir / "hub")
        os.environ['TRANSFORMERS_CACHE'] = str(self.cache_dir / "transformers")
        
        # PyTorch缓存目录
        os.environ['TORCH_HOME'] = str(self.cache_dir / "torch")
        
        # 临时目录
        os.environ['TMPDIR'] = str(self.temp_dir)
        os.environ['TEMP'] = str(self.temp_dir)
        os.environ['TMP'] = str(self.temp_dir)
        
        # 禁用外部缓存
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = "1"
        os.environ['HF_HUB_DISABLE_EXPERIMENTAL_WARNING'] = "1"
    
    def get_model_path(self, model_name: str) -> Path:
        """获取模型的内部存储路径"""
        return self.downloaded_models / model_name
    
    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否已下载到内部目录"""
        model_path = self.get_model_path(model_name)
        return model_path.exists() and any(model_path.iterdir())
    
    def get_available_models(self) -> List[str]:
        """获取所有已下载的模型列表"""
        if not self.downloaded_models.exists():
            return []
        
        return [d.name for d in self.downloaded_models.iterdir() if d.is_dir()]
    
    def download_model_to_internal(self, model_name: str, repo_id: str, 
                                 progress_callback=None) -> bool:
        """下载模型到内部目录"""
        try:
            from huggingface_hub import snapshot_download
            
            model_path = self.get_model_path(model_name)
            
            if progress_callback:
                progress_callback(f"开始下载模型: {model_name}")
            
            # 下载到内部目录
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(model_path),
                local_dir_use_symlinks=False,  # 不使用符号链接
                cache_dir=str(self.cache_dir / "hub"),
                resume_download=True
            )
            
            if progress_callback:
                progress_callback(f"模型下载完成: {model_name}")
            
            # 更新配置
            self._update_model_config(model_name, repo_id, str(model_path))
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"模型下载失败: {model_name} - {e}")
            return False
    
    def _update_model_config(self, model_name: str, repo_id: str, local_path: str):
        """更新模型配置文件"""
        config = self._load_config()
        
        config["models"][model_name] = {
            "repo_id": repo_id,
            "local_path": local_path,
            "download_time": self._get_current_time(),
            "status": "available"
        }
        
        self._save_config(config)
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认配置
        return {
            "app_root": str(self.app_root),
            "models_root": str(self.models_root),
            "cache_dir": str(self.cache_dir),
            "models": {}
        }
    
    def _save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def cleanup_external_caches(self):
        """清理可能存在的外部缓存"""
        external_cache_dirs = [
            Path.home() / ".cache" / "huggingface",
            Path.home() / ".cache" / "torch",
            Path.home() / "AppData" / "Local" / "huggingface",  # Windows
        ]
        
        for cache_dir in external_cache_dirs:
            if cache_dir.exists():
                try:
                    # 不直接删除，而是移动到内部缓存
                    if cache_dir.name == "huggingface":
                        target_dir = self.cache_dir / "imported_hf_cache"
                        if not target_dir.exists():
                            shutil.move(str(cache_dir), str(target_dir))
                except Exception as e:
                    print(f"清理外部缓存失败: {e}")
    
    def get_total_size(self) -> int:
        """获取模型目录总大小（字节）"""
        total_size = 0
        for path in self.models_root.rglob('*'):
            if path.is_file():
                total_size += path.stat().st_size
        return total_size
    
    def get_size_info(self) -> Dict:
        """获取详细的大小信息"""
        info = {
            "total_size_mb": self.get_total_size() / 1024 / 1024,
            "models": {}
        }
        
        for model_name in self.get_available_models():
            model_path = self.get_model_path(model_name)
            model_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
            info["models"][model_name] = {
                "size_mb": model_size / 1024 / 1024,
                "path": str(model_path)
            }
        
        return info
    
    def verify_self_contained(self) -> Dict:
        """验证是否完全自包含"""
        verification = {
            "is_self_contained": True,
            "issues": [],
            "external_dependencies": []
        }
        
        # 检查环境变量是否正确设置
        required_env_vars = [
            "HF_HOME", "HUGGINGFACE_HUB_CACHE", 
            "TRANSFORMERS_CACHE", "TORCH_HOME"
        ]
        
        for var in required_env_vars:
            if var not in os.environ:
                verification["issues"].append(f"环境变量 {var} 未设置")
                verification["is_self_contained"] = False
            else:
                env_path = Path(os.environ[var])
                if not str(env_path).startswith(str(self.app_root)):
                    verification["external_dependencies"].append(f"{var}: {env_path}")
                    verification["is_self_contained"] = False
        
        # 检查模型文件是否都在内部目录
        config = self._load_config()
        for model_name, model_info in config.get("models", {}).items():
            model_path = Path(model_info["local_path"])
            if not str(model_path).startswith(str(self.app_root)):
                verification["external_dependencies"].append(f"模型 {model_name}: {model_path}")
                verification["is_self_contained"] = False
        
        return verification

class ModelDownloadUI:
    """模型下载用户界面"""
    
    def __init__(self, path_manager: ModelPathManager):
        self.path_manager = path_manager
        self.models_to_download = {
            "mistral-7b-en": "mistralai/Mistral-7B-Instruct-v0.2",
            "qwen3-1.7b-zh": "Qwen/Qwen3-1.7B-Instruct"
        }
    
    def check_and_download_models(self) -> bool:
        """检查并下载缺失的模型"""
        missing_models = []
        
        for model_name in self.models_to_download:
            if not self.path_manager.is_model_available(model_name):
                missing_models.append(model_name)
        
        if not missing_models:
            print("✅ 所有模型已就绪")
            return True
        
        print(f"📥 需要下载 {len(missing_models)} 个模型")
        
        for model_name in missing_models:
            repo_id = self.models_to_download[model_name]
            print(f"正在下载: {model_name}")
            
            success = self.path_manager.download_model_to_internal(
                model_name, repo_id, self._progress_callback
            )
            
            if not success:
                print(f"❌ 模型下载失败: {model_name}")
                return False
        
        print("✅ 所有模型下载完成")
        return True
    
    def _progress_callback(self, message: str):
        """进度回调函数"""
        print(f"   {message}")

# 全局实例
_path_manager = None

def get_model_path_manager() -> ModelPathManager:
    """获取全局模型路径管理器实例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = ModelPathManager()
    return _path_manager

def ensure_models_available() -> bool:
    """确保所有必需模型可用"""
    path_manager = get_model_path_manager()
    download_ui = ModelDownloadUI(path_manager)
    return download_ui.check_and_download_models()

if __name__ == "__main__":
    # 测试模型路径管理器
    manager = get_model_path_manager()
    
    print("模型路径管理器信息:")
    print(f"应用根目录: {manager.app_root}")
    print(f"模型目录: {manager.models_root}")
    print(f"下载目录: {manager.downloaded_models}")
    
    # 验证自包含性
    verification = manager.verify_self_contained()
    print(f"\n自包含验证: {'✅ 通过' if verification['is_self_contained'] else '❌ 失败'}")
    
    if verification["issues"]:
        print("问题:")
        for issue in verification["issues"]:
            print(f"  - {issue}")
    
    if verification["external_dependencies"]:
        print("外部依赖:")
        for dep in verification["external_dependencies"]:
            print(f"  - {dep}")
    
    # 显示大小信息
    size_info = manager.get_size_info()
    print(f"\n总大小: {size_info['total_size_mb']:.1f} MB")
    
    for model_name, model_info in size_info["models"].items():
        print(f"  {model_name}: {model_info['size_mb']:.1f} MB")
