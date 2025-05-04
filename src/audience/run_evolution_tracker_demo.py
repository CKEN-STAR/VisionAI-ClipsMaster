#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
偏好进化追踪器简化演示脚本

提供一个简单的命令行界面来演示偏好进化追踪器的功能。
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pprint import pprint

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("启动偏好进化追踪器简化演示...")

# 创建必要的模拟对象
class MockClass:
    def __init__(self, *args, **kwargs):
        pass
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

class MockLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")

class MockStorageManager:
    def get_preference_history(self, user_id, days=90):
        print(f"[MOCK] 获取用户 {user_id} 过去 {days} 天的偏好历史")
        # 创建模拟历史数据
        history = []
        for i in range(days, 0, -5):  # 每5天一个数据点
            # 生成日期
            date = datetime.now() - timedelta(days=i)
            
            # 创建偏好数据
            preferences = {
                "genre": {
                    "favorites": ["动作", "科幻"],
                    "strength_map": {
                        "动作": {"ratio": 0.5 + (i % 30) * 0.01},
                        "科幻": {"ratio": 0.3 + (i % 20) * 0.005}
                    }
                },
                "pace": {
                    "preferred_pace": "fast" if i % 25 < 10 else "moderate",
                    "engagement_by_pace": {
                        "fast": {"completion_rate": 0.7 - (i % 15) * 0.01},
                        "moderate": {"completion_rate": 0.5 + (i % 10) * 0.02}
                    }
                }
            }
            
            # 添加到历史
            history.append({
                "timestamp": date.isoformat(),
                "preferences": preferences
            })
        return history
    
    def save_preference_evolution(self, user_id, data):
        print(f"[MOCK] 保存用户 {user_id} 的偏好演变记录")
        return True
    
    def get_user_profile(self, user_id):
        print(f"[MOCK] 获取用户 {user_id} 的用户画像")
        # 创建模拟用户画像
        return {
            "user_id": user_id,
            "created_at": (datetime.now() - timedelta(days=90)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "behavior_patterns": {
                "genre_preferences": {
                    "动作": 45,
                    "科幻": 30,
                    "冒险": 15,
                    "喜剧": 10
                },
                "pace_preferences": {
                    "fast": {"completion_rate": 0.85, "view_count": 38},
                    "moderate": {"completion_rate": 0.72, "view_count": 55},
                    "slow": {"completion_rate": 0.45, "view_count": 12}
                },
                "emotional_preferences": {
                    "喜悦": 40,
                    "震撼": 25,
                    "悬疑": 20,
                    "紧张": 15
                }
            },
            "view_heatmap": {
                "favorite_timestamps": [10, 14, 18, 21],
                "weekday_pattern": [0.1, 0.15, 0.1, 0.15, 0.2, 0.3, 0.0],
                "skipped_sections": []
            }
        }

class MockPreferenceAnalyzer:
    def analyze_user_preferences(self, user_id):
        print(f"[MOCK] 分析用户 {user_id} 的偏好")
        return {
            "status": "success",
            "user_id": user_id,
            "genre": {
                "favorites": ["动作", "科幻", "冒险"],
                "strength_map": {
                    "动作": {"ratio": 0.45, "strength": "strong", "view_count": 45},
                    "科幻": {"ratio": 0.30, "strength": "moderate", "view_count": 30},
                    "冒险": {"ratio": 0.15, "strength": "slight", "view_count": 15},
                    "喜剧": {"ratio": 0.10, "strength": "slight", "view_count": 10}
                },
                "confidence": 0.85
            },
            "pace": {
                "preferred_pace": "moderate",
                "engagement_by_pace": {
                    "fast": {"completion_rate": 0.85, "view_count": 38},
                    "moderate": {"completion_rate": 0.72, "view_count": 55},
                    "slow": {"completion_rate": 0.45, "view_count": 12}
                },
                "confidence": 0.9
            },
            "emotional": {
                "preferred_emotions": ["喜悦", "震撼"],
                "strength_map": {
                    "喜悦": {"ratio": 0.4, "strength": "strong", "count": 40},
                    "震撼": {"ratio": 0.25, "strength": "moderate", "count": 25},
                    "悬疑": {"ratio": 0.2, "strength": "slight", "count": 20},
                    "紧张": {"ratio": 0.15, "strength": "slight", "count": 15}
                },
                "confidence": 0.8
            },
            "analyzed_at": datetime.now().isoformat()
        }

# 模拟日志记录器
sys.modules['src.utils.log_handler'] = MockClass()
sys.modules['src.utils.log_handler'].get_logger = lambda name: MockLogger()

# 模拟存储管理器
sys.modules['src.data.storage_manager'] = MockClass()
sys.modules['src.data.storage_manager'].get_storage_manager = lambda: MockStorageManager()

# 模拟画像引擎
sys.modules['src.audience.profile_builder'] = MockClass()
sys.modules['src.audience.profile_builder'].get_user_profile = lambda user_id: MockStorageManager().get_user_profile(user_id)
sys.modules['src.audience.profile_builder'].get_profile_engine = lambda: MockClass()

# 模拟偏好分析器
sys.modules['src.audience.preference_analyzer'] = MockClass()
sys.modules['src.audience.preference_analyzer'].PreferenceAnalyzer = MockPreferenceAnalyzer

# 模拟其他包
for module_name in [
    'src.utils.privacy_manager',
    'src.core.privacy_manager',
    'src.nlp.text_processor'
]:
    if module_name not in sys.modules:
        sys.modules[module_name] = MockClass()

# 直接导入模块
try:
    from src.audience.evolution_tracker import (
        PreferenceEvolution, 
        detect_preference_shift,
        track_preference_changes,
        get_preference_evolution_summary
    )
    module_imported = True
    print("成功导入偏好进化追踪器模块")
except ImportError as e:
    print(f"导入偏好进化追踪器模块失败: {str(e)}")
    module_imported = False
    
    # 创建模拟版本的演示功能
    class MockEvolutionTracker:
        def __init__(self):
            # 模拟追踪维度
            self.tracked_dimensions = [
                "genre", "narrative", "pace", "visuals", 
                "audio", "complexity", "emotional", "themes"
            ]
            self.db = MockStorageManager()
            self.analyzer = MockPreferenceAnalyzer()
        
        def detect_shift(self, user_id):
            # 获取模拟历史数据
            history = self.db.get_preference_history(user_id)
            
            return {
                "current_trend": {
                    "status": "success",
                    "dimension_trends": {
                        "genre": {"direction": "increasing", "magnitude": 0.3, "correlation": 0.75, "confidence": 0.8},
                        "pace": {"direction": "stable", "magnitude": 0.05, "correlation": 0.1, "confidence": 0.6},
                        "complexity": {"direction": "decreasing", "magnitude": 0.2, "correlation": 0.7, "confidence": 0.7}
                    },
                    "significant_shifts": [
                        {"dimension": "genre", "direction": "increasing", "magnitude": 0.3, "confidence": 0.8},
                        {"dimension": "complexity", "direction": "decreasing", "magnitude": 0.2, "confidence": 0.7}
                    ],
                    "overall_stability": 0.6
                },
                "predicted_shift": {
                    "status": "success",
                    "forecast_window": "30 days",
                    "dimension_forecasts": {
                        "genre": {"current_value": 0.5, "predicted_value": 0.7, "change_direction": "increasing", "confidence": 0.8},
                        "pace": {"current_value": 0.6, "predicted_value": 0.65, "change_direction": "stable", "confidence": 0.6},
                        "complexity": {"current_value": 0.7, "predicted_value": 0.5, "change_direction": "decreasing", "confidence": 0.7}
                    },
                    "potential_shifts": [
                        {"dimension": "genre", "current_value": 0.5, "predicted_value": 0.7, 
                         "change_percentage": 40.0, "direction": "increasing", "confidence": 0.75},
                        {"dimension": "complexity", "current_value": 0.7, "predicted_value": 0.5, 
                         "change_percentage": 28.6, "direction": "decreasing", "confidence": 0.65}
                    ]
                }
            }
        
        def track_preference_evolution(self, user_id):
            # 分析当前偏好
            current_preferences = self.analyzer.analyze_user_preferences(user_id)
            
            # 检测偏好迁移
            shifts = self.detect_shift(user_id)
            
            # 保存偏好演变记录
            self.db.save_preference_evolution(user_id, {
                "timestamp": datetime.now().isoformat(),
                "preferences": current_preferences,
                "shifts": shifts
            })
            
            return {
                "status": "success",
                "tracked_at": datetime.now().isoformat(),
                "current_preferences": current_preferences,
                "shifts": shifts
            }
        
        def get_evolution_summary(self, user_id, time_range=90):
            # 获取历史偏好
            history = self.db.get_preference_history(user_id)
            
            # 计算趋势
            trend = self.detect_shift(user_id)["current_trend"]
            
            # 预测未来
            forecast = self.detect_shift(user_id)["predicted_shift"]
            
            # 提取重要变化
            significant_changes = []
            
            # 从趋势中提取
            if "significant_shifts" in trend:
                for shift in trend["significant_shifts"]:
                    significant_changes.append({
                        "type": "observed_trend",
                        "dimension": shift["dimension"],
                        "direction": shift["direction"],
                        "magnitude": shift["magnitude"],
                        "confidence": shift.get("confidence", 0.0)
                    })
            
            # 从预测中提取
            if "potential_shifts" in forecast:
                for shift in forecast["potential_shifts"]:
                    significant_changes.append({
                        "type": "predicted_shift",
                        "dimension": shift["dimension"],
                        "direction": shift["direction"],
                        "change_percentage": shift["change_percentage"],
                        "confidence": shift.get("confidence", 0.0)
                    })
            
            return {
                "status": "success",
                "user_id": user_id,
                "time_range": f"{time_range} days",
                "generated_at": datetime.now().isoformat(),
                "history_points": len(history),
                "overall_stability": trend.get("overall_stability", 0.5),
                "significant_changes": significant_changes,
                "trend": trend,
                "forecast": forecast
            }
    
    PreferenceEvolution = MockEvolutionTracker
    
    def detect_preference_shift(user_id):
        tracker = PreferenceEvolution()
        return tracker.detect_shift(user_id)
    
    def track_preference_changes(user_id):
        tracker = PreferenceEvolution()
        return tracker.track_preference_evolution(user_id)
    
    def get_preference_evolution_summary(user_id, days=90):
        tracker = PreferenceEvolution()
        return tracker.get_evolution_summary(user_id, days)


def format_trend_output(trend_data):
    """格式化趋势输出"""
    output = []
    
    # 添加总体稳定性
    if "overall_stability" in trend_data:
        stability = trend_data["overall_stability"] * 100
        output.append(f"总体偏好稳定性: {stability:.1f}%")
    
    # 添加显著变化
    if "significant_shifts" in trend_data and trend_data["significant_shifts"]:
        output.append("\n显著偏好变化:")
        for shift in trend_data["significant_shifts"]:
            direction = "增加" if shift["direction"] == "increasing" else "减少" if shift["direction"] == "decreasing" else "稳定"
            output.append(f"  • {shift['dimension']} 偏好{direction}，变化幅度: {shift['magnitude']*100:.1f}%")
            if "confidence" in shift:
                output.append(f"    置信度: {shift['confidence']*100:.1f}%")
    else:
        output.append("\n未检测到显著变化")
    
    return "\n".join(output)


def format_forecast_output(forecast_data):
    """格式化预测输出"""
    output = []
    
    # 添加预测信息
    if "forecast_window" in forecast_data:
        output.append(f"预测窗口: {forecast_data['forecast_window']}")
    
    # 添加潜在变化
    if "potential_shifts" in forecast_data and forecast_data["potential_shifts"]:
        output.append("\n预测的偏好转变:")
        for shift in forecast_data["potential_shifts"]:
            direction = "增加" if shift["direction"] == "increasing" else "减少" if shift["direction"] == "decreasing" else "稳定"
            output.append(f"  • {shift['dimension']} 偏好预计将{direction}")
            output.append(f"    当前: {shift['current_value']:.2f} → 预测: {shift['predicted_value']:.2f}")
            if "change_percentage" in shift:
                output.append(f"    变化幅度: {shift['change_percentage']:.1f}%")
            if "confidence" in shift:
                output.append(f"    置信度: {shift['confidence']*100:.1f}%")
    else:
        output.append("\n未预测到显著变化")
    
    return "\n".join(output)


def run_demo():
    """运行演示"""
    # 测试用户ID
    user_id = "test_user_123"
    
    print("\n" + "="*50)
    print("偏好进化追踪器演示")
    print("="*50)
    
    # 创建追踪器实例
    tracker = PreferenceEvolution()
    
    # 演示偏好迁移检测
    print("\n>> 检测用户偏好迁移")
    print("-"*50)
    
    shift_result = tracker.detect_shift(user_id)
    
    print("\n当前趋势:")
    if "current_trend" in shift_result:
        print(format_trend_output(shift_result["current_trend"]))
    
    print("\n预测未来偏好变化:")
    if "predicted_shift" in shift_result:
        print(format_forecast_output(shift_result["predicted_shift"]))
    
    # 演示追踪偏好演变
    print("\n\n>> 追踪记录用户偏好演变")
    print("-"*50)
    
    tracking_result = track_preference_changes(user_id)
    
    if "status" in tracking_result and tracking_result["status"] == "success":
        print("\n偏好演变记录已成功保存")
        print(f"记录时间: {tracking_result.get('tracked_at', '未知')}")
        
        if "shifts" in tracking_result and "current_trend" in tracking_result["shifts"]:
            current_trend = tracking_result["shifts"]["current_trend"]
            if "significant_shifts" in current_trend and current_trend["significant_shifts"]:
                print("\n检测到的偏好变化:")
                for shift in current_trend["significant_shifts"][:2]:
                    direction = "增加" if shift["direction"] == "increasing" else "减少" if shift["direction"] == "decreasing" else "稳定"
                    print(f"  • {shift['dimension']} 偏好{direction}，幅度 {shift['magnitude']*100:.1f}%")
    else:
        print("\n偏好演变记录保存失败")
        if "message" in tracking_result:
            print(f"原因: {tracking_result['message']}")
    
    # 演示获取偏好演变摘要
    print("\n\n>> 获取偏好演变摘要 (过去90天)")
    print("-"*50)
    
    summary = get_preference_evolution_summary(user_id, 90)
    
    if "overall_stability" in summary:
        print(f"\n总体偏好稳定性: {summary['overall_stability']*100:.1f}%")
    
    if "significant_changes" in summary and summary["significant_changes"]:
        print("\n重要变化:")
        for i, change in enumerate(summary["significant_changes"][:3]):
            change_type = "观察到的趋势" if change["type"] == "observed_trend" else "预测的转变"
            dimension = change["dimension"]
            direction = "增加" if change["direction"] == "increasing" else "减少" if change["direction"] == "decreasing" else "稳定"
            
            print(f"  {i+1}. [{change_type}] {dimension} 偏好{direction}")
            
            if "magnitude" in change:
                print(f"     变化幅度: {change['magnitude']*100:.1f}%")
            elif "change_percentage" in change:
                print(f"     变化幅度: {change['change_percentage']:.1f}%")
            
            if "confidence" in change:
                print(f"     置信度: {change['confidence']*100:.1f}%")
    
    print("\n" + "="*50)
    print("偏好进化追踪器演示完成")
    print("="*50)


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n演示已中断")
    except Exception as e:
        import traceback
        print(f"\n\n演示出错: {str(e)}")
        traceback.print_exc() 