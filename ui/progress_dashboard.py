
# 安全导入包装 - 自动生成
import sys
import os

# 确保PyQt6可用
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    print(f"[WARN] PyQt6不可用，ProgressDashboard将使用fallback模式")

# 线程安全检查
def ensure_main_thread():
    """确保在主线程中执行"""
    if QT_AVAILABLE and QApplication.instance():
        current_thread = QThread.currentThread()
        main_thread = QApplication.instance().thread()
        if current_thread != main_thread:
            print(f"[WARN] ProgressDashboard不在主线程中，可能导致问题")
            return False
    return True

"""
进度看板组件
提供任务进度的可视化监控和管理功能
"""

import time
from typing import Dict, Any, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QGridLayout, QListWidget, QListWidgetItem,
    QTabWidget, QTextEdit, QFrame, QSplitter, QScrollArea
)
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter

try:
    from ui.progress.tracker import ProgressTracker, ProgressInfo
    from ui.components.alert_manager import AlertManager, AlertLevel
    HAS_PROGRESS_TRACKER = True
except ImportError:
    HAS_PROGRESS_TRACKER = False
    print("[WARN] Progress tracker not available, using fallback")

class TaskProgressWidget(QWidget):
    """单个任务进度显示组件"""
    
    def __init__(self, task_id: str, task_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.task_info = task_info
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 任务标题
        title_layout = QHBoxLayout()
        self.title_label = QLabel(self.task_info.get('name', self.task_id))
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_layout.addWidget(self.title_label)
        
        # 状态标签
        self.status_label = QLabel(self.task_info.get('status', 'Unknown'))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_layout.addWidget(self.status_label)
        
        layout.addLayout(title_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(self.task_info.get('progress', 0))
        layout.addWidget(self.progress_bar)
        
        # 详细信息
        info_layout = QHBoxLayout()
        
        # 进度文本
        progress = self.task_info.get('progress', 0)
        self.progress_text = QLabel(f"{progress}%")
        info_layout.addWidget(self.progress_text)
        
        # 预估时间
        eta = self.task_info.get('eta', 0)
        if eta > 0:
            eta_text = self.format_time(eta)
            self.eta_label = QLabel(f"剩余: {eta_text}")
        else:
            self.eta_label = QLabel("剩余: --")
        self.eta_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.eta_label)
        
        layout.addLayout(info_layout)
        
        # 设置样式
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            TaskProgressWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
    
    def update_progress(self, progress: int, status: str = None, eta: float = 0):
        """更新进度"""
        self.progress_bar.setValue(progress)
        self.progress_text.setText(f"{progress}%")
        
        if status:
            self.status_label.setText(status)
            self.task_info['status'] = status
        
        if eta > 0:
            eta_text = self.format_time(eta)
            self.eta_label.setText(f"剩余: {eta_text}")
        else:
            self.eta_label.setText("剩余: --")
        
        # 根据状态更新颜色
        if status == "完成":
            self.setStyleSheet("""
                TaskProgressWidget {
                    border: 1px solid #4CAF50;
                    background-color: #E8F5E8;
                }
            """)
        elif status == "失败":
            self.setStyleSheet("""
                TaskProgressWidget {
                    border: 1px solid #F44336;
                    background-color: #FFEBEE;
                }
            """)
        elif status == "进行中":
            self.setStyleSheet("""
                TaskProgressWidget {
                    border: 1px solid #2196F3;
                    background-color: #E3F2FD;
                }
            """)
    
    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}时{minutes}分"

