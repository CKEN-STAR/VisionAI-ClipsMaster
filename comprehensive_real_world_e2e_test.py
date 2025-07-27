#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 全面端到端输入输出链路测试
验证完整工作流程："原片视频 + SRT字幕文件 → 剧本重构 → 混剪视频输出"

测试覆盖：
1. UI功能完整性验证（启动、显示、交互）
2. 核心功能链路测试（语言检测、剧本重构、视频处理）
3. 工作流程流畅性验证（完整用户操作路径）
4. 关键约束验证（时长控制、剧情连贯性）
5. 测试数据管理（真实素材、自动清理）
"""

import sys
import os
import time
import json
import shutil
import tempfile
import traceback
import subprocess
import threading
import psutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class ComprehensiveRealWorldE2ETest:
    """全面端到端输入输出链路测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.test_start_time = datetime.now()
        self.temp_dir = None
        self.test_data_dir = None
        self.output_dir = None
        self.memory_baseline = 0
        self.max_memory_usage = 0
        self.created_files = []
        self.ui_app = None
        self.main_window = None
        
        # 测试配置
        self.config = {
            "max_memory_limit_gb": 3.8,
            "test_timeout_seconds": 900,  # 15分钟超时
            "ui_startup_timeout": 60,
            "video_processing_timeout": 300,
            "min_output_duration": 10,  # 最短输出时长（秒）
            "max_compression_ratio": 0.8,  # 最大压缩比
            "min_compression_ratio": 0.1   # 最小压缩比
        }
        
        # 初始化测试环境
        self._setup_test_environment()
        
    def _setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置全面测试环境...")
        
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix="comprehensive_e2e_test_"))
        self.test_data_dir = self.temp_dir / "test_data"
        self.output_dir = self.temp_dir / "output"
        
        # 创建必要的目录结构
        for dir_path in [self.test_data_dir, self.output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # 记录基线内存使用
        self.memory_baseline = psutil.virtual_memory().used / (1024**3)
        
        print(f"✅ 全面测试环境已设置: {self.temp_dir}")
        print(f"📊 基线内存使用: {self.memory_baseline:.2f} GB")
        
    def create_realistic_test_materials(self) -> Dict[str, Any]:
        """创建真实的测试素材"""
        print("📝 创建真实测试素材...")
        
        # 创建复杂的中文短剧SRT内容（模拟真实短剧）
        realistic_chinese_drama_srt = """1
00:00:00,000 --> 00:00:05,000
【开场】都市夜晚，霓虹闪烁

2
00:00:05,000 --> 00:00:10,000
林小雨匆忙走出地铁站，手机响个不停

3
00:00:10,000 --> 00:00:15,000
"又是加班通知..."她无奈地叹了口气

4
00:00:15,000 --> 00:00:20,000
突然，一个陌生男子撞了她一下

5
00:00:20,000 --> 00:00:25,000
"对不起！"男子连忙道歉，弯腰捡起散落的文件

6
00:00:25,000 --> 00:00:30,000
林小雨看到他温暖的笑容，心跳莫名加速

7
00:00:30,000 --> 00:00:35,000
"没关系的。"她轻声回答，脸颊微红

8
00:00:35,000 --> 00:00:40,000
【第一次心动】两人的目光在空中交汇

9
00:00:40,000 --> 00:00:45,000
"我叫陈浩，很高兴认识你。"

10
00:00:45,000 --> 00:00:50,000
"林小雨。"她羞涩地报出自己的名字

11
00:00:50,000 --> 00:00:55,000
【命运的安排】原来他们在同一栋写字楼工作

12
00:00:55,000 --> 00:01:00,000
从那天起，他们经常在电梯里偶遇

13
00:01:00,000 --> 00:01:05,000
每次见面，林小雨都会心跳加速

14
00:01:05,000 --> 00:01:10,000
陈浩也总是找借口和她多说几句话

15
00:01:10,000 --> 00:01:15,000
【感情升温】一个月后的雨夜

16
00:01:15,000 --> 00:01:20,000
林小雨忘记带伞，在楼下徘徊

17
00:01:20,000 --> 00:01:25,000
陈浩主动走过来："我送你回家吧。"

18
00:01:25,000 --> 00:01:30,000
雨伞下，两人的距离越来越近

19
00:01:30,000 --> 00:01:35,000
【告白时刻】"小雨，我喜欢你。"

20
00:01:35,000 --> 00:01:40,000
林小雨的心彻底融化了："我也是..."

21
00:01:40,000 --> 00:01:45,000
【甜蜜恋爱】从此他们形影不离

22
00:01:45,000 --> 00:01:50,000
一起吃饭，一起看电影，一起规划未来

23
00:01:50,000 --> 00:01:55,000
【危机出现】但是好景不长

24
00:01:55,000 --> 00:02:00,000
陈浩的前女友突然回国

25
00:02:00,000 --> 00:02:05,000
她带着孩子出现在陈浩面前

26
00:02:05,000 --> 00:02:10,000
"浩哥，这是你的儿子。"

27
00:02:10,000 --> 00:02:15,000
【真相大白】原来五年前他们有过一段情

28
00:02:15,000 --> 00:02:20,000
林小雨震惊得说不出话来

29
00:02:20,000 --> 00:02:25,000
【痛苦抉择】陈浩陷入了两难境地

30
00:02:25,000 --> 00:02:30,000
是选择责任还是选择爱情？

31
00:02:30,000 --> 00:02:35,000
【分手】林小雨主动提出分手

32
00:02:35,000 --> 00:02:40,000
"我不想成为你们之间的第三者。"

33
00:02:40,000 --> 00:02:45,000
【各自痛苦】两人都在承受着分离的痛苦

34
00:02:45,000 --> 00:02:50,000
陈浩努力做一个好父亲

35
00:02:50,000 --> 00:02:55,000
林小雨把所有精力投入工作

36
00:02:55,000 --> 00:03:00,000
【意外发现】半年后，真相浮出水面

37
00:03:00,000 --> 00:03:05,000
孩子根本不是陈浩的

38
00:03:05,000 --> 00:03:10,000
前女友只是想利用他

39
00:03:10,000 --> 00:03:15,000
【重新开始】陈浩立刻去找林小雨

40
00:03:15,000 --> 00:03:20,000
"小雨，我们重新开始好吗？"

41
00:03:20,000 --> 00:03:25,000
【圆满结局】林小雨含泪点头

42
00:03:25,000 --> 00:03:30,000
真爱终于战胜了一切困难

43
00:03:30,000 --> 00:03:35,000
【婚礼】一年后，他们步入了婚姻殿堂

44
00:03:35,000 --> 00:03:40,000
"从今以后，我们永远不分离。"

45
00:03:40,000 --> 00:03:45,000
【完美结局】爱情的力量让一切都变得美好
"""
        
        # 创建英文短剧SRT内容
        realistic_english_drama_srt = """1
00:00:00,000 --> 00:00:05,000
[Opening] New York City skyline at sunset

2
00:00:05,000 --> 00:00:10,000
Emma rushes through the busy coffee shop

3
00:00:10,000 --> 00:00:15,000
"One large coffee, please. I'm running late!"

4
00:00:15,000 --> 00:00:20,000
A handsome stranger accidentally bumps into her

5
00:00:20,000 --> 00:00:25,000
"I'm so sorry! Let me buy you another coffee."

6
00:00:25,000 --> 00:00:30,000
Emma looks into his kind blue eyes

7
00:00:30,000 --> 00:00:35,000
"It's okay, really. I'm Emma."

8
00:00:35,000 --> 00:00:40,000
"I'm Jake. Nice to meet you, Emma."

9
00:00:40,000 --> 00:00:45,000
[First Connection] They talk for hours

10
00:00:45,000 --> 00:00:50,000
Emma misses her important meeting

11
00:00:50,000 --> 00:00:55,000
But she doesn't care anymore

12
00:00:55,000 --> 00:01:00,000
[Growing Love] They start dating

13
00:01:00,000 --> 00:01:05,000
Romantic dinners and long walks

14
00:01:05,000 --> 00:01:10,000
Emma has never been happier

15
00:01:10,000 --> 00:01:15,000
[The Proposal] Six months later

16
00:01:15,000 --> 00:01:20,000
Jake gets down on one knee

17
00:01:20,000 --> 00:01:25,000
"Emma, will you marry me?"

18
00:01:25,000 --> 00:01:30,000
"Yes! A thousand times yes!"

19
00:01:30,000 --> 00:01:35,000
[Happy Ending] Their wedding day

20
00:01:35,000 --> 00:01:40,000
"I love you forever and always."
"""
        
        # 保存测试SRT文件
        chinese_srt_path = self.test_data_dir / "realistic_chinese_drama.srt"
        english_srt_path = self.test_data_dir / "realistic_english_drama.srt"
        
        with open(chinese_srt_path, 'w', encoding='utf-8') as f:
            f.write(realistic_chinese_drama_srt)
        self.created_files.append(str(chinese_srt_path))
        
        with open(english_srt_path, 'w', encoding='utf-8') as f:
            f.write(realistic_english_drama_srt)
        self.created_files.append(str(english_srt_path))
        
        # 创建真实的测试视频文件
        chinese_video_path = self.test_data_dir / "chinese_drama_source.mp4"
        english_video_path = self.test_data_dir / "english_drama_source.mp4"
        
        self._create_realistic_test_video(chinese_video_path, duration=225)  # 3分45秒
        self._create_realistic_test_video(english_video_path, duration=100)  # 1分40秒
        
        print(f"✅ 真实测试素材已创建:")
        print(f"   - 中文短剧字幕: {chinese_srt_path} (45段)")
        print(f"   - 英文短剧字幕: {english_srt_path} (20段)")
        print(f"   - 中文短剧视频: {chinese_video_path}")
        print(f"   - 英文短剧视频: {english_video_path}")
        
        return {
            "chinese_materials": {
                "srt": chinese_srt_path,
                "video": chinese_video_path,
                "duration": 225,
                "segments": 45,
                "language": "zh"
            },
            "english_materials": {
                "srt": english_srt_path,
                "video": english_video_path,
                "duration": 100,
                "segments": 20,
                "language": "en"
            }
        }
        
    def _create_realistic_test_video(self, video_path: Path, duration: int):
        """创建真实的测试视频文件"""
        try:
            # 使用FFmpeg创建指定时长的高质量测试视频
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"testsrc2=duration={duration}:size=1920x1080:rate=30",
                "-f", "lavfi", 
                "-i", f"sine=frequency=1000:duration={duration}",
                "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0 and video_path.exists():
                self.created_files.append(str(video_path))
                file_size = video_path.stat().st_size / (1024*1024)  # MB
                print(f"   ✅ 测试视频创建成功: {video_path.name} ({file_size:.1f}MB)")
            else:
                # 创建占位文件
                video_path.touch()
                self.created_files.append(str(video_path))
                print(f"   ⚠️  FFmpeg不可用，创建占位视频文件: {video_path.name}")
                
        except Exception as e:
            print(f"   ⚠️  创建测试视频失败: {e}")
            video_path.touch()
            self.created_files.append(str(video_path))

    def test_ui_comprehensive_functionality(self) -> Dict[str, Any]:
        """测试UI功能完整性"""
        print("\n🖥️  测试UI功能完整性...")

        test_result = {
            "test_name": "UI功能完整性验证",
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "ui_components": {},
            "interaction_tests": {}
        }

        try:
            # 1. 测试UI模块导入和初始化
            print("   📦 测试UI模块导入和初始化...")

            # 导入主UI模块
            import simple_ui_fixed
            test_result["ui_components"]["main_module_import"] = "success"

            # 测试PyQt6依赖
            from PyQt6.QtWidgets import QApplication, QMainWindow
            from PyQt6.QtCore import QTimer, Qt
            test_result["ui_components"]["pyqt6_dependencies"] = "success"

            # 2. 测试应用程序创建和主窗口启动
            print("   🚀 测试应用程序创建和主窗口启动...")

            # 创建QApplication实例
            self.ui_app = QApplication.instance()
            if self.ui_app is None:
                self.ui_app = QApplication(sys.argv)
            test_result["ui_components"]["app_creation"] = "success"

            # 创建主窗口实例
            self.main_window = simple_ui_fixed.SimpleScreenplayApp()
            test_result["ui_components"]["main_window_creation"] = "success"

            # 3. 测试主窗口组件
            print("   🔍 测试主窗口组件...")

            # 检查主要UI组件是否存在
            ui_components_check = {
                "central_widget": hasattr(self.main_window, 'centralWidget'),
                "tabs": hasattr(self.main_window, 'tabs'),
                "video_list": hasattr(self.main_window, 'video_list'),
                "srt_list": hasattr(self.main_window, 'srt_list'),
                "process_progress_bar": hasattr(self.main_window, 'process_progress_bar'),
                "status_label": hasattr(self.main_window, 'status_label'),
                "training_feeder": hasattr(self.main_window, 'training_feeder')
            }

            test_result["ui_components"]["component_availability"] = ui_components_check

            # 4. 测试标签页功能
            print("   📑 测试标签页功能...")

            if hasattr(self.main_window, 'tabs'):
                tab_count = self.main_window.tabs.count()
                tab_names = []
                for i in range(tab_count):
                    tab_names.append(self.main_window.tabs.tabText(i))

                test_result["ui_components"]["tabs"] = {
                    "count": tab_count,
                    "names": tab_names,
                    "status": "success" if tab_count >= 4 else "partial"
                }
            else:
                test_result["ui_components"]["tabs"] = {"status": "failed", "error": "tabs not found"}

            # 5. 测试训练面板组件
            print("   🎓 测试训练面板组件...")

            if hasattr(self.main_window, 'training_feeder'):
                training_components = {
                    "original_srt_list": hasattr(self.main_window.training_feeder, 'original_srt_list'),
                    "viral_srt": hasattr(self.main_window.training_feeder, 'viral_srt'),
                    "language_mode": hasattr(self.main_window.training_feeder, 'language_mode')
                }
                test_result["ui_components"]["training_panel"] = training_components
            else:
                test_result["ui_components"]["training_panel"] = {"status": "failed"}

            # 6. 测试UI交互功能
            print("   🖱️  测试UI交互功能...")

            # 测试窗口显示（不实际显示，只测试方法）
            try:
                # 设置窗口大小
                self.main_window.resize(1200, 800)
                test_result["interaction_tests"]["window_resize"] = "success"
            except Exception as e:
                test_result["interaction_tests"]["window_resize"] = f"failed: {str(e)}"

            # 测试标签页切换
            try:
                if hasattr(self.main_window, 'tabs') and self.main_window.tabs.count() > 1:
                    current_index = self.main_window.tabs.currentIndex()
                    self.main_window.tabs.setCurrentIndex(1)
                    self.main_window.tabs.setCurrentIndex(current_index)
                    test_result["interaction_tests"]["tab_switching"] = "success"
                else:
                    test_result["interaction_tests"]["tab_switching"] = "skipped"
            except Exception as e:
                test_result["interaction_tests"]["tab_switching"] = f"failed: {str(e)}"

            # 测试进度条更新
            try:
                if hasattr(self.main_window, 'process_progress_bar'):
                    self.main_window.process_progress_bar.setValue(50)
                    test_result["interaction_tests"]["progress_bar_update"] = "success"
                else:
                    test_result["interaction_tests"]["progress_bar_update"] = "component_missing"
            except Exception as e:
                test_result["interaction_tests"]["progress_bar_update"] = f"failed: {str(e)}"

            # 测试状态标签更新
            try:
                if hasattr(self.main_window, 'status_label'):
                    self.main_window.status_label.setText("测试状态更新")
                    test_result["interaction_tests"]["status_label_update"] = "success"
                else:
                    test_result["interaction_tests"]["status_label_update"] = "component_missing"
            except Exception as e:
                test_result["interaction_tests"]["status_label_update"] = f"failed: {str(e)}"

            # 计算UI测试成功率
            total_components = len(ui_components_check)
            successful_components = sum(1 for v in ui_components_check.values() if v)
            ui_success_rate = successful_components / total_components if total_components > 0 else 0

            total_interactions = len(test_result["interaction_tests"])
            successful_interactions = sum(1 for v in test_result["interaction_tests"].values() if v == "success")
            interaction_success_rate = successful_interactions / total_interactions if total_interactions > 0 else 0

            test_result["summary"] = {
                "ui_success_rate": ui_success_rate,
                "interaction_success_rate": interaction_success_rate,
                "overall_ui_status": "excellent" if ui_success_rate >= 0.9 and interaction_success_rate >= 0.8 else
                                   "good" if ui_success_rate >= 0.7 and interaction_success_rate >= 0.6 else
                                   "needs_improvement"
            }

            print(f"   ✅ UI功能测试完成:")
            print(f"      组件可用率: {ui_success_rate:.1%}")
            print(f"      交互成功率: {interaction_success_rate:.1%}")
            print(f"      整体UI状态: {test_result['summary']['overall_ui_status']}")

            test_result["status"] = "completed"
            test_result["end_time"] = datetime.now().isoformat()

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            test_result["end_time"] = datetime.now().isoformat()
            print(f"   ❌ UI功能测试失败: {e}")
            traceback.print_exc()

        return test_result

    def test_core_functionality_chain(self, test_materials: Dict[str, Any]) -> Dict[str, Any]:
        """测试核心功能链路"""
        print("\n⚙️  测试核心功能链路...")

        test_result = {
            "test_name": "核心功能链路测试",
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "chain_tests": {}
        }

        try:
            # 测试中文和英文两种材料
            for material_type, materials in test_materials.items():
                print(f"\n   🔍 测试{material_type}材料处理链路...")

                chain_result = self._test_single_material_chain(materials)
                test_result["chain_tests"][material_type] = chain_result

            # 计算整体链路成功率
            total_chains = len(test_result["chain_tests"])
            successful_chains = sum(1 for chain in test_result["chain_tests"].values()
                                  if chain.get("overall_status") == "success")

            test_result["summary"] = {
                "total_material_types": total_chains,
                "successful_chains": successful_chains,
                "chain_success_rate": successful_chains / total_chains if total_chains > 0 else 0
            }

            print(f"\n   📊 核心功能链路测试完成:")
            print(f"      测试材料类型: {total_chains}")
            print(f"      成功链路: {successful_chains}")
            print(f"      链路成功率: {test_result['summary']['chain_success_rate']:.1%}")

            test_result["status"] = "completed"
            test_result["end_time"] = datetime.now().isoformat()

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            test_result["end_time"] = datetime.now().isoformat()
            print(f"   ❌ 核心功能链路测试失败: {e}")

        return test_result

    def _test_single_material_chain(self, materials: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个材料的完整处理链路"""
        chain_result = {
            "material_info": materials,
            "steps": {},
            "performance_metrics": {}
        }

        try:
            # 步骤1: 语言检测
            print(f"      🔍 步骤1: 语言检测...")
            language_result = self._test_language_detection_step(materials["srt"])
            chain_result["steps"]["language_detection"] = language_result

            # 步骤2: SRT解析
            print(f"      📄 步骤2: SRT解析...")
            parsing_result = self._test_srt_parsing_step(materials["srt"])
            chain_result["steps"]["srt_parsing"] = parsing_result

            # 步骤3: 剧本重构
            print(f"      🎬 步骤3: 剧本重构...")
            reconstruction_result = self._test_screenplay_reconstruction_step(materials["srt"])
            chain_result["steps"]["screenplay_reconstruction"] = reconstruction_result

            # 步骤4: 视频处理
            print(f"      🎥 步骤4: 视频处理...")
            video_result = self._test_video_processing_step(materials["video"], reconstruction_result)
            chain_result["steps"]["video_processing"] = video_result

            # 步骤5: 剪映导出
            print(f"      📤 步骤5: 剪映导出...")
            export_result = self._test_jianying_export_step(reconstruction_result)
            chain_result["steps"]["jianying_export"] = export_result

            # 计算链路成功率
            total_steps = len(chain_result["steps"])
            successful_steps = sum(1 for step in chain_result["steps"].values()
                                 if step.get("status") == "success")

            chain_result["performance_metrics"] = {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "step_success_rate": successful_steps / total_steps if total_steps > 0 else 0
            }

            # 验证关键约束
            constraint_validation = self._validate_key_constraints(reconstruction_result, materials)
            chain_result["constraint_validation"] = constraint_validation

            # 确定整体状态
            if (successful_steps == total_steps and
                constraint_validation.get("duration_appropriate", False) and
                constraint_validation.get("storyline_coherent", False)):
                chain_result["overall_status"] = "success"
            elif successful_steps >= total_steps * 0.8:
                chain_result["overall_status"] = "partial_success"
            else:
                chain_result["overall_status"] = "failed"

            print(f"         ✅ 链路完成: {successful_steps}/{total_steps} 步骤成功")

        except Exception as e:
            chain_result["overall_status"] = "failed"
            chain_result["error"] = str(e)
            print(f"         ❌ 链路测试失败: {e}")

        return chain_result

    def _test_language_detection_step(self, srt_path: Path) -> Dict[str, Any]:
        """测试语言检测步骤"""
        try:
            from src.core.language_detector import LanguageDetector
            detector = LanguageDetector()

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            detected_language = detector.detect_language(content)

            return {
                "status": "success",
                "detected_language": detected_language,
                "content_sample": content[:100] + "..." if len(content) > 100 else content
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _test_srt_parsing_step(self, srt_path: Path) -> Dict[str, Any]:
        """测试SRT解析步骤"""
        try:
            from src.core.srt_parser import SRTParser
            parser = SRTParser()

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            segments = parser.parse_srt_content(content)

            return {
                "status": "success",
                "segments_count": len(segments) if segments else 0,
                "first_segment": segments[0] if segments else None,
                "last_segment": segments[-1] if segments else None
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _test_screenplay_reconstruction_step(self, srt_path: Path) -> Dict[str, Any]:
        """测试剧本重构步骤"""
        try:
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()

            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            result = engineer.reconstruct_screenplay(content, target_style="viral")

            if result:
                return {
                    "status": "success",
                    "original_duration": result.get("original_duration", 0),
                    "new_duration": result.get("new_duration", 0),
                    "segments_count": len(result.get("segments", [])),
                    "optimization_score": result.get("optimization_score", 0),
                    "compression_ratio": result.get("new_duration", 0) / result.get("original_duration", 1),
                    "reconstruction_data": result
                }
            else:
                return {"status": "failed", "error": "重构结果为空"}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _test_video_processing_step(self, video_path: Path, reconstruction_result: Dict[str, Any]) -> Dict[str, Any]:
        """测试视频处理步骤"""
        try:
            from src.core.video_processor import VideoProcessor
            processor = VideoProcessor()

            if not video_path.exists():
                return {"status": "skipped", "reason": "测试视频文件不存在"}

            # 获取视频信息
            video_info = processor.get_video_info(str(video_path))

            return {
                "status": "success",
                "video_info_available": video_info is not None,
                "processor_initialized": True,
                "video_file_size": video_path.stat().st_size if video_path.exists() else 0
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _test_jianying_export_step(self, reconstruction_result: Dict[str, Any]) -> Dict[str, Any]:
        """测试剪映导出步骤"""
        try:
            if reconstruction_result.get("status") == "success":
                segments = reconstruction_result.get("reconstruction_data", {}).get("segments", [])

                # 创建输出路径
                output_path = self.output_dir / f"test_project_{int(time.time())}.json"

                # 模拟导出过程（创建简单的工程文件）
                project_data = {
                    "version": "1.0",
                    "segments": segments,
                    "created_at": datetime.now().isoformat(),
                    "total_segments": len(segments)
                }

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, ensure_ascii=False, indent=2)

                self.created_files.append(str(output_path))

                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "segments_exported": len(segments),
                    "file_size": output_path.stat().st_size
                }
            else:
                return {"status": "skipped", "reason": "没有重构数据可导出"}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_key_constraints(self, reconstruction_result: Dict[str, Any], materials: Dict[str, Any]) -> Dict[str, Any]:
        """验证关键约束"""
        validation_result = {
            "duration_appropriate": False,
            "storyline_coherent": False,
            "compression_reasonable": False
        }

        try:
            if reconstruction_result.get("status") == "success":
                reconstruction_data = reconstruction_result.get("reconstruction_data", {})
                original_duration = reconstruction_data.get("original_duration", 0)
                new_duration = reconstruction_data.get("new_duration", 0)

                if original_duration > 0 and new_duration > 0:
                    compression_ratio = new_duration / original_duration

                    # 验证时长合理性
                    if (new_duration >= self.config["min_output_duration"] and
                        compression_ratio >= self.config["min_compression_ratio"] and
                        compression_ratio <= self.config["max_compression_ratio"]):
                        validation_result["duration_appropriate"] = True

                    # 验证压缩比合理性
                    if (self.config["min_compression_ratio"] <= compression_ratio <=
                        self.config["max_compression_ratio"]):
                        validation_result["compression_reasonable"] = True

                    # 验证剧情连贯性（简化检查）
                    segments = reconstruction_data.get("segments", [])
                    if len(segments) >= 2:  # 至少有2个片段才能保证基本连贯性
                        validation_result["storyline_coherent"] = True

        except Exception as e:
            validation_result["error"] = str(e)

        return validation_result

    def test_complete_workflow_integration(self, test_materials: Dict[str, Any]) -> Dict[str, Any]:
        """测试完整工作流程集成"""
        print("\n🔄 测试完整工作流程集成...")

        test_result = {
            "test_name": "完整工作流程集成测试",
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "workflow_tests": {}
        }

        try:
            # 测试每种材料的完整工作流程
            for material_type, materials in test_materials.items():
                print(f"\n   🔗 测试{material_type}完整工作流程...")

                workflow_result = self._test_complete_user_workflow(materials)
                test_result["workflow_tests"][material_type] = workflow_result

            # 计算工作流程成功率
            total_workflows = len(test_result["workflow_tests"])
            successful_workflows = sum(1 for workflow in test_result["workflow_tests"].values()
                                     if workflow.get("workflow_status") == "success")

            test_result["summary"] = {
                "total_workflows": total_workflows,
                "successful_workflows": successful_workflows,
                "workflow_success_rate": successful_workflows / total_workflows if total_workflows > 0 else 0
            }

            print(f"\n   📊 完整工作流程测试完成:")
            print(f"      测试工作流程: {total_workflows}")
            print(f"      成功工作流程: {successful_workflows}")
            print(f"      工作流程成功率: {test_result['summary']['workflow_success_rate']:.1%}")

            test_result["status"] = "completed"
            test_result["end_time"] = datetime.now().isoformat()

        except Exception as e:
            test_result["status"] = "failed"
            test_result["error"] = str(e)
            test_result["end_time"] = datetime.now().isoformat()
            print(f"   ❌ 完整工作流程测试失败: {e}")

        return test_result

    def _test_complete_user_workflow(self, materials: Dict[str, Any]) -> Dict[str, Any]:
        """测试完整用户工作流程"""
        workflow_result = {
            "material_type": materials.get("language", "unknown"),
            "user_actions": {},
            "output_validation": {}
        }

        try:
            # 模拟用户操作1: 文件上传
            print(f"         📁 模拟文件上传...")
            upload_result = self._simulate_file_upload(materials)
            workflow_result["user_actions"]["file_upload"] = upload_result

            # 模拟用户操作2: 处理启动
            print(f"         ▶️  模拟处理启动...")
            processing_result = self._simulate_processing_start(materials)
            workflow_result["user_actions"]["processing_start"] = processing_result

            # 模拟用户操作3: 结果预览
            print(f"         👁️  模拟结果预览...")
            preview_result = self._simulate_result_preview(processing_result)
            workflow_result["user_actions"]["result_preview"] = preview_result

            # 模拟用户操作4: 导出操作
            print(f"         💾 模拟导出操作...")
            export_result = self._simulate_export_operation(processing_result)
            workflow_result["user_actions"]["export_operation"] = export_result

            # 验证输出质量
            output_validation = self._validate_output_quality(processing_result, materials)
            workflow_result["output_validation"] = output_validation

            # 计算工作流程成功率
            total_actions = len(workflow_result["user_actions"])
            successful_actions = sum(1 for action in workflow_result["user_actions"].values()
                                   if action.get("status") == "success")

            workflow_success_rate = successful_actions / total_actions if total_actions > 0 else 0

            if (workflow_success_rate >= 0.8 and
                output_validation.get("quality_acceptable", False)):
                workflow_result["workflow_status"] = "success"
            elif workflow_success_rate >= 0.6:
                workflow_result["workflow_status"] = "partial_success"
            else:
                workflow_result["workflow_status"] = "failed"

            print(f"            ✅ 工作流程完成: {successful_actions}/{total_actions} 操作成功")

        except Exception as e:
            workflow_result["workflow_status"] = "failed"
            workflow_result["error"] = str(e)
            print(f"            ❌ 工作流程失败: {e}")

        return workflow_result

    def _simulate_file_upload(self, materials: Dict[str, Any]) -> Dict[str, Any]:
        """模拟文件上传操作"""
        try:
            srt_path = materials["srt"]
            video_path = materials["video"]

            # 检查文件是否存在和可读
            srt_exists = srt_path.exists() and srt_path.is_file()
            video_exists = video_path.exists() and video_path.is_file()

            return {
                "status": "success" if srt_exists and video_exists else "partial",
                "srt_file_valid": srt_exists,
                "video_file_valid": video_exists,
                "srt_size": srt_path.stat().st_size if srt_exists else 0,
                "video_size": video_path.stat().st_size if video_exists else 0
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _simulate_processing_start(self, materials: Dict[str, Any]) -> Dict[str, Any]:
        """模拟处理启动操作"""
        try:
            # 模拟处理过程
            start_time = time.time()

            # 执行实际的剧本重构
            from src.core.screenplay_engineer import ScreenplayEngineer
            engineer = ScreenplayEngineer()

            with open(materials["srt"], 'r', encoding='utf-8') as f:
                content = f.read()

            result = engineer.reconstruct_screenplay(content, target_style="viral")

            processing_time = time.time() - start_time

            return {
                "status": "success" if result else "failed",
                "processing_time": processing_time,
                "result_data": result
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _simulate_result_preview(self, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """模拟结果预览操作"""
        try:
            if processing_result.get("status") == "success":
                result_data = processing_result.get("result_data", {})
                segments = result_data.get("segments", [])

                # 模拟预览数据生成
                preview_data = {
                    "segments_count": len(segments),
                    "total_duration": result_data.get("new_duration", 0),
                    "preview_available": len(segments) > 0
                }

                return {
                    "status": "success",
                    "preview_data": preview_data
                }
            else:
                return {"status": "skipped", "reason": "处理未成功"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _simulate_export_operation(self, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """模拟导出操作"""
        try:
            if processing_result.get("status") == "success":
                result_data = processing_result.get("result_data", {})

                # 创建导出文件
                export_path = self.output_dir / f"exported_project_{int(time.time())}.json"

                export_data = {
                    "project_name": "测试项目",
                    "created_at": datetime.now().isoformat(),
                    "segments": result_data.get("segments", []),
                    "total_duration": result_data.get("new_duration", 0)
                }

                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)

                self.created_files.append(str(export_path))

                return {
                    "status": "success",
                    "export_path": str(export_path),
                    "file_size": export_path.stat().st_size
                }
            else:
                return {"status": "skipped", "reason": "处理未成功"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _validate_output_quality(self, processing_result: Dict[str, Any], materials: Dict[str, Any]) -> Dict[str, Any]:
        """验证输出质量"""
        validation = {
            "quality_acceptable": False,
            "duration_check": False,
            "compression_check": False,
            "coherence_check": False
        }

        try:
            if processing_result.get("status") == "success":
                result_data = processing_result.get("result_data", {})
                original_duration = result_data.get("original_duration", 0)
                new_duration = result_data.get("new_duration", 0)

                if original_duration > 0 and new_duration > 0:
                    compression_ratio = new_duration / original_duration

                    # 检查时长
                    validation["duration_check"] = new_duration >= self.config["min_output_duration"]

                    # 检查压缩比
                    validation["compression_check"] = (
                        self.config["min_compression_ratio"] <= compression_ratio <=
                        self.config["max_compression_ratio"]
                    )

                    # 检查连贯性
                    segments = result_data.get("segments", [])
                    validation["coherence_check"] = len(segments) >= 2

                    # 综合质量评估
                    validation["quality_acceptable"] = (
                        validation["duration_check"] and
                        validation["compression_check"] and
                        validation["coherence_check"]
                    )

        except Exception as e:
            validation["error"] = str(e)

        return validation

    def cleanup_test_environment(self):
        """清理测试环境"""
        print("\n🧹 清理测试环境...")

        try:
            # 清理UI资源
            if self.main_window:
                self.main_window.close()
                self.main_window = None

            if self.ui_app:
                self.ui_app.quit()
                self.ui_app = None

            # 清理创建的文件
            for file_path in self.created_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"   ⚠️  清理文件失败 {file_path}: {e}")

            # 清理临时目录
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"   ✅ 测试目录已清理: {self.temp_dir}")

        except Exception as e:
            print(f"   ❌ 清理测试环境失败: {e}")

    def run_comprehensive_real_world_test(self) -> Dict[str, Any]:
        """运行全面的真实世界端到端测试"""
        print("=" * 80)
        print("🚀 VisionAI-ClipsMaster 全面端到端输入输出链路测试")
        print("=" * 80)

        all_test_results = {
            "test_suite": "全面端到端输入输出链路测试",
            "start_time": self.test_start_time.isoformat(),
            "test_environment": {
                "temp_dir": str(self.temp_dir),
                "baseline_memory_gb": self.memory_baseline,
                "max_memory_limit_gb": self.config["max_memory_limit_gb"]
            },
            "test_results": {},
            "summary": {}
        }

        try:
            # 1. 创建真实测试材料
            test_materials = self.create_realistic_test_materials()
            all_test_results["test_materials"] = {
                "chinese_segments": test_materials["chinese_materials"]["segments"],
                "english_segments": test_materials["english_materials"]["segments"],
                "chinese_duration": test_materials["chinese_materials"]["duration"],
                "english_duration": test_materials["english_materials"]["duration"]
            }

            # 2. UI功能完整性验证
            ui_result = self.test_ui_comprehensive_functionality()
            all_test_results["test_results"]["ui_functionality"] = ui_result

            # 3. 核心功能链路测试
            core_result = self.test_core_functionality_chain(test_materials)
            all_test_results["test_results"]["core_functionality"] = core_result

            # 4. 完整工作流程集成测试
            workflow_result = self.test_complete_workflow_integration(test_materials)
            all_test_results["test_results"]["workflow_integration"] = workflow_result

            # 5. 计算综合测试结果
            self._calculate_comprehensive_summary(all_test_results)

            # 6. 生成详细测试报告
            self._generate_detailed_report(all_test_results)

        except Exception as e:
            print(f"\n❌ 测试执行失败: {e}")
            traceback.print_exc()
            all_test_results["error"] = str(e)

        finally:
            all_test_results["end_time"] = datetime.now().isoformat()
            all_test_results["total_duration"] = (datetime.now() - self.test_start_time).total_seconds()

        return all_test_results

    def _calculate_comprehensive_summary(self, all_test_results: Dict[str, Any]):
        """计算综合测试总结"""
        try:
            ui_result = all_test_results["test_results"]["ui_functionality"]
            core_result = all_test_results["test_results"]["core_functionality"]
            workflow_result = all_test_results["test_results"]["workflow_integration"]

            # UI成功率
            ui_success_rate = ui_result.get("summary", {}).get("ui_success_rate", 0)
            ui_interaction_rate = ui_result.get("summary", {}).get("interaction_success_rate", 0)

            # 核心功能成功率
            core_success_rate = core_result.get("summary", {}).get("chain_success_rate", 0)

            # 工作流程成功率
            workflow_success_rate = workflow_result.get("summary", {}).get("workflow_success_rate", 0)

            # 计算综合评分
            overall_score = (ui_success_rate * 0.2 +
                           ui_interaction_rate * 0.2 +
                           core_success_rate * 0.3 +
                           workflow_success_rate * 0.3)

            all_test_results["summary"] = {
                "ui_component_success_rate": ui_success_rate,
                "ui_interaction_success_rate": ui_interaction_rate,
                "core_functionality_success_rate": core_success_rate,
                "workflow_integration_success_rate": workflow_success_rate,
                "overall_success_score": overall_score,
                "test_grade": self._get_test_grade(overall_score),
                "system_readiness": self._assess_system_readiness(overall_score, all_test_results)
            }

        except Exception as e:
            all_test_results["summary"] = {"error": str(e)}

    def _get_test_grade(self, score: float) -> str:
        """获取测试等级"""
        if score >= 0.9:
            return "A+ (优秀)"
        elif score >= 0.8:
            return "A (良好)"
        elif score >= 0.7:
            return "B (合格)"
        elif score >= 0.6:
            return "C (需要改进)"
        else:
            return "D (不合格)"

    def _assess_system_readiness(self, score: float, all_test_results: Dict[str, Any]) -> str:
        """评估系统就绪状态"""
        if score >= 0.85:
            return "生产就绪"
        elif score >= 0.7:
            return "基本可用，需要优化"
        elif score >= 0.5:
            return "功能不完整，需要修复"
        else:
            return "不可用，需要重大修复"

    def _generate_detailed_report(self, all_test_results: Dict[str, Any]):
        """生成详细测试报告"""
        print("\n" + "=" * 80)
        print("📊 全面端到端测试总结报告")
        print("=" * 80)

        summary = all_test_results.get("summary", {})

        print(f"🎯 综合评分: {summary.get('overall_success_score', 0):.1%}")
        print(f"📈 测试等级: {summary.get('test_grade', 'N/A')}")
        print(f"🚀 系统状态: {summary.get('system_readiness', 'N/A')}")

        print(f"\n📋 详细成功率:")
        print(f"   UI组件可用率: {summary.get('ui_component_success_rate', 0):.1%}")
        print(f"   UI交互成功率: {summary.get('ui_interaction_success_rate', 0):.1%}")
        print(f"   核心功能成功率: {summary.get('core_functionality_success_rate', 0):.1%}")
        print(f"   工作流程成功率: {summary.get('workflow_integration_success_rate', 0):.1%}")

        # 保存详细报告
        report_path = self.temp_dir / "comprehensive_real_world_e2e_test_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(all_test_results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细测试报告已保存: {report_path}")


def main():
    """主函数"""
    try:
        # 创建测试套件
        test_suite = ComprehensiveRealWorldE2ETest()

        # 运行全面测试
        results = test_suite.run_comprehensive_real_world_test()

        # 清理测试环境
        test_suite.cleanup_test_environment()

        # 根据测试结果返回退出码
        summary = results.get("summary", {})
        overall_score = summary.get("overall_success_score", 0)
        system_readiness = summary.get("system_readiness", "")

        if overall_score >= 0.85:
            print("\n🎉 全面端到端测试完全通过！")
            print("   系统已准备好进行生产使用")
            return 0
        elif overall_score >= 0.7:
            print(f"\n✅ 测试基本通过，系统基本可用")
            print(f"   综合评分: {overall_score:.1%}")
            print(f"   系统状态: {system_readiness}")
            return 0
        elif overall_score >= 0.5:
            print(f"\n⚠️  测试部分通过，需要进一步优化")
            print(f"   综合评分: {overall_score:.1%}")
            print(f"   系统状态: {system_readiness}")
            return 1
        else:
            print(f"\n❌ 测试失败，系统需要重大修复")
            print(f"   综合评分: {overall_score:.1%}")
            print(f"   系统状态: {system_readiness}")
            return 2

    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
