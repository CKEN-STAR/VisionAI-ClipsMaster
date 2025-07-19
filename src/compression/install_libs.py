#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
压缩库安装脚本

安装高性能压缩所需的库
"""

import os
import sys
import subprocess
import logging
import platform
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("InstallLibs")

def get_pip_command():
    """
    获取正确的pip命令(pip或pip3)
    
    Returns:
        str: pip命令
    """
    if sys.version_info.major == 3:
        # 在虚拟环境中
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            return "pip"
        # 检查pip3是否可用
        try:
            subprocess.check_call(["pip3", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return "pip3"
        except:
            return "pip"
    else:
        return "pip"

def install_package(package_name, version=None, extra_args=None):
    """
    安装Python包
    
    Args:
        package_name: 包名
        version: 版本(可选)
        extra_args: 额外的pip参数(列表)
        
    Returns:
        bool: 是否成功
    """
    pip_cmd = get_pip_command()
    
    # 构建安装命令
    cmd = [pip_cmd, "install"]
    
    # 添加额外参数
    if extra_args:
        cmd.extend(extra_args)
    
    # 添加包名和版本
    if version:
        cmd.append(f"{package_name}=={version}")
    else:
        cmd.append(package_name)
    
    # 执行安装
    try:
        logger.info(f"安装 {package_name}" + (f" 版本 {version}" if version else "") + "...")
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        logger.info(f"成功安装 {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安装 {package_name} 失败: {e.output.decode()}")
        return False

def install_compression_libs():
    """安装压缩库"""
    logger.info("开始安装压缩库...")
    
    libs = [
        {"name": "zstandard", "version": "0.18.0", "alias": "zstd"},
        {"name": "lz4", "version": "4.3.2"},
        {"name": "python-snappy", "alias": "snappy"},
    ]
    
    success_count = 0
    
    for lib in libs:
        lib_name = lib["name"]
        lib_version = lib.get("version")
        alias = lib.get("alias", lib_name)
        
        # 尝试导入库以检查是否已安装
        try:
            if alias == "zstd":
                import zstd
                logger.info(f"{alias} 已安装，版本: {getattr(zstd, '__version__', '未知')}")
                success_count += 1
                continue
            elif alias == "lz4":
                import lz4
                logger.info(f"{alias} 已安装，版本: {getattr(lz4, '__version__', '未知')}")
                success_count += 1
                continue
            elif alias == "snappy":
                import snappy
                logger.info(f"{alias} 已安装，版本: {getattr(snappy, '__version__', '未知')}")
                success_count += 1
                continue
        except ImportError:
            pass
        
        # 安装库
        if install_package(lib_name, lib_version):
            success_count += 1
    
    # 返回是否全部成功
    return success_count == len(libs)

def install_build_tools():
    """安装构建工具(针对需要编译的库)"""
    system = platform.system().lower()
    
    if system == "windows":
        logger.info("Windows平台检测到，安装Visual C++ Build Tools...")
        
        # 检查Visual C++ Build Tools是否已安装
        # 这是一个简单的检查，可能不总是准确
        vc_path = os.path.expandvars("%ProgramFiles(x86)%\\Microsoft Visual Studio")
        if os.path.exists(vc_path):
            logger.info("Visual C++ 构建工具似乎已经安装")
            return True
        
        logger.warning("需要安装Visual C++ Build Tools才能编译某些压缩库")
        logger.info("请访问: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        logger.info("安装后重新运行此脚本")
        
        return False
        
    elif system == "linux":
        logger.info("Linux平台检测到，安装构建工具...")
        
        # 检测发行版
        try:
            import distro
            dist_name = distro.id()
        except:
            # 尝试使用platform.linux_distribution(已弃用)
            dist_name = platform.linux_distribution()[0].lower()
        
        if "ubuntu" in dist_name or "debian" in dist_name:
            cmd = "apt-get update && apt-get install -y build-essential python3-dev"
        elif "fedora" in dist_name or "rhel" in dist_name or "centos" in dist_name:
            cmd = "dnf install -y gcc gcc-c++ python3-devel"
        else:
            logger.warning(f"未知的Linux发行版: {dist_name}，请手动安装构建工具")
            return False
        
        try:
            logger.info(f"执行: {cmd}")
            subprocess.check_call(cmd, shell=True)
            logger.info("构建工具安装成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"安装构建工具失败: {e}")
            return False
            
    elif system == "darwin":  # macOS
        logger.info("macOS平台检测到，安装构建工具...")
        
        # 检查Xcode Command Line Tools
        try:
            subprocess.check_call(["xcode-select", "-p"], stdout=subprocess.PIPE)
            logger.info("Xcode Command Line Tools 已安装")
            return True
        except:
            logger.info("安装 Xcode Command Line Tools...")
            try:
                subprocess.check_call(["xcode-select", "--install"])
                logger.info("Xcode Command Line Tools 安装请求已发送，请按照屏幕提示完成安装")
                logger.info("安装完成后重新运行此脚本")
                return False
            except:
                logger.error("安装 Xcode Command Line Tools 失败")
                return False
    
    else:
        logger.warning(f"未知的操作系统: {system}，请手动安装必要的构建工具")
        return False

def update_requirements():
    """更新requirements.txt文件"""
    requirements_path = Path(__file__).parent / "requirements.txt"
    
    compression_libs = [
        "zstandard>=0.18.0",
        "lz4>=4.3.2",
        "python-snappy"
    ]
    
    # 读取现有requirements
    existing_lines = []
    if requirements_path.exists():
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                existing_lines = [line.strip() for line in f.readlines()]
        except UnicodeDecodeError:
            # 尝试不同的编码
            encodings = ['latin1', 'gbk', 'cp1252']
            for encoding in encodings:
                try:
                    with open(requirements_path, 'r', encoding=encoding) as f:
                        existing_lines = [line.strip() for line in f.readlines()]
                    break
                except UnicodeDecodeError:
                    continue
    
    # 添加缺失的库
    for lib in compression_libs:
        lib_name = lib.split('>=')[0].split('==')[0]
        if not any(line.startswith(lib_name) for line in existing_lines):
            existing_lines.append(lib)
    
    # 写回文件
    with open(requirements_path, 'w', encoding='utf-8') as f:
        for line in existing_lines:
            f.write(line + '\n')
    
    logger.info(f"已更新 {requirements_path}")

def main():
    """主函数"""
    logger.info("检查并安装高性能压缩库...")
    
    # 检查构建工具
    tools_ready = install_build_tools()
    if not tools_ready:
        logger.warning("构建工具不完整，某些库可能无法正确安装")
        user_input = input("是否继续安装? (y/n): ")
        if user_input.lower() != 'y':
            logger.info("安装已取消")
            return 1
    
    # 安装压缩库
    if install_compression_libs():
        logger.info("所有压缩库安装成功 ✓")
    else:
        logger.warning("部分压缩库安装失败，某些高性能压缩功能可能不可用")
    
    # 更新requirements.txt
    update_requirements()
    
    logger.info("安装过程完成")
    
    # 尝试重新导入库以验证安装
    try:
        import zstd
        logger.info(f"zstd 库可用: 版本 {getattr(zstd, '__version__', '未知')}")
    except ImportError:
        logger.warning("zstd 库不可用，无法使用zstd压缩算法")
    
    try:
        import lz4
        logger.info(f"lz4 库可用: 版本 {getattr(lz4, '__version__', '未知')}")
    except ImportError:
        logger.warning("lz4 库不可用，无法使用lz4压缩算法")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 