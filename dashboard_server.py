#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多维度数据源服务器

提供HTTP API接口访问多维度数据源，展示系统资源使用情况、
模型性能指标和混沌测试结果。适合在4GB RAM环境中运行。
"""

import os
import sys
import json
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard_server")

# 强制使用模拟模式
USE_MOCK = True

# 导入模拟数据处理函数
from test_data_integration import (
    mock_api_handler as api_handler,
    MockDataAggregator as DataAggregator,
    fetch_mock_data_sources_status as fetch_data_sources_status
)
logger.info("使用模拟数据源")

class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """处理HTTP请求的处理器"""
    
    # 设置跨域头
    def _set_cors_headers(self):
        """设置CORS头，允许跨域访问"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def _set_json_headers(self):
        """设置JSON响应头"""
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._set_cors_headers()
        self.end_headers()
    
    def _set_text_headers(self):
        """设置纯文本响应头"""
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self._set_cors_headers()
        self.end_headers()
    
    def _set_html_headers(self):
        """设置HTML响应头"""
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._set_cors_headers()
        self.end_headers()
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        # 解析URL
        url = urlparse(self.path)
        path = url.path
        
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
        elif path == "/api/system/report":
            self._handle_system_report()
        elif path == "/api/cache/metrics":
            self._handle_cache_metrics()
        elif path == "/api/models/metrics":
            self._handle_model_metrics()
        else:
            self._handle_not_found()
    
    def _handle_index(self):
        """处理根路径请求，返回简单HTML页面"""
        self.send_response(200)
        self._set_html_headers()
        
        # 简单的HTML页面，展示API信息
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VisionAI-ClipsMaster 数据仪表板</title>
    <style>
        body { font-family: "Segoe UI", Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; }
        .endpoint { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .endpoint h3 { margin-top: 0; color: #0066cc; }
        .endpoint .path { font-family: monospace; background-color: #f8f9fa; padding: 5px; border-radius: 3px; }
        .endpoint .desc { margin-top: 10px; }
        h1 { color: #333; }
        h2 { color: #0066cc; margin-top: 30px; }
        .status { margin-top: 20px; padding: 10px; border-radius: 4px; }
        .status-ok { background-color: #d4edda; color: #155724; }
        .status-warning { background-color: #fff3cd; color: #856404; }
        .status-error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>VisionAI-ClipsMaster 数据仪表板 API</h1>
        
        <div class="status status-ok">
            服务状态: 运行中 ("""
        
        html += "模拟模式" if USE_MOCK else "实际模式"
        
        html += """)</div>
        
        <h2>API 端点</h2>
        
        <div class="endpoint">
            <h3>数据源状态</h3>
            <div class="path">GET /api/data_sources</div>
            <div class="desc">获取所有数据源的连接状态</div>
        </div>
        
        <div class="endpoint">
            <h3>数据源详情</h3>
            <div class="path">GET /api/source/{source_name}</div>
            <div class="desc">获取特定数据源的详细数据</div>
        </div>
        
        <div class="endpoint">
            <h3>系统状态</h3>
            <div class="path">GET /api/system/status</div>
            <div class="desc">获取系统健康状态</div>
        </div>
        
        <div class="endpoint">
            <h3>系统报告</h3>
            <div class="path">GET /api/system/report</div>
            <div class="desc">获取完整系统报告</div>
        </div>
        
        <div class="endpoint">
            <h3>缓存指标</h3>
            <div class="path">GET /api/cache/metrics</div>
            <div class="desc">获取缓存性能指标</div>
        </div>
        
        <div class="endpoint">
            <h3>模型指标</h3>
            <div class="path">GET /api/models/metrics</div>
            <div class="desc">获取模型性能指标</div>
        </div>
        
        <div class="endpoint">
            <h3>健康检查</h3>
            <div class="path">GET /health</div>
            <div class="desc">检查服务是否正常运行</div>
        </div>
    </div>
    
    <script>
        // 实时更新状态信息
        function updateStatus() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.querySelector('.status');
                    statusDiv.innerHTML = `服务状态: ${data.status} (""" + ("模拟模式" if USE_MOCK else "实际模式") + """)`;
                    
                    if (data.status === 'ok') {
                        statusDiv.className = 'status status-ok';
                    } else if (data.status === 'warning') {
                        statusDiv.className = 'status status-warning';
                    } else {
                        statusDiv.className = 'status status-error';
                    }
                })
                .catch(error => {
                    console.error('更新状态失败:', error);
                    const statusDiv = document.querySelector('.status');
                    statusDiv.innerHTML = '服务状态: 连接错误';
                    statusDiv.className = 'status status-error';
                });
        }
        
        // 每30秒更新一次状态
        setInterval(updateStatus, 30000);
    </script>
</body>
</html>
"""
        self.wfile.write(html.encode('utf-8'))
    
    def _handle_health(self):
        """处理健康检查请求"""
        self.send_response(200)
        self._set_json_headers()
        
        response = {
            "status": "ok",
            "timestamp": time.time(),
            "mock": USE_MOCK
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_data_sources(self):
        """处理数据源状态请求"""
        self.send_response(200)
        self._set_json_headers()
        
        # 获取数据源状态
        response = api_handler("/data_sources")
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_source_data(self, source_name):
        """处理特定数据源数据请求"""
        self.send_response(200)
        self._set_json_headers()
        
        # 获取数据源数据
        response = api_handler(f"/source/{source_name}")
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_system_status(self):
        """处理系统状态请求"""
        self.send_response(200)
        self._set_json_headers()
        
        # 获取系统状态
        response = api_handler("/system/status")
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_system_report(self):
        """处理系统报告请求"""
        self.send_response(200)
        self._set_json_headers()
        
        # 获取系统报告
        response = api_handler("/system/report")
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_cache_metrics(self):
        """处理缓存指标请求"""
        self.send_response(200)
        self._set_json_headers()
        
        # 获取缓存指标
        response = api_handler("/cache/metrics")
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_model_metrics(self):
        """处理模型指标请求"""
        self.send_response(200)
        self._set_json_headers()
        
        # 获取模型指标
        response = api_handler("/models/metrics")
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _handle_not_found(self):
        """处理未找到的路径请求"""
        self.send_response(404)
        self._set_json_headers()
        
        response = {
            "status": "error",
            "error": "未找到请求的路径",
            "path": self.path,
            "timestamp": time.time()
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志记录"""
        # 使用logger而非标准输出
        logger.info("%s - %s", self.address_string(), format % args)


def run_server(host='0.0.0.0', port=8080):
    """运行HTTP服务器"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DashboardHTTPHandler)
    
    logger.info(f"启动数据仪表板服务器于 http://{host}:{port}/")
    logger.info(f"运行模式: {'模拟' if USE_MOCK else '实际'}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    finally:
        httpd.server_close()


def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="VisionAI-ClipsMaster 数据仪表板服务器")
    parser.add_argument("-p", "--port", type=int, default=8080, help="服务器端口号")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址")
    
    args = parser.parse_args()
    
    # 运行服务器
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main() 