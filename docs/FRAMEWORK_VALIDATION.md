# VisionAI-ClipsMaster 框架验证

框架验证工具用于检查项目结构、依赖和配置的完整性，确保开发和测试环境正确配置。

## 验证内容

框架验证会检查以下内容：

1. **目录结构** - 确保所有必要的目录存在
2. **配置文件** - 验证配置文件的存在和格式
3. **Python环境** - 检查Python版本和必要的依赖
4. **系统依赖** - 检查外部工具（如FFmpeg和Git）的可用性
5. **测试数据** - 验证测试数据和黄金样本是否存在

## 使用方法

### 方法1：使用根目录验证脚本

项目根目录提供了一个简单的验证脚本，可以在任何平台上运行：

```bash
# 在项目根目录下运行
python validate_framework.py
```

### 方法2：使用命令行工具

脚本目录提供了一个命令行工具，支持更多选项：

```bash
# 基本验证
python scripts/validate_framework.py

# 严格模式验证（将警告视为错误）
python scripts/validate_framework.py --strict

# 生成详细报告
python scripts/validate_framework.py --report
```

### 方法3：使用特定平台脚本

针对不同操作系统提供了优化的验证脚本：

#### Windows
```bash
# CMD或PowerShell中运行
tests\validate_framework.bat
```

#### Linux/macOS
```bash
# 在终端中运行
bash tests/validate_framework.sh
```

## 验证输出解释

验证输出使用以下符号表示不同状态：

- ✓ (绿色) - 检查通过
- ⚠ (黄色) - 警告，表示可能的问题但不影响基本功能
- ✗ (红色) - 错误，表示需要修复的问题

## 常见问题和解决方案

### 1. Python依赖缺失

如果缺少Python依赖，可以通过以下命令安装：

```bash
pip install -r requirements.txt
```

### 2. 缺少FFmpeg

FFmpeg是处理视频必需的工具，可以从[官方网站](https://ffmpeg.org/download.html)下载并安装。

### 3. 缺少模型配置文件

如果模型配置文件缺失，请确保：

1. 中文模型配置存在于 `models/chinese/config.json`
2. 英文模型配置存在于 `models/english/config.json`

## 自动修复

目前，框架验证工具只提供检测功能。将来的版本可能会添加自动修复选项来解决常见问题。

## 开发者说明

框架验证脚本位于以下位置：

- `tests/validate_framework.py` - Python主验证脚本，跨平台
- `tests/validate_framework.sh` - Linux/macOS的Bash脚本
- `tests/validate_framework.bat` - Windows的批处理脚本
- `scripts/validate_framework.py` - 命令行工具包装器
- `validate_framework.py` - 根目录简单启动器 