#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版多维度数据源服务器

提供HTTP API接口访问模拟数据源，展示系统资源使用情况，
完全独立实现，不依赖项目其他模块。
"""

import os
import sys
import json
import time
import logging
import threading
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simple_dashboard")

# 模拟数据源
class DataSource:
    """提供模拟数据"""
    
    @staticmethod
    def get_system_status():
        """获取系统状态"""
        try:
            vm = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                "status": "ok",
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "memory": {
                    "total_mb": vm.total / (1024 * 1024),
                    "available_mb": vm.available / (1024 * 1024),
                    "used_mb": vm.used / (1024 * 1024),
                    "percent": vm.percent
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count()
                }
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def get_data_sources():
        """获取数据源列表"""
        return {
            "status": "ok",
            "timestamp": time.time(),
            "sources": {
                "memory": {"status": "ok", "type": "system"},
                "cache": {"status": "ok", "type": "redis"},
                "models": {"status": "ok", "type": "performance"},
                "system": {"status": "ok", "type": "os"}
            }
        }
    
    @staticmethod
    def get_source_data(source_name):
        """获取特定数据源详情"""
        if source_name == "memory":
            vm = psutil.virtual_memory()
            return {
                "status": "ok",
                "source": source_name,
                "timestamp": time.time(),
                "data": {
                    "memory_metrics": {
                        "process_rss": psutil.Process().memory_info().rss / (1024 * 1024),
                        "system_used": vm.used / (1024 * 1024),
                        "system_percent": vm.percent
                    }
                }
            }
        elif source_name == "cache":
            return {
                "status": "ok",
                "source": source_name,
                "timestamp": time.time(),
                "data": {
                    "cache_metrics": {
                        "used_memory_mb": 128.5,
                        "hit_rate": 0.85,
                        "evicted_keys": 24,
                        "expired_keys": 156
                    }
                }
            }
        elif source_name == "models":
            return {
                "status": "ok",
                "source": source_name,
                "timestamp": time.time(),
                "data": {
                    "model_metrics": {
                        "clip_base": {
                            "avg_inference_ms": 148.2,
                            "p95_inference_ms": 150.8,
                        },
                        "vit_small": {
                            "avg_inference_ms": 80.8,
                            "p95_inference_ms": 82.1,
                        }
                    }
                }
            }
        elif source_name == "system":
            return {
                "status": "ok",
                "source": source_name,
                "timestamp": time.time(),
                "data": {
                    "system_metrics": {
                        "memory": {
                            "percent": psutil.virtual_memory().percent,
                            "available_mb": psutil.virtual_memory().available / (1024 * 1024)
                        },
                        "cpu": {
                            "percent": psutil.cpu_percent(interval=0.1),
                            "count": psutil.cpu_count()
                        }
                    }
                }
            }
        else:
            return {
                "status": "error",
                "error": f"未知数据源: {source_name}",
                "timestamp": time.time()
            }


class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """处理HTTP请求的处理器"""
    
    # 设置跨域头
    def _set_headers(self, content_type="application/json"):
        """设置响应头，支持跨域"""
        self.send_response(200)
        self.send_header("Content-type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        # 解析URL
        url = urlparse(self.path)
        path = url.path
        
        try:
            # 简单路由分发
            if path == "/":
                self._handle_index()
            elif path == "/health":
                self._handle_health()
            elif path == "/api/data_sources":
                self._handle_data_sources()
            elif path.startswith("/api/source/"):
                source_name = path.split("/")[-1]
                self._handle_source_data(source_name)
            elif path == "/api/system/status":
                self._handle_system_status()
            else:
                self._handle_not_found()
        except Exception as e:
            self._handle_error(e)
    
    def _handle_index(self):
        """处理根路径请求"""
        self._set_headers("text/html")
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>简化版数据仪表板</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .endpoint { margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .path { font-family: monospace; background-color: #f5f5f5; padding: 3px; }
    </style>
</head>
<body>
    <h1>简化版数据仪表板 API</h1>
    
    <div class="endpoint">
        <h3>健康检查</h3>
        <div class="path">GET /health</div>
    </div>
    
    <div class="endpoint">
        <h3>数据源列表</h3>
        <div class="path">GET /api/data_sources</div>
    </div>
    
    <div class="endpoint">
        <h3>数据源详情</h3>
        <div class="path">GET /api/source/{source_name}</div>
    </div>
    
    <div class="endpoint">
        <h3>系统状态</h3>
        <div class="path">GET /api/system/status</div>
    </div>
</body>
</html>
"""
        self.wfile.write(html.encode("utf-8"))
    
    def _handle_health(self):
        """处理健康检查请求"""
        self._set_headers()
        response = {
            "status": "ok",
            "timestamp": time.time(),
            "server": "simple_dashboard",
            "version": "1.0"
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def _handle_data_sources(self):
        """处理数据源列表请求"""
        self._set_headers()
        response = DataSource.get_data_sources()
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def _handle_source_data(self, source_name):
        """处理数据源详情请求"""
        self._set_headers()
        response = DataSource.get_source_data(source_name)
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def _handle_system_status(self):
        """处理系统状态请求"""
        self._set_headers()
        response = DataSource.get_system_status()
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def _handle_not_found(self):
        """处理未找到的请求"""
        self.send_response(404)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        response = {
            "status": "error",
            "error": "未找到请求的路径",
            "path": self.path
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def _handle_error(self, error):
        """处理请求处理过程中的错误"""
        self.send_response(500)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        response = {
            "status": "error",
            "error": str(error),
            "path": self.path
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))
    
    def log_message(self, format, *args):
        """自定义日志记录"""
        logger.info("%s - %s", self.address_string(), format % args)


def run_server(host='0.0.0.0', port=8088):
    """运行HTTP服务器"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DashboardHTTPHandler)
    
    logger.info(f"启动简化版数据仪表板服务器于 http://{host}:{port}/")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="简化版数据仪表板服务器")
    parser.add_argument("-p", "--port", type=int, default=8088, help="服务器端口号")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    
    args = parser.parse_args()
    
    # 运行服务器
    run_server(host=args.host, port=args.port) 