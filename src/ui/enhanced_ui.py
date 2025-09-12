#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 增强UI
Enhanced UI with Fixed Core Modules

修复内容：
1. 集成增强的核心模块
2. 确保UI界面正常运行
3. 添加进度监控和错误处理
4. 优化用户体验
"""

import gradio as gr
import os
import sys
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入增强的核心模块
try:
    from src.core.enhanced_screenplay_engineer import EnhancedScreenplayEngineer
    from src.core.enhanced_language_detector import EnhancedLanguageDetector
    from src.core.enhanced_model_switcher import EnhancedModelSwitcher
    from src.core.enhanced_workflow_manager import EnhancedWorkflowManager
    from src.core.enhanced_sync_engine import EnhancedSyncEngine
    ENHANCED_MODULES_AVAILABLE = True
    logger.info("✅ 增强模块导入成功")
except ImportError as e:
    ENHANCED_MODULES_AVAILABLE = False
    logger.error(f"❌ 增强模块导入失败: {e}")
    
    # 创建占位符类
    class EnhancedScreenplayEngineer:
        def analyze_plot_structure(self, content): return {"error": "模块未加载"}
        def generate_viral_version(self, content, language): return {"success": False, "error": "模块未加载"}
        
    class EnhancedLanguageDetector:
        def detect_language(self, text): return "zh"
        
    class EnhancedModelSwitcher:
        def switch_to_language(self, lang): return True
        def get_model_status(self): return {}
        
    class EnhancedWorkflowManager:
        def __init__(self, progress_callback=None): self.progress_callback = progress_callback
        def process_complete_workflow(self, video_path, srt_path, output_path, language=None):
            return {"success": False, "error": "模块未加载"}
            
    class EnhancedSyncEngine:
        def calculate_sync_accuracy(self, subtitles, shots): return {"mapping_success_rate": 0}

# 导入其他必要模块
try:
    from src.visionai_clipsmaster.core.srt_parser import parse_srt, generate_srt_content
    SRT_PARSER_AVAILABLE = True
except ImportError:
    SRT_PARSER_AVAILABLE = False
    def parse_srt(path): return []
    def generate_srt_content(subtitles): return ""

# 全局变量
current_workflow_manager = None
processing_status = {"is_processing": False, "current_step": "", "progress": 0}

class EnhancedUI:
    """增强UI类"""
    
    def __init__(self):
        """初始化UI"""
        self.screenplay_engineer = EnhancedScreenplayEngineer()
        self.language_detector = EnhancedLanguageDetector()
        self.model_switcher = EnhancedModelSwitcher()
        self.sync_engine = EnhancedSyncEngine()
        
        # 初始化工作流管理器，传入进度回调
        self.workflow_manager = EnhancedWorkflowManager(progress_callback=self.update_progress)
        
        # 处理历史
        self.processing_history = []
        
    def update_progress(self, current: int, total: int, message: str):
        """更新进度"""
        global processing_status
        processing_status["current_step"] = message
        processing_status["progress"] = (current / total) * 100 if total > 0 else 0
        logger.info(f"进度: {processing_status['progress']:.1f}% - {message}")
        
    def process_srt_file(self, srt_file, video_file=None, language=None, progress=gr.Progress()):
        """处理SRT文件"""
        global processing_status
        
        if not srt_file:
            return "❌ 请上传SRT文件", "", ""
            
        try:
            processing_status["is_processing"] = True
            progress(0, desc="开始处理...")
            
            # 读取SRT文件
            with open(srt_file.name, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            progress(0.2, desc="分析剧情结构...")
            
            # 分析剧情结构
            plot_analysis = self.screenplay_engineer.analyze_plot_structure(original_content)
            
            if "error" in plot_analysis:
                return f"❌ 剧情分析失败: {plot_analysis['error']}", "", ""
                
            progress(0.5, desc="生成爆款版本...")
            
            # 检测语言
            if not language or language == "自动检测":
                detected_language = self.language_detector.detect_language(original_content)
            else:
                detected_language = "zh" if language == "中文" else "en"
                
            # 生成爆款版本
            viral_result = self.screenplay_engineer.generate_viral_version(original_content, detected_language)
            
            if not viral_result.get("success"):
                return f"❌ 爆款生成失败: {viral_result.get('error', '未知错误')}", "", ""
                
            progress(0.8, desc="生成输出文件...")
            
            # 生成输出
            viral_srt_content = viral_result["viral_content"]
            
            # 保存爆款SRT文件
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            viral_srt_path = output_dir / f"viral_{timestamp}.srt"
            
            with open(viral_srt_path, 'w', encoding='utf-8') as f:
                f.write(viral_srt_content)
                
            progress(1.0, desc="处理完成！")
            
            # 生成分析报告
            analysis_report = self.generate_analysis_report(plot_analysis, viral_result)
            
            # 记录处理历史
            self.processing_history.append({
                "timestamp": datetime.now().isoformat(),
                "original_file": srt_file.name,
                "language": detected_language,
                "viral_file": str(viral_srt_path),
                "quality_score": viral_result.get("quality_metrics", {}).get("overall_score", 0)
            })
            
            processing_status["is_processing"] = False
            
            return (
                f"✅ 处理完成！\n语言: {detected_language}\n输出文件: {viral_srt_path}",
                viral_srt_content,
                analysis_report
            )
            
        except Exception as e:
            processing_status["is_processing"] = False
            error_msg = f"❌ 处理失败: {str(e)}"
            logger.error(f"SRT处理失败: {e}")
            traceback.print_exc()
            return error_msg, "", ""
            
    def process_complete_workflow(self, srt_file, video_file, output_name, language=None, progress=gr.Progress()):
        """处理完整工作流"""
        global processing_status
        
        if not srt_file:
            return "❌ 请上传SRT文件"
            
        try:
            processing_status["is_processing"] = True
            progress(0, desc="启动完整工作流...")
            
            # 准备文件路径
            video_path = video_file.name if video_file else "test_video.mp4"
            srt_path = srt_file.name
            output_path = f"output/{output_name or 'output'}.mp4"
            
            # 检测语言
            if not language or language == "自动检测":
                with open(srt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                detected_language = self.language_detector.detect_language(content)
            else:
                detected_language = "zh" if language == "中文" else "en"
                
            progress(0.1, desc="执行完整工作流...")
            
            # 执行完整工作流
            result = self.workflow_manager.process_complete_workflow(
                video_path=video_path,
                srt_path=srt_path,
                output_path=output_path,
                language=detected_language
            )
            
            processing_status["is_processing"] = False
            
            if result["success"]:
                progress(1.0, desc="工作流完成！")
                
                output_info = [
                    f"✅ 完整工作流处理成功！",
                    f"语言: {detected_language}",
                    f"处理时长: {result.get('total_duration', 0):.2f}秒",
                    f"完成步骤: {result.get('steps_completed', 0)}/{result.get('steps_completed', 0)}",
                    f"爆款SRT: {result.get('viral_srt_path', 'N/A')}",
                    f"剪映工程: {result.get('jianying_project_path', 'N/A')}"
                ]
                
                return "\n".join(output_info)
            else:
                return f"❌ 工作流失败: {result.get('error', '未知错误')}"
                
        except Exception as e:
            processing_status["is_processing"] = False
            error_msg = f"❌ 完整工作流失败: {str(e)}"
            logger.error(f"完整工作流失败: {e}")
            traceback.print_exc()
            return error_msg
            
    def generate_analysis_report(self, plot_analysis: Dict, viral_result: Dict) -> str:
        """生成分析报告"""
        lines = [
            "📊 剧情分析报告",
            "=" * 40,
            f"语言: {plot_analysis.get('language', 'unknown')}",
            f"原始字幕数: {plot_analysis.get('total_subtitles', 0)}",
            f"总时长: {plot_analysis.get('duration', 0):.1f}秒",
            f"剧情类型: {plot_analysis.get('genre', 'unknown')}",
            f"节奏: {plot_analysis.get('pacing', {}).get('rhythm', 'unknown')}",
            "",
            "🎯 爆款转换结果",
            "=" * 40,
            f"爆款字幕数: {len(viral_result.get('subtitles', []))}",
            f"压缩比: {viral_result.get('compression_ratio', 0):.2f}",
            f"质量分数: {viral_result.get('quality_metrics', {}).get('overall_score', 0):.2f}",
            f"情感强度: {viral_result.get('quality_metrics', {}).get('emotional_score', 0)}",
            f"悬念元素: {viral_result.get('quality_metrics', {}).get('suspense_score', 0)}",
            "",
            "📈 处理统计",
            "=" * 40,
            f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"模块状态: {'✅ 正常' if ENHANCED_MODULES_AVAILABLE else '⚠️ 降级模式'}"
        ]
        
        return "\n".join(lines)
        
    def get_processing_status(self):
        """获取处理状态"""
        global processing_status
        
        if processing_status["is_processing"]:
            return f"🔄 处理中... {processing_status['progress']:.1f}% - {processing_status['current_step']}"
        else:
            return "✅ 就绪"
            
    def get_model_status(self):
        """获取模型状态"""
        try:
            status = self.model_switcher.get_model_status()
            
            lines = [
                "🤖 模型状态",
                "=" * 30,
                f"中文模型: {'✅ 已加载' if status.get('model_status', {}).get('chinese_model_loaded', False) else '❌ 未加载'}",
                f"英文模型: {'✅ 已加载' if status.get('model_status', {}).get('english_model_loaded', False) else '❌ 未加载'}",
                f"当前模型: {status.get('active_model', 'None')}",
                f"当前语言: {status.get('active_language', 'None')}",
                f"总切换次数: {status.get('model_status', {}).get('total_switches', 0)}",
                f"切换错误: {status.get('model_status', {}).get('switch_errors', 0)}"
            ]
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"❌ 获取模型状态失败: {e}"

def create_enhanced_ui():
    """创建增强UI界面"""
    ui = EnhancedUI()
    
    # 自定义CSS
    custom_css = """
    .gradio-container {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    .status-box {
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .success {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    .error {
        background-color: #f8d7da;
        border-color: #f5c6cb;
        color: #721c24;
    }
    """
    
    with gr.Blocks(css=custom_css, title="VisionAI-ClipsMaster 增强版") as app:
        gr.Markdown("# 🎬 VisionAI-ClipsMaster 增强版")
        gr.Markdown("### 原片字幕 → 爆款混剪，一键搞定！")
        
        with gr.Tabs():
            # 基础处理标签页
            with gr.TabItem("📝 基础处理"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📁 文件上传")
                        srt_file = gr.File(
                            label="SRT字幕文件",
                            file_types=[".srt"],
                            type="filepath"
                        )
                        language_choice = gr.Dropdown(
                            choices=["自动检测", "中文", "English"],
                            value="自动检测",
                            label="语言选择"
                        )
                        process_btn = gr.Button("🚀 开始处理", variant="primary")
                        
                    with gr.Column(scale=2):
                        gr.Markdown("### 📊 处理结果")
                        result_text = gr.Textbox(
                            label="处理状态",
                            lines=3,
                            interactive=False
                        )
                        viral_srt_output = gr.Textbox(
                            label="爆款SRT内容",
                            lines=10,
                            interactive=False
                        )
                        
                with gr.Row():
                    analysis_report = gr.Textbox(
                        label="📈 分析报告",
                        lines=15,
                        interactive=False
                    )
                    
            # 完整工作流标签页
            with gr.TabItem("🎯 完整工作流"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📁 输入文件")
                        workflow_srt_file = gr.File(
                            label="SRT字幕文件",
                            file_types=[".srt"],
                            type="filepath"
                        )
                        workflow_video_file = gr.File(
                            label="视频文件（可选）",
                            file_types=[".mp4", ".avi", ".mov", ".mkv"],
                            type="filepath"
                        )
                        workflow_output_name = gr.Textbox(
                            label="输出文件名",
                            value="viral_output",
                            placeholder="不含扩展名"
                        )
                        workflow_language = gr.Dropdown(
                            choices=["自动检测", "中文", "English"],
                            value="自动检测",
                            label="语言选择"
                        )
                        workflow_btn = gr.Button("🎬 执行完整工作流", variant="primary")
                        
                    with gr.Column(scale=2):
                        gr.Markdown("### 🎯 工作流结果")
                        workflow_result = gr.Textbox(
                            label="工作流状态",
                            lines=15,
                            interactive=False
                        )
                        
            # 系统状态标签页
            with gr.TabItem("📊 系统状态"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🔄 处理状态")
                        processing_status_text = gr.Textbox(
                            label="当前状态",
                            interactive=False
                        )
                        refresh_status_btn = gr.Button("🔄 刷新状态")
                        
                    with gr.Column():
                        gr.Markdown("### 🤖 模型状态")
                        model_status_text = gr.Textbox(
                            label="模型信息",
                            lines=8,
                            interactive=False
                        )
                        refresh_model_btn = gr.Button("🔄 刷新模型状态")
                        
        # 绑定事件
        process_btn.click(
            fn=ui.process_srt_file,
            inputs=[srt_file, None, language_choice],
            outputs=[result_text, viral_srt_output, analysis_report]
        )
        
        workflow_btn.click(
            fn=ui.process_complete_workflow,
            inputs=[workflow_srt_file, workflow_video_file, workflow_output_name, workflow_language],
            outputs=[workflow_result]
        )
        
        refresh_status_btn.click(
            fn=ui.get_processing_status,
            outputs=[processing_status_text]
        )
        
        refresh_model_btn.click(
            fn=ui.get_model_status,
            outputs=[model_status_text]
        )
        
        # 定时刷新状态
        app.load(
            fn=ui.get_processing_status,
            outputs=[processing_status_text],
            every=2
        )
        
    return app

def main():
    """主函数"""
    print("🚀 启动VisionAI-ClipsMaster增强版UI")
    print("=" * 50)
    
    # 检查模块状态
    if ENHANCED_MODULES_AVAILABLE:
        print("✅ 增强模块加载成功")
    else:
        print("⚠️ 增强模块加载失败，使用降级模式")
        
    # 创建UI
    app = create_enhanced_ui()
    
    # 启动应用
    try:
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=False,
            show_error=True
        )
    except Exception as e:
        print(f"❌ UI启动失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
