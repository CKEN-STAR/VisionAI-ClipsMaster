# 差异可视化报告

## 概述

差异可视化报告是VisionAI-ClipsMaster项目的测试和评估工具，用于直观地比较测试视频与黄金标准视频之间的差异。通过精美的HTML报告，开发者和用户可以快速了解视频质量、字幕匹配度和剧情完整性等关键指标的表现。

## 主要功能

1. **视频关键帧对比**：提取并对比测试视频与黄金标准视频的关键帧，直观展示画面差异
2. **时间轴差异分析**：可视化展示字幕时间轴的差异，帮助评估时间对齐精度
3. **字幕文本差异高亮**：突出显示字幕文本中的修改、添加和删除内容
4. **多维度质量评估**：集成了视频质量、字幕匹配度和剧情连贯性的综合评分
5. **版权安全检测**：提供水印和音频指纹的安全评估结果

## 使用方法

### 基本使用

```python
from tests.golden_samples.report_generator import generate_diff_report

# 生成差异报告
report_path = generate_diff_report(
    test_video="path/to/test_video.mp4",
    golden_video="path/to/golden_video.mp4",
    test_srt="path/to/test_subtitle.srt",  # 可选，默认为视频同名srt文件
    golden_srt="path/to/golden_subtitle.srt",  # 可选
    output_dir="path/to/reports"  # 可选
)

print(f"报告已生成: {report_path}")
```

### 命令行使用

也可以直接从命令行运行报告生成器：

```bash
python tests/golden_samples/report_generator.py test_video.mp4 golden_video.mp4 [test_srt.srt] [golden_srt.srt] [output_dir]
```

## 报告内容

生成的HTML报告包含以下主要部分：

1. **整体质量评分**：根据容差管理系统计算的总体评分和质量级别（优秀/提示/警告/严重问题）

2. **质量指标摘要**：
   - 视频质量指标（分辨率匹配、PSNR、色彩保真度等）
   - 字幕质量指标（时间码误差、文本相似度、实体匹配率等）
   - 剧情质量指标（情节点保留率、角色弧线完整度、时长比例等）

3. **视频关键帧对比**：
   - 并排展示测试视频和黄金标准的关键帧
   - 显示每组关键帧的相似度百分比

4. **时间轴对比分析**：
   - 可视化时间轴差异图
   - 时间轴统计数据（平均起始时间差异、平均结束时间差异、最大时间差异）

5. **字幕文本对比**：
   - 高亮显示文本差异
   - 显示每条字幕的相似度百分比

## 技术细节

### 视觉比较算法

报告使用了以下算法来评估视频内容差异：

- **颜色直方图比较**：使用HSV色彩空间的直方图相似度评估整体画面色彩分布差异
- **PSNR计算**：评估帧级别的图像质量
- **关键帧提取**：均匀采样或场景变化检测提取关键帧

### 字幕比较技术

字幕比较使用以下技术：

- **序列比对算法**：基于difflib的SequenceMatcher计算文本相似度和差异
- **实体抽取**：检测并比较字幕中的关键实体（如人名、地点）保留情况
- **时间轴对齐**：比较字幕时间码的精确对齐程度

## 与容差管理系统的集成

差异可视化报告与VisionAI-ClipsMaster的容差管理系统紧密集成，使用统一的质量标准和容差规则：

- 报告中的评分和通过/失败判定基于配置的容差规则
- 支持根据设备资源自动调整容差标准
- 提供与容差管理系统一致的质量级别分类

## 相关文件

- 实现代码：`tests/golden_samples/report_generator.py`
- 辅助工具：`src/utils/file_checker.py`
- 测试代码：`tests/golden_samples/test_report_generator.py`
- 配置文件：`configs/tolerance_rules.yaml`（共享容差管理系统的配置） 