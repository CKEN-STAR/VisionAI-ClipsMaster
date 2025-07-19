#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 汇编扩展CMake构建脚本
使用CMake构建平台特定的汇编优化库，提供更好的跨平台支持
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
logger = logging.getLogger('build-asm-cmake')

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent
BUILD_DIR = ROOT_DIR / 'build' / 'assembly'
LIB_DIR = ROOT_DIR / 'lib'

def detect_cmake():
    """检测CMake是否可用"""
    try:
        output = subprocess.check_output('cmake --version', shell=True, stderr=subprocess.STDOUT)
        logger.info(f"找到CMake: {output.decode().splitlines()[0]}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("未找到CMake，请安装CMake以构建汇编库")
        return False

def create_cmakelists():
    """创建CMakeLists.txt文件"""
    cmake_file_path = ROOT_DIR / 'assembly_CMakeLists.txt'
    
    cmake_content = """# 汇编优化库的CMakeLists.txt
cmake_minimum_required(VERSION 3.10)
project(assembly_kernels)

# 设置C++标准
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 设置输出目录
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 设置优化选项
if(MSVC)
    # MSVC编译器选项
    add_compile_options(/O2 /DNDEBUG /EHsc /fp:fast)
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        add_compile_options(/arch:AVX2)
    endif()
else()
    # GCC/Clang编译器选项
    add_compile_options(-O3 -DNDEBUG -Wall -Wextra)
    
    # 检测系统架构
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "arm|aarch64")
        # ARM架构
        if(CMAKE_SYSTEM_PROCESSOR MATCHES "aarch64")
            add_compile_options(-march=native)
        else()
            add_compile_options(-march=native -mfpu=neon)
        endif()
    else()
        # x86_64/x86架构
        if(CMAKE_SIZEOF_VOID_P EQUAL 8)
            # 64位
            add_compile_options(-mavx2 -mfma)
        else()
            # 32位
            add_compile_options(-msse4.2)
        endif()
    endif()
endif()

# 检测macOS平台并链接Accelerate框架
if(APPLE)
    find_library(ACCELERATE_LIBRARY Accelerate)
    if(ACCELERATE_LIBRARY)
        message(STATUS "Found Accelerate framework")
        list(APPEND PLATFORM_LIBS ${ACCELERATE_LIBRARY})
    endif()
endif()

# 检查pthreads
find_package(Threads)
if(Threads_FOUND)
    list(APPEND PLATFORM_LIBS ${CMAKE_THREAD_LIBS_INIT})
endif()

# 包含目录
include_directories(${CMAKE_SOURCE_DIR}/src/hardware)

# 添加库目标
add_library(assembly_kernels SHARED src/hardware/assembly_kernels.cpp)

# 链接平台相关库
if(PLATFORM_LIBS)
    target_link_libraries(assembly_kernels ${PLATFORM_LIBS})
endif()

# 设置输出名称
set_target_properties(assembly_kernels PROPERTIES 
    PREFIX "lib" 
    OUTPUT_NAME "assembly_kernels"
)

# 重命名Windows上的输出
if(WIN32)
    set_target_properties(assembly_kernels PROPERTIES 
        PREFIX "" 
        SUFFIX ".dll"
    )
endif()

# 安装规则
install(TARGETS assembly_kernels
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION lib)
"""

    with open(cmake_file_path, 'w') as f:
        f.write(cmake_content)
    
    logger.info(f"已创建CMakeLists.txt: {cmake_file_path}")
    return cmake_file_path

def build_with_cmake():
    """使用CMake构建汇编库"""
    # 确保目录存在
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(LIB_DIR, exist_ok=True)
    
    # 创建CMakeLists.txt
    cmake_file = create_cmakelists()
    
    # 配置CMake
    try:
        cmd = f'cmake -S {ROOT_DIR} -B {BUILD_DIR} -DCMAKE_BUILD_TYPE=Release -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX={ROOT_DIR} -DCMAKE_POSITION_INDEPENDENT_CODE=ON'
        
        # Windows上使用特定的生成器
        if platform.system() == 'Windows':
            cmd = f'cmake -S {ROOT_DIR} -B {BUILD_DIR} -DCMAKE_BUILD_TYPE=Release -G "MinGW Makefiles" -DCMAKE_INSTALL_PREFIX={ROOT_DIR} -DCMAKE_POSITION_INDEPENDENT_CODE=ON'
            
            # 如果有Visual Studio，尝试使用它
            try:
                vs_check = subprocess.check_output('cl', shell=True, stderr=subprocess.STDOUT)
                cmd = f'cmake -S {ROOT_DIR} -B {BUILD_DIR} -DCMAKE_BUILD_TYPE=Release -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX={ROOT_DIR}'
            except:
                pass
        
        # 指定CMakeLists.txt文件
        cmd += f' -DCMAKE_PROJECT_assembly_kernels_INCLUDE={cmake_file}'
        
        logger.info(f"运行CMake配置: {cmd}")
        subprocess.check_call(cmd, shell=True, cwd=ROOT_DIR)
        
        # 构建
        build_cmd = f'cmake --build {BUILD_DIR} --config Release --target assembly_kernels'
        logger.info(f"运行CMake构建: {build_cmd}")
        subprocess.check_call(build_cmd, shell=True, cwd=ROOT_DIR)
        
        # 安装
        install_cmd = f'cmake --install {BUILD_DIR} --config Release'
        logger.info(f"运行CMake安装: {install_cmd}")
        subprocess.check_call(install_cmd, shell=True, cwd=ROOT_DIR)
        
        # 拷贝库文件到lib目录
        if platform.system() == 'Windows':
            src_lib = BUILD_DIR / 'bin' / 'Release' / 'assembly_kernels.dll'
            if not os.path.exists(src_lib):
                src_lib = BUILD_DIR / 'assembly_kernels.dll'
            if not os.path.exists(src_lib):
                src_lib = BUILD_DIR / 'Release' / 'assembly_kernels.dll'
            
            dst_lib = LIB_DIR / 'assembly_kernels.dll'
        elif platform.system() == 'Darwin':
            src_lib = BUILD_DIR / 'lib' / 'libassembly_kernels.dylib'
            dst_lib = LIB_DIR / 'libassembly_kernels.dylib'
        else:
            src_lib = BUILD_DIR / 'lib' / 'libassembly_kernels.so'
            dst_lib = LIB_DIR / 'libassembly_kernels.so'
        
        # 确保源文件存在
        if os.path.exists(src_lib):
            shutil.copy2(src_lib, dst_lib)
            logger.info(f"已拷贝库文件: {src_lib} -> {dst_lib}")
        else:
            # 尝试查找库文件
            logger.warning(f"找不到预期的库文件: {src_lib}")
            for root, dirs, files in os.walk(BUILD_DIR):
                for file in files:
                    if file.endswith('.dll') or file.endswith('.so') or file.endswith('.dylib'):
                        found_lib = os.path.join(root, file)
                        dst_name = os.path.basename(found_lib)
                        dst_lib = LIB_DIR / dst_name
                        shutil.copy2(found_lib, dst_lib)
                        logger.info(f"找到并拷贝了库文件: {found_lib} -> {dst_lib}")
                        return True
            
            logger.error("找不到编译后的库文件")
            return False
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"CMake构建失败: {e}")
        return False
    except Exception as e:
        logger.error(f"构建过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始使用CMake构建VisionAI-ClipsMaster平台特定汇编优化库")
    
    if not detect_cmake():
        logger.error("未找到CMake, 无法继续构建")
        sys.exit(1)
    
    success = build_with_cmake()
    
    if success:
        logger.info("CMake构建成功完成!")
    else:
        logger.error("CMake构建失败!")
        sys.exit(1) 