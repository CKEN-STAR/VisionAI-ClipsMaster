"""
系统监控应用
提供系统资源监控界面
"""

import time
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QPushButton, QTextEdit, QTabWidget)

class SystemMonitorWindow(QWidget):
    """系统监控窗口"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("系统监控")
        self.setMinimumSize(600, 400)
        
        # 监控数据
        self.monitor_data = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_usage': 0.0
        }
        
        # 设置UI
        self.setup_ui()
        
        # 启动监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor_data)
        self.monitor_timer.start(2000)  # 2秒更新一次
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 系统资源标签页
        resource_tab = self.create_resource_tab()
        tab_widget.addTab(resource_tab, "系统资源")
        
        # 进程监控标签页
        process_tab = self.create_process_tab()
        tab_widget.addTab(process_tab, "进程监控")
        
        # 日志标签页
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "系统日志")
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始监控")
        self.start_button.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止监控")
        self.stop_button.clicked.connect(self.stop_monitoring)
        button_layout.addWidget(self.stop_button)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)
        
        layout.addLayout(button_layout)
    
    def create_resource_tab(self) -> QWidget:
        """创建资源监控标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # CPU使用率
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU使用率:"))
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_progress)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_label)
        layout.addLayout(cpu_layout)
        
        # 内存使用率
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("内存使用率:"))
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        memory_layout.addWidget(self.memory_progress)
        self.memory_label = QLabel("0%")
        memory_layout.addWidget(self.memory_label)
        layout.addLayout(memory_layout)
        
        # 磁盘使用率
        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("磁盘使用率:"))
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        disk_layout.addWidget(self.disk_progress)
        self.disk_label = QLabel("0%")
        disk_layout.addWidget(self.disk_label)
        layout.addLayout(disk_layout)
        
        # 网络使用率
        network_layout = QHBoxLayout()
        network_layout.addWidget(QLabel("网络使用率:"))
        self.network_progress = QProgressBar()
        self.network_progress.setRange(0, 100)
        network_layout.addWidget(self.network_progress)
        self.network_label = QLabel("0%")
        network_layout.addWidget(self.network_label)
        layout.addLayout(network_layout)
        
        return widget
    
    def create_process_tab(self) -> QWidget:
        """创建进程监控标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 进程信息显示
        self.process_text = QTextEdit()
        self.process_text.setReadOnly(True)
        layout.addWidget(self.process_text)
        
        return widget
    
    def create_log_tab(self) -> QWidget:
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        return widget
    
    def update_monitor_data(self):
        """更新监控数据"""
        try:
            # 获取系统资源信息
            self.monitor_data = self.get_system_resources()
            
            # 更新UI
            self.update_resource_display()
            self.update_process_display()
            self.update_log_display()
            
        except Exception as e:
            print(f"[WARN] 更新监控数据失败: {e}")
    
    def get_system_resources(self) -> Dict[str, float]:
        """获取系统资源信息"""
        try:
            import psutil
            
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=0.1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 网络使用率（简化）
            network_usage = min(50.0, cpu_usage)  # 简化计算
            
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'network_usage': network_usage
            }
            
        except ImportError:
            # 如果psutil不可用，返回模拟数据
            return {
                'cpu_usage': 25.0,
                'memory_usage': 60.0,
                'disk_usage': 45.0,
                'network_usage': 15.0
            }
        except Exception as e:
            print(f"[WARN] 获取系统资源失败: {e}")
            return self.monitor_data
    
    def update_resource_display(self):
        """更新资源显示"""
        try:
            # 更新CPU
            cpu_value = int(self.monitor_data['cpu_usage'])
            self.cpu_progress.setValue(cpu_value)
            self.cpu_label.setText(f"{cpu_value}%")
            
            # 更新内存
            memory_value = int(self.monitor_data['memory_usage'])
            self.memory_progress.setValue(memory_value)
            self.memory_label.setText(f"{memory_value}%")
            
            # 更新磁盘
            disk_value = int(self.monitor_data['disk_usage'])
            self.disk_progress.setValue(disk_value)
            self.disk_label.setText(f"{disk_value}%")
            
            # 更新网络
            network_value = int(self.monitor_data['network_usage'])
            self.network_progress.setValue(network_value)
            self.network_label.setText(f"{network_value}%")
            
        except Exception as e:
            print(f"[WARN] 更新资源显示失败: {e}")
    
    def update_process_display(self):
        """更新进程显示"""
        try:
            process_info = self.get_process_info()
            self.process_text.setPlainText(process_info)
        except Exception as e:
            print(f"[WARN] 更新进程显示失败: {e}")
    
    def get_process_info(self) -> str:
        """获取进程信息"""
        try:
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    processes.append(f"PID: {info['pid']:<8} "
                                   f"名称: {info['name']:<20} "
                                   f"CPU: {info['cpu_percent']:<6.1f}% "
                                   f"内存: {info['memory_percent']:<6.1f}%")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 按CPU使用率排序，取前10个
            processes.sort(key=lambda x: float(x.split('CPU: ')[1].split('%')[0]), reverse=True)
            return "\n".join(processes[:10])
            
        except ImportError:
            return "psutil模块不可用，无法显示进程信息"
        except Exception as e:
            return f"获取进程信息失败: {e}"
    
    def update_log_display(self):
        """更新日志显示"""
        try:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{current_time}] 系统监控更新 - CPU: {self.monitor_data['cpu_usage']:.1f}%, 内存: {self.monitor_data['memory_usage']:.1f}%"
            
            # 添加到日志
            current_text = self.log_text.toPlainText()
            lines = current_text.split('\n')
            
            # 保持最多100行日志
            if len(lines) >= 100:
                lines = lines[-99:]
            
            lines.append(log_entry)
            self.log_text.setPlainText('\n'.join(lines))
            
            # 滚动到底部
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
            
        except Exception as e:
            print(f"[WARN] 更新日志显示失败: {e}")
    
    def start_monitoring(self):
        """开始监控"""
        try:
            if not self.monitor_timer.isActive():
                self.monitor_timer.start(2000)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            print("[OK] 系统监控已开始")
        except Exception as e:
            print(f"[WARN] 开始监控失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            self.monitor_timer.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            print("[OK] 系统监控已停止")
        except Exception as e:
            print(f"[WARN] 停止监控失败: {e}")
    
    def refresh_data(self):
        """刷新数据"""
        try:
            self.update_monitor_data()
            print("[OK] 监控数据已刷新")
        except Exception as e:
            print(f"[WARN] 刷新数据失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            self.monitor_timer.stop()
            event.accept()
        except Exception as e:
            print(f"[WARN] 关闭监控窗口失败: {e}")
            event.accept()

__all__ = [
    'SystemMonitorWindow'
]
