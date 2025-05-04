#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟数据生成器

为用户画像构建系统生成模拟测试数据
"""

import os
import json
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.data.storage_manager import get_storage_manager
from src.utils.log_handler import get_logger

# 配置日志
mock_logger = get_logger("mock_data")

class MockDataGenerator:
    """模拟数据生成器
    
    为用户画像构建系统生成各类模拟数据。
    """
    
    def __init__(self):
        """初始化模拟数据生成器"""
        # 获取存储管理器
        self.storage = get_storage_manager()
        
        # 短剧类型
        self.drama_genres = [
            "都市情感", "古装言情", "悬疑推理", "校园青春", 
            "家庭伦理", "职场励志", "武侠仙侠", "科幻奇幻"
        ]
        
        # 剧情主题
        self.drama_themes = [
            "成长", "爱情", "友情", "亲情", "复仇", "救赎", 
            "冒险", "生存", "智斗", "励志", "悬疑", "社会"
        ]
        
        # 角色类型
        self.character_types = [
            "学生", "职场人", "家长", "恋人", "朋友", "对手", 
            "师徒", "上下级", "陌生人", "亲戚"
        ]
        
        # 情感类型
        self.emotion_types = [
            "喜悦", "悲伤", "愤怒", "恐惧", "厌恶", "惊讶", "中性"
        ]
        
        # 情感曲线类型
        self.emotion_arcs = [
            "上升型", "下降型", "波浪型", "平稳型", "V型", "倒V型"
        ]
        
        # 剪辑转场类型
        self.transition_types = [
            "硬切", "淡入淡出", "交叉叠化", "划像", "推拉", "闪白", "无转场"
        ]
        
        # 叙事结构类型
        self.narrative_structures = [
            "三幕式", "五幕式", "英雄之旅", "双线并行", "多线交织", "倒叙", "闪回"
        ]
        
        # 节奏类型
        self.pacing_types = [
            "快节奏", "中等节奏", "慢节奏", "渐进式", "起伏型"
        ]
        
        mock_logger.info("模拟数据生成器初始化完成")
    
    def generate_user_data(self, user_id: str):
        """生成用户基本数据
        
        Args:
            user_id: 用户ID
        """
        # 生成用户基本信息
        age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
        genders = ["male", "female", "other"]
        regions = ["华东", "华南", "华北", "西南", "西北", "东北", "华中"]
        
        user_data = {
            "user_id": user_id,
            "username": f"用户_{user_id[-4:]}",
            "age_group": random.choice(age_groups),
            "gender": random.choice(genders),
            "region": random.choice(regions),
            "language": "zh",
            "registration_date": (datetime.now() - timedelta(days=random.randint(10, 500))).isoformat()
        }
        
        # 保存用户数据
        user_dir = os.path.join(self.storage.data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "user_data.json"), "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        
        mock_logger.info(f"为用户 {user_id} 生成基本数据")
    
    def generate_device_data(self, user_id: str):
        """生成用户设备数据
        
        Args:
            user_id: 用户ID
        """
        # 生成设备信息
        memory_options = [2048, 4096, 8192, 16384]
        cpu_options = [2, 4, 6, 8, 12]
        gpu_options = [True, False]
        network_options = ["wifi", "mobile", "slow-mobile", "ethernet"]
        storage_options = [10240, 20480, 51200, 102400]
        resolution_options = ["1280x720", "1920x1080", "2560x1440", "3840x2160"]
        
        primary_device = {
            "device_id": str(uuid.uuid4()),
            "device_type": random.choice(["desktop", "laptop", "tablet", "mobile"]),
            "memory_mb": random.choice(memory_options),
            "cpu_cores": random.choice(cpu_options),
            "gpu_available": random.choice(gpu_options),
            "network_type": random.choice(network_options),
            "storage_mb": random.choice(storage_options),
            "screen_resolution": random.choice(resolution_options),
            "last_used": datetime.now().isoformat()
        }
        
        device_data = {
            "user_id": user_id,
            "primary_device": primary_device,
            "other_devices": [],
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存设备数据
        user_dir = os.path.join(self.storage.data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "devices.json"), "w", encoding="utf-8") as f:
            json.dump(device_data, f, ensure_ascii=False, indent=2)
        
        mock_logger.info(f"为用户 {user_id} 生成设备数据")
    
    def generate_view_history(self, user_id: str, count: int = 30):
        """生成观看历史数据
        
        Args:
            user_id: 用户ID
            count: 生成记录数量
        """
        view_history = []
        
        for i in range(count):
            content_id = f"drama_{random.randint(1000, 9999)}"
            
            # 生成内容元数据
            metadata = {
                "title": f"短剧《星辰大海》第{random.randint(1, 24)}集",
                "genre": random.choice(self.drama_genres),
                "themes": random.sample(self.drama_themes, k=random.randint(1, 3)),
                "character_types": random.sample(self.character_types, k=random.randint(1, 3)),
                "duration": random.randint(300, 1800),  # 5-30分钟
                "type": "short_drama"
            }
            
            # 生成观看时间线
            timeline = []
            current_time = 0
            while current_time < metadata["duration"]:
                segment_duration = random.randint(5, 60)
                action = random.choice(["play", "pause", "replay", "skip"])
                
                timeline.append({
                    "timestamp": current_time,
                    "action": action,
                    "duration": segment_duration,
                    "replay_count": random.randint(1, 3) if action == "replay" else 1
                })
                
                current_time += segment_duration
            
            # 生成观看记录
            view_data = {
                "user_id": user_id,
                "content_id": content_id,
                "start_time": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "session_id": str(uuid.uuid4()),
                "metadata": metadata,
                "timeline": timeline,
                "completion_status": random.choice(["completed", "abandoned", "partial"]),
                "view_id": str(uuid.uuid4())
            }
            
            view_history.append(view_data)
        
        # 保存观看历史数据
        user_dir = os.path.join(self.storage.data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "view_history.json"), "w", encoding="utf-8") as f:
            json.dump(view_history, f, ensure_ascii=False, indent=2)
        
        mock_logger.info(f"为用户 {user_id} 生成{count}条观看历史数据")
    
    def generate_mock_content(self, content_type: str = "剧情片段"):
        """生成模拟内容数据
        
        用于测试内容变形器功能
        
        Args:
            content_type: 内容类型描述
            
        Returns:
            Dict: 模拟内容数据
        """
        content_id = f"content_{random.randint(10000, 99999)}"
        
        # 根据内容类型调整生成参数
        if "爱情" in content_type or "情感" in content_type:
            primary_emotions = ["喜悦", "悲伤"]
            primary_themes = ["爱情", "成长", "亲情"]
        elif "悬疑" in content_type or "推理" in content_type:
            primary_emotions = ["紧张", "惊讶", "恐惧"]
            primary_themes = ["悬疑", "复仇", "智斗"]
        elif "动作" in content_type or "冒险" in content_type:
            primary_emotions = ["紧张", "惊讶", "喜悦"]
            primary_themes = ["冒险", "智斗", "生存"]
        else:
            primary_emotions = self.emotion_types
            primary_themes = self.drama_themes
        
        # 生成标题和描述
        title = f"《{random.choice(['星辰', '流光', '追梦', '逐风', '暗夜', '晨曦'])}{random.choice(['之旅', '传说', '故事', '探险', '秘闻'])}》"
        description = f"一段关于{random.choice(primary_themes)}的{content_type}，{random.choice(['令人深思', '扣人心弦', '感人至深', '引人入胜'])}"
        
        # 生成场景数据
        scene_count = random.randint(3, 7)
        scenes = []
        current_time = 0.0
        
        for i in range(scene_count):
            # 场景持续时间，3-15秒
            scene_duration = random.uniform(3.0, 15.0)
            scene_duration = round(scene_duration, 1)
            
            # 场景情感
            emotion_type = random.choice(primary_emotions)
            emotion_intensity = random.uniform(0.3, 0.8)
            emotion_intensity = round(emotion_intensity, 2)
            emotion_score = random.uniform(emotion_intensity - 0.1, emotion_intensity + 0.2)
            emotion_score = round(min(1.0, emotion_score), 2)
            
            scene = {
                "id": f"scene_{i+1}",
                "start": current_time,
                "end": current_time + scene_duration,
                "duration": scene_duration,
                "emotion": {
                    "type": emotion_type,
                    "intensity": emotion_intensity,
                    "score": emotion_score
                }
            }
            
            scenes.append(scene)
            current_time += scene_duration
        
        # 生成整体情感数据
        emotions = []
        for emotion_type in random.sample(primary_emotions, min(3, len(primary_emotions))):
            emotion_intensity = random.uniform(0.3, 0.8)
            emotion_intensity = round(emotion_intensity, 2)
            emotion_score = random.uniform(emotion_intensity - 0.1, emotion_intensity + 0.2)
            emotion_score = round(min(1.0, emotion_score), 2)
            
            emotions.append({
                "type": emotion_type,
                "intensity": emotion_intensity,
                "score": emotion_score
            })
        
        # 生成对话数据
        dialogue_samples = [
            "你觉得人生的意义是什么？",
            "有些事情，只能靠自己去面对。",
            "我们已经走了这么远，不能放弃。",
            "无论发生什么，我都会在你身边。",
            "有时候，放手也是一种勇气。",
            "我不后悔认识你，即使结局是这样。",
            "真相往往比我们想象的更复杂。",
            "春节快到了，我们要准备红包。",
            "这次考试真难，我要好好复习。",
            "你看窗外的风景，多美啊。"
        ]
        
        dialogues = []
        for i in range(min(4, scene_count)):
            scene = scenes[i]
            start_time = scene["start"] + random.uniform(0.5, 1.5)
            end_time = min(scene["end"] - 0.5, start_time + 3.0)
            
            dialogues.append({
                "id": f"dialogue_{i+1}",
                "text": random.choice(dialogue_samples),
                "start": round(start_time, 1),
                "end": round(end_time, 1)
            })
        
        # 生成旁白数据
        narration_samples = [
            "时间如同流水，带走了太多回忆。",
            "在这座城市里，每个人都有自己的故事。",
            "命运有时就是这样奇妙，让两个人在最美的时刻相遇。",
            "有些选择，一旦做出，就再也无法回头。",
            "这是一个关于勇气与坚持的故事。",
            "黎明前的黑暗，总是最为漫长。"
        ]
        
        narrations = []
        for i in range(min(2, scene_count)):
            scene = scenes[i]
            start_time = scene["start"] + random.uniform(0.5, 1.0)
            end_time = min(scene["end"] - 0.5, start_time + 3.0)
            
            narrations.append({
                "id": f"narration_{i+1}",
                "text": random.choice(narration_samples),
                "start": round(start_time, 1),
                "end": round(end_time, 1)
            })
        
        # 组装内容数据
        content = {
            "id": content_id,
            "title": title,
            "description": description,
            "type": content_type,
            "duration": scenes[-1]["end"],
            "scenes": scenes,
            "emotions": emotions,
            "dialogues": dialogues,
            "narration": narrations,
            "themes": random.sample(primary_themes, min(3, len(primary_themes))),
            "created_at": datetime.now().isoformat()
        }
        
        return content
    
    def generate_biometric_data(self, user_id: str, count: int = 20):
        """生成生物特征数据
        
        Args:
            user_id: 用户ID
            count: 生成记录数量
        """
        bio_data = []
        
        for i in range(count):
            content_id = f"drama_{random.randint(1000, 9999)}"
            start_time = datetime.now() - timedelta(days=random.randint(1, 30))
            
            # 生成心率数据
            heart_rates = []
            for j in range(random.randint(10, 60)):
                timestamp = start_time + timedelta(seconds=j*10)
                heart_rates.append({
                    "timestamp": timestamp.isoformat(),
                    "value": random.randint(60, 120)
                })
            
            # 生成情绪估计
            emotions = []
            for j in range(random.randint(5, 15)):
                timestamp = start_time + timedelta(seconds=j*20)
                emotion_type = random.choice(self.emotion_types)
                emotions.append({
                    "timestamp": timestamp.isoformat(),
                    "type": emotion_type,
                    "intensity": round(random.uniform(0.1, 1.0), 2)
                })
            
            # 生成观看专注度
            focus_data = []
            for j in range(random.randint(5, 30)):
                timestamp = start_time + timedelta(seconds=j*15)
                focus_data.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(random.uniform(0.0, 1.0), 2)
                })
            
            # 组合生物特征数据
            data_point = {
                "user_id": user_id,
                "content_id": content_id,
                "session_id": str(uuid.uuid4()),
                "start_time": start_time.isoformat(),
                "heart_rate": heart_rates,
                "emotions": emotions,
                "focus": focus_data,
                "bio_id": str(uuid.uuid4())
            }
            
            bio_data.append(data_point)
        
        # 保存生物特征数据
        user_dir = os.path.join(self.storage.data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "biometric_data.json"), "w", encoding="utf-8") as f:
            json.dump(bio_data, f, ensure_ascii=False, indent=2)
        
        mock_logger.info(f"为用户 {user_id} 生成{count}条生物特征数据")
    
    def generate_behavior_data(self, user_id: str):
        """生成行为数据
        
        Args:
            user_id: 用户ID
        """
        # 行为事件类型
        event_types = ["view", "like", "share", "comment", "save", "replay", "skip", "search", "click"]
        
        # 生成行为数据
        behavior_data = []
        for i in range(100):  # 生成100条行为数据
            content_id = f"drama_{random.randint(1000, 9999)}"
            event_type = random.choice(event_types)
            
            event_data = {
                "user_id": user_id,
                "event_type": event_type,
                "content_id": content_id,
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30), 
                                                        hours=random.randint(0, 23), 
                                                        minutes=random.randint(0, 59))).isoformat(),
                "device_id": str(uuid.uuid4()),
                "event_id": str(uuid.uuid4())
            }
            
            # 添加事件特定数据
            if event_type == "view":
                event_data["view_duration"] = random.randint(10, 1800)  # 10秒到30分钟
                event_data["completion_rate"] = round(random.uniform(0.0, 1.0), 2)
            elif event_type == "like":
                event_data["like_strength"] = random.choice(["light", "medium", "strong"])
            elif event_type == "share":
                event_data["share_platform"] = random.choice(["wechat", "weibo", "qq", "tiktok"])
            elif event_type == "comment":
                event_data["comment_length"] = random.randint(5, 200)
                event_data["comment_sentiment"] = random.choice(["positive", "neutral", "negative"])
            elif event_type == "replay":
                event_data["replay_count"] = random.randint(1, 5)
                event_data["replay_sections"] = [
                    {"start": random.randint(0, 300), "end": random.randint(301, 600)}
                    for _ in range(random.randint(1, 3))
                ]
            elif event_type == "skip":
                event_data["skip_sections"] = [
                    {"start": random.randint(0, 300), "end": random.randint(301, 600)}
                    for _ in range(random.randint(1, 3))
                ]
            
            behavior_data.append(event_data)
        
        # 保存行为数据
        user_dir = os.path.join(self.storage.data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "behavior_data.json"), "w", encoding="utf-8") as f:
            json.dump(behavior_data, f, ensure_ascii=False, indent=2)
        
        mock_logger.info(f"为用户 {user_id} 生成行为数据")
    
    def generate_temporal_data(self, user_id: str):
        """生成时间模式数据
        
        Args:
            user_id: 用户ID
        """
        # 生成每日观看时间分布
        daily_distribution = {}
        for hour in range(24):
            daily_distribution[str(hour)] = round(random.uniform(0.0, 1.0), 2)
        
        # 标准化每日分布
        total = sum(daily_distribution.values())
        for hour in daily_distribution:
            daily_distribution[hour] = round(daily_distribution[hour] / total, 2)
        
        # 生成每周观看时间分布
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_distribution = {}
        for day in weekday_names:
            weekly_distribution[day] = round(random.uniform(0.0, 1.0), 2)
        
        # 标准化每周分布
        total = sum(weekly_distribution.values())
        for day in weekly_distribution:
            weekly_distribution[day] = round(weekly_distribution[day] / total, 2)
        
        # 生成会话持续时间分布
        session_durations = {
            "short": round(random.uniform(0.0, 0.3), 2),     # <15分钟
            "medium": round(random.uniform(0.0, 0.5), 2),    # 15-30分钟
            "long": round(random.uniform(0.0, 0.2), 2)       # >30分钟
        }
        
        # 标准化会话持续时间分布
        total = sum(session_durations.values())
        for duration in session_durations:
            session_durations[duration] = round(session_durations[duration] / total, 2)
        
        # 组合时间模式数据
        temporal_data = {
            "user_id": user_id,
            "daily_pattern": daily_distribution,
            "weekly_pattern": weekly_distribution,
            "session_durations": session_durations,
            "peak_hours": sorted([int(h) for h, v in daily_distribution.items() 
                                if v > 0.08]),  # 高峰时段
            "prime_time": max(daily_distribution.items(), key=lambda x: x[1])[0],  # 黄金时段
            "weekend_ratio": round(
                (weekly_distribution["Saturday"] + weekly_distribution["Sunday"]) / 
                sum(v for k, v in weekly_distribution.items() if k not in ["Saturday", "Sunday"]), 
                2),  # 周末/工作日比例
            "updated_at": datetime.now().isoformat()
        }
        
        # 保存时间模式数据
        user_dir = os.path.join(self.storage.data_dir, "users", user_id)
        os.makedirs(user_dir, exist_ok=True)
        with open(os.path.join(user_dir, "temporal_patterns.json"), "w", encoding="utf-8") as f:
            json.dump(temporal_data, f, ensure_ascii=False, indent=2)
        
        mock_logger.info(f"为用户 {user_id} 生成时间模式数据")
    
    def generate_all_data(self, user_id: str):
        """为用户生成所有类型的模拟数据
        
        Args:
            user_id: 用户ID
        """
        self.generate_user_data(user_id)
        self.generate_device_data(user_id)
        self.generate_view_history(user_id)
        self.generate_biometric_data(user_id)
        self.generate_behavior_data(user_id)
        self.generate_temporal_data(user_id)
        
        mock_logger.info(f"为用户 {user_id} 生成所有类型的模拟数据完成")


# 模块级函数
_mock_data_generator = None

def get_mock_data_generator():
    """获取模拟数据生成器实例"""
    global _mock_data_generator
    if _mock_data_generator is None:
        _mock_data_generator = MockDataGenerator()
    return _mock_data_generator

def generate_mock_behavior_data(user_id: str):
    """生成模拟行为数据"""
    generator = get_mock_data_generator()
    generator.generate_behavior_data(user_id)

def generate_mock_content(content_type: str = "剧情片段"):
    """生成模拟内容数据"""
    generator = get_mock_data_generator()
    return generator.generate_mock_content(content_type)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python mock_data_generator.py <user_id> [count]")
        return
    
    user_id = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    generator = MockDataGenerator()
    for i in range(count):
        if count > 1:
            current_user_id = f"{user_id}_{i+1}"
        else:
            current_user_id = user_id
        
        generator.generate_all_data(current_user_id)
    
    print(f"成功为 {count} 个用户生成模拟数据")


if __name__ == "__main__":
    main() 