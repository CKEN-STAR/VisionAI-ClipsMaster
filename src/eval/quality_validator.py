#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 视频质量检测器
检测视频质量、音视频同步、分辨率保持等指标
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import logging
logger = logging.getLogger(__name__)


class QualityValidator:
    """质量验证器 - 用于剧情连贯性和内容质量检查"""

    def __init__(self):
        """初始化质量验证器"""
        self.coherence_weights = {
            "temporal_consistency": 0.3,  # 时间一致性
            "narrative_flow": 0.4,        # 叙事流畅性
            "emotional_continuity": 0.3   # 情感连续性
        }

        # 情感关键词字典
        self.emotion_keywords = {
            "positive": ["开心", "高兴", "快乐", "笑", "哈哈", "好", "棒", "赞"],
            "negative": ["伤心", "难过", "哭", "生气", "愤怒", "讨厌", "坏"],
            "neutral": ["说", "看", "去", "来", "在", "的", "了", "是"],
            "surprise": ["惊讶", "震惊", "不敢相信", "天哪", "什么", "怎么"]
        }

    def check_narrative_coherence(self, subtitle_sequence: List[Dict[str, Any]]) -> float:
        """
        检查叙事连贯性

        Args:
            subtitle_sequence: 字幕序列列表

        Returns:
            float: 连贯性评分 (0.0-1.0)
        """
        try:
            if not subtitle_sequence or len(subtitle_sequence) < 2:
                logger.warning("字幕序列太短，无法进行连贯性检查")
                return 0.0

            # 计算各项连贯性指标
            temporal_score = self._check_temporal_consistency(subtitle_sequence)
            narrative_score = self._check_narrative_flow(subtitle_sequence)
            emotional_score = self._check_emotional_continuity(subtitle_sequence)

            # 加权计算总分
            total_score = (
                temporal_score * self.coherence_weights["temporal_consistency"] +
                narrative_score * self.coherence_weights["narrative_flow"] +
                emotional_score * self.coherence_weights["emotional_continuity"]
            )

            logger.info(f"连贯性检查完成: 时间{temporal_score:.3f}, 叙事{narrative_score:.3f}, 情感{emotional_score:.3f}, 总分{total_score:.3f}")
            return total_score

        except Exception as e:
            logger.error(f"连贯性检查失败: {e}")
            return 0.0

    def _check_temporal_consistency(self, subtitles: List[Dict[str, Any]]) -> float:
        """检查时间一致性"""
        try:
            if len(subtitles) < 2:
                return 1.0

            inconsistencies = 0
            total_checks = 0

            for i in range(1, len(subtitles)):
                prev_subtitle = subtitles[i-1]
                curr_subtitle = subtitles[i]

                # 获取时间信息
                prev_end = self._parse_time(prev_subtitle.get("end", prev_subtitle.get("end_time", 0)))
                curr_start = self._parse_time(curr_subtitle.get("start", curr_subtitle.get("start_time", 0)))

                # 检查时间顺序
                if curr_start < prev_end:
                    inconsistencies += 1

                # 检查时间间隔是否合理（不超过5秒）
                time_gap = curr_start - prev_end
                if time_gap > 5.0:
                    inconsistencies += 0.5

                total_checks += 1

            if total_checks == 0:
                return 1.0

            consistency_rate = 1.0 - (inconsistencies / total_checks)
            return max(0.0, consistency_rate)

        except Exception as e:
            logger.error(f"时间一致性检查失败: {e}")
            return 0.5

    def _check_narrative_flow(self, subtitles: List[Dict[str, Any]]) -> float:
        """检查叙事流畅性"""
        try:
            if len(subtitles) < 3:
                return 1.0

            flow_score = 0.0
            total_transitions = 0

            for i in range(1, len(subtitles) - 1):
                prev_text = subtitles[i-1].get("text", "")
                curr_text = subtitles[i].get("text", "")
                next_text = subtitles[i+1].get("text", "")

                # 检查语义连贯性（简化版）
                transition_score = self._analyze_semantic_transition(prev_text, curr_text, next_text)
                flow_score += transition_score
                total_transitions += 1

            if total_transitions == 0:
                return 1.0

            average_flow = flow_score / total_transitions
            return min(1.0, average_flow)

        except Exception as e:
            logger.error(f"叙事流畅性检查失败: {e}")
            return 0.5

    def _check_emotional_continuity(self, subtitles: List[Dict[str, Any]]) -> float:
        """检查情感连续性"""
        try:
            if len(subtitles) < 2:
                return 1.0

            emotion_sequence = []
            for subtitle in subtitles:
                text = subtitle.get("text", "")
                emotion = self._detect_emotion(text)
                emotion_sequence.append(emotion)

            # 计算情感变化的合理性
            continuity_score = 0.0
            total_transitions = 0

            for i in range(1, len(emotion_sequence)):
                prev_emotion = emotion_sequence[i-1]
                curr_emotion = emotion_sequence[i]

                # 情感转换合理性评分
                transition_score = self._evaluate_emotion_transition(prev_emotion, curr_emotion)
                continuity_score += transition_score
                total_transitions += 1

            if total_transitions == 0:
                return 1.0

            average_continuity = continuity_score / total_transitions
            return min(1.0, average_continuity)

        except Exception as e:
            logger.error(f"情感连续性检查失败: {e}")
            return 0.5

    def _parse_time(self, time_value) -> float:
        """解析时间值为秒数"""
        try:
            if isinstance(time_value, (int, float)):
                return float(time_value)

            if isinstance(time_value, str):
                # 支持格式: "00:00:10,500" 或 "00:00:10.500"
                time_str = time_value.replace(',', '.')
                parts = time_str.split(':')

                if len(parts) == 3:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
                elif len(parts) == 2:
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                else:
                    return float(parts[0])

            return 0.0

        except Exception:
            return 0.0

    def _detect_emotion(self, text: str) -> str:
        """检测文本情感"""
        try:
            text_lower = text.lower()

            # 统计各种情感关键词
            emotion_scores = {}
            for emotion, keywords in self.emotion_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score > 0:
                    emotion_scores[emotion] = score

            if not emotion_scores:
                return "neutral"

            # 返回得分最高的情感
            return max(emotion_scores, key=emotion_scores.get)

        except Exception:
            return "neutral"

    def _analyze_semantic_transition(self, prev_text: str, curr_text: str, next_text: str) -> float:
        """分析语义转换的合理性"""
        try:
            # 简化的语义分析：检查关键词重叠和逻辑连接词

            # 逻辑连接词
            connectors = ["然后", "接着", "但是", "不过", "所以", "因此", "于是", "后来"]

            score = 0.5  # 基础分数

            # 检查是否有逻辑连接词
            for connector in connectors:
                if connector in curr_text:
                    score += 0.2
                    break

            # 检查关键词重叠
            prev_words = set(prev_text)
            curr_words = set(curr_text)
            next_words = set(next_text)

            # 前后文关键词重叠
            overlap_prev = len(prev_words & curr_words) / max(len(curr_words), 1)
            overlap_next = len(curr_words & next_words) / max(len(curr_words), 1)

            # 适度的重叠是好的
            if 0.1 <= overlap_prev <= 0.5:
                score += 0.1
            if 0.1 <= overlap_next <= 0.5:
                score += 0.1

            return min(1.0, score)

        except Exception:
            return 0.5

    def _evaluate_emotion_transition(self, prev_emotion: str, curr_emotion: str) -> float:
        """评估情感转换的合理性"""
        try:
            # 情感转换合理性矩阵
            transition_matrix = {
                ("positive", "positive"): 0.9,
                ("positive", "neutral"): 0.8,
                ("positive", "negative"): 0.6,  # 较大转换
                ("positive", "surprise"): 0.7,

                ("negative", "negative"): 0.9,
                ("negative", "neutral"): 0.8,
                ("negative", "positive"): 0.6,  # 较大转换
                ("negative", "surprise"): 0.7,

                ("neutral", "positive"): 0.8,
                ("neutral", "negative"): 0.8,
                ("neutral", "neutral"): 0.9,
                ("neutral", "surprise"): 0.8,

                ("surprise", "positive"): 0.7,
                ("surprise", "negative"): 0.7,
                ("surprise", "neutral"): 0.8,
                ("surprise", "surprise"): 0.6,  # 连续惊讶不太自然
            }

            return transition_matrix.get((prev_emotion, curr_emotion), 0.5)

        except Exception:
            return 0.5

