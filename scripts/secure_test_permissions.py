#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试权限加固工具

该脚本用于设置和验证测试目录的权限，确保:
1. 黄金样本(golden_samples)目录为只读，防止意外修改
2. 临时输出目录具有适当的读写权限
3. 跨平台兼容(Windows, Linux, macOS)

使用方法:
    python scripts/secure_test_permissions.py [--check | --fix]
"""

import os
import sys
import stat
import argparse
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_permissions')

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 目录权限配置
DIR_PERMISSIONS = {
    'tests/golden_samples': {
        'linux': '550',   # r-xr-x---
        'windows': {'readonly': True, 'system': False, 'hidden': False}
    },
    'tests/tmp_output': {
        'linux': '750',   # rwxr-x---
        'windows': {'readonly': False, 'system': False, 'hidden': False}
    },
    'tests/data': {
        'linux': '550',   # r-xr-x---
        'windows': {'readonly': True, 'system': False, 'hidden': False}
    }
}

def is_windows() -> bool:
    """检查是否运行在Windows平台上"""
    return platform.system() == 'Windows'

def check_dir_exists(dir_path: Path) -> bool:
    """检查目录是否存在，如果不存在则打印警告"""
    if not dir_path.exists():
        logger.warning(f"目录 {dir_path} 不存在")
        return False
    if not dir_path.is_dir():
        logger.warning(f"{dir_path} 不是一个目录")
        return False
    return True

def ensure_dir_exists(dir_path: Path) -> bool:
    """确保目录存在，如果不存在则创建"""
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建目录 {dir_path}")
            return True
        except Exception as e:
            logger.error(f"创建目录 {dir_path} 失败: {e}")
            return False
    return True

def get_linux_permissions(path: Path) -> str:
    """获取Linux/Unix系统下的文件权限(八进制格式)"""
    try:
        mode = os.stat(path).st_mode
        # 转换为八进制字符串并截取最后3位
        return oct(mode)[-3:]
    except Exception as e:
        logger.error(f"获取 {path} 权限失败: {e}")
        return "000"

def set_linux_permissions(path: Path, permission: str) -> bool:
    """设置Linux/Unix系统下的文件权限"""
    try:
        # 八进制字符串转整数
        mode = int(permission, 8)
        if path.is_dir():
            # 递归设置目录权限
            for root, dirs, files in os.walk(path):
                root_path = Path(root)
                os.chmod(root_path, mode)
                for file in files:
                    file_path = root_path / file
                    os.chmod(file_path, mode)
        else:
            os.chmod(path, mode)
        logger.info(f"已设置 {path} 权限为 {permission}")
        return True
    except Exception as e:
        logger.error(f"设置 {path} 权限失败: {e}")
        return False

def get_windows_attributes(path: Path) -> Dict[str, bool]:
    """获取Windows系统下的文件属性"""
    try:
        result = subprocess.run(
            ['attrib', str(path)],
            capture_output=True, text=True, check=True
        )
        output = result.stdout.strip()
        
        # 解析attrib输出，例如: "R  C:\path\to\file"
        attributes = {
            'readonly': 'R' in output,
            'hidden': 'H' in output,
            'system': 'S' in output
        }
        return attributes
    except Exception as e:
        logger.error(f"获取 {path} 属性失败: {e}")
        return {'readonly': False, 'hidden': False, 'system': False}

def set_windows_attributes(path: Path, attrs: Dict[str, bool]) -> bool:
    """设置Windows系统下的文件属性"""
    try:
        if attrs.get('readonly'):
            subprocess.run(['attrib', '+R', str(path)], check=True)
        else:
            subprocess.run(['attrib', '-R', str(path)], check=True)
            
        if attrs.get('hidden'):
            subprocess.run(['attrib', '+H', str(path)], check=True)
        else:
            subprocess.run(['attrib', '-H', str(path)], check=True)
            
        if attrs.get('system'):
            subprocess.run(['attrib', '+S', str(path)], check=True)
        else:
            subprocess.run(['attrib', '-S', str(path)], check=True)
            
        logger.info(f"已设置 {path} 属性为 {attrs}")
        return True
    except Exception as e:
        logger.error(f"设置 {path} 属性失败: {e}")
        return False

def set_windows_dir_attributes_recursive(path: Path, attrs: Dict[str, bool]) -> bool:
    """递归设置Windows系统下的目录及其内容的属性"""
    try:
        # 设置目录自身属性
        set_windows_attributes(path, attrs)
        
        # 递归设置子目录和文件
        for item in path.glob('**/*'):
            set_windows_attributes(item, attrs)
            
        return True
    except Exception as e:
        logger.error(f"递归设置 {path} 属性失败: {e}")
        return False

def verify_permissions() -> bool:
    """验证所有测试目录权限是否正确"""
    all_correct = True
    
    for dir_rel_path, perm_config in DIR_PERMISSIONS.items():
        dir_path = PROJECT_ROOT / dir_rel_path
        
        if not check_dir_exists(dir_path):
            all_correct = False
            continue
            
        if is_windows():
            expected_attrs = perm_config['windows']
            actual_attrs = get_windows_attributes(dir_path)
            
            if expected_attrs['readonly'] != actual_attrs['readonly']:
                logger.warning(f"{dir_path} 只读属性不正确: 期望={expected_attrs['readonly']}, 实际={actual_attrs['readonly']}")
                all_correct = False
        else:
            expected_perm = perm_config['linux']
            actual_perm = get_linux_permissions(dir_path)
            
            if expected_perm != actual_perm:
                logger.warning(f"{dir_path} 权限不正确: 期望={expected_perm}, 实际={actual_perm}")
                all_correct = False
    
    if all_correct:
        logger.info("✓ 所有测试目录权限正确")
    else:
        logger.warning("✗ 部分测试目录权限不正确，请运行修复命令: python scripts/secure_test_permissions.py --fix")
        
    return all_correct

def fix_permissions() -> bool:
    """修复所有测试目录权限"""
    all_fixed = True
    
    for dir_rel_path, perm_config in DIR_PERMISSIONS.items():
        dir_path = PROJECT_ROOT / dir_rel_path
        
        if not ensure_dir_exists(dir_path):
            all_fixed = False
            continue
            
        if is_windows():
            if not set_windows_dir_attributes_recursive(dir_path, perm_config['windows']):
                all_fixed = False
        else:
            if not set_linux_permissions(dir_path, perm_config['linux']):
                all_fixed = False
    
    if all_fixed:
        logger.info("✓ 所有测试目录权限已修复")
    else:
        logger.error("✗ 部分测试目录权限修复失败")
        
    return all_fixed

def verify_test_integrity() -> bool:
    """验证测试文件完整性"""
    golden_samples_dir = PROJECT_ROOT / 'tests/golden_samples'
    
    if not check_dir_exists(golden_samples_dir):
        return False
        
    # 检查index.json是否存在且有效
    index_file = golden_samples_dir / 'index.json'
    if not index_file.exists():
        logger.warning(f"黄金样本索引文件不存在: {index_file}")
        return False
        
    # TODO: 实现更复杂的完整性检查，如哈希验证等
    logger.info("✓ 测试文件完整性验证通过")
    return True

def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description='测试权限加固工具')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='检查测试目录权限是否正确')
    group.add_argument('--fix', action='store_true', help='修复测试目录权限')
    args = parser.parse_args()
    
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    
    if args.check:
        if not verify_permissions():
            return 1
        if not verify_test_integrity():
            return 1
    elif args.fix:
        if not fix_permissions():
            return 1
    else:
        # 默认执行检查
        if not verify_permissions():
            logger.info("运行 'python scripts/secure_test_permissions.py --fix' 来修复权限问题")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 