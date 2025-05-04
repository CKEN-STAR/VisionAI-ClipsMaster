#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
偏好进化追踪器演示脚本

演示如何使用偏好进化追踪器检测用户偏好变化、分析趋势并预测未来偏好演变。
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timedelta
from pprint import pprint
import matplotlib.pyplot as plt
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

print("开始偏好进化追踪器演示...")

# 创建模拟模块类
class MockModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# 替换真实模块为模拟模块
try:
    from src.audience.evolution_tracker import (
        PreferenceEvolution,
        detect_preference_shift,
        track_preference_changes,
        get_preference_evolution_summary
    )
except ImportError:
    print("无法导入偏好进化追踪器模块，将使用模拟数据")
    
    class MockPreferenceEvolution:
        def __init__(self):
            self.tracked_dimensions = [
                "genre", "narrative", "pace", "visuals", 
                "audio", "complexity", "emotional", "themes"
            ]
        
        def detect_shift(self, user_id):
            return {
                "current_trend": self._mock_trend(),
                "predicted_shift": self._mock_forecast()
            }
        
        def _mock_trend(self):
            trends = {}
            for dim in self.tracked_dimensions:
                direction = random.choice(["stable", "increasing", "decreasing"])
                magnitude = random.uniform(0.1, 0.8) if direction != "stable" else 0.05
                trends[dim] = {
                    "direction": direction,
                    "magnitude": round(magnitude, 2),
                    "correlation": round(random.uniform(0.3, 0.9), 2),
                    "confidence": round(random.uniform(0.4, 0.9), 2)
                }
            
            significant = []
            for dim, data in trends.items():
                if data["magnitude"] > 0.2:
                    significant.append({
                        "dimension": dim,
                        "direction": data["direction"],
                        "magnitude": data["magnitude"],
                        "confidence": data["confidence"]
                    })
            
            return {
                "status": "success",
                "analyzed_at": datetime.now().isoformat(),
                "dimension_trends": trends,
                "significant_shifts": sorted(significant, key=lambda x: x["magnitude"], reverse=True)[:3],
                "overall_stability": round(random.uniform(0.3, 0.8), 2)
            }
        
        def _mock_forecast(self):
            forecasts = {}
            for dim in self.tracked_dimensions:
                current = random.uniform(0.3, 0.7)
                predicted = current + random.uniform(-0.3, 0.3)
                direction = "stable" if abs(predicted - current) < 0.05 else ("increasing" if predicted > current else "decreasing")
                
                forecasts[dim] = {
                    "current_value": round(current, 2),
                    "predicted_value": round(predicted, 2),
                    "change_direction": direction,
                    "confidence": round(random.uniform(0.4, 0.9), 2)
                }
            
            potential = []
            for dim, data in forecasts.items():
                change_pct = abs((data["predicted_value"] - data["current_value"]) / data["current_value"])
                if change_pct > 0.2:
                    potential.append({
                        "dimension": dim,
                        "current_value": data["current_value"],
                        "predicted_value": data["predicted_value"],
                        "change_percentage": round(change_pct * 100, 1),
                        "direction": data["change_direction"],
                        "confidence": data["confidence"]
                    })
            
            return {
                "status": "success",
                "forecasted_at": datetime.now().isoformat(),
                "forecast_window": "30 days",
                "dimension_forecasts": forecasts,
                "potential_shifts": sorted(potential, key=lambda x: x["change_percentage"], reverse=True)[:3]
            }
        
        def track_preference_evolution(self, user_id):
            return {
                "status": "success",
                "tracked_at": datetime.now().isoformat(),
                "current_preferences": self._mock_preferences(),
                "shifts": self.detect_shift(user_id)
            }
        
        def _mock_preferences(self):
            return {
                "status": "success",
                "genre": {
                    "favorites": ["动作", "科幻"],
                    "strength_map": {
                        "动作": {"ratio": 0.7, "strength": "strong"},
                        "科幻": {"ratio": 0.3, "strength": "moderate"}
                    }
                },
                "pace": {
                    "preferred_pace": "fast",
                    "engagement_by_pace": {
                        "fast": {"completion_rate": 0.8},
                        "moderate": {"completion_rate": 0.6}
                    }
                }
            }
        
        def get_evolution_summary(self, user_id, time_range=90):
            result = {
                "status": "success",
                "user_id": user_id,
                "time_range": f"{time_range} days",
                "generated_at": datetime.now().isoformat(),
                "history_points": random.randint(10, 30),
                "overall_stability": round(random.uniform(0.3, 0.8), 2),
                "significant_changes": []
            }
            
            trend = self._mock_trend()
            forecast = self._mock_forecast()
            
            result["trend"] = trend
            result["forecast"] = forecast
            
            # 提取重要变化
            for shift in trend.get("significant_shifts", []):
                result["significant_changes"].append({
                    "type": "observed_trend",
                    "dimension": shift["dimension"],
                    "direction": shift["direction"],
                    "magnitude": shift["magnitude"],
                    "confidence": shift.get("confidence", 0.0)
                })
            
            for shift in forecast.get("potential_shifts", []):
                result["significant_changes"].append({
                    "type": "predicted_shift",
                    "dimension": shift["dimension"],
                    "direction": shift["direction"],
                    "change_percentage": shift["change_percentage"],
                    "confidence": shift.get("confidence", 0.0)
                })
            
            return result
    
    PreferenceEvolution = MockPreferenceEvolution
    
    def detect_preference_shift(user_id):
        tracker = PreferenceEvolution()
        return tracker.detect_shift(user_id)
    
    def track_preference_changes(user_id):
        tracker = PreferenceEvolution()
        return tracker.track_preference_evolution(user_id)
    
    def get_preference_evolution_summary(user_id, days=90):
        tracker = PreferenceEvolution()
        return tracker.get_evolution_summary(user_id, days)


