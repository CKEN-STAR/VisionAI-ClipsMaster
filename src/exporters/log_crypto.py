#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志加密模块

提供日志文件加密和解密功能，用于保护归档日志的安全性。
使用AES-256加密算法对归档日志进行加密，确保敏感日志信息的安全。
支持密钥管理、文件加密/解密和加密日志的完整性验证。
"""

import os
import sys
import base64
import hashlib
import secrets
import zipfile
import datetime
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

# 导入加密库
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from src.utils.logger import get_module_logger
from src.exporters.log_path import get_log_directory, get_archived_logs_directory

# 模块日志记录器
logger = get_module_logger("log_crypto")

# 全局加密设置
# 可以从环境变量或配置文件中读取密钥
# 这里使用一个默认密钥，实际应用时应该安全存储
DEFAULT_KEY = hashlib.sha256(b"VisionAI-ClipsMaster-Archive-Key").digest()
ARCHIVE_KEY = os.environ.get("LOG_ARCHIVE_KEY", DEFAULT_KEY)

def get_encryption_key(key_name: str = "archive") -> bytes:
    """
    获取加密密钥
    
    Args:
        key_name: 密钥名称
        
    Returns:
        加密密钥
    """
    if key_name == "archive":
        return ARCHIVE_KEY
    
    # 可以扩展其他类型的密钥
    key_dict = {
        "archive": ARCHIVE_KEY
    }
    
    return key_dict.get(key_name, DEFAULT_KEY)

def check_crypto_available() -> bool:
    """
    检查是否可用加密库
    
    如果cryptography库不可用，会尝试安装
    
    Returns:
        是否可用加密功能
    """
    global CRYPTO_AVAILABLE
    
    if CRYPTO_AVAILABLE:
        return True
        
    try:
        # 尝试导入加密库
        import importlib
        importlib.import_module("cryptography")
        CRYPTO_AVAILABLE = True
        return True
    except ImportError:
        logger.warning("加密库不可用，将尝试安装")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
            
            # 再次尝试导入
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.backends import default_backend
            CRYPTO_AVAILABLE = True
            return True
        except Exception as e:
            logger.error(f"安装加密库失败: {str(e)}")
            CRYPTO_AVAILABLE = False
            return False

def encrypt_file(file_path: Union[str, Path], 
                key: Optional[bytes] = None, 
                output_path: Optional[Union[str, Path]] = None,
                delete_original: bool = False) -> Optional[Path]:
    """
    加密文件
    
    使用AES-256加密算法加密文件
    
    Args:
        file_path: 要加密的文件路径
        key: 加密密钥，如果为None则使用默认密钥
        output_path: 输出文件路径，如果为None则在原文件名后添加.enc后缀
        delete_original: 是否删除原始文件
        
    Returns:
        加密后的文件路径，如果失败则返回None
    """
    if not check_crypto_available():
        logger.error("加密功能不可用，无法加密文件")
        return None
        
    file_path = Path(file_path)
    
    # 确保文件存在
    if not file_path.exists():
        logger.error(f"要加密的文件不存在: {file_path}")
        return None
        
    # 设置输出路径
    if output_path is None:
        output_path = file_path.with_suffix(file_path.suffix + ".enc")
    else:
        output_path = Path(output_path)
        
    # 使用默认密钥（如果未提供）
    if key is None:
        key = get_encryption_key("archive")
        
    try:
        # 生成随机IV（初始化向量）
        iv = secrets.token_bytes(16)
        
        # 创建加密器
        backend = default_backend()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()
        
        # 创建填充器
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        
        # 读取原始文件并加密
        with open(file_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            # 写入IV
            f_out.write(iv)
            
            # 写入元数据 (JSON格式)
            metadata = {
                "filename": file_path.name,
                "encrypted_at": datetime.datetime.now().isoformat(),
                "algorithm": "AES-256-CBC",
                "version": "1.0"
            }
            metadata_json = json.dumps(metadata).encode('utf-8')
            metadata_length = len(metadata_json).to_bytes(4, byteorder='big')
            
            # 加密并写入元数据
            padded_metadata = padder.update(metadata_json) + padder.finalize()
            encrypted_metadata = encryptor.update(padded_metadata)
            
            # 写入元数据长度和加密的元数据
            f_out.write(metadata_length)
            f_out.write(encrypted_metadata)
            
            # 重置加密器和填充器
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            
            # 分块读取和加密文件内容
            while True:
                chunk = f_in.read(64 * 1024)  # 64KB 块
                if not chunk:
                    break
                    
                # 对最后一块进行填充
                if len(chunk) < 64 * 1024:
                    padded_chunk = padder.update(chunk) + padder.finalize()
                else:
                    padded_chunk = padder.update(chunk)
                    
                encrypted_chunk = encryptor.update(padded_chunk)
                if encrypted_chunk:
                    f_out.write(encrypted_chunk)
                    
            # 写入最后的加密块
            final_chunk = encryptor.finalize()
            if final_chunk:
                f_out.write(final_chunk)
                
        logger.info(f"文件加密成功: {output_path}")
        
        # 如果需要，删除原始文件
        if delete_original:
            file_path.unlink()
            logger.info(f"已删除原始文件: {file_path}")
            
        return output_path
        
    except Exception as e:
        logger.error(f"加密文件时出错: {str(e)}")
        # 如果输出文件已创建，删除它
        if output_path.exists():
            try:
                output_path.unlink()
            except:
                pass
        return None

def decrypt_file(file_path: Union[str, Path], 
                key: Optional[bytes] = None,
                output_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    解密文件
    
    解密使用AES-256加密的文件
    
    Args:
        file_path: 要解密的文件路径
        key: 解密密钥，如果为None则使用默认密钥
        output_path: 输出文件路径，如果为None则移除.enc后缀
        
    Returns:
        解密后的文件路径，如果失败则返回None
    """
    if not check_crypto_available():
        logger.error("加密功能不可用，无法解密文件")
        return None
        
    file_path = Path(file_path)
    
    # 确保文件存在
    if not file_path.exists():
        logger.error(f"要解密的文件不存在: {file_path}")
        return None
        
    # 设置输出路径
    if output_path is None:
        # 如果文件以.enc结尾，去掉后缀
        if file_path.suffix == ".enc":
            output_path = file_path.with_suffix("")
        else:
            stem = file_path.stem
            suffix = file_path.suffix
            output_path = file_path.with_name(f"{stem}_decrypted{suffix}")
    else:
        output_path = Path(output_path)
        
    # 使用默认密钥（如果未提供）
    if key is None:
        key = get_encryption_key("archive")
        
    try:
        with open(file_path, 'rb') as f_in:
            # 读取IV
            iv = f_in.read(16)
            
            # 读取元数据长度
            metadata_length = int.from_bytes(f_in.read(4), byteorder='big')
            
            # 创建解密器
            backend = default_backend()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            
            # 创建解填充器
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            
            # 解密元数据
            encrypted_metadata = f_in.read(metadata_length + 16)  # 加上填充
            decrypted_metadata = decryptor.update(encrypted_metadata)
            
            try:
                # 解填充元数据
                unpadded_metadata = unpadder.update(decrypted_metadata) + unpadder.finalize()
                metadata = json.loads(unpadded_metadata.decode('utf-8'))
                logger.debug(f"解密文件元数据: {metadata}")
            except Exception as e:
                logger.warning(f"无法解析文件元数据: {str(e)}")
            
            # 重置解密器和解填充器
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            
            # 解密文件内容
            with open(output_path, 'wb') as f_out:
                while True:
                    chunk = f_in.read(64 * 1024 + 16)  # 64KB块 + 可能的填充
                    if not chunk:
                        break
                        
                    decrypted_chunk = decryptor.update(chunk)
                    
                    # 对最后一块进行解填充
                    if len(chunk) < 64 * 1024 + 16:
                        try:
                            unpadded_chunk = unpadder.update(decrypted_chunk) + unpadder.finalize()
                        except ValueError:
                            # 如果解填充失败，可能是密钥错误
                            logger.error("解密失败：密钥不正确或文件已损坏")
                            output_path.unlink()
                            return None
                    else:
                        unpadded_chunk = unpadder.update(decrypted_chunk)
                        
                    f_out.write(unpadded_chunk)
                    
                # 写入最后的解密数据
                final_chunk = decryptor.finalize()
                if final_chunk:
                    f_out.write(final_chunk)
                    
        logger.info(f"文件解密成功: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"解密文件时出错: {str(e)}")
        # 如果输出文件已创建，删除它
        if output_path.exists():
            try:
                output_path.unlink()
            except:
                pass
        return None

def find_old_logs(days: int = 30, include_pattern: str = "*.log*") -> List[Path]:
    """
    查找需要加密的旧日志文件
    
    Args:
        days: 超过多少天的日志视为旧日志
        include_pattern: 文件匹配模式
        
    Returns:
        旧日志文件列表
    """
    log_dir = get_log_directory()
    archive_dir = get_archived_logs_directory()
    
    # 确保归档目录存在
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 计算截止时间
    cutoff_time = time.time() - (days * 86400)
    
    # 查找所有符合条件的日志文件
    old_logs = []
    
    # 递归遍历所有日志文件
    for log_file in log_dir.glob(f"**/{include_pattern}"):
        if (log_file.is_file() and
            log_file.stat().st_mtime < cutoff_time and
            # 排除已加密和已归档的文件
            not log_file.name.endswith(".enc") and
            not str(log_file).startswith(str(archive_dir))):
            old_logs.append(log_file)
            
    return old_logs

def encrypt_archived_logs(days: int = 30, delete_original: bool = True) -> Dict[str, str]:
    """
    加密所有符合条件的归档日志
    
    Args:
        days: 超过多少天的日志需要加密
        delete_original: 是否删除原始文件
        
    Returns:
        加密结果字典 {原始文件: 加密文件/错误信息}
    """
    # 查找旧日志
    old_logs = find_old_logs(days)
    
    # 获取归档目录
    archive_dir = get_archived_logs_directory()
    
    results = {}
    for log_file in old_logs:
        try:
            # 创建目标路径（保持相对路径结构）
            rel_path = log_file.relative_to(get_log_directory())
            target_dir = archive_dir / rel_path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 加密文件路径
            encrypted_file = target_dir / f"{log_file.name}.enc"
            
            # 加密文件
            result = encrypt_file(log_file, output_path=encrypted_file, delete_original=delete_original)
            
            if result:
                results[str(log_file)] = str(result)
            else:
                results[str(log_file)] = "加密失败"
                
        except Exception as e:
            logger.error(f"处理日志文件 {log_file} 时出错: {str(e)}")
            results[str(log_file)] = f"错误: {str(e)}"
            
    return results
    
def decrypt_log_archive(archive_path: Union[str, Path], 
                       output_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """
    解密日志归档文件
    
    Args:
        archive_path: 归档文件路径
        output_dir: 输出目录
        
    Returns:
        解密后的目录路径
    """
    archive_path = Path(archive_path)
    
    # 默认输出到临时目录
    if output_dir is None:
        output_dir = get_log_directory() / "temp" / f"decrypted_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        output_dir = Path(output_dir)
        
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 解密文件
        decrypted_path = decrypt_file(archive_path, output_path=output_dir / archive_path.stem)
        
        if decrypted_path:
            logger.info(f"归档日志解密成功: {decrypted_path}")
            return decrypted_path
        else:
            logger.error(f"无法解密归档日志: {archive_path}")
            return None
            
    except Exception as e:
        logger.error(f"解密归档日志时出错: {str(e)}")
        return None

if __name__ == "__main__":
    # 测试加密/解密功能
    import time
    
    logger.info("测试日志加密模块")
    
    # 检查加密库
    if check_crypto_available():
        logger.info("加密库可用")
        
        # 创建测试文件
        test_file = Path("test_log.txt")
        with open(test_file, "w") as f:
            f.write(f"这是一个测试日志文件\n创建时间: {datetime.datetime.now().isoformat()}\n")
            for i in range(100):
                f.write(f"日志行 {i}: 这是一些测试内容 {secrets.token_hex(8)}\n")
                
        logger.info(f"创建测试文件: {test_file}")
        
        # 加密文件
        encrypted_file = encrypt_file(test_file, delete_original=False)
        logger.info(f"加密后的文件: {encrypted_file}")
        
        # 等待一秒
        time.sleep(1)
        
        # 解密文件
        decrypted_file = decrypt_file(encrypted_file)
        logger.info(f"解密后的文件: {decrypted_file}")
        
        # 清理测试文件
        test_file.unlink(missing_ok=True)
        encrypted_file.unlink(missing_ok=True)
        decrypted_file.unlink(missing_ok=True)
        
        logger.info("测试完成，所有测试文件已清理")
    else:
        logger.error("加密库不可用，无法进行测试") 