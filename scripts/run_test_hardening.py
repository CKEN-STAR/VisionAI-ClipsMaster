#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试权限加固一键运行脚本

该脚本执行完整的测试权限加固流程：
1. 设置目录权限
2. 生成/更新黄金样本哈希
3. 验证权限和完整性
4. 运行权限测试
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_hardening')

# 获取项目根目录
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent

def run_command(cmd, desc=None, ignore_error=False):
    """运行命令并打印结果"""
    if desc:
        logger.info(f"执行: {desc}")
        
    logger.debug(f"命令: {cmd}")
    
    try:
        result = subprocess.run(
            cmd, 
            check=not ignore_error,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(line)
                
        if result.stderr:
            for line in result.stderr.splitlines():
                if ignore_error:
                    logger.debug(line)
                else:
                    logger.warning(line)
                    
        return result.returncode == 0
    except Exception as e:
        logger.error(f"执行命令失败: {e}")
        return False

def step_fix_permissions():
    """步骤1: 修复目录权限"""
    logger.info("=== 步骤1: 修复目录权限 ===")
    
    script_path = SCRIPT_DIR / "secure_test_permissions.py"
    return run_command(
        [sys.executable, str(script_path), "--fix"],
        "修复测试目录权限"
    )

def step_generate_hashes():
    """步骤2: 生成/更新黄金样本哈希"""
    logger.info("=== 步骤2: 生成/更新黄金样本哈希 ===")
    
    script_path = PROJECT_ROOT / "tests/golden_samples/verify_integrity.py"
    return run_command(
        [sys.executable, str(script_path), "--generate", "--force"],
        "生成黄金样本哈希"
    )

def step_verify_integrity():
    """步骤3: 验证权限和完整性"""
    logger.info("=== 步骤3: 验证权限和完整性 ===")
    
    # 验证权限
    perm_script = SCRIPT_DIR / "secure_test_permissions.py"
    perm_success = run_command(
        [sys.executable, str(perm_script), "--check"],
        "验证目录权限"
    )
    
    # 验证完整性
    hash_script = PROJECT_ROOT / "tests/golden_samples/verify_integrity.py"
    hash_success = run_command(
        [sys.executable, str(hash_script), "--verify"],
        "验证黄金样本完整性",
        ignore_error=True  # 如果没有哈希文件，可能会失败
    )
    
    return perm_success and hash_success

def step_run_tests():
    """步骤4: 运行权限测试"""
    logger.info("=== 步骤4: 运行权限测试 ===")
    
    test_script = PROJECT_ROOT / "tests/test_permissions.py"
    return run_command(
        [sys.executable, str(test_script)],
        "运行权限测试",
        ignore_error=True  # 不中断流程
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试权限加固一键运行脚本')
    parser.add_argument('--no-fix', action='store_true', help='跳过修复步骤，只执行验证')
    parser.add_argument('--no-hash', action='store_true', help='跳过哈希生成步骤')
    parser.add_argument('--no-test', action='store_true', help='跳过测试步骤')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"开始测试权限加固流程，工作目录: {PROJECT_ROOT}")
    
    success = True
    
    # 步骤1: 修复权限
    if not args.no_fix:
        if not step_fix_permissions():
            logger.error("❌ 修复权限失败！")
            success = False
    
    # 步骤2: 生成哈希
    if not args.no_hash and success:
        if not step_generate_hashes():
            logger.error("❌ 生成哈希失败！")
            success = False
    
    # 步骤3: 验证权限和完整性
    if success:
        if not step_verify_integrity():
            logger.error("❌ 验证失败！")
            success = False
    
    # 步骤4: 运行测试
    if not args.no_test and success:
        if not step_run_tests():
            logger.error("❌ 权限测试失败！")
            success = False
    
    if success:
        logger.info("✅ 测试权限加固流程完成！")
        return 0
    else:
        logger.error("❌ 测试权限加固流程失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 