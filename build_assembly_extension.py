#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 汇编扩展构建脚本
用于编译平台特定的汇编优化库
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('build-asm')

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent

# 目标目录
LIB_DIR = ROOT_DIR / 'lib'
SRC_DIR = ROOT_DIR / 'src' / 'hardware'

# 编译器参数
CXX_COMPILER = None
CXX_FLAGS = []
LINK_FLAGS = []
OUTPUT_NAME = None

def detect_compiler():
    """检测并设置编译器和参数"""
    global CXX_COMPILER, CXX_FLAGS, LINK_FLAGS, OUTPUT_NAME
    
    system = platform.system()
    machine = platform.machine()
    
    if system == 'Windows':
        # 首先尝试MSVC
        try:
            msvc_output = subprocess.check_output('cl', shell=True, stderr=subprocess.STDOUT)
            CXX_COMPILER = 'cl'
            CXX_FLAGS = ['/O2', '/EHsc', '/DNDEBUG', '/arch:AVX2', '/DWIN32', '/D_WINDOWS', '/fp:fast']
            LINK_FLAGS = ['/DLL', '/MACHINE:X64' if machine == 'AMD64' else '/MACHINE:X86']
            OUTPUT_NAME = 'assembly_kernels.dll'
            logger.info("使用MSVC编译器")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # 尝试Intel oneAPI
        try:
            icx_output = subprocess.check_output('icx --version', shell=True, stderr=subprocess.STDOUT)
            CXX_COMPILER = 'icx'
            CXX_FLAGS = ['/O2', '/EHsc', '/DNDEBUG', '/QxHOST', '/DWIN32', '/D_WINDOWS']
            LINK_FLAGS = ['/DLL', '/MACHINE:X64' if machine == 'AMD64' else '/MACHINE:X86']
            OUTPUT_NAME = 'assembly_kernels.dll'
            logger.info("使用Intel oneAPI编译器")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # 尝试MinGW-w64
        try:
            mingw_output = subprocess.check_output('g++ --version', shell=True, stderr=subprocess.STDOUT)
            CXX_COMPILER = 'g++'
            
            arch_flags = '-mavx2 -mfma' if machine == 'AMD64' else '-msse4.2'
            
            CXX_FLAGS = ['-O3', '-std=c++14', '-fPIC', '-shared', '-DNDEBUG', 
                         '-Wall', '-Wextra', arch_flags]
            LINK_FLAGS = []
            OUTPUT_NAME = 'assembly_kernels.dll'
            logger.info("使用MinGW-w64编译器")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    elif system == 'Darwin':
        # macOS平台使用clang
        try:
            clang_output = subprocess.check_output('clang++ --version', shell=True, stderr=subprocess.STDOUT)
            CXX_COMPILER = 'clang++'
            
            # Apple Silicon (ARM64)
            if machine == 'arm64':
                CXX_FLAGS = ['-O3', '-std=c++14', '-fPIC', '-shared', '-DNDEBUG', 
                            '-Wall', '-Wextra', '-framework', 'Accelerate']
            else:
                # Intel x86_64
                CXX_FLAGS = ['-O3', '-std=c++14', '-fPIC', '-shared', '-DNDEBUG', 
                            '-Wall', '-Wextra', '-mavx2', '-mfma', '-framework', 'Accelerate']
                
            LINK_FLAGS = []
            OUTPUT_NAME = 'libassembly_kernels.dylib'
            logger.info("使用Clang编译器")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    elif system == 'Linux':
        # 尝试GCC
        try:
            gcc_output = subprocess.check_output('g++ --version', shell=True, stderr=subprocess.STDOUT)
            CXX_COMPILER = 'g++'
            
            # 为不同架构设置优化标志
            if 'arm' in machine.lower() or 'aarch' in machine.lower():
                # ARM架构
                arch_flags = '-march=native -mfpu=neon'
            else:
                # x86_64架构
                arch_flags = '-mavx2 -mfma'
                
            CXX_FLAGS = ['-O3', '-std=c++14', '-fPIC', '-shared', '-DNDEBUG', 
                         '-Wall', '-Wextra', arch_flags]
            LINK_FLAGS = []
            OUTPUT_NAME = 'libassembly_kernels.so'
            logger.info("使用GCC编译器")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
        # 尝试Clang
        try:
            clang_output = subprocess.check_output('clang++ --version', shell=True, stderr=subprocess.STDOUT)
            CXX_COMPILER = 'clang++'
            
            # 为不同架构设置优化标志
            if 'arm' in machine.lower() or 'aarch' in machine.lower():
                # ARM架构
                arch_flags = '-march=native -mfpu=neon'
            else:
                # x86_64架构
                arch_flags = '-mavx2 -mfma'
                
            CXX_FLAGS = ['-O3', '-std=c++14', '-fPIC', '-shared', '-DNDEBUG', 
                         '-Wall', '-Wextra', arch_flags]
            LINK_FLAGS = []
            OUTPUT_NAME = 'libassembly_kernels.so'
            logger.info("使用Clang编译器")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
    # 未找到支持的编译器
    logger.error(f"未在{system}平台找到支持的C++编译器")
    return False

def build_assembly_library():
    """构建汇编库"""
    # 检测编译器
    if not detect_compiler():
        logger.error("找不到合适的编译器，无法构建汇编扩展")
        return False
    
    # 创建lib目录
    os.makedirs(LIB_DIR, exist_ok=True)
    
    # 源文件
    src_file = SRC_DIR / 'assembly_kernels.cpp'
    include_dir = SRC_DIR
    
    # 输出文件
    output_file = LIB_DIR / OUTPUT_NAME
    
    # 构建命令
    if CXX_COMPILER == 'cl':
        # MSVC编译命令
        cmd = [
            CXX_COMPILER,
            str(src_file),
            f'/I{include_dir}',
            *CXX_FLAGS,
            f'/Fe:{output_file}',
            *LINK_FLAGS
        ]
    elif CXX_COMPILER == 'icx':
        # Intel oneAPI编译命令
        cmd = [
            CXX_COMPILER,
            str(src_file),
            f'/I{include_dir}',
            *CXX_FLAGS,
            f'/Fe:{output_file}',
            *LINK_FLAGS
        ]
    else:
        # GCC/Clang编译命令
        cmd = [
            CXX_COMPILER,
            str(src_file),
            f'-I{include_dir}',
            *CXX_FLAGS,
            '-o',
            str(output_file),
            *LINK_FLAGS
        ]
    
    # 执行编译
    try:
        logger.info(f"编译命令: {' '.join(cmd)}")
        subprocess.check_call(' '.join(cmd), shell=True)
        logger.info(f"汇编库已成功构建: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"编译失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始构建VisionAI-ClipsMaster平台特定汇编优化库")
    
    success = build_assembly_library()
    
    if success:
        logger.info("构建成功完成!")
    else:
        logger.error("构建失败!")
        sys.exit(1) 