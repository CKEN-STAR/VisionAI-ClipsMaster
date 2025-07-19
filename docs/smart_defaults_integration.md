# 智能默认值系统集成指南

本文档提供了VisionAI-ClipsMaster智能默认值系统的集成和使用指南。

## 1. 系统概述

智能默认值系统是VisionAI-ClipsMaster的一个强大功能，它可以：

- 根据用户硬件自动推荐最佳分辨率、帧率和性能设置
- 根据系统环境推荐界面语言和主题
- 根据使用习惯学习并调整配置
- 自动适应不同使用场景，提供个性化体验

系统主要包含两个核心组件：

1. **SmartDefaults** - 智能默认值引擎，负责检测硬件和软件环境，并推荐最佳配置
2. **SmartUpdater** - 智能更新器，负责记录使用习惯，定期更新推荐设置

## 2. 集成步骤

### 2.1 导入必要的模块

在应用程序的入口点（如`main.py`或`app.py`）中导入智能默认值系统组件：

```python
from src.config.defaults import smart_defaults
from src.config.smart_updater import initialize_updater
from src.config.config_manager import config_manager
```

### 2.2 初始化智能默认值系统

在应用程序初始化过程中，添加以下代码：

```python
def initialize_smart_defaults(config_manager):
    """初始化智能默认值系统"""
    logger.info("正在初始化智能默认值引擎...")
    
    # 对首次运行的用户应用智能默认值
    result = smart_defaults.apply_to_config(config_manager, override_existing=False)
    logger.info(f"应用智能默认值{'成功' if result else '失败'}")
    
    # 初始化智能更新器
    updater = initialize_updater()
    if updater:
        # 启动自动更新线程
        updater.start_auto_update(interval_days=1)
        logger.info("已启动智能默认值自动更新服务")
    else:
        logger.warning("初始化智能更新器失败")
    
    return updater

# 应用程序初始化函数中调用
def initialize_application():
    # ...其他初始化代码...
    
    # 加载配置
    config_manager.load_all_configs()
    
    # 初始化智能默认值系统
    smart_updater = initialize_smart_defaults(config_manager)
    
    # ...其他初始化代码...
```

### 2.3 记录用户交互和使用模式

在相关功能模块中，记录用户的使用行为：

```python
# 在导出模块中
from src.config.smart_updater import smart_updater

def export_video(resolution, codec, format):
    # ... 导出处理代码 ...
    
    # 记录导出设置使用情况
    if smart_updater:
        smart_updater.update_export_stats(resolution, codec, format)
```

```python
# 在界面设置更改处理函数中
def on_interface_setting_changed(timeline_zoom, theme):
    # ... 设置更改处理代码 ...
    
    # 记录界面设置使用情况
    if smart_updater:
        smart_updater.update_interface_stats(timeline_zoom, theme)
```

```python
# 在性能监控模块中
def on_render_complete(render_time, memory_usage):
    # ... 渲染完成处理代码 ...
    
    # 记录性能数据
    if smart_updater:
        smart_updater.update_performance_stats(render_time, memory_usage)
```

### 2.4 处理用户手动更改设置

当用户手动更改设置时，记录该设置已被用户覆盖：

```python
# 在设置更改处理函数中
def on_user_setting_changed(setting_path, value):
    # ... 设置更改处理代码 ...
    
    # 记录用户覆盖
    if smart_updater:
        smart_updater.record_setting_override(setting_path)
```

## 3. 使用智能默认值API

### 3.1 获取智能推荐设置

```python
# 获取所有智能默认值
all_defaults = smart_defaults.get_all_smart_defaults()

# 获取硬件感知默认值
hw_defaults = smart_defaults.get_hardware_aware_defaults()

# 获取软件环境感知默认值
sw_defaults = smart_defaults.get_software_aware_defaults()

# 获取使用模式感知默认值
usage_defaults = smart_defaults.get_usage_aware_defaults()
```

### 3.2 使用智能更新器API

```python
# 获取最常用的设置
most_used_resolution = smart_updater.get_most_used_setting("export", "resolutions")
most_used_theme = smart_updater.get_most_used_setting("interface", "theme")

# 强制检查和更新设置
smart_updater.check_and_update(force=True)
```

## 4. 测试智能默认值系统

可以使用`src/demos/smart_defaults_demo.py`脚本来测试和演示智能默认值系统的功能：

```bash
# 运行完整演示
python src/demos/smart_defaults_demo.py

# 只测试硬件检测
python src/demos/smart_defaults_demo.py --hardware

# 应用智能默认值到配置并强制覆盖
python src/demos/smart_defaults_demo.py --apply --force
```

也可以运行自动化测试：

```bash
python tests/test_smart_defaults.py
```

## 5. 排错和维护

### 5.1 日志查看

智能默认值系统的日志消息带有前缀`smart_defaults`和`smart_updater`，可以在应用日志中搜索这些前缀来查看相关日志。

### 5.2 重置用户偏好

如果需要重置智能默认值系统记录的用户偏好，删除以下文件：

```
configs/usage_stats.json
```

### 5.3 禁用自动更新

如果需要临时禁用智能默认值自动更新，可以在应用初始化时添加以下代码：

```python
# 初始化但不启动自动更新
updater = initialize_updater()
# 不调用updater.start_auto_update()
```

## 6. 进阶开发

智能默认值系统设计为可扩展的，开发者可以：

1. 在`src/config/defaults.py`中添加新的检测方法
2. 在`src/config/smart_updater.py`中添加新的统计指标
3. 扩展智能系统以支持更多的个性化推荐功能

## 7. 结论

智能默认值系统为VisionAI-ClipsMaster提供了个性化的用户体验，通过自动适应不同用户的硬件环境和使用习惯，为用户提供最佳的默认设置，简化了配置过程，提高了用户满意度。 