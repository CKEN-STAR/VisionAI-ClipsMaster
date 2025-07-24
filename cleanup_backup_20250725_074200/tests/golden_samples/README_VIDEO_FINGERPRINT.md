# 视频指纹提取引擎

视频指纹提取引擎是VisionAI-ClipsMaster项目的核心组件之一，用于从视频中提取稳定的视觉特征指纹，实现视频内容的比对、查重和相似度分析。无论视频编码、分辨率或轻微剪辑如何变化，相同内容的视频都能生成高度相似的指纹。

## 核心指标

- **相同视频不同编码**: 相似度 > 0.99
- **高度相似内容**: 相似度 0.95-0.99
- **部分相似内容**: 相似度 0.70-0.95
- **不同内容视频**: 相似度 < 0.70

## 功能特点

- **编码无关性**: 无论视频使用何种编码格式(H.264, VP9, AV1等)，指纹基本保持一致
- **分辨率无关性**: 同一内容的不同分辨率版本能产生高度相似的指纹
- **帧率无关性**: 不同帧率的同一内容视频能产生高度相似的指纹
- **高性能**: 采用抽样技术，无需处理视频中的每一帧
- **多维特征**: 结合灰度直方图和边缘特征，提高特征区分能力
- **批量处理**: 支持批量提取和比较指纹，适用于大规模视频库

## 使用方法

### 代码中直接使用

```python
from tests.golden_samples.video_fingerprint import VideoFingerprint, compare_videos

# 方法1: 简单比较两个视频
similarity = compare_videos("path/to/video1.mp4", "path/to/video2.mp4")
print(f"相似度: {similarity:.4f}")

# 方法2: 使用VideoFingerprint类进行更复杂的操作
fp = VideoFingerprint(sample_frames=16, hist_bins=256)

# 提取单个视频指纹
signature = fp.extract_signature("path/to/video.mp4")

# 比较两个指纹
sig1 = fp.extract_signature("path/to/video1.mp4")
sig2 = fp.extract_signature("path/to/video2.mp4")
similarity = fp.compare_signatures(sig1, sig2)

# 批量提取指纹
video_paths = ["video1.mp4", "video2.mp4", "video3.mp4"]
signatures = fp.batch_extract_signatures(video_paths)

# 查找相似视频
similar_videos = fp.find_similar_videos(
    "target.mp4", 
    ["video1.mp4", "video2.mp4", "video3.mp4"],
    threshold=0.7
)
```

### 命令行工具

项目提供了方便的命令行工具用于比较视频相似度：

#### Windows

```bash
# 比较两个视频
scripts\compare_videos.bat compare video1.mp4 video2.mp4

# 批量查找相似视频
scripts\compare_videos.bat batch target.mp4 D:\videos\collection --threshold 0.8 --limit 20
```

#### 通用Python脚本

```bash
# 比较两个视频
python scripts/compare_videos.py compare video1.mp4 video2.mp4

# 批量查找相似视频
python scripts/compare_videos.py batch target.mp4 /path/to/videos --threshold 0.8 --limit 20
```

## 技术实现

视频指纹提取引擎采用了以下技术来确保鲁棒性和准确性：

1. **关键帧抽样**: 均匀采样视频中的帧，确保覆盖整个视频的内容
2. **多特征融合**:
   - 灰度直方图: 捕获整体亮度分布
   - 边缘特征: 检测图像中的形状和结构
3. **特征归一化**: 将特征值归一化到0-1范围，减少亮度变化影响
4. **余弦相似度**: 使用余弦相似度度量两个指纹向量的相似程度

## 性能考虑

- 提取指纹的时间与视频长度相关，但由于使用了抽样技术，性能相对较好
- 对于长视频(>10分钟)，可以考虑增加`sample_frames`参数以获得更准确的结果
- 内存使用随视频分辨率增加而增加，但一般不会成为瓶颈

## 应用场景

- **视频查重**: 检测视频库中的重复内容
- **版权保护**: 识别可能侵权的相似内容
- **内容审核**: 检测与已知内容相似的视频
- **片段识别**: 判断某视频片段是否来自特定源视频
- **视频组织**: 将相似内容的视频进行分组

## 扩展与优化

- **指纹存储**: 可以使用数据库存储视频指纹，支持大规模视频库
- **加速计算**: 可考虑使用GPU加速指纹提取过程
- **深度学习**: 可整合深度学习模型提取更高级的语义特征
- **时间序列比较**: 可添加时间序列比对，支持片段匹配

## 单元测试

引擎包含全面的单元测试，确保在各种情况下的准确性：

```bash
# 运行所有测试
python -m unittest tests/unit_test/test_video_fingerprint.py

# 运行特定测试
python -m unittest tests.unit_test.test_video_fingerprint.TestVideoFingerprint.test_different_encoding_same_content
```

## 依赖库

- OpenCV (cv2): 视频处理和图像特征提取
- NumPy: 数组操作和计算
- SciPy: 用于相似度计算 