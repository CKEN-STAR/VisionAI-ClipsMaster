# VisionAI-ClipsMaster 快速入门指南 ⚡

> 5分钟上手指南 - 从安装到生成第一个爆款混剪视频

## 🎯 快速概览

VisionAI-ClipsMaster 让您通过AI技术将完整短剧转化为吸引眼球的混剪视频。整个流程只需4个简单步骤：

```
安装程序 → 导入素材 → AI处理 → 导出视频
```

## ⚡ 5分钟快速开始

### 第1步：环境准备（1分钟）

**系统要求检查：**
- ✅ 内存：4GB以上
- ✅ 存储：10GB可用空间
- ✅ Python：3.8+版本

**快速安装：**
```bash
# 1. 克隆项目
git clone https://github.com/your-repo/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动程序
python simple_ui_fixed.py
```

### 第2步：导入素材（1分钟）

**准备素材：**
- 📹 **短剧原片：** MP4/AVI/MOV格式视频文件
- 📝 **字幕文件：** 对应的SRT字幕文件

**导入操作：**
1. 启动程序后，点击"导入视频"按钮
2. 选择您的短剧原片文件
3. 上传对应的SRT字幕文件
4. 程序自动检测语言（中文/英文）

### 第3步：AI智能处理（2分钟）

**自动处理流程：**
1. **语言检测：** 系统自动识别字幕语言
   - 中文内容 → 加载Qwen2.5-7B模型
   - 英文内容 → 加载Mistral-7B模型

2. **剧本分析：** AI深度理解剧情结构
   - 分析角色关系和情节发展
   - 识别关键情节点和高潮部分
   - 评估情感曲线和节奏变化

3. **智能重构：** 生成爆款风格字幕
   - 提取最精彩的片段
   - 重新组织叙事结构
   - 优化节奏和情感张力

**处理状态监控：**
```
[████████████████████████████████] 100%
✅ 模型加载完成
✅ 剧情分析完成  
✅ 字幕重构完成
```

### 第4步：导出成品（1分钟）

**导出选项：**
1. **混剪视频：** 直接生成最终视频文件
2. **剪映工程：** 生成可二次编辑的工程文件

**导出操作：**
1. 点击"生成视频"按钮
2. 选择输出格式和质量
3. 设置保存路径
4. 等待自动拼接完成

**输出文件：**
```
output/
├── final_video.mp4          # 混剪视频
├── generated_subtitles.srt  # 新字幕文件
└── jianying_project.json    # 剪映工程文件
```

## 🎬 示例操作演示

### 典型使用场景

**场景：** 将一部20集的古装短剧混剪成3分钟爆款视频

```bash
# 1. 启动程序
python simple_ui_fixed.py

# 2. 在界面中操作：
导入视频: "古装剧_完整版.mp4" (2.5GB, 400分钟)
上传字幕: "古装剧_完整版.srt" (包含所有对话)

# 3. AI处理结果：
检测语言: 中文 → 加载Qwen2.5-7B模型
剧情分析: 识别出15个关键情节点
智能重构: 生成180秒精华字幕

# 4. 输出结果：
混剪视频: "古装剧_爆款混剪.mp4" (85MB, 3分钟)
剪映工程: 可进一步添加BGM和特效
```

## 🚀 进阶功能快速体验

### 投喂训练功能

**目的：** 让AI学习网络爆款的剪辑规律

**快速操作：**
1. 切换到"训练"标签页
2. 上传训练数据对：
   - 原片字幕：完整短剧的SRT文件
   - 爆款字幕：对应混剪视频的SRT文件
3. 点击"开始训练"
4. 监控训练进度和效果

### 批量处理功能

**适用场景：** 处理多个短剧文件

```bash
# 命令行批量处理
python src/api/cli_interface.py \
  --input_dir "data/input/videos/" \
  --output_dir "data/output/" \
  --batch_size 5
```

## 🔧 常见问题快速解决

### Q1: 程序启动失败
```bash
# 检查Python版本
python --version  # 需要3.8+

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### Q2: 内存不足
```yaml
# 编辑 configs/model_config.yaml
quantization: "Q2_K"  # 更激进的量化
max_memory: "3GB"     # 限制内存使用
```

### Q3: 视频格式不支持
```bash
# 使用FFmpeg转换格式
ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
```

### Q4: 字幕时间轴不准确
- 检查SRT文件格式是否正确
- 确认字幕与视频时间轴对应
- 使用字幕编辑工具预先校正

## 📈 性能优化建议

### 硬件配置建议
- **最低配置：** 4GB内存 + CPU模式
- **推荐配置：** 8GB内存 + 集成显卡
- **最佳配置：** 16GB内存 + 独立显卡

### 处理速度优化
```python
# 在 configs/model_config.yaml 中调整
batch_size: 4        # 根据内存调整
num_threads: 4       # CPU线程数
use_gpu: false       # 低配设备建议关闭
```

## 🎉 完成！

恭喜！您已经掌握了VisionAI-ClipsMaster的基本使用方法。

**下一步建议：**
- 📖 阅读 [USER_GUIDE.md](USER_GUIDE.md) 了解详细功能
- 🔧 查看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md) 解决问题
- 💡 尝试投喂训练功能提升AI效果

**开始创造您的第一个爆款短视频吧！** 🚀