class ProgressDashboard(QWidget):
    """进度看板主组件"""
    
    # 信号定义
    task_selected = pyqtSignal(str)  # 任务被选中
    task_cancelled = pyqtSignal(str)  # 任务被取消
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_tasks: Dict[str, TaskProgressWidget] = {}
        self.completed_tasks: List[Dict[str, Any]] = []
        self.task_counter = 0
        
        # 初始化组件
        if HAS_PROGRESS_TRACKER:
            self.progress_tracker = ProgressTracker()
            self.progress_tracker.progress_updated.connect(self.on_progress_updated)
            self.progress_tracker.task_completed.connect(self.on_task_completed)
            self.progress_tracker.task_started.connect(self.on_task_started)
        else:
            self.progress_tracker = None
        
        self.init_ui()
        self.setup_timer()

    def setup_ui(self):
        """设置UI界面 - 公共接口方法"""
        # 为了兼容性提供公共接口
        if hasattr(self, '_ui_initialized') and self._ui_initialized:
            print("[INFO] ProgressDashboard UI已经初始化，跳过重复设置")
            return

        self.init_ui()
        self._ui_initialized = True
        print("[OK] ProgressDashboard UI设置完成")

    def show(self):
        """显示进度看板"""
        super().show()
        self.raise_()
        print("[OK] ProgressDashboard已显示")

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("任务进度看板")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        title_layout.addWidget(refresh_btn)
        
        # 清理按钮
        clear_btn = QPushButton("清理完成任务")
        clear_btn.clicked.connect(self.clear_completed_tasks)
        title_layout.addWidget(clear_btn)
        
        layout.addLayout(title_layout)
        
        # 创建标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 活动任务页
        self.active_tab = self._create_active_tasks_tab()
        self.tabs.addTab(self.active_tab, "活动任务")
        
        # 完成任务页
        self.completed_tab = self._create_completed_tasks_tab()
        self.tabs.addTab(self.completed_tab, "完成任务")
        
        # 统计信息页
        self.stats_tab = self._create_stats_tab()
        self.tabs.addTab(self.stats_tab, "统计信息")
    
    def _create_active_tasks_tab(self) -> QWidget:
        """创建活动任务页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 任务概览
        overview_group = QGroupBox("任务概览")
        overview_layout = QGridLayout(overview_group)
        
        overview_layout.addWidget(QLabel("活动任务:"), 0, 0)
        self.active_count_label = QLabel("0")
        overview_layout.addWidget(self.active_count_label, 0, 1)
        
        overview_layout.addWidget(QLabel("总进度:"), 1, 0)
        self.overall_progress = QProgressBar()
        overview_layout.addWidget(self.overall_progress, 1, 1)
        
        layout.addWidget(overview_group)
        
        # 任务列表滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.addStretch()  # 添加弹性空间
        
        scroll_area.setWidget(self.tasks_container)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_completed_tasks_tab(self) -> QWidget:
        """创建完成任务页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 完成任务列表
        self.completed_list = QListWidget()
        layout.addWidget(self.completed_list)
        
        # 详细信息
        details_group = QGroupBox("任务详情")
        details_layout = QVBoxLayout(details_group)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_group)
        
        # 连接信号
        self.completed_list.itemClicked.connect(self.show_task_details)
        
        return tab
    
    def _create_stats_tab(self) -> QWidget:
        """创建统计信息页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 统计信息组
        stats_group = QGroupBox("统计信息")
        stats_layout = QGridLayout(stats_group)
        
        # 任务统计
        stats_layout.addWidget(QLabel("总任务数:"), 0, 0)
        self.total_tasks_label = QLabel("0")
        stats_layout.addWidget(self.total_tasks_label, 0, 1)
        
        stats_layout.addWidget(QLabel("完成任务:"), 1, 0)
        self.completed_tasks_label = QLabel("0")
        stats_layout.addWidget(self.completed_tasks_label, 1, 1)
        
        stats_layout.addWidget(QLabel("成功率:"), 2, 0)
        self.success_rate_label = QLabel("0%")
        stats_layout.addWidget(self.success_rate_label, 2, 1)
        
        stats_layout.addWidget(QLabel("平均完成时间:"), 3, 0)
        self.avg_time_label = QLabel("--")
        stats_layout.addWidget(self.avg_time_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # 性能图表占位符
        chart_group = QGroupBox("性能趋势")
        chart_layout = QVBoxLayout(chart_group)
        
        self.chart_placeholder = QLabel("图表功能开发中...")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_placeholder.setMinimumHeight(200)
        self.chart_placeholder.setStyleSheet("border: 1px dashed #ccc;")
        chart_layout.addWidget(self.chart_placeholder)
        
        layout.addWidget(chart_group)
        
        return tab
    
    def setup_timer(self):
        """设置定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(1000)  # 每秒更新一次
    
    def add_task(self, task_id: str, task_name: str, total_steps: int = 100) -> bool:
        """添加新任务"""
        try:
            if task_id in self.active_tasks:
                return False
            
            task_info = {
                'id': task_id,
                'name': task_name,
                'progress': 0,
                'status': '准备中',
                'start_time': time.time(),
                'total_steps': total_steps,
                'eta': 0
            }
            
            # 创建任务组件
            task_widget = TaskProgressWidget(task_id, task_info, self)
            self.active_tasks[task_id] = task_widget
            
            # 添加到布局（在弹性空间之前）
            self.tasks_layout.insertWidget(self.tasks_layout.count() - 1, task_widget)
            
            # 更新计数
            self.update_task_counts()
            
            # 如果有进度跟踪器，注册任务
            if self.progress_tracker:
                self.progress_tracker.start_task(task_id, total_steps, task_name)
            
            return True
            
        except Exception as e:
            print(f"[WARN] 添加任务失败: {e}")
            return False
    
    def update_task_progress(self, task_id: str, progress: int, status: str = None, message: str = ""):
        """更新任务进度"""
        try:
            if task_id in self.active_tasks:
                task_widget = self.active_tasks[task_id]
                
                # 计算预估时间
                task_info = task_widget.task_info
                if progress > 0 and task_info.get('start_time'):
                    elapsed = time.time() - task_info['start_time']
                    if progress < 100:
                        eta = (elapsed / progress) * (100 - progress)
                    else:
                        eta = 0
                else:
                    eta = 0
                
                task_widget.update_progress(progress, status, eta)
                
                # 更新进度跟踪器
                if self.progress_tracker:
                    self.progress_tracker.update_progress(task_id, progress, message)
                
                # 更新总体进度
                self.update_overall_progress()
                
        except Exception as e:
            print(f"[WARN] 更新任务进度失败: {e}")
    
    def complete_task(self, task_id: str, success: bool = True, result: Dict[str, Any] = None):
        """完成任务"""
        try:
            if task_id in self.active_tasks:
                task_widget = self.active_tasks[task_id]
                task_info = task_widget.task_info.copy()
                
                # 更新任务信息
                task_info['end_time'] = time.time()
                task_info['duration'] = task_info['end_time'] - task_info.get('start_time', 0)
                task_info['success'] = success
                task_info['result'] = result or {}
                
                # 移动到完成列表
                self.completed_tasks.append(task_info)
                
                # 从活动任务中移除
                self.tasks_layout.removeWidget(task_widget)
                task_widget.deleteLater()
                del self.active_tasks[task_id]
                
                # 添加到完成列表UI
                status_text = "成功" if success else "失败"
                duration_text = self.format_duration(task_info['duration'])
                item_text = f"{task_info['name']} - {status_text} ({duration_text})"
                self.completed_list.addItem(item_text)
                
                # 更新计数和统计
                self.update_task_counts()
                self.update_statistics()
                
                # 完成进度跟踪器中的任务
                if self.progress_tracker:
                    self.progress_tracker.complete_task(task_id)
                
        except Exception as e:
            print(f"[WARN] 完成任务失败: {e}")
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        try:
            if task_id in self.active_tasks:
                self.complete_task(task_id, success=False, result={'cancelled': True})
                self.task_cancelled.emit(task_id)
                
        except Exception as e:
            print(f"[WARN] 取消任务失败: {e}")
    
    def update_dashboard(self):
        """更新看板显示"""
        self.update_overall_progress()
        self.update_statistics()
    
    def update_task_counts(self):
        """更新任务计数"""
        active_count = len(self.active_tasks)
        self.active_count_label.setText(str(active_count))
    
    def update_overall_progress(self):
        """更新总体进度"""
        if not self.active_tasks:
            self.overall_progress.setValue(0)
            return
        
        total_progress = sum(
            task.task_info.get('progress', 0) 
            for task in self.active_tasks.values()
        )
        avg_progress = total_progress / len(self.active_tasks)
        self.overall_progress.setValue(int(avg_progress))
    
    def update_statistics(self):
        """更新统计信息"""
        total_tasks = len(self.completed_tasks)
        self.total_tasks_label.setText(str(total_tasks))
        self.completed_tasks_label.setText(str(total_tasks))
        
        if total_tasks > 0:
            # 计算成功率
            successful_tasks = sum(1 for task in self.completed_tasks if task.get('success', False))
            success_rate = (successful_tasks / total_tasks) * 100
            self.success_rate_label.setText(f"{success_rate:.1f}%")
            
            # 计算平均完成时间
            total_duration = sum(task.get('duration', 0) for task in self.completed_tasks)
            avg_duration = total_duration / total_tasks
            self.avg_time_label.setText(self.format_duration(avg_duration))
        else:
            self.success_rate_label.setText("0%")
            self.avg_time_label.setText("--")
    
    def format_duration(self, seconds: float) -> str:
        """格式化持续时间"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}时{minutes}分"
    
    def show_task_details(self, item: QListWidgetItem):
        """显示任务详情"""
        try:
            row = self.completed_list.row(item)
            if 0 <= row < len(self.completed_tasks):
                task_info = self.completed_tasks[row]
                
                details = f"""
