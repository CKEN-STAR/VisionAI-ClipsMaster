# 硬件检测器模块 (Hardware Detector)

此模块为 VisionAI-ClipsMaster 提供硬件加速能力检测，能够自动发现系统可用的硬件加速资源。

## 主要功能

- 检测 NVIDIA CUDA/NVENC/NVDEC 加速能力
- 检测 Intel Quick Sync Video (QSV) 加速能力
- 检测 AMD VCE/AMF 加速能力
- 检测 CPU 指令集加速 (AVX, AVX2)
- 检测通用计算加速 (OpenCL, Vulkan)
- 零拷贝内存传输支持检测
- 生成硬件加速能力报告

## 使用方法

### 基本用法

```python
from src.exporters.hw_detector import detect_zero_copy_acceleration

# 获取支持零拷贝的加速器列表
accelerators = detect_zero_copy_acceleration()
print(f"支持零拷贝的加速器: {accelerators}")

# 示例输出: 支持零拷贝的加速器: ['nvidia_nvdec', 'intel_qsv']
```

### 获取全面硬件加速支持情况

```python
from src.exporters.hw_detector import get_detected_acceleration, AccelerationType

# 获取所有硬件加速支持情况
acceleration = get_detected_acceleration()

# 检查特定加速类型
if acceleration[AccelerationType.NVIDIA_CUDA]:
    print("系统支持NVIDIA CUDA加速")

if acceleration[AccelerationType.INTEL_QSV]:
    print("系统支持Intel Quick Sync Video加速")

if acceleration[AccelerationType.ZERO_COPY]:
    print("系统支持零拷贝内存传输")
```

### 获取CUDA设备详细信息

```python
from src.exporters.hw_detector import get_cuda_device_info

# 获取CUDA设备信息
cuda_info = get_cuda_device_info()

if cuda_info["available"]:
    print(f"CUDA版本: {cuda_info['cuda_version']}")
    print(f"驱动版本: {cuda_info['driver_version']}")
    
    for device in cuda_info["devices"]:
        print(f"设备: {device['name']}")
        print(f"内存: {device['total_memory_mb']} MB")
        print(f"计算能力: {device['capability']}")
```

### 生成硬件加速报告

```python
from src.exporters.hw_detector import print_acceleration_report

# 打印完整的硬件加速能力报告
print_acceleration_report()
```

## 支持的加速类型

模块定义了 `AccelerationType` 枚举类，包含以下类型：

- `NVIDIA_CUDA`: NVIDIA CUDA 通用计算加速
- `NVIDIA_NVENC`: NVIDIA 视频编码加速
- `NVIDIA_NVDEC`: NVIDIA 视频解码加速
- `INTEL_QSV`: Intel Quick Sync Video 加速
- `INTEL_MFX`: Intel Media SDK 加速
- `AMD_AMF`: AMD Advanced Media Framework 加速
- `AMD_VCE`: AMD Video Coding Engine 加速
- `OPENCL`: OpenCL 通用计算加速
- `VULKAN`: Vulkan 计算加速
- `CPU_AVX`: CPU AVX 指令集加速
- `CPU_AVX2`: CPU AVX2 指令集加速
- `ZERO_COPY`: 零拷贝内存传输支持

## 依赖关系

硬件检测器模块尽量减少外部依赖，但某些特定功能检测可能需要以下可选依赖：

- PyTorch (CUDA 检测)
- PyOpenCL (OpenCL 检测)
- pynvml (NVIDIA 详细信息)
- py-cpuinfo (CPU 指令集检测)

未安装上述依赖不会导致模块失效，只会使用替代方法进行检测或跳过特定检测。

## 注意事项

1. 某些硬件加速检测可能需要管理员/root权限
2. 在容器化环境中，硬件检测可能不准确
3. 驱动版本过低可能导致硬件加速不可用
4. 实际加速效果取决于硬件能力和软件实现 