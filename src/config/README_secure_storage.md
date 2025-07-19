# 配置安全存储模块

本模块提供配置文件的加密和解密功能，用于保护敏感的配置信息。它支持字段级加密，确保敏感信息不会以明文形式存储在配置文件中。

## 主要功能

- **字段级加密**：只加密特定的敏感字段，而不是整个配置文件
- **多种密钥管理**：支持通过环境变量、密钥文件或自定义密码提供密钥
- **强大的加密算法**：使用AES-GCM和ChaCha20-Poly1305提供高强度加密
- **自动密钥派生**：使用PBKDF2-HMAC-SHA256从密码派生密钥
- **优雅的错误处理**：当解密失败时提供友好的错误信息
- **可靠的机器绑定**：使用机器特定信息生成默认密钥
- **与配置管理器集成**：无缝集成到现有的配置管理系统中

## 使用方法

### 加密敏感字段

```python
from src.config.secure_storage import encrypt_sensitive_fields

config = {
    "api_key": "my-secret-api-key",
    "endpoint": "https://api.example.com",
    "max_connections": 10
}

# 加密特定字段
encrypted_config = encrypt_sensitive_fields(
    config, 
    sensitive_paths=["api_key"]
)

# encrypted_config 中的 api_key 字段现在是加密的
```

### 解密配置

```python
from src.config.secure_storage import decrypt_sensitive_fields

# 解密所有加密的字段
decrypted_config = decrypt_sensitive_fields(encrypted_config)

# decrypted_config 中的 api_key 现在恢复为原始值
```

### 安全保存和加载配置文件

```python
from src.config.secure_storage import secure_save_config, secure_load_config

# 保存加密的配置到文件
secure_save_config(config, "config.json", sensitive_paths=["api_key", "password"])

# 加载并自动解密配置
loaded_config = secure_load_config("config.json")
```

### 使用密钥文件

```python
from src.config.secure_storage import generate_key_file

# 生成新的密钥文件
generate_key_file("encryption_key.json")

# 使用密钥文件加密和保存
secure_save_config(config, "config.json", 
                  sensitive_paths=["api_key"], 
                  key_file="encryption_key.json")

# 使用相同的密钥文件加载
loaded_config = secure_load_config("config.json", key_file="encryption_key.json")
```

### 使用环境变量

```python
import os

# 设置环境变量作为密钥
os.environ["VISIONAI_MASTER_KEY"] = "my-secret-master-key"

# 加密配置
encrypted_config = encrypt_sensitive_fields(config, sensitive_paths=["api_key"])

# 不需要明确提供密钥，会自动使用环境变量
```

### 创建自定义的 SecureStorage 实例

```python
from src.config.secure_storage import SecureStorage

# 创建安全存储实例
secure = SecureStorage(master_key="my-custom-key")

# 使用实例直接加密值
encrypted_value = secure.encrypt_config_value("sensitive-data")

# 解密值
decrypted_value = secure.decrypt_config_value(encrypted_value)
```

## 安全注意事项

1. **密钥管理**：请安全地存储和管理您的密钥。使用环境变量或密钥文件，避免在代码中硬编码密钥。

2. **盐值**：每个加密操作都使用唯一的随机数(nonce)，确保相同的明文不会产生相同的密文。

3. **错误处理**：解密错误可能表明使用了错误的密钥，或者数据被篡改。

4. **迭代次数**：默认的密钥派生使用100,000次迭代，提供良好的安全性。

5. **算法选择**：默认使用AES-GCM，它提供了认证加密(AEAD)，可以检测数据是否被篡改。

## 与配置管理器集成

安全存储模块已集成到配置管理器中，可以通过以下方式使用：

```python
from src.config import config_manager

# 使用配置管理器安全加载配置
config = config_manager.secure_load_config("user_config.json")

# 修改配置
config["api_key"] = "new-api-key"

# 安全保存配置
config_manager.secure_save_config(config, "user_config.json")
```

## 依赖项

本模块依赖以下Python包：

- `cryptography`：提供加密功能
- `pycryptodome`：提供额外的加密算法

可以使用以下命令安装依赖：

```bash
pip install cryptography pycryptodome
```

## 示例

查看 `src/demos/secure_storage_demo.py` 文件，了解更多使用示例。 