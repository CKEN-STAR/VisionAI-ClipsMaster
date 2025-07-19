#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIMD扩展编译脚本 - VisionAI-ClipsMaster
编译SIMD库文件为共享库/DLL
"""

import os
import sys
import platform
import subprocess
import argparse
import shutil
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("build-simd")

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent

# 源代码文件
SIMD_KERNELS_CPP = os.path.join(ROOT_DIR, "src", "hardware", "simd_kernels.cpp")

# 输出目录
LIB_DIR = os.path.join(ROOT_DIR, "lib")
os.makedirs(LIB_DIR, exist_ok=True)

# 根据平台确定输出文件名
if platform.system() == "Windows":
    OUTPUT_FILE = os.path.join(LIB_DIR, "simd_kernels.dll")
elif platform.system() == "Darwin":  # macOS
    OUTPUT_FILE = os.path.join(LIB_DIR, "libsimd_kernels.dylib")
else:  # Linux和其他类Unix系统
    OUTPUT_FILE = os.path.join(LIB_DIR, "libsimd_kernels.so")

def detect_compiler():
    """检测可用的C++编译器"""
    if platform.system() == "Windows":
        # 检查MSVC
        try:
            result = subprocess.run(["cl", "/?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return "msvc"
        except FileNotFoundError:
            pass
        
        # 检查MinGW
        try:
            result = subprocess.run(["g++", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return "g++"
        except FileNotFoundError:
            pass
    else:
        # 检查clang++
        try:
            result = subprocess.run(["clang++", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return "clang++"
        except FileNotFoundError:
            pass
        
        # 检查g++
        try:
            result = subprocess.run(["g++", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                return "g++"
        except FileNotFoundError:
            pass
    
    return None

def build_with_msvc():
    """使用MSVC编译"""
    logger.info("使用MSVC编译SIMD扩展...")
    
    # MSVC编译命令
    cmd = [
        "cl",
        "/O2",                  # 优化级别
        "/arch:AVX2",           # 启用AVX2指令集
        "/EHsc",                # 标准C++异常处理
        "/LD",                  # 创建DLL
        f"/Fe:{OUTPUT_FILE}",   # 输出文件名
        SIMD_KERNELS_CPP        # 源文件
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info(f"编译成功: {OUTPUT_FILE}")
            
            # 清理中间文件
            for ext in ['.obj', '.lib', '.exp']:
                obj_file = SIMD_KERNELS_CPP.replace('.cpp', ext)
                if os.path.exists(obj_file):
                    os.remove(obj_file)
            
            return True
        else:
            logger.error(f"编译失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
    except Exception as e:
        logger.error(f"编译过程出错: {str(e)}")
        return False

def build_with_gcc(compiler="g++"):
    """使用GCC/Clang编译"""
    logger.info(f"使用{compiler}编译SIMD扩展...")
    
    # 检测平台
    if platform.system() == "Windows":
        output_flag = f"-o {OUTPUT_FILE}"
        shared_flag = "-shared"
    elif platform.system() == "Darwin":  # macOS
        output_flag = f"-o {OUTPUT_FILE}"
        shared_flag = "-dynamiclib"
    else:  # Linux
        output_flag = f"-o {OUTPUT_FILE}"
        shared_flag = "-shared -fPIC"
    
    # 根据架构确定指令集优化标志
    if platform.machine().startswith(('arm', 'aarch')):
        # ARM架构
        simd_flags = "-march=native"
        if platform.machine() == "aarch64":
            simd_flags += " -O3"
    else:
        # x86架构
        simd_flags = "-march=native -O3"
    
    # 完整编译命令
    cmd_str = f"{compiler} {simd_flags} {shared_flag} {SIMD_KERNELS_CPP} {output_flag}"
    
    try:
        logger.info(f"运行命令: {cmd_str}")
        result = subprocess.run(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            logger.info(f"编译成功: {OUTPUT_FILE}")
            return True
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            logger.error(f"编译失败: {stderr}")
            return False
    except Exception as e:
        logger.error(f"编译过程出错: {str(e)}")
        return False

def build_simd_extension(force=False, compiler=None):
    """
    构建SIMD扩展
    
    Args:
        force: 是否强制重新构建
        compiler: 指定编译器，默认自动检测
    
    Returns:
        bool: 构建是否成功
    """
    # 检查源文件是否存在
    if not os.path.exists(SIMD_KERNELS_CPP):
        logger.error(f"源文件不存在: {SIMD_KERNELS_CPP}")
        return False
    
    # 如果输出文件已存在且不强制重新构建，则跳过
    if os.path.exists(OUTPUT_FILE) and not force:
        logger.info(f"输出文件已存在: {OUTPUT_FILE}")
        logger.info("使用--force参数强制重新构建")
        return True
    
    # 如果没有指定编译器，自动检测
    if compiler is None:
        compiler = detect_compiler()
    
    # 根据编译器选择构建方法
    if compiler == "msvc":
        return build_with_msvc()
    elif compiler in ["g++", "clang++"]:
        return build_with_gcc(compiler)
    else:
        logger.error("找不到支持的C++编译器。请安装MSVC、GCC或Clang。")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="构建SIMD扩展")
    parser.add_argument("--force", action="store_true", help="强制重新构建")
    parser.add_argument("--compiler", choices=["msvc", "g++", "clang++"], help="指定编译器")
    args = parser.parse_args()
    
    result = build_simd_extension(args.force, args.compiler)
    sys.exit(0 if result else 1) 