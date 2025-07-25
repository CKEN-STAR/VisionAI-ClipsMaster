# 📖 VisionAI-ClipsMaster User Guide

> **Complete User Manual** | From Beginner to Expert

## 📋 Table of Contents

- [🚀 Getting Started](#-getting-started)
- [💻 System Requirements](#-system-requirements)
- [📥 Installation](#-installation)
- [🎬 Basic Usage](#-basic-usage)
- [🧠 AI Features](#-ai-features)
- [📤 Export Options](#-export-options)
- [⚙️ Advanced Settings](#-advanced-settings)
- [🔧 Troubleshooting](#-troubleshooting)
- [📞 Support](#-support)

## 🚀 Getting Started

VisionAI-ClipsMaster is an AI-powered video editing tool that automatically creates viral-style short drama clips from original footage using advanced language models.

### Key Features
- **Dual AI Models**: Mistral-7B (English) + Qwen2.5-7B (Chinese)
- **Intelligent Script Reconstruction**: AI analyzes and restructures narratives
- **Low-Resource Optimization**: Runs on 4GB RAM systems
- **Professional Export**: Generate JianYing project files
- **Zero Video Processing**: Pure concatenation, no quality loss

## 💻 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.11+ (3.13 recommended)
- **RAM**: 4GB+ (8GB+ recommended)
- **Storage**: 2GB+ available space
- **GPU**: Optional (CPU inference supported)

### Recommended Configuration
- **RAM**: 8GB+ for optimal performance
- **GPU**: NVIDIA/AMD GPU for acceleration
- **Storage**: SSD for faster processing
- **Network**: Stable connection for model downloads

## 📥 Installation

### Quick Installation
```bash
# Clone the repository
git clone https://github.com/CKEN-STAR/VisionAI-ClipsMaster.git
cd VisionAI-ClipsMaster

# Install dependencies
pip install -r requirements.txt

# Launch application
python simple_ui_fixed.py
```

### Detailed Installation
For detailed installation instructions, see [INSTALLATION.md](../../INSTALLATION.md).

## 🎬 Basic Usage

### Step 1: Launch Application
```bash
python simple_ui_fixed.py
```

The modern interface includes:
- **File Upload Area**: Drag & drop or select video/subtitle files
- **AI Settings Panel**: Model selection and processing parameters
- **Progress Monitor**: Real-time processing status
- **Results Preview**: Generated clip preview

### Step 2: Upload Materials
1. **Upload Video File**
   - Click "Select Video File" button
   - Or drag video file to upload area
   - Supported formats: MP4, AVI, MOV, FLV

2. **Upload Subtitle File**
   - Click "Select Subtitle File" button
   - Select corresponding SRT subtitle file
   - System automatically validates subtitle format

### Step 3: AI Processing
1. **Language Detection**
   - System automatically detects subtitle language
   - Switches to appropriate AI model

2. **Model Selection** (Optional)
   - **Chinese Content**: Qwen2.5-7B model
   - **English Content**: Mistral-7B model
   - **Mixed Content**: Intelligent primary language selection

### Step 4: Configure Parameters
1. **Editing Style**
   - **Viral Style**: Optimized for TikTok, YouTube Shorts
   - **Dramatic Style**: Maintains narrative integrity
   - **Comedy Style**: Emphasizes humor and entertainment

2. **Duration Control**
   - **Short Video**: 30-60 seconds (recommended)
   - **Medium Video**: 1-3 minutes
   - **Long Video**: 3-5 minutes

3. **Quality Settings**
   - **Fast Mode**: Speed priority
   - **Balanced Mode**: Speed-quality balance (recommended)
   - **High Quality Mode**: Quality priority

### Step 5: Start Processing
1. Click "Start AI Reconstruction" button
2. Monitor real-time progress:
   - ✅ File validation complete
   - ✅ Language detection complete
   - ✅ Model loading complete
   - ✅ Narrative analysis in progress...
   - ✅ Reconstruction generation...
   - ✅ Video concatenation...

### Step 6: Review Results
Upon completion, you'll receive:
- **Mixed Video**: Generated based on AI-reconstructed narrative
- **JianYing Project File**: Import into JianYing for further editing
- **Processing Report**: Detailed analysis and processing information

## 🧠 AI Features

### Intelligent Script Analysis
- **Narrative Structure**: Identifies plot points, character arcs
- **Emotion Curve**: Analyzes emotional intensity throughout
- **Pacing Analysis**: Optimizes rhythm and timing
- **Key Scene Detection**: Identifies crucial story moments

### Viral Content Generation
- **Hook Creation**: Generates compelling openings
- **Tension Building**: Maintains audience engagement
- **Climax Optimization**: Enhances dramatic peaks
- **Resolution Crafting**: Creates satisfying conclusions

### Language-Specific Processing
- **Chinese Processing**: Cultural context awareness, idiom handling
- **English Processing**: Natural language flow, cultural references
- **Mixed Language**: Intelligent primary language detection

## 📤 Export Options

### Video Export
- **Format**: MP4 (H.264 encoding)
- **Quality**: Original quality preservation
- **Audio**: Original audio track maintained
- **Subtitles**: Optional embedded subtitles

### Project Export
- **JianYing Pro**: Native project file format
- **DaVinci Resolve**: XML project file
- **Generic XML**: Universal editing software compatibility

### Batch Export
```bash
# Command-line batch processing
python src/api/cli_interface.py --input-dir "input/" --output-dir "output/"
```

## ⚙️ Advanced Settings

### Model Configuration
Edit `configs/model_config.yaml`:
```yaml
models:
  chinese:
    name: "qwen2.5-7b-zh"
    quantization: "Q4_K_M"
    memory_limit: "3.8GB"
  english:
    name: "mistral-7b-en"
    quantization: "Q5_K_M"
    memory_limit: "4.2GB"
```

### Performance Tuning
Edit `configs/clip_settings.json`:
```json
{
  "processing": {
    "max_concurrent_tasks": 2,
    "memory_threshold": 0.85,
    "cache_size": "1GB"
  },
  "quality": {
    "emotion_sensitivity": 0.7,
    "narrative_coherence": 0.8,
    "pacing_optimization": true
  }
}
```

### Custom Styles
Create custom editing styles in `configs/narrative/`:
```yaml
# custom_style.yaml
style_name: "thriller"
parameters:
  tension_curve: "exponential"
  cut_frequency: "high"
  emotion_intensity: 0.9
  suspense_building: true
```

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: Model Download Slow
**Solution**:
```bash
# Use mirror for faster downloads
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Issue 2: Insufficient Memory
**Solutions**:
- Select lighter quantization models
- Close memory-intensive applications
- Process videos in segments

#### Issue 3: Subtitle Format Error
**Solutions**:
- Use standard SRT format
- Check timecode format: `00:00:01,000 --> 00:00:05,000`
- Ensure UTF-8 encoding

#### Issue 4: Processing Timeout
**Solutions**:
- Reduce video length
- Lower quality settings
- Check system resources

### Performance Optimization

#### Memory Optimization
```python
# Enable memory optimization
import gc
gc.collect()  # Force garbage collection

# Monitor memory usage
from src.utils.memory_guard import MemoryGuard
guard = MemoryGuard()
print(guard.get_memory_info())
```

#### Speed Optimization
- Use SSD storage for materials
- Enable GPU acceleration (if available)
- Optimize model quantization levels
- Use batch processing for multiple files

### Debugging Mode
Enable detailed logging:
```bash
# Run with debug logging
python simple_ui_fixed.py --debug --log-level DEBUG
```

## 📞 Support

### Documentation
- **Quick Start**: [5-minute guide](../zh/QUICKSTART.md)
- **Installation Guide**: [Detailed setup](../../INSTALLATION.md)
- **API Reference**: [Developer docs](../API_REFERENCE.md)
- **FAQ**: [Common questions](../../FAQ.md)

### Community Support
- **GitHub Issues**: [Report bugs](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
- **GitHub Discussions**: [Technical discussions](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/discussions)
- **Email Support**: [peresbreedanay7156@gmail.com](mailto:peresbreedanay7156@gmail.com)

### Contributing
We welcome contributions! See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

**Happy editing with VisionAI-ClipsMaster!** 🎬✨
