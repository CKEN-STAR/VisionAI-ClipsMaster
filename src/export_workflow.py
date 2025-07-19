#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪映导出工作流主程序

集成XML模板处理、时间轴转换、法律声明和合规审计等功能，
实现符合剪映规范的导出工作流。
"""

import os
import sys
import argparse
import json
import datetime
import tkinter as tk
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# 添加项目根目录到PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入项目模块
from src.exporters.xml_template import XMLTemplateProcessor
from src.exporters.timeline_converter import TimelineConverter
from src.exporters.jianying_project import JianyingProject
from src.exporters.log_audit import AuditReportGenerator
from src.exporters.workflow_audit import WorkflowAuditIntegrator
from src.ui.export_workflow_panel import ExportWorkflowPanel
from src.utils.logger import get_module_logger

# 初始化日志记录器
logger = get_module_logger("export_workflow")

def run_export_workflow(args):
    """
    运行导出工作流
    
    Args:
        args: 命令行参数
    """
    # 创建工作流审计集成器
    auditor = WorkflowAuditIntegrator()
    
    try:
        # 步骤1: 项目初始化
        logger.info("步骤1: 项目初始化")
        project = JianyingProject(args.project_name)
        
        project_info = {
            "name": args.project_name,
            "creation_time": datetime.datetime.now().isoformat(),
            "author": args.author or "VisionAI-ClipsMaster"
        }
        
        project.set_project_info(project_info)
        
        # 记录项目初始化事件
        auditor.record_project_initialization(project_info)
        
        # 步骤2: 时间轴转换
        logger.info("步骤2: 时间轴转换")
        fps = float(args.fps)
        
        # 构建时间轴数据
        timeline_data = {
            "attributes": {"fps": str(fps), "duration": "0.0"},
            "tracks": [
                {"type": "video", "id": "video_track_1", "clips": []},
                {"type": "audio", "id": "audio_track_1", "clips": []}
            ]
        }
        
        # 如果提供了输入资源
        if args.resources:
            # 解析资源列表
            resources = []
            for resource_str in args.resources:
                parts = resource_str.split(":")
                if len(parts) >= 2:
                    resource_type, path = parts[0], parts[1]
                    resources.append({
                        "id": f"{resource_type}_{len(resources) + 1}",
                        "type": resource_type,
                        "path": path
                    })
            
            # 添加资源到时间轴
            position = 0.0
            total_duration = 0.0
            
            for resource in resources:
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
                    timeline_data["tracks"][0]["clips"].append(video_clip)
                    
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
                    timeline_data["tracks"][1]["clips"].append(audio_clip)
                    
                    # 更新位置
                    position += 5.0
                    total_duration += 5.0
            
            # 更新总时长
            timeline_data["attributes"]["duration"] = str(total_duration)
        
        # 设置时间轴
        project.set_timeline(timeline_data)
        
        # 记录时间轴转换事件
        auditor.record_timeline_conversion({
            "fps": str(fps),
            "tracks": len(timeline_data["tracks"]),
            "duration": timeline_data["attributes"]["duration"]
        })
        
        # 步骤3: XML模板填充
        logger.info("步骤3: XML模板填充")
        
        # 添加资源
        if args.resources:
            for resource in resources:
                project.add_resource(
                    resource["id"],
                    resource["type"],
                    resource["path"],
                    copy_file=True
                )
        
        # 设置导出设置
        export_format = args.format
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
        
        project.set_export_settings(export_settings)
        
        # 记录XML模板填充事件
        auditor.record_xml_template_filling({
            "resource_count": len(resources) if args.resources else 0,
            "export_format": export_format
        })
        
        # 步骤4: 法律声明注入
        logger.info("步骤4: 法律声明注入")
        
        # 创建法律声明
        legal_info = {
            "copyright": f"© {datetime.datetime.now().year} {args.project_name}",
            "license": args.license or "本内容版权所有，未经授权禁止使用",
            "data_processing": (
                "本导出内容符合GDPR和中国个人信息保护法规定，"
                "所有个人数据已经过适当处理，并获得相关许可。"
            )
        }
        
        # 注入法律声明
        project.set_legal_info(legal_info)
        
        # 记录法律声明注入事件
        auditor.record_legal_info_injection(legal_info)
        
        # 步骤5: 验证
        logger.info("步骤5: 验证")
        
        # 验证项目
        is_valid = project.validate()
        
        # 记录验证结果
        auditor.record_validation_result(is_valid, {
            "validation_items": ["项目元数据", "时间轴", "资源", "法律声明"],
            "all_passed": is_valid
        })
        
        if not is_valid:
            logger.error("验证失败")
            print("错误: 项目验证失败，请检查设置和资源")
            
            # 记录错误事件
            auditor.record_error({
                "message": "项目验证失败",
                "stage": "validation"
            })
            
            # 生成错误报告
            error_report_path = Path(args.output).with_suffix(".error.json")
            auditor.generate_workflow_audit_report(error_report_path)
            
            print(f"错误报告已保存到: {error_report_path}")
            
            # 清理项目
            project.cleanup()
            return 1
        
        # 步骤6: 导出
        logger.info("步骤6: 导出")
        
        # 导出项目
        success = project.export_project_package(args.output)
        
        if success:
            logger.info(f"导出成功: {args.output}")
            print(f"项目已成功导出到: {args.output}")
            
            # 记录导出完成事件
            auditor.record_export_completion({
                "output_path": args.output,
                "format": args.format,
                "size_bytes": os.path.getsize(args.output)
            })
            
            # 生成审计报告
            if args.generate_audit:
                audit_report_path = Path(args.output).with_suffix(".audit.json")
                
                # 创建综合审计报告
                auditor.create_comprehensive_audit_report(
                    project_info,
                    audit_report_path
                )
                
                print(f"审计报告已保存到: {audit_report_path}")
        else:
            logger.error("导出失败")
            print("错误: 项目导出失败")
            
            # 记录错误事件
            auditor.record_error({
                "message": "项目导出失败",
                "stage": "export"
            })
            
            # 生成错误报告
            error_report_path = Path(args.output).with_suffix(".error.json")
            auditor.generate_workflow_audit_report(error_report_path)
            
            print(f"错误报告已保存到: {error_report_path}")
            
            # 清理项目
            project.cleanup()
            return 1
        
        # 清理项目
        project.cleanup()
        return 0
        
    except Exception as e:
        logger.error(f"工作流错误: {str(e)}")
        print(f"错误: {str(e)}")
        
        # 记录错误事件
        auditor.record_error({
            "message": str(e),
            "exception": type(e).__name__
        })
        
        # 生成错误报告
        try:
            error_report_path = Path(args.output).with_suffix(".error.json") if args.output else Path("export_error.json")
            auditor.generate_workflow_audit_report(error_report_path)
            
            print(f"错误报告已保存到: {error_report_path}")
        except Exception:
            print("无法生成错误报告")
        
        # 尝试清理项目
        if 'project' in locals():
            project.cleanup()
            
        return 1

def launch_ui():
    """启动UI界面"""
    # 创建主窗口
    root = tk.Tk()
    root.geometry("1000x700")
    root.title("剪映导出工作流")
    
    # 创建工作流面板
    app = ExportWorkflowPanel(root, root)
    
    # 启动主循环
    root.mainloop()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="剪映导出工作流")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # UI命令
    ui_parser = subparsers.add_parser("ui", help="启动UI界面")
    
    # 导出命令
    export_parser = subparsers.add_parser("export", help="导出项目")
    export_parser.add_argument("--project-name", "-n", type=str, required=True, help="项目名称")
    export_parser.add_argument("--output", "-o", type=str, required=True, help="输出文件路径")
    export_parser.add_argument("--fps", type=str, default="30", help="帧率 (默认: 30)")
    export_parser.add_argument("--format", "-f", type=str, default="project", choices=["mp4", "mov", "project"], help="导出格式 (默认: project)")
    export_parser.add_argument("--resources", "-r", type=str, nargs="+", help="资源列表，格式为 'type:path'")
    export_parser.add_argument("--author", "-a", type=str, help="作者")
    export_parser.add_argument("--license", "-l", type=str, help="许可证")
    export_parser.add_argument("--generate-audit", "-g", action="store_true", help="生成审计报告")
    
    # 验证命令
    validate_parser = subparsers.add_parser("validate", help="验证XML文件")
    validate_parser.add_argument("--file", "-f", type=str, required=True, help="XML文件路径")
    
    # 审计命令
    audit_parser = subparsers.add_parser("audit", help="生成审计报告")
    audit_parser.add_argument("--project", "-p", type=str, required=True, help="项目文件路径")
    audit_parser.add_argument("--output", "-o", type=str, required=True, help="输出文件路径")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行对应的命令
    if args.command == "ui":
        launch_ui()
        return 0
    
    elif args.command == "export":
        return run_export_workflow(args)
    
    elif args.command == "validate":
        # 验证XML文件
        from src.exporters.xml_template import validate_xml
        
        if validate_xml(args.file):
            print(f"XML文件验证通过: {args.file}")
            return 0
        else:
            print(f"XML文件验证失败: {args.file}")
            return 1
    
    elif args.command == "audit":
        # 生成审计报告
        try:
            project_path = Path(args.project)
            
            # 读取项目信息
            if project_path.suffix == ".zip" and project_path.exists():
                import zipfile
                
                with zipfile.ZipFile(project_path, "r") as zipf:
                    try:
                        with zipf.open("project_info.json") as f:
                            project_info = json.load(f)
                    except:
                        project_info = {"name": project_path.stem}
            else:
                project_info = {"name": project_path.stem}
            
            # 创建审计报告生成器
            audit_generator = AuditReportGenerator()
            
            # 生成审计报告
            today = datetime.date.today()
            report = audit_generator.generate_audit_report(
                start_date=today - datetime.timedelta(days=30),
                end_date=today,
                report_type="all",
                output_format="json",
                include_details=True
            )
            
            # 导出报告
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump({
                    "project_info": project_info,
                    "audit_report": report,
                    "generation_time": datetime.datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
                
            print(f"审计报告已保存到: {args.output}")
            return 0
            
        except Exception as e:
            print(f"生成审计报告失败: {str(e)}")
            return 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 