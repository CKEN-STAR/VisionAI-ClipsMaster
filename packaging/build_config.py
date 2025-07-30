#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 打包配置
完全自包含整合包构建系统
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

class PackagingConfig:
    """打包配置管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.package_name = "VisionAI-ClipsMaster"
        self.version = "1.0.1"
        
        # 打包目录结构
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.package_dir = self.dist_dir / f"{self.package_name}-v{self.version}"
        
        # 主程序入口
        self.main_script = "simple_ui_fixed.py"
        self.executable_name = "VisionAI-ClipsMaster.exe"
        
        # 模型存储配置
        self.models_dir = self.package_dir / "models"
        self.internal_models_dir = self.models_dir / "downloaded"
        
    def get_pyinstaller_spec(self) -> Dict:
        """获取PyInstaller规格配置"""
        return {
            "name": self.package_name,
            "script": str(self.project_root / self.main_script),
            "icon": None,  # 可以添加图标路径
            "console": True,  # 保留控制台用于调试
            "onefile": False,  # 使用目录模式，便于模型管理
            "hidden_imports": self.get_hidden_imports(),
            "datas": self.get_data_files(),
            "excludes": self.get_excludes(),
            "runtime_hooks": [],
            "collect_all": ["transformers", "torch", "cv2"],
        }
    
    def get_hidden_imports(self) -> List[str]:
        """获取需要显式导入的隐藏模块"""
        return [
            # PyQt6相关
            "PyQt6.QtCore",
            "PyQt6.QtGui", 
            "PyQt6.QtWidgets",
            
            # AI框架核心
            "torch",
            "transformers",
            "transformers.models",
            "transformers.models.mistral",
            "transformers.models.qwen2",
            
            # 视频处理
            "cv2",
            "ffmpeg",
            
            # 项目核心模块
            "src.core.clip_generator",
            "src.core.model_switcher",
            "src.core.language_detector",
            "src.training.trainer",
            "src.training.en_trainer",
            "src.training.zh_trainer",
            
            # UI组件
            "ui.main_window",
            "ui.training_panel",
            "ui.progress_dashboard",
            
            # 工具模块
            "psutil",
            "requests",
            "numpy",
            "matplotlib",
        ]
    
    def get_data_files(self) -> List[tuple]:
        """获取需要打包的数据文件"""
        data_files = []
        
        # 配置文件
        configs_src = self.project_root / "configs"
        if configs_src.exists():
            data_files.append((str(configs_src), "configs"))
        
        # UI资源
        ui_assets = self.project_root / "ui" / "assets"
        if ui_assets.exists():
            data_files.append((str(ui_assets), "ui/assets"))
        
        # 模板文件
        templates = self.project_root / "templates"
        if templates.exists():
            data_files.append((str(templates), "templates"))
        
        # 示例数据
        test_data = self.project_root / "test_data"
        if test_data.exists():
            data_files.append((str(test_data), "test_data"))
        
        # FFmpeg工具（如果存在）
        ffmpeg_tools = self.project_root / "tools" / "ffmpeg"
        if ffmpeg_tools.exists():
            data_files.append((str(ffmpeg_tools), "tools/ffmpeg"))
        
        return data_files
    
    def get_excludes(self) -> List[str]:
        """获取需要排除的模块（减小包体积）"""
        return [
            # 开发工具
            "pytest",
            "pytest-qt",
            "jupyter",
            "notebook",
            
            # 不必要的AI框架
            "tensorflow",
            "jax",
            "flax",
            
            # 文档和测试
            "sphinx",
            "docutils",
            "test",
            "tests",
            
            # 其他大型库的非必要部分
            "matplotlib.tests",
            "numpy.tests",
            "scipy.tests",
        ]

class ModelDownloadManager:
    """模型下载管理器"""
    
    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.models_dir = package_dir / "models"
        self.download_dir = self.models_dir / "downloaded"
        
        # 模型配置
        self.model_configs = {
            "mistral-7b-en": {
                "repo_id": "mistralai/Mistral-7B-Instruct-v0.2",
                "quantization": "Q4_K_M",
                "size_gb": 4.1,
                "language": "en"
            },
            "qwen2.5-7b-zh": {
                "repo_id": "Qwen/Qwen2.5-7B-Instruct",
                "quantization": "Q4_K_M", 
                "size_gb": 4.3,
                "language": "zh"
            }
        }
    
    def create_model_downloader_script(self) -> str:
        """创建模型下载脚本"""
        script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 模型下载器
首次运行时自动下载所需的AI模型
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, Optional

class ModelDownloader:
    """模型下载器"""
    
    def __init__(self):
        # 获取程序根目录（整合包目录）
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            self.app_dir = Path(sys.executable).parent
        else:
            # 开发环境
            self.app_dir = Path(__file__).parent
        
        self.models_dir = self.app_dir / "models"
        self.download_dir = self.models_dir / "downloaded"
        self.config_file = self.models_dir / "download_status.json"
        
        # 确保目录存在
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def check_model_exists(self, model_name: str) -> bool:
        """检查模型是否已下载"""
        model_path = self.download_dir / model_name
        return model_path.exists() and any(model_path.iterdir())
    
    def download_model(self, model_name: str, repo_id: str) -> bool:
        """下载指定模型"""
        try:
            print(f"正在下载模型: {model_name}")
            print(f"来源: {repo_id}")
            
            # 这里实现实际的模型下载逻辑
            # 使用huggingface_hub或其他下载方法
            from huggingface_hub import snapshot_download
            
            model_path = self.download_dir / model_name
            snapshot_download(
                repo_id=repo_id,
                local_dir=str(model_path),
                local_dir_use_symlinks=False
            )
            
            print(f"模型下载完成: {model_name}")
            return True
            
        except Exception as e:
            print(f"模型下载失败: {e}")
            return False
    
    def ensure_models_available(self) -> bool:
        """确保所有必需模型可用"""
        models_config = {
            "mistral-7b-en": "mistralai/Mistral-7B-Instruct-v0.2",
            "qwen2.5-7b-zh": "Qwen/Qwen2.5-7B-Instruct"
        }
        
        all_available = True
        for model_name, repo_id in models_config.items():
            if not self.check_model_exists(model_name):
                print(f"检测到缺失模型: {model_name}")
                if not self.download_model(model_name, repo_id):
                    all_available = False
        
        return all_available

if __name__ == "__main__":
    downloader = ModelDownloader()
    success = downloader.ensure_models_available()
    sys.exit(0 if success else 1)
'''
        return script_content
    
    def create_startup_script(self) -> str:
        """创建启动脚本"""
        script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 启动脚本
检查模型完整性并启动主程序
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主启动函数"""
    # 获取程序根目录
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
    
    print("VisionAI-ClipsMaster 正在启动...")
    
    # 检查并下载模型
    model_downloader = app_dir / "model_downloader.py"
    if model_downloader.exists():
        print("检查模型完整性...")
        result = subprocess.run([sys.executable, str(model_downloader)], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("模型检查失败，请检查网络连接")
            input("按回车键退出...")
            return
    
    # 启动主程序
    main_script = app_dir / "simple_ui_fixed.py"
    if main_script.exists():
        print("启动主界面...")
        os.chdir(str(app_dir))
        subprocess.run([sys.executable, str(main_script)])
    else:
        print("错误：找不到主程序文件")
        input("按回车键退出...")

if __name__ == "__main__":
    main()
'''
        return script_content

def get_packaging_config() -> PackagingConfig:
    """获取打包配置实例"""
    project_root = Path(__file__).parent.parent
    return PackagingConfig(str(project_root))

if __name__ == "__main__":
    config = get_packaging_config()
    print(f"项目根目录: {config.project_root}")
    print(f"打包目录: {config.package_dir}")
    print(f"主程序: {config.main_script}")