# 定义测试用户
TEST_USER_ID = "user_7842"

def demo_preference_shift_detection():
    """演示偏好迁移检测"""
    print("\n\n===== 演示偏好迁移检测 =====")
    
    # 创建追踪器实例
    tracker = PreferenceEvolution()
    
    # 检测偏好迁移
    print("检测用户 {} 的偏好迁移...".format(TEST_USER_ID))
    shift_result = tracker.detect_shift(TEST_USER_ID)
    
    # 打印结果
    print("\n当前趋势:")
    if "current_trend" in shift_result and "significant_shifts" in shift_result["current_trend"]:
        for shift in shift_result["current_trend"]["significant_shifts"]:
            print("  • {} 偏好{}，变化幅度: {:.1f}% (置信度: {:.1f}%)".format(
                shift["dimension"],
                "增加" if shift["direction"] == "increasing" else "减少",
                shift["magnitude"] * 100,
                shift["confidence"] * 100
            ))
    else:
        print("  • 未检测到显著趋势")
    
    print("\n预测的偏好转变:")
    if "predicted_shift" in shift_result and "potential_shifts" in shift_result["predicted_shift"]:
        for shift in shift_result["predicted_shift"]["potential_shifts"]:
            print("  • {} 偏好预计将{}: 当前 {:.2f} -> 预测 {:.2f}，变化 {:.1f}% (置信度: {:.1f}%)".format(
                shift["dimension"],
                "增加" if shift["direction"] == "increasing" else "减少",
                shift["current_value"],
                shift["predicted_value"],
                shift["change_percentage"],
                shift["confidence"] * 100
            ))
    else:
        print("  • 未预测到显著转变")
    
    # 使用便捷函数
    print("\n使用便捷函数检测偏好迁移...")
    quick_result = detect_preference_shift(TEST_USER_ID)
    print("检测完成!")


