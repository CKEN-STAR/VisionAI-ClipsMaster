"""
ClipsMaster Python 批量任务调用示例

- 需先准备 test_data/ 目录下的多个测试视频和字幕（如 test1.mp4, test1.srt 等）
- 默认使用中文模型（Qwen2.5-7B），英文模型配置已保留但未下载模型本体
- 生成结果会输出每个任务的工程文件路径和渲染耗时
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sdk')))
from clipsmaster_sdk import ClipsMasterClient

# 批量任务参数
VIDEO_LIST = [
    ("test_data/test1.mp4", "test_data/test1.srt"),
    ("test_data/test2.mp4", "test_data/test2.srt"),
    # 可继续添加更多任务
]
QUANT_LEVEL = "Q4_K_M"
LANG = "zh"

if __name__ == "__main__":
    client = ClipsMasterClient()
    results = []
    for video_path, srt_path in VIDEO_LIST:
        try:
            result = client.generate_clip(video_path, srt_path, quant_level=QUANT_LEVEL, lang=LANG)
            print(f"[{video_path}] 生成结果: {result}")
            results.append(result)
        except Exception as e:
            print(f"[{video_path}] 请求失败: {e}")
    print(f"批量处理完成，共{len(results)}个任务。") 