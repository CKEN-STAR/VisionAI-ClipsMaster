# 预测性趋势投影功能

## 功能概述

预测性趋势投影是VisionAI-ClipsMaster的一项关键性能优化功能，它通过分析历史资源使用数据，预测未来系统资源使用趋势，帮助用户提前发现潜在性能瓶颈并及时优化系统配置。

主要功能包括：
- 内存使用率预测：预测未来5/15/30分钟内的内存使用趋势
- OOM风险评估：评估系统发生内存不足的风险和可能的时间点
- 工作负载趋势预测：预测未来CPU使用率和请求量变化
- 缓存效率衰减曲线：预测缓存命中率的变化趋势
- 系统状态综合分析：提供基于多维度分析的系统状态预测和优化建议

## 技术实现

预测性趋势投影功能采用轻量级设计，针对4GB RAM环境进行了优化：

1. **核心算法**：
   - 主要预测模型采用LSTM（长短期记忆网络）
   - 在不支持TensorFlow的环境中，自动降级为简单线性回归模型
   - 内置回退机制，确保在任何环境下都能正常工作

2. **数据流设计**：
   - 历史数据收集：定期采集系统资源使用数据
   - 预处理：对原始数据进行归一化和时间序列化处理
   - 模型训练：基于历史数据训练预测模型
   - 预测：使用训练好的模型进行未来趋势预测
   - 可视化：将预测结果以图表形式直观呈现

3. **组件结构**：
   - PredictiveEngine：预测引擎核心类
   - MemoryProphet：内存使用预测器
   - WorkloadPredictor：工作负载预测器
   - PredictiveView：预测视图UI组件

## 使用指南

### 通过主界面访问

1. 在主窗口中，切换到"趋势预测"标签页
2. 你将看到四个子标签页：概览、内存预测、工作负载预测和缓存效率预测
3. 默认情况下系统会自动刷新预测数据，你也可以点击"立即刷新"按钮手动更新

### 内存预测

内存预测标签页显示未来内存使用趋势和OOM风险：

- 可选择不同的预测时间范围（短期30分钟、中期1.5小时、长期3小时）
- 图表中红色虚线表示危险阈值（默认90%）
- 底部的风险指示器显示OOM风险级别和预计达到阈值的时间

### 工作负载预测

工作负载预测标签页显示未来CPU使用率和请求数预测：

- 可选择不同的预测时间（1小时、2小时、4小时）
- 双Y轴图表分别显示CPU使用率和请求数
- 底部显示预测方法和置信度

### 缓存效率预测

缓存效率预测标签页显示缓存命中率的未来趋势：

- 图表颜色反映趋势方向（绿色=上升，红色=下降，蓝色=稳定）
- 底部显示趋势类型和置信度

### 系统综合状态

概览标签页提供系统综合状态分析：

- 状态指示器显示整体系统状态（稳定、警告或危险）
- 趋势分析区域展示内存和CPU使用趋势
- 系统建议区域提供基于预测的优化建议

## 编程接口

### 获取预测引擎实例

```python
from src.dashboard.predictive_engine import get_predictive_engine
from src.dashboard.data_integration import DataAggregator

# 创建数据聚合器
data_aggregator = DataAggregator()

# 获取预测引擎单例
engine = get_predictive_engine(data_aggregator)
```

### 获取内存预测

```python
# 获取中期内存预测（默认1.5小时）
memory_forecast = engine.get_memory_predictions("medium")

# 内存使用预测值
values = memory_forecast.get("values", [])

# OOM风险分析
oom_risk = memory_forecast.get("oom_risk", {})
risk_level = oom_risk.get("risk_level", "low")
time_to_threshold = oom_risk.get("time_to_threshold_minutes")
```

### 获取工作负载预测

```python
# 获取2小时工作负载预测
workload_forecast = engine.get_workload_predictions(hours=2)

# CPU使用率预测
cpu_values = workload_forecast.get("cpu_percent", [])

# 请求数预测
request_values = workload_forecast.get("request_count", [])
```

### 获取缓存效率预测

```python
# 获取缓存效率预测
cache_forecast = engine.get_cache_efficiency_forecast()

# 效率预测值
efficiency_values = cache_forecast.get("predicted_efficiency", [])

# 趋势方向
trend = cache_forecast.get("trend", "stable")  # "increasing", "decreasing", "stable"
```

### 获取综合预测

```python
# 获取综合预测
forecast = engine.get_comprehensive_forecast()

# 系统状态
system_status = forecast.get("system_status", {})
status = system_status.get("status", "unknown")  # "critical", "warning", "stable"

# 获取建议
recommendation = system_status.get("recommendation", "")
```

## 注意事项

1. 预测功能需要足够的历史数据才能提供准确结果，初次使用时预测准确度可能较低
2. 在低内存环境下，本功能会自动降级以减少资源消耗
3. 预测结果的置信度会在UI中显示，低置信度的预测应谨慎参考
4. 自动刷新频率会根据系统性能自动调整，以避免影响主程序性能 