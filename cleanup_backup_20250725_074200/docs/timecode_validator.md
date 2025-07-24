# 时间轴精密校验器

## 概述

时间轴精密校验器是VisionAI-ClipsMaster的质量保证组件之一，用于高精度验证字幕文件与视频内容的同步性。此模块支持帧级精度的校验，可以检测字幕文本是否在正确的视频帧上出现，确保混剪内容的时间同步精确度。

## 主要功能

- **帧级精确验证**：检测每条字幕是否在其时间戳对应的视频帧上实际出现
- **高精度容错**：支持设置容错范围，默认精度控制在±0.5帧内（约16ms@30fps）
- **多种验证模式**：支持基本检测和OCR文本识别两种验证模式
- **批量验证**：支持批量处理多个字幕和视频文件对
- **详细报告**：提供验证过程的详细统计和结果报告

## 技术实现

### 基本原理

时间轴精密校验器的工作原理是：
1. 解析字幕文件，获取每条字幕的时间戳和文本内容
2. 对于每条字幕，根据其起始时间定位到视频的对应帧
3. 分析该帧，检测是否包含字幕区域
4. 验证字幕区域中的文本是否与字幕文件中的文本匹配

### 核心组件

- **FrameExactValidator**: 基础字幕帧验证器，使用图像处理技术检测字幕区域存在性
- **OCRSubtitleValidator**: 高级字幕验证器，使用OCR技术识别视频帧中的实际文本内容并与字幕文本比较

### 技术指标

- **验证精度**: ±0.5帧（约16ms@30fps）
- **容错阈值**: 可配置，默认匹配阈值为0.7（文本相似度）
- **通过标准**: 默认95%的字幕通过验证即为整体通过

## 使用方法

### 基本用法

```python
from src.quality import FrameExactValidator

# 创建验证器
validator = FrameExactValidator()

# 验证单个字幕和视频文件
result = validator.validate("path/to/subtitle.srt", "path/to/video.mp4")

# 检查验证结果
if result:
    print("验证通过")
else:
    print("验证失败")
    
# 获取详细结果
details = validator.get_last_results()
print(f"通过率: {details.get('pass_rate', 0):.2%}")
```

### 使用OCR验证

```python
from src.quality import OCRSubtitleValidator

# 创建OCR验证器（需要pytesseract库）
validator = OCRSubtitleValidator(tolerance_frames=0.5, ocr_threshold=0.7)

# 验证字幕和视频
result = validator.validate("path/to/subtitle.srt", "path/to/video.mp4")
```

### 批量验证

```python
# 准备字幕和视频文件对
pairs = [
    ("subtitle1.srt", "video1.mp4"),
    ("subtitle2.srt", "video2.mp4"),
]

# 批量验证
results = validator.validate_batch(pairs)

# 查看每个文件的验证结果
for video_name, passed in results.items():
    print(f"{video_name}: {'通过' if passed else '失败'}")
```

### 命令行工具

项目提供了命令行工具用于快速验证：

```bash
# 验证单个文件
python src/examples/timecode_validator_example.py --video path/to/video.mp4 --srt path/to/subtitle.srt

# 使用OCR模式
python src/examples/timecode_validator_example.py --video path/to/video.mp4 --srt path/to/subtitle.srt --mode ocr

# 调整容错参数
python src/examples/timecode_validator_example.py --video path/to/video.mp4 --srt path/to/subtitle.srt --tolerance 1.0 --threshold 0.6

# 批量验证
python src/examples/timecode_validator_example.py --batch-file batch_list.csv
```

## 技术依赖

- **必需依赖**
  - opencv-python: 用于视频处理和图像分析
  - numpy: 用于数值计算

- **可选依赖**
  - pytesseract: 用于OCR文本识别（需要安装Tesseract OCR引擎）

## 常见问题

### 验证准确性

- **字幕区域检测**：当前实现假设字幕位于画面底部区域，如果字幕位置不规则，可能会影响检测准确性
- **OCR识别率**：OCR模式下识别准确性受字幕样式、字体、背景等因素影响
- **硬字幕与软字幕**：此验证器主要适用于硬字幕（嵌入视频画面的字幕），对于软字幕可能无法正确验证

### 性能考虑

- **验证速度**：帧级验证需要处理视频帧，对于长视频可能耗时较长
- **OCR模式开销**：OCR模式比基本检测模式耗时更长，但提供更准确的验证结果

## 最佳实践

1. **选择合适的验证模式**：对于简单验证，使用基本模式；对于需要高精度文本匹配的场景，使用OCR模式
2. **调整容错参数**：根据视频特性调整容错参数，高帧率视频可能需要更严格的容错设置
3. **预处理字幕文件**：确保字幕文件格式正确，避免解析错误
4. **结合其他验证工具**：与其他质量验证工具配合使用，全面保证视频质量

## 实现细节

### 字幕区域检测算法

时间轴精密校验器使用以下步骤检测字幕区域：
1. 将视频帧转换为灰度图像
2. 截取画面底部30%区域（字幕通常出现的位置）
3. 对该区域进行二值化处理，突出文字像素
4. 分析白色像素（可能是文字）的比例，判断是否包含字幕

### 文本相似度计算

OCR模式下，使用Levenshtein距离（编辑距离）计算识别文本与期望文本的相似度：
1. 将文本归一化（转为小写，移除标点符号等）
2. 计算两段文本之间的编辑距离
3. 归一化编辑距离到[0,1]范围，作为相似度得分 