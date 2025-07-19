#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置安全存储演示脚本

展示如何使用配置安全存储模块加密和解密敏感配置信息。
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
import pprint
import getpass
import datetime
import base64

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# 导入安全存储模块
from src.config.secure_storage import (
    SecureStorage,
    encrypt_sensitive_fields,
    decrypt_sensitive_fields,
    secure_save_config,
    secure_load_config,
    generate_key_file
)

# 导入日志工具
try:
    from src.utils.log_handler import get_logger
    logger = get_logger("secure_storage_demo")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("secure_storage_demo")

# 配置文件路径
CONFIG_DIR = os.path.join(root_dir, "configs")
SAMPLE_DIR = os.path.join(CONFIG_DIR, "samples")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def create_sample_config():
    """创建示例配置文件"""
    # 常规配置
    sample_config = {
        "app_name": "VisionAI-ClipsMaster",
        "version": "3.0",
        "processing": {
            "threads": 4,
            "max_memory": 2048,
            "temp_dir": "D:/temp/visionai"
        },
        "ui": {
            "theme": "dark",
            "language": "zh_CN",
            "font_size": 12
        },
        # 敏感信息
        "cloud": {
            "provider": "azure",
            "region": "east-asia",
            "api_key": "sk-Aslk291ksjKDikmsP01dkLKsjdkaLMnw",
            "secret_key": "siJ1nslwpoeR3smn31LpQmzlsPK231ns",
            "endpoint": "https://api.cognitive.azure.com/vision/v3.0"
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "user": "visionai_user",
            "password": "Abcd@1234!VerySecureP@ssw0rd"
        },
        "auth": {
            "method": "jwt",
            "secret": "Jsp2k3nmLpoa92KLnm20sklJNnslwp",
            "expire_days": 30
        },
        "api": {
            "key": "vai-Kls29kal1LKjsw01msnK",
            "rate_limit": 100,
            "cache_ttl": 300
        }
    }
    
    # 写入示例配置文件
    config_file = os.path.join(SAMPLE_DIR, "sample_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    logger.info(f"创建示例配置文件: {config_file}")
    return sample_config, config_file


def demonstrate_field_encryption(config):
    """演示字段级加密"""
    print("\n字段级加密演示")
    print("=" * 60)
    
    # 指定敏感字段路径
    sensitive_fields = [
        "cloud.api_key",
        "cloud.secret_key",
        "database.password",
        "auth.secret",
        "api.key"
    ]
    
    # 创建SecureStorage实例 - 使用固定密钥用于演示
    fixed_demo_key = "demo-key-123456789-for-testing-only"
    secure = SecureStorage(master_key=fixed_demo_key)
    
    # 加密指定字段
    print("\n1. 加密前的配置值:")
    for field in sensitive_fields:
        parts = field.split('.')
        value = config
        for part in parts:
            value = value.get(part, {})
        print(f"  {field}: {value}")
    
    # 加密配置
    encrypted_config = encrypt_sensitive_fields(config, sensitive_fields, master_key=fixed_demo_key)
    
    print("\n2. 加密后的配置值:")
    for field in sensitive_fields:
        parts = field.split('.')
        temp = encrypted_config
        for part in parts:
            temp = temp.get(part, {})
        
        if isinstance(temp, dict) and temp.get("__encrypted__") is True:
            print(f"  {field}: {temp}")
    
    # 解密配置
    decrypted_config = decrypt_sensitive_fields(encrypted_config, master_key=fixed_demo_key)
    
    print("\n3. 解密后的配置值:")
    for field in sensitive_fields:
        parts = field.split('.')
        value = decrypted_config
        for part in parts:
            value = value.get(part, {})
        print(f"  {field}: {value}")
    
    # 验证与原始配置相同
    for field in sensitive_fields:
        parts = field.split('.')
        original = config
        decrypted = decrypted_config
        for part in parts:
            original = original.get(part, {})
            decrypted = decrypted.get(part, {})
        
        if original == decrypted:
            print(f"  ✓ 字段 {field} 加密解密验证通过")
        else:
            print(f"  ✗ 字段 {field} 加密解密验证失败")
    
    return encrypted_config, decrypted_config


def demonstrate_key_file(config):
    """演示密钥文件使用"""
    print("\n密钥文件使用演示")
    print("=" * 60)
    
    # 创建固定的密钥和盐值用于演示
    fixed_master_key = "demo-key-file-testing-123456"
    
    # 生成密钥文件
    key_file = os.path.join(SAMPLE_DIR, "encryption.key")
    print(f"\n1. 生成密钥文件: {key_file}")
    
    # 手动创建密钥文件
    key_data = {
        'master_key': fixed_master_key,
        'salt': base64.b64encode(b"demo-salt-12345678").decode('utf-8'),
        'algorithm': "AES-GCM",
        'created_at': datetime.datetime.now().isoformat(),
        'key_type': 'visionai-encryption-key'
    }
    
    # 确保目录存在
    os.makedirs(os.path.dirname(key_file), exist_ok=True)
    
    # 写入文件
    with open(key_file, 'w') as f:
        json.dump(key_data, f, indent=2)
    
    print("  密钥文件已创建")
    
    # 使用密钥文件加密
    print("\n2. 使用密钥文件加密配置")
    test_config = {
        "api_key": "test-api-key-for-key-file-demo",
        "secret": "test-secret-value"
    }
    
    encrypted_with_key = encrypt_sensitive_fields(
        test_config, 
        sensitive_paths=["api_key"],
        key_file=key_file
    )
    
    # 使用相同密钥文件解密
    print("\n3. 使用相同密钥文件解密配置")
    decrypted_with_key = decrypt_sensitive_fields(
        encrypted_with_key,
        key_file=key_file
    )
    
    # 验证
    if test_config["api_key"] == decrypted_with_key["api_key"]:
        print("  ✓ 使用密钥文件加密解密验证通过")
    else:
        print("  ✗ 使用密钥文件加密解密验证失败")
    
    # 再次创建不同的密钥文件
    alt_key_file = os.path.join(SAMPLE_DIR, "encryption_alt.key")
    print(f"\n4. 生成另一个密钥文件: {alt_key_file}")
    
    # 手动创建不同的密钥文件
    alt_key_data = {
        'master_key': "different-key-for-testing",
        'salt': base64.b64encode(b"other-salt-87654321").decode('utf-8'),
        'algorithm': "AES-GCM",
        'created_at': datetime.datetime.now().isoformat(),
        'key_type': 'visionai-encryption-key'
    }
    
    # 写入文件
    with open(alt_key_file, 'w') as f:
        json.dump(alt_key_data, f, indent=2)
    
    print("  另一个密钥文件已创建")
    
    # 尝试使用不同密钥解密
    print("\n5. 尝试使用不同密钥文件解密配置")
    try:
        decrypted_wrong = decrypt_sensitive_fields(encrypted_with_key, key_file=alt_key_file)
        if isinstance(decrypted_wrong["api_key"], str) and decrypted_wrong["api_key"].startswith("[解密失败"):
            print("  ✓ 使用不同密钥解密失败并返回错误标记")
        else:
            print("  ✗ 使用不同密钥仍能解密 - 这是错误的行为")
    except Exception as e:
        print(f"  ✓ 使用不同密钥解密失败，这是预期行为: {type(e).__name__}")
    
    return key_file


def demonstrate_config_file_operations(config, key_file):
    """演示配置文件操作"""
    print("\n配置文件加密保存和加载演示")
    print("=" * 60)
    
    # 创建简单配置用于演示
    test_config = {
        "app": "secure-config-test",
        "api_key": "file-demo-api-key-123",
        "password": "file-demo-password-456",
        "endpoint": "https://api.example.com/v1"
    }
    
    # 保存加密的配置文件
    secure_config_file = os.path.join(SAMPLE_DIR, "secure_config.json")
    print(f"\n1. 保存加密配置到文件: {secure_config_file}")
    
    # 指定敏感字段路径
    sensitive_paths = ["api_key", "password"]
    
    # 保存配置
    success = secure_save_config(
        test_config,
        secure_config_file,
        sensitive_paths=sensitive_paths,
        key_file=key_file
    )
    
    if success:
        print("  ✓ 配置已安全保存")
    else:
        print("  ✗ 配置保存失败")
    
    # 直接读取加密文件
    print("\n2. 直接查看加密文件内容")
    try:
        with open(secure_config_file, 'r', encoding='utf-8') as f:
            encrypted_content = json.load(f)
        
        # 检查敏感字段是否已加密
        for path in sensitive_paths:
            value = encrypted_content.get(path)
            
            if isinstance(value, dict) and value.get("__encrypted__") is True:
                print(f"  ✓ 字段 {path} 已被加密")
            else:
                print(f"  ✗ 字段 {path} 未被加密")
    except Exception as e:
        print(f"  ✗ 读取加密文件失败: {str(e)}")
    
    # 安全加载配置
    print("\n3. 安全加载加密的配置文件")
    loaded_config = secure_load_config(secure_config_file, key_file=key_file)
    
    # 验证加载的配置是否正确
    if loaded_config:
        for path in sensitive_paths:
            original = test_config.get(path)
            loaded = loaded_config.get(path)
            
            if original == loaded:
                print(f"  ✓ 字段 {path} 正确加载和解密")
            else:
                print(f"  ✗ 字段 {path} 加载或解密失败: {loaded}")
    else:
        print("  ✗ 配置加载失败")
    
    # 尝试使用错误的密钥文件加载
    print("\n4. 尝试使用错误的密钥文件加载")
    wrong_key_file = os.path.join(SAMPLE_DIR, "encryption_alt.key")
    wrong_loaded = secure_load_config(secure_config_file, key_file=wrong_key_file)
    
    if not wrong_loaded or (wrong_loaded and any(
            isinstance(wrong_loaded.get(path), str) and wrong_loaded.get(path).startswith("[解密失败") 
            for path in sensitive_paths)):
        print("  ✓ 使用错误的密钥加载失败")
    else:
        print("  ✗ 使用错误的密钥加载成功 - 这是错误的行为")
    
    return loaded_config


def demonstrate_env_variables(config):
    """演示使用环境变量"""
    print("\n使用环境变量作为密钥演示")
    print("=" * 60)
    
    # 生成固定密钥用于演示
    master_key = "demo-env-var-key-123456789"
    print(f"\n1. 生成固定主密钥: {master_key[:5]}...（已截断）")
    
    # 设置环境变量
    os.environ["VISIONAI_MASTER_KEY"] = master_key
    print("  设置环境变量 VISIONAI_MASTER_KEY")
    
    # 使用环境变量加密 - 使用简单的字符串值测试配置
    print("\n2. 使用环境变量中的密钥加密配置")
    test_config = {
        "api_key": "env-var-test-api-key-123",
        "password": "env-var-test-password-456"
    }
    
    env_encrypted = encrypt_sensitive_fields(
        test_config,
        sensitive_paths=["api_key", "password"]
    )
    
    # 删除环境变量并尝试解密
    print("\n3. 删除环境变量并尝试解密")
    prev_key = os.environ.pop("VISIONAI_MASTER_KEY")
    
    try:
        decrypted_no_env = decrypt_sensitive_fields(env_encrypted)
        if decrypted_no_env["api_key"].startswith("[解密失败"):
            print("  ✓ 删除环境变量后解密失败，返回错误标记")
        else:
            print("  ✗ 删除环境变量后仍能解密 - 这可能是由于使用了默认密钥")
    except Exception as e:
        print(f"  ✓ 删除环境变量后解密失败: {type(e).__name__}")
    
    # 恢复环境变量
    os.environ["VISIONAI_MASTER_KEY"] = prev_key
    print("\n4. 恢复环境变量并再次解密")
    
    decrypted = decrypt_sensitive_fields(env_encrypted)
    if test_config["api_key"] == decrypted["api_key"]:
        print("  ✓ 恢复环境变量后解密成功")
    else:
        print("  ✗ 解密失败，密钥可能不匹配")
    
    # 清理环境变量
    os.environ.pop("VISIONAI_MASTER_KEY", None)


def demonstrate_custom_password():
    """演示使用自定义密码"""
    print("\n使用自定义密码演示")
    print("=" * 60)
    
    # 简单配置
    simple_config = {
        "service": "test-service",
        "api_key": "secret-api-key-12345",
        "endpoint": "https://api.test.com"
    }
    
    # 固定密码用于演示
    password = "demo-password-123"
    print(f"\n1. 使用固定密码加密: {password}")
    
    # 使用密码加密
    encrypted = encrypt_sensitive_fields(
        simple_config,
        sensitive_paths=["api_key"],
        master_key=password
    )
    
    print("\n2. 加密后的配置:")
    print(json.dumps(encrypted, indent=2))
    
    # 使用相同密码解密
    print("\n3. 使用相同密码解密")
    decrypted = decrypt_sensitive_fields(encrypted, master_key=password)
    
    # 验证
    if simple_config["api_key"] == decrypted["api_key"]:
        print("  ✓ 使用自定义密码加密解密验证通过")
    else:
        print("  ✗ 使用自定义密码加密解密验证失败")
    
    # 使用错误密码尝试解密
    wrong_password = "wrong-password"
    print("\n4. 使用错误密码尝试解密")
    
    try:
        incorrect_decrypt = decrypt_sensitive_fields(encrypted, master_key=wrong_password)
        if isinstance(incorrect_decrypt["api_key"], str) and incorrect_decrypt["api_key"].startswith("[解密失败"):
            print("  ✓ 使用错误密码解密返回了错误标记")
        else:
            print("  ✗ 使用错误密码仍能解密 - 这是错误的行为")
    except Exception:
        print("  ✓ 使用错误密码解密失败，这是预期行为")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="配置安全存储演示")
    parser.add_argument("--field", action="store_true", help="演示字段级加密")
    parser.add_argument("--key-file", action="store_true", help="演示密钥文件使用")
    parser.add_argument("--file-ops", action="store_true", help="演示配置文件操作")
    parser.add_argument("--env-vars", action="store_true", help="演示环境变量使用")
    parser.add_argument("--custom-pwd", action="store_true", help="演示自定义密码使用")
    args = parser.parse_args()
    
    print("VisionAI-ClipsMaster 配置安全存储演示")
    print("=" * 60)
    
    # 创建示例配置
    sample_config, config_file = create_sample_config()
    
    # 如果没有指定参数，运行所有演示
    if not any([args.field, args.key_file, args.file_ops, args.env_vars, args.custom_pwd]):
        args.field = True
        args.key_file = True
        args.file_ops = True
        args.env_vars = True
        args.custom_pwd = True
    
    # 字段级加密演示
    if args.field:
        encrypted_config, decrypted_config = demonstrate_field_encryption(sample_config)
    
    # 密钥文件使用演示
    key_file = None
    if args.key_file:
        key_file = demonstrate_key_file(sample_config)
    
    # 配置文件操作演示
    if args.file_ops and key_file:
        demonstrate_config_file_operations(sample_config, key_file)
    
    # 环境变量使用演示
    if args.env_vars:
        demonstrate_env_variables(sample_config)
    
    # 自定义密码使用演示
    if args.custom_pwd:
        demonstrate_custom_password()
    
    print("\n配置安全存储演示完成")


if __name__ == "__main__":
    main() 