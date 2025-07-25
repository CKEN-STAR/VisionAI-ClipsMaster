# ❌ VisionAI-ClipsMaster Error Codes Reference

> **Version**: v1.0.1  
> **Last Updated**: July 25, 2025  
> **Purpose**: Complete error code reference for troubleshooting

## 📋 Table of Contents

- [🔢 Error Code Format](#-error-code-format)
- [🧠 Model Errors (1000-1999)](#-model-errors-1000-1999)
- [📁 File Errors (2000-2999)](#-file-errors-2000-2999)
- [🎬 Processing Errors (3000-3999)](#-processing-errors-3000-3999)
- [💾 Memory Errors (4000-4999)](#-memory-errors-4000-4999)
- [🌐 Network Errors (5000-5999)](#-network-errors-5000-5999)
- [📤 Export Errors (6000-6999)](#-export-errors-6000-6999)
- [⚙️ Configuration Errors (7000-7999)](#-configuration-errors-7000-7999)
- [🔧 System Errors (8000-8999)](#-system-errors-8000-8999)
- [🆘 Quick Solutions](#-quick-solutions)

## 🔢 Error Code Format

Error codes follow the format: `VAIC-XXXX`
- `VAIC`: VisionAI-ClipsMaster prefix
- `XXXX`: 4-digit error number

Example: `VAIC-1001` - Model not found error

## 🧠 Model Errors (1000-1999)

### VAIC-1001: Model Not Found
**Description**: The specified AI model file cannot be located.
**Cause**: Model file missing or incorrect path.
**Solution**:
```bash
# Download missing models
python scripts/download_models.py --model mistral-7b-en
python scripts/download_models.py --model qwen2.5-7b-zh
```

### VAIC-1002: Model Load Failed
**Description**: Model file exists but failed to load.
**Cause**: Corrupted model file or insufficient permissions.
**Solution**:
```bash
# Verify model integrity
python scripts/verify_models.py
# Re-download if corrupted
python scripts/download_models.py --force-redownload
```

### VAIC-1003: Model Switch Timeout
**Description**: Model switching operation timed out.
**Cause**: System overload or memory constraints.
**Solution**:
- Close unnecessary applications
- Increase timeout in `configs/model_config.yaml`
- Use lighter quantization models

### VAIC-1004: Unsupported Model Format
**Description**: Model format is not supported.
**Cause**: Incompatible model file format.
**Solution**:
```bash
# Convert model format
python models/converters/model_converter.py --input model.bin --output model.gguf
```

### VAIC-1005: Model Quantization Failed
**Description**: Model quantization process failed.
**Cause**: Insufficient disk space or memory.
**Solution**:
- Free up disk space (minimum 2GB required)
- Use pre-quantized models from repository

### VAIC-1006: Language Detection Failed
**Description**: Unable to detect input text language.
**Cause**: Empty input or unsupported language.
**Solution**:
- Ensure input text is not empty
- Manually specify language: `--language zh` or `--language en`

## 📁 File Errors (2000-2999)

### VAIC-2001: File Not Found
**Description**: Input file cannot be located.
**Cause**: Incorrect file path or file deleted.
**Solution**:
- Verify file path is correct
- Check file permissions
- Ensure file exists in specified location

### VAIC-2002: Invalid SRT Format
**Description**: Subtitle file format is invalid.
**Cause**: Malformed SRT file structure.
**Solution**:
```bash
# Validate SRT format
python src/core/srt_parser.py --validate input.srt
# Fix common issues
python scripts/fix_srt_format.py input.srt output.srt
```

### VAIC-2003: File Encoding Error
**Description**: File encoding is not supported.
**Cause**: Non-UTF-8 encoding.
**Solution**:
```bash
# Convert to UTF-8
python scripts/convert_encoding.py input.srt --output output.srt --encoding utf-8
```

### VAIC-2004: File Size Limit Exceeded
**Description**: Input file exceeds maximum size limit.
**Cause**: File too large for processing.
**Solution**:
- Split large files into smaller segments
- Increase limit in `configs/system_settings.yaml`

### VAIC-2005: File Permission Denied
**Description**: Insufficient permissions to access file.
**Cause**: File access restrictions.
**Solution**:
- Run with administrator privileges
- Change file permissions: `chmod 644 filename`

### VAIC-2006: Corrupted Video File
**Description**: Video file is corrupted or unreadable.
**Cause**: Damaged video file.
**Solution**:
```bash
# Verify video integrity
ffmpeg -v error -i input.mp4 -f null -
# Repair if possible
ffmpeg -i input.mp4 -c copy output.mp4
```

## 🎬 Processing Errors (3000-3999)

### VAIC-3001: Processing Timeout
**Description**: Video processing operation timed out.
**Cause**: Large file size or system overload.
**Solution**:
- Reduce video length
- Increase timeout in settings
- Use faster processing mode

### VAIC-3002: Narrative Analysis Failed
**Description**: AI failed to analyze narrative structure.
**Cause**: Poor quality subtitles or unsupported content.
**Solution**:
- Improve subtitle quality
- Use manual narrative markers
- Try different AI model

### VAIC-3003: Segment Generation Failed
**Description**: Failed to generate video segments.
**Cause**: Timeline inconsistencies or missing video data.
**Solution**:
```bash
# Validate timeline
python src/core/alignment_engineer.py --validate input.srt
# Fix timeline issues
python scripts/fix_timeline.py input.srt output.srt
```

### VAIC-3004: Audio Sync Error
**Description**: Audio synchronization failed.
**Cause**: Mismatched audio/video timing.
**Solution**:
- Check original video audio sync
- Use audio offset correction: `--audio-offset 0.5`

### VAIC-3005: Quality Validation Failed
**Description**: Output quality below acceptable threshold.
**Cause**: Poor input quality or processing errors.
**Solution**:
- Use higher quality input materials
- Adjust quality settings in `configs/clip_settings.json`

## 💾 Memory Errors (4000-4999)

### VAIC-4001: Insufficient Memory
**Description**: Not enough RAM to complete operation.
**Cause**: Memory usage exceeds available RAM.
**Solution**:
```bash
# Enable memory optimization
python simple_ui_fixed.py --memory-optimize
# Use lighter models
python simple_ui_fixed.py --model-size small
```

### VAIC-4002: Memory Leak Detected
**Description**: Memory usage continuously increasing.
**Cause**: Improper memory management.
**Solution**:
- Restart application
- Update to latest version
- Report issue if persistent

### VAIC-4003: GPU Memory Insufficient
**Description**: GPU memory exhausted.
**Cause**: Model too large for GPU memory.
**Solution**:
```bash
# Force CPU mode
python simple_ui_fixed.py --device cpu
# Use smaller batch size
python simple_ui_fixed.py --batch-size 1
```

### VAIC-4004: Memory Allocation Failed
**Description**: Failed to allocate required memory.
**Cause**: System memory fragmentation.
**Solution**:
- Restart system
- Close memory-intensive applications
- Use virtual memory if available

## 🌐 Network Errors (5000-5999)

### VAIC-5001: Model Download Failed
**Description**: Failed to download AI model.
**Cause**: Network connectivity issues.
**Solution**:
```bash
# Use alternative download source
python scripts/download_models.py --mirror china
# Manual download
wget https://huggingface.co/model-name/resolve/main/model.bin
```

### VAIC-5002: Connection Timeout
**Description**: Network connection timed out.
**Cause**: Slow or unstable internet connection.
**Solution**:
- Check internet connection
- Increase timeout: `--timeout 300`
- Use offline mode if models are cached

### VAIC-5003: SSL Certificate Error
**Description**: SSL certificate verification failed.
**Cause**: Outdated certificates or network restrictions.
**Solution**:
```bash
# Skip SSL verification (not recommended for production)
python scripts/download_models.py --no-ssl-verify
```

## 📤 Export Errors (6000-6999)

### VAIC-6001: Export Format Not Supported
**Description**: Requested export format is not supported.
**Cause**: Invalid export format specified.
**Solution**:
- Use supported formats: `jianying`, `davinci`, `xml`
- Check available formats: `python src/exporters/list_formats.py`

### VAIC-6002: JianYing Export Failed
**Description**: Failed to generate JianYing project file.
**Cause**: Invalid segment data or export settings.
**Solution**:
```bash
# Validate segments
python src/exporters/jianying_pro_exporter.py --validate segments.json
# Use fallback export
python src/exporters/jianying_pro_exporter.py --fallback-mode
```

### VAIC-6003: Output Directory Not Writable
**Description**: Cannot write to specified output directory.
**Cause**: Permission restrictions or disk full.
**Solution**:
- Check directory permissions
- Ensure sufficient disk space
- Use alternative output directory

## ⚙️ Configuration Errors (7000-7999)

### VAIC-7001: Invalid Configuration
**Description**: Configuration file contains invalid settings.
**Cause**: Malformed YAML/JSON or invalid values.
**Solution**:
```bash
# Validate configuration
python scripts/validate_config.py configs/model_config.yaml
# Reset to defaults
cp configs/defaults/model_config.yaml configs/model_config.yaml
```

### VAIC-7002: Missing Configuration File
**Description**: Required configuration file not found.
**Cause**: Configuration file deleted or moved.
**Solution**:
```bash
# Restore default configuration
python scripts/restore_defaults.py
```

### VAIC-7003: Configuration Version Mismatch
**Description**: Configuration file version incompatible.
**Cause**: Outdated configuration format.
**Solution**:
```bash
# Migrate configuration
python scripts/migrate_config.py --from v1.0.0 --to v1.0.1
```

## 🔧 System Errors (8000-8999)

### VAIC-8001: Python Version Incompatible
**Description**: Python version not supported.
**Cause**: Using Python version < 3.11.
**Solution**:
- Upgrade Python to 3.11 or higher
- Use virtual environment with correct Python version

### VAIC-8002: Missing Dependencies
**Description**: Required Python packages not installed.
**Cause**: Incomplete installation.
**Solution**:
```bash
# Install missing dependencies
pip install -r requirements.txt
# Force reinstall
pip install -r requirements.txt --force-reinstall
```

### VAIC-8003: FFmpeg Not Found
**Description**: FFmpeg executable not found.
**Cause**: FFmpeg not installed or not in PATH.
**Solution**:
```bash
# Install FFmpeg
python tools/ffmpeg_installer.py
# Or manually add to PATH
export PATH=$PATH:/path/to/ffmpeg/bin
```

### VAIC-8004: Disk Space Insufficient
**Description**: Not enough disk space for operation.
**Cause**: Low disk space.
**Solution**:
- Free up disk space (minimum 2GB required)
- Use alternative storage location
- Clean temporary files: `python scripts/cleanup.py`

## 🆘 Quick Solutions

### Emergency Recovery
```bash
# Reset to factory defaults
python scripts/factory_reset.py

# Clear all caches
python scripts/clear_cache.py

# Repair installation
python scripts/repair_installation.py
```

### Diagnostic Tools
```bash
# Run system diagnostics
python scripts/diagnose_system.py

# Check model integrity
python scripts/verify_models.py

# Test basic functionality
python scripts/basic_test.py
```

### Log Analysis
```bash
# View recent errors
python scripts/analyze_logs.py --recent --errors-only

# Generate diagnostic report
python scripts/generate_diagnostic_report.py
```

---

## 📞 Get Help

If you encounter an error not listed here:

1. **Check Logs**: Look in `logs/` directory for detailed error information
2. **Run Diagnostics**: Use `python scripts/diagnose_system.py`
3. **Search Issues**: Check [GitHub Issues](https://github.com/CKEN-STAR/VisionAI-ClipsMaster/issues)
4. **Report Bug**: Create new issue with error code and logs
5. **Contact Support**: Email [peresbreedanay7156@gmail.com](mailto:peresbreedanay7156@gmail.com)

---

**VisionAI-ClipsMaster Error Codes** | Version v1.0.1 | Updated July 25, 2025