def demo_preference_tracking():
    """演示偏好跟踪"""
    print("\n\n===== 演示偏好跟踪 =====")
    
    # 跟踪偏好演变
    print("跟踪用户 {} 的偏好演变...".format(TEST_USER_ID))
    tracking_result = track_preference_changes(TEST_USER_ID)
    
    # 打印结果
    print("\n当前偏好概述:")
    if "current_preferences" in tracking_result and "genre" in tracking_result["current_preferences"]:
        genre_prefs = tracking_result["current_preferences"]["genre"]
        if "favorites" in genre_prefs and genre_prefs["favorites"]:
            print("  • 最喜欢的内容类型: {}".format(", ".join(genre_prefs["favorites"][:3])))
        
        if "pace" in tracking_result["current_preferences"]:
            pace = tracking_result["current_preferences"]["pace"]
            if "preferred_pace" in pace:
                print("  • 偏好节奏: {}".format(pace["preferred_pace"]))
    
    print("\n检测到的偏好变化:")
    if "shifts" in tracking_result and "current_trend" in tracking_result["shifts"]:
        if "overall_stability" in tracking_result["shifts"]["current_trend"]:
            stability = tracking_result["shifts"]["current_trend"]["overall_stability"]
            print("  • 偏好稳定性: {:.1f}%".format(stability * 100))
        
        if "significant_shifts" in tracking_result["shifts"]["current_trend"]:
            for shift in tracking_result["shifts"]["current_trend"]["significant_shifts"]:
                print("  • {} 偏好{}中，幅度 {:.1f}%".format(
                    shift["dimension"],
                    "增强" if shift["direction"] == "increasing" else "减弱",
                    shift["magnitude"] * 100
                ))


def demo_evolution_summary():
    """演示偏好演变摘要"""
    print("\n\n===== 演示偏好演变摘要 =====")
    
    # 获取偏好演变摘要
    print("获取用户 {} 最近90天的偏好演变摘要...".format(TEST_USER_ID))
    summary = get_preference_evolution_summary(TEST_USER_ID, 90)
    
    # 打印结果
    print("\n偏好演变摘要:")
    print("  • 分析时段: {}".format(summary.get("time_range", "未知")))
    print("  • 数据点数: {}".format(summary.get("history_points", 0)))
    print("  • 偏好稳定性: {:.1f}%".format(summary.get("overall_stability", 0) * 100))
    
    print("\n显著变化:")
    if "significant_changes" in summary:
        for i, change in enumerate(summary["significant_changes"]):
            if change["type"] == "observed_trend":
                print("  {}. {} 偏好已{}，幅度 {:.1f}% (置信度: {:.1f}%)".format(
                    i+1,
                    change["dimension"],
                    "增强" if change["direction"] == "increasing" else "减弱",
                    change["magnitude"] * 100,
                    change["confidence"] * 100
                ))
            else:
                print("  {}. {} 偏好预计将{}，变化 {:.1f}% (置信度: {:.1f}%)".format(
                    i+1,
                    change["dimension"],
                    "增强" if change["direction"] == "increasing" else "减弱",
                    change.get("change_percentage", 0),
                    change["confidence"] * 100
                ))
    
    # 尝试绘制趋势图表
    try:
        plot_evolution_trends(summary)
    except Exception as e:
        print(f"无法绘制趋势图表: {str(e)}")


