# 实时错误监控看板 (LiveErrorMonitor)

## 功能概述

`LiveErrorMonitor` 是一个实时错误监控和可视化组件，为VisionAI-ClipsMaster提供全面的错误跟踪、分析和告警功能。该模块专注于帮助开发者和用户快速发现、理解和解决程序运行过程中出现的问题，提高系统的可靠性和稳定性。

## 主要特性

- **实时错误统计**：收集并统计各种错误类型、组件和严重程度
- **错误分类**：智能分类错误，帮助识别常见问题模式
- **趋势分析**：显示错误发生的时间趋势，帮助发现与时间相关的问题
- **智能建议**：针对不同类型的错误提供恢复建议
- **告警系统**：当错误达到阈值时自动触发告警
- **可扩展接口**：支持自定义回调和第三方集成
- **轻量级设计**：低开销的错误监控，适合在生产环境使用
- **配置灵活**：通过配置文件自定义监控行为和阈值

## 组件结构

实时错误监控看板由以下核心部分组成：

1. **LiveErrorMonitor**：主要监控类，管理错误统计、分析和告警
2. **错误分类系统**：将错误按类型、组件和严重程度进行分类
3. **告警机制**：当错误达到预设阈值时触发告警
4. **回调系统**：支持注册自定义回调函数处理错误事件
5. **配置管理**：从配置文件加载自定义设置

## 安装和配置

### 配置文件

错误监控看板使用 `configs/error_dashboard.json` 文件进行配置。配置文件包含以下主要部分：

```json
{
  "version": "1.0",
  "description": "实时错误监控看板配置",
  "enabled": true,
  "ui": {
    "refresh_interval_ms": 500,
    "max_history_items": 100,
    "auto_expand_critical": true,
    "show_suggestions": true
  },
  "alert_thresholds": {
    "total": 10,
    "rate": 0.05,
    "critical": 1
  },
  "recovery_suggestions": {
    "MODEL_ERROR": "检查模型文件完整性或尝试重新加载模型",
    "MEMORY_ERROR": "关闭其他应用释放内存或降低批处理大小"
  }
}
```

### 主要配置选项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| enabled | 是否启用错误监控 | true |
| ui.refresh_interval_ms | UI更新间隔(毫秒) | 500 |
| ui.max_history_items | 最大历史记录数量 | 100 |
| alert_thresholds.total | 错误总数告警阈值 | 10 |
| alert_thresholds.rate | 错误率告警阈值 | 0.05 (5%) |
| alert_thresholds.critical | 严重错误告警阈值 | 1 |
| recovery_suggestions | 错误恢复建议映射表 | {...} |

## 使用方法

### 基本用法

```python
from src.exporters.error_dashboard import get_error_monitor

# 获取错误监控看板实例
monitor = get_error_monitor()

# 启动监控
monitor.start_monitoring()

try:
    # 执行可能出错的操作
    process_video()
except Exception as e:
    # 更新错误监控看板
    monitor.update_dashboard(e)
    
    # 继续处理或重试
    # ...

# 停止监控并获取统计数据
stats = monitor.stop_monitoring()
print(f"总错误数: {stats['total_errors']}")
```

### 注册回调函数

```python
def on_error_update(metrics):
    """当错误监控看板更新时调用"""
    print(f"检测到新错误! 总计: {metrics['total_errors']}")
    if metrics['recent_errors']:
        latest = metrics['recent_errors'][-1]
        print(f"最新错误: {latest['error_code']} - {latest['message']}")

# 注册回调
monitor = get_error_monitor()
monitor.register_callback(on_error_update)
```

### 使用错误字典

除了异常对象外，也可以使用字典形式的错误信息：

```python
# 使用字典创建错误信息
error_info = {
    "code": "NETWORK_ERROR",
    "message": "API服务器连接超时",
    "component": "network",
    "phase": "data_loading",
    "severity": "ERROR"
}

# 更新错误监控看板
monitor.update_dashboard(error_info)
```

### 获取错误摘要

