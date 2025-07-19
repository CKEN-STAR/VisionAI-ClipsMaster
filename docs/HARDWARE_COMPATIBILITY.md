# 硬件兼容性测试

本文档介绍如何使用VisionAI-ClipsMaster的硬件兼容性测试功能，检测系统的GPU兼容性并优化模型运行参数。

## 概述

VisionAI-ClipsMaster设计为能在多种硬件配置下运行，包括有无独立显卡的设备。硬件兼容性测试模块可以：

1. 检测系统上的所有GPU设备
2. 确定最佳的运行设备
3. 推荐最优的模型量化参数
4. 测试外接显卡的兼容性
5. 进行GPU压力测试
6. 监控系统资源使用情况

## 设备管理器

设备管理器是处理硬件资源的核心组件，负责检测硬件、分配资源和监控性能。

### 基本使用

```python
from src.utils.device_manager import device_manager

# 初始化设备管理器
info = device_manager.initialize()

# 获取最佳设备
device = device_manager.get_optimal_device()  # 返回 "cuda:0", "mps" 或 "cpu"

# 获取中文模型的推荐量化级别
quant_level = device_manager.get_recommended_quantization("qwen")

# 检查模型兼容性
meets_requirements, details = device_manager.check_model_requirements("qwen2.5-7b-zh")
if meets_requirements:
    print(f"系统可以运行Qwen2.5-7B模型，推荐量化: {details['recommended_quantization']}")
else:
    print(f"系统配置不足: {details['notes']}")

# 启动资源监控
device_manager.start_monitoring(interval=1.0)  # 每秒检查一次

# 获取当前资源使用情况
usage = device_manager.get_current_usage()
print(f"CPU使用率: {usage['cpu']}%")
print(f"内存使用率: {usage['memory']}%")
if device != "cpu":
    print(f"GPU使用率: {usage['gpu']}%")

# 停止资源监控
device_manager.stop_monitoring()
```

### 运行兼容性测试

```python
# 运行基本兼容性测试
result = device_manager.run_compatibility_test()

# 运行完整测试(包括GPU压力测试)
full_result = device_manager.run_compatibility_test(full_test=True)

# 检查结果
if result["success"]:
    if result["is_gpu_available"]:
        print(f"检测到可用GPU: {result['gpu_info']['summary']['best_api']}")
        for gpu_type, info in result["gpu_info"].items():
            if gpu_type != "summary" and info.get("available", False):
                print(f"- {gpu_type.upper()} GPU: {info.get('count', 0)}个设备")
    else:
        print("未检测到GPU，将使用CPU模式")
else:
    print(f"兼容性测试失败: {result.get('message')}")
```

## 外部GPU测试工具

项目提供了专门的命令行工具来测试外部GPU兼容性，对于连接了外接GPU的用户特别有用。

### 命令行参数

```
python tests/device_compatibility/run_external_gpu_test.py --help
```

可用参数：

- `--stress-test`: 执行GPU压力测试
- `--stress-duration <seconds>`: 设置压力测试持续时间（秒）
- `--detect-only`: 仅检测GPU设备，不执行其他测试
- `--connect-egpu <name>`: 尝试连接指定名称的外接GPU
- `--model-compatibility`: 检查GPU与项目模型的兼容性
- `--output-json <file>`: 将测试结果保存为JSON文件
- `--log-level <level>`: 设置日志级别 (debug/info/warning/error/critical)
- `--no-color`: 禁用彩色输出
- `--check-changes`: 检测GPU状态变化

### 示例用法

基本GPU检测：
```bash
python tests/device_compatibility/run_external_gpu_test.py
```

执行完整测试：
```bash
python tests/device_compatibility/run_external_gpu_test.py --stress-test --model-compatibility
```

检查外接GPU：
```bash
python tests/device_compatibility/run_external_gpu_test.py --connect-egpu "Razer Core X"
```

保存测试结果：
```bash
python tests/device_compatibility/run_external_gpu_test.py --stress-test --output-json "./results/gpu_test_results.json"
```

## UI集成

硬件兼容性检查已集成到主界面中。用户可以通过点击"检测GPU硬件"按钮来检查系统GPU状态。

## 针对低配置设备的优化

如果检测到设备配置较低，系统会自动采取以下优化措施：

1. 使用高度量化的模型（如Q2_K或Q3_K）减少内存占用
2. 降低批处理大小
3. 限制上下文窗口长度
4. 处理较小分辨率的视频

## 支持的GPU类型

- NVIDIA GPU：通过CUDA加速
- AMD GPU：通过ROCm加速（实验性）
- Intel集成显卡：通过oneAPI加速（有限支持）
- Apple Silicon：通过Metal API加速

## 故障排除

如果遇到GPU兼容性问题，可尝试以下步骤：

1. 确保安装了最新的GPU驱动程序
2. 检查PyTorch是否为GPU版本 (`torch.cuda.is_available()` 应返回 `True`)
3. 尝试强制使用CPU模式：`device_manager.initialize(force_cpu=True)`
4. 检查是否有足够的内存和显存
5. 运行外部GPU测试工具获取详细诊断信息

## 参考

更多信息请参阅以下文件：

- `src/utils/device_manager.py`: 设备管理器实现
- `tests/device_compatibility/peripheral_test.py`: GPU兼容性测试实现
- `tests/device_compatibility/run_external_gpu_test.py`: 命令行测试工具

如有问题，请联系技术支持或查看项目文档。 