#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练数据验证测试
专门验证"原片字幕→爆款字幕"的训练数据对格式和质量
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class TrainingDataValidator:
    """训练数据验证器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {},
            "data_quality_metrics": {},
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
        
    def validate_srt_format(self, srt_content: str) -> Dict[str, Any]:
        """验证SRT字幕格式"""
        lines = srt_content.strip().split('\n')
        
        validation = {
            "is_valid": True,
            "subtitle_count": 0,
            "format_errors": [],
            "time_format_errors": [],
            "encoding_issues": []
        }
        
        i = 0
        subtitle_count = 0
        
        while i < len(lines):
            # 跳过空行
            while i < len(lines) and not lines[i].strip():
                i += 1
                
            if i >= len(lines):
                break
                
            # 检查序号
            if not lines[i].strip().isdigit():
                validation["format_errors"].append(f"行 {i+1}: 序号格式错误")
                validation["is_valid"] = False
                i += 1
                continue
                
            i += 1
            if i >= len(lines):
                validation["format_errors"].append("文件意外结束")
                break
                
            # 检查时间轴格式
            time_line = lines[i].strip()
            if "-->" not in time_line:
                validation["format_errors"].append(f"行 {i+1}: 时间轴格式错误")
                validation["is_valid"] = False
            else:
                # 验证时间格式 (HH:MM:SS,mmm --> HH:MM:SS,mmm)
                parts = time_line.split(" --> ")
                if len(parts) != 2:
                    validation["time_format_errors"].append(f"行 {i+1}: 时间轴分隔符错误")
                else:
                    for part in parts:
                        if not self._is_valid_time_format(part.strip()):
                            validation["time_format_errors"].append(f"行 {i+1}: 时间格式错误 - {part}")
                            
            i += 1
            
            # 读取字幕文本
            subtitle_text = []
            while i < len(lines) and lines[i].strip():
                subtitle_text.append(lines[i])
                i += 1
                
            if not subtitle_text:
                validation["format_errors"].append(f"字幕 {subtitle_count + 1}: 缺少字幕文本")
                
            subtitle_count += 1
            
        validation["subtitle_count"] = subtitle_count
        return validation
        
    def _is_valid_time_format(self, time_str: str) -> bool:
        """检查时间格式是否正确"""
        try:
            # 格式: HH:MM:SS,mmm
            if ',' not in time_str:
                return False
            time_part, ms_part = time_str.split(',')
            if len(ms_part) != 3:
                return False
            time_components = time_part.split(':')
            if len(time_components) != 3:
                return False
            hours, minutes, seconds = map(int, time_components)
            milliseconds = int(ms_part)
            return 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59 and 0 <= milliseconds <= 999
        except:
            return False
            
    def validate_training_pair(self, original_srt: str, viral_srt: str) -> Dict[str, Any]:
        """验证训练数据对"""
        validation = {
            "pair_valid": True,
            "original_validation": {},
            "viral_validation": {},
            "pair_analysis": {},
            "issues": []
        }
        
        # 验证原片字幕
        validation["original_validation"] = self.validate_srt_format(original_srt)
        
        # 验证爆款字幕
        validation["viral_validation"] = self.validate_srt_format(viral_srt)
        
        # 分析数据对关系
        if validation["original_validation"]["is_valid"] and validation["viral_validation"]["is_valid"]:
            original_count = validation["original_validation"]["subtitle_count"]
            viral_count = validation["viral_validation"]["subtitle_count"]
            
            validation["pair_analysis"] = {
                "original_subtitle_count": original_count,
                "viral_subtitle_count": viral_count,
                "compression_ratio": viral_count / original_count if original_count > 0 else 0,
                "is_compressed": viral_count < original_count,
                "compression_percentage": (1 - viral_count / original_count) * 100 if original_count > 0 else 0
            }
            
            # 检查压缩比是否合理
            compression_ratio = validation["pair_analysis"]["compression_ratio"]
            if compression_ratio < 0.1:  # 压缩过度
                validation["issues"].append("压缩比过低，可能丢失重要剧情")
                validation["pair_valid"] = False
            elif compression_ratio > 0.9:  # 几乎没有压缩
                validation["issues"].append("压缩比过高，与原片差异不大")
                validation["pair_valid"] = False
                
        else:
            validation["pair_valid"] = False
            if not validation["original_validation"]["is_valid"]:
                validation["issues"].append("原片字幕格式无效")
            if not validation["viral_validation"]["is_valid"]:
                validation["issues"].append("爆款字幕格式无效")
                
        return validation
        
    def scan_training_data(self) -> Dict[str, Any]:
        """扫描所有训练数据"""
        results = {
            "english_data": {"valid_pairs": 0, "invalid_pairs": 0, "total_files": 0},
            "chinese_data": {"valid_pairs": 0, "invalid_pairs": 0, "total_files": 0},
            "detailed_results": [],
            "quality_metrics": {}
        }
        
        # 扫描英文训练数据
        en_dir = self.project_root / "data/training/en"
        if en_dir.exists():
            en_results = self._scan_language_data(en_dir, "en")
            results["english_data"].update(en_results)
            
        # 扫描中文训练数据
        zh_dir = self.project_root / "data/training/zh"
        if zh_dir.exists():
            zh_results = self._scan_language_data(zh_dir, "zh")
            results["chinese_data"].update(zh_results)
            
        # 计算整体质量指标
        total_valid = results["english_data"]["valid_pairs"] + results["chinese_data"]["valid_pairs"]
        total_invalid = results["english_data"]["invalid_pairs"] + results["chinese_data"]["invalid_pairs"]
        total_pairs = total_valid + total_invalid
        
        results["quality_metrics"] = {
            "total_training_pairs": total_pairs,
            "valid_pairs": total_valid,
            "invalid_pairs": total_invalid,
            "validity_rate": total_valid / total_pairs * 100 if total_pairs > 0 else 0,
            "data_quality_score": self._calculate_quality_score(results)
        }
        
        return results
        
    def _scan_language_data(self, data_dir: Path, language: str) -> Dict[str, Any]:
        """扫描特定语言的训练数据"""
        results = {
            "valid_pairs": 0,
            "invalid_pairs": 0,
            "total_files": 0,
            "file_details": []
        }
        
        # 查找训练数据文件
        data_files = list(data_dir.glob("*.json")) + list(data_dir.glob("*.txt"))
        results["total_files"] = len(data_files)
        
        for file_path in data_files:
            try:
                file_result = self._validate_training_file(file_path, language)
                results["file_details"].append(file_result)
                
                if file_result["is_valid"]:
                    results["valid_pairs"] += file_result.get("pair_count", 0)
                else:
                    results["invalid_pairs"] += 1
                    
            except Exception as e:
                self.logger.error(f"处理文件 {file_path} 时出错: {e}")
                results["invalid_pairs"] += 1
                
        return results
        
    def _validate_training_file(self, file_path: Path, language: str) -> Dict[str, Any]:
        """验证单个训练文件"""
        result = {
            "file_name": file_path.name,
            "language": language,
            "is_valid": False,
            "pair_count": 0,
            "issues": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if file_path.suffix == '.json':
                # JSON格式的训练数据
                data = json.loads(content)
                if isinstance(data, dict) and "original_srt" in data and "viral_srt" in data:
                    validation = self.validate_training_pair(data["original_srt"], data["viral_srt"])
                    result["is_valid"] = validation["pair_valid"]
                    result["pair_count"] = 1
                    result["issues"] = validation["issues"]
                elif isinstance(data, list):
                    # 多个训练对
                    valid_pairs = 0
                    for item in data:
                        if isinstance(item, dict) and "original_srt" in item and "viral_srt" in item:
                            validation = self.validate_training_pair(item["original_srt"], item["viral_srt"])
                            if validation["pair_valid"]:
                                valid_pairs += 1
                            else:
                                result["issues"].extend(validation["issues"])
                    result["pair_count"] = len(data)
                    result["is_valid"] = valid_pairs > 0
                else:
                    result["issues"].append("JSON格式不符合训练数据要求")
            else:
                # 文本格式，假设是简单的字幕文件
                if self.validate_srt_format(content)["is_valid"]:
                    result["is_valid"] = True
                    result["pair_count"] = 1
                else:
                    result["issues"].append("字幕格式无效")
                    
        except json.JSONDecodeError:
            result["issues"].append("JSON格式错误")
        except UnicodeDecodeError:
            result["issues"].append("文件编码错误")
        except Exception as e:
            result["issues"].append(f"文件处理错误: {str(e)}")
            
        return result
        
    def _calculate_quality_score(self, results: Dict[str, Any]) -> float:
        """计算数据质量分数"""
        en_data = results["english_data"]
        zh_data = results["chinese_data"]
        
        # 基础分数：有效性
        total_valid = en_data["valid_pairs"] + zh_data["valid_pairs"]
        total_pairs = total_valid + en_data["invalid_pairs"] + zh_data["invalid_pairs"]
        validity_score = total_valid / total_pairs * 100 if total_pairs > 0 else 0
        
        # 数据平衡性分数
        balance_score = 100
        if total_valid > 0:
            en_ratio = en_data["valid_pairs"] / total_valid
            zh_ratio = zh_data["valid_pairs"] / total_valid
            # 理想情况是中英文数据各占50%
            balance_score = 100 - abs(en_ratio - 0.5) * 200
            
        # 数据量充足性分数
        volume_score = min(total_valid / 10 * 100, 100)  # 假设10对是基本要求
        
        # 综合分数
        quality_score = (validity_score * 0.5 + balance_score * 0.3 + volume_score * 0.2)
        return round(quality_score, 2)
        
    def generate_recommendations(self, scan_results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        quality_score = scan_results["quality_metrics"]["data_quality_score"]
        validity_rate = scan_results["quality_metrics"]["validity_rate"]
        
        if validity_rate < 80:
            recommendations.append("数据有效性不足，建议检查和修复无效的训练数据对")
            
        if quality_score < 70:
            recommendations.append("整体数据质量偏低，建议增加高质量训练样本")
            
        en_pairs = scan_results["english_data"]["valid_pairs"]
        zh_pairs = scan_results["chinese_data"]["valid_pairs"]
        
        if en_pairs == 0:
            recommendations.append("缺少英文训练数据，建议添加英文原片→爆款字幕对")
        elif en_pairs < 5:
            recommendations.append("英文训练数据不足，建议增加更多英文训练样本")
            
        if zh_pairs == 0:
            recommendations.append("缺少中文训练数据，建议添加中文原片→爆款字幕对")
        elif zh_pairs < 5:
            recommendations.append("中文训练数据不足，建议增加更多中文训练样本")
            
        total_pairs = scan_results["quality_metrics"]["total_training_pairs"]
        if total_pairs < 10:
            recommendations.append("训练数据总量不足，建议收集更多原片→爆款的训练对")
            
        return recommendations
        
    def run_validation(self) -> Dict[str, Any]:
        """运行完整的训练数据验证"""
        self.logger.info("开始训练数据验证")
        
        # 扫描训练数据
        scan_results = self.scan_training_data()
        self.results["validation_results"] = scan_results
        
        # 生成建议
        recommendations = self.generate_recommendations(scan_results)
        self.results["recommendations"] = recommendations
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"training_data_validation_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
            
        self.logger.info(f"验证完成，结果已保存至: {output_file}")
        return self.results


def main():
    """主函数"""
    print("🔍 启动训练数据验证测试")
    print("=" * 50)
    
    validator = TrainingDataValidator()
    results = validator.run_validation()
    
    # 显示结果摘要
    metrics = results["validation_results"]["quality_metrics"]
    print(f"\n📊 验证结果摘要:")
    print(f"  总训练对数: {metrics['total_training_pairs']}")
    print(f"  有效训练对: {metrics['valid_pairs']}")
    print(f"  无效训练对: {metrics['invalid_pairs']}")
    print(f"  有效性率: {metrics['validity_rate']:.1f}%")
    print(f"  数据质量分数: {metrics['data_quality_score']:.1f}/100")
    
    # 显示建议
    if results["recommendations"]:
        print(f"\n💡 改进建议:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. {rec}")
    else:
        print(f"\n✅ 训练数据质量良好，无需特别改进")
        
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
