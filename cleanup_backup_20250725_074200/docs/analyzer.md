# VisionAI-ClipsMaster 实时分析器

## 概述

实时分析器（Real-time Analyzer）是 VisionAI-ClipsMaster 监控系统的核心组件之一，提供了对系统指标的智能分析、趋势预测和模式识别功能。该模块专为低资源设备（4GB 内存/无 GPU）环境下运行的双模型架构（中文使用 Qwen2.5-7B，英文使用 Mistral-7B）设计，能够在资源受限的情况下提供高效的分析能力。

## 核心功能

### 1. 内存泄漏检测

* 使用线性回归分析近期内存使用趋势
* 实时计算内存增长速率（MB/s）
* 根据配置的阈值智能判断是否存在泄漏

### 2. OOM（内存耗尽）预测

* 基于当前内存使用和增长趋势预测可能的 OOM 时间
* 提供剩余运行时间估计（分钟/秒）
* 设置临界状态阈值，及时预警

### 3. 缓存效率分析

* 监控缓存命中率变化趋势
* 识别热点分片和冷分片
* 提供缓存健康评分
* 生成缓存优化建议

### 4. 模型性能趋势分析

* 跟踪模型推理时间和吞吐量变化
* 检测性能下降趋势
* 对比不同时间段的性能变化
* 分析中英文双模型的性能表现

### 5. 系统行为模式识别

* 使用 FFT（快速傅里叶变换）检测负载周期性模式
* 识别高负载和低负载时间段
* 提供带置信度的模式分析结果
* 生成基于模式的资源调度建议

## 技术实现

### 分析算法

* **内存泄漏检测**：使用线性回归计算内存增长斜率，与配置阈值比较
* **OOM 预测**：基于当前内存使用和增长率的线性预测
* **周期性检测**：使用 FFT 分析系统负载时间序列数据
* **性能变化检测**：比较前后时间段的平均性能指标

### 自适应能力

* 在 NumPy/SciPy 不可用时，提供简化的分析实现
* 根据数据量动态调整分析精度
* 支持多种数据格式（时间戳字符串或数值）

### 与监控系统集成

* 与数据采集器（`DataCollector`）集成获取原始数据
* 与阈值管理器（`DynamicThresholds`）集成获取动态阈值
* 提供回调机制用于结果通知

## 使用指南

### 基本使用

```python
from monitoring.analyzer import get_analyzer, run_analysis

# 获取分析器实例
analyzer = get_analyzer()

# 运行一次完整分析
result = run_analysis()

# 获取内存分析结果
memory_analysis = result.get("memory_analysis", {})
if memory_analysis.get("leak_detected", False):
    print(f"检测到内存泄漏！速率: {memory_analysis.get('leak_rate_mb_per_s')} MB/s")
    print(f"预计 {memory_analysis.get('time_to_oom_s')/60:.1f} 分钟后内存耗尽")

# 获取系统建议
recommendations = result.get("recommendations", [])
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec}")
```

### 自动分析

```python
from monitoring.analyzer import start_analysis, stop_analysis

# 启动自动分析（每5分钟一次）
start_analysis(interval=300)

# ... 应用运行 ...

# 停止自动分析
stop_analysis()
```

### 注册结果回调

```python
def on_analysis_result(result):
    """分析结果回调函数"""
    # 检查是否有紧急问题
    memory = result.get("memory_analysis", {})
    if memory.get("is_critical", False):
        print(f"紧急：内存即将耗尽！({memory.get('time_to_oom_s')/60:.1f} 分钟)")
        # 执行紧急措施

# 注册回调
analyzer = get_analyzer()
analyzer.register_result_callback(on_analysis_result)
```

### 导出分析结果

```python
# 导出为 JSON 格式
json_path = analyzer.export_analysis(format="json")
print(f"分析结果已导出到：{json_path}")

# 导出为 CSV 格式（仅主要指标）
csv_path = analyzer.export_analysis(format="csv")
```

## 配置参数

分析器的参数可通过 `configs/analyzer_config.yaml` 文件配置：

```yaml
# 内存泄漏检测配置
leak_threshold: 0.5      # 内存增长速率阈值 (MB/s)
leak_window: 300         # 用于检测泄漏的数据窗口大小 (秒)

# 内存预测配置
max_memory: 4096         # 系统可用最大内存 (MB)
prediction_window: 180   # 用于预测OOM的数据窗口大小 (秒)
critical_time: 600       # 临界状态阈值 (秒)

# 缓存分析配置
cache_efficiency_threshold: 0.7  # 缓存效率阈值
cache_analysis_window: 1800      # 缓存分析窗口大小 (秒)

# 模型性能配置
perf_degradation_threshold: 0.2  # 性能下降检测阈值
perf_analysis_window: 3600       # 性能分析窗口大小 (秒)

# 系统行为模式配置
pattern_window: 86400            # 模式分析窗口大小 (秒)
pattern_resolution: 300          # 模式识别分辨率 (秒)

# 自动分析配置
analysis_interval: 60            # 自动分析间隔 (秒)

# 模型特定参数
model_specific:
  # 中文模型 (Qwen2.5-7B)
  qwen:
    inference_threshold: 2000    # 推理时间阈值 (ms)
    tokens_per_second_threshold: 5  # 处理速度阈值 (tokens/s)
  
  # 英文模型 (Mistral-7B) - 预留配置
  mistral:
    inference_threshold: 2000
    tokens_per_second_threshold: 5
    enabled: false               # 默认禁用
```

## 可视化仪表盘

实时分析器提供了一个基于 Streamlit 的可视化仪表盘，用于直观展示分析结果和系统状态：

```bash
# 启动分析仪表盘
python -m ui.analyzer_dashboard
```

仪表盘主要功能：

1. 实时显示系统状态和关键指标
2. 内存使用和泄漏率趋势图
3. 缓存命中率和健康分曲线
4. 模型性能变化趋势
5. 热点分片可视化
6. 系统建议和预警历史
7. 支持手动触发分析和导出结果

## 与其他组件集成

### 与 MetricsIntegration 集成

分析器已与 `MetricsIntegration` 类集成，可以自动响应分析结果：

```python
from monitoring.metrics_integration import MetricsIntegration

# 创建集成实例
integration = MetricsIntegration(
    cache_manager=cache_manager,
    model_loader=model_loader
)

# 启动集成服务（包括分析器）
integration.start()

# 停止服务
integration.stop()
```

### 示例应用

参考 `src/monitoring/analyzer_example.py` 了解完整的使用示例。

## 系统要求

* Python 3.7+
* 推荐安装 NumPy 和 SciPy 以获得完整分析能力
* 对于可视化仪表盘：Streamlit, Plotly, Pandas
* 适用于 4GB RAM 及以上的设备
* 支持中英文双模型架构（Qwen2.5-7B / Mistral-7B）

## 注意事项

1. 分析器设计为资源友好型，即使在低配置设备上也能高效运行
2. 预测准确度依赖于数据采集的质量和数量
3. 在极低内存环境下推荐增大分析间隔以减少资源占用
4. 英文模型（Mistral-7B）的相关配置已预留，但默认禁用 