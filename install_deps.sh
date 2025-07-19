#!/bin/bash

# 设置错误时退出
set -e

echo "开始安装 VisionAI-ClipsMaster 依赖..."

# 检查Python版本
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo "错误: 需要Python 3.8或更高版本"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate || source venv/Scripts/activate

# 升级pip
python -m pip install --upgrade pip

# 安装基本依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 克隆并编译llama.cpp
echo "设置llama.cpp..."
if [ ! -d "llama.cpp" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git
    cd llama.cpp
    make
    cd ..
fi

# 初始化模型
echo "初始化模型..."
python -m models.init_models

echo "安装完成!"
echo "请使用 'source venv/bin/activate' (Linux/Mac) 或 'venv\Scripts\activate' (Windows) 激活虚拟环境" 