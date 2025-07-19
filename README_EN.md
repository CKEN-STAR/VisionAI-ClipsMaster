# VisionAI-ClipsMaster

<div align="center">

![VisionAI-ClipsMaster Logo](https://img.shields.io/badge/VisionAI-ClipsMaster-brightgreen)

**AI-Powered Short Drama Video Editing Platform - Automatically Generate Viral Video Clips Using Large Language Models**

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Language](https://img.shields.io/badge/Language-Python-yellow)
![Stars](https://img.shields.io/github/stars/CKEN-STAR/VisionAI-ClipsMaster?style=social)

[简体中文](README.md) | [English](README_EN.md)

</div>

## 📖 Project Overview

VisionAI-ClipsMaster is a revolutionary video processing tool designed specifically for short drama video creators. It leverages locally deployed large language models (Qwen2.5-7B and Mistral-7B) to intelligently analyze original drama plots, automatically reconstruct subtitles, and generate more engaging viral short video content.

The core advantage of this tool lies in **complete local processing** - no cloud services required. It can run efficiently even on low-spec computers, providing creators with a convenient automated video editing solution. Through advanced script reconstruction technology, the system can identify the most engaging plot points in original content, reorganize storylines, and create captivating short video content.

<details>
<summary>🎬 Click to View Demo</summary>

*GIF demonstration will be added in future versions*

</details>

## ✨ Core Features

- **🤖 Intelligent Script Reconstruction**: Uses large language models to analyze original subtitles, automatically reorganize plot structure, and extract key scenes
- **🔄 Dual Language Model Support**: Integrates Qwen2.5-7B (Chinese) and Mistral-7B (English), intelligently switching between different language content
- **🪶 Lightweight Design**: Suitable for 4GB RAM/no GPU computers, reduces hardware requirements through model quantization and dynamic loading
- **📚 Model Training Functionality**: Provides training interface for models to learn viral content creation patterns
- **🎞️ Subtitle-to-Video Automation**: Automatically cuts and concatenates video segments based on generated viral subtitles
- **⚡ Zero Video Processing**: Pure concatenation strategy, no complex editing or transitions, focuses on content reorganization
- **🔄 Batch Processing**: Supports batch analysis and generation of multiple video files
- **📤 Multi-format Export**: Supports generating JianYing project files for secondary creation

## 🚀 Quick Start

### ⚙️ System Requirements

- Python 3.8+
- Windows/macOS/Linux
- Minimum 4GB RAM (8GB+ recommended)
- FFmpeg (for video processing)
- CUDA support (optional, for GPU acceleration)

### 📥 Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Launch the application:

```bash
python simple_ui.py
```

On first startup, the system will automatically download and configure necessary model files.

### 🎮 Basic Usage Workflow

1. **Add Video and Subtitles**:
   - Click "Add Video" to select short drama video files
   - Click "Add SRT" to select corresponding subtitle files

2. **Select Language Mode**:
   - Auto-detect (default)
   - Chinese mode (uses Qwen2.5-7B)
   - English mode (uses Mistral-7B)

3. **Generate Viral Subtitles**:
   - Select SRT files to process
   - Click "Generate Viral SRT" button
   - System automatically analyzes plot, reconstructs subtitles, and generates new SRT files

4. **Generate Video**:
   - Select a video and corresponding viral SRT
   - Click "Generate Video" button
   - Choose save location and wait for processing completion

## 🔧 Technical Features

- **💻 Dynamic Model Loading/Unloading**: Automatically switches models based on language detection, optimizing memory usage
- **📊 Q4_K_M Quantization Technology**: Significantly reduces model memory requirements, suitable for low-spec computers
- **🎭 Emotional Coherence Analysis**: Ensures plot and emotional coherence during reconstruction
- **👥 Character Relationship Mapping**: Builds character relationship networks, ensuring character consistency
- **⚖️ Length Balance Mechanism**: Avoids generated clips being too short (causing plot incoherence) or too long (minimal difference from original)
- **🎛️ Autonomous Parameter Management**: AI models autonomously determine optimal parameters based on training, no manual adjustment needed
- **📈 Enhanced Emotional Analysis**: Multi-dimensional emotional assessment, precisely captures text emotional changes

## 🧠 Design Philosophy

The core design philosophy of VisionAI-ClipsMaster is "**Understand the Plot, Extract the Essence**". Through deep analysis of original short drama subtitle content, the system can:

1. Identify key plot points and turning points
2. Preserve character relationships and emotional coherence
3. Compress redundant content while maintaining story core
4. Optimize pacing and emotional fluctuations to increase audience engagement

The final generated clips retain the essence of original content while having stronger appeal and viral potential.

## 🎓 Model Training

Personalize model training to improve generation quality:

1. Switch to "Model Training" tab
2. Select training language (Chinese or English)
3. Import multiple original SRTs as plot materials
4. Import one viral SRT as target style
5. Click "Start Model Training"
6. After completion, the model will automatically apply your style to generate content

## 📚 Training Feed Principle

The training feed process used in this project is based on the following principles:

1. **Input Data**:
   - Provide multi-episode subtitle files from original short dramas (as input)
   - Provide subtitle files from successful viral clips (as target output)

2. **Learning Process**:
   - Large language models analyze transformation patterns between original and viral content
   - Identify engaging plot structures and key point selection patterns
   - Learn how to extract and reorganize the most attractive content segments

3. **Application Effects**:
   - Trained models can automatically identify potential viral points in original content
   - Generate subtitle reconstructions that better match target viral styles
   - Maintain emotional coherence and character relationship consistency

## 🏗️ Technical Architecture

VisionAI-ClipsMaster adopts modular design, including the following main components:

- **🔍 Language Detector**: Automatically identifies content language, selects appropriate models
- **🧠 Model Manager**: Dynamically loads/unloads language models, optimizes memory usage
- **📑 Script Analyzer**: Analyzes original subtitles, extracts key plots and character relationships
- **✏️ Script Reconstructor**: Reorganizes content based on analysis results, generates viral structures
- **⏱️ Subtitle Timecode Optimizer**: Optimizes new subtitle timecodes, ensures video segment coherence
- **🎞️ Video Concatenator**: Cuts and concatenates original videos based on new subtitle timecodes

On low-spec devices, the system automatically uses quantized models and progressive loading strategies to ensure smooth operation.

## 🔮 Future Plans

We are developing the following features for future releases:

- **Automatic Speech Recognition**: No need to manually provide SRT files
- **Extended Multi-language Support**: Add more language models
- **Cloud Collaboration Features**: Teams can collaborate on projects
- **More Export Formats**: Support for DaVinci Resolve, Premiere, and other mainstream video editing software
- **Style Template Library**: Preset multiple creative style templates

## ❓ FAQ

<details>
<summary><b>Q: Can it process videos without subtitles?</b></summary>
A: Currently requires SRT subtitle files. Future versions may support automatic speech recognition.
</details>

<details>
<summary><b>Q: What's the maximum video length supported?</b></summary>
A: Theoretically no length limit, but recommend single input videos under 2 hours for optimal results.
</details>

<details>
<summary><b>Q: Will generated video quality degrade?</b></summary>
A: No. The system only performs simple cutting and concatenation without re-encoding or compressing video content.
</details>

<details>
<summary><b>Q: How to improve generated content quality?</b></summary>
A: Providing diverse training samples, especially successful viral samples, can significantly improve generation quality.
</details>

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Please check the [Contributing Guide](CONTRIBUTING.md) for details.

## 📞 Contact

- GitHub: [https://github.com/CKEN-STAR/VisionAI-ClipsMaster](https://github.com/CKEN-STAR/VisionAI-ClipsMaster)
- Issues: [Submit Issue](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)

## 🙏 Acknowledgments

Thanks to the following open source projects:

- [Qwen2.5](https://github.com/QwenLM/Qwen) - Alibaba Cloud's open source large language model
- [Mistral](https://github.com/mistralai/mistral-src) - High-performance open source large language model
- [FFmpeg](https://ffmpeg.org/) - Video processing tools
- [PyQt](https://riverbankcomputing.com/software/pyqt/) - GUI development framework

---

<div align="center">

© 2025 CKEN-STAR All Rights Reserved

Last Updated: January 19, 2025

</div>
