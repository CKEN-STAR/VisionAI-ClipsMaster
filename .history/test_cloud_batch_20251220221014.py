#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试云端AI引擎的批量字幕生成功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.cloud_ai_engine import CloudAIEngine, CloudPlatform, CloudModel

# 硅基流动API密钥
SILICONFLOW_API_KEY = "sk-rovcxclyumgjbiihizlmrpgdnrkeyanohuvvdrkorryvqaat"

def create_test_subtitles():
    """创建测试字幕数据"""
    # 模拟3集短剧的字幕
    all_subtitles = []
    
    # 第1集
    episode1 = [
        {"id": 1, "start_time": 0.0, "end_time": 2.5, "text": "你好，我是李明。"},
        {"id": 2, "start_time": 2.5, "end_time": 5.0, "text": "我来自北京，今年25岁。"},
        {"id": 3, "start_time": 5.0, "end_time": 8.0, "text": "我一直在寻找我的真爱。"},
        {"id": 4, "start_time": 8.0, "end_time": 11.0, "text": "直到有一天，我遇见了她。"},
        {"id": 5, "start_time": 11.0, "end_time": 14.0, "text": "她的名字叫小雨，是个美丽的女孩。"},
        {"id": 6, "start_time": 14.0, "end_time": 17.0, "text": "我们在咖啡店相遇。"},
        {"id": 7, "start_time": 17.0, "end_time": 20.0, "text": "那一刻，我的心跳加速了。"},
        {"id": 8, "start_time": 20.0, "end_time": 23.0, "text": "我鼓起勇气向她打招呼。"},
        {"id": 9, "start_time": 23.0, "end_time": 26.0, "text": "她微笑着回应了我。"},
        {"id": 10, "start_time": 26.0, "end_time": 30.0, "text": "这就是我们故事的开始。"},
    ]
    all_subtitles.append(episode1)
    
    # 第2集
    episode2 = [
        {"id": 1, "start_time": 0.0, "end_time": 3.0, "text": "我们开始频繁约会。"},
        {"id": 2, "start_time": 3.0, "end_time": 6.0, "text": "每次见面都让我心动不已。"},
        {"id": 3, "start_time": 6.0, "end_time": 9.0, "text": "但是，她的家人反对我们在一起。"},
        {"id": 4, "start_time": 9.0, "end_time": 12.0, "text": "他们认为我配不上她。"},
        {"id": 5, "start_time": 12.0, "end_time": 15.0, "text": "小雨哭着告诉我这个消息。"},
        {"id": 6, "start_time": 15.0, "end_time": 18.0, "text": "我紧紧抱住她，说：我不会放弃的。"},
        {"id": 7, "start_time": 18.0, "end_time": 21.0, "text": "我要证明给他们看，我值得拥有你。"},
        {"id": 8, "start_time": 21.0, "end_time": 24.0, "text": "从那天起，我开始努力工作。"},
        {"id": 9, "start_time": 24.0, "end_time": 27.0, "text": "我要成为更好的人。"},
        {"id": 10, "start_time": 27.0, "end_time": 30.0, "text": "为了我们的未来。"},
    ]
    all_subtitles.append(episode2)
    
    # 第3集
    episode3 = [
        {"id": 1, "start_time": 0.0, "end_time": 3.0, "text": "三年后，我终于成功了。"},
        {"id": 2, "start_time": 3.0, "end_time": 6.0, "text": "我创办了自己的公司。"},
        {"id": 3, "start_time": 6.0, "end_time": 9.0, "text": "我带着诚意去见她的父母。"},
        {"id": 4, "start_time": 9.0, "end_time": 12.0, "text": "这一次，他们终于接受了我。"},
        {"id": 5, "start_time": 12.0, "end_time": 15.0, "text": "小雨激动得流下了眼泪。"},
        {"id": 6, "start_time": 15.0, "end_time": 18.0, "text": "我单膝跪地，向她求婚。"},
        {"id": 7, "start_time": 18.0, "end_time": 21.0, "text": "小雨，你愿意嫁给我吗？"},
        {"id": 8, "start_time": 21.0, "end_time": 24.0, "text": "她含泪点头：我愿意！"},
        {"id": 9, "start_time": 24.0, "end_time": 27.0, "text": "这是我人生中最幸福的时刻。"},
        {"id": 10, "start_time": 27.0, "end_time": 30.0, "text": "我们的爱情故事，终于有了美好的结局。"},
    ]
    all_subtitles.append(episode3)
    
    return all_subtitles

def test_cloud_batch_generation():
    """测试云端批量字幕生成"""
    print("="*60)
    print("测试云端AI引擎批量字幕生成")
    print("="*60)
    
    # 创建测试数据
    all_subtitles = create_test_subtitles()
    print(f"\n测试数据：{len(all_subtitles)}集，每集{len(all_subtitles[0])}条字幕")
    
    # 计算原始总时长
    total_original_duration = sum(
        max(sub["end_time"] for sub in episode) 
        for episode in all_subtitles
    )
    print(f"原始总时长：{total_original_duration:.2f}秒")
    
    # 创建云端AI引擎
    print("\n初始化云端AI引擎...")
    engine = CloudAIEngine()
    engine.configure(CloudPlatform.SILICONFLOW, CloudModel.QWEN3, SILICONFLOW_API_KEY)
    
    # 定义进度回调
    def progress_callback(progress, message):
        print(f"[{progress}%] {message}")
    
    engine.progress_callback = progress_callback
    
    # 测试批量生成
    print("\n开始批量生成爆款字幕...")
    try:
        viral_subtitles = engine.generate_viral_subtitle_batch(all_subtitles, language="zh")
        
        print(f"\n生成结果：")
        print(f"  - 字幕条数：{len(viral_subtitles)}")
        
        if viral_subtitles:
            total_duration = viral_subtitles[-1]["end_time"]
            print(f"  - 总时长：{total_duration:.2f}秒")
            print(f"  - 压缩比：{total_duration/total_original_duration*100:.1f}%")
            
            print(f"\n前5条字幕：")
            for sub in viral_subtitles[:5]:
                print(f"  [{sub['start_time']:.2f}s-{sub['end_time']:.2f}s] {sub['text']}")
            
            print(f"\n后5条字幕：")
            for sub in viral_subtitles[-5:]:
                print(f"  [{sub['start_time']:.2f}s-{sub['end_time']:.2f}s] {sub['text']}")
        
        print("\n✅ 测试成功！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cloud_batch_generation()
