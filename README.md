# 🎬 VisionAI-ClipsMaster

<div align="center">

![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

**AI驱动的短剧视频混剪工具** - 智能分析原始字幕，重构为爆款短剧风格，一键导出剪映项目

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [安装指南](#-安装指南) • [使用文档](#-使用文档) • [更新日志](#-更新日志)

</div>

---

## 📖 项目简介

VisionAI-ClipsMaster 是一款专业的AI短剧混剪工具，能够智能分析原始短剧字幕，理解剧情结构和情感走向，自动重构为更具吸引力的"爆款"风格字幕，并支持一键导出到剪映进行二次编辑。

### 核心能力

- 🧠 **AI剧情分析**: 深度理解剧情结构、角色关系、情感曲线
- ✂️ **智能混剪**: 自动提取关键对话，保持叙事连贯性
- 🎯 **爆款重构**: 将普通字幕转化为更具感染力的表达
- 📱 **剪映导出**: 一键生成剪映草稿，支持二次编辑

---

## ✨ 功能特性

### 🌐 双模式推理 (v1.2.0 新增)

| 模式 | 特点 | 适用场景 |
|------|------|----------|
| **本地模式** | 使用本地GGUF模型，无需网络 | 隐私敏感、离线环境 |
| **云端模式** | 调用云端大模型API | 无GPU设备、追求效果 |

**支持的云端平台:**
- 硅基流动 (SiliconFlow) - Qwen3-235B / DeepSeek-V3.2
- 魔搭社区 (ModelScope) - Qwen3-235B-FP8 / DeepSeek-V3

### 🎬 视频处理

- **多格式支持**: MP4, AVI, MOV, MKV
- **字幕解析**: SRT格式，自动编码检测
- **多集混剪**: 支持多集短剧批量处理
- **时间轴同步**: 精确的字幕时间轴映射

### 🧠 AI分析

- **语言检测**: 自动识别中文/英文
- **情感分析**: 识别情感高潮和转折点
- **叙事结构**: 分析剧情起承转合
- **角色识别**: 提取主要角色和关系

### 📤 导出功能

- **剪映草稿**: 一键导出到剪映
- **SRT字幕**: 标准SRT格式输出
- **项目文件**: JSON格式项目数据

---

## 🚀 快速开始

### 环境要求

- **操作系统**: Windows 10/11
- **Python**: 3.11+
- **内存**: 8GB+ (推荐16GB)
- **存储**: 5GB+ 可用空间

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 4. 启动程序
python simple_ui_fixed.py
```

### 5分钟体验

1. **导入素材**: 拖拽视频和SRT字幕文件
2. **选择模式**: 本地模式或云端模式
3. **生成混剪**: 点击"生成爆款SRT"
4. **导出剪映**: 点击"导出到剪映"

---

## 📦 安装指南

详细安装说明请参考: [安装指南](docs/guides/INSTALLATION.md)

### 本地模式配置

1. 下载AI模型（首次使用）
2. 在"设置 → 模型管理"中下载中文/英文模型
3. 等待模型下载和转换完成

### 云端模式配置

1. 选择"云端模式"
2. 选择平台（硅基流动/魔搭社区）
3. 填写API密钥
4. 点击"测试连接"验证

**获取API密钥:**
- 硅基流动: https://cloud.siliconflow.cn
- 魔搭社区: https://modelscope.cn

---

## 📚 使用文档

| 文档 | 说明 |
|------|------|
| [快速入门](docs/guides/QUICK_START.md) | 5分钟上手指南 |
| [用户指南](docs/guides/USER_GUIDE.md) | 完整功能说明 |
| [API参考](docs/API_REFERENCE.md) | 开发者接口文档 |
| [常见问题](docs/guides/FAQ.md) | FAQ和解决方案 |
| [故障排除](docs/guides/TROUBLESHOOTING.md) | 问题诊断手册 |

### 进阶文档

| 文档 | 说明 |
|------|------|
| [模型训练指南](docs/guides/training/TRAINING_USAGE_GUIDE.md) | 自定义模型训练 |
| [模型工作流程](docs/模型工作流程和删除操作说明.md) | 模型管理详解 |
| [剪映导出指南](docs/JIANYING_EXPORT_GUIDE.md) | 剪映集成说明 |
| [打包部署指南](docs/deployment/PACKAGING_GUIDE.md) | 便携版制作 |

---

## 🏗️ 项目结构

```
VisionAI-ClipsMaster/
├── src/                    # 源代码
│   ├── core/              # 核心引擎
│   │   ├── cloud_ai_engine.py    # 云端AI引擎
│   │   ├── real_ai_engine.py     # 本地AI引擎
│   │   └── ...
│   ├── ui/                # UI组件
│   ├── training/          # 训练模块
│   └── exporters/         # 导出模块
├── configs/               # 配置文件
├── models/                # AI模型
├── tools/                 # 工具（FFmpeg等）
├── docs/                  # 文档
├── simple_ui_fixed.py     # 主程序入口
└── requirements.txt       # 依赖清单
```

---

## 🔄 更新日志

### v1.2.0 (2025-12-22) - 云端AI集成版

**新增功能:**
- 🌐 云端AI推理模式（硅基流动 + 魔搭社区）
- 🤖 支持Qwen3-235B和DeepSeek-V3.2大模型
- 🔄 本地/云端模式无缝切换
- 📦 便携版打包功能

**优化改进:**
- 🧠 叙事连贯性算法优化（10大智能策略）
- 📊 关键对白保留比例默认75%（可配置）
- 🧹 项目体积优化（1GB+ → 216MB）

[查看完整更新日志](docs/release-notes/RELEASE_NOTES_v1.2.0.md)

### v1.1.0 (2025-10-06)

- 智能推荐下载器优化
- CUDA设备检测修复
- 系统稳定性提升

[查看v1.1.0更新日志](docs/release-notes/RELEASE_NOTES_v1.1.0.md)

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [Transformers](https://huggingface.co/transformers/) - AI模型框架
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - GGUF推理引擎
- [FFmpeg](https://ffmpeg.org/) - 视频处理
- [pyCapCut](https://github.com/GuanYixuan/pyCapCut) - 剪映项目导出参考
- [硅基流动](https://siliconflow.cn/) - 云端API服务
- [魔搭社区](https://modelscope.cn/) - 云端API服务

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

Made with ❤️ by CKEN-STAR

</div>
