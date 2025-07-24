#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多维度比对引擎

此模块用于实现多维度比对算法，比较视频和字幕在不同维度上的相似度，
包括视频时长、分辨率、色彩分布、关键帧质量，以及字幕时间码对齐、文本相似度、实体匹配等维度。
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union
import json
import re
from difflib import SequenceMatcher
import scipy.spatial.distance as distance
from datetime import datetime

# 添加项目根目录到系统路径
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

# 导入项目模块
try:
    from tests.golden_samples.video_fingerprint import VideoFingerprint, extract_video_signature
    from src.utils.subtitle_parser import parse_subtitle
except ImportError:
    # 提供基本的模拟实现，以便模块可以独立运行
    def extract_video_signature(video_path):
        """模拟视频指纹提取"""
        return np.random.rand(256)
    
    def parse_subtitle(subtitle_path):
        """模拟字幕解析"""
        return [{"start": i, "end": i+2, "text": f"字幕行 {i}"} for i in range(0, 10, 2)]

class CompareResult:
    """比对结果类"""
    
    def __init__(self, scores: Dict[str, Union[float, Dict[str, float]]], threshold: float = 0.8):
        """
        初始化比对结果
        
        Args:
            scores: 各维度得分
            threshold: 通过阈值
        """
        self.scores = scores
        self.threshold = threshold
        
        # 计算总分
        self._calculate_total_score()
    
    def _calculate_total_score(self):
        """计算总体得分"""
        # 计算视频和字幕的平均分
        video_scores = []
        subtitle_scores = []
        
        for key, value in self.scores.items():
            if isinstance(value, dict):
                # 如果是子类别，计算其平均分
                category_avg = sum(value.values()) / len(value)
                if key == "video":
                    video_scores.append(category_avg)
                elif key == "subtitle":
                    subtitle_scores.append(category_avg)
            else:
                # 单独的分数
                if key.startswith("video_"):
                    video_scores.append(value)
                elif key.startswith("subtitle_"):
                    subtitle_scores.append(value)
        
        # 计算视频和字幕的得分
        self.video_score = sum(video_scores) / len(video_scores) if video_scores else 0
        self.subtitle_score = sum(subtitle_scores) / len(subtitle_scores) if subtitle_scores else 0
        
        # 计算总分 (视频和字幕各占50%)
        self.total_score = (self.video_score + self.subtitle_score) / 2
    
    def is_passed(self) -> bool:
        """检查是否通过阈值"""
        return self.total_score >= self.threshold
    
    def format_score(self, score: float) -> str:
        """格式化分数"""
        return f"{score:.2f} ({score*100:.0f}%)"
    
    def __str__(self) -> str:
        """格式化比对结果"""
        result = [
            "多维度比对结果:",
            "=" * 50,
            f"总体得分: {self.format_score(self.total_score)} {'✓' if self.is_passed() else '✗'}",
            f"视频得分: {self.format_score(self.video_score)}",
            f"字幕得分: {self.format_score(self.subtitle_score)}",
            "-" * 50,
            "详细分数:"
        ]
        
        # 添加详细得分
        for category, scores in self.scores.items():
            if isinstance(scores, dict):
                result.append(f"  {category}:")
                for name, score in scores.items():
                    result.append(f"    {name}: {self.format_score(score)}")
            else:
                result.append(f"  {category}: {self.format_score(scores)}")
        
        return "\n".join(result)

