#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映导出工作流面板

提供符合剪映导出工作流的用户界面，支持项目导出和审计。
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# 添加项目根目录到PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入相关模块
from src.exporters.xml_template import XMLTemplateProcessor
from src.exporters.timeline_converter import TimelineConverter
from src.exporters.jianying_project import JianyingProject
from src.exporters.log_audit import AuditReportGenerator
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("export_workflow_panel")

class ExportWorkflowPanel:
    """导出工作流面板类"""
    
    def __init__(self, parent=None, master=None):
        """
        初始化导出工作流面板
        
        Args:
            parent: 父容器
            master: 主窗口
        """
        self.parent = parent
        self.master = master or parent
        
        # 创建面板框架
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 设置面板标题
        if master:
            master.title("剪映导出工作流")
        
        # 初始化变量
        self.project_name = tk.StringVar(value="新项目")
        self.export_path = tk.StringVar()
        self.timeline_fps = tk.StringVar(value="30")
        self.export_format = tk.StringVar(value="mp4")
        self.include_audit = tk.BooleanVar(value=True)
        
        # 工作流状态
        self.workflow_status = {
            "project_initialized": False,
            "timeline_converted": False,
            "xml_filled": False,
            "legal_injected": False,
            "validated": False,
            "exported": False
        }
        
        # 资源列表
        self.resources = []
        
        # 初始化组件
        self._init_widgets()
        
        # 初始化项目
        self.project = None
    
    def _init_widgets(self):
        """初始化UI组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="导出设置")
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # 项目设置
        project_frame = ttk.Frame(control_frame)
        project_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(project_frame, text="项目名称:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(project_frame, textvariable=self.project_name, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(project_frame, text="导出路径:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(project_frame, textvariable=self.export_path, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(project_frame, text="浏览...", command=self._browse_export_path).grid(row=1, column=2, padx=5, pady=5)
        
        # 时间轴设置
        timeline_frame = ttk.Frame(control_frame)
        timeline_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(timeline_frame, text="帧率:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Combobox(timeline_frame, textvariable=self.timeline_fps, values=["24", "25", "30", "50", "60"], width=5).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(timeline_frame, text="导出格式:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Combobox(timeline_frame, textvariable=self.export_format, values=["mp4", "mov", "project"], width=5).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 资源管理
        resources_frame = ttk.LabelFrame(control_frame, text="资源管理")
        resources_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(resources_frame, text="添加视频", command=lambda: self._add_resource("video")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(resources_frame, text="添加音频", command=lambda: self._add_resource("audio")).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(resources_frame, text="添加图片", command=lambda: self._add_resource("image")).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 法律合规设置
        legal_frame = ttk.LabelFrame(control_frame, text="法律合规")
        legal_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Checkbutton(legal_frame, text="包含审计报告", variable=self.include_audit).pack(anchor=tk.W, padx=5, pady=5)
        
        # 工作流操作按钮
        workflow_frame = ttk.LabelFrame(control_frame, text="工作流操作")
        workflow_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_button = ttk.Button(workflow_frame, text="开始导出流程", command=self._run_workflow)
        self.start_button.pack(fill=tk.X, padx=5, pady=5)
        
        # 右侧状态和日志
        status_frame = ttk.LabelFrame(main_frame, text="工作流状态")
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 状态指示器
        indicators_frame = ttk.Frame(status_frame)
        indicators_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_labels = {}
        row = 0
        for status_key in self.workflow_status.keys():
            label_text = status_key.replace("_", " ").title()
            ttk.Label(indicators_frame, text=f"{label_text}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            self.status_labels[status_key] = ttk.Label(indicators_frame, text="待处理", foreground="gray")
            self.status_labels[status_key].grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            row += 1
        
        # 日志文本区域
        log_frame = ttk.Frame(status_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, width=50, height=20)
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 初始化状态
        self._update_status_display()
        
        # 显示欢迎信息
        self._log("欢迎使用剪映导出工作流\n")
        self._log("请设置项目名称和导出路径，然后点击'开始导出流程'按钮")
    
    def _browse_export_path(self):
        """浏览导出路径"""
        if self.export_format.get() == "project":
            filename = filedialog.asksaveasfilename(
                title="选择导出路径",
                filetypes=[("剪映工程", "*.zip")],
                defaultextension=".zip"
            )
        else:
            filename = filedialog.asksaveasfilename(
                title="选择导出路径",
                filetypes=[("视频文件", f"*.{self.export_format.get()}"), ("所有文件", "*.*")],
                defaultextension=f".{self.export_format.get()}"
            )
        
        if filename:
            self.export_path.set(filename)
    
    def _add_resource(self, resource_type: str):
        """
        添加资源
        
        Args:
            resource_type: 资源类型
        """
        if resource_type == "video":
            filetypes = [("视频文件", "*.mp4 *.mov *.avi *.mkv"), ("所有文件", "*.*")]
        elif resource_type == "audio":
            filetypes = [("音频文件", "*.mp3 *.wav *.aac *.m4a"), ("所有文件", "*.*")]
        elif resource_type == "image":
            filetypes = [("图片文件", "*.jpg *.jpeg *.png *.gif"), ("所有文件", "*.*")]
        else:
            filetypes = [("所有文件", "*.*")]
        
        filenames = filedialog.askopenfilenames(
            title=f"选择{resource_type}文件",
            filetypes=filetypes
        )
        
        if not filenames:
            return
            
        for filename in filenames:
            resource_id = f"{resource_type}_{len(self.resources) + 1}"
            
            self.resources.append({
                "id": resource_id,
                "type": resource_type,
                "path": filename
            })
            
            self._log(f"已添加{resource_type}资源: {Path(filename).name}")
        
        self._log(f"当前共有 {len(self.resources)} 个资源")
    
    def _update_status(self, key: str, status: bool = True, message: str = None):
        """
        更新工作流状态
        
        Args:
            key: 状态键
            status: 状态值
            message: 状态消息
        """
        if key in self.workflow_status:
            self.workflow_status[key] = status
            
            # 更新界面
            color = "green" if status else "red"
            text = "完成" if status else "失败"
            if message:
                text = message
                
            if key in self.status_labels:
                self.status_labels[key].config(text=text, foreground=color)
        
        # 更新界面
        self.frame.update()
    
    def _update_status_display(self):
        """更新状态显示"""
        for key, status in self.workflow_status.items():
            color = "green" if status else "gray"
            text = "完成" if status else "待处理"
            
            if key in self.status_labels:
                self.status_labels[key].config(text=text, foreground=color)
    
    def _log(self, message: str):
        """
        记录日志
        
        Args:
            message: 日志消息
        """
        # 在文本框中添加时间戳和消息
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        # 更新界面
        self.log_text.update()
    
    def _initialize_project(self) -> bool:
        """
        初始化项目
        
        Returns:
            是否成功
        """
        try:
            project_name = self.project_name.get()
            if not project_name:
                messagebox.showerror("错误", "项目名称不能为空")
                return False
                
            self._log(f"初始化项目: {project_name}")
            
            # 创建项目
            self.project = JianyingProject(project_name)
            
            # 设置项目信息
            self.project.set_project_info({
                "name": project_name,
                "creation_time": datetime.datetime.now().isoformat()
            })
            
            self._update_status("project_initialized", True)
            return True
            
        except Exception as e:
            self._log(f"初始化项目失败: {str(e)}")
            self._update_status("project_initialized", False, "失败")
            return False
    
    def _convert_timeline(self) -> bool:
        """
        转换时间轴
        
        Returns:
            是否成功
        """
        try:
            fps = float(self.timeline_fps.get())
            self._log(f"设置时间轴帧率: {fps} fps")
            
            # 构建基本时间轴
            timeline_data = {
                "attributes": {"fps": str(fps), "duration": "0.0"},
                "tracks": []
            }
            
            # 添加视频轨道
            video_track = {"type": "video", "id": "video_track_1", "clips": []}
            timeline_data["tracks"].append(video_track)
            
            # 添加音频轨道
            audio_track = {"type": "audio", "id": "audio_track_1", "clips": []}
            timeline_data["tracks"].append(audio_track)
            
            # 根据资源添加片段
            position = 0.0
            total_duration = 0.0
            
            for resource in self.resources:
                resource_id = resource["id"]
                resource_type = resource["type"]
                
                # 根据资源类型添加到相应轨道
                if resource_type == "video":
                    # 添加到视频轨道
                    video_clip = {
                        "id": f"clip_{resource_id}",
                        "start": str(position),
                        "duration": "5.0", # 默认5秒
                        "media_id": resource_id
                    }
                    video_track["clips"].append(video_clip)
                    
                    # 更新位置
                    position += 5.0
                    total_duration += 5.0
                    
                elif resource_type == "audio":
                    # 添加到音频轨道
                    audio_clip = {
                        "id": f"clip_{resource_id}",
                        "start": str(position),
                        "duration": "5.0", # 默认5秒
                        "media_id": resource_id
                    }
                    audio_track["clips"].append(audio_clip)
                    
                    # 更新位置
                    position += 5.0
                    total_duration += 5.0
            
            # 更新总时长
            timeline_data["attributes"]["duration"] = str(total_duration)
            
            # 设置时间轴
            self.project.set_timeline(timeline_data)
            
            self._log(f"时间轴转换完成，总时长: {total_duration} 秒")
            self._update_status("timeline_converted", True)
            return True
            
        except Exception as e:
            self._log(f"时间轴转换失败: {str(e)}")
            self._update_status("timeline_converted", False, "失败")
            return False
    
    def _fill_xml_template(self) -> bool:
        """
        填充XML模板
        
        Returns:
            是否成功
        """
        try:
            self._log("填充XML模板")
            
            # 添加资源
            for resource in self.resources:
                self.project.add_resource(
                    resource["id"],
                    resource["type"],
                    resource["path"],
                    copy_file=True
                )
            
            # 设置导出设置
            export_format = self.export_format.get()
            fps = float(self.timeline_fps.get())
            
            export_settings = {
                "format": export_format,
                "codec": "h264" if export_format == "mp4" else "prores",
                "resolution": {
                    "width": "1920",
                    "height": "1080"
                },
                "fps": str(fps),
                "bitrate": "8000000"
            }
            
            self.project.set_export_settings(export_settings)
            
            self._log("XML模板填充完成")
            self._update_status("xml_filled", True)
            return True
            
        except Exception as e:
            self._log(f"XML模板填充失败: {str(e)}")
            self._update_status("xml_filled", False, "失败")
            return False
    
    def _inject_legal_info(self) -> bool:
        """
        注入法律声明
        
        Returns:
            是否成功
        """
        try:
            self._log("注入法律声明")
            
            # 创建法律声明
            legal_info = {
                "copyright": f"© {datetime.datetime.now().year} {self.project_name.get()}",
                "license": "本内容版权所有，未经授权禁止使用",
                "data_processing": (
                    "本导出内容符合GDPR和中国个人信息保护法规定，"
                    "所有个人数据已经过适当处理，并获得相关许可。"
                )
            }
            
            # 注入法律声明
            self.project.set_legal_info(legal_info)
            
            self._log("法律声明注入完成")
            self._update_status("legal_injected", True)
            return True
            
        except Exception as e:
            self._log(f"法律声明注入失败: {str(e)}")
            self._update_status("legal_injected", False, "失败")
            return False
    
    def _validate_project(self) -> bool:
        """
        验证项目
        
        Returns:
            是否验证通过
        """
        try:
            self._log("验证项目")
            
            # 验证项目
            if self.project.validate():
                self._log("项目验证通过")
                self._update_status("validated", True)
                return True
            else:
                self._log("项目验证失败")
                self._update_status("validated", False, "失败")
                return False
                
        except Exception as e:
            self._log(f"项目验证出错: {str(e)}")
            self._update_status("validated", False, "失败")
            return False
    
    def _export_project(self) -> bool:
        """
        导出项目
        
        Returns:
            是否成功
        """
        try:
            export_path = self.export_path.get()
            if not export_path:
                messagebox.showerror("错误", "导出路径不能为空")
                self._update_status("exported", False, "失败")
                return False
                
            self._log(f"导出项目到: {export_path}")
            
            # 导出项目
            if self.project.export_project_package(export_path):
                self._log("项目导出成功")
                
                # 生成审计报告
                if self.include_audit.get():
                    self._generate_audit_report(export_path)
                
                self._update_status("exported", True)
                return True
            else:
                self._log("项目导出失败")
                self._update_status("exported", False, "失败")
                return False
                
        except Exception as e:
            self._log(f"项目导出出错: {str(e)}")
            self._update_status("exported", False, "失败")
            return False
    
    def _generate_audit_report(self, project_path: str) -> None:
        """
        生成审计报告
        
        Args:
            project_path: 项目路径
        """
        try:
            self._log("生成审计报告")
            
            # 获取当前日期
            today = datetime.date.today()
            
            # 创建审计报告生成器
            generator = AuditReportGenerator()
            
            # 生成报告
            report = generator.generate_audit_report(
                start_date=today - datetime.timedelta(days=7),
                end_date=today,
                report_type="all",
                output_format="json",
                include_details=True
            )
            
            # 导出报告
            report_path = Path(project_path).with_suffix(".audit.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            self._log(f"审计报告已保存到: {report_path}")
            
        except Exception as e:
            self._log(f"生成审计报告失败: {str(e)}")
    
    def _run_workflow(self):
        """运行工作流"""
        # 禁用开始按钮
        self.start_button.config(state=tk.DISABLED)
        
        # 重置状态
        for key in self.workflow_status:
            self.workflow_status[key] = False
        self._update_status_display()
        
        # 在后台线程中运行工作流
        def workflow_thread():
            try:
                # 步骤1: 初始化项目
                if not self._initialize_project():
                    raise Exception("项目初始化失败")
                
                # 步骤2: 时间轴转换
                if not self._convert_timeline():
                    raise Exception("时间轴转换失败")
                
                # 步骤3: XML模板填充
                if not self._fill_xml_template():
                    raise Exception("XML模板填充失败")
                
                # 步骤4: 法律声明注入
                if not self._inject_legal_info():
                    raise Exception("法律声明注入失败")
                
                # 步骤5: 验证项目
                if not self._validate_project():
                    # 跳转到错误处理分支
                    self._log("验证失败，显示错误信息")
                    messagebox.showerror("验证失败", "项目验证失败，请检查设置和资源")
                    self._update_status("exported", False, "取消")
                else:
                    # 步骤6: 导出项目
                    if self._export_project():
                        messagebox.showinfo("导出成功", f"项目已成功导出到: {self.export_path.get()}")
                
            except Exception as e:
                self._log(f"工作流出错: {str(e)}")
                messagebox.showerror("工作流错误", str(e))
            
            finally:
                # 清理资源
                if self.project:
                    self.project.cleanup()
                
                # 恢复开始按钮
                self.master.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        
        # 启动后台线程
        threading.Thread(target=workflow_thread, daemon=True).start()


def create_export_workflow_panel(parent=None):
    """
    创建导出工作流面板
    
    Args:
        parent: 父容器
        
    Returns:
        导出工作流面板实例
    """
    return ExportWorkflowPanel(parent)


if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    root.geometry("1000x700")
    app = ExportWorkflowPanel(root, root)
    root.mainloop() 