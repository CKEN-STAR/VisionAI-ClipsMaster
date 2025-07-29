# 📥 VisionAI-ClipsMaster 中文安装指南

> **详细的中文安装配置教程** - 让您轻松上手

## 🎯 安装概述

VisionAI-ClipsMaster支持多种安装方式，从简单的一键安装到专业的开发环境配置。本指南将帮助您选择最适合的安装方法。

## 📋 系统要求

### 最低配置要求
```
操作系统: Windows 10 (版本1903+)
处理器: Intel i5-8400 / AMD Ryzen 5 2600
内存: 4GB RAM
存储: 2GB 可用空间
网络: 宽带连接 (用于下载模型)
```

### 推荐配置
```
操作系统: Windows 11
处理器: Intel i7-10700 / AMD Ryzen 7 3700X
内存: 8GB+ RAM
存储: 5GB+ 可用空间 (SSD推荐)
显卡: NVIDIA GTX 1060+ / AMD RX 580+ (可选)
```

### 软件依赖
- **Python**: 3.11.0 或更高版本 (推荐 3.13.x)
- **Git**: 用于克隆项目 (可选)
- **Visual Studio**: 用于编译某些依赖 (可选)

## 🚀 快速安装 (推荐新手)

### 方法1: 一键安装脚本

1. **下载项目**
   ```bash
   # 使用Git克隆 (推荐)
   git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
   cd VisionAI-ClipsMaster
   
   # 或直接下载ZIP包
   # 下载后解压到任意目录
   ```

2. **运行安装脚本**
   ```bash
   # Windows用户 (双击运行)
   install_deps.bat
   
   # 或使用PowerShell
   .\install_dependencies.ps1
   ```

3. **等待安装完成**
   - 脚本会自动检测Python环境
   - 创建虚拟环境
   - 安装所有必需依赖
   - 下载基础AI模型

4. **启动程序**
   ```bash
   # 双击启动文件
   packaging\启动VisionAI-ClipsMaster.bat

   # 或命令行启动
   python simple_ui_fixed.py
   ```

### 方法2: 便携版安装 (免配置)

1. **下载便携版**
   - 访问 [Releases页面](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/releases)
   - 下载 `VisionAI-ClipsMaster-Portable.zip`

2. **解压运行**
   ```
   解压到任意目录 → 双击 VisionAI-ClipsMaster.exe
   ```

3. **首次运行配置**
   - 程序会自动检测系统配置
   - 根据内存大小选择合适的模型
   - 无需额外配置即可使用

## 🔧 手动安装 (开发者)

### 步骤1: 环境准备

1. **安装Python**
   ```bash
   # 下载Python 3.13.x
   https://www.python.org/downloads/
   
   # 安装时勾选 "Add Python to PATH"
   # 验证安装
   python --version
   pip --version
   ```

2. **安装Git (可选)**
   ```bash
   # 下载Git for Windows
   https://git-scm.com/download/win
   
   # 验证安装
   git --version
   ```

### 步骤2: 项目配置

1. **克隆项目**
   ```bash
   git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
   cd VisionAI-ClipsMaster
   ```

2. **创建虚拟环境**
   ```bash
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   venv\Scripts\activate  # Windows
   
   # 验证环境
   which python  # 应该指向venv目录
   ```

3. **安装依赖**
   ```bash
   # 升级pip
   python -m pip install --upgrade pip
   
   # 安装基础依赖
   pip install -r requirements.txt
   
   # 安装测试依赖 (可选)
   pip install -r requirements_test.txt
   ```

### 步骤3: 模型配置

1. **自动配置 (推荐)**
   ```bash
   # 根据硬件自动配置
   python configure_model_by_hardware.py
   ```

2. **手动下载模型**
   ```bash
   # 下载中文模型
   python scripts/download_models.py --model qwen2.5-7b-zh
   
   # 下载英文模型
   python scripts/download_models.py --model mistral-7b-en
   ```

3. **验证模型**
   ```bash
   # 检查模型状态
   python scripts/verify_models.py
   ```

### 步骤4: 功能测试

1. **运行基础测试**
   ```bash
   # 测试核心功能
   python test_core_video_processing.py
   
   # 测试UI界面
   python test_simple_ui_fixed_log_viewer.py
   ```

2. **启动程序**
   ```bash
   # 启动主UI程序（推荐）
   python simple_ui_fixed.py

   # 或启动命令行版本
   python main.py
   ```

## 🐳 Docker安装 (高级用户)

### 使用预构建镜像

1. **拉取镜像**
   ```bash
   docker pull visionai/clipsmaster:latest
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name visionai-app \
     -p 8080:8080 \
     -v /path/to/videos:/app/data/input \
     -v /path/to/output:/app/data/output \
     visionai/clipsmaster:latest
   ```

### 自定义构建

1. **构建镜像**
   ```bash
   # 克隆项目
   git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
   cd VisionAI-ClipsMaster
   
   # 构建镜像
   docker build -t visionai-clipsmaster .
   ```

2. **运行容器**
   ```bash
   docker-compose up -d
   ```

## ⚙️ 配置优化

### 内存优化配置

1. **低内存设备 (4GB)**
   ```yaml
   # configs/memory_optimization.json
   {
     "quantization_level": "Q2_K",
     "max_memory_usage": "3.5GB",
     "enable_swap": true,
     "model_offload": true
   }
   ```

2. **标准配置 (8GB)**
   ```yaml
   {
     "quantization_level": "Q4_K_M",
     "max_memory_usage": "6GB",
     "enable_cache": true,
     "parallel_processing": true
   }
   ```

### GPU加速配置

1. **NVIDIA GPU**
   ```bash
   # 安装CUDA支持
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   
   # 验证GPU支持
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **AMD GPU**
   ```bash
   # 安装ROCm支持
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.6
   ```

## 🔧 故障排除

### 常见安装问题

**问题1: Python版本不兼容**
```bash
# 解决方案: 安装正确的Python版本
pyenv install 3.13.0  # 使用pyenv管理版本
pyenv local 3.13.0
```

**问题2: 依赖安装失败**
```bash
# 解决方案: 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

**问题3: 模型下载失败**
```bash
# 解决方案: 手动下载模型
# 1. 访问 https://huggingface.co/
# 2. 搜索对应模型
# 3. 下载到 models/ 目录
```

**问题4: 权限错误**
```bash
# 解决方案: 以管理员身份运行
# 右键 → "以管理员身份运行"
```

### 性能优化建议

1. **关闭不必要的程序**
   - 释放内存空间
   - 减少CPU占用

2. **使用SSD存储**
   - 提高文件读写速度
   - 减少模型加载时间

3. **调整虚拟内存**
   - 设置为物理内存的1.5-2倍
   - 放在SSD上效果更好

## 📞 获取帮助

如果安装过程中遇到问题:

1. **查看日志文件**
   ```bash
   # 查看安装日志
   cat logs/installation.log
   
   # 查看运行日志
   cat logs/visionai.log
   ```

2. **运行诊断工具**
   ```bash
   # 系统环境检查
   python scripts/check_environment.py
   
   # 依赖验证
   python verify_dependencies.py
   ```

3. **寻求帮助**
   - [GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
   - [故障排除指南](../../TROUBLESHOOTING.md)
   - [常见问题解答](../../FAQ.md)

---

**安装完成后，您就可以开始体验AI驱动的短剧混剪功能了！** 🎬✨
