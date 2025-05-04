# VisionAI-ClipsMaster
<div align="center">

![VisionAI-ClipsMaster Logo](https://img.shields.io/badge/VisionAI-ClipsMaster-brightgreen)

**AI驱动的短剧混剪创作平台 - 利用大模型技术自动生成爆款混剪视频**

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Language](https://img.shields.io/badge/Language-Python-yellow)
![Stars](https://img.shields.io/github/stars/CKEN-STAR/VisionAI-ClipsMaster?style=social)

[简体中文](README.md) | [English](README_EN.md)

</div>

## 📖 项目简介

VisionAI-ClipsMaster是一款革命性的视频处理工具，专为短剧混剪创作者设计。它通过本地部署大型语言模型（Qwen2.5-7B和Mistral-7B），智能分析原片剧情，自动重构字幕，生成更具吸引力的爆款短视频内容。

本工具核心优势在于**完全本地化处理**，无需依赖云服务，即使在配置较低的电脑上也能高效运行，为创作者提供便捷的混剪自动化解决方案。通过先进的剧本重构技术，系统能够识别原片中最具吸引力的情节点，重新编排故事线，创造引人入胜的短视频内容。

<details>
<summary>🎬 点击查看功能演示</summary>

*GIF演示将在未来版本中添加*

</details>

## ✨ 核心功能

- **🤖 剧本智能重构**：基于大模型分析原片字幕，自动重组剧情结构，提炼关键情节
- **🔄 双语模型支持**：集成Qwen2.5-7B(中文)和Mistral-7B(英文)，智能切换处理不同语言内容
- **🪶 轻量级设计**：适用于4GB内存/无独显电脑，通过模型量化和动态加载降低硬件需求
- **📚 模型训练功能**：提供投喂训练界面，使模型学习爆款内容创作模式
- **🎞️ 字幕到视频自动化**：根据生成的爆款字幕自动切割拼接视频片段
- **⚡ 零视频处理**：纯拼接策略，不进行复杂剪辑和转场，专注于内容重组
- **🔄 批量处理**：支持批量分析和生成多个视频文件
- **📤 多格式导出**：支持生成剪映工程文件，方便二次创作

## 🚀 快速开始

### ⚙️ 环境要求

- Python 3.8+
- Windows/macOS/Linux
- 最低4GB内存（推荐8GB以上）
- FFmpeg (用于视频处理)
- CUDA支持（可选，用于GPU加速）

### 📥 安装步骤

1. 克隆仓库到本地：

```bash
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 启动应用：

```bash
python simple_ui.py
```

首次启动时，系统会自动下载并配置必要的模型文件。

### 🎮 基本使用流程

1. **添加视频和字幕**：
   - 点击"添加视频"选择短剧视频文件
   - 点击"添加SRT"选择对应的字幕文件

2. **选择语言模式**：
   - 自动检测（默认）
   - 中文模式（使用Qwen2.5-7B）
   - 英文模式（使用Mistral-7B）

3. **生成爆款字幕**：
   - 选择要处理的SRT文件
   - 点击"生成爆款SRT"按钮
   - 系统会自动分析剧情，重构字幕，生成新的SRT文件

4. **生成视频**：
   - 选择一个视频和对应的爆款SRT
   - 点击"生成视频"按钮
   - 选择保存位置，等待处理完成

## 🔧 技术特点

- **💻 动态模型加载/卸载**：根据语言检测结果自动切换模型，优化内存使用
- **📊 Q4_K_M量化技术**：大幅降低模型内存需求，适配低配置电脑
- **🎭 情感连贯性分析**：在重构过程中保证情节和情感的连贯性
- **👥 角色关系图谱**：建立人物关系网络，确保角色形象一致性
- **⚖️ 长度平衡机制**：避免生成的混剪过短(导致剧情不连贯)或过长(与原片相差不大)
- **🎛️ 自主参数管理**：AI模型根据训练自主决定最佳参数，无需人工调整
- **📈 增强型情感分析**：多维度情感评估，精准捕捉文本情感变化

## 🧠 设计理念

VisionAI-ClipsMaster的核心设计理念是"**理解剧情，提炼精华**"。通过深度分析原始短剧的字幕内容，系统能够：

1. 识别关键情节点和转折点
2. 保留角色关系和情感连贯性
3. 压缩冗余内容，保持故事核心
4. 优化节奏和情感波动，提高观众参与感

最终生成的混剪既保留了原片的精华内容，又具有更强的吸引力和传播性。

## 🔍 高级功能

- **🔁 批量处理**：可以一次性导入多个视频和字幕文件进行批量处理
- **⚙️ 模型参数调整**：在设置中可以微调生成参数，影响创作风格和生成结果
- **📤 多样化导出**：支持导出为MP4视频或剪映工程文件
- **📊 数据可视化**：提供情感曲线和剧情结构可视化功能

## 🎓 模型训练

对模型进行个性化训练以提升生成质量：

1. 切换到"模型训练"标签页
2. 选择训练语言（中文或英文）
3. 导入多个原始SRT作为剧情素材
4. 导入一个爆款SRT作为目标样式
5. 点击"开始训练模型"
6. 完成后，模型将自动应用你的风格生成内容

## 📚 投喂训练原理

本项目使用的投喂训练过程基于以下原理：

1. **输入数据**：
   - 提供短剧原片的多集字幕文件（作为输入）
   - 提供成功爆款混剪的字幕文件（作为目标输出）

2. **学习过程**：
   - 大模型分析原片与爆款之间的转化模式
   - 识别吸引人的剧情结构和关键点选择规律
   - 学习如何提取和重组最具吸引力的内容片段

3. **应用效果**：
   - 训练后的模型能够自动识别原片中的潜在爆点
   - 生成更符合目标爆款风格的字幕重构
   - 保持情感连贯性和角色关系一致性

## 🏗️ 技术架构

VisionAI-ClipsMaster采用模块化设计，主要包括以下组件：

- **🔍 语言检测器**：自动识别内容语言，选择适当的模型
- **🧠 模型管理器**：动态加载/卸载语言模型，优化内存使用
- **📑 剧本分析器**：分析原始字幕，提取关键情节和角色关系
- **✏️ 剧本重构器**：基于分析结果重新组织内容，生成爆款结构
- **⏱️ 字幕时间码优化器**：优化新字幕的时间码，确保视频片段连贯
- **🎞️ 视频拼接器**：根据新字幕时间码切割和拼接原始视频

低配置设备上，系统会自动使用量化模型和渐进式加载策略，确保流畅运行。

## 🔮 未来计划

我们正在开发以下功能，将在未来版本中推出：

- **自动语音识别**：无需手动提供SRT文件
- **多语言支持扩展**：增加更多语言模型
- **云端协作功能**：团队可以共同创作和管理项目
- **更多导出格式**：支持达芬奇、Premiere等主流视频编辑软件
- **风格模板库**：预设多种创作风格模板

## ❓ 常见问题解答

<details>
<summary><b>Q: 能否处理没有字幕的视频？</b></summary>
A: 目前需要提供SRT字幕文件。未来版本可能支持自动语音识别功能。
</details>

<details>
<summary><b>Q: 支持多长的视频处理？</b></summary>
A: 理论上没有长度限制，但建议单个输入视频不超过2小时，以获得最佳效果。
</details>

<details>
<summary><b>Q: 生成的视频质量会下降吗？</b></summary>
A: 不会。系统仅执行简单的切割和拼接，不会重新编码或压缩视频内容。
</details>

<details>
<summary><b>Q: 如何提高生成内容的质量？</b></summary>
A: 提供多样化的训练样本，尤其是成功的爆款样本，可以显著提高生成质量。
</details>

## 📜 许可证

本项目采用MIT许可证 - 详细信息请查看[LICENSE](LICENSE)文件。

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议！请查看[贡献指南](CONTRIBUTING.md)了解详情。

## 📞 联系方式

- GitHub: [https://github.com/CKEN-STAR/VisionAI-ClipsMaster](https://github.com/CKEN-STAR/VisionAI-ClipsMaster)
- 问题反馈: [提交Issue](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)

## 🙏 致谢

感谢以下开源项目的支持：

- [Qwen2.5](https://github.com/QwenLM/Qwen) - 阿里云开源的大型语言模型
- [Mistral](https://github.com/mistralai/mistral-src) - 高性能开源大语言模型
- [FFmpeg](https://ffmpeg.org/) - 视频处理工具
- [PyQt](https://riverbankcomputing.com/software/pyqt/) - GUI开发框架

---

<div align="center">

© 2025 CKEN-STAR 版权所有

最后更新：2024年5月4日

</div> 
重击
python main.py --input video.mp4 --output output.mp4
🎥 示例演示
以下是 VisionAI-ClipsMaster 生成的视频示例：

示例 GIF

📖 文档与指南
用户画像模块
导出模块
🤝 参与贡献
我们欢迎社区开发者通过以下方式贡献代码：

Fork 本仓库
创建分支：git checkout -b feature/your-feature
提交改动：git commit -m "Add some feature"
推送分支：git push origin feature/your-feature
提交 Pull Request
📜 许可证
本项目基于 MIT License 进行开源。

📬 联系方式
维护者： CKEN-STAR
GitHub： CKEN-STAR
根据现有信息，我已整合了用户画像模块的内容，但导出模块的 README 目前为空。如果你希望更具体地完善某些模块，或者包括其他内容（如徽章、贡献者列表等），请告诉我！