任务名称: {task_info.get('name', 'Unknown')}
任务ID: {task_info.get('id', 'Unknown')}
开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task_info.get('start_time', 0)))}
结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task_info.get('end_time', 0)))}
持续时间: {self.format_duration(task_info.get('duration', 0))}
状态: {'成功' if task_info.get('success', False) else '失败'}
结果: {task_info.get('result', {})}
                """.strip()
                
                self.details_text.setText(details)
                
        except Exception as e:
            print(f"[WARN] 显示任务详情失败: {e}")
    
    def refresh_dashboard(self):
        """刷新看板"""
        self.update_dashboard()
        print("[INFO] 进度看板已刷新")
    
    def clear_completed_tasks(self):
        """清理完成的任务"""
        self.completed_tasks.clear()
        self.completed_list.clear()
        self.details_text.clear()
        self.update_statistics()
        print("[INFO] 已清理完成的任务")
    
    # 进度跟踪器信号处理
    def on_progress_updated(self, task_id: str, current: int, total: int, message: str):
        """处理进度更新信号"""
        if total > 0:
            progress = int((current / total) * 100)
            self.update_task_progress(task_id, progress, "进行中", message)
    
    def on_task_completed(self, task_id: str):
        """处理任务完成信号"""
        self.complete_task(task_id, success=True)
    
    def on_task_started(self, task_id: str, message: str):
        """处理任务开始信号"""
        if task_id not in self.active_tasks:
            self.add_task(task_id, message)

# 全局实例
_progress_dashboard = None

def get_progress_dashboard():
    """获取进度仪表板实例"""
    global _progress_dashboard
    if _progress_dashboard is None:
        _progress_dashboard = ProgressDashboard()
    return _progress_dashboard

__all__ = ['ProgressDashboard', 'TaskProgressWidget', 'get_progress_dashboard']
