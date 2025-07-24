# 📥 VisionAI-ClipsMaster 安装指南

## 🔧 环境准备

### 📋 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| **操作系统** | Windows 10 | Windows 11 |
| **Python** | 3.11+ | 3.11.7+ |
| **内存** | 4GB RAM | 8GB+ RAM |
| **存储** | 10GB 可用空间 | 20GB+ 可用空间 |
| **显卡** | 集成显卡 | NVIDIA/AMD 独立显卡 |

### 🐍 Python环境配置

#### 方法1: 使用系统Python（推荐）

1. **下载Python 3.11+**
   ```
   访问: https://www.python.org/downloads/
   下载: Python 3.11.7 或更新版本
   ```

2. **安装Python**
   - ✅ 勾选 "Add Python to PATH"
   - ✅ 勾选 "Install for all users"
   - 选择 "Customize installation"
   - ✅ 勾选所有可选功能

3. **验证安装**
   ```bash
   # 打开命令提示符
   python --version
   pip --version
   ```

#### 方法2: 使用Anaconda（可选）

```bash
# 下载Anaconda
# 访问: https://www.anaconda.com/products/distribution

# 创建虚拟环境
conda create -n visionai python=3.11
conda activate visionai
```

### 🔧 系统依赖

#### FFmpeg安装（必需）

1. **下载FFmpeg**
   ```
   访问: https://ffmpeg.org/download.html#build-windows
   下载: Windows builds by BtbN
   ```

2. **解压并配置**
   ```bash
   # 解压到项目目录
   D:\zancun\VisionAI-ClipsMaster\tools\ffmpeg\bin\
   
   # 或添加到系统PATH
   # 控制面板 > 系统 > 高级系统设置 > 环境变量
   # 在PATH中添加FFmpeg的bin目录
   ```

3. **验证安装**
   ```bash
   ffmpeg -version
   ```

#### Visual C++ Build Tools（Windows）

如果遇到编译错误，请安装：
```
下载: Microsoft C++ Build Tools
访问: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

---

## 🚀 快速安装

### ⚡ 一键安装脚本

```bash
# 1. 克隆仓库
git clone https://github.com/CKEN/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 运行安装脚本
install.bat
```

### 📝 手动安装步骤

#### 1. 克隆仓库
```bash
git clone https://github.com/CKEN/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster
```

#### 2. 安装Python依赖
```bash
# 使用清华镜像源（推荐）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或使用官方源
pip install -r requirements.txt
```

#### 3. 验证安装
```bash
cd VisionAI-ClipsMaster-Core
python simple_ui_fixed.py
```

---

## 🎯 详细安装步骤

### 1️⃣ 核心依赖安装

```bash
# GUI框架
pip install PyQt6>=6.5.0

# 系统监控
pip install psutil>=5.9.0

# 网络请求
pip install requests>=2.31.0

# 自然语言处理
pip install spacy>=3.7.0 langdetect>=1.0.9

# AI模型支持
pip install torch>=2.0.0 transformers>=4.30.0 huggingface-hub>=0.16.0
```

### 2️⃣ 可选依赖安装

```bash
# 图像处理（可选）
pip install opencv-python>=4.8.0

# 音视频处理（可选）
pip install ffmpeg-python>=0.2.0

# 数据处理（可选）
pip install pandas>=2.0.0 numpy>=1.24.0
```

### 3️⃣ 开发工具（开发者）

```bash
# 测试工具
pip install pytest>=7.4.0 pytest-cov>=4.1.0

# 代码格式化
pip install black>=23.7.0 flake8>=6.0.0

# 类型检查
pip install mypy>=1.5.0
```

---

## 🔧 配置说明

### 📁 目录结构

安装完成后的目录结构：
```
VisionAI-ClipsMaster/
├── VisionAI-ClipsMaster-Core/    # 核心应用
│   ├── simple_ui_fixed.py        # 主程序入口
│   ├── src/                      # 源代码
│   ├── models/                   # AI模型存储
│   └── tools/                    # 外部工具
├── docs/                         # 文档
├── requirements.txt              # 依赖列表
└── README.md                     # 项目说明
```

### ⚙️ 配置文件

#### 1. 模型配置
```bash
# 创建模型配置目录
mkdir VisionAI-ClipsMaster-Core\models\configs

