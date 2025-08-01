# 🚀 VisionAI-ClipsMaster 快速开始指南

> **5分钟快速上手** | 从零开始制作爆款短剧混剪

## 📋 准备工作

### 🔧 系统要求
- **操作系统**: Windows 10/11, Linux, macOS
- **Python**: 3.11+ (推荐 3.13)
- **内存**: 4GB+ RAM
- **存储**: 2GB+ 可用空间

### 📁 准备素材
在开始之前，请准备以下材料：
- **短剧原片**: MP4/AVI/MOV格式视频文件
- **字幕文件**: 对应的SRT格式字幕文件

## ⚡ 快速安装

### 方法一：一键安装（推荐）
```bash
# 1. 克隆项目
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 运行一键安装脚本
python install_dependencies.py

# 3. 启动应用
python simple_ui_fixed.py
```

### 方法二：手动安装
```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python simple_ui_fixed.py
```

## 🎬 第一次使用

### 步骤1：启动应用
```bash
python simple_ui_fixed.py
```

启动后您将看到现代化的用户界面，包含以下主要区域：
- **文件上传区**: 拖拽或选择视频和字幕文件
- **AI设置区**: 选择模型和处理参数
- **进度监控区**: 实时查看处理进度
- **结果预览区**: 查看生成的混剪效果

### 步骤2：上传素材
1. **上传视频文件**
   - 点击"选择视频文件"按钮
   - 或直接拖拽视频文件到上传区域
   - 支持格式：MP4, AVI, MOV, FLV

2. **上传字幕文件**
   - 点击"选择字幕文件"按钮
   - 选择对应的SRT字幕文件
   - 系统会自动验证字幕格式

### 步骤3：AI智能分析
1. **语言检测**
   - 系统自动检测字幕语言（中文/英文）
   - 自动切换到对应的AI模型

2. **模型选择**（可选）
   - **中文内容**: 自动使用 Qwen2.5-7B 模型
   - **英文内容**: 自动使用 Mistral-7B 模型
   - **混合内容**: 智能选择主要语言模型

### 步骤4：设置处理参数
1. **混剪风格**
   - **爆款风格**: 适合抖音、快手等短视频平台
   - **剧情风格**: 保持原有剧情完整性
   - **搞笑风格**: 突出幽默和娱乐元素

2. **时长控制**
   - **短视频**: 30-60秒（推荐）
   - **中视频**: 1-3分钟
   - **长视频**: 3-5分钟

3. **质量设置**
   - **快速模式**: 处理速度优先
   - **平衡模式**: 速度与质量平衡（推荐）
   - **高质量模式**: 质量优先

### 步骤5：开始处理
1. 点击"开始AI重构"按钮
2. 系统将显示实时处理进度：
   - ✅ 文件验证完成
   - ✅ 语言检测完成
   - ✅ 模型加载完成
   - ✅ 剧情分析中...
   - ✅ 重构生成中...
   - ✅ 视频拼接中...

### 步骤6：查看结果
处理完成后，您将获得：
- **混剪视频**: 根据AI重构的新剧情生成
- **剪映项目文件**: 可导入剪映进行二次编辑
- **处理报告**: 详细的分析和处理信息

## 🎯 实用技巧

### 💡 提升效果的技巧
1. **选择高质量原片**
   - 画质清晰，音频清楚
   - 剧情完整，逻辑连贯

2. **优化字幕文件**
   - 确保时间轴准确
   - 文本内容完整无误
   - 避免特殊字符和格式错误

3. **合理设置参数**
   - 根据目标平台选择合适的时长
   - 根据内容类型选择合适的风格

### ⚡ 性能优化技巧
1. **内存优化**
   - 关闭不必要的应用程序
   - 选择合适的模型量化级别

2. **处理速度优化**
   - 使用SSD硬盘存储素材
   - 确保网络连接稳定（首次下载模型时）

### 🔧 常见问题快速解决

#### 问题1：模型下载缓慢
**解决方案**：
```bash
# 使用国内镜像加速
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 问题2：内存不足
**解决方案**：
- 选择更轻量的量化模型
- 关闭其他占用内存的应用
- 分段处理长视频

#### 问题3：字幕格式错误
**解决方案**：
- 使用标准SRT格式
- 检查时间码格式：`00:00:01,000 --> 00:00:05,000`
- 确保文件编码为UTF-8

## 📚 进阶使用

### 🎨 自定义风格
1. 修改 `configs/clip_settings.json` 文件
2. 调整情感强度、节奏参数
3. 重启应用使配置生效

### 🔄 批量处理
```bash
# 使用命令行接口批量处理
python src/api/cli_interface.py --input-dir "data/input/" --output-dir "data/output/"
```

### 📊 性能监控
启动性能监控面板：
```bash
python ui/progress_dashboard.py
```

## 🆘 获取帮助

### 📞 支持渠道
- **在线文档**: [完整使用指南](../../USAGE.md)
- **常见问题**: [FAQ文档](../../FAQ.md)
- **GitHub Issues**: [报告问题](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
- **技术讨论**: [GitHub Discussions](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions)

### 🔗 相关文档
- [📥 详细安装指南](../../INSTALLATION.md)
- [📖 完整使用教程](../../USAGE.md)
- [🔧 开发者指南](../../DEVELOPMENT.md)
- [📚 API参考文档](../API_REFERENCE.md)

## 🎉 恭喜！

您已经成功完成了第一个AI短剧混剪项目！

**下一步建议**：
1. 尝试不同的混剪风格和参数
2. 探索剪映项目文件的二次编辑功能
3. 查看完整的使用教程了解更多高级功能

---

**开始您的AI短剧混剪之旅吧！** 🚀✨
