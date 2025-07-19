#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强版依赖安装脚本

支持多镜像源、详细错误处理和完整的依赖管理
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dependency_install.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DependencyInstaller:
    """增强版依赖安装器"""
    
    def __init__(self, python_path: str = None):
        """初始化安装器
        
        Args:
            python_path: Python解释器路径，默认使用系统Python
        """
        self.python_path = python_path or r"C:\Users\13075\AppData\Local\Programs\Python\Python313\python.exe"
        
        # 镜像源配置（按优先级排序）
        self.mirror_sources = [
            {
                'name': '清华大学镜像',
                'url': 'https://pypi.tuna.tsinghua.edu.cn/simple/',
                'trusted_host': 'pypi.tuna.tsinghua.edu.cn'
            },
            {
                'name': '阿里云镜像',
                'url': 'https://mirrors.aliyun.com/pypi/simple/',
                'trusted_host': 'mirrors.aliyun.com'
            },
            {
                'name': '官方PyPI源',
                'url': 'https://pypi.org/simple/',
                'trusted_host': 'pypi.org'
            }
        ]
        
        # 核心依赖包列表
        self.core_dependencies = [
            'matplotlib',
            'pyqtgraph', 
            'spacy',
            'jieba',
            'nltk',
            'sentence-transformers',
            'numpy',
            'pandas',
            'scipy',
            'scikit-learn',
            'requests',
            'pyyaml',
            'tqdm',
            'psutil',
            'pillow',
            'opencv-python',
            'moviepy',
            'librosa',
            'torch',
            'transformers'
        ]
        
        # 可选依赖包（安装失败不影响核心功能）
        self.optional_dependencies = [
            'py-cpuinfo',
            'GPUtil',
            'pyqtgraph',
            'scikit-image',
            'ffmpeg-python',
            'soundfile',
            'resampy'
        ]
        
        # 安装结果统计
        self.install_results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
    
    def check_python_environment(self) -> bool:
        """检查Python环境"""
        try:
            result = subprocess.run(
                [self.python_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✓ Python环境检查通过: {version}")
                logger.info(f"✓ Python路径: {self.python_path}")
                return True
            else:
                logger.error(f"✗ Python环境检查失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"✗ Python环境检查异常: {e}")
            return False
    
    def check_package_installed(self, package_name: str) -> bool:
        """检查包是否已安装"""
        try:
            result = subprocess.run(
                [self.python_path, '-c', f'import {package_name.replace("-", "_")}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def install_package_with_mirror(self, package_name: str, mirror: Dict[str, str]) -> bool:
        """使用指定镜像源安装包"""
        try:
            cmd = [
                self.python_path, '-m', 'pip', 'install',
                package_name,
                '-i', mirror['url'],
                '--trusted-host', mirror['trusted_host'],
                '--timeout', '60',
                '--retries', '3'
            ]
            
            logger.info(f"  尝试使用 {mirror['name']} 安装 {package_name}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"  ✓ {package_name} 安装成功 (使用 {mirror['name']})")
                return True
            else:
                logger.warning(f"  ✗ {package_name} 安装失败 (使用 {mirror['name']}): {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning(f"  ✗ {package_name} 安装超时 (使用 {mirror['name']})")
            return False
        except Exception as e:
            logger.warning(f"  ✗ {package_name} 安装异常 (使用 {mirror['name']}): {e}")
            return False
    
    def install_package(self, package_name: str, is_optional: bool = False) -> bool:
        """安装单个包，尝试所有镜像源"""
        logger.info(f"正在安装 {package_name}...")
        
        # 检查是否已安装
        if self.check_package_installed(package_name):
            logger.info(f"✓ {package_name} 已安装，跳过")
            self.install_results['skipped'].append(package_name)
            return True
        
        # 尝试所有镜像源
        for mirror in self.mirror_sources:
            if self.install_package_with_mirror(package_name, mirror):
                self.install_results['success'].append(package_name)
                return True
            
            # 短暂延迟后尝试下一个镜像源
            time.sleep(1)
        
        # 所有镜像源都失败
        logger.error(f"✗ {package_name} 安装失败 (所有镜像源都尝试过)")
        self.install_results['failed'].append(package_name)
        
        if not is_optional:
            logger.warning(f"  {package_name} 是核心依赖，建议手动安装")
        
        return False
    
    def install_all_dependencies(self) -> bool:
        """安装所有依赖"""
        logger.info("=" * 60)
        logger.info("VisionAI-ClipsMaster 增强版依赖安装")
        logger.info("=" * 60)
        
        # 检查Python环境
        if not self.check_python_environment():
            logger.error("Python环境检查失败，无法继续安装")
            return False
        
        # 安装核心依赖
        logger.info("\n1. 安装核心依赖包...")
        for package in self.core_dependencies:
            self.install_package(package, is_optional=False)
            time.sleep(0.5)  # 避免过于频繁的请求
        
        # 安装可选依赖
        logger.info("\n2. 安装可选依赖包...")
        for package in self.optional_dependencies:
            self.install_package(package, is_optional=True)
            time.sleep(0.5)
        
        # 输出安装结果
        self.print_install_summary()
        
        # 判断是否成功
        core_failed = [pkg for pkg in self.install_results['failed'] 
                      if pkg in self.core_dependencies]
        
        if core_failed:
            logger.error(f"核心依赖安装失败: {core_failed}")
            return False
        else:
            logger.info("✓ 所有核心依赖安装成功！")
            return True
    
    def print_install_summary(self):
        """打印安装结果摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("安装结果摘要")
        logger.info("=" * 60)
        
        logger.info(f"✓ 成功安装: {len(self.install_results['success'])} 个")
        for pkg in self.install_results['success']:
            logger.info(f"  - {pkg}")
        
        logger.info(f"⚠ 跳过安装: {len(self.install_results['skipped'])} 个")
        for pkg in self.install_results['skipped']:
            logger.info(f"  - {pkg} (已安装)")
        
        logger.info(f"✗ 安装失败: {len(self.install_results['failed'])} 个")
        for pkg in self.install_results['failed']:
            logger.info(f"  - {pkg}")
        
        logger.info("=" * 60)

def main():
    """主函数"""
    installer = DependencyInstaller()
    
    try:
        success = installer.install_all_dependencies()
        
        if success:
            logger.info("\n🎉 依赖安装完成！")
            logger.info("现在可以运行 simple_ui_fixed.py 测试UI功能")
            return 0
        else:
            logger.error("\n❌ 依赖安装失败！")
            logger.error("请检查网络连接和Python环境")
            return 1
            
    except KeyboardInterrupt:
        logger.info("\n用户中断安装")
        return 1
    except Exception as e:
        logger.error(f"\n安装过程中发生异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
