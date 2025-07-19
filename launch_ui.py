#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI启动器

该脚本会设置必要的环境变量，解决依赖问题，然后启动UI
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    """主函数"""
    print("VisionAI-ClipsMaster UI启动器")
    print("设置环境变量...")
    
    # 设置环境变量，禁用CUDA，强制CPU模式
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ["TORCH_USE_CUDA_DSA"] = "0"
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "garbage_collection_threshold:0.6,max_split_size_mb:32"
    os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"
    os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"  # 防止在线下载模型
    
    # 项目路径
    project_dir = Path(__file__).parent.absolute()
    
    # Python解释器路径
    python_path = sys.executable
    
    # 尝试运行simple_ui.py
    print("尝试运行simple_ui.py...")
    try:
        process = subprocess.run(
            [python_path, str(project_dir / "simple_ui.py")],
            env=os.environ,
            check=False
        )
        
        if process.returncode == 0:
            print("UI已成功启动")
            return 0
        else:
            print(f"simple_ui.py启动失败，返回代码: {process.returncode}")
    except Exception as e:
        print(f"simple_ui.py启动失败: {e}")
        
    # 如果simple_ui.py失败，尝试运行app.py
    print("尝试运行app.py...")
    try:
        process = subprocess.run(
            [python_path, str(project_dir / "app.py")],
            env=os.environ,
            check=False
        )
        
        if process.returncode == 0:
            print("UI已成功启动")
            return 0
        else:
            print(f"app.py启动失败，返回代码: {process.returncode}")
    except Exception as e:
        print(f"app.py启动失败: {e}")
    
    print("无法启动任何UI界面")
    print("请尝试以下步骤:")
    print("1. 确保已安装所有依赖: pip install -r requirements.txt")
    print("2. 确保PyTorch CPU版本已正确安装: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
    print("3. 检查transformers库版本是否兼容: pip install transformers==4.26.1")
    print("4. 确保安装了PyQt6: pip install PyQt6")
    return 1

if __name__ == "__main__":
    sys.exit(main()) 