# 🔧 VisionAI-ClipsMaster 故障排除指南

## 🎯 概述

本文档提供VisionAI-ClipsMaster常见问题的解决方案。如果您遇到问题，请先查看此文档，大多数问题都能快速解决。

## 🚀 启动问题

### 问题1: 程序无法启动

#### 症状
- 双击程序无反应
- 命令行显示"找不到模块"
- 程序启动后立即崩溃

#### 解决方案
```bash
# 1. 检查Python版本
python --version
# 必须是3.11或更高版本

# 2. 检查依赖安装
pip list | findstr PyQt6
pip list | findstr torch

# 3. 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 4. 使用完整路径启动
C:\Users\[用户名]\AppData\Local\Programs\Python\Python313\python.exe simple_ui_fixed.py
```

### 问题2: PyQt6导入错误

#### 症状
```
ImportError: No module named 'PyQt6'
ModuleNotFoundError: No module named 'PyQt6.QtCore'
```

#### 解决方案
```bash
# 方法1: 重新安装PyQt6
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6>=6.4.0

# 方法2: 使用conda安装
conda install pyqt

# 方法3: 检查虚拟环境
# 确保在正确的虚拟环境中安装
venv\Scripts\activate
pip install PyQt6
```

### 问题3: 启动时间过长

#### 症状
- 程序启动超过10秒
- 界面加载缓慢
- 系统响应迟缓

#### 解决方案
```bash
# 1. 检查系统资源
# 任务管理器查看CPU和内存使用

# 2. 关闭不必要的程序
# 释放更多系统资源

# 3. 使用性能模式
# 在设置中选择"性能优先"模式

# 4. 清理临时文件
# 删除缓存和临时文件
```

## 💾 内存问题

### 问题4: 内存不足错误

#### 症状
```
MemoryError: Unable to allocate memory
RuntimeError: CUDA out of memory
程序运行中突然崩溃
```

#### 解决方案
```bash
# 1. 选择更小的量化模型
# 在设置中选择Q2_K模型 (2.8GB) 而不是Q5_K (6.3GB)

# 2. 关闭其他程序
# 释放更多内存给VisionAI-ClipsMaster

# 3. 增加虚拟内存
# 控制面板 → 系统 → 高级系统设置 → 性能设置 → 虚拟内存

# 4. 分批处理
# 将大文件分割成小段处理
```

### 问题5: 内存泄漏

#### 症状
- 程序运行时间越长，内存使用越多
- 系统变得越来越慢
- 最终导致系统卡死

#### 解决方案
```bash
# 1. 定期重启程序
# 每处理几个文件后重启一次

# 2. 检查内存监控
# 在程序中查看实时内存使用

# 3. 更新到最新版本
# 新版本修复了内存泄漏问题

# 4. 使用任务管理器监控
# 观察内存使用趋势
```

## 🤖 AI模型问题

### 问题6: 模型下载失败

#### 症状
```
ConnectionError: Failed to download model
TimeoutError: Request timed out
模型文件损坏或不完整
```

#### 解决方案
```bash
# 1. 检查网络连接
ping huggingface.co

# 2. 使用镜像源 (中国用户)
# 在设置中选择"中国镜像源"

# 3. 手动下载模型
# 从官方网站下载后放入models目录

# 4. 增加超时时间
# 在设置中调整下载超时时间
```

### 问题7: 模型加载失败

#### 症状
```
RuntimeError: Error loading model
FileNotFoundError: Model file not found
模型推理返回空结果
```

#### 解决方案
```bash
# 1. 检查模型文件完整性
# 重新下载损坏的模型文件

# 2. 检查磁盘空间
# 确保有足够空间存储模型

# 3. 验证模型格式
# 确保是GGUF格式的量化模型

# 4. 重置模型设置
# 删除模型配置文件，重新配置
```

### 问题8: AI处理结果质量差

#### 症状
- 重构后的剧情不连贯
- 时间轴对应错误
- 生成的文本有语法错误

#### 解决方案
```bash
# 1. 调整AI参数
# 降低创意程度，提高保真度

# 2. 使用更高质量的模型
# 选择Q5_K而不是Q2_K

# 3. 检查输入质量
# 确保原始字幕格式正确

# 4. 手动后处理
# 对AI结果进行人工调整
```

## 🎬 视频处理问题

### 问题9: FFmpeg未找到

#### 症状
```
FileNotFoundError: FFmpeg not found
视频处理功能不可用
无法导出视频文件
```

#### 解决方案
```bash
# 1. 自动安装FFmpeg
# 程序首次运行时会提示自动安装

# 2. 手动下载安装
# 下载地址: https://ffmpeg.org/download.html
# 解压到: tools/ffmpeg/bin/

# 3. 添加到系统PATH
# 将FFmpeg添加到系统环境变量

# 4. 验证安装
tools\ffmpeg\bin\ffmpeg.exe -version
```

### 问题10: 视频格式不支持

