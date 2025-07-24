#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端视频处理工作流测试
验证从原片字幕到爆款混剪视频生成的完整流程
"""

import os
import sys
import json
import time
import logging
import unittest
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# 导入核心组件
try:
    from src.core.video_workflow_manager import VideoWorkflowManager
    from src.core.language_detector import LanguageDetector
    from src.utils.memory_guard import get_memory_manager
    from src.utils.device_manager import DeviceManager
    HAS_CORE_COMPONENTS = True
except ImportError as e:
    HAS_CORE_COMPONENTS = False
    logging.warning(f"核心组件导入失败: {e}")

class EndToEndWorkflowTest(unittest.TestCase):
    """端到端工作流测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.test_results = {}
        self.temp_dir = tempfile.mkdtemp(prefix="workflow_test_")
        self.memory_manager = get_memory_manager() if HAS_CORE_COMPONENTS else None
        self.device_manager = DeviceManager() if HAS_CORE_COMPONENTS else None
        
        # 创建测试数据
        self.test_videos = self._create_test_videos()
        self.test_subtitles = self._create_test_subtitles()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("端到端工作流测试初始化完成")
    
    def _create_test_videos(self) -> Dict[str, str]:
        """创建测试视频文件"""
        test_videos = {}
        
        # 创建不同格式的测试视频
        video_configs = [
            {"name": "test_mp4_short", "format": "mp4", "duration": 30, "resolution": "640x480"},
            {"name": "test_mp4_medium", "format": "mp4", "duration": 120, "resolution": "1280x720"},
            {"name": "test_avi_short", "format": "avi", "duration": 60, "resolution": "854x480"},
        ]
        
        for config in video_configs:
            video_path = self._generate_test_video(
                name=config["name"],
                format=config["format"],
                duration=config["duration"],
                resolution=config["resolution"]
            )
            if video_path:
                test_videos[config["name"]] = video_path
        
        return test_videos
    
    def _generate_test_video(self, name: str, format: str, duration: int, resolution: str) -> Optional[str]:
        """生成测试视频文件"""
        try:
            output_path = os.path.join(self.temp_dir, f"{name}.{format}")
            
            # 使用FFmpeg生成测试视频
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"testsrc=duration={duration}:size={resolution}:rate=25",
                "-f", "lavfi",
                "-i", "sine=frequency=1000:duration={}".format(duration),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            
            # 检查FFmpeg是否可用
            try:
                subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.warning("FFmpeg不可用，创建模拟视频文件")
                return self._create_mock_video_file(output_path)
            
            # 执行FFmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                self.logger.info(f"成功创建测试视频: {output_path}")
                return output_path
            else:
                self.logger.warning(f"FFmpeg创建视频失败: {result.stderr}")
                return self._create_mock_video_file(output_path)
                
        except Exception as e:
            self.logger.error(f"生成测试视频失败: {e}")
            return self._create_mock_video_file(output_path)
    
    def _create_mock_video_file(self, output_path: str) -> str:
        """创建模拟视频文件"""
        try:
            # 创建一个小的二进制文件作为模拟视频
            with open(output_path, 'wb') as f:
                # 写入一些模拟的视频数据
                f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
                f.write(b'\x00' * 1024)  # 1KB的模拟数据
            
            self.logger.info(f"创建模拟视频文件: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"创建模拟视频文件失败: {e}")
            return None
    
    def _create_test_subtitles(self) -> Dict[str, str]:
        """创建测试字幕文件"""
        test_subtitles = {}
        
        # 英文字幕
        english_srt = """1
00:00:00,000 --> 00:00:05,000
John walked to the store to buy some groceries.

2
00:00:05,000 --> 00:00:10,000
He picked up milk, bread, and eggs from the shelves.

3
00:00:10,000 --> 00:00:15,000
At the checkout, he paid with his credit card.

4
00:00:15,000 --> 00:00:20,000
Then he walked back home with his shopping bags.
"""
        
        # 中文字幕
        chinese_srt = """1
00:00:00,000 --> 00:00:05,000
小明今天去学校上课，心情很好。

2
00:00:05,000 --> 00:00:10,000
他在数学课上认真听讲，做了很多笔记。

3
00:00:10,000 --> 00:00:15,000
下课后，他和同学们一起讨论问题。

4
00:00:15,000 --> 00:00:20,000
放学后，他高兴地回到了家里。
"""
        
        # 保存字幕文件
        subtitles = {
            "english": english_srt,
            "chinese": chinese_srt
        }
        
        for lang, content in subtitles.items():
            subtitle_path = os.path.join(self.temp_dir, f"test_{lang}.srt")
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(content)
            test_subtitles[lang] = subtitle_path
            self.logger.info(f"创建测试字幕文件: {subtitle_path}")
        
        return test_subtitles
    
    def test_complete_workflow_english(self):
        """测试英文完整工作流"""
        self.logger.info("开始英文完整工作流测试...")
        
        if not HAS_CORE_COMPONENTS:
            self.skipTest("核心组件不可用")
        
        # 选择测试文件
        video_path = self.test_videos.get("test_mp4_short")
        subtitle_path = self.test_subtitles.get("english")
        
        if not video_path or not subtitle_path:
            self.skipTest("测试文件创建失败")
        
        # 创建输出路径
        output_path = os.path.join(self.temp_dir, "output_english.mp4")
        
        # 执行工作流
        workflow_manager = VideoWorkflowManager()
        
        # 设置进度回调
        progress_updates = []
        def progress_callback(stage: str, progress: float):
            progress_updates.append({"stage": stage, "progress": progress, "timestamp": time.time()})
            self.logger.info(f"进度更新: {stage} - {progress:.1f}%")
        
        workflow_manager.set_progress_callback(progress_callback)
        
        # 记录开始时间和内存
        start_time = time.time()
        memory_before = self.memory_manager.get_memory_usage() if self.memory_manager else 0
        
        # 执行完整工作流
        result = workflow_manager.process_video_complete_workflow(
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            language="en",
            style="viral"
        )
        
        # 记录结束时间和内存
        end_time = time.time()
        memory_after = self.memory_manager.get_memory_usage() if self.memory_manager else 0
        
        # 验证结果
        self.assertTrue(result.get("success", False), f"英文工作流失败: {result.get('error', '未知错误')}")
        
        # 验证输出文件
        if result.get("success", False):
            self.assertTrue(os.path.exists(output_path), "输出视频文件不存在")
            if os.path.exists(output_path):
                self.assertGreater(os.path.getsize(output_path), 0, "输出视频文件为空")
        
        # 记录测试结果
        self.test_results["english_workflow"] = {
            "success": result.get("success", False),
            "processing_time": end_time - start_time,
            "memory_usage": {
                "before": memory_before,
                "after": memory_after,
                "delta": memory_after - memory_before
            },
            "progress_updates": progress_updates,
            "output_file_exists": os.path.exists(output_path),
            "output_file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            "workflow_result": result
        }
        
        self.logger.info("英文完整工作流测试完成")
    
    def test_complete_workflow_chinese(self):
        """测试中文完整工作流"""
        self.logger.info("开始中文完整工作流测试...")
        
        if not HAS_CORE_COMPONENTS:
            self.skipTest("核心组件不可用")
        
        # 选择测试文件
        video_path = self.test_videos.get("test_mp4_medium")
        subtitle_path = self.test_subtitles.get("chinese")
        
        if not video_path or not subtitle_path:
            self.skipTest("测试文件创建失败")
        
        # 创建输出路径
        output_path = os.path.join(self.temp_dir, "output_chinese.mp4")
        
        # 执行工作流
        workflow_manager = VideoWorkflowManager()
        
        # 设置进度回调
        progress_updates = []
        def progress_callback(stage: str, progress: float):
            progress_updates.append({"stage": stage, "progress": progress, "timestamp": time.time()})
            self.logger.info(f"进度更新: {stage} - {progress:.1f}%")
        
        workflow_manager.set_progress_callback(progress_callback)
        
        # 记录开始时间和内存
        start_time = time.time()
        memory_before = self.memory_manager.get_memory_usage() if self.memory_manager else 0
        
        # 执行完整工作流
        result = workflow_manager.process_video_complete_workflow(
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            language="zh",
            style="viral"
        )
        
        # 记录结束时间和内存
        end_time = time.time()
        memory_after = self.memory_manager.get_memory_usage() if self.memory_manager else 0
        
        # 验证结果
        self.assertTrue(result.get("success", False), f"中文工作流失败: {result.get('error', '未知错误')}")
        
        # 验证输出文件
        if result.get("success", False):
            self.assertTrue(os.path.exists(output_path), "输出视频文件不存在")
            if os.path.exists(output_path):
                self.assertGreater(os.path.getsize(output_path), 0, "输出视频文件为空")
        
        # 记录测试结果
        self.test_results["chinese_workflow"] = {
            "success": result.get("success", False),
            "processing_time": end_time - start_time,
            "memory_usage": {
                "before": memory_before,
                "after": memory_after,
                "delta": memory_after - memory_before
            },
            "progress_updates": progress_updates,
            "output_file_exists": os.path.exists(output_path),
            "output_file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            "workflow_result": result
        }
        
        self.logger.info("中文完整工作流测试完成")
    
    def tearDown(self):
        """测试清理"""
        # 清理临时文件
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"清理临时目录: {self.temp_dir}")
        except Exception as e:
            self.logger.warning(f"清理临时文件失败: {e}")
        
        # 保存测试结果
        self._save_test_results()
    
    def _save_test_results(self):
        """保存测试结果"""
        try:
            output_dir = os.path.join(PROJECT_ROOT, "test_output")
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = os.path.join(output_dir, f"end_to_end_workflow_test_{timestamp}.json")
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"端到端工作流测试结果已保存到: {result_file}")
            
        except Exception as e:
            self.logger.error(f"保存测试结果失败: {e}")

if __name__ == "__main__":
    unittest.main()
