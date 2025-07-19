#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 内存压力可视化模块
提供内存压力趋势的实时可视化功能
"""

import time
import threading
import logging
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO
import base64

# 导入压力检测器
from src.fuse.pressure_detector import get_pressure_detector
from src.fuse.integration import get_integration_manager
from src.memory.fuse_manager import FuseLevel

# 设置日志
logger = logging.getLogger("memory_visualization")

class PressureVisualizer:
    """内存压力可视化工具，提供实时图表和导出功能"""
    
    def __init__(self):
        """初始化可视化工具"""
        self._pressure_detector = get_pressure_detector()
        self._integration_manager = get_integration_manager()
        
        # 图表数据
        self._history: List[float] = []
        self._timestamps: List[float] = []
        self._start_time = time.time()
        
        # 锁
        self._lock = threading.RLock()
        
        # 主题颜色
        self._colors = {
            "background": "#f8f9fa",
            "grid": "#dcdcdc",
            "normal": "#4CAF50",
            "warning": "#FFC107",
            "critical": "#FF5722",
            "emergency": "#F44336",
            "text": "#333333",
            "trend": "#2196F3"
        }
        
        logger.info("内存压力可视化工具初始化完成")
    
    def update_data(self, window_seconds: int = 600) -> None:
        """
        更新图表数据
        
        Args:
            window_seconds: 保留数据的时间窗口（秒）
        """
        with self._lock:
            # 获取当前压力和时间
            current_time = time.time()
            current_pressure = self._pressure_detector.get_current_pressure()
            
            # 追加数据
            self._history.append(current_pressure)
            self._timestamps.append(current_time)
            
            # 删除超出窗口的旧数据
            cutoff_time = current_time - window_seconds
            while self._timestamps and self._timestamps[0] < cutoff_time:
                self._timestamps.pop(0)
                self._history.pop(0)
    
    def generate_figure(
        self,
        width: int = 800,
        height: int = 400,
        dark_mode: bool = False
    ) -> Figure:
        """
        生成图表
        
        Args:
            width: 图表宽度（像素）
            height: 图表高度（像素）
            dark_mode: 是否使用暗色模式
            
        Returns:
            Matplotlib图表对象
        """
        with self._lock:
            # 调整颜色主题
            if dark_mode:
                self._colors.update({
                    "background": "#212121",
                    "grid": "#424242",
                    "text": "#f5f5f5"
                })
            
            # 创建图表
            fig = plt.figure(figsize=(width/100, height/100), dpi=100)
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            
            # 设置背景色
            fig.patch.set_facecolor(self._colors["background"])
            ax.set_facecolor(self._colors["background"])
            
            # 如果没有数据，显示空图表
            if not self._history:
                ax.text(
                    0.5, 0.5,
                    "无数据",
                    ha='center',
                    va='center',
                    fontsize=14,
                    color=self._colors["text"]
                )
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                return fig
            
            # 计算相对时间（秒）
            relative_times = [t - self._start_time for t in self._timestamps]
            
            # 绘制压力曲线
            ax.plot(
                relative_times,
                self._history,
                linewidth=2,
                color=self._colors["normal"]
            )
            
            # 获取压力阈值
            status = self._integration_manager.get_status()
            thresholds = status.get("pressure_thresholds", {})
            
            # 绘制阈值线
            if "WARNING" in thresholds:
                ax.axhline(
                    y=thresholds["WARNING"],
                    color=self._colors["warning"],
                    linestyle='--',
                    alpha=0.7,
                    label=f"警告阈值 ({thresholds['WARNING']}%)"
                )
            
            if "CRITICAL" in thresholds:
                ax.axhline(
                    y=thresholds["CRITICAL"],
                    color=self._colors["critical"],
                    linestyle='--',
                    alpha=0.7,
                    label=f"临界阈值 ({thresholds['CRITICAL']}%)"
                )
            
            if "EMERGENCY" in thresholds:
                ax.axhline(
                    y=thresholds["EMERGENCY"],
                    color=self._colors["emergency"],
                    linestyle='--',
                    alpha=0.7,
                    label=f"紧急阈值 ({thresholds['EMERGENCY']}%)"
                )
            
            # 绘制趋势线
            if len(self._history) > 5:
                x = np.array(relative_times)
                y = np.array(self._history)
                
                # 计算趋势线
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                # 绘制趋势线
                trend_x = np.array([min(x), max(x) + (max(x) - min(x))*0.2])
                trend_y = p(trend_x)
                
                ax.plot(
                    trend_x,
                    trend_y,
                    'k--',
                    color=self._colors["trend"],
                    alpha=0.7,
                    label=f"趋势 ({z[0]:.2f}/s)"
                )
                
                # 显示预测点
                if status.get("prediction_enabled", False):
                    future_time = max(x) + 30  # 预测30秒后
                    future_pressure = p(future_time)
                    
                    if 0 <= future_pressure <= 100:
                        ax.plot(
                            future_time,
                            future_pressure,
                            'o',
                            color=self._colors["trend"],
                            markersize=8,
                            label=f"预测 ({future_pressure:.1f}%)"
                        )
            
            # 设置标题和标签
            current_level = status.get("current_fuse_level", "NORMAL")
            level_colors = {
                "NORMAL": self._colors["normal"],
                "WARNING": self._colors["warning"],
                "CRITICAL": self._colors["critical"],
                "EMERGENCY": self._colors["emergency"]
            }
            
            title_color = level_colors.get(current_level, self._colors["text"])
            
            ax.set_title(
                f"内存压力指数 - 当前: {self._history[-1]:.1f}% ({current_level})",
                fontsize=14,
                color=title_color
            )
            
            ax.set_xlabel("时间 (秒)", fontsize=12, color=self._colors["text"])
            ax.set_ylabel("压力指数", fontsize=12, color=self._colors["text"])
            
            # 设置网格
            ax.grid(True, color=self._colors["grid"], linestyle='-', linewidth=0.5, alpha=0.5)
            
            # 设置刻度标签颜色
            ax.tick_params(axis='x', colors=self._colors["text"])
            ax.tick_params(axis='y', colors=self._colors["text"])
            
            # 设置Y轴范围
            ax.set_ylim(0, 100)
            
            # 显示图例
            ax.legend(loc='upper left', framealpha=0.7, facecolor=self._colors["background"])
            
            # 添加当前状态说明
            status_text = [
                f"当前状态: {current_level}",
                f"预测功能: {'开启' if status.get('prediction_enabled', False) else '关闭'}",
                f"自动触发: {'开启' if status.get('auto_trigger_enabled', False) else '关闭'}"
            ]
            
            status_str = '\n'.join(status_text)
            ax.text(
                0.02, 0.05,
                status_str,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor=self._colors["background"], alpha=0.8, 
                          edgecolor=title_color, pad=0.5)
            )
            
            fig.tight_layout()
            return fig
    
    def get_image_base64(
        self,
        width: int = 800,
        height: int = 400,
        dark_mode: bool = False,
        image_format: str = 'png'
    ) -> str:
        """
        获取图表的Base64编码
        
        Args:
            width: 图表宽度（像素）
            height: 图表高度（像素）
            dark_mode: 是否使用暗色模式
            image_format: 图像格式（png或jpg）
            
        Returns:
            Base64编码的图像
        """
        # 更新数据
        self.update_data()
        
        # 生成图表
        fig = self.generate_figure(width, height, dark_mode)
        
        # 转换为图像
        buf = BytesIO()
        fig.savefig(buf, format=image_format, dpi=100, 
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        
        # 转为Base64
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_base64
    
    def save_image(
        self,
        filename: str,
        width: int = 1200,
        height: int = 600,
        dark_mode: bool = False
    ) -> bool:
        """
        保存图表为图像文件
        
        Args:
            filename: 文件名
            width: 图表宽度（像素）
            height: 图表高度（像素）
            dark_mode: 是否使用暗色模式
            
        Returns:
            是否保存成功
        """
        try:
            # 更新数据
            self.update_data()
            
            # 生成图表
            fig = self.generate_figure(width, height, dark_mode)
            
            # 保存图表
            fig.savefig(filename, dpi=100, facecolor=fig.get_facecolor())
            plt.close(fig)
            
            logger.info(f"内存压力图表已保存到: {filename}")
            return True
        except Exception as e:
            logger.error(f"保存内存压力图表失败: {str(e)}")
            return False
    
    def generate_html(
        self,
        width: int = 800,
        height: int = 400,
        dark_mode: bool = False,
        refresh_interval: int = 5
    ) -> str:
        """
        生成HTML页面用于嵌入Web界面
        
        Args:
            width: 图表宽度（像素）
            height: 图表高度（像素）
            dark_mode: 是否使用暗色模式
            refresh_interval: 自动刷新间隔（秒）
            
        Returns:
            HTML代码
        """
        # 获取图表Base64
        img_base64 = self.get_image_base64(width, height, dark_mode)
        
        # 生成HTML
        bg_color = "#212121" if dark_mode else "#f8f9fa"
        text_color = "#f5f5f5" if dark_mode else "#333333"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="{refresh_interval}">
            <title>VisionAI-ClipsMaster 内存压力监控</title>
            <style>
                body {{ background-color: {bg_color}; color: {text_color}; font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: {width}px; margin: 0 auto; }}
                .title {{ text-align: center; margin-bottom: 20px; }}
                .image-container {{ text-align: center; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; }}
                img {{ max-width: 100%; height: auto; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="title">
                    <h1>VisionAI-ClipsMaster 内存压力监控</h1>
                    <p>实时更新间隔: {refresh_interval}秒 | 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div class="image-container">
                    <img src="data:image/png;base64,{img_base64}" alt="内存压力图表">
                </div>
                <div class="footer">
                    <p>VisionAI-ClipsMaster 内存压力监控系统 | 技术支持: 运行时资源管理团队</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def start_web_server(self, port: int = 8080) -> None:
        """
        启动Web服务器显示实时图表
        
        Args:
            port: Web服务器端口
        """
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler

# 内存使用警告阈值（百分比）
MEMORY_WARNING_THRESHOLD = 80

            
            visualizer = self
            
            class PressureHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    # 默认暗色模式
                    dark_mode = True
                    if '?theme=light' in self.path:
                        dark_mode = False
                    
                    # 生成HTML
                    html = visualizer.generate_html(
                        width=1000,
                        height=500,
                        dark_mode=dark_mode,
                        refresh_interval=5
                    )
                    
                    self.wfile.write(html.encode())
            
            server = HTTPServer(('localhost', port), PressureHandler)
            logger.info(f"内存压力监控Web服务器已启动，访问 http://localhost:{port}/")
            logger.info(f"使用 http://localhost:{port}/?theme=light 切换亮色主题")
            
            # 启动服务器
            server.serve_forever()
            
        except ImportError:
            logger.error("启动Web服务器失败: 缺少http.server模块")
        except Exception as e:
            logger.error(f"启动Web服务器失败: {str(e)}")


# 全局单例
_visualizer = None

def get_pressure_visualizer() -> PressureVisualizer:
    """
    获取压力可视化工具单例
    
    Returns:
        压力可视化工具实例
    """
    global _visualizer
    
    if _visualizer is None:
        _visualizer = PressureVisualizer()
        
    return _visualizer


if __name__ == "__main__":
    # 设置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 初始化集成管理器
    integration_manager = get_integration_manager()
    integration_manager.initialize()
    integration_manager.start()
    
    # 测试可视化
    visualizer = get_pressure_visualizer()
    
    # 更新数据
    for _ in range(60):
        visualizer.update_data()
        time.sleep(0.2)
    
    # 保存图表
    visualizer.save_image("memory_pressure.png", dark_mode=True)
    
    try:
        # 尝试启动Web服务器
        visualizer.start_web_server()
    except KeyboardInterrupt:
        print("停止Web服务器")
    finally:
        # 停止集成系统
        integration_manager.stop() 