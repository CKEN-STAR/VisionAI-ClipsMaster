#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
跨平台习惯融合独立演示脚本

这是一个独立的演示脚本，展示跨平台习惯融合模块的核心功能，
不依赖于其他模块，方便快速测试和演示。
"""

import copy
import time
from datetime import datetime
from typing import Dict, Any

def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def print_platform_data(title, data):
    """打印平台数据摘要"""
    print(f"\n--- {title} ---")
    if not data:
        print("  无可用数据")
        return
    
    # 打印分类偏好
    if "category_preferences" in data:
        print("\n分类偏好:")
        for category, pref in data["category_preferences"].items():
            print(f"  {category}: 分数 {pref.get('score', 0):.2f}")
    
    # 打印内容格式偏好
    if "content_format_preference" in data:
        print("\n内容格式偏好:")
        for format_type, score in data["content_format_preference"].items():
            print(f"  {format_type}: {score:.2f}")
    
    # 打印观看时长
    if "watch_duration" in data:
        duration = data["watch_duration"]
        if "average" in duration:
            print(f"\n平均观看时长: {duration['average']:.1f} {duration.get('unit', 'seconds')}")
    
    # 打印活跃时段
    if "active_time_slots" in data:
        print("\n活跃时段:")
        for slot in data["active_time_slots"]:
            print(f"  {slot}")

def print_unified_preference(pref):
    """打印统一偏好摘要"""
    print("\n--- 统一偏好表达 ---")
    if not pref:
        print("  无可用数据")
        return
    
    # 打印分类偏好
    if "category_preferences" in pref:
        print("\n跨平台分类偏好:")
        for category, data in pref["category_preferences"].items():
            platforms = ', '.join(data.get("platforms", []))
            print(f"  {category}: 分数 {data.get('score', 0):.2f} (来源: {platforms})")
    
    # 打印内容格式偏好
    if "format_preferences" in pref:
        print("\n跨平台内容格式偏好:")
        for format_type, data in pref["format_preferences"].items():
            platforms = ', '.join(data.get("platforms", []))
            print(f"  {format_type}: 分数 {data.get('score', 0):.2f} (来源: {platforms})")
    
    # 打印观看时长
    if "watch_duration" in pref:
        duration = pref["watch_duration"]
        if "average" in duration:
            print(f"\n跨平台平均观看时长: {duration['average']:.1f} {duration.get('unit', 'seconds')}")
    
    # 打印活跃时段
    if "active_time_slots" in pref:
        print("\n跨平台活跃时段:")
        for slot in pref["active_time_slots"]:
            print(f"  {slot}")
    
    # 打印平台覆盖
    if "platform_coverage" in pref:
        print("\n平台数据覆盖:")
        for platform, has_data in pref["platform_coverage"].items():
            print(f"  {platform}: {'✓' if has_data else '✗'}")

class SimpleCrossPlatformIntegrator:
    """简化版跨平台习惯融合器"""
    
    def __init__(self):
        """初始化跨平台整合器简化版"""
        # 平台权重
        self.platform_weights = {
            "douyin": 1.0,
            "bilibili": 0.9,
            "youtube": 0.8
        }
    
    def integrate_habits(self, user_id: str) -> Dict[str, Any]:
        """整合用户在多平台上的习惯与偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 整合后的跨平台习惯数据
        """
        print(f"开始整合用户 {user_id} 的跨平台习惯")
        
        # 获取各平台数据（这里用模拟数据）
        douyin_data = self.get_douyin_habits(user_id)
        bilibili_data = self.get_bilibili_habits(user_id)
        youtube_data = self.get_youtube_habits(user_id)
        
        # 计算统一偏好表达
        unified_preference = self.calculate_unified_preference({
            "douyin": douyin_data,
            "bilibili": bilibili_data,
            "youtube": youtube_data
        })
        
        # 整合结果
        result = {
            "抖音": douyin_data,
            "B站": bilibili_data,
            "油管": youtube_data,
            "融合策略": unified_preference
        }
        
        return result
    
    def get_douyin_habits(self, user_id: str) -> Dict[str, Any]:
        """获取用户抖音平台习惯数据（模拟）"""
        # 模拟数据
        return {
            "favorite_categories": ["搞笑", "生活", "美食"],
            "content_format_preference": {
                "短视频": 0.8,
                "直播": 0.2
            },
            "watch_duration": {
                "average": 35.6,
                "unit": "seconds"
            },
            "active_time_slots": ["18:00-22:00", "12:00-13:00"],
            "category_preferences": {
                "搞笑": {"score": 0.8, "strength": "strong_like"},
                "生活": {"score": 0.7, "strength": "like"},
                "美食": {"score": 0.9, "strength": "strong_like"}
            }
        }
    
    def get_bilibili_habits(self, user_id: str) -> Dict[str, Any]:
        """获取用户B站平台习惯数据（模拟）"""
        # 模拟数据
        return {
            "favorite_partitions": ["动画", "游戏", "科技"],
            "content_format_preference": {
                "视频": 0.6,
                "直播": 0.3,
                "番剧": 0.1
            },
            "watch_duration": {
                "average": 420.5,
                "unit": "seconds"
            },
            "active_time_slots": ["19:00-23:00", "13:00-15:00"],
            "category_preferences": {
                "动画": {"score": 0.8, "strength": "strong_like"},
                "游戏": {"score": 0.9, "strength": "strong_like"},
                "科技": {"score": 0.7, "strength": "like"}
            }
        }
    
    def get_youtube_habits(self, user_id: str) -> Dict[str, Any]:
        """获取用户YouTube平台习惯数据（模拟）"""
        # 模拟数据
        return {
            "subscribed_categories": ["Entertainment", "Technology", "Music"],
            "content_format_preference": {
                "视频": 0.7,
                "短视频": 0.2,
                "直播": 0.1
            },
            "watch_duration": {
                "average": 540.2,
                "unit": "seconds"
            },
            "active_time_slots": ["20:00-24:00", "7:00-9:00"],
            "category_preferences": {
                "Entertainment": {"score": 0.7, "strength": "like"},
                "Technology": {"score": 0.8, "strength": "strong_like"},
                "Music": {"score": 0.6, "strength": "like"}
            }
        }
    
    def calculate_unified_preference(self, platform_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """计算统一的偏好表达
        
        将来自不同平台的偏好数据融合为一个统一的偏好表达
        
        Args:
            platform_data: 各平台数据字典
            
        Returns:
            Dict[str, Any]: 统一的偏好表达
        """
        # 提取各平台的分类偏好
        category_preferences = {}
        for platform, data in platform_data.items():
            platform_weight = self.platform_weights.get(platform, 0.5)
            
            # 提取该平台的分类偏好
            platform_categories = data.get("category_preferences", {})
            
            # 合并到统一偏好中
            for category, pref_data in platform_categories.items():
                score = pref_data.get("score", 0.5) * platform_weight
                
                if category not in category_preferences:
                    category_preferences[category] = {
                        "score": score,
                        "platforms": [platform]
                    }
                else:
                    category_preferences[category]["score"] = (
                        category_preferences[category]["score"] + score
                    ) / 2  # 取平均值
                    category_preferences[category]["platforms"].append(platform)
        
        # 计算内容格式偏好
        format_preferences = {}
        for platform, data in platform_data.items():
            platform_weight = self.platform_weights.get(platform, 0.5)
            
            # 提取该平台的内容格式偏好
            platform_formats = data.get("content_format_preference", {})
            
            # 合并到统一偏好中
            for format_type, score in platform_formats.items():
                weighted_score = score * platform_weight
                
                if format_type not in format_preferences:
                    format_preferences[format_type] = {
                        "score": weighted_score,
                        "platforms": [platform]
                    }
                else:
                    format_preferences[format_type]["score"] = (
                        format_preferences[format_type]["score"] + weighted_score
                    ) / 2  # 取平均值
                    format_preferences[format_type]["platforms"].append(platform)
        
        # 计算活跃时段偏好
        time_slots = []
        for platform, data in platform_data.items():
            platform_slots = data.get("active_time_slots", [])
            time_slots.extend(platform_slots)
        
        # 提取观看时长偏好
        watch_durations = {}
        for platform, data in platform_data.items():
            if "watch_duration" in data and "average" in data["watch_duration"]:
                watch_durations[platform] = data["watch_duration"]["average"]
        
        avg_watch_duration = sum(watch_durations.values()) / len(watch_durations) if watch_durations else 0
        
        # 组装统一偏好表达
        unified_preference = {
            "category_preferences": category_preferences,
            "format_preferences": format_preferences,
            "active_time_slots": list(set(time_slots)),  # 去重
            "watch_duration": {
                "average": avg_watch_duration,
                "unit": "seconds"
            },
            "platform_coverage": {
                "douyin": "douyin" in platform_data and bool(platform_data["douyin"]),
                "bilibili": "bilibili" in platform_data and bool(platform_data["bilibili"]),
                "youtube": "youtube" in platform_data and bool(platform_data["youtube"])
            },
            "updated_at": datetime.now().isoformat()
        }
        
        return unified_preference
    
    def get_unified_preference(self, user_id: str) -> Dict[str, Any]:
        """获取用户的统一偏好表达"""
        integrated_data = self.integrate_habits(user_id)
        if "融合策略" in integrated_data:
            return integrated_data["融合策略"]
        return {}
    
    def get_platform_habit(self, user_id: str, platform: str) -> Dict[str, Any]:
        """获取特定平台的习惯数据"""
        if platform == "douyin":
            return self.get_douyin_habits(user_id)
        elif platform == "bilibili":
            return self.get_bilibili_habits(user_id)
        elif platform == "youtube":
            return self.get_youtube_habits(user_id)
        else:
            print(f"不支持的平台: {platform}")
            return {}

def demonstrate_cross_platform_integration():
    """演示跨平台习惯融合功能"""
    test_user_id = "demo_user_123"
    
    print_section("跨平台习惯融合演示")
    print(f"用户ID: {test_user_id}")
    
    # 创建简化版整合器
    integrator = SimpleCrossPlatformIntegrator()
    
    # 获取各平台数据
    print("\n获取各平台习惯数据...")
    douyin_data = integrator.get_platform_habit(test_user_id, "douyin")
    bilibili_data = integrator.get_platform_habit(test_user_id, "bilibili")
    youtube_data = integrator.get_platform_habit(test_user_id, "youtube")
    
    # 打印各平台数据摘要
    print_platform_data("抖音平台数据", douyin_data)
    print_platform_data("B站平台数据", bilibili_data)
    print_platform_data("YouTube平台数据", youtube_data)
    
    # 整合跨平台习惯
    print("\n开始整合跨平台习惯数据...")
    integrated_data = integrator.integrate_habits(test_user_id)
    
    # 获取统一偏好表达
    print("\n获取统一偏好表达...")
    unified_pref = integrated_data["融合策略"]
    
    # 打印统一偏好摘要
    print_unified_preference(unified_pref)
    
    print("\n演示完成！")

if __name__ == "__main__":
    try:
        demonstrate_cross_platform_integration()
    except Exception as e:
        print(f"演示过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 