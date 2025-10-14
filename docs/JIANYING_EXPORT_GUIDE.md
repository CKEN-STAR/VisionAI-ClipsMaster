# 剪映导出功能使用指南

## 概述

VisionAI-ClipsMaster 提供了完整的剪映草稿导出功能，可以将混剪结果导出为剪映可编辑的草稿文件，支持在剪映中进行二次编辑。

## 核心功能

### ✅ 已验证的功能
1. **草稿生成**：生成符合剪映标准的草稿文件
2. **时间轴映射**：视频片段与原始素材一一对应
3. **可编辑性**：在剪映中可以拖拽调整片段时长
4. **跨环境兼容**：支持不同设备、不同安装路径、不同草稿目录

### ✅ 质量保证
- 所有自动化测试通过（10/10）
- 用户真实验证通过
- 跨环境兼容性测试通过（4/4）

---

## 使用方法

### 方法1：通过主程序UI

在 `simple_ui_fixed.py` 中，混剪完成后会自动提示是否导出到剪映：

```python
# 运行主程序
python simple_ui_fixed.py

# 按照提示操作：
# 1. 上传视频和字幕
# 2. 生成混剪
# 3. 选择导出到剪映
```

### 方法2：使用便捷工具

#### 从SRT字幕文件导出

```bash
python scripts/tools/export_to_jianying.py \
    --video "path/to/video.mp4" \
    --srt "path/to/subtitles.srt" \
    --name "我的项目" \
    --auto-copy
```

#### 从片段JSON文件导出

```bash
python tools/export_to_jianying.py \
    --video "path/to/video.mp4" \
    --segments "path/to/segments.json" \
    --name "我的项目" \
    --auto-copy
```

**片段JSON格式**：
```json
[
    {
        "start_time": 0.0,
        "end_time": 5.0,
        "speed": 1.0,
        "volume": 1.0
    },
    {
        "start_time": 10.0,
        "end_time": 15.0,
        "speed": 1.0,
        "volume": 1.0
    }
]
```

### 方法3：编程接口

```python
from src.exporters.jianying_exporter_adapter import JianyingExporterAdapter

# 创建导出器
adapter = JianyingExporterAdapter(width=1920, height=1080, fps=30)

# 准备项目数据
project_data = {
    "project_name": "我的项目",
    "segments": [
        {
            "source_file": "path/to/video.mp4",
            "start_time": 0.0,
            "end_time": 5.0,
            "duration": 5.0,
            "speed": 1.0,
            "volume": 1.0
        },
        {
            "source_file": "path/to/video.mp4",
            "start_time": 10.0,
            "end_time": 15.0,
            "duration": 5.0,
            "speed": 1.0,
            "volume": 1.0
        }
    ]
}

# 导出草稿
draft_path = adapter.export_project(project_data, "data/output")

if draft_path:
    print(f"草稿已导出到: {draft_path}")
```

---

## 草稿文件结构

### 文件组成

```
项目名称/
├── draft_content.json      # 草稿内容文件
└── draft_meta_info.json    # 草稿元信息文件
```

### draft_content.json

包含完整的草稿内容：

```json
{
    "id": "草稿ID",
    "duration": 15000000,  // 总时长（微秒）
    "materials": {
        "videos": [...],   // 视频素材列表
        "audios": [],      // 音频素材列表
        "texts": []        // 文本素材列表
    },
    "tracks": [
        {
            "type": "video",
            "segments": [...]  // 视频片段列表
        }
    ],
    "canvas_config": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "ratio": "16:9"
    }
}
```

### draft_meta_info.json

包含草稿元信息：

```json
{
    "draft_id": "草稿ID",
    "draft_name": "项目名称",
    "draft_fold_path": "草稿文件夹路径",
    "tm_duration": 15000000  // 总时长（微秒）
}
```

---

## 导入到剪映

### 自动导入（推荐）

使用 `--auto-copy` 参数自动复制到剪映目录：

```bash
python tools/export_to_jianying.py \
    --video "video.mp4" \
    --srt "subtitles.srt" \
    --name "我的项目" \
    --auto-copy
```

### 手动导入

1. **找到草稿文件夹**
   ```
   data/output/项目名称/
   ```

2. **复制到剪映草稿目录**
   
   Windows:
   ```
   C:\Users\用户名\AppData\Local\JianyingPro\User Data\Projects\com.lveditor.draft\
   ```
   
   macOS:
   ```
   ~/Library/Application Support/JianyingPro/User Data/Projects/com.lveditor.draft/
   ```

3. **打开剪映**
   - 启动剪映专业版
   - 在草稿列表中查找项目
   - 双击打开

---

## 在剪映中编辑

### 基本操作

1. **查看时间轴**
   - 时间轴上显示所有视频片段
   - 片段按顺序排列，无间隙

2. **调整片段时长**
   - 选中片段
   - 拖拽片段边缘
   - 向右拖拽：延长时长
   - 向左拖拽：缩短时长

3. **移动片段**
   - 拖拽片段到不同位置
   - 调整片段顺序

