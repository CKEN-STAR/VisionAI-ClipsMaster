#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web应用主入口

提供Web API和用户界面，整合各个组件功能。
"""

import os
import sys
import logging
import asyncio
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.api.version_api import register_version_api
from src.api.canary_api import register_canary_api
from src.api.quality_api import register_quality_api
from src.utils.log_handler import configure_logging, get_logger

# 创建应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 配置日志
configure_logging({
    "level": "info",
    "console_enabled": True,
    "file_enabled": True,
    "file_path": "logs",
    "file_prefix": "visionai_api"
})

logger = get_logger("app")

# 注册API路由
register_version_api(app)
register_canary_api(app)
register_quality_api(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "service": "VisionAI-ClipsMaster"
    })

@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({
        "success": False,
        "error": "资源不存在",
        "message": str(error)
    }), 404

@app.errorhandler(500)
def server_error(error):
    """处理500错误"""
    logger.error(f"服务器错误: {str(error)}")
    return jsonify({
        "success": False,
        "error": "服务器内部错误",
        "message": str(error)
    }), 500

# 添加实时通信模块初始化
def init_duplex_communication():
    """初始化双工通信模块"""
    try:
        # 导入双工通信模块
        from src.realtime import (
            initialize_duplex_engine,
            initialize_session_manager,
            initialize_command_router,
            MessageType,
            ProtocolType
        )
        
        # 创建异步事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 初始化双工通信引擎
        loop.run_until_complete(
            initialize_duplex_engine(
                protocols=[ProtocolType.WEBSOCKET],
                ws_host="0.0.0.0",
                ws_port=8765
            )
        )
        
        # 初始化会话管理器
        initialize_session_manager(
            max_sessions=10000,  # 最多支持10000个会话
            idle_timeout=3600,   # 空闲1小时自动过期
            cleanup_interval=300 # 每5分钟清理一次过期会话
        )
        
        # 初始化命令路由器
        initialize_command_router()
        
        # 设置初始化标志
        app.config['DUPLEX_INITIALIZED'] = True
        
        # 在新线程中运行事件循环
        def run_async_loop():
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        import threading
        threading.Thread(target=run_async_loop, daemon=True).start()
        
        logger.info("双工通信模块已初始化，WebSocket服务器运行在 ws://0.0.0.0:8765")
        logger.info("会话管理器已初始化，最大支持10000个会话")
        logger.info("命令路由器已初始化，支持编辑、协作、撤销等命令")
        
    except ImportError as e:
        logger.warning(f"无法导入双工通信模块: {str(e)}")
        logger.warning("双工通信功能将不可用，请安装所需依赖: pip install websockets")
        app.config['DUPLEX_INITIALIZED'] = False
    except Exception as e:
        logger.error(f"初始化双工通信模块失败: {str(e)}")
        app.config['DUPLEX_INITIALIZED'] = False

# 在应用启动前初始化双工通信模块
init_duplex_communication()

# 添加关闭双工通信的函数，用于在应用关闭时调用
def shutdown_duplex_communication():
    """关闭双工通信模块"""
    if app.config.get('DUPLEX_INITIALIZED', False):
        try:
            from src.realtime import shutdown_duplex_engine, get_session_manager, get_command_router
            
            # 获取会话管理器并关闭所有会话
            try:
                session_manager = get_session_manager()
                # 获取所有会话ID
                with session_manager.lock:
                    session_ids = list(session_manager.sessions.keys())
                
                # 关闭所有会话
                for session_id in session_ids:
                    session_manager.close_session(session_id)
                
                logger.info(f"已关闭所有会话: {len(session_ids)}个")
            except Exception as e:
                logger.error(f"关闭会话时出错: {str(e)}")
            
            # 获取事件循环
            loop = asyncio.get_event_loop()
            
            # 关闭双工通信引擎
            loop.run_until_complete(shutdown_duplex_engine())
            
            # 停止事件循环
            loop.stop()
            
            logger.info("双工通信模块已关闭")
        except ImportError:
            logger.warning("双工通信模块未导入，无需关闭")
        except Exception as e:
            logger.error(f"关闭双工通信模块出错: {str(e)}")

# 应用退出时关闭双工通信
import atexit
atexit.register(shutdown_duplex_communication)

# 如果直接运行此文件则启动应用
if __name__ == '__main__':
    # 生产环境应使用生产级Web服务器，如gunicorn
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 