# GPU 加速

VisionAI-ClipsMaster 提供强大的 GPU 加速功能，可以显著提高视频处理和比较的性能。本文档介绍了 GPU 加速的实现方式、配置方法以及性能优势。

## 功能概述

GPU 加速主要用于以下功能：

1. **视频帧比较**：使用 GPU 加速计算帧之间的相似度指标，包括 PSNR、直方图相似度等
2. **视觉质量评估**：加速 SSIM、MSE 等质量指标的计算
3. **颜色处理**：HSV 颜色空间转换和直方图计算
4. **视频处理**：帧调整大小、过滤器应用等操作

## 性能优势

GPU 加速可以带来显著的性能提升，根据测试结果：

- **帧比较**：从 CPU 的 15 帧/秒提升到 GPU 的 240 帧/秒（约 16 倍加速）
- **视频处理**：大多数操作获得 5-10 倍的性能提升
- **批量处理**：处理大量视频时，整体性能提升更为明显

## 支持的硬件

VisionAI-ClipsMaster 支持多种 GPU 加速后端：

1. **NVIDIA CUDA**：提供最佳性能，推荐使用 NVIDIA GPU
2. **OpenCL**：支持 AMD、Intel 等多种 GPU
3. **CPU 回退**：在 GPU 不可用时自动回退到优化的 CPU 实现

## 系统要求

### NVIDIA GPU 支持

- NVIDIA GPU（最低要求：Pascal 架构/GTX 1060 或更高）
- CUDA Toolkit 11.0+
- CUDA 驱动（适合您的 GPU）
- 至少 4GB 显存（可配置）

### 其他 GPU 支持（OpenCL）

- 支持 OpenCL 1.2+ 的 GPU
- 安装正确的 GPU 驱动
- OpenCL 运行时

## 安装指南

### 1. 安装 GPU 加速依赖

```bash
# 安装基本依赖
pip install -r requirements.txt

# 如需对 CUDA 版本有特殊要求，可使用以下方式安装特定版本
# pip install cupy-cuda12x  # 对于 CUDA 12.x
# pip install cupy-cuda11x  # 对于 CUDA 11.x
```

### 2. 验证 GPU 支持

运行以下命令检测系统 GPU 加速能力：

```bash
python -m src.demos.hw_detector_demo
```

输出会显示可用的加速能力，例如 CUDA、OpenCL 等。

## 使用方法

### 视频比较示例

```python
from src.core.video_comparison import VideoCompare, compare_videos

# 方法 1：便捷函数（默认启用 GPU 加速）
result = compare_videos("video1.mp4", "video2.mp4")

# 方法 2：手动控制
# 创建比较器（默认使用 GPU）
comparator = VideoCompare(use_gpu=True)

# 比较两个视频
result = comparator.compare_videos("video1.mp4", "video2.mp4")

# 比较两个帧
frame1 = cv2.imread("frame1.jpg")
frame2 = cv2.imread("frame2.jpg")
similarity = comparator.compare_frames(frame1, frame2)
```

### 配置 GPU 内存使用

可以调整最小显存要求，适应不同的硬件环境：

```python
from src.core.video_comparison import VideoCompare

# 将最小显存要求设为 2GB（默认为 1GB）
comparator = VideoCompare(use_gpu=True, min_vram_mb=2048)
```

## 性能基准测试

可以使用提供的基准测试工具来评估 GPU 加速效果：

```bash
# 帧比较性能测试
python -m tests.performance.test_video_comparison_perf --video path/to/video.mp4

# 视频比较性能测试
python -m tests.performance.test_video_comparison_perf --video1 path/to/video1.mp4 --video2 path/to/video2.mp4
```

测试结果会生成性能对比图，保存在 `tests/performance/results/` 目录下。

## 智能回退机制

VisionAI-ClipsMaster 实现了智能回退机制，确保在不同硬件环境下的兼容性：

1. **设备检测**：启动时自动检测可用的 GPU 和显存
2. **优雅降级**：如果 GPU 不可用或显存不足，自动回退到 CPU
3. **操作级回退**：部分操作如果在 GPU 上失败，会自动切换到 CPU 实现
4. **CPU 优化**：回退到 CPU 时使用 SIMD 指令集优化（AVX2/AVX）

## 常见问题

### 如何确定 GPU 是否正在使用？

检查程序输出的日志，应该包含类似以下内容：

```
成功初始化CUDA加速
当前设备: cuda
```

或者在代码中查询设备状态：

```python
from src.core.video_comparison import get_video_comparator

comparator = get_video_comparator()
print(f"当前设备: {comparator.device}")
```

### GPU 加速无法工作？

1. 确保已安装正确的 CUDA 工具包和驱动
2. 检查 `opencv-contrib-python` 是否正确安装
3. 验证 GPU 是否被其他程序占用
4. 使用 `nvidia-smi` 命令检查 GPU 状态

### 如何强制使用 CPU？

```python
from src.core.video_comparison import VideoCompare

# 强制使用 CPU
comparator = VideoCompare(use_gpu=False)
```

## 未来改进

计划中的 GPU 加速改进：

1. **TensorRT 集成**：进一步优化深度学习模型推理
2. **批处理优化**：提高大批量视频处理的并行性
3. **混合精度**：支持 FP16 计算以提高性能
4. **多 GPU 支持**：在多 GPU 系统上分配工作负载 