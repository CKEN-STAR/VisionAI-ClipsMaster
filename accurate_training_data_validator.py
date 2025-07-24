#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
准确的训练数据验证器
基于实际的训练数据格式进行验证
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class AccurateTrainingDataValidator:
    """准确的训练数据验证器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_summary": {},
            "detailed_analysis": {},
            "quality_assessment": {},
            "recommendations": []
        }
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def validate_training_pair_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证训练数据对格式"""
        validation = {
            "is_valid": True,
            "format_score": 100,
            "issues": [],
            "strengths": []
        }
        
        # 检查必需字段
        required_fields = ["original", "viral"]
        for field in required_fields:
            if field not in data:
                validation["issues"].append(f"缺少必需字段: {field}")
                validation["is_valid"] = False
                validation["format_score"] -= 30
            elif not isinstance(data[field], str) or not data[field].strip():
                validation["issues"].append(f"字段 {field} 为空或格式错误")
                validation["is_valid"] = False
                validation["format_score"] -= 20
                
        # 检查元数据
        if "metadata" in data:
            metadata = data["metadata"]
            validation["strengths"].append("包含元数据信息")
            
            # 检查元数据字段
            metadata_fields = ["language", "genre", "quality_score"]
            for field in metadata_fields:
                if field in metadata:
                    validation["strengths"].append(f"包含{field}信息")
                else:
                    validation["issues"].append(f"元数据缺少{field}字段")
                    validation["format_score"] -= 5
        else:
            validation["issues"].append("缺少元数据")
            validation["format_score"] -= 10
            
        return validation
        
    def analyze_content_quality(self, original: str, viral: str) -> Dict[str, Any]:
        """分析内容质量"""
        analysis = {
            "content_metrics": {},
            "transformation_analysis": {},
            "quality_indicators": {},
            "issues": []
        }
        
        # 基础内容指标
        analysis["content_metrics"] = {
            "original_length": len(original),
            "viral_length": len(viral),
            "length_ratio": len(viral) / len(original) if len(original) > 0 else 0,
            "original_word_count": len(original.split()),
            "viral_word_count": len(viral.split())
        }
        
        # 转换分析
        length_ratio = analysis["content_metrics"]["length_ratio"]
        if length_ratio > 1.5:
            analysis["transformation_analysis"]["type"] = "扩展型"
            analysis["transformation_analysis"]["description"] = "爆款版本比原版更详细"
        elif length_ratio < 0.5:
            analysis["transformation_analysis"]["type"] = "压缩型"
            analysis["transformation_analysis"]["description"] = "爆款版本高度浓缩"
        else:
            analysis["transformation_analysis"]["type"] = "重构型"
            analysis["transformation_analysis"]["description"] = "爆款版本长度适中，重新组织"
            
        # 质量指标
        viral_keywords = ["震撼", "惊呆", "霸道", "突然", "反应", "所有人", "！"]
        keyword_count = sum(1 for keyword in viral_keywords if keyword in viral)
        
        analysis["quality_indicators"] = {
            "has_emotional_words": keyword_count > 0,
            "emotional_intensity": keyword_count,
            "has_exclamation": "！" in viral or "!" in viral,
            "has_suspense_elements": any(word in viral for word in ["震撼", "惊呆", "突然"]),
            "engagement_score": min(keyword_count * 20, 100)
        }
        
        # 检查潜在问题
        if len(original.strip()) < 10:
            analysis["issues"].append("原始内容过短")
        if len(viral.strip()) < 10:
            analysis["issues"].append("爆款内容过短")
        if original == viral:
            analysis["issues"].append("原始内容与爆款内容相同")
        if keyword_count == 0:
            analysis["issues"].append("爆款内容缺乏吸引力关键词")
            
        return analysis
        
    def scan_training_directory(self, dir_path: Path, language: str) -> Dict[str, Any]:
        """扫描训练数据目录"""
        results = {
            "language": language,
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "total_pairs": 0,
            "valid_pairs": 0,
            "file_details": [],
            "quality_distribution": {"high": 0, "medium": 0, "low": 0}
        }
        
        if not dir_path.exists():
            self.logger.warning(f"目录不存在: {dir_path}")
            return results
            
        # 扫描所有JSON和TXT文件
        data_files = list(dir_path.glob("*.json")) + list(dir_path.glob("*.txt"))
        results["total_files"] = len(data_files)
        
        for file_path in data_files:
            file_result = self._analyze_training_file(file_path, language)
            results["file_details"].append(file_result)
            
            if file_result["is_valid"]:
                results["valid_files"] += 1
                results["valid_pairs"] += file_result["pair_count"]
                
                # 质量分布统计
                avg_quality = file_result.get("average_quality_score", 0)
                if avg_quality >= 80:
                    results["quality_distribution"]["high"] += file_result["pair_count"]
                elif avg_quality >= 60:
                    results["quality_distribution"]["medium"] += file_result["pair_count"]
                else:
                    results["quality_distribution"]["low"] += file_result["pair_count"]
            else:
                results["invalid_files"] += 1
                
            results["total_pairs"] += file_result["pair_count"]
            
        return results
        
    def _analyze_training_file(self, file_path: Path, language: str) -> Dict[str, Any]:
        """分析单个训练文件"""
        result = {
            "file_name": file_path.name,
            "language": language,
            "is_valid": False,
            "pair_count": 0,
            "format_issues": [],
            "content_issues": [],
            "quality_scores": [],
            "average_quality_score": 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if file_path.suffix == '.json':
                try:
                    data = json.loads(content)
                    
                    if isinstance(data, dict):
                        # 单个训练对
                        pair_validation = self.validate_training_pair_format(data)
                        result["is_valid"] = pair_validation["is_valid"]
                        result["pair_count"] = 1
                        result["format_issues"] = pair_validation["issues"]
                        
                        if pair_validation["is_valid"]:
                            content_analysis = self.analyze_content_quality(
                                data["original"], data["viral"]
                            )
                            result["content_issues"] = content_analysis["issues"]
                            quality_score = content_analysis["quality_indicators"]["engagement_score"]
                            result["quality_scores"] = [quality_score]
                            result["average_quality_score"] = quality_score
                            
                    elif isinstance(data, list):
                        # 多个训练对
                        valid_pairs = 0
                        all_quality_scores = []
                        
                        for item in data:
                            if isinstance(item, dict):
                                pair_validation = self.validate_training_pair_format(item)
                                if pair_validation["is_valid"]:
                                    valid_pairs += 1
                                    content_analysis = self.analyze_content_quality(
                                        item["original"], item["viral"]
                                    )
                                    quality_score = content_analysis["quality_indicators"]["engagement_score"]
                                    all_quality_scores.append(quality_score)
                                else:
                                    result["format_issues"].extend(pair_validation["issues"])
                                    
                        result["pair_count"] = len(data)
                        result["is_valid"] = valid_pairs > 0
                        result["quality_scores"] = all_quality_scores
                        result["average_quality_score"] = sum(all_quality_scores) / len(all_quality_scores) if all_quality_scores else 0
                        
                except json.JSONDecodeError as e:
                    result["format_issues"].append(f"JSON格式错误: {str(e)}")
                    
            else:
                # TXT文件，检查是否为简单文本
                if len(content) > 0:
                    result["pair_count"] = 1
                    result["is_valid"] = True
                    # 简单文本文件的质量评估
                    result["quality_scores"] = [50]  # 默认中等质量
                    result["average_quality_score"] = 50
                else:
                    result["format_issues"].append("文件为空")
                    
        except UnicodeDecodeError:
            result["format_issues"].append("文件编码错误")
        except Exception as e:
            result["format_issues"].append(f"文件处理错误: {str(e)}")
            
        return result
        
    def generate_comprehensive_report(self) -> str:
        """生成综合报告"""
        summary = self.results["validation_summary"]
        
        lines = [
            "=" * 80,
            "VisionAI-ClipsMaster 训练数据验证报告",
            "=" * 80,
            f"验证时间: {self.results['timestamp']}",
            "",
            "📊 数据概览:",
            f"  英文训练文件: {summary.get('english', {}).get('total_files', 0)}",
            f"  中文训练文件: {summary.get('chinese', {}).get('total_files', 0)}",
            f"  总训练对数: {summary.get('total_pairs', 0)}",
            f"  有效训练对: {summary.get('valid_pairs', 0)}",
            f"  数据有效率: {summary.get('validity_rate', 0):.1f}%",
            "",
            "🎯 质量分析:",
            f"  高质量数据对: {summary.get('quality_distribution', {}).get('high', 0)}",
            f"  中等质量数据对: {summary.get('quality_distribution', {}).get('medium', 0)}",
            f"  低质量数据对: {summary.get('quality_distribution', {}).get('low', 0)}",
            f"  平均质量分数: {summary.get('average_quality', 0):.1f}/100",
            ""
        ]
        
        # 添加建议
        if self.results["recommendations"]:
            lines.extend([
                "💡 改进建议:",
                ""
            ])
            for i, rec in enumerate(self.results["recommendations"], 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")
            
        lines.extend([
            "=" * 80,
            "报告结束",
            "=" * 80
        ])
        
        return "\n".join(lines)
        
    def run_validation(self) -> Dict[str, Any]:
        """运行完整验证"""
        self.logger.info("开始准确的训练数据验证")
        
        # 扫描英文数据
        en_dir = self.project_root / "data/training/en"
        en_results = self.scan_training_directory(en_dir, "en")
        
        # 扫描中文数据
        zh_dir = self.project_root / "data/training/zh"
        zh_results = self.scan_training_directory(zh_dir, "zh")
        
        # 汇总结果
        total_pairs = en_results["total_pairs"] + zh_results["total_pairs"]
        valid_pairs = en_results["valid_pairs"] + zh_results["valid_pairs"]
        
        self.results["validation_summary"] = {
            "english": en_results,
            "chinese": zh_results,
            "total_pairs": total_pairs,
            "valid_pairs": valid_pairs,
            "validity_rate": valid_pairs / total_pairs * 100 if total_pairs > 0 else 0,
            "quality_distribution": {
                "high": en_results["quality_distribution"]["high"] + zh_results["quality_distribution"]["high"],
                "medium": en_results["quality_distribution"]["medium"] + zh_results["quality_distribution"]["medium"],
                "low": en_results["quality_distribution"]["low"] + zh_results["quality_distribution"]["low"]
            }
        }
        
        # 计算平均质量
        all_quality_scores = []
        for lang_results in [en_results, zh_results]:
            for file_detail in lang_results["file_details"]:
                all_quality_scores.extend(file_detail["quality_scores"])
                
        avg_quality = sum(all_quality_scores) / len(all_quality_scores) if all_quality_scores else 0
        self.results["validation_summary"]["average_quality"] = avg_quality
        
        # 生成建议
        self._generate_recommendations()
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"accurate_training_validation_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"验证完成，结果已保存至: {output_file}")
        return self.results
        
    def _generate_recommendations(self):
        """生成改进建议"""
        summary = self.results["validation_summary"]
        recommendations = []
        
        # 数据量建议
        if summary["total_pairs"] < 10:
            recommendations.append("训练数据总量不足，建议收集更多原片→爆款的训练对")
        elif summary["total_pairs"] < 50:
            recommendations.append("训练数据量偏少，建议增加训练样本以提高模型效果")
            
        # 质量建议
        if summary["average_quality"] < 60:
            recommendations.append("平均质量偏低，建议优化爆款内容的吸引力和表达方式")
        elif summary["average_quality"] < 80:
            recommendations.append("质量中等，建议增加更多高质量的爆款样本")
            
        # 语言平衡建议
        en_pairs = summary["english"]["valid_pairs"]
        zh_pairs = summary["chinese"]["valid_pairs"]
        
        if en_pairs == 0:
            recommendations.append("缺少英文训练数据，建议添加英文原片→爆款字幕对")
        if zh_pairs == 0:
            recommendations.append("缺少中文训练数据，建议添加中文原片→爆款字幕对")
            
        if en_pairs > 0 and zh_pairs > 0:
            ratio = min(en_pairs, zh_pairs) / max(en_pairs, zh_pairs)
            if ratio < 0.3:
                recommendations.append("中英文数据不平衡，建议增加数量较少的语言的训练样本")
                
        # 质量分布建议
        quality_dist = summary["quality_distribution"]
        high_ratio = quality_dist["high"] / summary["valid_pairs"] if summary["valid_pairs"] > 0 else 0
        
        if high_ratio < 0.3:
            recommendations.append("高质量样本比例偏低，建议增加更多优秀的爆款案例")
            
        self.results["recommendations"] = recommendations


def main():
    """主函数"""
    print("🔍 启动准确的训练数据验证")
    print("=" * 50)
    
    validator = AccurateTrainingDataValidator()
    results = validator.run_validation()
    
    # 生成并显示报告
    report = validator.generate_comprehensive_report()
    print(report)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
