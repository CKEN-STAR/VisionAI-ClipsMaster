# GGUF模型转换功能安装指南

## 📋 概述

本文档说明如何安装和配置GGUF模型转换功能，使VisionAI-ClipsMaster能够将HuggingFace格式的模型转换为GGUF格式。

## 🎯 功能说明

### 什么是GGUF转换？

GGUF（GPT-Generated Unified Format）是一种优化的模型格式，具有以下优势：

| 特性 | HuggingFace格式 | GGUF格式 | 优势 |
|------|----------------|---------|------|
| **推理速度** | 1x（基准） | **3-5x** | GGUF快3-5倍 |
| **内存占用** | 1x（基准） | **0.25-0.5x** | GGUF节省50-75% |
| **模型大小** | ~14GB（7B FP16） | **~4GB（7B Q4_K_M）** | GGUF小70% |
| **训练支持** | ✅ 完整支持 | ❌ 不支持 | HF独有 |
| **CPU推理** | 慢 | **快** | GGUF优化更好 |

### 双轨道设计

```
训练轨道（HuggingFace格式）
    ↓
[训练] → [保存HF格式] → [增量训练]
    ↓
推理轨道（GGUF格式）
    ↓
[GGUF转换] → [推理引擎]
```

## 🔧 安装步骤

### 步骤1：安装Python依赖

所有必需的Python包已包含在 `requirements.txt` 中：

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖（如果还没安装）
pip install -r requirements.txt
```

**关键依赖**：
- `torch>=2.9.0` - PyTorch深度学习框架
- `transformers>=4.45.1` - HuggingFace模型库
- `gguf>=0.1.0` - GGUF格式支持
- `sentencepiece>=0.2.0` - Tokenizer支持
- `numpy>=1.26.4` - 数值计算库

### 步骤2：克隆llama.cpp仓库

llama.cpp提供了HF→GGUF的转换工具：

```bash
# 在项目根目录执行
git clone --depth 1 https://github.com/ggerganov/llama.cpp.git

# 如果GitHub访问慢，使用镜像：
git clone --depth 1 https://gitclone.com/github.com/ggerganov/llama.cpp.git
```

**验证安装**：
```bash
# 检查转换脚本是否存在
Test-Path "llama.cpp\convert_hf_to_gguf.py"
# 应该输出: True
```

### 步骤3：测试转换功能

运行测试脚本验证安装：

```bash
python scripts\test_gguf_conversion.py
```

**预期输出**：
```
🚀 开始GGUF转换功能测试

======================================================================
测试1: 检查llama.cpp转换脚本
======================================================================
✅ 转换脚本存在: D:\...\llama.cpp\convert_hf_to_gguf.py

======================================================================
测试2: 检查Python依赖
======================================================================
✅ PyTorch 已安装
✅ Transformers 已安装
✅ NumPy 已安装
✅ GGUF 已安装
✅ SentencePiece 已安装

======================================================================
测试3: 测试ModelConverter类
======================================================================
✅ ModelConverter初始化成功
   支持的格式: ['pytorch', 'onnx', 'tensorrt', 'gguf']
   支持的量化: ['Q4_K_M', 'Q5_K', 'Q2_K', 'Q8_0']

======================================================================
📊 测试结果汇总
======================================================================
转换脚本检查: ✅ 通过
Python依赖检查: ✅ 通过
ModelConverter测试: ✅ 通过
======================================================================
🎉 所有测试通过！GGUF转换功能已就绪
```

### 步骤4：编译量化工具（可选，推荐）

如果需要K-quants量化（Q4_K_M, Q5_K, Q2_K），需要编译llama.cpp：

#### Windows (使用Visual Studio)

```bash
# 1. 安装Visual Studio 2019/2022（包含C++工作负载）
# 下载：https://visualstudio.microsoft.com/

# 2. 编译llama.cpp
cd llama.cpp
cmake -B build -G "Visual Studio 16 2019" -A x64
cmake --build build --config Release

# 3. 验证
Test-Path "build\bin\Release\quantize.exe"
```

#### Windows (使用MinGW)

```bash
# 1. 安装MinGW-w64
# 下载：https://www.mingw-w64.org/

# 2. 编译llama.cpp
cd llama.cpp
make

# 3. 验证
Test-Path "quantize.exe"
```

**注意**：如果不编译量化工具，转换功能仍然可用，但只能转换为F16/F32/Q8_0格式，无法使用K-quants（Q4_K_M等）。

## 📖 使用方法

### 方法1：通过UI界面转换

1. 打开VisionAI-ClipsMaster主界面
2. 进入"模型管理"或"训练"标签页
3. 找到"转换为GGUF"按钮
4. 选择要转换的HF模型
5. 选择量化级别（Q4_K_M推荐）
6. 点击"开始转换"

### 方法2：通过Python代码转换

```python
from models.converters.model_converter import ModelConverter

