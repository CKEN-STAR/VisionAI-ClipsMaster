# VisionAI-ClipsMaster 用户手册

## 目录
1. [简介](#简介)
2. [安装与环境要求](#安装与环境要求)
3. [快速上手](#快速上手)
4. [功能详解](#功能详解)
5. [配置说明](#配置说明)
6. [模型管理与多语言支持](#模型管理与多语言支持)
7. [设备兼容性与性能建议](#设备兼容性与性能建议)
8. [常见问题与故障排查](#常见问题与故障排查)
9. [测试与报告](#测试与报告)
10. [联系方式与贡献指南](#联系方式与贡献指南)

---

## 简介
VisionAI-ClipsMaster 是一款基于大模型的智能短视频编辑工具，专为短剧混剪设计。通过分析原始短剧字幕，重构剧情脉络，生成更具吸引力的"爆款风格"字幕，并按照新字幕自动拼接原片，实现高效率的短视频创作。

**核心优势**:
- **智能剧本重构**: 通过大模型理解原剧情，重构叙事结构
- **低配置硬件支持**: 无需GPU，4GB内存即可流畅运行
- **中英双语支持**: 支持中文(Qwen2.5-7B)和英文(Mistral-7B)模型
- **投喂训练**: 支持用户提供爆款视频案例进行模型优化

## 安装与环境要求

### 系统需求
- **最低配置**: 4GB 内存，无需 GPU
- **推荐配置**: 8GB 内存，SSD存储
- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)

### 安装步骤
1. **下载并解压程序包**
2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```
3. **初始化环境**:
   ```bash
   python setup.py
   ```

## 快速上手

### 基础使用流程
1. **准备素材**:
   - 将短剧视频文件(.mp4/.avi/.mov)放入 `data/input/videos/` 目录
   - 将对应字幕文件(.srt)放入 `data/input/subtitles/` 目录

2. **启动程序**:

   **图形界面模式（推荐）**:
   ```bash
   python ui/simple_ui.py
   ```

   **命令行模式**:
   ```bash
   python main.py --input <视频目录> --output <输出目录>
   ```

3. **查看结果**:
   - 生成的混剪视频保存在 `data/output/final_videos/` 目录
   - 生成的编辑项目保存在 `data/output/edit_projects/` 目录

### 命令行参数
```bash
python main.py [选项]

选项:
  --input PATH        输入视频或目录路径
  --output PATH       输出目录路径 (默认: data/output)
  --lang {zh,en}      处理语言 (默认: zh)
  --mode {single,batch} 处理模式 (默认: single)
  --export {video,project,both} 导出类型 (默认: both)
  --memory-limit SIZE 内存限制 (MB, 默认: auto)
```

## 功能详解

### 图形界面使用指南

#### 主界面布局
VisionAI-ClipsMaster提供了直观的图形界面，包含以下主要标签页：

1. **视频处理标签页**：
   - 视频文件导入和预览
   - 字幕文件上传和编辑
   - 剪辑参数设置
   - 处理进度监控

2. **模型训练标签页**：
   - 训练数据投喂
   - 模型训练进度监控
   - 训练参数调整
   - 模型性能评估

3. **设置标签页**：
   - 系统配置选项
   - 主题切换（明暗模式）
   - 性能优化设置
   - 语言和区域设置

4. **关于我们标签页**：
   - 项目信息和版本
   - 使用帮助和教程
   - 技术支持联系方式

#### 界面操作流程

**基础剪辑流程**：
1. 在"视频处理"标签页点击"导入视频"按钮
2. 选择要处理的视频文件（支持MP4、AVI、MOV等格式）
3. 上传对应的SRT字幕文件
4. 在剧本编辑区域查看AI分析的剧情结构
5. 调整剪辑参数（如节奏、重点片段等）
6. 点击"开始处理"按钮启动剪辑
7. 在进度条中监控处理状态
8. 处理完成后点击"导出"保存结果

**主题切换**：
- 在设置标签页中选择"明亮"或"暗黑"主题
- 支持跟随系统主题自动切换
- 主题设置会自动保存，下次启动时生效

**性能监控**：
- 实时显示CPU和内存使用情况
- 监控AI模型加载状态
- 显示处理速度和预计完成时间

### 短剧剪辑功能
- **字幕解析与剧情理解**: 自动解析SRT字幕，理解剧情脉络
- **剧本重构**: 智能重组叙事结构，生成更吸引人的剪辑方案
- **精准时间码匹配**: 自动将新生成的字幕与原视频精确对齐
- **智能节奏调整**: 根据内容重要性动态调整剪辑节奏

### 批量处理
- **多文件批处理**: 一次处理多个视频文件
- **任务调度**: 智能调度任务，优化资源使用
- **断点续传**: 支持中断后继续处理

### 导出选项
- **视频文件**: 直接导出可分享的视频文件
- **项目文件**: 导出剪映/达芬奇等编辑软件兼容的项目文件
- **字幕文件**: 单独导出生成的新字幕文件

### 投喂训练
1. 将原片字幕放入 `data/training/<语言>/raw_pairs/` 目录
2. 将爆款视频字幕放入 `data/training/<语言>/hit_subtitles/` 目录
3. 执行训练:
   ```bash
   python train.py --lang zh --epochs 3
   ```

## 配置说明

### 主配置文件
路径: `configs/model_config.yaml`

主要配置项:
```yaml
models:
  zh:
    path: "models/qwen/quantized/qwen2.5-7b-zh.gguf"
    quantization: "Q4_K_M"
  en: 
    path: "models/mistral/quantized/mistral-7b-en.gguf"
    quantization: "Q4_K_M"

clip_settings:
  min_segment_duration: 1.0  # 最小片段时长(秒)
  max_segment_duration: 15.0 # 最大片段时长(秒)
  narrative_threshold: 0.6   # 叙事紧凑度阈值
  emotion_weight: 0.4        # 情感因素权重
  
memory:
  max_usage_mb: 3800         # 最大内存使用(MB)
  auto_release: true         # 自动释放未使用的模型
```

### 附加配置文件
- `configs/export_policy.yaml`: 导出设置
- `configs/training_policy.yaml`: 训练参数
- `configs/ui_settings.yaml`: 界面设置

### UI界面配置
路径: `configs/ui_settings.yaml`

主要配置项:
```yaml
# 窗口设置
window:
  title: "VisionAI-ClipsMaster - 智能短剧混剪工具"
  width: 1400
  height: 900
  min_width: 1000
  min_height: 700
  center_on_startup: true
  remember_position: true

# 主题设置
theme:
  current: "light"  # light, dark, auto
  auto_switch: false
  follow_system: false

  light:
    primary_color: "#2196F3"
    background_color: "#FFFFFF"
    text_color: "#333333"

  dark:
    primary_color: "#1976D2"
    background_color: "#121212"
    text_color: "#FFFFFF"

# 字体设置
fonts:
  family: "Microsoft YaHei UI"
  size: 9
  bold_titles: true
  scale_factor: 1.0

# 性能设置
performance:
  enable_animations: true
  update_interval: 100  # 界面更新间隔(毫秒)
  max_log_entries: 1000 # 最大日志显示条数
  auto_save_interval: 300 # 自动保存间隔(秒)
```

**配置说明**：
- **窗口设置**：控制主窗口的大小、位置和行为
- **主题设置**：定义界面的颜色方案和外观
- **字体设置**：配置界面文字的显示效果
- **性能设置**：调整界面响应性和资源使用

## 模型管理与多语言支持

### 中文模型 (默认)
- 模型: Qwen2.5-7B
- 状态: 默认已集成，无需额外操作
- 路径: `models/qwen/quantized/qwen2.5-7b-zh.gguf`

### 英文模型 (可选)
- 模型: Mistral-7B
- 状态: 仅保留配置，首次未下载
- 路径: `models/mistral/quantized/mistral-7b-en.gguf`
- 激活方法: 将模型文件下载到指定路径后自动识别，无需修改配置

### 语言切换
- 命令行: 使用 `--lang zh` 或 `--lang en` 参数
- 配置文件: 修改 `configs/models/active_model.yaml` 中的 `language` 值

## 设备兼容性与性能建议

### 资源优化策略
- **内存动态管理**: 自动调整模型加载方式以适应可用内存
- **分片处理**: 大文件自动分段处理，减少内存峰值
- **量化等级自适应**: 根据设备性能自动选择最佳量化等级

### 性能最佳实践
- **限制批量处理数量**: 一次处理不超过10个视频
- **预处理视频**: 使用较低分辨率(720p)视频以加快处理速度
- **定期清理缓存**: 删除 `logs/` 和 `data/output/temp/` 中的临时文件

## 常见问题与故障排查

### 常见错误
| 错误信息 | 可能原因 | 解决方法 |
|---------|---------|---------|
| "模型加载失败" | 内存不足或模型文件损坏 | 关闭其他程序或检查模型文件完整性 |
| "字幕解析错误" | SRT文件格式不正确 | 检查字幕文件编码(UTF-8)和格式 |
| "无法生成输出" | 输出路径权限问题 | 检查目录权限或选择其他输出目录 |
| "英文处理失败" | 英文模型未下载 | 下载英文模型到配置指定路径 |

### 日志分析
- 日志位置: `logs/` 目录
- 错误代码查询: 参考 `docs/ERROR_CODES.md`

### 内存问题
- **症状**: 程序崩溃或运行缓慢
- **解决方案**:
  - 使用 `--memory-limit` 参数限制内存使用
  - 关闭其他内存密集型应用
  - 尝试更激进的量化(修改配置文件中的 `quantization` 为 `Q2_K`)

## 测试与报告

### 测试与监控
- **单元测试**: 覆盖核心功能和边界情况
- **压力测试**: 测试在极限条件下的稳定性
- **用户旅程测试**: 模拟真实使用场景

### 报告生成
- 运行 `python tests/generate_report.py` 生成测试报告
- 报告保存在 `reports/` 目录，支持 HTML、JSON 等格式

## 联系方式与贡献指南

### 获取帮助
- 官方文档: `docs/` 目录下的各类文档
- 问题反馈: 请提交详细错误信息和日志

### 参与贡献
- 贡献规范: 参见 `CONTRIBUTING.md`
- 代码风格: 遵循项目现有代码风格
- 提交PR: 确保通过所有测试并附上详细说明 