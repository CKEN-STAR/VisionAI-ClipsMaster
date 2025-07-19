#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
历史数据可视化仪表盘

为VisionAI-ClipsMaster提供历史性能数据可视化界面，展示内存趋势、缓存性能和OOM风险分析。
"""

import os
import sys
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
        QPushButton, QComboBox, QSizePolicy, QGroupBox, QTableWidget,
        QTableWidgetItem, QHeaderView, QProgressBar, QTabWidget,
        QApplication, QMainWindow, QFileDialog, QMessageBox, QSplitter,
        QTextEdit, QDateEdit, QSpinBox
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QDate
    from PyQt6.QtGui import QPixmap, QColor, QPalette, QFont, QIcon
    import pyqtgraph as pg
    HAS_QT = True
except ImportError:
    HAS_QT = False
    logging.warning("PyQt6 或 pyqtgraph 未安装，可视化仪表盘将不可用")

# 导入历史分析模块
from src.monitor.history_analyzer import (
    get_history_analyzer, analyze_memory_trends, analyze_cache_performance, 
    analyze_oom_risks, generate_daily_report, generate_weekly_report,
    get_latest_reports
)

# 设置日志
logger = logging.getLogger("history_dashboard")


class TrendChart(QWidget):
    """趋势图表组件"""
    
    def __init__(self, title: str, parent=None):
        """初始化趋势图表
        
        Args:
            title: 图表标题
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.setMinimumHeight(250)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题标签
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title_label)
        
        # 创建绘图小部件
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        layout.addWidget(self.plot_widget)
        
        # 初始化曲线
        self.curves = {}
    
    def plot_data(self, data_dict: Dict[str, List], x_key: str, y_keys: List[str], 
                 colors: Optional[Dict[str, tuple]] = None, clear: bool = True):
        """绘制数据
        
        Args:
            data_dict: 数据字典，包含x_key和y_keys指定的键
            x_key: X轴数据的键
            y_keys: Y轴数据的键列表
            colors: 各曲线的颜色，键为y_keys中的元素，值为RGB元组
            clear: 是否清除现有曲线
        """
        if clear:
            self.plot_widget.clear()
            self.curves = {}
            
        if not data_dict or x_key not in data_dict or not data_dict[x_key]:
            return
            
        x_data = data_dict[x_key]
        
        for y_key in y_keys:
            if y_key not in data_dict or not data_dict[y_key]:
                continue
                
            # 获取Y轴数据
            y_data = data_dict[y_key]
            
            # 设置颜色
            color = colors.get(y_key, (0, 0, 0)) if colors else (0, 0, 0)
            
            # 创建曲线
            self.curves[y_key] = self.plot_widget.plot(
                x_data, 
                y_data, 
                name=y_key,
                pen=pg.mkPen(color=color, width=2),
                symbol='o',
                symbolSize=5,
                symbolBrush=color
            )
    
    def add_legend(self, labels: Dict[str, str]):
        """添加图例
        
        Args:
            labels: 曲线标签字典，键为y_keys中的元素，值为显示标签
        """
        legend = self.plot_widget.addLegend()
        
        for curve_key, curve in self.curves.items():
            if curve_key in labels:
                legend.addItem(curve, labels[curve_key])
    
    def set_axes_labels(self, x_label: str, y_label: str):
        """设置坐标轴标签
        
        Args:
            x_label: X轴标签
            y_label: Y轴标签
        """
        self.plot_widget.setLabel('bottom', x_label)
        self.plot_widget.setLabel('left', y_label)


