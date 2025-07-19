#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一优化构建脚本 - VisionAI-ClipsMaster
构建SIMD和汇编优化库

该脚本提供了一个统一的入口来构建项目所需的所有优化库：
1. SIMD向量化优化
2. 平台特定汇编优化
3. 内存对齐优化已集成到Python代码中，无需编译
"""

import os
import sys
import logging
import platform
import argparse
import subprocess
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("build-optimizations")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="构建VisionAI-ClipsMaster优化库")
    parser.add_argument("--simd", action="store_true", help="仅构建SIMD优化库")
    parser.add_argument("--assembly", action="store_true", help="仅构建汇编优化库")
    parser.add_argument("--all", action="store_true", help="构建所有优化库")
    parser.add_argument("--debug", action="store_true", help="构建调试版本")
    parser.add_argument("--clean", action="store_true", help="清理构建文件")
    parser.add_argument("--test", action="store_true", help="构建后运行测试")
    
    return parser.parse_args()

def run_build_script(script_name, debug=False, clean=False, extra_args=None):
    """运行构建脚本
    
    Args:
        script_name: 脚本名称
        debug: 是否构建调试版本
        clean: 是否清理构建文件
        extra_args: 额外参数
    
    Returns:
        bool: 构建是否成功
    """
    cmd = [sys.executable, script_name]
    
    if clean:
        cmd.append("--clean")
    if debug:
        cmd.append("--debug")
    if extra_args:
        cmd.extend(extra_args)
        
    logger.info(f"运行构建脚本: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"构建失败: {str(e)}")
        return False

def build_simd(debug=False, clean=False):
    """构建SIMD优化库
    
    Args:
        debug: 是否构建调试版本
        clean: 是否清理构建文件
    
    Returns:
        bool: 构建是否成功
    """
    logger.info("开始构建SIMD优化库...")
    return run_build_script("build_simd_extension.py", debug, clean)

def build_assembly(debug=False, clean=False):
    """构建汇编优化库
    
    Args:
        debug: 是否构建调试版本
        clean: 是否清理构建文件
    
    Returns:
        bool: 构建是否成功
    """
    logger.info("开始构建汇编优化库...")
    return run_build_script("build_assembly_cmake.py", debug, clean)

def run_tests():
    """运行优化测试
    
    Returns:
        bool: 测试是否通过
    """
    logger.info("运行优化测试...")
    
    test_files = [
        "src/hardware/test_simd.py",
        "src/hardware/test_assembly.py",
        "src/hardware/test_memory_alignment.py",
        "src/hardware/test_integration.py"
    ]
    
    all_passed = True
    
    for test_file in test_files:
        logger.info(f"运行测试: {test_file}")
        try:
            result = subprocess.run([sys.executable, test_file], check=False)
            if result.returncode != 0:
                logger.error(f"测试失败: {test_file}")
                all_passed = False
            else:
                logger.info(f"测试通过: {test_file}")
        except Exception as e:
            logger.error(f"测试异常: {test_file} - {str(e)}")
            all_passed = False
            
    return all_passed

def check_memory_alignment():
    """检查内存对齐模块是否可用
    
    Returns:
        bool: 内存对齐模块是否可用
    """
    try:
        from src.hardware.memory_aligner import get_alignment_for_simd
        alignment = get_alignment_for_simd()
        logger.info(f"内存对齐模块可用，当前平台最佳对齐值: {alignment}字节")
        return True
    except ImportError:
        logger.warning("内存对齐模块不可用")
        return False

def main():
    """主函数"""
    args = parse_args()
    
    # 显示系统信息
    logger.info(f"系统: {platform.system()} {platform.release()}")
    logger.info(f"处理器: {platform.processor()}")
    logger.info(f"Python: {sys.version.split()[0]}")
    
    # 检查项目结构
    src_dir = Path("src/hardware")
    if not src_dir.exists():
        logger.error(f"项目目录结构错误: {src_dir} 不存在")
        return 1
    
    # 创建lib目录（如果不存在）
    lib_dir = Path("lib")
    if not lib_dir.exists():
        logger.info(f"创建库目录: {lib_dir}")
        lib_dir.mkdir(parents=True)
    
    # 检查内存对齐模块
    memory_alignment_available = check_memory_alignment()
    
    # 根据参数决定构建哪些库
    build_all = args.all or (not args.simd and not args.assembly)
    
    success = True
    
    if args.simd or build_all:
        success = build_simd(args.debug, args.clean) and success
        
    if args.assembly or build_all:
        success = build_assembly(args.debug, args.clean) and success
        
    # 测试
    if args.test and success:
        test_success = run_tests()
        logger.info(f"测试{'通过' if test_success else '失败'}")
        success = test_success and success
    
    # 总结
    logger.info("=" * 70)
    logger.info("构建总结:")
    logger.info(f"- SIMD优化: {'已构建' if args.simd or build_all else '未构建'}")
    logger.info(f"- 汇编优化: {'已构建' if args.assembly or build_all else '未构建'}")
    logger.info(f"- 内存对齐: {'可用' if memory_alignment_available else '不可用'}")
    logger.info(f"- 构建模式: {'调试' if args.debug else '发布'}")
    logger.info(f"- 构建结果: {'成功' if success else '失败'}")
    
    if success:
        logger.info("\n优化库构建成功！现在可以在项目中使用优化功能了。")
        if memory_alignment_available:
            logger.info("内存对齐优化已集成，无需编译。")
        logger.info("""
使用方法:
1. SIMD向量化: from src.hardware.simd_utils import matrix_multiply
2. 汇编优化: from src.hardware.assembly_wrapper import get_platform_asm
3. 内存对齐: from src.hardware.memory_aligner import create_aligned_array
4. 优化路由器: from src.hardware.optimization_router import OptimizationRouter
""")
    else:
        logger.error("\n构建失败，请检查错误日志。")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 