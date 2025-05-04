#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
人工评估接口演示

演示如何使用人工评估接口收集和分析用户对视频质量的评价
"""

import os
import sys
import time
from pprint import pprint

# 添加src到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 确保目录存在
os.makedirs("data/human_ratings", exist_ok=True)
os.makedirs("data/evaluation_campaigns", exist_ok=True)

# 导入人工评估模块
from src.quality.human_eval import CrowdRatingSystem, EvaluationCampaign, HumanEvaluator

def demo_basic_rating():
    """基本评分演示"""
    print("\n=== 基本评分演示 ===")
    
    # 创建评分系统
    rating_system = CrowdRatingSystem()
    
    # 模拟的视频ID
    video_id = "video_12345"
    
    # 模拟收集评分
    print("模拟收集人工评分...")
    ratings = rating_system.collect_ratings(video_id)
    print(f"评分结果: {ratings}")
    
    # 提交评分
    user_id = "user_test123"
    rating_id = rating_system.submit_rating(video_id, ratings, user_id)
    print(f"已提交评分，ID: {rating_id}")
    
    # 查看评分
    saved_ratings = rating_system.get_ratings(video_id)
    print(f"已保存 {len(saved_ratings)} 条评分")
    
    # 计算平均评分
    avg_ratings = rating_system.calculate_average_ratings(video_id)
    print("平均评分:")
    pprint(avg_ratings)

def demo_evaluation_campaign():
    """评估活动演示"""
    print("\n=== 评估活动演示 ===")
    
    # 创建评估活动
    campaign = EvaluationCampaign(name="示例视频评估活动")
    print(f"创建评估活动: {campaign.name} (ID: {campaign.campaign_id})")
    
    # 添加视频
    videos = ["video_001", "video_002", "video_003"]
    for i, video_id in enumerate(videos):
        campaign.add_video(video_id, {"title": f"测试视频 {i+1}", "duration": 60 + i*30})
    
    print(f"已添加 {len(campaign.video_ids)} 个视频到评估活动")
    
    # 添加参与者
    participants = ["user_001", "user_002", "user_003"]
    for user_id in participants:
        campaign.add_participant(user_id)
    
    print(f"已添加 {len(campaign.participants)} 名参与者")
    
    # 启动活动
    campaign.start_campaign()
    print(f"活动状态: {campaign.status}")
    
    # 模拟提交评分
    rating_system = campaign.rating_system
    
    for video_id in videos:
        for user_id in participants:
            # 不是所有用户都评价所有视频，模拟真实情况
            if video_id != "video_003" or user_id != "user_003":  # 最后一个用户没有评价最后一个视频
                ratings = rating_system.collect_ratings(video_id)
                rating_id = rating_system.submit_rating(video_id, ratings, user_id)
                print(f"用户 {user_id} 对视频 {video_id} 提交评分: {rating_id}")
                
                # 更新活动参与者状态
                if user_id in campaign.participants:
                    if video_id not in campaign.participants[user_id].get("completed_videos", []):
                        campaign.participants[user_id].setdefault("completed_videos", []).append(video_id)
    
    # 保存活动状态
    campaign.save()
    
    # 获取活动摘要
    print("\n活动评估摘要:")
    summary = campaign.get_summary()
    print(f"活动: {summary['name']} (ID: {summary['campaign_id']})")
    print(f"状态: {summary['status']}")
    print(f"视频数量: {summary['video_count']}")
    print(f"评分总数: {summary['total_ratings']}")
    print(f"总体平均分: {summary['overall_average']:.2f}")
    
    # 完成活动
    campaign.complete_campaign()
    print(f"活动状态: {campaign.status}")

def demo_human_evaluator():
    """人工评估器演示"""
    print("\n=== 人工评估器演示 ===")
    
    # 创建评估器
    evaluator = HumanEvaluator()
    
    # 创建新活动
    campaign = evaluator.create_campaign("全面性能评估")
    print(f"已创建新活动: {campaign.name} (ID: {campaign.campaign_id})")
    
    # 添加视频
    test_videos = ["performance_video_1", "performance_video_2"]
    for video_id in test_videos:
        campaign.add_video(video_id)
    
    # 启动活动
    campaign.start_campaign()
    
    # 模拟用户提交评分
    test_users = ["tester_1", "tester_2", "tester_3"]
    
    for user_id in test_users:
        campaign.add_participant(user_id)
        
        for video_id in test_videos:
            # 模拟不同用户的不同评分偏好
            if user_id == "tester_1":
                # 严格评分者
                ratings = {
                    "clarity": 3.8,
                    "engagement": 3.5,
                    "artistry": 3.2,
                    "coherence": 3.9,
                    "relevance": 4.0
                }
            elif user_id == "tester_2":
                # 中立评分者
                ratings = {
                    "clarity": 4.2,
                    "engagement": 4.0,
                    "artistry": 3.9,
                    "coherence": 4.1,
                    "relevance": 4.3
                }
            else:
                # 宽松评分者
                ratings = {
                    "clarity": 4.8,
                    "engagement": 4.5,
                    "artistry": 4.7,
                    "coherence": 4.6,
                    "relevance": 4.9
                }
            
            # 提交评分
            evaluator.submit_rating(
                video_id=video_id,
                user_id=user_id,
                ratings=ratings,
                campaign_id=campaign.campaign_id,
                comments=f"{user_id}的评价: 这是一个测试评价"
            )
    
    # 完成活动
    campaign.complete_campaign()
    
    # 获取评估报告
    report = evaluator.get_evaluation_report(campaign_id=campaign.campaign_id)
    
    print("\n评估报告:")
    print(f"活动: {report['name']} (ID: {report['campaign_id']})")
    print(f"状态: {report['status']}")
    print(f"视频数量: {report['video_count']}")
    print(f"评分总数: {report['total_ratings']}")
    print(f"总体平均分: {report['overall_average']:.2f}")
    
    # 显示每个视频的评分
    print("\n各视频评分:")
    for video_id, summary in report["video_summaries"].items():
        print(f"- 视频 {video_id}:")
        print(f"  评分数量: {summary['ratings_count']}")
        if 'average_ratings' in summary and summary['average_ratings']:
            for criterion, score in summary['average_ratings'].items():
                if criterion != 'overall':
                    print(f"  {criterion}: {score:.2f}")
            if 'overall' in summary['average_ratings']:
                print(f"  总体: {summary['average_ratings']['overall']:.2f}")
    
    print("\n演示完成")

def main():
    """主函数"""
    print("开始人工评估接口演示")
    
    # 运行基本评分演示
    demo_basic_rating()
    
    # 运行评估活动演示
    demo_evaluation_campaign()
    
    # 运行人工评估器演示
    demo_human_evaluator()
    
    print("\n人工评估接口演示结束")

if __name__ == "__main__":
    main() 