class ReportSummaryWidget(QWidget):
    """报告摘要组件"""
    
    def __init__(self, parent=None):
        """初始化报告摘要组件
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("报告摘要")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title_label)
        
        # 创建网格布局
        grid_layout = QGridLayout()
        
        # 添加指标标签
        metrics = [
            ("峰值内存使用率:", "peak_memory_label", "%"),
            ("平均内存使用率:", "avg_memory_label", "%"),
            ("峰值进程内存:", "peak_process_label", "MB"),
            ("平均进程内存:", "avg_process_label", "MB"),
            ("缓存命中率:", "cache_hit_label", "%"),
            ("内存使用趋势:", "memory_trend_label", ""),
            ("缓存健康状态:", "cache_health_label", ""),
            ("OOM风险等级:", "oom_risk_label", "")
        ]
        
        for i, (label_text, attr_name, unit) in enumerate(metrics):
            # 创建标签
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold;")
            
            # 创建值标签
            value_label = QLabel(f"--{unit}")
            value_label.setStyleSheet("font-size: 11pt;")
            
            # 将标签和值添加到网格
            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(value_label, i, 1)
            
            # 保存值标签的引用
            setattr(self, attr_name, value_label)
        
        layout.addLayout(grid_layout)
        
        # 添加生成报告按钮
        buttons_layout = QHBoxLayout()
        
        self.generate_daily_button = QPushButton("生成日报")
        self.generate_daily_button.clicked.connect(self._generate_daily)
        buttons_layout.addWidget(self.generate_daily_button)
        
        self.generate_weekly_button = QPushButton("生成周报")
        self.generate_weekly_button.clicked.connect(self._generate_weekly)
        buttons_layout.addWidget(self.generate_weekly_button)
        
        layout.addLayout(buttons_layout)
        
        # 添加最新报告列表
        self.reports_list = QTableWidget()
        self.reports_list.setColumnCount(3)
        self.reports_list.setHorizontalHeaderLabels(["类型", "日期", "操作"])
        
        # 调整列宽
        header = self.reports_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.reports_list)
        
        # 更新最新报告列表
        self._update_reports_list()
    
    def update_summary(self, memory_data: Dict[str, Any], cache_data: Dict[str, Any], oom_data: Dict[str, Any]):
        """更新报告摘要
        
        Args:
            memory_data: 内存分析数据
            cache_data: 缓存分析数据
            oom_data: OOM风险分析数据
        """
        # 更新内存指标
        mem_data = memory_data.get("data", {})
        self.peak_memory_label.setText(f"{mem_data.get('peak_memory_percent', 0):.1f}%")
        self.avg_memory_label.setText(f"{mem_data.get('avg_memory_percent', 0):.1f}%")
        self.peak_process_label.setText(f"{mem_data.get('peak_process_memory_mb', 0):.1f} MB")
        self.avg_process_label.setText(f"{mem_data.get('avg_process_memory_mb', 0):.1f} MB")
        
        # 设置趋势颜色
        trend_type = mem_data.get("trend_type", "未知")
        self.memory_trend_label.setText(trend_type)
        
        if trend_type in ["显著上升", "缓慢上升"]:
            self.memory_trend_label.setStyleSheet("color: red;")
        elif trend_type in ["显著下降", "缓慢下降"]:
            self.memory_trend_label.setStyleSheet("color: green;")
        else:
            self.memory_trend_label.setStyleSheet("color: black;")
        
        # 更新缓存指标
        cache_data = cache_data.get("data", {})
        self.cache_hit_label.setText(f"{cache_data.get('avg_hit_rate', 0):.1f}%")
        
        # 设置缓存健康状态
        cache_health = cache_data.get("cache_health", {})
        health_status = cache_health.get("status", "未知")
        self.cache_health_label.setText(health_status)
        
        if health_status in ["优秀", "良好"]:
            self.cache_health_label.setStyleSheet("color: green;")
        elif health_status == "一般":
            self.cache_health_label.setStyleSheet("color: orange;")
        elif health_status in ["较差", "很差"]:
            self.cache_health_label.setStyleSheet("color: red;")
        else:
            self.cache_health_label.setStyleSheet("color: black;")
        
        # 更新OOM风险
        oom_data = oom_data.get("data", {})
        risk_level = oom_data.get("overall_risk", "未知")
        self.oom_risk_label.setText(risk_level)
        
        if risk_level in ["高", "中高"]:
            self.oom_risk_label.setStyleSheet("color: red;")
        elif risk_level == "中":
            self.oom_risk_label.setStyleSheet("color: orange;")
        elif risk_level == "低":
            self.oom_risk_label.setStyleSheet("color: green;")
        else:
            self.oom_risk_label.setStyleSheet("color: black;")
    
    def _update_reports_list(self):
        """更新最新报告列表"""
        try:
            # 获取最新报告
            reports = get_latest_reports(limit=5)
            
            # 清空表格
            self.reports_list.setRowCount(0)
            
            # 添加报告
            for i, report in enumerate(reports):
                self.reports_list.insertRow(i)
                
                # 报告类型
                report_type = "日报" if "daily" in report.get('file_name', '') else "周报"
                self.reports_list.setItem(i, 0, QTableWidgetItem(report_type))
                
                # 报告日期
                date_str = report.get('datetime', '').split('T')[0]
                self.reports_list.setItem(i, 1, QTableWidgetItem(date_str))
                
                # 操作按钮
                view_button = QPushButton("查看")
                view_button.setProperty("report_path", report.get('file_path'))
                view_button.clicked.connect(self._view_report)
                
                self.reports_list.setCellWidget(i, 2, view_button)
                
        except Exception as e:
            logger.error(f"更新报告列表失败: {e}")
    
    def _generate_daily(self):
        """生成日报"""
        try:
            # 显示进度对话框
            QMessageBox.information(self, "生成报告", "正在生成每日报告，请稍候...")
            
            # 生成报告
            report = generate_daily_report()
            
            # 提示成功
            QMessageBox.information(self, "生成成功", "每日报告生成成功！")
            
            # 更新报告列表
            self._update_reports_list()
            
        except Exception as e:
            logger.error(f"生成日报失败: {e}")
            QMessageBox.critical(self, "生成失败", f"生成日报失败: {str(e)}")
    
    def _generate_weekly(self):
        """生成周报"""
        try:
            # 显示进度对话框
            QMessageBox.information(self, "生成报告", "正在生成每周报告，请稍候...")
            
            # 生成报告
            report = generate_weekly_report()
            
            # 提示成功
            QMessageBox.information(self, "生成成功", "每周报告生成成功！")
            
            # 更新报告列表
            self._update_reports_list()
            
        except Exception as e:
            logger.error(f"生成周报失败: {e}")
            QMessageBox.critical(self, "生成失败", f"生成周报失败: {str(e)}")
    
    def _view_report(self):
        """查看报告"""
        # 获取报告路径
        sender = self.sender()
        if not sender:
            return
            
        report_path = sender.property("report_path")
        if not report_path or not os.path.exists(report_path):
            QMessageBox.warning(self, "查看失败", "报告文件不存在")
            return
            
        try:
            # 读取报告
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
                
            # 创建查看对话框
            dialog = QMainWindow(self)
            dialog.setWindowTitle(f"查看报告 - {os.path.basename(report_path)}")
            dialog.resize(800, 600)
            
            # 创建文本框
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(json.dumps(report_data, indent=2, ensure_ascii=False))
            
            dialog.setCentralWidget(text_edit)
            dialog.show()
            
        except Exception as e:
            logger.error(f"查看报告失败: {e}")
            QMessageBox.critical(self, "查看失败", f"查看报告失败: {str(e)}")


class RecommendationsWidget(QWidget):
    """建议组件"""
    
    def __init__(self, parent=None):
        """初始化建议组件
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("系统优化建议")
        title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title_label)
        
        # 创建内容部分
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.content.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: Arial, sans-serif;
            }
        """)
        layout.addWidget(self.content)
    
    def update_recommendations(self, memory_data: Dict[str, Any], cache_data: Dict[str, Any], oom_data: Dict[str, Any]):
        """更新建议内容
        
        Args:
            memory_data: 内存分析数据
            cache_data: 缓存分析数据
            oom_data: OOM风险分析数据
        """
        html_content = []
        
        # 添加标题
        html_content.append("<h2>系统优化建议</h2>")
        
        # 1. 内存建议
        html_content.append("<h3>内存使用</h3>")
        
        mem_data = memory_data.get("data", {})
        trend_type = mem_data.get("trend_type", "")
        predicted_30d = mem_data.get("predicted_usage_30d", 0)
        
        if trend_type in ["显著上升", "缓慢上升"] and predicted_30d > 90:
            html_content.append(f"""
            <p style="color: red;">
                <b>警告：</b> 内存使用呈{trend_type}趋势，预计30天后将达到{predicted_30d:.1f}%，
                存在潜在的内存泄漏风险。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>定期重启应用以释放内存</li>
                <li>检查可能的内存泄漏源</li>
                <li>考虑增加系统内存</li>
            </ul>
            """)
        elif mem_data.get("peak_memory_percent", 0) > 90:
            html_content.append(f"""
            <p style="color: orange;">
                <b>注意：</b> 峰值内存使用率达到{mem_data.get('peak_memory_percent', 0):.1f}%，
                接近系统限制。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>监控内存使用，避免长时间运行</li>
                <li>关闭不必要的应用程序</li>
                <li>优化模型加载策略</li>
            </ul>
            """)
        else:
            html_content.append(f"""
            <p style="color: green;">
                <b>良好：</b> 内存使用趋势为{trend_type}，
                峰值使用率为{mem_data.get('peak_memory_percent', 0):.1f}%，
                平均使用率为{mem_data.get('avg_memory_percent', 0):.1f}%。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>保持当前内存配置</li>
            </ul>
            """)
        
        # 2. 缓存建议
        html_content.append("<h3>缓存性能</h3>")
        
        cache_data = cache_data.get("data", {})
        cache_health = cache_data.get("cache_health", {})
        health_score = cache_health.get("score", 0)
        
        if health_score < 60:
            html_content.append(f"""
            <p style="color: red;">
                <b>问题：</b> 缓存健康评分为{health_score}，状态为"{cache_health.get('status', '')}"，
                命中率为{cache_data.get('avg_hit_rate', 0):.1f}%。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>优化缓存预热策略</li>
                <li>增加常用分片的缓存优先级</li>
                <li>调整缓存大小</li>
            </ul>
            """)
        elif health_score < 75:
            html_content.append(f"""
            <p style="color: orange;">
                <b>一般：</b> 缓存健康评分为{health_score}，状态为"{cache_health.get('status', '')}"，
                命中率为{cache_data.get('avg_hit_rate', 0):.1f}%。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>分析访问模式，优化缓存策略</li>
                <li>监控缓存驱逐率</li>
            </ul>
            """)
        else:
            html_content.append(f"""
            <p style="color: green;">
                <b>良好：</b> 缓存健康评分为{health_score}，状态为"{cache_health.get('status', '')}"，
                命中率为{cache_data.get('avg_hit_rate', 0):.1f}%。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>保持当前缓存配置</li>
            </ul>
            """)
        
        # 3. OOM风险建议
        html_content.append("<h3>OOM风险</h3>")
        
        oom_data = oom_data.get("data", {})
        risk_level = oom_data.get("overall_risk", "")
        
        if risk_level in ["高", "中高"]:
            # 添加详细预测
            predictions = oom_data.get("predictions", [])
            prediction_html = ""
            
            for pred in predictions:
                if pred.get("risk_level") in ["高", "中高"]:
                    prediction_html += f"""
                    <li>
                        <b>{pred.get('reason')}</b><br/>
                        建议：{pred.get('recommendation')}
                    </li>
                    """
            
            html_content.append(f"""
            <p style="color: red;">
                <b>警告：</b> OOM风险等级为{risk_level}，
                过去有{oom_data.get('warning_count', 0)}次警告、
                {oom_data.get('error_count', 0)}次错误和
                {oom_data.get('critical_count', 0)}次严重预警。
            </p>
            <p><b>详细分析：</b></p>
            <ul>
                {prediction_html}
            </ul>
            """)
        elif risk_level == "中":
            html_content.append(f"""
            <p style="color: orange;">
                <b>注意：</b> OOM风险等级为{risk_level}，
                过去有{oom_data.get('warning_count', 0)}次警告、
                {oom_data.get('error_count', 0)}次错误预警。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>监控内存使用，避免长时间运行</li>
                <li>使用更强的量化策略减少内存占用</li>
            </ul>
            """)
        else:
            html_content.append(f"""
            <p style="color: green;">
                <b>良好：</b> OOM风险等级为{risk_level}，
                系统运行稳定。
            </p>
            <p><b>建议：</b></p>
            <ul>
                <li>保持当前配置</li>
            </ul>
            """)
        
        # 4. 综合建议
        html_content.append("<h3>综合建议</h3>")
        
        if risk_level in ["高", "中高"] or health_score < 60 or predicted_30d > 90:
            html_content.append("""
            <p><b>系统配置建议：</b></p>
            <ol>
                <li>考虑增加系统内存至8GB</li>
                <li>使用更强的量化策略减少模型内存占用</li>
                <li>优化缓存配置，提高命中率</li>
                <li>定期重启应用以释放内存</li>
                <li>使用自动清理功能，释放长时间未使用的资源</li>
            </ol>
            """)
        else:
            html_content.append("""
            <p><b>系统配置建议：</b></p>
            <ol>
                <li>当前配置适合正常运行</li>
                <li>保持定期监控系统资源使用情况</li>
                <li>根据实际使用场景，考虑调整缓存大小</li>
            </ol>
            """)
        
        # 设置内容
        self.content.setHtml("".join(html_content))


class HistoryDashboard(QWidget):
    """历史数据可视化仪表盘"""
    
    def __init__(self, parent=None):
        """初始化仪表盘
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置窗口标题和大小
        self.setWindowTitle("历史数据分析仪表盘")
        self.resize(1000, 700)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化数据
        self.days_to_analyze = 7
        
        # 更新数据
        self.update_dashboard()
        
        # 自动更新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(3600000)  # 每小时更新一次
        
        logger.info("历史数据分析仪表盘初始化完成")
    
    def init_ui(self):
        """初始化UI界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建顶部控制区域
        control_layout = QHBoxLayout()
        
        # 分析天数选择
        days_label = QLabel("分析天数:")
        self.days_combo = QComboBox()
        self.days_combo.addItems(["1天", "3天", "7天", "14天", "30天"])
        self.days_combo.setCurrentIndex(2)  # 默认7天
        self.days_combo.currentIndexChanged.connect(self._on_days_changed)
        
        control_layout.addWidget(days_label)
        control_layout.addWidget(self.days_combo)
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.update_dashboard)
        control_layout.addWidget(self.refresh_button)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板：图表区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 内存趋势图
        self.memory_chart = TrendChart("内存使用趋势")
        left_layout.addWidget(self.memory_chart)
        
        # 缓存命中率图
        self.cache_chart = TrendChart("缓存命中率趋势")
        left_layout.addWidget(self.cache_chart)
        
        splitter.addWidget(left_panel)
        
        # 右侧面板：摘要和建议
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 报告摘要
        self.summary_widget = ReportSummaryWidget()
        right_layout.addWidget(self.summary_widget)
        
        # 建议
        self.recommendations_widget = RecommendationsWidget()
        right_layout.addWidget(self.recommendations_widget)
        
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        main_layout.addWidget(self.status_label)
    
    def _on_days_changed(self):
        """天数选择变化时的处理"""
        # 获取当前选择的天数
        index = self.days_combo.currentIndex()
        days_map = {0: 1, 1: 3, 2: 7, 3: 14, 4: 30}
        self.days_to_analyze = days_map.get(index, 7)
        
        # 更新仪表盘
        self.update_dashboard()
    
    def update_dashboard(self):
        """更新仪表盘数据"""
        self.status_label.setText("正在更新数据...")
        QApplication.processEvents()
        
        try:
            # 获取分析数据
            memory_data = analyze_memory_trends(self.days_to_analyze)
            cache_data = analyze_cache_performance(self.days_to_analyze)
            oom_data = analyze_oom_risks(self.days_to_analyze)
            
            # 更新内存趋势图
            self._update_memory_chart(memory_data)
            
            # 更新缓存命中率图
            self._update_cache_chart(cache_data)
            
            # 更新报告摘要
            self.summary_widget.update_summary(memory_data, cache_data, oom_data)
            
            # 更新建议
            self.recommendations_widget.update_recommendations(memory_data, cache_data, oom_data)
            
            # 更新状态
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.status_label.setText(f"数据已更新 ({now})")
            
        except Exception as e:
            logger.error(f"更新仪表盘失败: {e}")
            self.status_label.setText(f"更新失败: {str(e)}")
    
    def _update_memory_chart(self, memory_data: Dict[str, Any]):
        """更新内存趋势图
        
        Args:
            memory_data: 内存分析数据
        """
        try:
            daily_data = memory_data.get("data", {}).get("daily_data", [])
            
            if not daily_data:
                return
                
            # 准备数据
            dates = []
            peak_memory = []
            avg_memory = []
            
            for item in daily_data:
                dates.append(item.get("date"))
                peak_memory.append(item.get("memory_percent_max", 0))
                avg_memory.append(item.get("memory_percent_mean", 0))
            
            # 准备数据字典
            data_dict = {
                "dates": range(len(dates)),  # X轴使用索引
                "peak_memory": peak_memory,
                "avg_memory": avg_memory
            }
            
            # 颜色设置
            colors = {
                "peak_memory": (255, 0, 0),
                "avg_memory": (0, 0, 255)
            }
            
            # 绘制图表
            self.memory_chart.plot_data(
                data_dict, 
                "dates", 
                ["peak_memory", "avg_memory"],
                colors
            )
            
            # 添加图例
            self.memory_chart.add_legend({
                "peak_memory": "峰值内存使用率",
                "avg_memory": "平均内存使用率"
            })
            
            # 设置坐标轴标签
            self.memory_chart.set_axes_labels("日期", "内存使用率 (%)")
            
            # 设置X轴刻度
            if dates:
                axis = self.memory_chart.plot_widget.getAxis('bottom')
                ticks = [(i, date) for i, date in enumerate(dates)]
                axis.setTicks([ticks])
            
        except Exception as e:
            logger.error(f"更新内存趋势图失败: {e}")
    
    def _update_cache_chart(self, cache_data: Dict[str, Any]):
        """更新缓存命中率图
        
        Args:
            cache_data: 缓存分析数据
        """
        try:
            daily_data = cache_data.get("data", {}).get("daily_data", [])
            
            if not daily_data:
                return
                
            # 准备数据
            dates = []
            hit_rates = []
            
            for item in daily_data:
                dates.append(item.get("date"))
                hit_rates.append(item.get("hit_rate_mean", 0))
            
            # 准备数据字典
            data_dict = {
                "dates": range(len(dates)),  # X轴使用索引
                "hit_rates": hit_rates
            }
            
            # 颜色设置
            colors = {
                "hit_rates": (0, 128, 0)
            }
            
            # 绘制图表
            self.cache_chart.plot_data(
                data_dict, 
                "dates", 
                ["hit_rates"],
                colors
            )
            
            # 添加图例
            self.cache_chart.add_legend({
                "hit_rates": "缓存命中率"
            })
            
            # 设置坐标轴标签
            self.cache_chart.set_axes_labels("日期", "命中率 (%)")
            
            # 设置X轴刻度
            if dates:
                axis = self.cache_chart.plot_widget.getAxis('bottom')
                ticks = [(i, date) for i, date in enumerate(dates)]
                axis.setTicks([ticks])
            
        except Exception as e:
            logger.error(f"更新缓存命中率图失败: {e}")


def run_dashboard():
    """运行历史数据可视化仪表盘"""
    if not HAS_QT:
        logger.error("缺少PyQt6或pyqtgraph，无法启动仪表盘")
        return
    
    app = QApplication([])
    dashboard = HistoryDashboard()
    dashboard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行仪表盘
    run_dashboard() 