class VideoQualityValidator:
    """视频质量验证器"""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.quality_thresholds = {
            'min_resolution': (480, 360),  # 最小分辨率
            'max_resolution': (3840, 2160),  # 最大分辨率
            'min_bitrate': 500,  # 最小比特率 (kbps)
            'max_bitrate': 50000,  # 最大比特率 (kbps)
            'min_fps': 15,  # 最小帧率
            'max_fps': 60,  # 最大帧率
            'max_audio_delay': 0.1,  # 最大音频延迟 (秒)
            'min_audio_quality': 64  # 最小音频比特率 (kbps)
        }
    
    def _find_ffmpeg(self) -> Optional[str]:
        """查找FFmpeg可执行文件"""
        # 常见的FFmpeg路径
        possible_paths = [
            'ffmpeg',  # 系统PATH中
            'ffmpeg.exe',  # Windows
            str(PROJECT_ROOT / 'tools' / 'ffmpeg' / 'ffmpeg.exe'),  # 项目内置
            str(PROJECT_ROOT / 'ffmpeg.exe'),  # 项目根目录
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=10)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        return None
    
    def validate_video_quality(self, video_path: str) -> Dict[str, Any]:
        """验证视频质量"""
        video_file = Path(video_path)
        if not video_file.exists():
            return {
                'status': 'ERROR',
                'error': f'视频文件不存在: {video_path}',
                'timestamp': datetime.now().isoformat()
            }
        
        if not self.ffmpeg_path:
            return {
                'status': 'ERROR',
                'error': 'FFmpeg未找到，无法进行视频质量检测',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # 获取视频信息
            video_info = self._get_video_info(video_path)
            if 'error' in video_info:
                return {
                    'status': 'ERROR',
                    'error': video_info['error'],
                    'timestamp': datetime.now().isoformat()
                }
            
            # 执行质量检查
            quality_results = self._check_video_quality(video_info)
            
            # 检查音视频同步
            sync_results = self._check_audio_video_sync(video_path)
            
            # 检查视频完整性
            integrity_results = self._check_video_integrity(video_path)
            
            # 汇总结果
            overall_status = self._determine_overall_status([
                quality_results['status'],
                sync_results['status'],
                integrity_results['status']
            ])
            
            return {
                'status': overall_status,
                'video_info': video_info,
                'quality_check': quality_results,
                'sync_check': sync_results,
                'integrity_check': integrity_results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': f'视频质量检测过程中发生错误: {e}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频信息"""
        try:
            cmd = [
                self.ffmpeg_path, '-i', video_path,
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            # FFmpeg将信息输出到stderr
            output = result.stderr
            
            # 解析视频信息
            info = self._parse_ffmpeg_output(output)
            return info
            
        except subprocess.TimeoutExpired:
            return {'error': 'FFmpeg执行超时'}
        except Exception as e:
            return {'error': f'获取视频信息失败: {e}'}
    
    def _parse_ffmpeg_output(self, output: str) -> Dict[str, Any]:
        """解析FFmpeg输出"""
        info = {}
        
        try:
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 解析视频流信息
                if 'Video:' in line:
                    # 提取分辨率
                    if 'x' in line:
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and part.replace('x', '').replace(',', '').isdigit():
                                width, height = part.rstrip(',').split('x')
                                info['width'] = int(width)
                                info['height'] = int(height)
                                break
                    
                    # 提取帧率
                    if 'fps' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'fps' in part and i > 0:
                                try:
                                    fps = float(parts[i-1])
                                    info['fps'] = fps
                                except ValueError:
                                    pass
                                break
                    
                    # 提取比特率
                    if 'kb/s' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'kb/s' in part and i > 0:
                                try:
                                    bitrate = int(parts[i-1])
                                    info['video_bitrate'] = bitrate
                                except ValueError:
                                    pass
                                break
                
                # 解析音频流信息
                elif 'Audio:' in line:
                    if 'kb/s' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if 'kb/s' in part and i > 0:
                                try:
                                    audio_bitrate = int(parts[i-1])
                                    info['audio_bitrate'] = audio_bitrate
                                except ValueError:
                                    pass
                                break
                
                # 解析时长
                elif 'Duration:' in line:
                    duration_part = line.split('Duration:')[1].split(',')[0].strip()
                    info['duration'] = duration_part
            
            return info
            
        except Exception as e:
            return {'error': f'解析FFmpeg输出失败: {e}'}
    
    def _check_video_quality(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """检查视频质量"""
        issues = []
        warnings = []
        
        # 检查分辨率
        if 'width' in video_info and 'height' in video_info:
            width, height = video_info['width'], video_info['height']
            min_w, min_h = self.quality_thresholds['min_resolution']
            max_w, max_h = self.quality_thresholds['max_resolution']
            
            if width < min_w or height < min_h:
                issues.append(f'分辨率过低: {width}x{height} (最小要求: {min_w}x{min_h})')
            elif width > max_w or height > max_h:
                warnings.append(f'分辨率过高: {width}x{height} (建议最大: {max_w}x{max_h})')
        else:
            issues.append('无法获取视频分辨率信息')
        
        # 检查帧率
        if 'fps' in video_info:
            fps = video_info['fps']
            if fps < self.quality_thresholds['min_fps']:
                issues.append(f'帧率过低: {fps}fps (最小要求: {self.quality_thresholds["min_fps"]}fps)')
            elif fps > self.quality_thresholds['max_fps']:
                warnings.append(f'帧率过高: {fps}fps (建议最大: {self.quality_thresholds["max_fps"]}fps)')
        else:
            warnings.append('无法获取视频帧率信息')
        
        # 检查视频比特率
        if 'video_bitrate' in video_info:
            bitrate = video_info['video_bitrate']
            if bitrate < self.quality_thresholds['min_bitrate']:
                issues.append(f'视频比特率过低: {bitrate}kbps (最小要求: {self.quality_thresholds["min_bitrate"]}kbps)')
            elif bitrate > self.quality_thresholds['max_bitrate']:
                warnings.append(f'视频比特率过高: {bitrate}kbps (建议最大: {self.quality_thresholds["max_bitrate"]}kbps)')
        else:
            warnings.append('无法获取视频比特率信息')
        
        # 检查音频比特率
        if 'audio_bitrate' in video_info:
            audio_bitrate = video_info['audio_bitrate']
            if audio_bitrate < self.quality_thresholds['min_audio_quality']:
                issues.append(f'音频比特率过低: {audio_bitrate}kbps (最小要求: {self.quality_thresholds["min_audio_quality"]}kbps)')
        else:
            warnings.append('无法获取音频比特率信息')
        
        # 确定状态
        if issues:
            status = 'FAIL'
        elif warnings:
            status = 'WARNING'
        else:
            status = 'PASS'
        
        return {
            'status': status,
            'issues': issues,
            'warnings': warnings,
            'quality_score': self._calculate_quality_score(video_info, issues, warnings)
        }
    
    def _check_audio_video_sync(self, video_path: str) -> Dict[str, Any]:
        """检查音视频同步"""
        try:
            # 简化的同步检查：检查音频和视频流是否都存在
            cmd = [
                self.ffmpeg_path, '-i', video_path,
                '-t', '1', '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            output = result.stderr
            
            has_video = 'Video:' in output
            has_audio = 'Audio:' in output
            
            if has_video and has_audio:
                return {
                    'status': 'PASS',
                    'message': '音视频流都存在',
                    'has_video': True,
                    'has_audio': True
                }
            elif has_video and not has_audio:
                return {
                    'status': 'WARNING',
                    'message': '仅有视频流，缺少音频',
                    'has_video': True,
                    'has_audio': False
                }
            elif not has_video and has_audio:
                return {
                    'status': 'FAIL',
                    'message': '仅有音频流，缺少视频',
                    'has_video': False,
                    'has_audio': True
                }
            else:
                return {
                    'status': 'FAIL',
                    'message': '音视频流都缺失',
                    'has_video': False,
                    'has_audio': False
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': f'音视频同步检查失败: {e}'
            }
    
    def _check_video_integrity(self, video_path: str) -> Dict[str, Any]:
        """检查视频完整性"""
        try:
            video_file = Path(video_path)
            
            # 检查文件大小
            file_size = video_file.stat().st_size
            if file_size == 0:
                return {
                    'status': 'FAIL',
                    'error': '视频文件为空'
                }
            
            # 检查文件是否可读
            cmd = [
                self.ffmpeg_path, '-v', 'error',
                '-i', video_path,
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30)
            
            if result.returncode == 0:
                return {
                    'status': 'PASS',
                    'message': '视频文件完整性良好',
                    'file_size_bytes': file_size
                }
            else:
                return {
                    'status': 'FAIL',
                    'error': f'视频文件损坏或格式错误: {result.stderr}'
                }
                
        except Exception as e:
            return {
                'status': 'ERROR',
                'error': f'视频完整性检查失败: {e}'
            }
    
    def _calculate_quality_score(self, video_info: Dict[str, Any], issues: List[str], warnings: List[str]) -> int:
        """计算质量评分 (0-100)"""
        score = 100
        
        # 问题扣分
        score -= len(issues) * 20
        
        # 警告扣分
        score -= len(warnings) * 5
        
        # 根据具体参数调整分数
        if 'width' in video_info and 'height' in video_info:
            width, height = video_info['width'], video_info['height']
            if width >= 1920 and height >= 1080:  # 1080p及以上
                score += 5
            elif width >= 1280 and height >= 720:  # 720p
                score += 2
        
        if 'fps' in video_info:
            fps = video_info['fps']
            if 24 <= fps <= 30:  # 标准帧率
                score += 3
            elif fps > 30:  # 高帧率
                score += 5
        
        return max(0, min(100, score))
    
    def _determine_overall_status(self, statuses: List[str]) -> str:
        """确定总体状态"""
        if 'ERROR' in statuses:
            return 'ERROR'
        elif 'FAIL' in statuses:
            return 'FAIL'
        elif 'WARNING' in statuses:
            return 'WARNING'
        else:
            return 'PASS'
    
    def batch_validate(self, video_paths: List[str]) -> Dict[str, Any]:
        """批量验证视频质量"""
        results = {}
        summary = {
            'total_videos': len(video_paths),
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'errors': 0
        }
        
        for video_path in video_paths:
            result = self.validate_video_quality(video_path)
            results[video_path] = result
            
            status = result['status']
            if status == 'PASS':
                summary['passed'] += 1
            elif status == 'FAIL':
                summary['failed'] += 1
            elif status == 'WARNING':
                summary['warnings'] += 1
            elif status == 'ERROR':
                summary['errors'] += 1
        
        return {
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """主函数 - 用于测试"""
    validator = VideoQualityValidator()
    
    # 查找测试视频文件
    test_data_dir = PROJECT_ROOT / "test_data"
    if test_data_dir.exists():
        video_files = list(test_data_dir.glob("*.mp4"))
        if video_files:
            print(f"找到{len(video_files)}个测试视频文件")
            
            # 批量验证
            video_paths = [str(f) for f in video_files]
            results = validator.batch_validate(video_paths)
            
            # 打印结果
            print("\n视频质量检测结果:")
            print(f"总计: {results['summary']['total_videos']}")
            print(f"通过: {results['summary']['passed']}")
            print(f"失败: {results['summary']['failed']}")
            print(f"警告: {results['summary']['warnings']}")
            print(f"错误: {results['summary']['errors']}")
            
            # 保存详细结果
            report_file = PROJECT_ROOT / f"test_output/video_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"详细报告已保存到: {report_file}")
        else:
            print("未找到测试视频文件")
    else:
        print("测试数据目录不存在")


if __name__ == "__main__":
    main()
