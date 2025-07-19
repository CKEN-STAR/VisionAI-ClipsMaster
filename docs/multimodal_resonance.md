# 多模态情感共振模块

多模态情感共振模块是VisionAI-ClipsMaster的一个核心组件，用于根据内容的情感类型自动增强视频和音频效果，实现跨模态的情感协同增强。

## 主要功能

1. **情感检测**：根据文本内容自动检测场景的情感类型和强度
2. **视觉增强**：根据情感类型应用相应的色彩调整、速度变化和特殊效果
3. **听觉增强**：添加情感匹配的背景音乐、音效和音频处理效果
4. **节奏同步**：将情感效果与视频节奏动态同步
5. **情感流程分析**：分析整个视频的情感流程和高潮点

## 情感类型效果对应关系

不同情感类型会应用不同的视觉和听觉效果：

| 情感类型 | 视觉效果 | 听觉效果 |
|---------|---------|---------|
| 悲伤 | 冷色调、低饱和度、晕影效果、减速 | 悲伤钢琴曲、混响、低音量 |
| 喜悦 | 暖色调、高饱和度、发光效果、加速 | 欢快节奏、高音增强 |
| 紧张 | 对比度增强、轻微抖动、快速切换 | 悬疑音乐、低音增强 |
| 恐惧 | 强冷色调、噪点、画面闪烁、暗调 | 恐怖音效、强混响、低频增强 |
| 愤怒 | 暖色偏红、锐化、强对比度 | 强烈节奏、大音量、全频段增强 |
| 惊讶 | 亮度增加、闪光效果、缩放 | 惊奇音效、瞬间强调、高频增强 |

## 使用方法

### 单个场景处理

```python
from src.emotion import EmotionalResonance

# 创建情感共振器实例
resonator = EmotionalResonance()

# 处理单个场景
scene = {
    "text": "他站在雨中，泪水与雨水一起滑落脸颊，内心充满了对过去的思念。",
    "video_path": "assets/videos/rain_scene.mp4",
    "duration": 15.0
}

# 应用情感效果
enhanced_scene = resonator.add_audiovisual_cues(scene)

# 处理节奏同步（如果场景包含节奏数据）
if "rhythm" in scene:
    enhanced_scene = resonator.synchronize_emotion_with_rhythm(enhanced_scene)

# 输出结果
print(f"检测到的情感: {enhanced_scene['applied_emotion_resonance']['type']}")
print(f"应用的视频效果: {len(enhanced_scene.get('video_effects', []))} 个")
print(f"应用的音频效果: {len(enhanced_scene.get('audio_effects', []))} 个")
```

### 处理完整脚本

```python
from src.emotion import process_script_with_resonance

# 创建脚本
script = {
    "title": "雨中邂逅",
    "scenes": [
        {
            "text": "城市的清晨，阳光明媚，小明准备出门。",
            "video_path": "assets/videos/morning.mp4",
            "duration": 8.0
        },
        {
            "text": "突然，天空乌云密布，下起了大雨。",
            "video_path": "assets/videos/rain.mp4",
            "duration": 10.0
        },
        # 更多场景...
    ]
}

# 处理整个脚本
enhanced_script = process_script_with_resonance(script)

# 分析情感流程
emotion_flow = enhanced_script["emotion_flow"]
print(f"主要情感: {emotion_flow['dominant_emotion']}")
print(f"情感变化模式: {emotion_flow['emotional_pattern']}")
print(f"情感高峰点数量: {len(emotion_flow.get('emotional_peaks', []))}")
```

## 配置

情感共振模块的配置文件位于 `configs/emotion_resonance.yaml`，可以通过修改该文件来调整各种情感类型的效果参数：

- 视频效果参数（色温、饱和度、对比度等）
- 音频效果参数（音量、均衡器设置等）
- 节奏同步策略
- 情感流程分析参数

例如调整"悲伤"情感的效果：

```yaml
emotion_effects:
  悲伤:
    video:
      color_grading:
        temperature: -15    # 调整色温
        saturation: -20     # 调整饱和度
    audio:
      bgm_type: "sad_piano" # 背景音乐类型
```

## 技术实现

多模态情感共振模块使用以下技术实现情感增强：

1. **情感检测**：结合关键词匹配和情感焦点定位技术
2. **视觉处理**：色彩调整、特效应用、速度变换
3. **音频处理**：背景音乐选择、混响、均衡器调整
4. **节奏同步**：基于峰值检测的重点强调

## 与其他模块的集成

多模态情感共振模块可以与其他VisionAI-ClipsMaster的模块无缝集成：

- **情感焦点定位器**：提供情感检测的基础
- **情感词汇强化器**：与字幕效果协同工作
- **情感强度映射器**：提供情感强度曲线支持

## 示例和演示

可以查看 `examples/multimodal_resonance_demo.py` 了解更多使用示例，或运行 `test_multimodal_resonance.py` 查看模块的功能测试。 