```python
# 获取简洁的错误摘要
summary = monitor.get_error_summary()

print(f"状态: {summary['status']}")
print(f"错误总数: {summary['total_errors']}")
print(f"最常见错误: {summary['most_common_error']}")
print(f"建议: {summary['suggestion']}")
```

### 获取详细仪表盘数据

```python
# 获取完整的仪表盘数据
dashboard_data = monitor.get_dashboard_data()

# 查看错误趋势
print("错误趋势:")
for time_point, count in dashboard_data['error_trend'].items():
    print(f"  {time_point}: {count}次")

# 查看最常见错误
print("\n最常见错误:")
for error, count in dashboard_data['top_errors']:
    print(f"  {error}: {count}次")
```

## 与UI集成

错误监控看板可以与UI界面集成，实现实时错误反馈：

```python
# UI更新函数示例
def update_ui(metrics):
    # 更新错误计数器
    error_count_label.setText(str(metrics['total_errors']))
    
    # 更新错误列表
    error_list.clear()
    for error in metrics['recent_errors']:
        item = QListWidgetItem(f"[{error['severity']}] {error['error_code']}: {error['message']}")
        if error['severity'] == 'CRITICAL':
            item.setForeground(Qt.red)
        error_list.addItem(item)
    
    # 更新错误图表
    update_error_chart(metrics['error_trend'])

# 注册UI更新回调
monitor = get_error_monitor()
monitor.register_callback(update_ui)
```

## 错误分析和诊断

错误监控看板提供了多种分析视图，帮助识别和诊断问题：

### 错误类型分布

查看不同类型错误的分布情况，发现最常见的错误类型：

```python
dashboard_data = monitor.get_dashboard_data()
error_types = dashboard_data['error_types']

# 显示错误类型分布
for error_type, count in error_types.items():
    print(f"{error_type}: {count}次 ({count/sum(error_types.values())*100:.1f}%)")
```

### 组件错误分析

查看哪些组件产生了最多错误：

```python
component_errors = dashboard_data['component_errors']

# 显示组件错误分布
for component, count in component_errors.items():
    print(f"{component}: {count}次")
```

### 错误趋势分析

查看错误随时间的变化趋势：

```python
error_trend = dashboard_data['error_trend']

# 显示错误趋势
for timestamp, count in sorted(error_trend.items()):
    print(f"{timestamp}: {count}次")
```

## 最佳实践

使用错误监控看板的一些建议：

1. **及早初始化**：在程序启动时初始化错误监控看板
2. **异常处理**：在异常处理块中更新错误监控看板
3. **合理设置阈值**：根据应用规模设置合适的告警阈值
4. **定期查看趋势**：定期分析错误趋势，发现潜在问题
5. **集成日志系统**：与日志系统结合使用，提供更完整的上下文
6. **保存错误报告**：定期保存错误统计报告，用于长期分析

## 常见问题

**Q: 如何自定义错误分类规则？**

A: 修改配置文件中的 `categorization` 部分，添加或调整分类规则。

**Q: 为什么某些标准异常没有详细信息？**

A: 标准Python异常如 `ValueError` 没有自定义属性，只能提取基本信息。建议使用 `ClipMasterError` 及其子类获取更详细的错误信息。

**Q: 告警机制是如何工作的？**

A: 系统定期检查错误统计数据，当超过配置中的阈值时触发告警。告警可以通过回调函数通知UI或记录到日志。

**Q: 如何集成到现有错误处理系统？**

A: 使用注册回调函数的方式，将错误监控看板与现有系统集成。也可以在现有的异常处理逻辑中添加对监控看板的更新。

## 示例程序

参考 `src/exporters/error_dashboard_example.py` 查看完整的使用示例：

```bash
python -m src.exporters.error_dashboard_example
```

这个示例程序展示了如何：
- 初始化和配置错误监控看板
- 生成各种类型的错误进行测试
- 注册和使用回调函数
- 分析和展示错误统计数据
- 保存错误报告 