4. **分割片段**
   - 将播放头移动到分割位置
   - 点击分割按钮
   - 生成两个独立片段

5. **删除片段**
   - 选中片段
   - 按Delete键或点击删除按钮

### 高级编辑

1. **添加转场**
   - 在两个片段之间添加转场效果
   - 选择转场类型和时长

2. **添加BGM**
   - 从音频库选择音乐
   - 拖拽到音频轨道

3. **添加字幕**
   - 使用剪映的字幕功能
   - 自动识别或手动添加

4. **添加特效**
   - 选择视频特效
   - 应用到片段

5. **调色**
   - 使用剪映的调色工具
   - 调整亮度、对比度、饱和度等

---

## 跨环境使用

### 在不同设备上使用

1. **导出草稿**
   ```bash
   # 在设备A上导出
   python tools/export_to_jianying.py \
       --video "video.mp4" \
       --srt "subtitles.srt" \
       --name "我的项目"
   ```

2. **复制文件**
   ```
   # 复制草稿文件夹和视频文件到设备B
   项目名称/
   video.mp4
   ```

3. **在设备B上使用**
   - 将草稿文件夹复制到剪映目录
   - 确保视频文件路径正确
   - 打开剪映，导入草稿

### 注意事项

1. **视频文件路径**
   - 草稿使用绝对路径存储视频位置
   - 跨设备使用时，确保视频文件在相同位置
   - 或者在剪映中重新链接视频文件

2. **草稿目录**
   - `draft_fold_path` 会被剪映自动更新
   - 不需要手动修改

3. **剪映版本**
   - 建议使用剪映专业版 5.9.0 或更高版本
   - 不同版本可能有细微差异

---

## 故障排除

### 问题1：草稿无法打开

**可能原因**：
- 视频文件不存在
- 视频文件路径错误
- 草稿文件不完整

**解决方案**：
1. 检查视频文件是否存在
2. 检查视频文件路径是否正确
3. 检查草稿文件夹是否包含两个JSON文件
4. 尝试重新导出草稿

### 问题2：素材库不显示素材

**说明**：
- 这是剪映的正常行为
- 素材已经在时间轴上使用
- 剪映的素材库只显示"未使用"的素材

**验证**：
- 检查时间轴上是否有片段
- 尝试拖拽片段边缘
- 如果可以拖拽，说明素材链接正常

### 问题3：无法拖拽调整

**可能原因**：
- 片段被锁定
- 时间轴缩放比例不合适

**解决方案**：
1. 检查片段是否被锁定
2. 调整时间轴缩放比例
3. 尝试选中片段后再拖拽

### 问题4：导出失败

**可能原因**：
- 视频文件不存在
- 输出目录权限不足
- 片段数据格式错误

**解决方案**：
1. 检查视频文件是否存在
2. 检查输出目录是否有写入权限
3. 检查片段数据格式是否正确
4. 查看错误日志

---

## 技术细节

### 时间单位

所有时间值在内部使用微秒（μs）：

```python
# 转换示例
5秒 = 5,000,000微秒
0.5秒 = 500,000微秒
```

### 视频路径处理

所有视频路径自动转换为绝对路径：

```python
# 输入
相对路径: "data/input/video.mp4"

# 输出
绝对路径: "D:\Project\VisionAI-ClipsMaster\data\input\video.mp4"
```

### 素材管理

- 自动去重：相同视频文件只创建一个素材对象
- 自动提取元数据：使用pymediainfo提取视频信息
- 自动验证：检查文件是否存在

### 草稿格式

- 符合剪映5.9.0版本标准
- 使用标准JSON格式
- 包含所有必需字段

---

## 最佳实践

### 1. 文件组织

```
project/
├── videos/           # 原始视频
├── subtitles/        # 字幕文件
├── segments/         # 片段定义
└── output/           # 导出的草稿
```

### 2. 命名规范

- 使用有意义的项目名称
- 避免特殊字符
- 支持中文名称

### 3. 版本管理

- 保存草稿的多个版本
- 使用日期或版本号命名
- 定期备份

### 4. 性能优化

- 使用SSD存储视频文件
- 避免过长的视频文件
- 合理控制片段数量

---

## 参考资料

- [剪映官方文档](https://www.capcut.cn/)
- [pyCapCut项目](https://github.com/GuanYixuan/pyCapCut)
- [JIANYING_EXPORT_DIAGNOSIS_REPORT.md](../JIANYING_EXPORT_DIAGNOSIS_REPORT.md)
- [FINAL_VERIFICATION_REPORT.md](../FINAL_VERIFICATION_REPORT.md)

---

## 更新日志

### 2025-10-05
- ✅ 完成剪映导出功能开发
- ✅ 通过所有自动化测试（10/10）
- ✅ 通过用户真实验证
- ✅ 通过跨环境兼容性测试（4/4）
- ✅ 创建完整的使用文档

---

**文档版本**：1.0  
**最后更新**：2025-10-05  
**维护者**：VisionAI-ClipsMaster Team  

