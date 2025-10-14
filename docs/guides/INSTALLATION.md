# 📥 VisionAI-ClipsMaster 安装指南

## 🎯 概述

本指南将帮助您在Windows系统上成功安装和配置VisionAI-ClipsMaster。我们提供了多种安装方式，从简单的一键安装到高级的开发环境配置。

## 📋 系统要求

### 最低要求
- **操作系统**: Windows 10 (版本1903或更高)
- **Python**: 3.11.0 或更高版本
- **内存**: 4GB RAM
- **存储**: 2GB 可用磁盘空间
- **网络**: 用于下载依赖和AI模型

### 推荐配置
- **操作系统**: Windows 11
- **Python**: 3.13.x (最新稳定版)
- **内存**: 8GB RAM 或更多
- **存储**: 5GB 可用磁盘空间
- **显卡**: NVIDIA/AMD GPU (可选，用于加速)

## 🚀 快速安装

### 方法1: 一键安装 (推荐新手)

```bash
# 1. 克隆仓库
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 安装依赖 (使用清华镜像，中国用户推荐)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 3. 启动应用
python simple_ui_fixed.py
```

### 方法2: 虚拟环境安装 (推荐开发者)

```bash
# 1. 克隆仓库
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 创建虚拟环境
python -m venv visionai_env

# 3. 激活虚拟环境
visionai_env\Scripts\activate

# 4. 升级pip
python -m pip install --upgrade pip

# 5. 安装依赖
pip install -r requirements.txt

# 6. 启动应用
python simple_ui_fixed.py
```

## 🔧 详细安装步骤

### 步骤1: 安装Python

#### 下载Python
1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载Python 3.11或更高版本
3. **重要**: 安装时勾选"Add Python to PATH"

#### 验证安装
```bash
python --version
# 应该显示: Python 3.11.x 或更高版本

pip --version
# 应该显示pip版本信息
```

### 步骤2: 克隆项目

#### 使用Git (推荐)
```bash
# 确保已安装Git
git --version

# 克隆项目
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster
```

#### 直接下载
1. 访问 [项目页面](https://github.com/CKEN-STAR/VisionAI-ClipsMaster)
2. 点击"Code" → "Download ZIP"
3. 解压到目标目录

### 步骤3: 安装依赖

#### 标准安装
```bash
pip install -r requirements.txt
```

#### 中国大陆用户 (使用镜像)
```bash
# 清华大学镜像 (推荐)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 阿里云镜像 (备选)
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 豆瓣镜像 (备选)
pip install -r requirements.txt -i https://pypi.douban.com/simple/
```

#### 依赖说明
```
核心依赖:
- PyQt6>=6.4.0          # GUI框架
- psutil>=5.9.0         # 系统监控
- torch>=2.0.0          # AI模型推理
- transformers>=4.20.0  # Hugging Face模型库

可选依赖:
- GPUtil>=1.4.0         # GPU监控
- matplotlib>=3.6.0     # 图表绘制
- opencv-python>=4.6.0  # 视频处理
- ffmpeg-python>=0.2.0  # 视频编码
```

### 步骤4: 配置FFmpeg (可选但推荐)

#### 自动配置
程序首次运行时会自动检测并提示下载FFmpeg。

#### 手动配置
```bash
# 1. 下载FFmpeg
# 访问: https://ffmpeg.org/download.html#build-windows
# 下载Windows版本

# 2. 解压到项目目录
# 解压到: VisionAI-ClipsMaster/tools/ffmpeg/

# 3. 验证安装
tools\ffmpeg\bin\ffmpeg.exe -version
```

## 🧪 验证安装

### 运行测试
```bash
# 启动主程序
python simple_ui_fixed.py

# 运行完整测试 (可选)
python VisionAI_ClipsMaster_Comprehensive_Verification_Test.py
```

### 预期结果
- ✅ 程序在5秒内启动
- ✅ UI界面正常显示
- ✅ 内存使用约415MB
- ✅ 所有功能模块正常加载

## 🔧 高级配置

### 使用系统Python解释器
```bash
# 查找Python安装路径
where python

# 使用完整路径启动 (更稳定)
C:\Users\[用户名]\AppData\Local\Programs\Python\Python313\python.exe simple_ui_fixed.py
```

### GPU加速配置
```bash
# 检查CUDA支持
python -c "import torch; print(torch.cuda.is_available())"

# 安装CUDA版本的PyTorch (如果有NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 开发环境配置
```bash
# 安装开发依赖
pip install pytest>=7.0.0 pytest-qt>=4.2.0

# 运行测试
python -m pytest tests/ -v

# 代码格式化
pip install black flake8
black src/
flake8 src/
```

## 🚨 常见问题

### Python相关
```bash
# 问题: 'python' 不是内部或外部命令
# 解决: 重新安装Python并勾选"Add to PATH"

# 问题: pip安装失败
# 解决: 升级pip
python -m pip install --upgrade pip
```

### 依赖相关
```bash
# 问题: PyQt6安装失败
# 解决: 使用conda安装
conda install pyqt

# 问题: torch安装慢
# 解决: 使用清华镜像
pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 网络相关
```bash
# 问题: 下载超时
# 解决: 增加超时时间
pip install -r requirements.txt --timeout 1000

# 问题: SSL证书错误
# 解决: 使用信任的主机
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

## 📞 获取帮助

如果遇到安装问题，请：

1. **检查系统要求**: 确保满足最低配置要求
2. **查看错误日志**: 记录完整的错误信息
3. **搜索已知问题**: 查看[GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
4. **提交新问题**: 如果问题未解决，请创建新的Issue

### 问题报告模板
```
**系统信息**:
- 操作系统: Windows 10/11
- Python版本: 
- 错误信息: 

**重现步骤**:
1. 
2. 
3. 

**预期行为**:

**实际行为**:
```

---

**🎉 安装完成后，您就可以开始使用VisionAI-ClipsMaster创作精彩的短剧视频了！**
