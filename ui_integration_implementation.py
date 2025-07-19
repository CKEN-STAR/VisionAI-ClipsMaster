#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster UI集成和功能修改实现方案
"""

import os
import sys
import json
import subprocess
import platform
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_ui_layout_modifications():
    """获取UI布局修改代码"""
    
    # 原始代码（需要替换的部分）
    original_code = '''        generate_srt_btn = QPushButton("生成爆款SRT")
        generate_srt_btn.setMinimumHeight(40)
        generate_srt_btn.clicked.connect(self.generate_viral_srt)
        action_layout.addWidget(generate_srt_btn)
        
        generate_video_btn = QPushButton("生成视频")
        generate_video_btn.setMinimumHeight(40)
        generate_video_btn.clicked.connect(self.generate_video)
        action_layout.addWidget(generate_video_btn)'''
    
    # 新的代码（替换后的部分）
    new_code = '''        generate_srt_btn = QPushButton("生成爆款SRT")
        generate_srt_btn.setMinimumHeight(40)
        generate_srt_btn.clicked.connect(self.generate_viral_srt)
        action_layout.addWidget(generate_srt_btn)
        
        # 创建并排的生成视频和导出按钮布局
        video_export_layout = QHBoxLayout()
        
        # 生成工程文件按钮（左侧）
        generate_project_btn = QPushButton("生成工程文件")
        generate_project_btn.setMinimumHeight(40)
        generate_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
            QPushButton:pressed {
                background-color: #389e0d;
            }
        """)
        generate_project_btn.clicked.connect(self.generate_project_file)
        video_export_layout.addWidget(generate_project_btn)
        
        # 导出到剪映按钮（右侧）
        export_jianying_btn = QPushButton("导出到剪映")
        export_jianying_btn.setMinimumHeight(40)
        export_jianying_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        export_jianying_btn.clicked.connect(self.export_to_jianying)
        video_export_layout.addWidget(export_jianying_btn)
        
        # 将并排布局添加到主布局
        action_layout.addLayout(video_export_layout)'''
    
    return original_code, new_code

def get_generate_project_file_method():
    """获取生成工程文件方法的实现"""
    
    method_code = '''    def generate_project_file(self):
        """生成工程文件（不渲染视频）"""
        # 检查是否有选中的视频和SRT
        if self.video_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加视频")
            return
        
        # 获取选中的视频
        selected_video = self.video_list.currentItem()
        if not selected_video:
            QMessageBox.warning(self, "警告", "请选择一个要处理的视频")
            return
        
        video_path = selected_video.data(Qt.ItemDataRole.UserRole)
        
        # 找到选中的爆款SRT
        selected_srt = self.srt_list.currentItem()
        if not selected_srt:
            QMessageBox.warning(self, "警告", "请选择一个SRT文件")
            return
        
        srt_path = selected_srt.data(Qt.ItemDataRole.UserRole)
        
        # 检查是否为爆款SRT
        srt_name = os.path.basename(srt_path)
        if not "爆款" in srt_name:
            reply = QMessageBox.question(
                self, 
                "确认使用", 
                f"所选SRT文件 '{srt_name}' 不是爆款SRT，确定要使用吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # 显示处理中
        self.statusBar().showMessage(f"正在生成工程文件...")
        log_handler.log("info", f"开始生成工程文件: 视频={video_path}, 字幕={srt_path}")
        
        # 重置进度条
        self.process_progress_bar.setValue(0)
        
        # 询问保存路径
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        default_name = f"{video_name}_工程文件.json"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存工程文件", default_name, "工程文件 (*.json)"
        )
        
        if not save_path:
            self.statusBar().showMessage("工程文件生成已取消")
            log_handler.log("info", "用户取消工程文件生成")
            return
        
        try:
            # 生成工程文件数据
            project_data = self._build_project_data(video_path, srt_path)
            
            # 保存工程文件
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            # 保存到实例变量，供导出功能使用
            self.last_project_file = save_path
            self.last_project_data = project_data
            
            # 更新进度条
            self.process_progress_bar.setValue(100)
            
            # 成功
            self.statusBar().showMessage(f"工程文件生成成功: {os.path.basename(save_path)}")
            log_handler.log("info", f"工程文件生成成功: {save_path}")
            QMessageBox.information(
                self, 
                "成功", 
                f"工程文件已生成并保存到:\\n{save_path}\\n\\n"
                f"现在可以点击"导出到剪映"按钮将项目导出到剪映进行编辑。"
            )
            
        except Exception as e:
            # 失败
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("工程文件生成失败")
            log_handler.log("error", f"工程文件生成失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"工程文件生成失败: {str(e)}")
    
    def _build_project_data(self, video_path: str, srt_path: str) -> Dict[str, Any]:
        """构建工程文件数据"""
        try:
            # 读取SRT文件
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            # 解析SRT内容
            scenes = self._parse_srt_to_scenes(srt_content, video_path)
            
            # 构建工程数据
            project_data = {
                "project_id": f"visionai_project_{int(time.time())}",
                "title": f"VisionAI工程 - {os.path.splitext(os.path.basename(video_path))[0]}",
                "created_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_video": video_path,
                "source_srt": srt_path,
                "scenes": scenes,
                "metadata": {
                    "total_scenes": len(scenes),
                    "total_duration": scenes[-1]["end_time"] if scenes else 0,
                    "video_format": os.path.splitext(video_path)[1],
                    "srt_encoding": "utf-8"
                },
                "export_settings": {
                    "target_format": "jianying",
                    "resolution": "1920x1080",
                    "fps": 30
                }
            }
            
            return project_data
            
        except Exception as e:
            logger.error(f"构建工程数据失败: {e}")
            raise
    
    def _parse_srt_to_scenes(self, srt_content: str, video_path: str) -> List[Dict[str, Any]]:
        """解析SRT内容为场景数据"""
        import re
        
        scenes = []
        
        # SRT格式正则表达式
        srt_pattern = r'(\\\\1+)\\n([\\\\1:,]+) --> ([\\\\1:,]+)\\n(.*?)(?=\\n\\\\1+\\n|\\n*$)'
        matches = re.findall(srt_pattern, srt_content, re.DOTALL)
        
        for match in matches:
            scene_id, start_time_str, end_time_str, text = match
            
            # 转换时间格式
            start_time = self._time_str_to_seconds(start_time_str)
            end_time = self._time_str_to_seconds(end_time_str)
            
            scene = {
                "scene_id": f"scene_{scene_id}",
                "id": f"scene_{scene_id}",
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "text": text.strip().replace('\\n', ' '),
                "video_path": video_path,
                "source_start": start_time,
                "source_end": end_time
            }
            
            scenes.append(scene)
        
        return scenes
    
    def _time_str_to_seconds(self, time_str: str) -> float:
        """将时间字符串转换为秒数"""
        # 格式: HH:MM:SS,mmm
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds'''
    
    return method_code

def get_export_to_jianying_method():
    """获取导出到剪映方法的实现"""
    
    method_code = '''    def export_to_jianying(self):
        """导出到剪映"""
        try:
            # 检查是否有生成的工程文件
            if not hasattr(self, 'last_project_file') or not self.last_project_file:
                QMessageBox.warning(
                    self, 
                    "提示", 
                    "请先点击"生成工程文件"按钮生成项目数据，然后再导出到剪映"
                )
                return
            
            # 检查工程文件是否存在
            if not os.path.exists(self.last_project_file):
                QMessageBox.warning(
                    self, 
                    "错误", 
                    "工程文件不存在，请重新生成工程文件"
                )
                return
            
            # 显示进度
            self.statusBar().showMessage("正在导出到剪映...")
            self.process_progress_bar.setValue(0)
            
            # 选择保存位置
            project_name = os.path.splitext(os.path.basename(self.last_project_file))[0]
            default_name = f"{project_name}_剪映工程.zip"
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出剪映工程文件",
                default_name,
                "剪映工程文件 (*.zip);;JSON文件 (*.json)"
            )
            
            if not save_path:
                self.statusBar().showMessage("导出已取消")
                return
            
            # 执行导出
            from src.export.jianying_exporter import JianyingExporter
            
            exporter = JianyingExporter()
            
            # 使用工程数据进行导出
            result = exporter.export(self.last_project_data, save_path)
            
            if result:
                self.process_progress_bar.setValue(80)
                self.statusBar().showMessage("导出完成，正在启动剪映...")
                
                # 尝试自动启动剪映
                jianying_launched = self._launch_jianying_app(save_path)
                
                self.process_progress_bar.setValue(100)
                
                if jianying_launched:
                    self.statusBar().showMessage("剪映启动成功")
                    QMessageBox.information(
                        self,
                        "导出成功",
                        f"剪映工程文件已导出并自动打开剪映应用！\\n\\n"
                        f"导出文件：{save_path}\\n\\n"
                        f"剪映应用已启动，请在剪映中导入刚才保存的工程文件。"
                    )
                else:
                    self.statusBar().showMessage("导出完成")
                    # 显示手动操作指引
                    reply = QMessageBox.information(
                        self,
                        "导出成功",
                        f"剪映工程文件已保存到：\\n{save_path}\\n\\n"
                        f"由于无法自动启动剪映，请手动执行以下步骤：\\n"
                        f"1. 打开剪映应用\\n"
                        f"2. 选择"导入项目"\\n"
                        f"3. 选择刚才保存的工程文件\\n"
                        f"4. 开始在剪映中编辑视频\\n\\n"
                        f"是否打开文件所在文件夹？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self._open_file_folder(save_path)
            else:
                self.process_progress_bar.setValue(0)
                self.statusBar().showMessage("导出失败")
                QMessageBox.critical(self, "错误", "导出到剪映失败，请检查文件权限和磁盘空间")
                
        except Exception as e:
            self.process_progress_bar.setValue(0)
            self.statusBar().showMessage("导出失败")
            QMessageBox.critical(self, "错误", f"导出过程中发生错误：{str(e)}")
            logger.error(f"导出到剪映失败: {e}")
    
    def _launch_jianying_app(self, project_file_path: str) -> bool:
        """尝试自动启动剪映应用"""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows系统下尝试启动剪映
                jianying_paths = [
                    # 常见的剪映安装路径
                    os.path.expanduser("~/AppData/Local/JianyingPro/JianyingPro.exe"),
                    "C:/Program Files/JianyingPro/JianyingPro.exe",
                    "C:/Program Files (x86)/JianyingPro/JianyingPro.exe",
                ]
                
                # 尝试从注册表查找剪映路径
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       r"SOFTWARE\\\\\\\\1icrosoft\\\\\\\\1indows\\\\\\\\1urrentVersion\\\\\\\\1ninstall")
                    # 这里可以添加更复杂的注册表查找逻辑
                except:
                    pass
                
                # 尝试启动剪映
                for path in jianying_paths:
                    if os.path.exists(path):
                        try:
                            subprocess.Popen([path])
                            logger.info(f"成功启动剪映: {path}")
                            return True
                        except Exception as e:
                            logger.warning(f"启动剪映失败 {path}: {e}")
                            continue
                
                # 尝试通过系统关联启动
                try:
                    os.startfile(project_file_path)
                    logger.info("通过系统关联启动剪映")
                    return True
                except Exception as e:
                    logger.warning(f"通过系统关联启动失败: {e}")
                
            elif system == "Darwin":  # macOS
                # macOS系统下尝试启动剪映
                try:
                    subprocess.run(["open", "-a", "JianyingPro"], check=True)
                    logger.info("成功启动剪映 (macOS)")
                    return True
                except subprocess.CalledProcessError:
                    try:
                        subprocess.run(["open", project_file_path], check=True)
                        logger.info("通过系统关联启动剪映 (macOS)")
                        return True
                    except Exception as e:
                        logger.warning(f"macOS启动剪映失败: {e}")
            
            else:  # Linux
                # Linux系统下的处理
                try:
                    subprocess.run(["xdg-open", project_file_path], check=True)
                    logger.info("通过系统关联启动剪映 (Linux)")
                    return True
                except Exception as e:
                    logger.warning(f"Linux启动剪映失败: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"启动剪映应用失败: {e}")
            return False
    
    def _open_file_folder(self, file_path: str):
        """打开文件所在文件夹"""
        try:
            folder_path = os.path.dirname(file_path)
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(["explorer", folder_path])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
                
        except Exception as e:
            logger.error(f"打开文件夹失败: {e}")'''
    
    return method_code

def get_additional_imports():
    """获取需要添加的导入语句"""
    
    imports = '''import time
import json
import subprocess
import platform'''
    
    return imports