# 创建转换器
converter = ModelConverter()

# 转换模型
result = converter.convert_format(
    model_path="models/qwen/base",  # HF模型路径
    output_format='gguf',
    output_path="models/qwen/quantized/model_Q4_K_M.gguf",
    quant_type='Q4_K_M'  # 量化级别
)

print(f"转换完成: {result}")
```

### 方法3：通过命令行转换

```bash
# 直接使用llama.cpp转换脚本
python llama.cpp\convert_hf_to_gguf.py ^
    models\qwen\base ^
    --outfile models\qwen\quantized\model_f16.gguf ^
    --outtype f16
```

## 🎨 支持的量化级别

| 量化级别 | 说明 | 模型大小 | 质量保持率 | 推荐场景 |
|---------|------|---------|-----------|---------|
| **F32** | 32位浮点 | 100% | 100% | 研究/基准测试 |
| **F16** | 16位浮点 | 50% | 99.9% | 高质量推理 |
| **Q8_0** | 8位量化 | 25% | 99% | 平衡质量和速度 |
| **Q4_K_M** | 4位K-quants | 12.5% | 95% | **推荐**（最佳平衡） |
| **Q5_K** | 5位K-quants | 15.6% | 97% | 高质量需求 |
| **Q2_K** | 2位K-quants | 6.25% | 85% | 极低内存设备 |

**推荐配置**：
- **4GB内存设备**：Q2_K
- **8GB内存设备**：Q4_K_M（推荐）
- **16GB+内存设备**：Q5_K或Q8_0

## ⚙️ 硬件需求

### 转换时的硬件需求

| 模型大小 | 量化级别 | 转换时内存需求 | 推荐配置 | 转换时间 |
|---------|---------|---------------|---------|---------|
| **Qwen2.5-1.5B** | Q4_K_M | **~4GB** | 8GB RAM | 2-5分钟 |
| **Qwen2.5-7B** | Q4_K_M | **~8GB** | 16GB RAM | 5-15分钟 |
| **Mistral-7B** | Q5_K | **~10GB** | 16GB RAM | 8-20分钟 |

**重要提示**：
- ✅ 转换**不需要GPU**（CPU即可）
- ✅ 转换时内存需求 ≤ 运行时内存需求
- ✅ 如果设备能运行某个模型，就能转换它

### 最低配置要求

**与程序运行配置一致**：
- **CPU**: 2核心以上（推荐4核+）
- **内存**: 3-4GB可用内存
- **磁盘**: 10-20GB可用空间
- **GPU**: 不需要（可选加速）

## 🔍 故障排除

### 问题1：找不到convert_hf_to_gguf.py

**错误信息**：
```
FileNotFoundError: Conversion script not found at llama.cpp/convert_hf_to_gguf.py
```

**解决方法**：
```bash
# 克隆llama.cpp仓库
git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
```

### 问题2：缺少Python依赖

**错误信息**：
```
ModuleNotFoundError: No module named 'gguf'
```

**解决方法**：
```bash
pip install gguf sentencepiece
```

### 问题3：protobuf版本冲突

**错误信息**：
```
TypeError: Descriptors cannot not be created directly.
```

**解决方法**：
```bash
# 降级protobuf到兼容版本
pip install protobuf==4.25.3
```

### 问题4：无法使用K-quants量化

**现象**：转换后得到F16格式而不是Q4_K_M

**原因**：未编译llama.cpp的quantize工具

**解决方法**：
1. 安装Visual Studio或MinGW
2. 编译llama.cpp（见步骤4）
3. 或者使用F16/Q8_0格式（不需要编译）

## 📚 相关文档

- [双轨道设计文档](DUAL_TRACK_DESIGN.md)
- [训练工作流程](TRAINING_WORKFLOW.md)
- [模型选择策略](MODEL_SELECTION_STRATEGY.md)
- [量化系统指南](QUANTIZATION_GUIDE.md)

## ✅ 验证清单

安装完成后，请确认以下项目：

- [ ] llama.cpp仓库已克隆到项目根目录
- [ ] `llama.cpp/convert_hf_to_gguf.py` 文件存在
- [ ] Python依赖已安装（torch, transformers, gguf等）
- [ ] 测试脚本运行成功（`python scripts\test_gguf_conversion.py`）
- [ ] （可选）quantize工具已编译

## 🎉 完成

恭喜！GGUF转换功能已成功安装。您现在可以：

1. ✅ 将训练后的HF模型转换为GGUF格式
2. ✅ 享受3-5倍的推理速度提升
3. ✅ 节省50-75%的内存占用
4. ✅ 在低配设备上流畅运行大模型

**下一步**：
- 训练您的第一个模型（参见 [训练使用指南](guides/training/TRAINING_USAGE_GUIDE.md)）
- 转换模型为GGUF格式
- 使用转换后的模型进行推理

