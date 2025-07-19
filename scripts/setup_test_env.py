#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置VisionAI-ClipsMaster测试环境
支持低配置设备(4GB内存)验证
"""

import os
import sys
import argparse
import subprocess
import platform
from pathlib import Path


def create_venv(venv_name="test_venv"):
    """创建测试虚拟环境"""
    print(f"正在创建测试虚拟环境: {venv_name}")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 创建虚拟环境
    try:
        subprocess.run([sys.executable, "-m", "venv", venv_name], check=True)
        print(f"✓ 虚拟环境创建成功: {venv_name}")
    except subprocess.CalledProcessError:
        print("错误: 虚拟环境创建失败")
        sys.exit(1)
    
    return venv_name


def install_requirements(venv_name):
    """安装测试所需依赖"""
    print("正在安装测试依赖...")
    
    # 确定pip路径和测试需求文件
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_name, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_name, "bin", "pip")
    
    # 生成测试专用requirements文件
    create_test_requirements()
    
    # 安装依赖
    try:
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", "tests/requirements-test.txt"], check=True)
        print("✓ 测试依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"错误: 依赖安装失败: {e}")
        sys.exit(1)


def create_test_requirements():
    """创建测试专用requirements文件"""
    test_req_path = "tests/requirements-test.txt"
    os.makedirs("tests", exist_ok=True)
    
    # 测试环境需要的依赖清单
    requirements = [
        "pytest==7.4.0",
        "pytest-cov==4.1.0",
        "pytest-mock==3.11.1",
        "pytest-timeout==2.1.0",
        "pytest-xdist==3.3.1",
        "memory-profiler==0.61.0",
        "numpy==1.24.3",
        "pandas==2.0.3",
        "transformers==4.36.2",
        "tokenizers==0.15.0",
        "sentencepiece==0.1.99",
        "opencv-python-headless==4.8.0.76",  # 无GUI依赖版本，降低内存占用
        "ffmpeg-python==0.2.0",
        "torch==2.1.0+cpu",    # CPU版本避免CUDA依赖
        "fasttext==0.9.2",     # 语言检测
        "jieba==0.42.1",       # 中文分词
        "pysrt==1.1.2",        # SRT处理
    ]
    
    with open(test_req_path, "w", encoding="utf-8") as f:
        f.write("# VisionAI-ClipsMaster 测试环境依赖\n")
        f.write("# 针对低配置设备(4GB内存)优化\n\n")
        for req in requirements:
            f.write(f"{req}\n")
    
    print(f"✓ 测试依赖文件创建成功: {test_req_path}")


def setup_model_configs():
    """准备模型配置文件"""
    print("正在准备模型配置...")
    
    # 确保模型配置目录存在
    os.makedirs("configs/models/available_models", exist_ok=True)
    
    # 设置当前激活的中文模型
    with open("configs/models/active_model.yaml", "w", encoding="utf-8") as f:
        f.write("# 当前激活的模型配置\n")
        f.write("active_model: qwen2.5-7b-zh\n")
        f.write("language: zh\n")
    
    print("✓ 模型配置准备完成")


def verify_environment(venv_name):
    """验证测试环境是否正确设置"""
    print("正在验证测试环境...")
    
    # 确定Python解释器路径
    if platform.system() == "Windows":
        python_path = os.path.join(venv_name, "Scripts", "python")
    else:
        python_path = os.path.join(venv_name, "bin", "python")
    
    # 验证Python版本和虚拟环境路径
    try:
        result = subprocess.run([python_path, "-c", 
                               "import sys; print(f'Python {sys.version} / 虚拟环境: {sys.prefix}')"], 
                               capture_output=True, text=True, check=True)
        print(result.stdout.strip())
        
        # 验证关键依赖
        check_command = ("import torch; import transformers; import cv2; import jieba; "
                        f"print(f'PyTorch: {torch.__version__} / Transformers: {transformers.__version__}')")
        
        result = subprocess.run([python_path, "-c", check_command], 
                               capture_output=True, text=True, check=True)
        print(result.stdout.strip())
        print("✓ 测试环境验证通过")
    except subprocess.CalledProcessError as e:
        print(f"错误: 环境验证失败: {e}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)


def create_test_script():
    """创建内存监控测试脚本"""
    test_script_path = "tests/memory_test.py"
    
    with open(test_script_path, "w", encoding="utf-8") as f:
        f.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
VisionAI-ClipsMaster 内存使用测试
验证在4GB内存环境下的性能
\"\"\"

import os
import gc
import time
import psutil
import argparse
from memory_profiler import profile

class MemoryTest:
    \"\"\"内存使用测试类\"\"\"
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self):
        \"\"\"获取当前内存使用量(MB)\"\"\"
        return self.process.memory_info().rss / (1024 * 1024)
    
    @profile
    def simulate_model_loading(self):
        \"\"\"模拟模型加载\"\"\"
        print("模拟Qwen2.5-7B量化模型加载...")
        
        # 模拟模型内存占用(约3.8GB)
        large_list = [0] * (950 * 1024 * 1024)  # 约3.8GB
        print(f"当前内存占用: {self.get_memory_usage():.2f} MB")
        
        time.sleep(2)  # 模拟推理
        
        # 释放内存
        del large_list
        gc.collect()
        print(f"释放后内存占用: {self.get_memory_usage():.2f} MB")
        
        return True
    
    @profile
    def test_memory_guard(self):
        \"\"\"测试内存守卫功能\"\"\"
        print("测试内存守卫功能...")
        
        # 模拟逐步增加内存占用
        for i in range(1, 5):
            temp_list = [0] * (512 * 1024 * 1024)  # 约512MB
            print(f"阶段{i}内存占用: {self.get_memory_usage():.2f} MB")
            if self.get_memory_usage() > 3800:  # 接近4GB警戒线
                print("触发内存守卫，开始释放...")
                del temp_list
                gc.collect()
                break
        
        print(f"最终内存占用: {self.get_memory_usage():.2f} MB")
    
    def run_all_tests(self):
        \"\"\"运行所有内存测试\"\"\"
        print("===== VisionAI-ClipsMaster 内存测试 =====")
        print(f"初始内存占用: {self.get_memory_usage():.2f} MB")
        
        self.simulate_model_loading()
        self.test_memory_guard()
        
        print("===== 内存测试完成 =====")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 内存测试")
    args = parser.parse_args()
    
    tester = MemoryTest()
    tester.run_all_tests()
""")
    
    print(f"✓ 内存测试脚本创建成功: {test_script_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="设置VisionAI-ClipsMaster测试环境")
    parser.add_argument("--name", default="test_venv", help="虚拟环境名称")
    args = parser.parse_args()
    
    print("===== VisionAI-ClipsMaster 测试环境设置 =====")
    
    # 创建测试环境目录结构
    for directory in ["tests", "configs", "configs/models", "models"]:
        os.makedirs(directory, exist_ok=True)
    
    # 执行设置步骤
    venv_name = create_venv(args.name)
    install_requirements(venv_name)
    setup_model_configs()
    create_test_script()
    verify_environment(venv_name)
    
    print("\n✓ 测试环境设置完成!")
    print(f"可通过以下命令激活测试环境:")
    if platform.system() == "Windows":
        print(f"   {venv_name}\\Scripts\\activate")
    else:
        print(f"   source {venv_name}/bin/activate")
    print(f"运行内存测试: python tests/memory_test.py")


if __name__ == "__main__":
    main() 