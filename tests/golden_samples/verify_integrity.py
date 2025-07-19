#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
黄金样本完整性验证工具

该脚本用于验证黄金样本的完整性，通过计算文件哈希并与存储的哈希值比较。
确保测试数据未被意外或恶意修改。
"""

import os
import sys
import json
import hashlib
import argparse
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('integrity_checker')

# 项目根目录
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# 黄金样本目录
GOLDEN_SAMPLES_DIR = SCRIPT_DIR
HASH_DIR = GOLDEN_SAMPLES_DIR / "hashes"

# 默认的哈希算法
DEFAULT_HASH_ALGORITHM = "sha256"

def is_windows() -> bool:
    """检查是否运行在Windows平台上"""
    return platform.system() == 'Windows'

def ensure_hash_dir_exists() -> None:
    """确保哈希目录存在"""
    if not HASH_DIR.exists():
        HASH_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建哈希目录: {HASH_DIR}")

def set_dir_writable(dir_path: Path, writable: bool = True) -> bool:
    """设置目录为可写或只读
    
    Args:
        dir_path: 目录路径
        writable: 是否可写
        
    Returns:
        bool: 是否成功
    """
    try:
        if is_windows():
            if writable:
                subprocess.run(['attrib', '-R', str(dir_path)], check=True)
            else:
                subprocess.run(['attrib', '+R', str(dir_path)], check=True)
        else:
            if writable:
                os.chmod(dir_path, 0o755)  # rwxr-xr-x
            else:
                os.chmod(dir_path, 0o555)  # r-xr-xr-x
        return True
    except Exception as e:
        logger.error(f"设置目录 {dir_path} 权限失败: {e}")
        return False

def calculate_file_hash(file_path: Path, hash_algorithm: str = DEFAULT_HASH_ALGORITHM) -> str:
    """计算文件的哈希值
    
    Args:
        file_path: 文件路径
        hash_algorithm: 哈希算法，默认为SHA-256
        
    Returns:
        str: 文件哈希值的十六进制字符串
    """
    hash_obj = hashlib.new(hash_algorithm)
    
    # 分块读取，适用于大文件
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()

def collect_sample_files() -> List[Path]:
    """收集所有黄金样本文件（排除hashes目录和特定文件）
    
    Returns:
        List[Path]: 样本文件路径列表
    """
    sample_files = []
    
    # 排除的目录和文件
    exclude_dirs = {HASH_DIR, GOLDEN_SAMPLES_DIR / "__pycache__"}
    exclude_files = {
        GOLDEN_SAMPLES_DIR / "verify_integrity.py",
        GOLDEN_SAMPLES_DIR / "generate_samples.py",
        GOLDEN_SAMPLES_DIR / "run_golden_sample_generation.py",
        GOLDEN_SAMPLES_DIR / "__init__.py"
    }
    
    # 遍历目录收集文件
    for root, dirs, files in os.walk(GOLDEN_SAMPLES_DIR):
        root_path = Path(root)
        
        # 忽略排除的目录
        for exclude_dir in exclude_dirs:
            if exclude_dir in [root_path, *root_path.parents]:
                continue
        
        for file in files:
            file_path = root_path / file
            
            # 忽略排除的文件
            if file_path in exclude_files:
                continue
                
            sample_files.append(file_path)
    
    return sample_files

def generate_hashes(sample_files: List[Path], hash_algorithm: str = DEFAULT_HASH_ALGORITHM) -> Dict[str, str]:
    """为所有样本文件生成哈希值
    
    Args:
        sample_files: 样本文件路径列表
        hash_algorithm: 哈希算法
        
    Returns:
        Dict[str, str]: 文件路径到哈希值的映射
    """
    hash_dict = {}
    
    for file_path in sample_files:
        try:
            # 计算文件相对路径和哈希值
            rel_path = file_path.relative_to(GOLDEN_SAMPLES_DIR)
            file_hash = calculate_file_hash(file_path, hash_algorithm)
            hash_dict[str(rel_path)] = file_hash
            logger.debug(f"已生成哈希值: {rel_path} -> {file_hash[:8]}...")
        except Exception as e:
            logger.error(f"生成 {file_path} 的哈希值失败: {e}")
    
    return hash_dict

def save_hashes(hash_dict: Dict[str, str], hash_algorithm: str = DEFAULT_HASH_ALGORITHM) -> bool:
    """保存哈希值到文件
    
    Args:
        hash_dict: 文件路径到哈希值的映射
        hash_algorithm: 哈希算法
        
    Returns:
        bool: 是否成功保存
    """
    ensure_hash_dir_exists()
    hash_file = HASH_DIR / f"files_{hash_algorithm}.json"
    
    # 临时设置目录和文件为可写
    dir_was_readonly = False
    file_was_readonly = False
    
    try:
        # 检查并临时更改目录权限
        if HASH_DIR.exists():
            if is_windows():
                # 检查目录是否为只读
                result = subprocess.run(
                    ['attrib', str(HASH_DIR)],
                    capture_output=True, text=True, check=True
                )
                dir_was_readonly = 'R' in result.stdout
                
                # 还需要检查父目录是否为只读
                parent_dir_was_readonly = False
                parent_result = subprocess.run(
                    ['attrib', str(GOLDEN_SAMPLES_DIR)],
                    capture_output=True, text=True, check=True
                )
                parent_dir_was_readonly = 'R' in parent_result.stdout
                
                # 先临时设置父目录为可写
                if parent_dir_was_readonly:
                    subprocess.run(['attrib', '-R', str(GOLDEN_SAMPLES_DIR)], check=True)
                    logger.debug(f"临时设置父目录 {GOLDEN_SAMPLES_DIR} 为可写")
                
                # 设置哈希目录为可写
                if dir_was_readonly:
                    subprocess.run(['attrib', '-R', str(HASH_DIR)], check=True)
                    logger.debug(f"临时设置目录 {HASH_DIR} 为可写")
            else:
                # Linux/macOS处理
                dir_mode = os.stat(HASH_DIR).st_mode
                dir_was_readonly = not (dir_mode & 0o200)  # 检查用户写权限
                
                parent_dir_mode = os.stat(GOLDEN_SAMPLES_DIR).st_mode
                parent_dir_was_readonly = not (parent_dir_mode & 0o200)
                
                if parent_dir_was_readonly:
                    os.chmod(GOLDEN_SAMPLES_DIR, 0o755)  # rwxr-xr-x
                    logger.debug(f"临时设置父目录 {GOLDEN_SAMPLES_DIR} 为可写")
                    
                if dir_was_readonly:
                    os.chmod(HASH_DIR, 0o755)  # rwxr-xr-x
                    logger.debug(f"临时设置目录 {HASH_DIR} 为可写")
        
        # 检查并临时更改文件权限
        if hash_file.exists():
            if is_windows():
                result = subprocess.run(
                    ['attrib', str(hash_file)],
                    capture_output=True, text=True, check=True
                )
                file_was_readonly = 'R' in result.stdout
                
                if file_was_readonly:
                    subprocess.run(['attrib', '-R', str(hash_file)], check=True)
                    logger.debug(f"临时设置文件 {hash_file} 为可写")
            else:
                file_mode = os.stat(hash_file).st_mode
                file_was_readonly = not (file_mode & 0o200)
                
                if file_was_readonly:
                    os.chmod(hash_file, 0o644)  # rw-r--r--
                    logger.debug(f"临时设置文件 {hash_file} 为可写")
        
        # 保存哈希值
        with open(hash_file, 'w', encoding='utf-8') as f:
            json.dump(hash_dict, f, indent=2, sort_keys=True)
        logger.info(f"哈希值已保存到: {hash_file}")
        success = True
    except Exception as e:
        logger.error(f"保存哈希值失败: {e}")
        success = False
        
    # 恢复目录和文件权限
    try:
        # 恢复文件权限
        if hash_file.exists() and file_was_readonly:
            if is_windows():
                subprocess.run(['attrib', '+R', str(hash_file)], check=True)
                logger.debug(f"已恢复文件 {hash_file} 为只读")
            else:
                os.chmod(hash_file, 0o444)  # r--r--r--
                logger.debug(f"已恢复文件 {hash_file} 为只读")
        
        # 恢复目录权限
        if dir_was_readonly:
            if is_windows():
                subprocess.run(['attrib', '+R', str(HASH_DIR)], check=True)
                logger.debug(f"已恢复目录 {HASH_DIR} 为只读")
            else:
                os.chmod(HASH_DIR, 0o555)  # r-xr-xr-x
                logger.debug(f"已恢复目录 {HASH_DIR} 为只读")
                
        # 恢复父目录权限
        if parent_dir_was_readonly:
            if is_windows():
                subprocess.run(['attrib', '+R', str(GOLDEN_SAMPLES_DIR)], check=True)
                logger.debug(f"已恢复父目录 {GOLDEN_SAMPLES_DIR} 为只读")
            else:
                os.chmod(GOLDEN_SAMPLES_DIR, 0o555)  # r-xr-xr-x
                logger.debug(f"已恢复父目录 {GOLDEN_SAMPLES_DIR} 为只读")
    except Exception as e:
        logger.warning(f"恢复权限失败: {e}")
            
    return success

def load_hashes(hash_algorithm: str = DEFAULT_HASH_ALGORITHM) -> Optional[Dict[str, str]]:
    """从文件加载哈希值
    
    Args:
        hash_algorithm: 哈希算法
        
    Returns:
        Optional[Dict[str, str]]: 文件路径到哈希值的映射，失败时返回None
    """
    hash_file = HASH_DIR / f"files_{hash_algorithm}.json"
    
    if not hash_file.exists():
        logger.warning(f"哈希文件不存在: {hash_file}")
        return None
    
    try:
        with open(hash_file, 'r', encoding='utf-8') as f:
            hash_dict = json.load(f)
        logger.info(f"已加载哈希值: {hash_file}")
        return hash_dict
    except Exception as e:
        logger.error(f"加载哈希值失败: {e}")
        return None

def verify_integrity(hash_algorithm: str = DEFAULT_HASH_ALGORITHM) -> Tuple[bool, List[str]]:
    """验证黄金样本的完整性
    
    Args:
        hash_algorithm: 哈希算法
        
    Returns:
        Tuple[bool, List[str]]: (是否验证通过，失败文件列表)
    """
    # 加载存储的哈希值
    stored_hashes = load_hashes(hash_algorithm)
    if not stored_hashes:
        logger.error("无法加载存储的哈希值，请先运行生成命令")
        return False, ["无法加载存储的哈希值"]
    
    # 收集样本文件
    sample_files = collect_sample_files()
    
    # 验证所有文件
    failed_files = []
    
    # 检查文件是否缺失
    stored_paths = set(stored_hashes.keys())
    current_paths = {str(f.relative_to(GOLDEN_SAMPLES_DIR)) for f in sample_files}
    
    # 排除哈希文件本身 (规范化路径格式)
    hash_file_paths = [
        f"hashes/files_{hash_algorithm}.json",
        f"hashes\\files_{hash_algorithm}.json"
    ]
    
    # 检查缺失文件
    missing_files = stored_paths - current_paths
    if missing_files:
        for missing in missing_files:
            # 排除哈希文件本身
            if any(missing == path for path in hash_file_paths) or \
               missing.replace('\\', '/') in hash_file_paths or \
               missing.replace('/', '\\') in hash_file_paths:
                continue
            logger.warning(f"缺失文件: {missing}")
            failed_files.append(f"缺失: {missing}")
    
    # 检查新增文件
    new_files = current_paths - stored_paths
    if new_files:
        for new_file in new_files:
            # 排除哈希文件本身
            if any(new_file == path for path in hash_file_paths) or \
               new_file.replace('\\', '/') in hash_file_paths or \
               new_file.replace('/', '\\') in hash_file_paths:
                continue
            logger.warning(f"新增文件: {new_file}")
            failed_files.append(f"新增: {new_file}")
    
    # 验证文件哈希
    for file_path in sample_files:
        rel_path = str(file_path.relative_to(GOLDEN_SAMPLES_DIR))
        
        # 跳过哈希文件本身，它肯定会变化
        if any(rel_path == path for path in hash_file_paths) or \
           rel_path.replace('\\', '/') in hash_file_paths or \
           rel_path.replace('/', '\\') in hash_file_paths:
            logger.debug(f"跳过哈希文件: {rel_path}")
            continue
            
        # 跳过新文件
        if rel_path in new_files:
            continue
        
        try:
            # 尝试获取存储的哈希值，考虑不同的路径分隔符格式
            current_hash = calculate_file_hash(file_path, hash_algorithm)
            stored_hash = stored_hashes.get(rel_path)
            
            # 如果找不到，尝试替换路径分隔符
            if stored_hash is None:
                alt_rel_path = rel_path.replace('\\', '/')
                stored_hash = stored_hashes.get(alt_rel_path)
                
            # 如果还找不到，尝试另一种替换
            if stored_hash is None:
                alt_rel_path = rel_path.replace('/', '\\')
                stored_hash = stored_hashes.get(alt_rel_path)
            
            if stored_hash and current_hash != stored_hash:
                logger.warning(f"文件已修改: {rel_path}")
                logger.debug(f"  期望: {stored_hash}")
                logger.debug(f"  实际: {current_hash}")
                failed_files.append(f"已修改: {rel_path}")
        except Exception as e:
            logger.error(f"验证 {file_path} 失败: {e}")
            failed_files.append(f"错误: {rel_path} - {e}")
    
    # 验证结果
    if not failed_files:
        logger.info("✓ 所有黄金样本文件验证通过")
        return True, []
    else:
        logger.warning(f"✗ 发现 {len(failed_files)} 个文件完整性问题")
        return False, failed_files

def generate_or_update_hashes(hash_algorithm: str = DEFAULT_HASH_ALGORITHM) -> bool:
    """生成或更新黄金样本的哈希值
    
    Args:
        hash_algorithm: 哈希算法
        
    Returns:
        bool: 是否成功
    """
    # 收集样本文件
    sample_files = collect_sample_files()
    logger.info(f"发现 {len(sample_files)} 个样本文件")
    
    # 生成哈希值
    hash_dict = generate_hashes(sample_files, hash_algorithm)
    
    # 保存哈希值
    return save_hashes(hash_dict, hash_algorithm)

def main() -> int:
    """主函数"""
    parser = argparse.ArgumentParser(description='黄金样本完整性验证工具')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--verify', action='store_true', help='验证黄金样本的完整性')
    group.add_argument('--generate', action='store_true', help='生成黄金样本的哈希值')
    group.add_argument('--update', action='store_true', help='更新黄金样本的哈希值')
    
    parser.add_argument('--algorithm', default=DEFAULT_HASH_ALGORITHM,
                        choices=['md5', 'sha1', 'sha256', 'sha512'],
                        help=f'哈希算法 (默认: {DEFAULT_HASH_ALGORITHM})')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    parser.add_argument('--force', '-f', action='store_true', help='强制执行，忽略权限错误')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        if args.verify:
            success, failed_files = verify_integrity(args.algorithm)
            
            if failed_files:
                for failed in failed_files:
                    logger.error(f"- {failed}")
                return 1
                
        elif args.generate or args.update:
            # 临时设置目录权限（如果是只读的）
            if args.force:
                # 检查黄金样本目录是否为只读
                golden_dir_was_readonly = False
                try:
                    if is_windows():
                        result = subprocess.run(
                            ['attrib', str(GOLDEN_SAMPLES_DIR)],
                            capture_output=True, text=True, check=True
                        )
                        golden_dir_was_readonly = 'R' in result.stdout
                    else:
                        mode = os.stat(GOLDEN_SAMPLES_DIR).st_mode
                        golden_dir_was_readonly = not (mode & 0o200)
                        
                    if golden_dir_was_readonly:
                        set_dir_writable(GOLDEN_SAMPLES_DIR, True)
                        logger.info("临时设置黄金样本目录为可写")
                except Exception as e:
                    logger.warning(f"检查黄金样本目录权限失败: {e}")
            
            if not generate_or_update_hashes(args.algorithm):
                return 1
                
            # 恢复目录权限
            if args.force and golden_dir_was_readonly:
                try:
                    set_dir_writable(GOLDEN_SAMPLES_DIR, False)
                    logger.info("已恢复黄金样本目录为只读")
                except Exception as e:
                    logger.warning(f"恢复黄金样本目录权限失败: {e}")
                
    except Exception as e:
        logger.error(f"执行过程中出错: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(main()) 