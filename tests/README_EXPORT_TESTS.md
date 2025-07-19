# VisionAI-ClipsMaster 导出功能测试框架

本目录包含了VisionAI-ClipsMaster项目的导出功能测试框架，用于测试视频导出和剪映工程文件导出功能。

## 测试文件结构

- `export_functionality_test.py`: 基本导出功能测试
- `jianying_export_test.py`: 剪映工程文件导出测试
- `ui_export_test.py`: UI导出功能测试
- `run_export_tests.py`: 运行所有导出功能测试的脚本
- `generate_export_test_report.py`: 生成导出功能测试报告的脚本

## 运行测试

### 运行所有测试

```bash
python run_export_tests.py
```

### 跳过UI测试

由于UI测试需要PyQt6环境，可能在某些环境下无法运行，可以使用`--skip-ui`参数跳过UI测试：

```bash
python run_export_tests.py --skip-ui
```

### 生成测试报告

```bash
python generate_export_test_report.py --skip-ui
```

测试报告将保存在`reports`目录下，包括JSON格式和文本格式。

## 测试内容

### 基本导出功能测试

- 测试视频导出功能
- 测试从SRT生成视频功能
- 测试导出剪映工程文件功能
- 测试SRT导出功能

### 剪映工程文件导出测试

- 测试导出剪映工程文件功能
- 测试剪映工程文件结构
- 测试剪映工程文件兼容性

### UI导出功能测试

- 测试UI中的视频导出功能
- 测试UI中使用GPU导出视频
- 测试UI中没有视频时的导出行为
- 测试UI中没有SRT时的导出行为

## 注意事项

1. 运行测试前，请确保已安装所有依赖项：
   ```bash
   pip install -r requirements.txt
   ```

2. UI测试需要PyQt6环境，如果没有安装PyQt6，可以使用`--skip-ui`参数跳过UI测试。

3. 测试中使用了模拟对象替代实际的FFmpeg调用，因此即使没有安装FFmpeg，基本功能测试也能通过。

4. 如果需要测试实际的视频导出功能，请确保已安装FFmpeg，并将其添加到系统路径中。 