#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SIMD扩展CMake构建脚本 - VisionAI-ClipsMaster
使用CMake构建SIMD库
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
logger = logging.getLogger("build-simd-cmake")

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent

def check_cmake():
    """检查CMake是否可用"""
    try:
        result = subprocess.run(["cmake", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            cmake_version = result.stdout.decode('utf-8', errors='ignore').split('\n')[0]
            logger.info(f"CMake版本: {cmake_version}")
            return True
        else:
            logger.error("CMake不可用")
            return False
    except FileNotFoundError:
        logger.error("找不到CMake。请安装CMake后再试。")
        return False

def build_with_cmake(build_type="Release", clean=False):
    """
    使用CMake构建SIMD库
    
    Args:
        build_type: 构建类型 (Debug/Release)
        clean: 是否清理之前的构建
    
    Returns:
        bool: 构建是否成功
    """
    # 检查CMake是否可用
    if not check_cmake():
        return False
    
    # 构建目录
    build_dir = os.path.join(ROOT_DIR, "build")
    
    # 如果clean标志设置或构建目录不存在，创建或清理构建目录
    if clean and os.path.exists(build_dir):
        logger.info(f"清理构建目录: {build_dir}")
        shutil.rmtree(build_dir)
    
    # 创建构建目录
    os.makedirs(build_dir, exist_ok=True)
    
    # 进入构建目录
    os.chdir(build_dir)
    
    try:
        # 运行CMake配置
        logger.info("运行CMake配置...")
        cmake_cmd = ["cmake", f"-DCMAKE_BUILD_TYPE={build_type}", ".."]
        
        # 在Windows上，指定生成器
        if platform.system() == "Windows":
            # 检查是否有MSVC
            try:
                result = subprocess.run(["cl", "/?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    # 使用Visual Studio生成器
                    cmake_cmd.append("-G")
                    cmake_cmd.append("Visual Studio 16 2019")
            except FileNotFoundError:
                # 没有MSVC，使用MinGW
                cmake_cmd.append("-G")
                cmake_cmd.append("MinGW Makefiles")
        
        # 执行CMake配置
        result = subprocess.run(cmake_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"CMake配置失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
        
        # 运行CMake构建
        logger.info("运行CMake构建...")
        build_cmd = ["cmake", "--build", ".", "--config", build_type]
        result = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"CMake构建失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return False
        
        # 成功
        logger.info("CMake构建成功")
        
        # 返回项目根目录
        os.chdir(ROOT_DIR)
        
        # 检查库是否正确生成
        lib_dir = os.path.join(ROOT_DIR, "lib")
        os.makedirs(lib_dir, exist_ok=True)
        
        # 根据平台检查库文件
        if platform.system() == "Windows":
            lib_file = os.path.join(lib_dir, "simd_kernels.dll")
        elif platform.system() == "Darwin":  # macOS
            lib_file = os.path.join(lib_dir, "libsimd_kernels.dylib")
        else:  # Linux和其他Unix系统
            lib_file = os.path.join(lib_dir, "libsimd_kernels.so")
        
        if os.path.exists(lib_file):
            logger.info(f"SIMD库已生成: {lib_file}")
            return True
        else:
            logger.warning(f"找不到生成的库文件: {lib_file}")
            
            # 尝试从build目录复制
            if platform.system() == "Windows":
                build_lib = os.path.join(build_dir, "lib", build_type, "simd_kernels.dll")
            else:
                build_lib = os.path.join(build_dir, "lib", f"libsimd_kernels.{'dylib' if platform.system() == 'Darwin' else 'so'}")
            
            if os.path.exists(build_lib):
                shutil.copy2(build_lib, lib_file)
                logger.info(f"已从构建目录复制库文件: {lib_file}")
                return True
            else:
                logger.error(f"构建目录中也找不到库文件: {build_lib}")
                return False
        
    except Exception as e:
        logger.error(f"CMake构建过程出错: {str(e)}")
        # 返回项目根目录
        os.chdir(ROOT_DIR)
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="使用CMake构建SIMD库")
    parser.add_argument("--debug", action="store_true", help="构建Debug版本")
    parser.add_argument("--clean", action="store_true", help="清理之前的构建")
    args = parser.parse_args()
    
    build_type = "Debug" if args.debug else "Release"
    logger.info(f"构建类型: {build_type}")
    
    # 构建SIMD库
    result = build_with_cmake(build_type, args.clean)
    
    # 返回退出码
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main() 