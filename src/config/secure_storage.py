#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置安全存储模块

负责配置文件的加密和解密，保护敏感的配置信息。
支持AES-GCM和ChaCha20-Poly1305加密算法，提供安全的配置存储机制。
"""

import os
import sys
import json
import base64
import logging
import yaml
import hashlib
import secrets
import getpass
from typing import Dict, Any, Optional, Union, Tuple, List
from pathlib import Path
from datetime import datetime

# 导入加密库
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# 获取项目根目录
root_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ''))
sys.path.insert(0, root_dir)

try:
    from src.utils.log_handler import get_logger
    from src.config.path_resolver import resolve_special_path, normalize_path
except ImportError:
    # 简单日志设置
    logging.basicConfig(level=logging.INFO)
    
    def get_logger(name):
        return logging.getLogger(name)
    
    def resolve_special_path(path):
        return os.path.abspath(os.path.expanduser(path))
    
    def normalize_path(path):
        return os.path.abspath(path)

# 日志记录器
logger = get_logger("secure_storage")

# 常量定义
DEFAULT_KDF_ITERATIONS = 100000
DEFAULT_SALT_SIZE = 16
DEFAULT_KEY_SIZE = 32
DEFAULT_NONCE_SIZE = 12
ENCRYPTION_METADATA_TAG = "__encrypted__"
DEFAULT_ENCRYPTION_ALGORITHM = "AES-GCM"

# 环境变量名
ENV_MASTER_KEY = "VISIONAI_MASTER_KEY"
ENV_SALT = "VISIONAI_SALT"

class EncryptionError(Exception):
    """加密错误异常"""
    pass

class DecryptionError(Exception):
    """解密错误异常"""
    pass

class ConfigSecurityError(Exception):
    """配置安全错误异常"""
    pass

class SecureStorage:
    """安全存储类，负责配置的加密和解密"""
    
    def __init__(self, 
                 master_key: Optional[str] = None, 
                 salt: Optional[bytes] = None,
                 algorithm: str = DEFAULT_ENCRYPTION_ALGORITHM,
                 key_file: Optional[str] = None):
        """
        初始化安全存储
        
        Args:
            master_key: 主密钥，如果为None则尝试从环境变量获取
            salt: 盐值，用于密钥派生，如果为None则生成随机盐
            algorithm: 加密算法，支持 'AES-GCM' 和 'ChaCha20-Poly1305'
            key_file: 密钥文件路径，如果提供则从文件读取密钥
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("加密库未安装，安全存储功能无法使用。请执行 'pip install cryptography'")
            return
        
        self.algorithm = algorithm
        
        if key_file:
            # 从密钥文件加载
            master_key, salt = self._load_from_key_file(key_file)
        
        # 获取主密钥
        self.master_key = master_key or os.environ.get(ENV_MASTER_KEY)
        if not self.master_key:
            logger.debug("主密钥未提供，将使用默认密钥")
            self.master_key = self._get_default_master_key()
        
        # 获取盐值
        self.salt = salt
        if not self.salt:
            env_salt = os.environ.get(ENV_SALT)
            if env_salt:
                try:
                    self.salt = base64.b64decode(env_salt)
                except:
                    self.salt = self._generate_machine_salt()
            else:
                self.salt = self._generate_machine_salt()
        
        # 派生加密密钥
        self.key = self._derive_key(self.master_key.encode('utf-8'), self.salt)
        
        # 创建加密对象
        if self.algorithm == "AES-GCM":
            self.cipher = AESGCM(self.key)
        elif self.algorithm == "ChaCha20-Poly1305":
            self.cipher = ChaCha20Poly1305(self.key)
        else:
            raise ValueError(f"不支持的加密算法：{self.algorithm}")
        
        logger.debug(f"安全存储初始化完成，使用 {self.algorithm} 加密算法")
    
    def _get_default_master_key(self) -> str:
        """获取默认主密钥"""
        # 使用机器ID和用户名生成一个机器特定的默认密钥
        machine_id = self._get_machine_id()
        username = getpass.getuser()
        
        # 固定的应用程序盐值 - 确保不同运行之间使用相同的密钥
        app_salt = "VisionAI-ClipsMaster-2023-Static-Salt"
        
        # 混合生成密钥
        combined = f"{machine_id}:{username}:{app_salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _get_machine_id(self) -> str:
        """获取机器ID"""
        try:
            if sys.platform == 'win32':
                import subprocess
                try:
                    result = subprocess.check_output('wmic csproduct get uuid').decode()
                    uuid = [x.strip() for x in result.split('\n') if x.strip()][-1]
                    return uuid
                except:
                    # 使用磁盘序列号作为备选方案
                    try:
                        result = subprocess.check_output('wmic diskdrive get serialnumber').decode()
                        serial = [x.strip() for x in result.split('\n') if x.strip()][-1]
                        return serial
                    except:
                        # 如果都失败，使用注册表中的MachineGuid
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
                        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                        winreg.CloseKey(key)
                        return machine_guid
            elif sys.platform in ['linux', 'linux2']:
                # 尝试多种方法获取Linux机器ID
                id_files = [
                    '/etc/machine-id',
                    '/var/lib/dbus/machine-id',
                    '/sys/class/dmi/id/product_uuid'
                ]
                for id_file in id_files:
                    if os.path.exists(id_file):
                        with open(id_file, 'r') as f:
                            return f.read().strip()
                
                # 如果上述方法都失败，使用主机名
                import socket
                return socket.gethostname()
            elif sys.platform == 'darwin':
                # macOS系统
                from subprocess import Popen, PIPE
                try:
                    # 尝试获取硬件UUID
                    proc = Popen(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'], stdout=PIPE)
                    output = proc.communicate()[0]
                    return output.decode().split('IOPlatformUUID')[1].split('\n')[0].replace('</string>', '').replace('"', '').strip()
                except:
                    # 如果失败，使用主机名
                    import socket
                    return socket.gethostname()
            else:
                # 其他系统使用主机名和用户主目录
                import socket
                hostname = socket.gethostname()
                home_dir = os.path.expanduser('~')
                return hashlib.md5(f"{hostname}:{home_dir}".encode()).hexdigest()
        except:
            # 如果所有方法都失败，使用一个固定值与当前用户结合
            try:
                username = getpass.getuser()
                return hashlib.md5(f"VisionAI-ClipsMaster-Static:{username}".encode()).hexdigest()
            except:
                # 最后的后备方案
                return "VisionAI-ClipsMaster-Static-ID-Fixed-For-All-Users"
    
    def _generate_machine_salt(self) -> bytes:
        """生成基于机器ID的固定盐值，确保同一台机器上的盐值一致"""
        machine_id = self._get_machine_id()
        username = getpass.getuser()
        fixed_str = f"VisionAI-ClipsMaster-Salt-{machine_id}-{username}"
        return hashlib.sha256(fixed_str.encode()).digest()[:DEFAULT_SALT_SIZE]
    
    def _derive_key(self, password: bytes, salt: bytes) -> bytes:
        """
        使用PBKDF2派生密钥
        
        Args:
            password: 密码
            salt: 盐值
            
        Returns:
            派生的密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=DEFAULT_KEY_SIZE,
            salt=salt,
            iterations=DEFAULT_KDF_ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password)
    
    def _load_from_key_file(self, key_file: str) -> Tuple[str, bytes]:
        """
        从密钥文件加载主密钥和盐值
        
        Args:
            key_file: 密钥文件路径
            
        Returns:
            Tuple[str, bytes]: 主密钥和盐值
        """
        try:
            path = resolve_special_path(key_file)
            with open(path, 'r') as f:
                key_data = json.load(f)
                master_key = key_data.get('master_key')
                salt = base64.b64decode(key_data.get('salt'))
                return master_key, salt
        except Exception as e:
            logger.error(f"从密钥文件加载失败: {str(e)}")
            raise ConfigSecurityError(f"密钥文件加载失败: {str(e)}")
    
    def save_key_file(self, key_file: str, overwrite: bool = False) -> None:
        """
        保存密钥到文件
        
        Args:
            key_file: 密钥文件路径
            overwrite: 是否覆盖现有文件
        """
        path = resolve_special_path(key_file)
        if os.path.exists(path) and not overwrite:
            raise ConfigSecurityError(f"密钥文件已存在: {path}")
        
        key_data = {
            'master_key': self.master_key,
            'salt': base64.b64encode(self.salt).decode('utf-8'),
            'algorithm': self.algorithm,
            'created_at': datetime.now().isoformat(),
            'key_type': 'visionai-encryption-key'
        }
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # 写入文件，限制权限
            with open(path, 'w') as f:
                json.dump(key_data, f, indent=2)
            
            # 设置文件权限（仅限UNIX系统）
            if sys.platform != 'win32':
                os.chmod(path, 0o600)
            
            logger.info(f"密钥文件已保存到: {path}")
        except Exception as e:
            logger.error(f"保存密钥文件失败: {str(e)}")
            raise ConfigSecurityError(f"保存密钥文件失败: {str(e)}")
    
    def encrypt(self, data: bytes, aad: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        加密数据
        
        Args:
            data: 要加密的数据
            aad: 附加验证数据(AAD)
            
        Returns:
            Tuple[bytes, bytes]: 加密数据和随机数
        """
        if not CRYPTO_AVAILABLE:
            logger.error("加密库未安装，无法进行加密")
            raise EncryptionError("加密库未安装")
        
        # 生成随机数
        nonce = secrets.token_bytes(DEFAULT_NONCE_SIZE)
        
        try:
            # 加密数据
            aad_data = aad or b""
            encrypted_data = self.cipher.encrypt(nonce, data, aad_data)
            return encrypted_data, nonce
        except Exception as e:
            logger.error(f"加密数据失败: {str(e)}")
            raise EncryptionError(f"加密失败: {str(e)}")
    
    def decrypt(self, encrypted_data: bytes, nonce: bytes, aad: Optional[bytes] = None) -> bytes:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据
            nonce: 随机数
            aad: 附加验证数据(AAD)
            
        Returns:
            解密后的数据
        """
        if not CRYPTO_AVAILABLE:
            logger.error("加密库未安装，无法进行解密")
            raise DecryptionError("加密库未安装")
        
        try:
            aad_data = aad or b""
            logger.debug(f"解密: 数据长度={len(encrypted_data)}字节, nonce长度={len(nonce)}字节")
            decrypted_data = self.cipher.decrypt(nonce, encrypted_data, aad_data)
            return decrypted_data
        except Exception as e:
            logger.error(f"解密数据失败: {type(e).__name__} - {str(e)}")
            # 尝试使用不同的方法重新解密
            try:
                if isinstance(self.cipher, AESGCM) and len(nonce) == DEFAULT_NONCE_SIZE:
                    # 记录详细信息以便调试
                    logger.debug(f"尝试替代解密方法: 算法={self.algorithm}, 密钥长度={len(self.key)}字节")
                    decrypted_data = self.cipher.decrypt(nonce, encrypted_data, aad_data)
                    return decrypted_data
            except Exception as e2:
                logger.error(f"替代解密方法也失败: {type(e2).__name__} - {str(e2)}")
            
            raise DecryptionError(f"解密失败: {type(e).__name__} - {str(e)}")
    
    def encrypt_config_value(self, value: str) -> Dict[str, str]:
        """
        加密单个配置值
        
        Args:
            value: 要加密的值
            
        Returns:
            包含加密信息的字典
        """
        if not value or not isinstance(value, str):
            return value
        
        try:
            # 将值转换为字节
            value_bytes = value.encode('utf-8')
            
            # 加密
            encrypted_data, nonce = self.encrypt(value_bytes)
            
            # 转换为Base64编码
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            nonce_b64 = base64.b64encode(nonce).decode('utf-8')
            
            # 返回加密信息
            return {
                ENCRYPTION_METADATA_TAG: True,
                "algorithm": self.algorithm,
                "data": encrypted_b64,
                "nonce": nonce_b64
            }
        except Exception as e:
            logger.error(f"加密配置值失败: {str(e)}")
            # 返回原始值，避免加密失败导致数据丢失
            return value
    
    def decrypt_config_value(self, encrypted_value: Dict[str, Any]) -> str:
        """
        解密配置值
        
        Args:
            encrypted_value: 加密的配置值
            
        Returns:
            解密后的值
        """
        # 如果不是字典或不是加密值，直接返回
        if not isinstance(encrypted_value, dict) or not encrypted_value.get(ENCRYPTION_METADATA_TAG):
            return encrypted_value
        
        try:
            # 获取加密数据和随机数
            encrypted_data = base64.b64decode(encrypted_value["data"])
            nonce = base64.b64decode(encrypted_value["nonce"])
            
            # 如果算法不匹配，记录警告
            if encrypted_value.get("algorithm") != self.algorithm:
                logger.warning(f"算法不匹配，期望 {self.algorithm}，实际 {encrypted_value.get('algorithm')}")
            
            # 解密
            decrypted_data = self.decrypt(encrypted_data, nonce)
            
            # 转换为字符串
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"解密配置值失败: {str(e)}")
            # 返回一个标记解密失败的值
            return f"[解密失败: {type(e).__name__}]"

def encrypt_sensitive_fields(config: Dict[str, Any],
                            sensitive_paths: Optional[List[str]] = None,
                            master_key: Optional[str] = None,
                            key_file: Optional[str] = None) -> Dict[str, Any]:
    """
    加密配置中的敏感字段
    
    Args:
        config: 配置字典
        sensitive_paths: 敏感字段路径列表(点分隔)，例如 ["cloud.api_key", "database.password"]
        master_key: 可选的主密钥
        key_file: 可选的密钥文件路径
    
    Returns:
        Dict[str, Any]: 包含已加密字段的配置
    """
    # 默认敏感字段列表
    default_sensitive_paths = [
        "cloud.api_key",
        "cloud.secret_key",
        "cloud.access_token",
        "database.password",
        "auth.secret",
        "api.key",
        "service.credentials",
        "credentials.password",
        "smtp.password"
    ]
    
    paths_to_encrypt = sensitive_paths or default_sensitive_paths
    
    # 创建安全存储实例
    secure = SecureStorage(master_key=master_key, key_file=key_file)
    
    # 创建配置副本
    encrypted_config = config.copy()
    
    # 加密指定的敏感字段
    for path in paths_to_encrypt:
        try:
            _encrypt_path(encrypted_config, path, secure)
        except Exception as e:
            logger.warning(f"加密路径 {path} 失败: {str(e)}")
    
    return encrypted_config

def decrypt_sensitive_fields(config: Dict[str, Any],
                           master_key: Optional[str] = None,
                           key_file: Optional[str] = None) -> Dict[str, Any]:
    """
    解密配置中的敏感字段
    
    Args:
        config: 配置字典
        master_key: 可选的主密钥
        key_file: 可选的密钥文件路径
    
    Returns:
        Dict[str, Any]: 解密后的配置
    """
    # 创建安全存储实例
    secure = SecureStorage(master_key=master_key, key_file=key_file)
    
    # 创建配置副本
    decrypted_config = config.copy()
    
    # 递归解密所有字段
    _decrypt_recursive(decrypted_config, secure)
    
    return decrypted_config

def _encrypt_path(config: Dict[str, Any], path: str, secure: SecureStorage) -> None:
    """
    加密指定路径的值
    
    Args:
        config: 配置字典
        path: 字段路径(点分隔)
        secure: 安全存储实例
    """
    parts = path.split('.')
    current = config
    
    # 导航到倒数第二级
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            # 路径不存在或不是字典，创建空字典
            current[part] = {}
        current = current[part]
    
    # 获取最后一个键
    last_key = parts[-1]
    
    # 如果键存在且值不为空，则加密
    if last_key in current and current[last_key]:
        value = current[last_key]
        if isinstance(value, str):
            current[last_key] = secure.encrypt_config_value(value)
        else:
            logger.warning(f"无法加密非字符串值: {path}")

def _decrypt_recursive(obj: Any, secure: SecureStorage) -> None:
    """
    递归解密对象中的所有加密字段
    
    Args:
        obj: 要解密的对象
        secure: 安全存储实例
    """
    if isinstance(obj, dict):
        # 检查当前对象是否是加密值
        if ENCRYPTION_METADATA_TAG in obj and obj.get(ENCRYPTION_METADATA_TAG) is True:
            try:
                return secure.decrypt_config_value(obj)
            except Exception as e:
                logger.error(f"解密失败: {str(e)}")
                return obj  # 保留原始加密值
        
        # 处理字典的每个值
        for key, value in list(obj.items()):
            if isinstance(value, dict):
                if ENCRYPTION_METADATA_TAG in value and value.get(ENCRYPTION_METADATA_TAG) is True:
                    # 这是一个加密值，解密
                    try:
                        obj[key] = secure.decrypt_config_value(value)
                    except Exception as e:
                        logger.error(f"解密字段 {key} 失败: {str(e)}")
                        # 保留原始加密值
                else:
                    # 递归处理嵌套字典
                    _decrypt_recursive(value, secure)
            elif isinstance(value, list):
                # 递归处理列表
                for i, item in enumerate(value):
                    if isinstance(item, dict) and ENCRYPTION_METADATA_TAG in item and item.get(ENCRYPTION_METADATA_TAG) is True:
                        try:
                            value[i] = secure.decrypt_config_value(item)
                        except Exception as e:
                            logger.error(f"解密列表项 {i} 失败: {str(e)}")
                            # 保留原始加密值
                    elif isinstance(item, (dict, list)):
                        _decrypt_recursive(item, secure)

def secure_load_config(config_file: str, 
                       master_key: Optional[str] = None,
                       key_file: Optional[str] = None) -> Dict[str, Any]:
    """
    安全加载配置文件，自动解密敏感字段
    
    Args:
        config_file: 配置文件路径
        master_key: 可选的主密钥
        key_file: 可选的密钥文件路径
    
    Returns:
        Dict[str, Any]: 加载并解密后的配置
    """
    file_path = resolve_special_path(config_file)
    if not os.path.exists(file_path):
        logger.error(f"配置文件不存在: {file_path}")
        return {}
    
    try:
        # 读取配置文件
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                config = json.load(f)
            elif file_path.endswith(('.yaml', '.yml')):
                config = yaml.safe_load(f)
            else:
                logger.error(f"不支持的配置文件格式: {file_path}")
                return {}
        
        # 解密配置
        return decrypt_sensitive_fields(config, master_key, key_file)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}

def secure_save_config(config: Dict[str, Any], 
                       config_file: str,
                       sensitive_paths: Optional[List[str]] = None,
                       master_key: Optional[str] = None,
                       key_file: Optional[str] = None) -> bool:
    """
    安全保存配置，自动加密敏感字段
    
    Args:
        config: 配置字典
        config_file: 配置文件路径
        sensitive_paths: 敏感字段路径列表
        master_key: 可选的主密钥
        key_file: 可选的密钥文件路径
    
    Returns:
        bool: 是否成功保存
    """
    file_path = resolve_special_path(config_file)
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 加密敏感字段
        encrypted_config = encrypt_sensitive_fields(config, sensitive_paths, master_key, key_file)
        
        # 保存配置
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                json.dump(encrypted_config, f, indent=2, ensure_ascii=False)
            elif file_path.endswith(('.yaml', '.yml')):
                yaml.dump(encrypted_config, f, default_flow_style=False, allow_unicode=True)
            else:
                logger.error(f"不支持的配置文件格式: {file_path}")
                return False
        
        logger.info(f"配置已安全保存到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

def generate_key_file(key_file: str, overwrite: bool = False) -> bool:
    """
    生成新的密钥文件
    
    Args:
        key_file: 密钥文件路径
        overwrite: 是否覆盖现有文件
        
    Returns:
        bool: 是否成功生成
    """
    try:
        # 创建安全存储实例（使用随机生成的密钥）
        master_key = secrets.token_hex(32)
        secure = SecureStorage(master_key=master_key)
        
        # 保存密钥文件
        secure.save_key_file(key_file, overwrite)
        
        return True
    except Exception as e:
        logger.error(f"生成密钥文件失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 示例用法
    try:
        # 创建测试配置
        test_config = {
            "app_name": "VisionAI-ClipsMaster",
            "version": "1.0.0",
            "cloud": {
                "api_key": "sk_test_abcdefg123456789",
                "endpoint": "https://api.example.com/v1"
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "user": "postgres",
                "password": "super_secret_password"
            },
            "auth": {
                "secret": "jwt_secret_key_here",
                "expire_days": 30
            }
        }
        
        print("原始配置:")
        print(json.dumps(test_config, indent=2))
        
        # 加密敏感字段
        encrypted_config = encrypt_sensitive_fields(test_config)
        
        print("\n加密后的配置:")
        print(json.dumps(encrypted_config, indent=2))
        
        # 解密配置
        decrypted_config = decrypt_sensitive_fields(encrypted_config)
        
        print("\n解密后的配置:")
        print(json.dumps(decrypted_config, indent=2))
        
        # 验证原始配置和解密后的配置是否相同
        assert test_config == decrypted_config, "解密结果与原始配置不匹配!"
        print("\n✓ 加密/解密测试通过!")
        
        # 保存和加载测试
        test_file = os.path.join(root_dir, "configs", "test_secure_config.json")
        secure_save_config(test_config, test_file)
        loaded_config = secure_load_config(test_file)
        
        print(f"\n配置已保存到: {test_file}")
        print("重新加载的配置:")
        print(json.dumps(loaded_config, indent=2))
        
        # 生成密钥文件测试
        key_file = os.path.join(root_dir, "configs", "encryption_key.json")
        if generate_key_file(key_file, overwrite=True):
            print(f"\n✓ 密钥文件已生成: {key_file}")
        
    except Exception as e:
        print(f"测试失败: {str(e)}") 