# 🔧 VisionAI-ClipsMaster 故障排除手册

> **快速解决常见问题** - 系统化的故障诊断和解决方案

## 📋 目录

- [🚀 启动问题](#-启动问题)
- [🧠 AI模型问题](#-ai模型问题)
- [🎬 视频处理问题](#-视频处理问题)
- [📤 导出问题](#-导出问题)
- [⚡ 性能问题](#-性能问题)
- [🔧 系统问题](#-系统问题)

---

## 🚀 启动问题

### 问题1：程序无法启动

**症状**：
- 双击程序无响应
- 命令行启动报错
- 窗口闪退

**诊断步骤**：
```bash
# 1. 检查Python版本
python --version  # 应该是3.11+

# 2. 检查依赖
pip check

# 3. 查看错误日志
type logs\visionai.log
```

**解决方案**：
1. **Python版本过低**：
   ```bash
   # 升级Python到3.11+
   # 从python.org下载最新版本
   ```

2. **依赖缺失**：
   ```bash
   pip install -r requirements.txt
   ```

3. **配置文件损坏**：
   ```bash
   # 删除配置文件，重新生成
   del configs\active_model.yaml
   python simple_ui_fixed.py
   ```

---

### 问题2：启动时间过长

**症状**：
- 启动超过30秒
- 加载进度条卡住

**诊断步骤**：
```bash
# 运行性能诊断
python scripts\run_startup_benchmark.py
```

**解决方案**：
1. **模型文件过大**：
   - 使用更小的量化版本（INT4而非INT8）
   - 删除不需要的模型文件

2. **系统资源不足**：
   - 关闭其他程序
   - 增加虚拟内存
   - 升级硬件

---

## 🧠 AI模型问题

### 问题3：模型下载失败

**症状**：
- 下载中断
- 网络超时
- 文件损坏

**诊断步骤**：
```bash
# 检查网络连接
ping huggingface.co
ping modelscope.cn
```

**解决方案**：
1. **使用镜像源**：
   - 在设置中配置ModelScope镜像
   - 使用HuggingFace Mirror

2. **手动下载**：
   ```bash
   # 使用智能推荐下载器
   python scripts\setup_models_integrated.py
   ```

3. **断点续传**：
   - 程序会自动从断点继续下载

---

### 问题4：模型加载失败

**症状**：
- 提示"模型文件不存在"
- 加载时崩溃
- 内存不足错误

**诊断步骤**：
```bash
# 检查模型文件
dir models\qwen\qwen2.5-1.5b\base
dir models\mistral\base
```

**解决方案**：
1. **模型文件缺失**：
   ```bash
   # 重新下载模型
   python scripts\setup_models_integrated.py
   ```

2. **内存不足**：
   - 使用更小的模型（0.5B而非1.5B）
   - 使用更高的量化级别（INT4）
   - 关闭其他程序

3. **文件损坏**：
   ```bash
   # 删除损坏的模型，重新下载
   rmdir /S models\qwen\qwen2.5-1.5b
   python scripts\setup_models_integrated.py
   ```

---

## 🎬 视频处理问题

### 问题5：视频无法导入

**症状**：
- 提示"不支持的格式"
- 视频预览失败
- 时间轴错误

**诊断步骤**：
```bash
# 检查FFmpeg
ffmpeg -version

# 检查视频信息
ffprobe video.mp4
```

**解决方案**：
1. **FFmpeg未安装**：
   ```bash
   # 自动安装
   python tools\ffmpeg_installer.py
   ```

2. **视频格式不支持**：
   - 转换为MP4 (H.264)：
   ```bash
   ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
   ```

3. **视频损坏**：
   - 使用视频修复工具
   - 重新导出视频

---

### 问题6：字幕解析失败

**症状**：
- 提示"字幕格式错误"
- 时间轴不匹配
- 乱码

**诊断步骤**：
```bash
# 检查字幕编码
file -i subtitles.srt
```

**解决方案**：
1. **编码问题**：
   - 转换为UTF-8编码
   - 使用Notepad++或VS Code转换

2. **格式错误**：
   - 检查SRT格式是否正确
   - 使用字幕编辑器修复

3. **时间轴错误**：
   - 重新导出字幕
   - 手动调整时间轴

---

## 📤 导出问题

### 问题7：剪映导出失败

**症状**：
- 提示"导出失败"
- 剪映无法识别
- 文件损坏

**诊断步骤**：
```bash
# 检查导出目录
dir data\output

# 查看错误日志
type logs\export_errors.log
```

**解决方案**：
1. **权限问题**：
   - 以管理员身份运行
   - 检查文件夹权限

2. **路径问题**：
   - 使用英文路径
   - 避免特殊字符

3. **剪映版本不兼容**：
   - 更新剪映到最新版本
   - 使用兼容模式导出

---

## ⚡ 性能问题

### 问题8：处理速度慢

**症状**：
- 处理时间过长
- CPU/GPU使用率低
- 内存占用高

**诊断步骤**：
```bash
# 运行性能测试
python scripts\run_performance_test.py
```

**解决方案**：
1. **启用硬件加速**：
   - 在设置中启用GPU加速
   - 确保CUDA已安装

2. **优化模型**：
   - 使用更小的模型
   - 使用更高的量化级别

3. **调整批处理大小**：
   - 在设置中调整batch_size
   - 根据内存大小调整

---

### 问题9：内存不足

**症状**：
- 提示"内存不足"
- 程序崩溃
- 系统卡顿

**诊断步骤**：
```bash
# 检查内存使用
python -c "import psutil; print(f'可用内存: {psutil.virtual_memory().available / 1024**3:.2f}GB')"
```

**解决方案**：
1. **启用内存优化**：
   - 在设置中启用自动内存清理
   - 设置更低的内存阈值

2. **使用更小的模型**：
   - 选择0.5B而非1.5B
   - 使用INT4量化

3. **增加虚拟内存**：
   - Windows: 系统设置 → 高级系统设置 → 性能 → 虚拟内存

---

## 🔧 系统问题

### 问题10：依赖冲突

**症状**：
- pip check报错
- 导入模块失败
- 版本不兼容

**诊断步骤**：
```bash
# 检查依赖
pip check

# 查看已安装包
pip list
```

**解决方案**：
1. **重新安装依赖**：
   ```bash
   pip uninstall -y -r requirements.txt
   pip install -r requirements.txt
   ```

2. **使用虚拟环境**：
   ```bash
   python -m venv fresh_env
   fresh_env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **固定版本**：
   - 使用requirements.txt中指定的版本
   - 不要随意升级依赖

---

## 📞 获取帮助

如果以上方法都无法解决问题，请：

1. **查看FAQ**：[docs/guides/FAQ.md](FAQ.md)
2. **查看日志**：`logs/visionai.log`
3. **提交Issue**：[GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
4. **联系支持**：提供详细的错误信息和日志

---

**最后更新**：2025-10-11  
**版本**：v1.1.0

