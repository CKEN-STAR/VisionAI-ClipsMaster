# ClipsMaster Python Example

## 目录结构
- basic_usage.py         # 单任务调用示例
- batch_processing.py    # 批量任务调用示例
- test_data/             # 存放测试视频和字幕（需用户自备）

## 使用说明

1. 准备测试数据
   - 将测试视频（如 test.mp4）和对应字幕（如 test.srt）放入 test_data/ 目录
   - 字幕需为标准 SRT 格式

2. 运行示例
   - 单任务示例：`python basic_usage.py`
   - 批量任务示例：`python batch_processing.py`

3. 注意事项
   - 默认仅支持中文模型，英文模型配置已保留，需后续手动下载模型本体
   - 生成结果会输出工程文件路径和渲染耗时

4. 常见问题
   - 如遇"模型未找到"或"内存不足"等错误，请检查模型文件和设备配置

## 期望输出示例

运行 basic_usage.py 后，终端应输出如下内容（仅供参考）：

生成结果：
{'status': 'success', 'project_path': 'output/edit_projects/xxx.jyproj', 'render_time': 12.3}
生成成功，工程文件路径: output/edit_projects/xxx.jyproj, 渲染耗时: 12.3s

## API 测试

如需直接测试后端API，可使用 postman_collection/ClipsMaster_API.postman_collection.json 进行接口验证。 