class GoldenComparator:
    """黄金样本比对器"""
    
    def __init__(self, test_output: str, golden_sample: str = None):
        """
        初始化比对器
        
        Args:
            test_output: 测试输出文件前缀
            golden_sample: 黄金样本文件前缀，若为None则自动推断
        """
        # 测试文件
        self.test_video = test_output + ".mp4"
        self.test_srt = test_output + ".srt"
        
        # 如果未提供黄金样本，尝试自动推断
        if golden_sample is None:
            # 自动推断黄金样本
            test_dir = os.path.dirname(test_output)
            test_name = os.path.basename(test_output)
            
            # 尝试在黄金样本目录中查找匹配的样本
            golden_dir = os.path.join(project_root, "tests", "golden_samples")
            
            # 尝试zh和en两个子目录
            for lang in ["zh", "en"]:
                potential_golden = os.path.join(golden_dir, lang, test_name)
                if os.path.exists(potential_golden + ".mp4"):
                    golden_sample = potential_golden
                    break
            
            # 如果没找到，使用同目录下的golden_前缀文件
            if golden_sample is None and os.path.exists(os.path.join(test_dir, f"golden_{test_name}.mp4")):
                golden_sample = os.path.join(test_dir, f"golden_{test_name}")
        
        if golden_sample:
            self.golden_video = golden_sample + ".mp4"
            self.golden_srt = golden_sample + ".srt"
        else:
            raise ValueError(f"无法找到匹配的黄金样本: {test_output}")
        
        # 验证文件存在
        if not os.path.exists(self.test_video):
            raise FileNotFoundError(f"测试视频不存在: {self.test_video}")
        if not os.path.exists(self.test_srt):
            raise FileNotFoundError(f"测试字幕不存在: {self.test_srt}")
        if not os.path.exists(self.golden_video):
            raise FileNotFoundError(f"黄金样本视频不存在: {self.golden_video}")
        if not os.path.exists(self.golden_srt):
            raise FileNotFoundError(f"黄金样本字幕不存在: {self.golden_srt}")
        
        # 初始化视频指纹提取器
        self.fingerprinter = VideoFingerprint()
    
    def compare(self) -> CompareResult:
        """
        执行多维度比对
        
        Returns:
            CompareResult: 比对结果
        """
        # 视频比对
        video_scores = self.video_compare()
        
        # 字幕比对
        subtitle_scores = self.subtitle_compare()
        
        # 合并得分
        scores = {
            "video": video_scores,
            "subtitle": subtitle_scores
        }
        
        # 返回比对结果
        return CompareResult(scores)
    
    def video_compare(self) -> Dict[str, float]:
        """
        视频多维度比对
        
        Returns:
            Dict[str, float]: 各维度得分
        """
        # 获取视频基本信息
        test_info = self._get_video_info(self.test_video)
        golden_info = self._get_video_info(self.golden_video)
        
        # 计算各维度得分
        return {
            "duration": self._score_duration(test_info["duration"], golden_info["duration"]),
            "resolution": self._score_resolution(test_info["width"], test_info["height"], 
                                              golden_info["width"], golden_info["height"]),
            "color_hist": self._score_color_histogram(),
            "fingerprint": self._score_video_fingerprint(),
            "keyframe_psnr": self._score_keyframe_psnr()
        }
    
    def subtitle_compare(self) -> Dict[str, float]:
        """
        字幕多维度比对
        
        Returns:
            Dict[str, float]: 各维度得分
        """
        # 解析字幕
        test_subs = self._parse_srt(self.test_srt)
        golden_subs = self._parse_srt(self.golden_srt)
        
        # 如果字幕为空，返回零分
        if not test_subs or not golden_subs:
            return {
                "timecode": 0.0,
                "text_sim": 0.0,
                "entity_match": 0.0,
                "length_ratio": 0.0
            }
        
        # 计算各维度得分
        return {
            "timecode": self._score_timecode_alignment(test_subs, golden_subs),
            "text_sim": self._score_text_similarity(test_subs, golden_subs),
            "entity_match": self._score_entity_matching(test_subs, golden_subs),
            "length_ratio": self._score_length_ratio(test_subs, golden_subs)
        }
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        cap = cv2.VideoCapture(video_path)
        
        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
        
        # 计算时长
        if info["fps"] > 0 and info["frame_count"] > 0:
            info["duration"] = info["frame_count"] / info["fps"]
        else:
            # 如果无法获取帧数或帧率，尝试手动计算
            frame_count = 0
            while True:
                ret, _ = cap.read()
                if not ret:
                    break
                frame_count += 1
            
            cap.release()
            cap = cv2.VideoCapture(video_path)
            info["frame_count"] = frame_count
            info["duration"] = frame_count / info["fps"] if info["fps"] > 0 else 0
        
        cap.release()
        return info
    
    def _parse_srt(self, srt_path: str) -> List[Dict[str, Any]]:
        """解析SRT字幕文件"""
        try:
            return parse_subtitle(srt_path)
        except Exception as e:
            print(f"解析字幕文件出错: {srt_path}, {str(e)}")
            return []
    
    def _score_duration(self, test_duration: float, golden_duration: float) -> float:
        """
        计算时长相似度得分
        
        Args:
            test_duration: 测试视频时长
            golden_duration: 黄金样本时长
            
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        if golden_duration == 0:
            return 0.0
        
        # 计算时长差异比例
        diff_ratio = abs(test_duration - golden_duration) / golden_duration
        
        # 将差异转换为得分，差异越小得分越高
        # 允许0.5秒的时长差异
        if diff_ratio < 0.01:  # 1%以内视为完全匹配
            return 1.0
        elif diff_ratio < 0.05:  # 5%以内
            return 0.9
        elif diff_ratio < 0.1:  # 10%以内
            return 0.7
        elif diff_ratio < 0.2:  # 20%以内
            return 0.5
        elif diff_ratio < 0.3:  # 30%以内
            return 0.3
        else:
            return 0.0
    
    def _score_resolution(self, test_width: int, test_height: int, 
                        golden_width: int, golden_height: int) -> float:
        """
        计算分辨率相似度得分
        
        Args:
            test_width: 测试视频宽度
            test_height: 测试视频高度
            golden_width: 黄金样本宽度
            golden_height: 黄金样本高度
            
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        if golden_width == 0 or golden_height == 0:
            return 0.0
        
        # 计算分辨率差异比例
        width_ratio = test_width / golden_width
        height_ratio = test_height / golden_height
        
        # 计算宽高比差异
        test_aspect = test_width / test_height
        golden_aspect = golden_width / golden_height
        aspect_diff = abs(test_aspect - golden_aspect) / golden_aspect
        
        # 如果是相同分辨率，直接返回1.0
        if test_width == golden_width and test_height == golden_height:
            return 1.0
        
        # 如果宽高比一致（允许2%误差），但分辨率不同，可能是缩放版本
        if aspect_diff < 0.02:
            # 检查是否为常见的缩放比例（0.5x, 0.75x, 1.5x, 2x等）
            common_scales = [0.25, 0.5, 0.75, 1.25, 1.5, 2.0, 4.0]
            for scale in common_scales:
                if abs(width_ratio - scale) < 0.05:
                    return 0.9  # 常见缩放比例，给予较高分数
            
            # 其他缩放比例
            return 0.8
        
        # 如果宽高比也不一致，可能是裁剪或填充
        return 0.5 * (1 - min(aspect_diff, 1.0))
    
    def _score_color_histogram(self) -> float:
        """
        计算颜色直方图相似度得分
        
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        # 打开两个视频
        test_cap = cv2.VideoCapture(self.test_video)
        golden_cap = cv2.VideoCapture(self.golden_video)
        
        # 获取视频基本信息
        test_info = self._get_video_info(self.test_video)
        golden_info = self._get_video_info(self.golden_video)
        
        # 确定采样帧数和间隔
        sample_count = min(5, min(test_info["frame_count"], golden_info["frame_count"]))
        if sample_count <= 0:
            return 0.0
        
        test_interval = max(1, test_info["frame_count"] // sample_count)
        golden_interval = max(1, golden_info["frame_count"] // sample_count)
        
        # 计算平均直方图相似度
        similarities = []
        
        for i in range(sample_count):
            # 设置测试视频位置
            test_pos = i * test_interval
            test_cap.set(cv2.CAP_PROP_POS_FRAMES, test_pos)
            ret_test, test_frame = test_cap.read()
            
            # 设置黄金样本位置
            golden_pos = i * golden_interval
            golden_cap.set(cv2.CAP_PROP_POS_FRAMES, golden_pos)
            ret_golden, golden_frame = golden_cap.read()
            
            # 如果读取失败，跳过
            if not ret_test or not ret_golden:
                continue
            
            # 计算HSV直方图
            test_hist = self._calculate_color_histogram(test_frame)
            golden_hist = self._calculate_color_histogram(golden_frame)
            
            # 比较直方图
            similarity = cv2.compareHist(test_hist, golden_hist, cv2.HISTCMP_CORREL)
            similarities.append(max(0, similarity))  # 确保值在0-1之间
        
        # 释放视频
        test_cap.release()
        golden_cap.release()
        
        # 计算平均相似度
        if not similarities:
            return 0.0
        
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity
    
    def _calculate_color_histogram(self, frame):
        """计算HSV色彩直方图"""
        # 转换为HSV空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算直方图
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        
        # 归一化
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        
        return hist
    
    def _score_video_fingerprint(self) -> float:
        """
        计算视频指纹相似度得分
        
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        try:
            # 使用视频指纹提取引擎
            test_sig = extract_video_signature(self.test_video)
            golden_sig = extract_video_signature(self.golden_video)
            
            # 计算余弦相似度
            similarity = 1 - distance.cosine(test_sig, golden_sig)
            
            # 归一化到0-1之间
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            print(f"计算视频指纹相似度出错: {str(e)}")
            return 0.0
    
    def _score_keyframe_psnr(self) -> float:
        """
        计算关键帧PSNR得分
        
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        # 打开两个视频
        test_cap = cv2.VideoCapture(self.test_video)
        golden_cap = cv2.VideoCapture(self.golden_video)
        
        # 获取视频基本信息
        test_info = self._get_video_info(self.test_video)
        golden_info = self._get_video_info(self.golden_video)
        
        # 确定采样帧数和间隔
        sample_count = min(3, min(test_info["frame_count"], golden_info["frame_count"]))
        if sample_count <= 0:
            return 0.0
        
        test_interval = max(1, test_info["frame_count"] // sample_count)
        golden_interval = max(1, golden_info["frame_count"] // sample_count)
        
        # 计算平均PSNR
        psnr_values = []
        
        for i in range(sample_count):
            # 设置测试视频位置
            test_pos = i * test_interval
            test_cap.set(cv2.CAP_PROP_POS_FRAMES, test_pos)
            ret_test, test_frame = test_cap.read()
            
            # 设置黄金样本位置
            golden_pos = i * golden_interval
            golden_cap.set(cv2.CAP_PROP_POS_FRAMES, golden_pos)
            ret_golden, golden_frame = golden_cap.read()
            
            # 如果读取失败，跳过
            if not ret_test or not ret_golden:
                continue
            
            # 调整大小以匹配
            if test_frame.shape != golden_frame.shape:
                test_frame = cv2.resize(test_frame, (golden_frame.shape[1], golden_frame.shape[0]))
            
            # 计算PSNR
            mse = np.mean((test_frame.astype(np.float64) - golden_frame.astype(np.float64)) ** 2)
            if mse == 0:
                psnr = 100.0  # 完全相同
            else:
                psnr = 10 * np.log10((255.0 ** 2) / mse)
            
            psnr_values.append(psnr)
        
        # 释放视频
        test_cap.release()
        golden_cap.release()
        
        # 计算平均PSNR并归一化到0-1之间
        if not psnr_values:
            return 0.0
        
        avg_psnr = sum(psnr_values) / len(psnr_values)
        
        # PSNR到得分的映射:
        # PSNR >= 40 dB: 优秀(1.0)
        # PSNR >= 30 dB: 良好(0.8)
        # PSNR >= 25 dB: 一般(0.6)
        # PSNR >= 20 dB: 较差(0.4)
        # PSNR < 20 dB: 差(0.2)
        
        if avg_psnr >= 40:
            return 1.0
        elif avg_psnr >= 30:
            return 0.8
        elif avg_psnr >= 25:
            return 0.6
        elif avg_psnr >= 20:
            return 0.4
        else:
            return max(0.0, 0.2)
    
    def _score_timecode_alignment(self, test_subs: List[Dict[str, Any]], golden_subs: List[Dict[str, Any]]) -> float:
        """
        计算字幕时间码对齐度得分
        
        Args:
            test_subs: 测试字幕
            golden_subs: 黄金样本字幕
            
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        if not test_subs or not golden_subs:
            return 0.0
        
        # 字幕数量差异
        count_diff = abs(len(test_subs) - len(golden_subs)) / max(len(test_subs), len(golden_subs))
        count_score = 1.0 - min(1.0, count_diff)
        
        # 时间码对齐度
        # 取两者中较少的条数进行比较
        min_count = min(len(test_subs), len(golden_subs))
        max_count = max(len(test_subs), len(golden_subs))
        
        # 如果差异太大，直接返回较低分数
        if min_count < max_count * 0.5:
            return 0.3
        
        # 计算时间码偏差
        time_diffs = []
        for i in range(min_count):
            test_start = test_subs[i]["start"]
            test_end = test_subs[i]["end"]
            golden_start = golden_subs[i]["start"]
            golden_end = golden_subs[i]["end"]
            
            # 计算开始和结束时间的偏差
            start_diff = abs(test_start - golden_start)
            end_diff = abs(test_end - golden_end)
            
            # 计算此字幕的时长
            test_duration = test_end - test_start
            golden_duration = golden_end - golden_start
            
            # 使用两者中较长的时长作为参考
            ref_duration = max(test_duration, golden_duration, 1.0)  # 至少1秒，避免除零
            
            # 归一化偏差
            norm_start_diff = start_diff / ref_duration
            norm_end_diff = end_diff / ref_duration
            
            time_diffs.append((norm_start_diff + norm_end_diff) / 2)
        
        # 计算平均时间码偏差
        if not time_diffs:
            return 0.0
        
        avg_time_diff = sum(time_diffs) / len(time_diffs)
        time_score = 1.0 - min(1.0, avg_time_diff * 5)  # 偏差超过20%就得0分
        
        # 综合考虑数量差异和时间码偏差
        return 0.3 * count_score + 0.7 * time_score
    
    def _score_text_similarity(self, test_subs: List[Dict[str, Any]], golden_subs: List[Dict[str, Any]]) -> float:
        """
        计算字幕文本相似度得分
        
        Args:
            test_subs: 测试字幕
            golden_subs: 黄金样本字幕
            
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        if not test_subs or not golden_subs:
            return 0.0
        
        # 提取文本
        test_texts = [sub["text"] for sub in test_subs]
        golden_texts = [sub["text"] for sub in golden_subs]
        
        # 连接成单个文本字符串
        test_text = " ".join(test_texts)
        golden_text = " ".join(golden_texts)
        
        # 使用序列匹配计算相似度
        similarity = SequenceMatcher(None, test_text, golden_text).ratio()
        
        return similarity
    
    def _score_entity_matching(self, test_subs: List[Dict[str, Any]], golden_subs: List[Dict[str, Any]]) -> float:
        """
        计算字幕中实体匹配度得分
        
        Args:
            test_subs: 测试字幕
            golden_subs: 黄金样本字幕
            
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        if not test_subs or not golden_subs:
            return 0.0
        
        # 提取文本
        test_texts = [sub["text"] for sub in test_subs]
        golden_texts = [sub["text"] for sub in golden_subs]
        
        # 连接成单个文本字符串
        test_text = " ".join(test_texts)
        golden_text = " ".join(golden_texts)
        
        # 提取可能的实体（简单实现，提取大写开头的词，或者中文中的人名/地名模式）
        def extract_entities(text):
            # 英文实体识别（简化版，查找大写开头的词）
            english_entities = re.findall(r'\b[A-Z][a-zA-Z]*\b', text)
            
            # 中文实体识别（简化版，查找"某某："这样的对话开头）
            chinese_entities = re.findall(r'[^\s:：]+[：:]', text)
            
            # 数字识别
            numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
            
            return set(english_entities + chinese_entities + numbers)
        
        test_entities = extract_entities(test_text)
        golden_entities = extract_entities(golden_text)
        
        # 如果没有找到实体，返回基于文本相似度的退化值
        if not test_entities and not golden_entities:
            return self._score_text_similarity(test_subs, golden_subs) * 0.8
        
        # 计算实体匹配率
        if not test_entities or not golden_entities:
            return 0.0
        
        # 计算交集和并集
        intersection = test_entities.intersection(golden_entities)
        union = test_entities.union(golden_entities)
        
        # 计算Jaccard相似度
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        return jaccard
    
    def _score_length_ratio(self, test_subs: List[Dict[str, Any]], golden_subs: List[Dict[str, Any]]) -> float:
        """
        计算字幕长度比例得分
        
        Args:
            test_subs: 测试字幕
            golden_subs: 黄金样本字幕
            
        Returns:
            float: 0-1之间的得分，1表示完全匹配
        """
        if not test_subs or not golden_subs:
            return 0.0
        
        # 计算总字符数
        test_chars = sum(len(sub["text"]) for sub in test_subs)
        golden_chars = sum(len(sub["text"]) for sub in golden_subs)
        
        # 计算比例
        if golden_chars == 0:
            return 0.0
        
        ratio = test_chars / golden_chars
        
        # 如果比例接近1，得分高；否则根据差异程度降低得分
        if ratio > 0.9 and ratio < 1.1:
            return 1.0
        elif ratio > 0.8 and ratio < 1.2:
            return 0.8
        elif ratio > 0.7 and ratio < 1.3:
            return 0.6
        elif ratio > 0.5 and ratio < 1.5:
            return 0.4
        else:
            return 0.2

