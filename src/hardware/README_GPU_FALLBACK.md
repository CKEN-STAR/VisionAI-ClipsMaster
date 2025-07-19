# GPU回退机制

VisionAI-ClipsMaster的GPU回退机制使系统能够智能选择最适合当前硬件环境的执行方式，确保在各种设备上都能获得最佳性能。无论是否有GPU，代码都能正常运行。

## 主要特性

- **智能设备选择**：自动检测GPU可用性及显存状态
- **优雅的回退路径**：GPU不可用时自动回退到CPU
- **CPU优化路径**：根据CPU支持的指令集(AVX512/AVX2/AVX)选择优化路径
- **内存优化**：根据设备可用资源动态调整内存使用
- **中英文模型支持**：为Qwen2.5-7B中文模型和Mistral-7B英文模型提供专门配置

## 用法示例

```python
# 简单用法 - 尝试GPU加速
from src.hardware.gpu_fallback import try_gpu_accel

# 加载模型
model = load_your_model()

# 尝试GPU加速 (自动回退到CPU)
model = try_gpu_accel(model)

# 正常使用模型
result = model(input_data)
```

### 获取设备信息
```python
from src.hardware.gpu_fallback import get_device_info

# 获取当前设备状态
device_info = get_device_info()
print(f"当前设备: {device_info['current_device']}")
print(f"CUDA可用: {device_info['cuda_available']}")
```

### 获取优化配置
```python
from src.hardware.gpu_fallback import get_gpu_fallback_manager

# 获取GPU回退管理器
manager = get_gpu_fallback_manager()

# 获取特定模型的优化配置
qwen_config = manager.get_optimized_config("qwen2.5-7b-zh")
print(f"Qwen配置: {qwen_config}")
```

## 集成到模型加载流程

```python
from src.hardware.gpu_fallback import try_gpu_accel, get_device_info

def load_model(model_path):
    """加载模型并应用设备优化"""
    # 加载模型
    model = ...  # 实际的模型加载代码
    
    # 应用GPU加速或CPU优化
    model = try_gpu_accel(model)
    
    # 打印设备信息
    device_info = get_device_info()
    print(f"模型已加载到{device_info['current_device']}设备")
    
    return model
```

## 优化级别

在CPU模式下，系统会根据指令集支持选择不同的优化级别:

| 优化级别 | 指令集 | 特点 |
|---------|--------|-----|
| AVX512 | AVX512 | 最高性能，适用于最新Intel处理器 |
| AVX2 | AVX2 | 高性能，适用于现代处理器 |
| AVX | AVX | 中等性能，适用于较旧处理器 |
| 基线 | 基本指令集 | 最佳兼容性，适用于所有CPU |

## 显存要求

默认情况下，使用GPU需要至少4GB可用显存。可以通过以下方式调整:

```python
from src.hardware.gpu_fallback import get_gpu_fallback_manager

# 设置最低显存要求为2GB
manager = get_gpu_fallback_manager(min_vram_mb=2048)

# 强制使用CPU (即使有GPU)
manager = get_gpu_fallback_manager(prefer_gpu=False)
``` 