#### 症状
```
ValueError: Unsupported video format
无法读取视频文件
视频预览显示黑屏
```

#### 解决方案
```bash
# 1. 转换视频格式
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4

# 2. 检查编码格式
# 使用MediaInfo查看视频详细信息

# 3. 更新FFmpeg
# 下载最新版本的FFmpeg

# 4. 使用标准格式
# 推荐使用H.264编码的MP4文件
```

### 问题11: 时间轴不同步

#### 症状
- 字幕与视频不对应
- 剪切点位置错误
- 导出的视频时间轴混乱

#### 解决方案
```bash
# 1. 检查原始字幕
# 确保SRT文件时间轴正确

# 2. 重新解析字幕
# 删除缓存，重新导入字幕文件

# 3. 手动调整时间轴
# 使用时间轴编辑器精确调整

# 4. 验证视频帧率
# 确保视频帧率与字幕匹配
```

## 🔗 网络问题

### 问题12: 依赖下载缓慢

#### 症状
- pip安装速度极慢
- 下载经常中断
- 连接超时错误

#### 解决方案
```bash
# 1. 使用国内镜像 (中国用户)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 2. 增加超时时间
pip install -r requirements.txt --timeout 1000

# 3. 使用代理
pip install -r requirements.txt --proxy http://proxy.server:port

# 4. 离线安装
# 下载wheel文件后本地安装
```

### 问题13: SSL证书错误

#### 症状
```
SSLError: Certificate verification failed
CERTIFICATE_VERIFY_FAILED
无法建立安全连接
```

#### 解决方案
```bash
# 1. 更新证书
# 更新系统和Python的SSL证书

# 2. 使用信任的主机
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

# 3. 临时禁用SSL验证 (不推荐)
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

# 4. 配置企业代理
# 如果在企业网络中，配置代理设置
```

## 📁 文件问题

### 问题14: 权限不足

#### 症状
```
PermissionError: Access denied
无法写入文件
无法创建目录
```

#### 解决方案
```bash
# 1. 以管理员身份运行
# 右键程序 → "以管理员身份运行"

# 2. 检查文件权限
# 确保对项目目录有读写权限

# 3. 更改安装位置
# 安装到用户目录而不是系统目录

# 4. 关闭杀毒软件
# 临时关闭可能阻止文件操作的安全软件
```

### 问题15: 文件编码问题

#### 症状
- 中文字符显示乱码
- 字幕文件无法正确解析
- 导出文件编码错误

#### 解决方案
```bash
# 1. 转换文件编码
# 将SRT文件转换为UTF-8编码

# 2. 检查系统区域设置
# 控制面板 → 区域 → 管理 → 更改系统区域设置

# 3. 使用记事本转换
# 记事本打开文件 → 另存为 → 编码选择UTF-8

# 4. 使用专业工具
# 使用Notepad++等工具转换编码
```

## 🔧 性能优化

### 问题16: 程序运行缓慢

#### 症状
- 界面响应迟缓
- AI处理时间过长
- 视频预览卡顿

#### 解决方案
```bash
# 1. 检查系统资源
# 任务管理器查看CPU、内存、磁盘使用

# 2. 关闭后台程序
# 关闭不必要的应用程序

# 3. 调整AI参数
# 降低模型复杂度，选择更快的量化级别

# 4. 使用SSD
# 将项目文件存储在SSD上

# 5. 增加内存
# 如果可能，升级到8GB或更多内存
```

### 问题17: GPU加速不工作

#### 症状
- GPU使用率为0
- 处理速度没有提升
- CUDA相关错误

#### 解决方案
```bash
# 1. 检查GPU支持
python -c "import torch; print(torch.cuda.is_available())"

# 2. 安装CUDA版本的PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 3. 更新显卡驱动
# 下载最新的NVIDIA或AMD驱动

# 4. 检查CUDA版本
nvidia-smi
```

## 📞 获取更多帮助

### 自助诊断工具
```bash
# 运行系统诊断
python VisionAI_ClipsMaster_System_Diagnostic.py

# 生成诊断报告
python VisionAI_ClipsMaster_Comprehensive_Verification_Test.py
```

### 联系支持
- 🐛 **Bug报告**: [GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
- 💬 **社区讨论**: [GitHub Discussions](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions)
- 📧 **邮件支持**: peresbreedanay7156@gmail.com
- 📖 **在线文档**: [完整文档](README.md)

### 问题报告模板
```
**问题描述**: 
简要描述遇到的问题

**系统信息**:
- 操作系统: Windows 10/11
- Python版本: 
- 程序版本: 
- 硬件配置: 

**重现步骤**:
1. 
2. 
3. 

**错误信息**:
```
完整的错误日志
```

**预期行为**: 
描述期望的正常行为

**实际行为**: 
描述实际发生的情况

**已尝试的解决方案**: 
列出已经尝试过的解决方法
```

---

**🔧 大多数问题都可以通过本指南解决。如果问题仍然存在，请不要犹豫联系我们的支持团队！**
