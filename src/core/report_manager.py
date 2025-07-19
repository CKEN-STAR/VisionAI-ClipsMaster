import os
import json
import time
from datetime import datetime
from pathlib import Path

from src.utils.log_handler import get_logger
from src.eval.report_generator import generate_html_report

logger = get_logger(__name__)


class ReportManager:
    """报告管理器，负责收集混剪过程数据并生成报告"""
    
    def __init__(self, output_dir="output/reports"):
        """初始化报告管理器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.results = {
            "model_info": {},
            "clip_stats": {
                "segments": []
            },
            "version_data": {},
            "performance_data": {
                "内存峰值": 0,
                "处理速度": 0,
                "剧情连贯性": 0,
                "叙事结构": 0,
                "工程兼容性": 0
            },
            "error_data": []
        }
        self.start_time = time.time()
        self.init_report_data()
        
    def init_report_data(self):
        """初始化报告数据"""
        try:
            # 读取模型配置
            from configs.models.active_model import get_active_model
            model_info = get_active_model()
            if model_info:
                self.set_model_info(model_info["name"], {
                    "type": "中文模型" if "zh" in model_info["name"] else "英文模型",
                    "quantization": model_info.get("quantization", "未知"),
                    "status": "active",
                    "memory_usage": 0  # 将在处理过程中更新
                })
        except Exception as e:
            logger.warning(f"初始化报告数据时出错: {str(e)}")
        
        # 初始化版本兼容性数据
        try:
            # 从配置文件中读取剪映版本兼容性数据
            from configs.export_policy import get_compatibility_data
            compat_data = get_compatibility_data()
            if compat_data:
                self.results["version_data"] = compat_data
        except Exception as e:
            logger.warning(f"读取版本兼容性数据时出错: {str(e)}")
    
    def set_model_info(self, model_name, info):
        """设置模型信息"""
        self.results["model_info"][model_name] = info
        return self
    
    def set_clip_stats(self, original_duration, final_duration, segments=None):
        """设置混剪统计信息"""
        self.results["clip_stats"].update({
            "original_duration": original_duration,
            "final_duration": final_duration
        })
        
        if segments:
            self.results["clip_stats"]["segments"] = segments
        
        return self
    
    def add_segment(self, start, end, duration=None):
        """添加片段信息"""
        if duration is None:
            duration = end - start
            
        self.results["clip_stats"]["segments"].append({
            "start": start,
            "end": end,
            "duration": duration
        })
        
        return self
    
    def set_performance_metric(self, metric, value):
        """设置性能指标"""
        if metric in self.results["performance_data"]:
            self.results["performance_data"][metric] = value
        
        return self
    
    def add_error(self, error_type, location, description, suggestion=None):
        """添加错误信息"""
        self.results["error_data"].append({
            "type": error_type,
            "location": location,
            "description": description,
            "suggestion": suggestion or "无建议"
        })
        
        return self
    
    def update_memory_usage(self, usage_gb):
        """更新内存使用情况"""
        current = self.results["performance_data"].get("内存峰值", 0)
        if usage_gb > current:
            self.results["performance_data"]["内存峰值"] = usage_gb
        
        return self
    
    def set_narrative_metrics(self, coherence, structure):
        """设置叙事指标"""
        self.results["performance_data"]["剧情连贯性"] = coherence
        self.results["performance_data"]["叙事结构"] = structure
        
        return self
    
    def set_export_compatibility(self, compatibility):
        """设置导出兼容性"""
        self.results["performance_data"]["工程兼容性"] = compatibility
        
        return self
    
    def calculate_processing_speed(self, input_duration):
        """根据处理时间计算相对速度"""
        elapsed_time = time.time() - self.start_time
        
        # 理想值是实时速度(1x)，计算相对于理想值的比率
        ideal_time = input_duration
        relative_speed = min(ideal_time / max(elapsed_time, 1), 1.0)
        
        self.results["performance_data"]["处理速度"] = round(relative_speed, 2)
        
        return self
    
    def save_report_data(self, filepath):
        """保存原始报告数据"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告数据已保存至: {filepath}")
        return filepath
    
    def generate_report(self, task_id=None):
        """生成HTML报告"""
        # 生成唯一的任务ID
        if task_id is None:
            task_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON数据
        json_path = self.output_dir / f"report_data_{task_id}.json"
        self.save_report_data(json_path)
        
        # 生成HTML报告
        html_path = self.output_dir / f"clip_report_{task_id}.html"
        report_path = generate_html_report(self.results, str(html_path))
        
        logger.info(f"混剪报告已生成: {report_path}")
        return report_path


# 创建全局报告管理器实例
report_manager = ReportManager()


if __name__ == "__main__":
    # 测试代码
    manager = ReportManager()
    
    # 添加测试数据
    manager.set_model_info("Qwen2.5-7B-zh", {
        "type": "中文模型",
        "quantization": "Q4_K_M",
        "status": "active",
        "memory_usage": 3.6
    })
    
    manager.set_clip_stats(3600, 360)
    manager.add_segment(120, 130)
    manager.add_segment(240, 265)
    manager.add_segment(1200, 1215)
    
    manager.update_memory_usage(3.6)
    manager.set_narrative_metrics(0.78, 0.82)
    manager.set_export_compatibility(0.92)
    manager.calculate_processing_speed(3600)
    
    manager.add_error(
        "时间轴错位", 
        "字幕解析", 
        "部分SRT时间码与视频不同步",
        "检查SRT文件格式或使用自动对齐工具"
    )
    
    # 生成测试报告
    report_path = manager.generate_report("test_task")
    print(f"测试报告已生成: {report_path}") 