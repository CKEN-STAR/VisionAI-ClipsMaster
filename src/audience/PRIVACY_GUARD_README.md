# 隐私安全适配器 (PrivacyAdapter)

## 概述

隐私安全适配器是VisionAI-ClipsMaster项目的关键组件，用于实现用户数据的隐私保护、匿名化和同意管理功能，确保项目符合GDPR等隐私法规的要求。

## 主要功能

隐私安全适配器提供以下核心功能：

1. **数据匿名化**：
   - 应用差分隐私技术保护用户数据
   - 为敏感字段添加随机噪声
   - 模糊化位置信息和个人身份信息

2. **用户同意管理**：
   - 记录用户对不同功能的同意状态
   - 验证用户是否同意使用特定功能
   - 管理同意的有效期和版本

3. **数据保留策略**：
   - 按数据类型实施不同的保留期限
   - 自动清理过期数据
   - 维护数据最小化原则

4. **敏感信息保护**：
   - 检测内容中的敏感个人信息
   - 对敏感信息进行编辑和替换
   - 与系统隐私管理器集成

## 实现架构

隐私安全适配器基于以下架构设计：

- **PrivacyAdapter类**：核心适配器，协调各功能模块
- **差分隐私实现**：添加统计噪声保护用户数据
- **同意管理机制**：记录和验证用户同意状态
- **数据保留系统**：根据配置的保留期限清理数据
- **敏感信息处理**：利用正则表达式和模式匹配识别敏感信息

## 使用方法

### 数据匿名化

```python
from src.audience import anonymize_data

# 原始用户数据
raw_data = {
    "user_id": "user123",
    "age": 28,
    "gender": "female",
    "location": {"latitude": 39.9042, "longitude": 116.4074},
    "email": "user@example.com"
}

# 匿名化处理
anonymized_data = anonymize_data(raw_data)
```

### 用户同意管理

```python
from src.audience import enforce_consent, record_consent, check_consent, ConsentRequiredError

# 记录用户同意
record_consent("user123", "preference_tracking", "granted")

# 检查用户是否同意
has_consent = check_consent("user123", "preference_tracking")

# 强制检查用户同意（如不同意会抛出异常）
try:
    enforce_consent("user123", "data_sharing")
    # 执行需要用户同意的操作
except ConsentRequiredError as e:
    # 处理用户未同意的情况
    print(f"需要用户同意: {str(e)}")
```

### 获取所有同意记录

```python
from src.audience import get_privacy_adapter

privacy_adapter = get_privacy_adapter()
all_consents = privacy_adapter.get_all_consents("user123")
```

### 敏感数据检测和编辑

```python
from src.audience import get_privacy_adapter

privacy_adapter = get_privacy_adapter()

# 检测敏感信息
content = {"message": "我的电话是13812345678，邮箱是user@example.com"}
sensitive_info = privacy_adapter.detect_sensitive_data(content)

# 编辑敏感信息
redacted_content = privacy_adapter.redact_sensitive_data(content)
```

### 应用数据保留策略

```python
from src.audience import get_privacy_adapter

privacy_adapter = get_privacy_adapter()
retention_result = privacy_adapter.apply_data_retention("user123")
```

## 配置选项

隐私安全适配器提供以下可配置选项：

### 同意选项

可配置的同意选项包括：

- `preference_tracking`: 偏好追踪
- `behavior_analysis`: 行为分析
- `cross_platform_integration`: 跨平台整合
- `personalized_content`: 个性化内容
- `data_sharing`: 数据共享
- `recommendation`: 推荐系统

### 差分隐私配置

差分隐私相关配置：

- `age_noise`: 年龄字段噪声参数
- `location_noise`: 位置信息噪声参数
- `preference_noise`: 偏好分数噪声参数
- `threshold`: 随机化阈值
- `min_group_size`: 最小分组大小（k匿名性）

### 数据保留期限

不同类型数据的保留期限：

- `behavior_data`: 行为数据保留天数（默认90天）
- `preference_data`: 偏好数据保留天数（默认180天）
- `profile_data`: 画像数据保留天数（默认365天）
- `sensitive_data`: 敏感数据保留天数（默认30天）

## 注意事项

1. 强制检查用户同意时，如用户未同意会抛出`ConsentRequiredError`异常
2. 用户同意默认有效期为365天，过期需要重新获取同意
3. 数据匿名化会移除敏感个人信息，如电子邮件、电话号码等
4. 位置数据会被降低精度，通常精确到城市级别
5. 应用数据保留策略会永久删除过期数据，确保在调用前进行必要的备份

## 扩展支持

如需扩展隐私安全适配器功能，可以：

1. 在PrivacyAdapter类中添加新的保护方法
2. 扩展同意选项以支持新功能
3. 修改差分隐私参数以调整保护强度
4. 增加新的敏感信息检测模式
5. 自定义数据保留期限以符合特定法规要求 