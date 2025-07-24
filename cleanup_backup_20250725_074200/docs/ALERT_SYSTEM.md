# VisionAI-ClipsMaster 分级预警系统使用指南

VisionAI-ClipsMaster的分级预警系统为应用程序提供了实时监控、资源管理和异常处理能力，可以在内存、性能、处理质量等方面出现问题时及时预警，帮助保障系统在资源受限环境下的稳定运行。

## 1. 预警级别说明

系统支持四种预警级别，按照严重程度由低到高排序：

| 级别 | 阈值（百分比）| 颜色  | 行为                                     |
|------|-------------|-------|------------------------------------------|
| INFO | N/A         | 蓝色  | 仅记录日志，不干预                        |
| WARNING | 80%      | 黄色  | 记录日志，发送UI通知                      |
| ERROR | 90%        | 橙色  | 记录日志，发送UI通知，提示用户            |
| CRITICAL | 95%     | 红色  | 记录日志，发送UI通知，提示用户，执行紧急保存，释放资源 |

## 2. 监控指标

预警系统监控以下关键指标：

- **内存使用率**：系统内存占用百分比
- **CPU使用率**：系统CPU占用百分比
- **模型响应延迟**：模型处理请求的响应时间（毫秒）
- **视频处理延迟**：视频处理操作的响应时间（毫秒）
- **缓存命中率**：系统缓存命中效率百分比
- **字幕解析错误**：字幕文件解析过程中发生的错误计数

## 3. 配置方法

预警系统的配置存储在 `configs/alert_config.yaml` 文件中，可以根据需要调整以下配置：

### 3.1 阈值配置

```yaml
# 各资源的预警阈值配置
thresholds:
  # 内存相关阈值（百分比）
  memory:
    warning: 80    # 内存使用率80%触发警告
    error: 90      # 内存使用率90%触发错误
    critical: 95   # 内存使用率95%触发严重错误
  
  # CPU相关阈值（百分比）
  cpu:
    warning: 85    # CPU使用率85%触发警告
    error: 95      # CPU使用率95%触发错误
    critical: 98   # CPU使用率98%触发严重错误
```

### 3.2 预警行为配置

```yaml
# 各级别预警的处理动作
actions:
  warning:   # 警告级别
    - log                # 记录日志
    - ui_notify          # UI通知
  
  error:     # 错误级别
    - log                # 记录日志
    - ui_notify          # UI通知
    - user_alert         # 用户通知
```

### 3.3 通知配置

```yaml
# UI通知相关配置
ui_notification:
  enabled: true
  duration:              # 通知显示时间（秒）
    warning: 5
    error: 10
    critical: 30
  position: "bottom-right" # 通知显示位置
```

### 3.4 冷却期配置

避免预警过于频繁：

```yaml
# 预警冷却期配置（秒）
cooldown_periods:
  info: 60               # 信息级别冷却期
  warning: 300           # 警告级别冷却期
  error: 600             # 错误级别冷却期
  critical: 60           # 严重级别冷却期
```

## 4. 在代码中使用预警系统

### 4.1 检查资源使用

```python
from src.monitoring import check_memory_usage, check_cpu_usage, AlertLevel

# 检查内存使用情况
memory_percent = 85  # 这里应该是实际的内存占用百分比
alert_level = check_memory_usage(memory_percent, {"source": "my_module"})

if alert_level == AlertLevel.WARNING:
    # 处理警告级别预警
    pass
elif alert_level == AlertLevel.ERROR:
    # 处理错误级别预警
    pass
elif alert_level == AlertLevel.CRITICAL:
    # 处理严重级别预警
    pass
```

### 4.2 检查模型延迟

```python
from src.monitoring import check_model_latency

# 检查模型响应延迟
latency_ms = 3000  # 实际响应时间（毫秒）
model_name = "qwen2.5-7b-zh"
alert_level = check_model_latency(latency_ms, model_name, {
    "input_length": 1024,
    "operation": "text_generation"
})
```

### 4.3 触发自定义预警

```python
from src.monitoring import AlertLevel, AlertCategory, trigger_custom_alert

# 触发自定义预警
trigger_custom_alert(
    AlertLevel.ERROR,  # 预警级别
    AlertCategory.VIDEO,  # 预警类别
    "video_processing_error",  # 资源名称
    3,  # 值
    "视频处理失败",  # 消息
    {
        "video_file": "example.mp4",
        "error_type": "codec_error",
        "recommendation": "请检查视频编码格式是否支持"
    }
)
```

### 4.4 获取预警历史

```python
from src.monitoring import get_alert_manager

# 获取预警管理器
alert_manager = get_alert_manager()

# 获取历史预警记录
alerts = alert_manager.get_history(limit=10)

# 按特定级别筛选
from src.monitoring import AlertLevel
error_alerts = alert_manager.get_history(level=AlertLevel.ERROR)
```

## 5. 预警响应机制

当触发预警时，系统会执行以下操作：

### 5.1 警告级别 (WARNING)

- 记录日志
- 在UI界面显示黄色警告通知

### 5.2 错误级别 (ERROR)

- 记录日志
- 在UI界面显示橙色错误通知
- 向用户发送通知消息

### 5.3 严重级别 (CRITICAL)

- 记录日志
- 在UI界面显示红色严重错误通知
- 向用户发送紧急通知消息
- 执行紧急保存操作
- 释放系统资源（如卸载模型、清理缓存等）

## 6. 内存优化策略

严重级别预警触发后，系统会执行以下内存优化策略：

- **卸载非活动模型**：保留当前语言模型，卸载其他模型
- **清理缓存**：释放系统缓存所占用的内存
- **降低量化级别**：尝试将模型量化至更低的位宽（如从Q4降至Q2）
- **强制垃圾回收**：立即执行Python垃圾回收

## 7. 关联模块

预警系统与以下模块紧密结合：

- **监控模块**：提供系统资源和性能指标数据
- **模型加载适配器**：监控模型加载和切换性能
- **字幕解析器**：监控字幕解析错误
- **内存管理**：在资源紧张时进行干预

## 8. 常见问题

### 8.1 如何禁用预警？

可以通过修改配置文件或使用以下代码禁用预警：

```python
from src.monitoring import get_alert_manager

# 获取预警管理器
alert_manager = get_alert_manager()

# 更新配置，禁用UI通知
alert_manager.update_config({
    "ui_notification": {
        "enabled": False
    }
})
```

### 8.2 如何调整预警阈值？

```python
from src.monitoring import get_alert_manager

# 获取预警管理器
alert_manager = get_alert_manager()

# 更新内存阈值
alert_manager.update_config({
    "thresholds": {
        "memory": {
            "warning": 70,
            "error": 85,
            "critical": 90
        }
    }
})
```

### 8.3 如何查看预警历史？

在程序运行过程中，预警历史会被记录到`logs/alerts.json`文件中，可以通过以下方式查看：

1. 使用文本编辑器直接打开`logs/alerts.json`文件
2. 在程序中调用`get_alert_manager().get_history()`方法
3. 通过日志查看器界面查看预警历史

## 9. 英文模型配置

虽然当前未加载英文模型，但预警系统已保留相关配置，当英文模型被启用时，预警系统将自动监控英文模型的性能。

```yaml
# 特定于英文模型的预警配置（保留配置但暂不使用）
mistral_model:
  max_latency_ms: 10000         # 最大允许延迟（毫秒）
  min_tokens_per_second: 6      # 最小生成速度（每秒token数）
  max_memory_usage_gb: 3.5      # 最大内存使用（GB）
``` 