#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全链路监控看板示例

演示如何使用全链路监控看板收集和展示实时通信性能指标。
"""

import os
import sys
import json
import time
import random
import asyncio
import logging
from typing import Dict, Any

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("monitoring_example")

from src.realtime.monitoring import (
    TelemetryDashboard,
    initialize_telemetry_dashboard,
    get_telemetry_dashboard
)

# 全局变量
SHOULD_CONTINUE = True

async def simulate_websocket_traffic():
    """模拟WebSocket流量"""
    dashboard = get_telemetry_dashboard()
    
    # 初始连接计数
    active_connections = 0
    idle_connections = 0
    
    logger.info("开始模拟WebSocket流量")
    
    try:
        while SHOULD_CONTINUE:
            # 模拟新连接
            if random.random() < 0.2:  # 20%概率添加新连接
                if random.random() < 0.7:  # 70%概率为活跃连接
                    active_connections += 1
                else:
                    idle_connections += 1
                
            # 模拟断开连接
            if random.random() < 0.1 and (active_connections > 0 or idle_connections > 0):  # 10%概率断开连接
                if random.random() < 0.5 and active_connections > 0:  # 50%概率断开活跃连接
                    active_connections -= 1
                elif idle_connections > 0:
                    idle_connections -= 1
            
            # 更新连接指标
            dashboard.update_connection_metrics(active_connections, idle_connections)
            
            # 模拟消息传输
            for _ in range(random.randint(1, 5)):  # 每次循环1-5条消息
                # 随机消息方向
                direction = "incoming" if random.random() < 0.6 else "outgoing"
                
                # 随机消息大小(200-5000字节)
                size_bytes = random.randint(200, 5000)
                
                # 随机消息类型
                msg_types = ["data", "control", "heartbeat", "ack"]
                msg_type = random.choice(msg_types)
                
                # 记录消息
                dashboard.record_message(direction, size_bytes, msg_type)
            
            # 模拟延迟
            latency_ms = random.uniform(5.0, 100.0)
            if random.random() < 0.05:  # 5%概率出现高延迟
                latency_ms = random.uniform(100.0, 500.0)
            
            dashboard.record_latency(latency_ms)
            
            # 模拟错误
            if random.random() < 0.02:  # 2%概率出现错误
                components = ["websocket", "session", "router", "engine", "broadcaster"]
                component = random.choice(components)
                
                severities = ["warning", "error", "critical"]
                severity_weights = [0.7, 0.25, 0.05]  # 权重：70%警告，25%错误，5%严重错误
                severity = random.choices(severities, weights=severity_weights)[0]
                
                dashboard.record_error(component, severity)
            
            # 模拟会话更新
            session_count = active_connections  # 假设每个活跃连接有一个会话
            dashboard.update_session_count(session_count, session_count + idle_connections)
            
            # 模拟队列大小变化
            queues = ["message_queue", "task_queue", "event_queue"]
            for queue in queues:
                size = random.randint(0, 50)
                dashboard.update_queue_size(queue, size)
            
            # 显示当前指标
            if random.random() < 0.2:  # 20%概率打印指标
                metrics = dashboard.display_realtime_metrics()
                logger.info(f"活跃连接: {metrics['connections']['active']}, "
                            f"消息总数: {metrics['messages']['total']}, "
                            f"平均延迟: {metrics['latency']['avg']:.2f}ms, "
                            f"错误总数: {metrics['errors']['total']}")
            
            # 随机等待时间(0.5-2秒)
            await asyncio.sleep(random.uniform(0.5, 2.0))
    
    except asyncio.CancelledError:
        logger.info("模拟流量任务被取消")
    except Exception as e:
        logger.error(f"模拟流量出错: {str(e)}")

async def print_dashboard_summary():
    """定期打印仪表盘摘要"""
    dashboard = get_telemetry_dashboard()
    
    try:
        while SHOULD_CONTINUE:
            metrics = dashboard.display_realtime_metrics()
            
            # 格式化输出
            print("\n" + "="*50)
            print("全链路监控看板摘要")
            print("="*50)
            print(f"运行时间: {metrics['uptime']:.1f}秒")
            print(f"最后更新: {metrics['last_update']:.1f}秒前")
            print("-"*50)
            
            print("连接状态:")
            print(f"  活跃连接: {metrics['connections']['active']}")
            print(f"  空闲连接: {metrics['connections']['idle']}")
            print(f"  总连接数: {metrics['connections']['total']}")
            
            print("会话信息:")
            print(f"  活跃会话: {metrics['sessions']['active']}")
            print(f"  总会话数: {metrics['sessions']['total']}")
            
            print("延迟统计 (ms):")
            print(f"  平均延迟: {metrics['latency']['avg']:.2f}")
            print(f"  最小延迟: {metrics['latency']['min']:.2f}")
            print(f"  最大延迟: {metrics['latency']['max']:.2f}")
            print(f"  P95延迟: {metrics['latency']['p95']:.2f}")
            print(f"  P99延迟: {metrics['latency']['p99']:.2f}")
            
            print("消息统计:")
            print(f"  传入消息: {metrics['messages']['incoming']}")
            print(f"  传出消息: {metrics['messages']['outgoing']}")
            print(f"  消息总数: {metrics['messages']['total']}")
            
            print("带宽使用 (字节):")
            print(f"  传入带宽: {metrics['bandwidth']['incoming']}")
            print(f"  传出带宽: {metrics['bandwidth']['outgoing']}")
            print(f"  总带宽: {metrics['bandwidth']['total']}")
            
            print("错误统计:")
            print(f"  错误总数: {metrics['errors']['total']}")
            for component, count in metrics['errors'].get('by_component', {}).items():
                print(f"  {component}: {count}")
            
            print("队列状态:")
            for queue, size in metrics['queues'].items():
                print(f"  {queue}: {size}")
            
            print("资源使用:")
            print(f"  内存使用: {metrics['resources']['memory'] / (1024*1024):.2f} MB")
            print(f"  CPU使用率: {metrics['resources']['cpu']:.2f}%")
            
            print("="*50)
            
            await asyncio.sleep(5)  # 每5秒打印一次摘要
    
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"打印摘要出错: {str(e)}")

async def main():
    """主函数"""
    global SHOULD_CONTINUE
    
    logger.info("启动全链路监控看板示例")
    
    try:
        # 初始化仪表盘
        config = {}
        config_path = os.path.join("configs", "monitoring.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                logger.warning(f"加载监控配置失败: {str(e)}")
        
        dashboard = await initialize_telemetry_dashboard(config)
        logger.info("全链路监控看板已初始化")
        
        # 创建模拟流量任务
        traffic_task = asyncio.create_task(simulate_websocket_traffic())
        
        # 创建摘要打印任务
        summary_task = asyncio.create_task(print_dashboard_summary())
        
        # 运行一段时间后退出
        runtime = 60  # 运行60秒
        logger.info(f"示例将运行{runtime}秒")
        await asyncio.sleep(runtime)
        
        # 停止任务
        SHOULD_CONTINUE = False
        traffic_task.cancel()
        summary_task.cancel()
        
        try:
            await traffic_task
        except asyncio.CancelledError:
            pass
        
        try:
            await summary_task
        except asyncio.CancelledError:
            pass
        
        # 最终统计
        metrics = dashboard.display_realtime_metrics()
        logger.info("示例运行结束，最终统计:")
        logger.info(f"总运行时间: {metrics['uptime']:.1f}秒")
        logger.info(f"总消息数: {metrics['messages']['total']}")
        logger.info(f"错误总数: {metrics['errors']['total']}")
        logger.info(f"平均延迟: {metrics['latency']['avg']:.2f}ms")
        
    except Exception as e:
        logger.error(f"示例执行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 确保停止后台收集
        dashboard = get_telemetry_dashboard()
        dashboard.stop_background_collection()
        logger.info("示例完成，已停止后台指标收集")

if __name__ == "__main__":
    asyncio.run(main()) 