#!/bin/bash
# VisionAI-ClipsMaster测试依赖安装脚本
echo "======================================="
echo " VisionAI-ClipsMaster 测试依赖安装工具"
echo "======================================="
echo

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[错误] 未激活虚拟环境，请先激活测试环境"
    echo "运行 source activate_test_env.sh 激活测试环境"
    exit 1
fi

# 检查是否是测试环境
if [[ "$VIRTUAL_ENV" != *".test_venv"* ]]; then
    echo "[警告] 当前激活的不是测试环境，而是:"
    echo "$VIRTUAL_ENV"
    echo "建议在测试环境中安装依赖，以避免影响开发环境"
    
    echo -n "是否继续安装? (Y/N): "
    read choice
    if [[ "$choice" != "Y" && "$choice" != "y" ]]; then
        exit 0
    fi
fi

# 更新pip
echo "[步骤1/3] 更新pip..."
python -m pip install --upgrade pip

# 安装wheel和setuptools
echo "[步骤2/3] 安装基础包..."
python -m pip install wheel setuptools

# 安装测试依赖
echo "[步骤3/3] 安装测试依赖..."
python -m pip install -r requirements_test.txt

echo
echo "[成功] 测试依赖安装完成!"
echo "=======================================" 