# 模型会在首次使用时自动下载
```

#### 2. FFmpeg配置
```bash
# 方法1: 项目内配置（推荐）
# 解压FFmpeg到: VisionAI-ClipsMaster-Core\tools\ffmpeg\bin\

# 方法2: 系统PATH配置
# 添加FFmpeg路径到系统环境变量
```

---

## 🚀 启动应用

### 🖥️ 图形界面启动

```bash
# 进入核心目录
cd VisionAI-ClipsMaster-Core

# 启动应用
python simple_ui_fixed.py
```

### 🔧 使用系统Python（推荐）

```bash
# 使用完整路径启动（避免编码问题）
C:\Users\[用户名]\AppData\Local\Programs\Python\Python313\python.exe simple_ui_fixed.py
```

### 📊 验证启动

成功启动后应该看到：
```
============================================================
VisionAI-ClipsMaster 启动中...
============================================================
[OK] QApplication 创建成功
[OK] 应用样式设置成功
[OK] 窗口显示成功
窗口标题: 🎬 VisionAI-ClipsMaster - AI短剧混剪大师 v1.0.0
============================================================
UI已启动，等待用户交互...
============================================================
```

---

## ❗ 常见问题解决

### 🐛 编码问题

**问题**: `UnicodeEncodeError` 或中文显示异常

**解决方案**:
```bash
# 1. 使用系统Python解释器
C:\Users\[用户名]\AppData\Local\Programs\Python\Python313\python.exe simple_ui_fixed.py

# 2. 设置环境变量
set PYTHONIOENCODING=utf-8
python simple_ui_fixed.py
```

### 🔧 依赖安装失败

**问题**: `pip install` 失败或超时

**解决方案**:
```bash
# 1. 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 2. 升级pip
python -m pip install --upgrade pip

# 3. 单独安装失败的包
pip install [包名] --no-cache-dir
```

### 💾 内存不足

**问题**: 4GB内存设备运行缓慢

**解决方案**:
1. **使用量化模型**: 应用会自动推荐Q2_K模型
2. **关闭其他应用**: 释放更多内存
3. **调整虚拟内存**: 增加页面文件大小

### 🎬 FFmpeg问题

**问题**: 视频处理功能不可用

**解决方案**:
```bash
# 1. 验证FFmpeg安装
ffmpeg -version

# 2. 检查路径配置
# 确保FFmpeg在PATH中或项目tools目录中

# 3. 重新下载FFmpeg
# 访问: https://ffmpeg.org/download.html
```

### 🤖 AI模型下载失败

**问题**: 模型下载超时或失败

**解决方案**:
1. **检查网络连接**: 确保可以访问Hugging Face
2. **使用代理**: 如果网络受限，配置代理
3. **手动下载**: 从镜像站下载模型文件
4. **使用量化模型**: 选择更小的模型版本

---

## 🎯 性能优化

### 💾 内存优化

```bash
# 1. 使用量化模型
# 应用启动时选择Q2_K或Q4_K_M版本

# 2. 调整Python内存限制
set PYTHONMALLOC=malloc
python simple_ui_fixed.py
```

### ⚡ 启动优化

```bash
# 1. 预热Python环境
python -c "import PyQt6; print('PyQt6 ready')"

# 2. 使用SSD存储
# 将项目放在SSD上以提高I/O性能
```

### 🎮 GPU加速

```bash
# 如果有NVIDIA显卡
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证GPU可用性
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 📞 技术支持

### 🔍 日志查看

```bash
# 查看应用日志
# 日志文件位置: VisionAI-ClipsMaster-Core\logs\
```

### 🐛 问题报告

如果遇到问题，请提供：
1. **系统信息**: Windows版本、Python版本
2. **错误信息**: 完整的错误堆栈
3. **操作步骤**: 重现问题的具体步骤
4. **日志文件**: 相关的日志内容

### 📧 联系方式

- **GitHub Issues**: [提交问题](https://github.com/CKEN/VisionAI-ClipsMaster/issues)
- **讨论区**: [参与讨论](https://github.com/CKEN/VisionAI-ClipsMaster/discussions)

---

**🎉 安装完成！现在您可以开始使用VisionAI-ClipsMaster创作精彩的短剧视频了！**