def plot_evolution_trends(summary):
    """绘制偏好演变趋势图表"""
    # 检查matplotlib是否可用
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("无法导入matplotlib，跳过图表绘制")
        return
    
    # 提取显著变化的维度
    dimensions = []
    if "significant_changes" in summary:
        for change in summary["significant_changes"]:
            if change["dimension"] not in dimensions:
                dimensions.append(change["dimension"])
    
    if not dimensions:
        # 如果没有显著变化，使用默认维度
        dimensions = ["genre", "pace", "visuals", "complexity"]
    
    # 限制最多显示4个维度
    dimensions = dimensions[:4]
    
    # 创建模拟数据 - 在实际应用中，这将从历史数据中提取
    days = 90
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    
    # 为每个维度创建趋势线
    trends = {}
    for dim in dimensions:
        # 创建趋势数据 - 在实际中这将基于真实历史数据
        if "trend" in summary and "dimension_trends" in summary["trend"]:
            # 使用趋势信息调整趋势线
            trend_info = summary["trend"]["dimension_trends"].get(dim, {})
            direction = trend_info.get("direction", "stable")
            magnitude = trend_info.get("magnitude", 0.1)
            
            # 创建带噪声的趋势线
            if direction == "increasing":
                base = np.linspace(0.4, 0.4 + magnitude, num=days)
            elif direction == "decreasing":
                base = np.linspace(0.6, 0.6 - magnitude, num=days)
            else:
                base = np.linspace(0.5, 0.5, num=days)
            
            # 添加随机噪声
            noise = np.random.normal(0, 0.05, days)
            values = base + noise
            
            # 确保数值在0-1之间
            values = np.clip(values, 0, 1)
        else:
            # 随机生成数据
            start_val = random.uniform(0.3, 0.7)
            end_val = start_val + random.uniform(-0.3, 0.3)
            base = np.linspace(start_val, end_val, num=days)
            noise = np.random.normal(0, 0.05, days)
            values = np.clip(base + noise, 0, 1)
        
        trends[dim] = values
    
    # 创建图表
    plt.figure(figsize=(10, 6))
    for dim, values in trends.items():
        plt.plot(dates, values, label=dim, linewidth=2, alpha=0.7)
    
    # 添加未来预测延伸线
    future_days = 30
    future_dates = [datetime.now() + timedelta(days=i) for i in range(1, future_days+1)]
    
    for dim, values in trends.items():
        if "forecast" in summary and "dimension_forecasts" in summary["forecast"]:
            forecast_info = summary["forecast"]["dimension_forecasts"].get(dim, {})
            current = forecast_info.get("current_value", values[-1])
            predicted = forecast_info.get("predicted_value", current)
            
            # 创建线性预测
            future_values = np.linspace(values[-1], predicted, num=future_days)
        else:
            # 简单线性延伸
            slope = (values[-1] - values[-10]) / 10  # 使用最后10天的趋势
            future_values = [values[-1] + slope * i for i in range(1, future_days+1)]
            
            # 确保数值在0-1之间
            future_values = np.clip(future_values, 0, 1)
        
        plt.plot(future_dates, future_values, '--', color=plt.gca().lines[-1].get_color(), alpha=0.5)
    
    # 添加当前日期标记
    plt.axvline(x=datetime.now(), color='black', linestyle='--', alpha=0.3)
    plt.text(datetime.now(), 0.05, '当前', ha='center', va='bottom', alpha=0.7)
    
    # 设置图表样式
    plt.title('用户偏好演变趋势')
    plt.xlabel('日期')
    plt.ylabel('偏好强度')
    plt.ylim(0, 1)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper left')
    
    # 格式化日期刻度
    plt.gcf().autofmt_xdate()
    
    # 显示或保存图表
    try:
        plt.savefig('preference_evolution_trend.png')
        print("\n趋势图表已保存为 'preference_evolution_trend.png'")
    except:
        plt.show()


def demo_interactive_evolution_tracking():
    """交互式偏好演变追踪演示"""
    print("\n\n===== 交互式偏好演变追踪演示 =====")
    
    user_id = input("请输入用户ID (默认: {}): ".format(TEST_USER_ID)).strip() or TEST_USER_ID
    
    print("\n选择操作:")
    print("1. 检测偏好迁移")
    print("2. 追踪偏好演变")
    print("3. 获取偏好演变摘要")
    print("4. 执行所有演示")
    
    choice = input("\n请选择 (1-4, 默认: 4): ").strip() or "4"
    
    if choice == "1":
        demo_preference_shift_detection()
    elif choice == "2":
        demo_preference_tracking()
    elif choice == "3":
        demo_evolution_summary()
    else:
        demo_preference_shift_detection()
        demo_preference_tracking()
        demo_evolution_summary()


if __name__ == "__main__":
    try:
        demo_interactive_evolution_tracking()
    except KeyboardInterrupt:
        print("\n演示已中断")
    except Exception as e:
        print(f"\n演示过程中出错: {str(e)}")
    finally:
        print("\n偏好进化追踪器演示结束") 