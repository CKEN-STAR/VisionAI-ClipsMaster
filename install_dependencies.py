#!/usr/bin/env python3
"""
VisionAI-ClipsMaster 依赖安装脚本
自动检测和安装缺失的依赖包，确保程序能在低配设备上正常运行
"""

import os
import sys
import subprocess
import importlib
import platform
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[ERROR] Python版本过低: {version.major}.{version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    print(f"[OK] Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_package(package_name, import_name=None, pip_name=None):
    """安装Python包"""
    if import_name is None:
        import_name = package_name
    if pip_name is None:
        pip_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"[OK] {package_name} 已安装")
        return True
    except ImportError:
        print(f"[INSTALL] 正在安装 {package_name}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", pip_name, "--quiet"
            ])
            print(f"[OK] {package_name} 安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] {package_name} 安装失败: {e}")
            return False

def install_pytorch_cpu():
    """安装CPU版本的PyTorch"""
    try:
        import torch
        print(f"[OK] PyTorch 已安装: {torch.__version__}")
        return True
    except ImportError:
        print("[INSTALL] 正在安装CPU版本的PyTorch...")
        try:
            # 安装CPU版本的PyTorch
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "torch", "torchvision", "torchaudio", 
                "--index-url", "https://download.pytorch.org/whl/cpu",
                "--quiet"
            ])
            print("[OK] PyTorch CPU版本安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] PyTorch安装失败: {e}")
            return False

def check_ffmpeg():
    """检查FFmpeg是否可用"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print("[OK] FFmpeg 已安装")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("[WARN] FFmpeg 未安装或不在PATH中")
    print("请手动安装FFmpeg:")
    if platform.system() == "Windows":
        print("1. 下载: https://ffmpeg.org/download.html#build-windows")
        print("2. 解压到任意目录")
        print("3. 将bin目录添加到系统PATH")
    else:
        print("Ubuntu/Debian: sudo apt install ffmpeg")
        print("CentOS/RHEL: sudo yum install ffmpeg")
        print("macOS: brew install ffmpeg")
    return False

def install_core_dependencies():
    """安装核心依赖"""
    dependencies = [
        ("PyQt6", "PyQt6", "PyQt6"),
        ("numpy", "numpy", "numpy"),
        ("opencv-python", "cv2", "opencv-python"),
        ("Pillow", "PIL", "Pillow"),
        ("requests", "requests", "requests"),
        ("psutil", "psutil", "psutil"),
        ("pydantic", "pydantic", "pydantic"),
        ("transformers", "transformers", "transformers"),
        ("librosa", "librosa", "librosa"),
        ("matplotlib", "matplotlib", "matplotlib"),
        ("plotly", "plotly", "plotly"),
        ("jieba", "jieba", "jieba"),
        ("spacy", "spacy", "spacy"),
    ]
    
    success_count = 0
    for package_name, import_name, pip_name in dependencies:
        if install_package(package_name, import_name, pip_name):
            success_count += 1
    
    print(f"\n[INFO] 核心依赖安装完成: {success_count}/{len(dependencies)}")
    return success_count == len(dependencies)

def install_optional_dependencies():
    """安装可选依赖"""
    optional_deps = [
        ("accelerate", "accelerate", "accelerate"),
        ("bitsandbytes", "bitsandbytes", "bitsandbytes"),
        ("optimum", "optimum", "optimum"),
        ("onnx", "onnx", "onnx"),
        ("onnxruntime", "onnxruntime", "onnxruntime"),
    ]
    
    print("\n[INFO] 安装可选依赖（用于性能优化）...")
    for package_name, import_name, pip_name in optional_deps:
        install_package(package_name, import_name, pip_name)

def create_environment_config():
    """创建环境配置文件"""
    config_content = """# VisionAI-ClipsMaster 环境配置
# 强制使用CPU模式（适配无GPU设备）
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TORCH_USE_CUDA_DSA'] = '0'
os.environ['OMP_NUM_THREADS'] = '4'
os.environ['MKL_NUM_THREADS'] = '4'

# 内存优化设置
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

print("[OK] 环境配置已加载（CPU模式）")
"""
    
    config_path = Path("environment_setup.py")
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"[OK] 环境配置文件已创建: {config_path}")

def main():
    """主函数"""
    print("=" * 60)
    print("VisionAI-ClipsMaster 依赖安装脚本")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 升级pip
    print("\n[INFO] 升级pip...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"
        ])
        print("[OK] pip已升级")
    except subprocess.CalledProcessError:
        print("[WARN] pip升级失败，继续安装...")
    
    # 安装PyTorch CPU版本
    print("\n[INFO] 检查PyTorch...")
    install_pytorch_cpu()
    
    # 安装核心依赖
    print("\n[INFO] 安装核心依赖...")
    if not install_core_dependencies():
        print("[WARN] 部分核心依赖安装失败，程序可能无法正常运行")
    
    # 安装可选依赖
    install_optional_dependencies()
    
    # 检查FFmpeg
    print("\n[INFO] 检查FFmpeg...")
    check_ffmpeg()
    
    # 创建环境配置
    print("\n[INFO] 创建环境配置...")
    create_environment_config()
    
    print("\n" + "=" * 60)
    print("依赖安装完成！")
    print("=" * 60)
    print("下一步:")
    print("1. 如果FFmpeg未安装，请手动安装")
    print("2. 运行: python simple_ui_fixed.py")
    print("3. 如果遇到问题，请查看日志文件")

if __name__ == "__main__":
    main()
