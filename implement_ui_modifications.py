#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实施VisionAI-ClipsMaster UI修改的脚本
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_original_file():
    """备份原始文件"""
    original_file = "simple_ui_fixed.py"
    backup_file = f"simple_ui_fixed_backup_{int(time.time())}.py"
    
    try:
        shutil.copy2(original_file, backup_file)
        logger.info(f"✅ 原始文件已备份为: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"❌ 备份文件失败: {e}")
        return None

def implement_ui_modifications():
    """实施UI修改"""
    logger.info("🔧 开始实施UI修改")
    logger.info("=" * 60)
    
    try:
        # 1. 备份原始文件
        backup_file = backup_original_file()
        if not backup_file:
            logger.error("备份失败，停止修改")
            return False
        
        # 2. 读取原始文件
        with open("simple_ui_fixed.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3. 添加必要的导入
        logger.info("1. 添加必要的导入语句")
        
        # 查找现有的导入部分
        import_section = content.find("from PyQt6.QtWidgets import")
        if import_section != -1:
            # 在导入部分后添加新的导入
            additional_imports = """
import time
import json
import subprocess
import platform"""
            
            # 找到导入部分的结束位置
            import_end = content.find("\n\n", import_section)
            if import_end != -1:
                content = content[:import_end] + additional_imports + content[import_end:]
                logger.info("✅ 导入语句添加成功")
            else:
                logger.warning("⚠️ 无法找到导入部分的结束位置")
        
        # 4. 修改UI布局
        logger.info("2. 修改UI布局 - 替换生成视频按钮")
        
        # 原始代码
        original_button_code = '''        generate_srt_btn = QPushButton("生成爆款SRT")
        generate_srt_btn.setMinimumHeight(40)
        generate_srt_btn.clicked.connect(self.generate_viral_srt)
        action_layout.addWidget(generate_srt_btn)
        
        generate_video_btn = QPushButton("生成视频")
        generate_video_btn.setMinimumHeight(40)
        generate_video_btn.clicked.connect(self.generate_video)
        action_layout.addWidget(generate_video_btn)'''
        
        # 新的代码
        new_button_code = '''        generate_srt_btn = QPushButton("生成爆款SRT")
        generate_srt_btn.setMinimumHeight(40)
        generate_srt_btn.clicked.connect(self.generate_viral_srt)
        action_layout.addWidget(generate_srt_btn)
        
        # 创建并排的生成工程文件和导出按钮布局
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
        
        if original_button_code in content:
            content = content.replace(original_button_code, new_button_code)
            logger.info("✅ UI布局修改成功")
        else:
            logger.warning("⚠️ 未找到原始按钮代码，可能需要手动修改")
        
        # 5. 添加新的方法
        logger.info("3. 添加新的方法实现")
        
        # 找到类的结束位置（在最后一个方法后）
        class_end = content.rfind("    def ")
        if class_end != -1:
            # 找到该方法的结束位置
            method_end = content.find("\n\n", class_end)
            if method_end == -1:
                method_end = len(content)
            
            # 添加新方法
            new_methods = get_new_methods_code()
            content = content[:method_end] + "\n" + new_methods + content[method_end:]
            logger.info("✅ 新方法添加成功")
        else:
            logger.warning("⚠️ 无法找到类的结束位置")
        
        # 6. 保存修改后的文件
        with open("simple_ui_fixed.py", 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("🎉 UI修改实施完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ UI修改实施失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_new_methods_code():
    """获取新方法的代码"""
    
    return '''
    def generate_project_file(self):
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
    
    def _build_project_data(self, video_path: str, srt_path: str):
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
    
    def _parse_srt_to_scenes(self, srt_content: str, video_path: str):
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

if __name__ == "__main__":
    import time
    
    logger.info("🎬 开始VisionAI-ClipsMaster UI集成和功能修改实施")
    logger.info("=" * 80)
    
    success = implement_ui_modifications()
    
    if success:
        logger.info("🎉 UI修改实施成功！")
        logger.info("接下来需要手动添加导出到剪映的方法实现")
    else:
        logger.error("❌ UI修改实施失败")
    
    print("\n" + "=" * 80)
    print("VisionAI-ClipsMaster UI集成和功能修改实施完成！")
    print(f"实施结果: {'成功' if success else '失败'}")
    print("=" * 80)
