#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存探针C扩展构建脚本

此脚本用于编译内存探针的C扩展库，支持Windows、Linux和macOS平台。
"""

import os
import sys
import platform
import subprocess
import argparse
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BuildProbes")

# 支持平台
SUPPORTED_PLATFORMS = {
    "Windows": {
        "extension": ".dll",
        "prefix": "",
        "compiler": {
            "command": "cl",
            "args": "/LD {source_file} /Fe{output_file} /DMEMORY_PROBE_MAIN"
        }
    },
    "Linux": {
        "extension": ".so",
        "prefix": "lib",
        "compiler": {
            "command": "gcc",
            "args": "-shared -fPIC -o {output_file} {source_file} -DMEMORY_PROBE_MAIN"
        }
    },
    "Darwin": {  # macOS
        "extension": ".dylib",
        "prefix": "lib",
        "compiler": {
            "command": "gcc",
            "args": "-shared -fPIC -o {output_file} {source_file} -DMEMORY_PROBE_MAIN"
        }
    }
}

def check_compiler(platform_info):
    """
    检查编译器是否可用
    
    Args:
        platform_info: 平台信息
        
    Returns:
        bool: 编译器是否可用
    """
    compiler = platform_info["compiler"]["command"]
    try:
        if platform.system() == "Windows":
            # Windows上检查cl.exe
            result = subprocess.run(f"where {compiler}", shell=True, capture_output=True, text=True)
        else:
            # Linux/macOS上检查gcc
            result = subprocess.run(f"which {compiler}", shell=True, capture_output=True, text=True)
            
        return result.returncode == 0
    except Exception:
        return False

def build_probes(source_dir=None, output_dir=None, clean=False, debug=False):
    """
    构建内存探针C扩展
    
    Args:
        source_dir: 源代码目录，如果为None则使用默认目录
        output_dir: 输出目录，如果为None则使用默认目录
        clean: 是否在构建前清理目标文件
        debug: 是否使用调试模式构建
        
    Returns:
        bool: 构建是否成功
    """
    # 确定当前平台
    system = platform.system()
    if system not in SUPPORTED_PLATFORMS:
        logger.error(f"不支持的平台: {system}")
        return False
        
    platform_info = SUPPORTED_PLATFORMS[system]
    
    # 检查编译器
    if not check_compiler(platform_info):
        logger.error(f"找不到编译器: {platform_info['compiler']['command']}")
        logger.error("请确保已安装相应的编译工具链")
        return False
    
    # 确定目录
    root_dir = Path(__file__).resolve().parent.parent
    
    if source_dir is None:
        source_dir = root_dir / "src" / "probes"
        
    if output_dir is None:
        output_dir = root_dir / "build" / "lib"
        
    # 确保目录存在
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 确定源文件和目标文件
    source_file = source_dir / "memory_probes.c"
    output_file = output_dir / f"{platform_info['prefix']}memory_probes{platform_info['extension']}"
    
    # 验证源文件存在
    if not source_file.exists():
        logger.error(f"找不到源文件: {source_file}")
        return False
        
    # 如果需要清理，删除旧的目标文件
    if clean and output_file.exists():
        logger.info(f"删除旧的目标文件: {output_file}")
        output_file.unlink()
    
    # 构建编译命令
    compiler_command = platform_info["compiler"]["command"]
    compiler_args = platform_info["compiler"]["args"].format(
        source_file=source_file,
        output_file=output_file
    )
    
    # 添加调试标志
    if debug:
        if system == "Windows":
            compiler_args += " /Zi /DEBUG"
        else:
            compiler_args += " -g"
    
    # 完整的编译命令
    command = f"{compiler_command} {compiler_args}"
    
    # 执行编译
    logger.info(f"编译命令: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"编译失败，错误信息:")
            logger.error(result.stderr)
            return False
            
        logger.info(f"编译成功: {output_file}")
        
        # 验证输出文件是否存在
        if not output_file.exists():
            logger.error(f"编译似乎成功，但找不到输出文件: {output_file}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"编译过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="内存探针C扩展构建脚本")
    parser.add_argument("--source-dir", type=str, help="源代码目录")
    parser.add_argument("--output-dir", type=str, help="输出目录")
    parser.add_argument("--clean", action="store_true", help="在构建前清理目标文件")
    parser.add_argument("--debug", action="store_true", help="使用调试模式构建")
    
    args = parser.parse_args()
    
    logger.info("开始构建内存探针C扩展")
    
    success = build_probes(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        clean=args.clean,
        debug=args.debug
    )
    
    if success:
        logger.info("构建成功")
        sys.exit(0)
    else:
        logger.error("构建失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 