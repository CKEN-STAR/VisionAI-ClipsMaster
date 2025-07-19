#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
性能测试报告生成器 - 汇总内存、线程和性能测试结果
"""

import os
import sys
import time
import logging
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("performance_report")

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入内存泄漏检测器
try:
    from ui.utils.memory_leak_detector import generate_memory_report
    HAS_MEMORY_DETECTOR = True
except ImportError:
    HAS_MEMORY_DETECTOR = False
    logger.warning("内存泄漏检测器不可用，将跳过内存分析")

class PerformanceReportGenerator:
    """性能测试报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # 创建性能报告目录
        self.performance_dir = self.reports_dir / "performance"
        self.performance_dir.mkdir(exist_ok=True)
        
        # 创建内存报告目录
        self.memory_dir = self.reports_dir / "memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # 创建线程报告目录
        self.thread_dir = self.reports_dir / "thread"
        self.thread_dir.mkdir(exist_ok=True)
        
        logger.info("性能报告生成器初始化完成")
    
    def collect_memory_reports(self) -> List[Dict[str, Any]]:
        """收集所有内存报告
        
        Returns:
            List[Dict[str, Any]]: 内存报告列表
        """
        reports = []
        
        # 查找所有内存报告文件
        memory_files = glob.glob(str(self.reports_dir / "*memory*report*.txt"))
        
        for file_path in memory_files:
            try:
                # 读取报告文件
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 解析报告内容
                report_data = self._parse_memory_report(content)
                report_data["file"] = file_path
                
                reports.append(report_data)
                
            except Exception as e:
                logger.error(f"解析内存报告 {file_path} 时出错: {str(e)}")
        
        return reports
    
    def _parse_memory_report(self, content: str) -> Dict[str, Any]:
        """解析内存报告内容
        
        Args:
            content: 报告内容
            
        Returns:
            Dict[str, Any]: 解析后的报告数据
        """
        report_data = {
            "timestamp": None,
            "duration": None,
            "memory_start": None,
            "memory_end": None,
            "memory_min": None,
            "memory_max": None,
            "growth_rate": None,
            "risk_level": None,
            "objects_start": None,
            "objects_end": None,
            "objects_change": None,
        }
        
        # 解析时间戳
        for line in content.split("\n"):
            if line.startswith("生成时间:"):
                report_data["timestamp"] = line.split(":", 1)[1].strip()
            elif line.startswith("监控时长:"):
                try:
                    report_data["duration"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "开始:" in line and "MB" in line:
                try:
                    report_data["memory_start"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "结束:" in line and "MB" in line:
                try:
                    report_data["memory_end"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "最小:" in line and "MB" in line:
                try:
                    report_data["memory_min"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "最大:" in line and "MB" in line:
                try:
                    report_data["memory_max"] = float(line.split(":", 1)[1].strip().split()[0])
                except:
                    pass
            elif "每小时增长率:" in line:
                try:
                    report_data["growth_rate"] = float(line.split(":", 1)[1].strip().rstrip("%"))
                except:
                    pass
            elif "泄漏风险:" in line:
                report_data["risk_level"] = line.split(":", 1)[1].strip()
            elif "对象计数" in line and "开始:" in line:
                try:
                    report_data["objects_start"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
            elif "对象计数" in line and "结束:" in line:
                try:
                    report_data["objects_end"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
            elif "对象计数" in line and "变化:" in line:
                try:
                    report_data["objects_change"] = int(line.split(":", 1)[1].strip())
                except:
                    pass
        
        return report_data
    
    def generate_summary_report(self) -> str:
        """生成汇总报告
        
        Returns:
            str: 汇总报告内容
        """
        # 收集所有报告
        memory_reports = self.collect_memory_reports()
        
        # 生成报告
        report = []
        report.append("# VisionAI-ClipsMaster 性能测试汇总报告")
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 内存报告汇总
        report.append("## 内存性能分析")
        
        if memory_reports:
            # 计算平均值
            avg_growth_rate = sum(r.get("growth_rate", 0) or 0 for r in memory_reports) / len(memory_reports)
            avg_memory_change = sum((r.get("memory_end", 0) or 0) - (r.get("memory_start", 0) or 0) for r in memory_reports) / len(memory_reports)
            
            # 风险评估
            if avg_growth_rate < 1:
                risk = "低"
            elif avg_growth_rate < 5:
                risk = "中"
            else:
                risk = "高"
            
            report.append(f"- 测试报告数量: {len(memory_reports)}")
            report.append(f"- 平均内存增长率: {avg_growth_rate:.2f}%/小时")
            report.append(f"- 平均内存变化: {avg_memory_change:.2f} MB")
            report.append(f"- 整体内存泄漏风险: {risk}")
            report.append("")
            
            # 添加详细报告
            report.append("### 内存报告详情")
            report.append("| 报告文件 | 时长(秒) | 内存起始(MB) | 内存结束(MB) | 增长率(%/小时) | 风险级别 |")
            report.append("|---------|---------|------------|------------|--------------|---------|")
            
            for r in memory_reports:
                file_name = os.path.basename(r.get("file", "未知"))
                duration = r.get("duration", 0) or 0
                mem_start = r.get("memory_start", 0) or 0
                mem_end = r.get("memory_end", 0) or 0
                growth = r.get("growth_rate", 0) or 0
                risk = r.get("risk_level", "未知")
                
                report.append(f"| {file_name} | {duration:.1f} | {mem_start:.2f} | {mem_end:.2f} | {growth:.2f} | {risk} |")
        else:
            report.append("未找到内存测试报告")
        
        report.append("")
        report.append("## 性能优化建议")
        
        # 根据测试结果提供建议
        if memory_reports:
            avg_growth = sum(r.get("growth_rate", 0) or 0 for r in memory_reports) / len(memory_reports)
            
            if avg_growth > 5:
                report.append("1. **紧急**: 应用存在严重内存泄漏风险，建议检查以下方面:")
                report.append("   - 检查资源释放是否完整，特别是大型对象")
                report.append("   - 检查循环引用问题")
                report.append("   - 确保所有线程正确终止")
            elif avg_growth > 1:
                report.append("1. **注意**: 应用存在轻微内存增长，建议关注以下方面:")
                report.append("   - 优化大型对象的生命周期管理")
                report.append("   - 检查缓存策略是否合理")
            else:
                report.append("1. **良好**: 应用内存使用稳定，建议:")
                report.append("   - 继续保持当前的内存管理策略")
                report.append("   - 定期运行内存监控以确保稳定性")
        
        report.append("")
        report.append("2. **线程管理**: 确保所有线程在应用退出时正确清理")
        report.append("   - 使用SafeThread替代标准QThread")
        report.append("   - 实现requestInterruption和isInterruptionRequested方法")
        report.append("")
        report.append("3. **大文件处理**: 对于大型视频文件处理")
        report.append("   - 考虑分块处理策略")
        report.append("   - 定期调用gc.collect()释放不再使用的资源")
        
        # 保存报告
        report_path = self.performance_dir / f"performance_summary_{time.strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        
        logger.info(f"汇总报告已生成: {report_path}")
        
        return str(report_path)

def main():
    """主函数"""
    print("\n===== 生成性能测试汇总报告 =====\n")
    
    generator = PerformanceReportGenerator()
    report_path = generator.generate_summary_report()
    
    print(f"汇总报告已生成: {report_path}")
    
    # 显示报告内容
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            print("\n" + "="*50)
            print(f.read())
            print("="*50)
    except Exception as e:
        print(f"读取报告失败: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 