def compare_files(test_output: str, golden_sample: str = None, threshold: float = 0.8) -> CompareResult:
    """
    比较测试输出和黄金样本的多维度相似度
    
    Args:
        test_output: 测试输出文件前缀
        golden_sample: 黄金样本文件前缀，若为None则自动推断
        threshold: 通过阈值
        
    Returns:
        CompareResult: 比对结果
    """
    # 创建比对器
    comparator = GoldenComparator(test_output, golden_sample)
    
    # 执行比对
    result = comparator.compare()
    
    return result

class ResultComparer:
    """视频对比可视化比较器"""
    
    def __init__(self, video1_path: str, video2_path: str, 
                 srt1_path: Optional[str] = None, srt2_path: Optional[str] = None):
        """
        初始化比较器
        
        Args:
            video1_path: 第一个视频路径
            video2_path: 第二个视频路径
            srt1_path: 第一个字幕路径，如果不提供则默认为视频路径替换后缀
            srt2_path: 第二个字幕路径，如果不提供则默认为视频路径替换后缀
        """
        self.video1_path = video1_path
        self.video2_path = video2_path
        
        # 如果未提供字幕路径，尝试自动推断
        if srt1_path is None:
            self.srt1_path = video1_path.replace(".mp4", ".srt")
        else:
            self.srt1_path = srt1_path
            
        if srt2_path is None:
            self.srt2_path = video2_path.replace(".mp4", ".srt")
        else:
            self.srt2_path = srt2_path
        
        # 创建临时目录
        self.temp_dir = Path(os.path.dirname(video1_path)) / "temp_comparison"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 缓存对比结果
        self.comparison_result = None
    
    def compare_videos(self) -> Dict[str, Any]:
        """
        比较两个视频的各项指标
        
        Returns:
            Dict: 比较结果数据
        """
        # 获取视频信息
        video1_info = self._get_video_info(self.video1_path)
        video2_info = self._get_video_info(self.video2_path)
        
        # 比较视频基本特征
        basic_comparison = {
            "duration": {
                "video1": video1_info["duration"],
                "video2": video2_info["duration"],
                "diff": abs(video1_info["duration"] - video2_info["duration"]),
                "diff_percent": abs(video1_info["duration"] - video2_info["duration"]) / max(video1_info["duration"], video2_info["duration"]) * 100
            },
            "resolution": {
                "video1": f"{video1_info['width']}x{video1_info['height']}",
                "video2": f"{video2_info['width']}x{video2_info['height']}",
                "same": video1_info['width'] == video2_info['width'] and video1_info['height'] == video2_info['height']
            },
            "frames": {
                "video1": video1_info["frame_count"],
                "video2": video2_info["frame_count"],
                "diff": abs(video1_info["frame_count"] - video2_info["frame_count"]),
                "diff_percent": abs(video1_info["frame_count"] - video2_info["frame_count"]) / max(video1_info["frame_count"], video2_info["frame_count"]) * 100
            },
            "fps": {
                "video1": video1_info["fps"],
                "video2": video2_info["fps"],
                "same": abs(video1_info["fps"] - video2_info["fps"]) < 0.01
            }
        }
        
        # 比较视频帧
        frames_comparison = self._compare_frames(video1_info, video2_info)
        
        # 比较字幕
        subtitle_comparison = self._compare_subtitles()
        
        # 汇总结果
        result = {
            "basic": basic_comparison,
            "frames": frames_comparison,
            "subtitles": subtitle_comparison,
            "timestamp": datetime.now().isoformat()
        }
        
        # 缓存结果
        self.comparison_result = result
        
        return result
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {video_path}")
            
            # 提取基本信息
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count,
                "duration": duration
            }
        except Exception as e:
            print(f"获取视频信息失败: {str(e)}")
            return {
                "width": 0,
                "height": 0,
                "fps": 0,
                "frame_count": 0,
                "duration": 0
            }
    
    def _compare_frames(self, video1_info: Dict[str, Any], video2_info: Dict[str, Any]) -> Dict[str, Any]:
        """比较视频帧"""
        # 选择帧数较少的视频作为基准
        min_frames = min(video1_info["frame_count"], video2_info["frame_count"])
        
        # 选择最多10个均匀分布的采样点
        sample_count = min(10, min_frames)
        if sample_count <= 0:
            return {"error": "视频帧数不足"}
        
        # 采样帧位置
        sample_positions = [int(i * (min_frames - 1) / (sample_count - 1)) if sample_count > 1 else 0 
                           for i in range(sample_count)]
        
        # 提取并比较帧
        frame_results = []
        
        cap1 = cv2.VideoCapture(self.video1_path)
        cap2 = cv2.VideoCapture(self.video2_path)
        
        for idx, pos in enumerate(sample_positions):
            # 提取第一个视频帧
            cap1.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret1, frame1 = cap1.read()
            
            # 提取第二个视频帧
            cap2.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret2, frame2 = cap2.read()
            
            if not ret1 or not ret2:
                continue
            
            # 调整大小以便比较
            if frame1.shape != frame2.shape:
                frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
            
            # 计算PSNR
            mse = np.mean((frame1.astype(np.float64) - frame2.astype(np.float64)) ** 2)
            if mse == 0:
                psnr = 100
            else:
                psnr = 10 * np.log10((255 ** 2) / mse)
            
            # 计算颜色直方图相似度
            hist1 = self._calculate_color_histogram(frame1)
            hist2 = self._calculate_color_histogram(frame2)
            hist_similarity = 1 - distance.cosine(hist1, hist2)
            
            # 保存对比帧
            frame_time = pos / video1_info["fps"] if video1_info["fps"] > 0 else 0
            comparison_frame = self._create_comparison_frame(frame1, frame2, psnr, hist_similarity)
            comparison_path = self.temp_dir / f"frame_compare_{idx:02d}.jpg"
            cv2.imwrite(str(comparison_path), comparison_frame)
            
            # 记录结果
            frame_results.append({
                "position": pos,
                "time": frame_time,
                "psnr": psnr,
                "histogram_similarity": hist_similarity,
                "comparison_path": str(comparison_path)
            })
        
        # 释放视频对象
        cap1.release()
        cap2.release()
        
        # 计算平均值
        avg_psnr = np.mean([f["psnr"] for f in frame_results]) if frame_results else 0
        avg_hist_sim = np.mean([f["histogram_similarity"] for f in frame_results]) if frame_results else 0
        
        return {
            "samples": frame_results,
            "avg_psnr": avg_psnr,
            "avg_histogram_similarity": avg_hist_sim
        }
    
    def _calculate_color_histogram(self, frame):
        """计算颜色直方图"""
        # 转换为HSV空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算颜色直方图
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        
        return hist.flatten()
    
    def _create_comparison_frame(self, frame1, frame2, psnr, hist_similarity):
        """创建对比帧"""
        # 创建标题
        title = f"PSNR: {psnr:.2f} dB, Hist Sim: {hist_similarity:.2f}"
        
        # 创建带标题的画布
        h, w = frame1.shape[:2]
        title_height = 30
        canvas = np.ones((h * 2 + title_height, w, 3), dtype=np.uint8) * 255
        
        # 添加标题
        cv2.putText(
            canvas, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1
        )
        
        # 添加两个帧
        canvas[title_height:title_height+h, 0:w] = frame1
        canvas[title_height+h:title_height+h*2, 0:w] = frame2
        
        # 添加标签
        cv2.putText(
            canvas, "Video 1", (10, title_height+20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
        )
        cv2.putText(
            canvas, "Video 2", (10, title_height+h+20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1
        )
        
        return canvas
    
    def _compare_subtitles(self) -> Dict[str, Any]:
        """比较字幕文件"""
        # 检查字幕文件存在性
        if not os.path.exists(self.srt1_path) or not os.path.exists(self.srt2_path):
            return {"error": "字幕文件不存在"}
        
        try:
            # 解析字幕
            subs1 = parse_subtitle(self.srt1_path)
            subs2 = parse_subtitle(self.srt2_path)
            
            if not subs1 or not subs2:
                return {"error": "字幕为空"}
            
            # 基本统计信息
            stats = {
                "count": {
                    "srt1": len(subs1),
                    "srt2": len(subs2),
                    "diff": abs(len(subs1) - len(subs2))
                },
                "duration": {
                    "srt1": subs1[-1]["end"] - subs1[0]["start"] if subs1 else 0,
                    "srt2": subs2[-1]["end"] - subs2[0]["start"] if subs2 else 0
                }
            }
            
            # 分析文本相似度
            all_text1 = " ".join([s["text"] for s in subs1])
            all_text2 = " ".join([s["text"] for s in subs2])
            
            text_sim = SequenceMatcher(None, all_text1, all_text2).ratio()
            
            # 分析时间码
            time_differences = []
            
            # 使用较短的字幕列表长度
            min_length = min(len(subs1), len(subs2))
            
            for i in range(min_length):
                start_diff = abs(subs1[i]["start"] - subs2[i]["start"])
                end_diff = abs(subs1[i]["end"] - subs2[i]["end"])
                duration1 = subs1[i]["end"] - subs1[i]["start"]
                duration2 = subs2[i]["end"] - subs2[i]["start"]
                duration_diff = abs(duration1 - duration2)
                
                time_differences.append({
                    "index": i,
                    "start_diff": start_diff,
                    "end_diff": end_diff,
                    "duration_diff": duration_diff
                })
            
            # 计算平均时间差异
            avg_start_diff = np.mean([d["start_diff"] for d in time_differences]) if time_differences else 0
            avg_end_diff = np.mean([d["end_diff"] for d in time_differences]) if time_differences else 0
            avg_duration_diff = np.mean([d["duration_diff"] for d in time_differences]) if time_differences else 0
            
            return {
                "stats": stats,
                "text_similarity": text_sim,
                "time_analysis": {
                    "average_start_diff": avg_start_diff,
                    "average_end_diff": avg_end_diff,
                    "average_duration_diff": avg_duration_diff
                },
                "detailed_differences": time_differences[:5]  # 只返回前5个差异示例
            }
            
        except Exception as e:
            return {"error": f"比较字幕失败: {str(e)}"}
    
    def generate_report(self, output_path: str) -> bool:
        """
        生成HTML报告
        
        Args:
            output_path: 输出HTML文件路径
            
        Returns:
            bool: 是否成功生成报告
        """
        # 确保已经执行了比较
        if self.comparison_result is None:
            self.compare_videos()
        
        try:
            # 报告标题
            video1_name = os.path.basename(self.video1_path)
            video2_name = os.path.basename(self.video2_path)
            
            # 创建HTML内容
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>视频对比报告: {video1_name} vs {video2_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
        h1, h2, h3 {{ color: #444; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background-color: #f8f9fa; padding: 20px; margin-bottom: 30px; border-radius: 5px; }}
        .section {{ margin-bottom: 30px; }}
        .metric {{ margin-bottom: 15px; }}
        .metric-name {{ font-weight: bold; }}
        .comparison {{ display: flex; margin-top: 10px; }}
        .video-info {{ flex: 1; padding: 10px; }}
        .video-info:first-child {{ border-right: 1px solid #ddd; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #f1f1f1; }}
        .frame-comparison {{ margin-bottom: 30px; }}
        .frame-comparison img {{ max-width: 100%; border: 1px solid #ddd; }}
        .subtitle-diff {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .badge {{ padding: 3px 10px; border-radius: 12px; color: white; font-size: 12px; display: inline-block; margin-right: 5px; }}
        .badge-success {{ background-color: #28a745; }}
        .badge-warning {{ background-color: #ffc107; color: #212529; }}
        .badge-danger {{ background-color: #dc3545; }}
        .summary {{ background-color: #e9f7ef; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>视频对比报告</h1>
            <p><strong>视频1:</strong> {video1_name}</p>
            <p><strong>视频2:</strong> {video2_name}</p>
            <p><strong>生成时间:</strong> {self.comparison_result['timestamp']}</p>
        </div>
        
        <div class="section">
            <h2>基本信息对比</h2>
            <table>
                <tr>
                    <th>指标</th>
                    <th>视频1</th>
                    <th>视频2</th>
                    <th>差异</th>
                </tr>
                <tr>
                    <td>时长</td>
                    <td>{self.comparison_result['basic']['duration']['video1']:.2f}秒</td>
                    <td>{self.comparison_result['basic']['duration']['video2']:.2f}秒</td>
                    <td>
                        {self.comparison_result['basic']['duration']['diff']:.2f}秒
                        ({self.comparison_result['basic']['duration']['diff_percent']:.2f}%)
                    </td>
                </tr>
                <tr>
                    <td>分辨率</td>
                    <td>{self.comparison_result['basic']['resolution']['video1']}</td>
                    <td>{self.comparison_result['basic']['resolution']['video2']}</td>
                    <td>
                        {'相同' if self.comparison_result['basic']['resolution']['same'] else '不同'}
                    </td>
                </tr>
                <tr>
                    <td>帧数</td>
                    <td>{self.comparison_result['basic']['frames']['video1']}</td>
                    <td>{self.comparison_result['basic']['frames']['video2']}</td>
                    <td>
                        {self.comparison_result['basic']['frames']['diff']}
                        ({self.comparison_result['basic']['frames']['diff_percent']:.2f}%)
                    </td>
                </tr>
                <tr>
                    <td>帧率</td>
                    <td>{self.comparison_result['basic']['fps']['video1']:.2f} fps</td>
                    <td>{self.comparison_result['basic']['fps']['video2']:.2f} fps</td>
                    <td>
                        {'相同' if self.comparison_result['basic']['fps']['same'] else '不同'}
                    </td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>帧对比分析</h2>
            <div class="summary">
                <p><strong>平均PSNR:</strong> {self.comparison_result['frames']['avg_psnr']:.2f} dB</p>
                <p><strong>平均直方图相似度:</strong> {self.comparison_result['frames']['avg_histogram_similarity']:.4f}</p>
            </div>
            
            <h3>采样帧对比</h3>
"""
            
            # 添加帧比较
            for idx, frame in enumerate(self.comparison_result['frames']['samples']):
                # 将图片路径转换为相对路径
                img_path = frame['comparison_path']
                rel_path = os.path.relpath(img_path, os.path.dirname(output_path))
                
                html_content += f"""
            <div class="frame-comparison">
                <h4>帧 {idx+1} (时间点: {frame['time']:.2f}秒)</h4>
                <p>PSNR: {frame['psnr']:.2f} dB, 直方图相似度: {frame['histogram_similarity']:.4f}</p>
                <img src="{rel_path}" alt="Frame Comparison {idx+1}">
            </div>
"""
            
            # 添加字幕比较部分
            subtitle_html = ""
            if "error" in self.comparison_result['subtitles']:
                subtitle_html = f"""
        <div class="section">
            <h2>字幕对比分析</h2>
            <p>错误: {self.comparison_result['subtitles']['error']}</p>
        </div>
"""
            else:
                subtitle_html = f"""
        <div class="section">
            <h2>字幕对比分析</h2>
            <div class="summary">
                <p><strong>字幕行数:</strong> 视频1: {self.comparison_result['subtitles']['stats']['count']['srt1']}, 
                   视频2: {self.comparison_result['subtitles']['stats']['count']['srt2']}, 
                   差异: {self.comparison_result['subtitles']['stats']['count']['diff']}</p>
                <p><strong>文本相似度:</strong> {self.comparison_result['subtitles']['text_similarity']:.2f}</p>
                <p><strong>平均开始时间差异:</strong> {self.comparison_result['subtitles']['time_analysis']['average_start_diff']:.2f}秒</p>
                <p><strong>平均结束时间差异:</strong> {self.comparison_result['subtitles']['time_analysis']['average_end_diff']:.2f}秒</p>
                <p><strong>平均时长差异:</strong> {self.comparison_result['subtitles']['time_analysis']['average_duration_diff']:.2f}秒</p>
            </div>
"""
                
                # 添加详细字幕差异
                if self.comparison_result['subtitles']['detailed_differences']:
                    subtitle_html += """
            <h3>字幕时间差异示例</h3>
            <table>
                <tr>
                    <th>索引</th>
                    <th>开始时间差异</th>
                    <th>结束时间差异</th>
                    <th>时长差异</th>
                </tr>
"""
                    
                    for diff in self.comparison_result['subtitles']['detailed_differences']:
                        subtitle_html += f"""
                <tr>
                    <td>{diff['index'] + 1}</td>
                    <td>{diff['start_diff']:.2f}秒</td>
                    <td>{diff['end_diff']:.2f}秒</td>
                    <td>{diff['duration_diff']:.2f}秒</td>
                </tr>
"""
                    
                    subtitle_html += """
            </table>
"""
                
                subtitle_html += """
        </div>
"""
            
            # 完成HTML
            html_content += subtitle_html + """
    </div>
</body>
</html>
"""
            
            # 写入HTML文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return os.path.exists(output_path)
        
        except Exception as e:
            print(f"生成报告失败: {str(e)}")
            return False

if __name__ == "__main__":
    # 简单命令行界面
    if len(sys.argv) < 2:
        print("使用方法: python compare_engine.py <测试输出前缀> [黄金样本前缀]")
        sys.exit(1)
    
    test_output = sys.argv[1]
    golden_sample = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # 移除文件扩展名（如果有）
        test_output = os.path.splitext(test_output)[0]
        if golden_sample:
            golden_sample = os.path.splitext(golden_sample)[0]
        
        # 执行比对
        result = compare_files(test_output, golden_sample)
        
        # 打印结果
        print(result)
        
        # 设置退出码
        sys.exit(0 if result.is_passed() else 1)
    except Exception as e:
        print(f"比对过程出错: {str(e)}")
        sys.exit(1) 