# 安全审计追踪系统

## 概述

VisionAI-ClipsMaster 项目中的安全审计追踪系统提供全面、安全且不可篡改的操作记录功能，对敏感数据访问、模型参数调整和系统配置变更等关键操作进行监控和记录。该系统有助于满足安全合规要求，提供操作可追溯性，并在安全事件发生时支持取证分析。

## 主要功能

- **全面的操作审计**：记录所有关键操作，包括敏感数据访问、模型操作、参数变更等
- **安全存储机制**：支持加密存储和条目签名，确保日志完整性和不可篡改性
- **灵活的审计级别**：根据操作类型和数据敏感度自动划分不同审计级别
- **便捷的接口**：提供简单易用的API和装饰器，便于集成到现有代码中
- **审计日志导出**：支持将审计日志导出为多种格式（JSON、CSV等）
- **日志查询分析**：提供搜索和过滤功能，便于分析特定时间段或特定类型的操作

## 核心组件

### 1. AuditTrail 类

核心审计追踪类，提供以下功能：

- 安全记录不同类型的操作审计日志
- 使用加密和签名确保日志完整性
- 提供日志存储、检索和导出功能

### 2. 审计级别和类别

系统定义了多种审计级别和类别，用于分类不同操作：

```python
# 审计级别
class AuditLevel(str, Enum):
    LOW = "low"          # 低风险操作
    MEDIUM = "medium"    # 中风险操作
    HIGH = "high"        # 高风险操作
    CRITICAL = "critical"  # 关键风险操作

# 审计类别
class AuditCategory(str, Enum):
    DATA_ACCESS = "data_access"           # 数据访问
    MODEL_OPERATION = "model_operation"   # 模型操作
    LOG_VIEW = "log_view"                 # 日志查看
    PARAMETER_CHANGE = "parameter_change" # 参数变更
    SYSTEM_CONFIG = "system_config"       # 系统配置
    EXPORT_OPERATION = "export_operation" # 导出操作
    USER_MANAGEMENT = "user_management"   # 用户管理
    SECURITY_EVENT = "security_event"     # 安全事件
```

### 3. 便捷函数和装饰器

系统提供多种便捷函数和装饰器，简化审计日志记录：

- `log_view_action()`：记录查看操作
- `log_data_access()`：记录数据访问
- `log_model_operation()`：记录模型操作
- `log_parameter_change()`：记录参数变更
- `@audit_log`：自动记录函数调用的装饰器

## 使用指南

### 基本用法

1. **记录查看操作**

   ```python
   from src.dashboard.audit_trail import log_view_action
   
   # 记录用户查看操作
   log_view_action(user, "view_srt_files")
   ```

2. **记录数据访问**

   ```python
   from src.dashboard.audit_trail import log_data_access
   
   # 记录敏感数据访问
   log_data_access(
       user, 
       data_type="subtitle",        # 数据类型
       resource_id="subtitle_123",  # 资源ID
       operation="download"         # 操作类型
   )
   ```

3. **记录模型操作**

   ```python
   from src.dashboard.audit_trail import log_model_operation
   
   # 记录模型加载操作
   log_model_operation(
       user,
       model_name="qwen2.5-7b-zh",
       operation="load",
       parameters={"precision": "float16", "memory_efficient": True}
   )
   ```

4. **记录参数变更**

   ```python
   from src.dashboard.audit_trail import log_parameter_change
   
   # 记录参数变更
   log_parameter_change(
       user,
       param_name="temperature",
       old_value=0.7,
       new_value=0.9,
       component="text_generation"
   )
   ```

### 使用装饰器

将装饰器应用于敏感操作函数：

```python
from src.dashboard.audit_trail import audit_log, AuditCategory, AuditLevel

@audit_log(category=AuditCategory.DATA_ACCESS, level=AuditLevel.HIGH)
def process_sensitive_data(user, data_id):
    # 函数实现
    return result
```

装饰器会自动：
- 记录函数调用的开始和结束
- 记录函数参数和返回值
- 捕获并记录任何异常
- 根据指定类别和级别标记日志条目

### 自定义审计功能

需要更高级功能时，可以直接使用 `AuditTrail` 类：

```python
from src.dashboard.audit_trail import get_audit_trail

# 获取审计追踪实例
audit = get_audit_trail()

# 自定义记录
entry = {
    "category": "custom_operation",
    "level": "high",
    "user": user.id,
    "action": "special_operation",
    "details": {
        "custom_field": "value",
        "operation_data": {...}
    }
}
audit.secure_append(entry)
```

### 导出和分析审计日志

```python
from src.dashboard.audit_trail import get_audit_trail
import datetime

audit = get_audit_trail()

# 导出日志
start_date = datetime.datetime(2023, 1, 1)
end_date = datetime.datetime.now()

audit.export_logs(
    output_file="audit_export.json",
    start_date=start_date,
    end_date=end_date,
    format="json"
)

# 搜索特定操作
results = audit.search_logs(
    query={"category": "data_access", "level": "high"},
    start_date=start_date,
    end_date=end_date
)
```

## 安全注意事项

1. **保护审计日志**：审计日志包含敏感信息，应限制对日志文件的访问
2. **密钥管理**：安全存储和管理用于签名和加密的密钥
3. **定期备份**：定期备份审计日志到安全位置
4. **日志轮转**：实施日志轮转策略，防止日志文件过大
5. **日志验证**：定期验证日志的完整性，确保未被篡改

## 集成范例

以下是几个关键模块集成安全审计的示例：

### 1. 模型加载器集成

```python
from src.dashboard.audit_trail import log_model_operation

def load_model(user, model_name, parameters=None):
    # 记录模型加载开始
    log_model_operation(user, model_name, "load_start", parameters)
    
    try:
        # 执行模型加载
        model = actual_model_loader(model_name, parameters)
        
        # 记录成功加载
        log_model_operation(user, model_name, "load_success", parameters)
        return model
    except Exception as e:
        # 记录加载失败
        log_model_operation(
            user, 
            model_name, 
            "load_failed", 
            {"error": str(e), "parameters": parameters}
        )
        raise
```

### 2. 字幕处理集成

```python
from src.dashboard.audit_trail import log_data_access, audit_log, AuditCategory

@audit_log(category=AuditCategory.DATA_ACCESS)
def process_subtitle(user, subtitle_id, operations):
    # 函数已通过装饰器自动记录审计日志
    # 处理字幕逻辑...
    return processed_subtitle
```

### 3. 参数调整集成

```python
from src.dashboard.audit_trail import log_parameter_change

def update_generation_parameters(user, config_name, updates):
    # 加载当前配置
    current_config = load_config(config_name)
    
    # 记录每个参数变更
    for param, new_value in updates.items():
        old_value = current_config.get(param)
        if old_value != new_value:
            log_parameter_change(
                user, param, old_value, new_value, config_name
            )
    
    # 应用更新
    updated_config = {**current_config, **updates}
    save_config(config_name, updated_config)
    
    return updated_config
```

## 演示代码

参见 [examples/legal_audit_demo.py](../examples/legal_audit_demo.py) 了解完整的演示示例。

## 最佳实践

1. **职责分离**：审计日志的生成与查看应由不同人员负责
2. **全面覆盖**：确保所有敏感操作都有相应的审计记录
3. **上下文丰富**：记录足够的上下文信息，便于后续分析
4. **异常处理**：确保即使在错误条件下也能记录日志
5. **定期审查**：定期检查审计日志，寻找可疑活动
6. **避免过度记录**：只记录有意义的信息，避免日志膨胀 