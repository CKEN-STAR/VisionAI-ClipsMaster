#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
结果对比引擎

多维度评估生成结果质量的综合系统，通过视频内容相似度(50%)、
XML工程结构(30%)和性能指标(20%)的加权评分，确保输出质量符合预期标准。
"""

import os
import json
import logging
import numpy as np
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Tuple, Optional, Union
from pathlib import Path
import time
import difflib

from .metrics import calculate_ssim, calculate_psnr, optical_flow_analysis
from .golden_compare import GoldenComparator
from ..utils.file_utils import get_file_path, ensure_dir_exists
from ..utils.error_handler import handle_exception

# 配置日志
logger = logging.getLogger(__name__)

class ResultComparator:
    """
    结果对比引擎
    
    集成视频内容对比、XML结构分析和性能指标评估，提供全面的质量评估结果。
    """
    
    def __init__(self):
        """初始化结果对比引擎"""
        self.golden_comparator = GoldenComparator()
        
        # 评估维度权重
        self.weights = {
            "video_content": 0.5,    # 视频内容相似度权重
            "xml_structure": 0.3,    # XML工程结构权重
            "performance": 0.2       # 性能指标权重
        }
        
        # 性能指标内部权重
        self.performance_weights = {
            "processing_time": 0.4,   # 处理时间权重
            "memory_usage": 0.3,      # 内存使用权重
            "cpu_usage": 0.3          # CPU使用权重
        }
        
        logger.info("结果对比引擎初始化完成")
    
    def compare_results(self, 
                       generated_video: str, 
                       reference_video: Optional[str] = None,
                       generated_xml: Optional[str] = None,
                       reference_xml: Optional[str] = None,
                       performance_data: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        综合对比生成结果与参考结果
        
        Args:
            generated_video: 生成视频路径
            reference_video: 参考视频路径，如果为None则使用黄金样本中的最佳匹配
            generated_xml: 生成的XML工程文件路径
            reference_xml: 参考XML工程文件路径
            performance_data: 性能指标数据
            
        Returns:
            Dict[str, Any]: 包含多维度评估结果的字典
        """
        start_time = time.time()
        
        # 结果容器
        results = {
            "overall_score": 0.0,
            "video_content": {},
            "xml_structure": {},
            "performance": {},
            "details": {},
            "recommendations": []
        }
        
        try:
            # 1. 视频内容相似度评估 (50%)
            video_content_score = self._evaluate_video_content(generated_video, reference_video)
            results["video_content"] = video_content_score
            
            # 2. XML结构分析 (30%)
            if generated_xml and reference_xml:
                xml_structure_score = self._evaluate_xml_structure(generated_xml, reference_xml)
                results["xml_structure"] = xml_structure_score
            else:
                logger.warning("未提供XML文件路径，跳过XML结构分析")
                # 设置默认分数
                results["xml_structure"] = {
                    "score": 0.5,
                    "message": "未提供XML文件进行分析"
                }
            
            # 3. 性能指标评估 (20%)
            performance_score = self._evaluate_performance(performance_data)
            results["performance"] = performance_score
            
            # 计算加权总分
            overall_score = (
                self.weights["video_content"] * video_content_score["score"] +
                self.weights["xml_structure"] * results["xml_structure"]["score"] +
                self.weights["performance"] * performance_score["score"]
            )
            
            results["overall_score"] = round(overall_score, 2)
            
            # 添加评级
            results["rating"] = self._get_quality_rating(overall_score)
            
            # 添加建议
            results["recommendations"] = self._generate_recommendations(results)
            
            # 添加评估细节
            results["details"]["elapsed_time"] = round(time.time() - start_time, 2)
            results["details"]["evaluation_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"结果对比完成。总分: {results['overall_score']}, 评级: {results['rating']}")
            return results
            
        except Exception as e:
            error_msg = f"结果对比过程中发生错误: {str(e)}"
            logger.error(error_msg)
            handle_exception(e, error_msg)
            
            # 返回错误结果
            return {
                "overall_score": 0.0,
                "rating": "失败",
                "error": error_msg
            }
    
    def _evaluate_video_content(self, 
                               generated_video: str, 
                               reference_video: Optional[str] = None) -> Dict[str, Any]:
        """
        评估视频内容相似度
        
        使用SSIM、PSNR和光流分析评估视频质量
        
        Args:
            generated_video: 生成视频路径
            reference_video: 参考视频路径，如果为None则使用黄金样本
            
        Returns:
            Dict[str, Any]: 视频内容评估结果
        """
        try:
            # 如果没有提供参考视频，使用黄金样本中的最佳匹配
            if reference_video is None:
                best_match_id, best_match = self.golden_comparator.get_best_match(generated_video)
                reference_video = get_file_path(best_match["sample_data"]["path"])
                logger.info(f"使用黄金样本 {best_match_id} 作为参考视频")
            
            # 计算视频相似度指标
            ssim_score = calculate_ssim(generated_video, reference_video)
            psnr_score = calculate_psnr(generated_video, reference_video)
            motion_score = optical_flow_analysis(generated_video, reference_video)
            
            # 归一化PSNR (假设PSNR范围为20-50dB)
            normalized_psnr = min(max((psnr_score - 20) / 30, 0.0), 1.0)
            
            # 计算加权视频内容得分
            content_score = (
                ssim_score * 0.6 +         # SSIM权重
                normalized_psnr * 0.25 +   # PSNR权重
                motion_score * 0.15        # 运动一致性权重
            )
            
            # 评估消息
            if content_score >= 0.9:
                message = "视频内容质量极佳，与参考标准高度一致"
            elif content_score >= 0.8:
                message = "视频内容质量良好，与参考标准保持较高一致性"
            elif content_score >= 0.7:
                message = "视频内容质量尚可，与参考标准有一定差异"
            elif content_score >= 0.6:
                message = "视频内容质量一般，与参考标准存在明显差异"
            else:
                message = "视频内容质量较低，与参考标准差异显著"
            
            return {
                "score": round(content_score, 2),
                "ssim": round(ssim_score, 2),
                "psnr": round(psnr_score, 2),
                "motion_consistency": round(motion_score, 2),
                "message": message
            }
            
        except Exception as e:
            logger.error(f"视频内容评估失败: {str(e)}")
            return {
                "score": 0.5,
                "message": f"视频内容评估失败: {str(e)}"
            }
    
    def _evaluate_xml_structure(self, generated_xml: str, reference_xml: str) -> Dict[str, Any]:
        """
        评估XML工程结构差异
        
        分析生成XML与参考XML之间的结构相似度
        
        Args:
            generated_xml: 生成的XML文件路径
            reference_xml: 参考XML文件路径
            
        Returns:
            Dict[str, Any]: XML结构评估结果
        """
        try:
            # 加载XML文件
            with open(generated_xml, 'r', encoding='utf-8') as f:
                generated_content = f.readlines()
                
            with open(reference_xml, 'r', encoding='utf-8') as f:
                reference_content = f.readlines()
            
            # 使用difflib计算差异
            differ = difflib.Differ()
            diff = list(differ.compare(reference_content, generated_content))
            
            # 计算差异比例
            total_lines = len(reference_content)
            different_lines = sum(1 for line in diff if line.startswith('+ ') or line.startswith('- '))
            similarity = 1.0 - (different_lines / (total_lines * 2))  # 归一化到0-1
            
            # 分析XML结构
            gen_tree = ET.parse(generated_xml)
            ref_tree = ET.parse(reference_xml)
            
            gen_root = gen_tree.getroot()
            ref_root = ref_tree.getroot()
            
            # 比较关键元素数量
            gen_clips = len(gen_root.findall(".//clip"))
            ref_clips = len(ref_root.findall(".//clip"))
            
            # 计算结构一致性得分
            structural_score = min(gen_clips / max(ref_clips, 1), 1.0) if gen_clips <= ref_clips else min(ref_clips / gen_clips, 1.0)
            
            # 组合综合得分 (文本相似度60%，结构一致性40%)
            xml_score = similarity * 0.6 + structural_score * 0.4
            
            # 评估消息
            if xml_score >= 0.9:
                message = "XML结构一致性极高，工程文件结构完整"
            elif xml_score >= 0.8:
                message = "XML结构一致性良好，工程结构基本完整"
            elif xml_score >= 0.7:
                message = "XML结构一致性尚可，存在部分结构差异"
            elif xml_score >= 0.6:
                message = "XML结构一致性一般，工程结构有明显差异"
            else:
                message = "XML结构一致性较低，工程结构差异显著"
            
            return {
                "score": round(xml_score, 2),
                "text_similarity": round(similarity, 2),
                "structural_consistency": round(structural_score, 2),
                "generated_clips": gen_clips,
                "reference_clips": ref_clips,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"XML结构评估失败: {str(e)}")
            return {
                "score": 0.5,
                "message": f"XML结构评估失败: {str(e)}"
            }
    
    def _evaluate_performance(self, performance_data: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        评估性能指标
        
        分析处理时间、内存使用和CPU利用率等性能指标
        
        Args:
            performance_data: 性能指标数据，包括处理时间、内存使用和CPU利用率
            
        Returns:
            Dict[str, Any]: 性能评估结果
        """
        try:
            if performance_data is None:
                logger.warning("未提供性能数据，使用默认评分")
                return {
                    "score": 0.7,  # 默认中等分数
                    "message": "未提供性能数据进行评估"
                }
            
            # 提取性能指标
            processing_time = performance_data.get("processing_time", 300)  # 默认300秒
            memory_usage = performance_data.get("memory_usage", 2000)       # 默认2000MB
            cpu_usage = performance_data.get("cpu_usage", 50)               # 默认50%
            
            # 归一化处理时间 (假设目标处理时间为30-600秒)
            time_score = 1.0 - min(max((processing_time - 30) / 570, 0.0), 1.0)
            
            # 归一化内存使用 (假设目标内存为500-4000MB)
            memory_score = 1.0 - min(max((memory_usage - 500) / 3500, 0.0), 1.0)
            
            # 归一化CPU使用率 (假设目标CPU使用率为10-100%)
            cpu_score = 1.0 - min(max((cpu_usage - 10) / 90, 0.0), 1.0)
            
            # 计算加权性能得分
            performance_score = (
                time_score * self.performance_weights["processing_time"] +
                memory_score * self.performance_weights["memory_usage"] +
                cpu_score * self.performance_weights["cpu_usage"]
            )
            
            # 评估消息
            if performance_score >= 0.9:
                message = "性能表现极佳，资源利用效率高"
            elif performance_score >= 0.8:
                message = "性能表现良好，资源利用合理"
            elif performance_score >= 0.7:
                message = "性能表现尚可，资源利用基本合理"
            elif performance_score >= 0.6:
                message = "性能表现一般，存在资源利用效率问题"
            else:
                message = "性能表现较差，资源利用效率低"
            
            return {
                "score": round(performance_score, 2),
                "time_score": round(time_score, 2),
                "memory_score": round(memory_score, 2),
                "cpu_score": round(cpu_score, 2),
                "processing_time": processing_time,
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"性能指标评估失败: {str(e)}")
            return {
                "score": 0.5,
                "message": f"性能指标评估失败: {str(e)}"
            }
    
    def _get_quality_rating(self, score: float) -> str:
        """
        获取质量评级
        
        根据综合得分确定质量等级
        
        Args:
            score: 综合质量得分 (0-1)
            
        Returns:
            str: 质量评级
        """
        if score >= 0.9:
            return "卓越"
        elif score >= 0.8:
            return "优秀"
        elif score >= 0.7:
            return "良好"
        elif score >= 0.6:
            return "合格"
        elif score >= 0.5:
            return "一般"
        else:
            return "不合格"
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """
        生成改进建议
        
        根据评估结果生成具体改进建议
        
        Args:
            results: 评估结果
            
        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []
        
        # 视频内容建议
        video_score = results["video_content"].get("score", 0)
        if video_score < 0.7:
            ssim = results["video_content"].get("ssim", 0)
            psnr = results["video_content"].get("psnr", 0)
            motion = results["video_content"].get("motion_consistency", 0)
            
            if ssim < 0.8:
                recommendations.append("提高视频结构相似性，检查画面构图和场景转换是否符合原始风格")
            
            if psnr < 35:
                recommendations.append("提高视频信号质量，检查输出分辨率和编码参数")
            
            if motion < 0.7:
                recommendations.append("改善动作连贯性，减少跳跃性剪辑，保持自然流畅的动作过渡")
        
        # XML结构建议
        xml_score = results["xml_structure"].get("score", 0)
        if xml_score < 0.7:
            struct_score = results["xml_structure"].get("structural_consistency", 0)
            
            if struct_score < 0.7:
                recommendations.append("提高XML工程结构完整性，确保生成的剪辑片段数量接近参考标准")
        
        # 性能建议
        perf_score = results["performance"].get("score", 0)
        if perf_score < 0.7:
            time_score = results["performance"].get("time_score", 0)
            memory_score = results["performance"].get("memory_score", 0)
            cpu_score = results["performance"].get("cpu_score", 0)
            
            if time_score < 0.6:
                recommendations.append("优化处理流程，减少总处理时间")
            
            if memory_score < 0.6:
                recommendations.append("优化内存使用，避免不必要的大型数据结构和冗余数据")
            
            if cpu_score < 0.6:
                recommendations.append("优化计算密集型操作，考虑使用更高效的算法或并行处理")
        
        # 如果没有具体建议，添加一般性建议
        if not recommendations:
            if results["overall_score"] >= 0.8:
                recommendations.append("当前生成质量良好，可以考虑微调参数进一步提高质量")
            else:
                recommendations.append("综合优化生成过程，平衡内容质量与性能表现")
        
        return recommendations

    def save_results(self, results: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        保存评估结果为JSON文件
        
        Args:
            results: 评估结果
            output_path: 输出路径，如果为None则使用默认路径
            
        Returns:
            str: 保存的文件路径
        """
        try:
            if output_path is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join("outputs", "quality_reports")
                ensure_dir_exists(output_dir)
                output_path = os.path.join(output_dir, f"quality_report_{timestamp}.json")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"评估结果已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"保存评估结果失败: {str(e)}")
            return ""


def compare_results(
    generated_video: str,
    reference_video: Optional[str] = None,
    generated_xml: Optional[str] = None,
    reference_xml: Optional[str] = None,
    performance_data: Optional[Dict[str, float]] = None,
    save_output: bool = True
) -> Dict[str, Any]:
    """
    便捷函数：比较生成结果与参考结果
    
    Args:
        generated_video: 生成视频路径
        reference_video: 参考视频路径，如果为None则使用黄金样本
        generated_xml: 生成的XML工程文件路径
        reference_xml: 参考XML工程文件路径
        performance_data: 性能指标数据
        save_output: 是否保存评估结果
        
    Returns:
        Dict[str, Any]: 评估结果
    """
    comparator = ResultComparator()
    results = comparator.compare_results(
        generated_video, 
        reference_video,
        generated_xml,
        reference_xml,
        performance_data
    )
    
    if save_output:
        comparator.save_results(results)
    
    return results 