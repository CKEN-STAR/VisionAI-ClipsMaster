#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指令流水线优化构建脚本 - VisionAI-ClipsMaster
用于构建C/汇编指令流水线优化库
"""

import os
import sys
import logging
import platform
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('build-pipeline')

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
HARDWARE_DIR = PROJECT_ROOT / "src" / "hardware"
BUILD_DIR = PROJECT_ROOT / "build" / "pipeline_opt"

def check_cmake():
    """检查CMake是否已安装"""
    try:
        result = subprocess.run(["cmake", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True,
                               check=True)
        logger.info(f"找到CMake: {result.stdout.splitlines()[0]}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("未找到CMake，请确保它已安装并添加到PATH")
        return False

def check_compiler():
    """检查C/C++编译器是否已安装"""
    compilers = []
    
    if platform.system() == "Windows":
        compilers = ["cl", "gcc", "clang"]
    else:
        compilers = ["gcc", "clang", "icc"]
    
    for compiler in compilers:
        try:
            if compiler == "cl":
                # MSVC编译器需要特殊处理
                result = subprocess.run(["cl"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True)
            else:
                result = subprocess.run([compiler, "--version"], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True)
                
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else "未知版本"
                logger.info(f"找到C编译器: {compiler} - {first_line}")
                return compiler
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    logger.error("未找到支持的C/C++编译器")
    return None

def build_library():
    """构建指令流水线优化库"""
    logger.info("=== 开始构建指令流水线优化库 ===")
    
    # 检查CMake和编译器
    if not check_cmake():
        return False
    
    if not check_compiler():
        return False
    
    # 创建构建目录
    os.makedirs(BUILD_DIR, exist_ok=True)
    
    # 配置CMake项目
    logger.info(f"配置CMake项目...")
    try:
        subprocess.run(["cmake", "-S", str(HARDWARE_DIR), "-B", str(BUILD_DIR)],
                     check=True,
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE,
                     text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"CMake配置失败: {e}")
        logger.error(f"输出: {e.stdout}")
        logger.error(f"错误: {e.stderr}")
        return False
    
    # 构建项目
    logger.info(f"构建项目...")
    try:
        subprocess.run(["cmake", "--build", str(BUILD_DIR), "--config", "Release"],
                     check=True,
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE,
                     text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"构建失败: {e}")
        logger.error(f"输出: {e.stdout}")
        logger.error(f"错误: {e.stderr}")
        return False
    
    logger.info("构建成功!")
    
    # 复制库文件到硬件目录
    lib_name = ""
    if platform.system() == "Windows":
        lib_name = "pipeline_opt.dll"
    elif platform.system() == "Darwin":
        lib_name = "libpipeline_opt.dylib"
    else:
        lib_name = "libpipeline_opt.so"
    
    source_lib = BUILD_DIR / "Release" / lib_name
    if not source_lib.exists():
        source_lib = BUILD_DIR / lib_name
    
    if source_lib.exists():
        import shutil
        dest_lib = HARDWARE_DIR / lib_name
        shutil.copy2(source_lib, dest_lib)
        logger.info(f"已复制优化库到: {dest_lib}")
    else:
        logger.warning(f"未找到构建的库文件: {source_lib}")
    
    return True

def run_tests():
    """运行优化库测试"""
    logger.info("=== 运行优化库测试 ===")
    
    try:
        result = subprocess.run(["python", "-m", "src.hardware.test_pipeline_opt"], 
                              cwd=PROJECT_ROOT,
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        
        logger.info("测试输出:")
        for line in result.stdout.splitlines():
            logger.info(line)
        
        if result.returncode == 0:
            logger.info("所有测试通过!")
            return True
        else:
            logger.error("测试失败!")
            return False
    except Exception as e:
        logger.error(f"运行测试时出错: {e}")
        return False

def main():
    """主函数"""
    logger.info("=== 指令流水线优化库构建工具 ===")
    
    # 构建库
    if build_library():
        # 运行测试
        run_tests()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 