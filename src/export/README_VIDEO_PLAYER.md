# 视频播放器模块 (Video Player Module)

## 概述

视频播放器模块是 VisionAI-ClipsMaster 项目的一个核心组件，提供了跨平台的视频播放和剪辑功能。它与项目中的时间轴映射和素材指纹功能集成，为用户提供了一体化的视频预览和剪辑体验。

## 主要功能

- **基础视频播放**：播放、暂停、停止等基本控制
- **帧级精确控制**：逐帧前进/后退、精确时间码定位
- **剪辑点标记**：设置入点(In)和出点(Out)，并基于选区创建片段
- **时间轴集成**：与时间轴映射模块集成，支持片段可视化和导出
- **素材指纹集成**：与素材指纹模块集成，支持素材识别和管理
- **帧提取**：提取选定区域的帧图像，用于缩略图或预览生成

## 类和接口

### VideoPlayer 类

核心播放器类，提供所有视频播放和控制功能。

```python
player = VideoPlayer(video_path=None)  # 创建播放器实例
player.load_video(video_path)          # 加载视频
player.play()                          # 开始播放
player.pause()                         # 暂停播放
player.seek_to_frame(frame_number)     # 定位到指定帧
player.seek_to_time(time_seconds)      # 定位到指定时间
player.next_frame()                    # 下一帧
player.previous_frame()                # 上一帧
player.set_in_point(frame_number=None) # 设置入点
player.set_out_point(frame_number=None)# 设置出点
```

## 回调函数

视频播放器通过回调函数支持自定义事件处理：

```python
# 帧回调，用于处理每一帧图像
player.set_frame_callback(callback)  # callback(frame) -> None

# 位置回调，用于跟踪播放位置
player.set_position_callback(callback)  # callback(frame_index, time_seconds) -> None
```

## 与其它模块集成

### 素材指纹集成

视频播放器可以与素材指纹模块集成，用于识别和管理素材：

```python
from src.export.asset_fingerprint import generate_asset_id, save_asset_fingerprint

# 获取当前视频的素材ID
asset_id = generate_asset_id(player.video_path)

# 保存素材指纹
fingerprint_path = save_asset_fingerprint(player.video_path)
```

### 时间轴映射集成

视频播放器可以与时间轴映射模块集成，用于创建和导出编辑轨道：

```python
from src.export.timeline_mapper import map_segments_to_timeline

# 从播放器选择点创建片段
segment = create_segment_from_selection(player, text="场景标题")
segments.append(segment)

# 生成时间轴数据
timeline_data = map_segments_to_timeline(segments, player.fps)
```

## 示例用法

### 基本播放控制

```python
from src.export.video_player import VideoPlayer

# 创建播放器并加载视频
player = VideoPlayer("path/to/video.mp4")

# 播放控制
player.play()      # 开始播放
player.pause()     # 暂停播放
player.next_frame()  # 下一帧
player.previous_frame()  # 上一帧

# 定位
player.seek_to_time(10.5)  # 定位到 10.5 秒
player.seek_to_frame(300)  # 定位到第 300 帧

# 设置剪辑点
player.set_in_point()  # 设置当前位置为入点
player.set_out_point() # 设置当前位置为出点

# 获取剪辑信息
clip_info = player.get_selected_clip_info()
print(f"选择区域: {clip_info['in_timecode']} - {clip_info['out_timecode']} (时长: {clip_info['duration']}秒)")

# 提取帧
frame_files = player.extract_clip_frames(output_dir="frames", frame_interval=10)

# 关闭播放器
player.close()
```

### 与图形界面集成

```python
import cv2
from src.export.video_player import VideoPlayer

def on_frame(frame):
    # 显示帧
    cv2.imshow("Video Player", frame)
    
def on_position(frame_index, time_seconds):
    # 显示位置信息
    print(f"Frame: {frame_index} | Time: {time_seconds:.2f}s")

# 创建播放器
player = VideoPlayer("path/to/video.mp4")

# 设置回调
player.set_frame_callback(on_frame)
player.set_position_callback(on_position)

# 创建窗口
cv2.namedWindow("Video Player", cv2.WINDOW_NORMAL)

# 开始播放
player.play()

# 按键控制
while True:
    key = cv2.waitKey(1)
    
    if key == 27:  # ESC
        break
    elif key == 32:  # 空格
        player.toggle_play_pause()
        
player.close()
cv2.destroyAllWindows()
```

### 完整的集成示例

查看 `demo_video_player.py` 脚本，它展示了视频播放器与其他模块的完整集成。

## 性能考虑

- 视频播放使用单独的线程，避免阻塞主线程
- 大文件处理采用流式处理，避免一次性加载大文件
- 帧提取支持间隔设置，减少输出文件数量和处理时间

## 测试

使用 `test_video_player.py` 进行单元测试，验证视频播放器的各项功能：

```bash
python -m src.export.test_video_player
```

## 系统要求

- Python 3.6+
- OpenCV 4.0+
- NumPy 1.16+

## 注意事项

- 视频播放依赖于 OpenCV 的视频解码能力，支持的格式取决于 OpenCV 编译时的配置
- 对于大型视频文件，建议使用低分辨率的预览版本以提高性能 