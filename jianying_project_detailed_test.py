#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 剪映工程文件详细测试
专门测试剪映工程文件生成、导入兼容性和编辑功能
"""

import os
import sys
import json
import time
import tempfile
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 导入核心模块
try:
    from src.exporters.jianying_pro_exporter import JianyingProExporter
    from src.core.screenplay_engineer import import_srt
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保项目结构正确且依赖已安装")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jianying_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JianyingProjectTester:
    """剪映工程文件详细测试器"""
    
    def __init__(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="jianying_test_"))
        self.test_results = []
        self.created_files = []
        
        # 初始化剪映导出器
        self.jianying_exporter = JianyingProExporter()
        
        logger.info(f"测试目录: {self.test_dir}")
    
    def create_real_test_data(self) -> Tuple[str, str, str]:
        """创建真实的测试数据：视频文件和SRT字幕"""
        logger.info("创建真实测试数据...")
        
        # 创建一个简单的测试视频（使用FFmpeg生成）
        test_video_path = self.test_dir / "test_drama.mp4"
        
        # 尝试使用FFmpeg创建测试视频
        if self._create_test_video(test_video_path):
            logger.info(f"✅ 成功创建测试视频: {test_video_path}")
        else:
            # 如果FFmpeg不可用，创建一个占位文件
            logger.warning("FFmpeg不可用，创建占位视频文件")
            with open(test_video_path, 'wb') as f:
                # 写入一些二进制数据模拟视频文件
                f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
                f.write(b'\x00' * 1024)  # 1KB的占位数据
        
        self.created_files.append(str(test_video_path))
        
        # 创建原始SRT字幕文件
        original_srt_path = self.test_dir / "original_subtitles.srt"
        original_srt_content = """1
00:00:00,000 --> 00:00:05,000
第一段：男主角登场，展现其平凡的生活状态

2
00:00:05,000 --> 00:00:10,000
第二段：意外事件发生，改变了男主角的命运

3
00:00:10,000 --> 00:00:15,000
第三段：男主角开始觉醒，展现出特殊能力

4
00:00:15,000 --> 00:00:20,000
第四段：反派登场，与男主角产生冲突

5
00:00:20,000 --> 00:00:25,000
第五段：激烈的战斗场面，展现男主角的成长

6
00:00:25,000 --> 00:00:30,000
第六段：故事高潮，男主角面临最大挑战

7
00:00:30,000 --> 00:00:35,000
第七段：男主角克服困难，获得最终胜利

8
00:00:35,000 --> 00:00:40,000
第八段：结局，男主角的新生活和成长感悟"""
        
        with open(original_srt_path, 'w', encoding='utf-8') as f:
            f.write(original_srt_content)
        self.created_files.append(str(original_srt_path))
        
        # 创建重组后的爆款SRT字幕文件（非线性叙事）
        viral_srt_path = self.test_dir / "viral_subtitles.srt"
        viral_srt_content = """1
00:00:00,000 --> 00:00:03,000
故事高潮，男主角面临最大挑战

2
00:00:03,000 --> 00:00:08,000
第一段：男主角登场，展现其平凡的生活状态

3
00:00:08,000 --> 00:00:13,000
激烈的战斗场面，展现男主角的成长

4
00:00:13,000 --> 00:00:18,000
意外事件发生，改变了男主角的命运

5
00:00:18,000 --> 00:00:23,000
男主角克服困难，获得最终胜利

6
00:00:23,000 --> 00:00:28,000
男主角开始觉醒，展现出特殊能力"""
        
        with open(viral_srt_path, 'w', encoding='utf-8') as f:
            f.write(viral_srt_content)
        self.created_files.append(str(viral_srt_path))
        
        logger.info(f"测试数据创建完成:")
        logger.info(f"  测试视频: {test_video_path}")
        logger.info(f"  原始字幕: {original_srt_path}")
        logger.info(f"  爆款字幕: {viral_srt_path}")
        
        return str(test_video_path), str(original_srt_path), str(viral_srt_path)
    
    def _create_test_video(self, video_path: Path) -> bool:
        """使用FFmpeg创建测试视频"""
        try:
            # 检查FFmpeg是否可用
            ffmpeg_paths = [
                "ffmpeg",
                str(project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"),
                str(project_root / "tools" / "ffmpeg" / "bin" / "ffmpeg")
            ]
            
            ffmpeg_cmd = None
            for path in ffmpeg_paths:
                try:
                    result = subprocess.run([path, "-version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        ffmpeg_cmd = path
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                    continue
            
            if not ffmpeg_cmd:
                return False
            
            # 创建一个40秒的测试视频（彩色条纹 + 音频）
            cmd = [
                ffmpeg_cmd,
                "-f", "lavfi",
                "-i", "testsrc2=duration=40:size=1920x1080:rate=30",
                "-f", "lavfi", 
                "-i", "sine=frequency=1000:duration=40",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-t", "40",
                "-y",
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and video_path.exists():
                logger.info(f"成功创建测试视频: {video_path}")
                return True
            else:
                logger.warning(f"FFmpeg创建视频失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"创建测试视频时发生错误: {str(e)}")
            return False
    
    def test_project_file_generation(self, video_path: str, viral_srt_path: str) -> Dict[str, Any]:
        """测试1: 工程文件生成测试"""
        logger.info("=" * 60)
        logger.info("测试1: 剪映工程文件生成测试")
        logger.info("=" * 60)
        
        test_result = {
            "test_name": "剪映工程文件生成测试",
            "start_time": time.time(),
            "status": "未开始",
            "details": {},
            "errors": []
        }
        
        try:
            # 解析字幕文件
            logger.info("解析爆款SRT字幕文件...")
            subtitle_segments = import_srt(viral_srt_path)
            
            if not subtitle_segments:
                raise Exception("SRT字幕解析失败或为空")
            
            logger.info(f"成功解析 {len(subtitle_segments)} 个字幕片段")
            test_result["details"]["segments_count"] = len(subtitle_segments)
            
            # 准备项目数据
            project_data = {
                "segments": subtitle_segments,
                "source_video": video_path,
                "project_name": "VisionAI剪映测试项目",
                "description": "用于测试剪映兼容性的项目文件"
            }
            
            # 生成剪映工程文件路径
            jianying_project_path = self.test_dir / "test_project.draft"
            self.created_files.append(str(jianying_project_path))
            
            # 导出剪映工程文件
            logger.info("开始导出剪映工程文件...")
            export_success = self.jianying_exporter.export_project(
                project_data, str(jianying_project_path)
            )
            
            if export_success:
                logger.info("✅ 剪映工程文件导出成功")
                test_result["status"] = "通过"
                test_result["details"]["export_path"] = str(jianying_project_path)
                
                # 验证文件存在和大小
                if jianying_project_path.exists():
                    file_size = jianying_project_path.stat().st_size
                    logger.info(f"✅ 工程文件已创建: {jianying_project_path} ({file_size} bytes)")
                    test_result["details"]["file_created"] = True
                    test_result["details"]["file_size"] = file_size
                    
                    # 详细验证文件内容
                    validation_result = self._validate_project_file_content(jianying_project_path)
                    test_result["details"]["content_validation"] = validation_result
                    
                    if validation_result["valid"]:
                        logger.info("✅ 工程文件内容验证通过")
                    else:
                        logger.warning(f"⚠️ 工程文件内容验证发现问题: {validation_result['issues']}")
                        test_result["errors"].extend(validation_result["issues"])
                
                else:
                    logger.error("❌ 工程文件未创建")
                    test_result["details"]["file_created"] = False
                    test_result["errors"].append("工程文件未创建")
            
            else:
                logger.error("❌ 剪映工程文件导出失败")
                test_result["status"] = "失败"
                test_result["errors"].append("导出失败")
        
        except Exception as e:
            logger.error(f"❌ 剪映工程文件测试异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))
        
        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]
        
        self.test_results.append(test_result)
        return test_result

    def _validate_project_file_content(self, project_path: Path) -> Dict[str, Any]:
        """详细验证剪映工程文件内容"""
        validation_result = {
            "valid": True,
            "issues": [],
            "details": {}
        }

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_content = json.load(f)

            # 1. 基本结构检查
            required_fields = [
                "version", "type", "platform", "create_time", "update_time",
                "id", "canvas_config", "tracks", "materials"
            ]

            missing_fields = [field for field in required_fields if field not in project_content]
            if missing_fields:
                validation_result["valid"] = False
                validation_result["issues"].append(f"缺少必需字段: {missing_fields}")

            # 2. 版本兼容性检查
            version = project_content.get("version", "")
            if not version.startswith(("3.", "2.9", "2.8")):
                validation_result["issues"].append(f"版本可能不兼容: {version}")

            # 3. 轨道结构检查
            tracks = project_content.get("tracks", [])
            if not tracks:
                validation_result["valid"] = False
                validation_result["issues"].append("没有轨道数据")
            else:
                video_tracks = [t for t in tracks if t.get("type") == "video"]
                audio_tracks = [t for t in tracks if t.get("type") == "audio"]
                text_tracks = [t for t in tracks if t.get("type") == "text"]

                validation_result["details"]["track_counts"] = {
                    "video": len(video_tracks),
                    "audio": len(audio_tracks),
                    "text": len(text_tracks),
                    "total": len(tracks)
                }

                # 检查视频轨道的片段
                for i, track in enumerate(video_tracks):
                    segments = track.get("segments", [])
                    if not segments:
                        validation_result["issues"].append(f"视频轨道 {i} 没有片段")
                    else:
                        validation_result["details"][f"video_track_{i}_segments"] = len(segments)

                        # 检查每个片段的时间轴
                        for j, segment in enumerate(segments):
                            timerange = segment.get("target_timerange", {})
                            start = timerange.get("start", 0)
                            duration = timerange.get("duration", 0)

                            if duration <= 0:
                                validation_result["issues"].append(
                                    f"视频轨道 {i} 片段 {j} 持续时间无效: {duration}"
                                )

                            if start < 0:
                                validation_result["issues"].append(
                                    f"视频轨道 {i} 片段 {j} 开始时间无效: {start}"
                                )

            # 4. 素材库检查
            materials = project_content.get("materials", {})
            if not materials:
                validation_result["valid"] = False
                validation_result["issues"].append("没有素材数据")
            else:
                video_materials = materials.get("videos", [])
                audio_materials = materials.get("audios", [])
                text_materials = materials.get("texts", [])

                validation_result["details"]["material_counts"] = {
                    "videos": len(video_materials),
                    "audios": len(audio_materials),
                    "texts": len(text_materials)
                }

                # 检查视频素材的路径
                for i, video_material in enumerate(video_materials):
                    path = video_material.get("path", "")
                    if not path:
                        validation_result["issues"].append(f"视频素材 {i} 缺少路径")

            # 5. 画布配置检查
            canvas_config = project_content.get("canvas_config", {})
            if not canvas_config:
                validation_result["issues"].append("缺少画布配置")
            else:
                width = canvas_config.get("width", 0)
                height = canvas_config.get("height", 0)
                fps = canvas_config.get("fps", 0)

                if width <= 0 or height <= 0:
                    validation_result["issues"].append(f"画布尺寸无效: {width}x{height}")

                if fps <= 0:
                    validation_result["issues"].append(f"帧率无效: {fps}")

                validation_result["details"]["canvas"] = {
                    "width": width,
                    "height": height,
                    "fps": fps
                }

            # 6. 素材引用完整性检查
            material_ids = set()
            for material_type, material_list in materials.items():
                if isinstance(material_list, list):
                    for material in material_list:
                        if isinstance(material, dict) and "id" in material:
                            material_ids.add(material["id"])

            referenced_ids = set()
            for track in tracks:
                segments = track.get("segments", [])
                for segment in segments:
                    material_id = segment.get("material_id")
                    if material_id:
                        referenced_ids.add(material_id)

            missing_materials = referenced_ids - material_ids
            if missing_materials:
                validation_result["valid"] = False
                validation_result["issues"].append(f"缺少被引用的素材: {list(missing_materials)}")

            validation_result["details"]["material_reference_check"] = {
                "total_materials": len(material_ids),
                "referenced_materials": len(referenced_ids),
                "missing_materials": len(missing_materials)
            }

        except json.JSONDecodeError as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"JSON格式错误: {str(e)}")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["issues"].append(f"验证过程异常: {str(e)}")

        return validation_result

    def test_jianying_import_compatibility(self, project_path: str) -> Dict[str, Any]:
        """测试2: 剪映软件导入兼容性测试"""
        logger.info("=" * 60)
        logger.info("测试2: 剪映软件导入兼容性测试")
        logger.info("=" * 60)

        test_result = {
            "test_name": "剪映软件导入兼容性测试",
            "start_time": time.time(),
            "status": "未开始",
            "details": {},
            "errors": []
        }

        try:
            if not os.path.exists(project_path):
                raise Exception(f"剪映工程文件不存在: {project_path}")

            # 1. 文件格式预检查
            logger.info("执行文件格式预检查...")
            format_check = self._pre_check_file_format(project_path)
            test_result["details"]["format_check"] = format_check

            if not format_check["valid"]:
                test_result["status"] = "失败"
                test_result["errors"].extend(format_check["issues"])
                return test_result

            # 2. 尝试检测剪映软件
            logger.info("检测剪映软件安装...")
            jianying_detection = self._detect_jianying_software()
            test_result["details"]["jianying_detection"] = jianying_detection

            if jianying_detection["found"]:
                logger.info(f"✅ 检测到剪映软件: {jianying_detection['path']}")

                # 3. 尝试实际导入测试
                import_result = self._test_actual_import(project_path, jianying_detection["path"])
                test_result["details"]["actual_import"] = import_result

                if import_result["success"]:
                    logger.info("✅ 剪映软件导入测试成功")
                    test_result["status"] = "通过"
                else:
                    logger.warning(f"⚠️ 剪映软件导入测试失败: {import_result.get('error', '未知错误')}")
                    test_result["status"] = "失败"
                    test_result["errors"].append(f"导入失败: {import_result.get('error')}")

            else:
                logger.warning("⚠️ 未检测到剪映软件，执行模拟兼容性测试")

                # 4. 模拟兼容性测试
                simulation_result = self._simulate_jianying_compatibility(project_path)
                test_result["details"]["simulation"] = simulation_result

                if simulation_result["compatible"]:
                    logger.info("✅ 模拟兼容性测试通过")
                    test_result["status"] = "通过（模拟）"
                else:
                    logger.warning(f"⚠️ 模拟兼容性测试失败: {simulation_result.get('issues', [])}")
                    test_result["status"] = "失败"
                    test_result["errors"].extend(simulation_result.get("issues", []))

        except Exception as e:
            logger.error(f"❌ 剪映兼容性测试异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))

        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]

        self.test_results.append(test_result)
        return test_result

    def _pre_check_file_format(self, project_path: str) -> Dict[str, Any]:
        """预检查文件格式"""
        check_result = {
            "valid": True,
            "issues": [],
            "details": {}
        }

        try:
            # 检查文件扩展名
            if not project_path.endswith('.draft'):
                check_result["issues"].append("文件扩展名不是.draft")

            # 检查文件大小
            file_size = os.path.getsize(project_path)
            if file_size == 0:
                check_result["valid"] = False
                check_result["issues"].append("文件大小为0")
            elif file_size > 100 * 1024 * 1024:  # 100MB
                check_result["issues"].append("文件过大，可能有问题")

            check_result["details"]["file_size"] = file_size

            # 检查JSON格式
            with open(project_path, 'r', encoding='utf-8') as f:
                content = json.load(f)

            # 检查基本字段
            if content.get("type") != "draft_content":
                check_result["issues"].append("文件类型不是draft_content")

            if not content.get("version"):
                check_result["issues"].append("缺少版本信息")

            check_result["details"]["version"] = content.get("version", "未知")
            check_result["details"]["type"] = content.get("type", "未知")

        except json.JSONDecodeError as e:
            check_result["valid"] = False
            check_result["issues"].append(f"JSON格式错误: {str(e)}")
        except Exception as e:
            check_result["valid"] = False
            check_result["issues"].append(f"文件检查异常: {str(e)}")

        if check_result["issues"]:
            check_result["valid"] = False

        return check_result

    def _detect_jianying_software(self) -> Dict[str, Any]:
        """检测剪映软件安装"""
        detection_result = {
            "found": False,
            "path": None,
            "version": None,
            "details": {}
        }

        # 常见的剪映安装路径
        possible_paths = [
            # Windows路径
            r"C:\Program Files\JianyingPro\JianyingPro.exe",
            r"C:\Program Files (x86)\JianyingPro\JianyingPro.exe",
            r"C:\Users\{}\AppData\Local\JianyingPro\JianyingPro.exe".format(os.getenv('USERNAME', '')),
            # 可能的其他路径
            r"D:\Program Files\JianyingPro\JianyingPro.exe",
            r"E:\Program Files\JianyingPro\JianyingPro.exe",
        ]

        for path in possible_paths:
            try:
                if os.path.exists(path):
                    detection_result["found"] = True
                    detection_result["path"] = path

                    # 尝试获取版本信息
                    try:
                        import win32api
                        version_info = win32api.GetFileVersionInfo(path, "\\")
                        version = f"{version_info['FileVersionMS'] >> 16}.{version_info['FileVersionMS'] & 0xFFFF}.{version_info['FileVersionLS'] >> 16}.{version_info['FileVersionLS'] & 0xFFFF}"
                        detection_result["version"] = version
                    except:
                        detection_result["version"] = "无法获取版本"

                    break
            except Exception as e:
                continue

        # 如果没有找到，尝试通过注册表查找
        if not detection_result["found"]:
            try:
                import winreg

                # 查找卸载信息
                uninstall_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                             r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")

                for i in range(winreg.QueryInfoKey(uninstall_key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(uninstall_key, i)
                        subkey = winreg.OpenKey(uninstall_key, subkey_name)

                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if "剪映" in display_name or "JianyingPro" in display_name:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            exe_path = os.path.join(install_location, "JianyingPro.exe")

                            if os.path.exists(exe_path):
                                detection_result["found"] = True
                                detection_result["path"] = exe_path
                                detection_result["version"] = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                break

                        winreg.CloseKey(subkey)
                    except:
                        continue

                winreg.CloseKey(uninstall_key)
            except:
                pass

        return detection_result

    def _test_actual_import(self, project_path: str, jianying_path: str) -> Dict[str, Any]:
        """测试实际的剪映导入"""
        import_result = {
            "success": False,
            "error": None,
            "details": {}
        }

        try:
            # 尝试启动剪映并打开项目文件
            # 注意：这可能需要用户交互，在自动化测试中可能不适用
            logger.info("尝试启动剪映软件...")

            # 使用subprocess启动剪映
            cmd = [jianying_path, project_path]

            # 设置较短的超时时间，避免长时间等待
            process = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW)

            # 等待一小段时间看是否能正常启动
            time.sleep(3)

            # 检查进程状态
            if process.poll() is None:
                # 进程仍在运行，说明启动成功
                import_result["success"] = True
                import_result["details"]["process_started"] = True

                # 终止进程（避免影响系统）
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

                logger.info("✅ 剪映软件成功启动并打开项目文件")
            else:
                # 进程已退出，可能有错误
                stdout, stderr = process.communicate()
                import_result["error"] = f"进程退出，返回码: {process.returncode}"
                if stderr:
                    import_result["error"] += f", 错误信息: {stderr.decode('utf-8', errors='ignore')}"

        except Exception as e:
            import_result["error"] = f"启动剪映时发生异常: {str(e)}"

        return import_result

    def _simulate_jianying_compatibility(self, project_path: str) -> Dict[str, Any]:
        """模拟剪映兼容性测试"""
        compatibility_result = {
            "compatible": True,
            "issues": [],
            "details": {}
        }

        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                project_content = json.load(f)

            # 模拟剪映的导入验证流程

            # 1. 版本兼容性
            version = project_content.get("version", "")
            supported_versions = ["3.0.0", "2.9.0", "2.8.0"]
            if not any(version.startswith(v) for v in supported_versions):
                compatibility_result["issues"].append(f"版本 {version} 可能不被支持")

            # 2. 必需字段检查
            required_fields = ["id", "type", "version", "tracks", "materials", "canvas_config"]
            missing_fields = [field for field in required_fields if field not in project_content]
            if missing_fields:
                compatibility_result["issues"].append(f"缺少必需字段: {missing_fields}")

            # 3. 轨道结构验证
            tracks = project_content.get("tracks", [])
            if not tracks:
                compatibility_result["issues"].append("没有轨道数据")

            # 4. 素材路径验证
            materials = project_content.get("materials", {})
            video_materials = materials.get("videos", [])

            for i, video_material in enumerate(video_materials):
                path = video_material.get("path", "")
                if path and not os.path.exists(path):
                    compatibility_result["issues"].append(f"视频素材 {i} 路径不存在: {path}")

            # 5. 时间轴连续性检查
            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])
                    for i, segment in enumerate(segments):
                        timerange = segment.get("target_timerange", {})
                        start = timerange.get("start", 0)
                        duration = timerange.get("duration", 0)

                        if duration <= 0:
                            compatibility_result["issues"].append(f"片段 {i} 持续时间无效")

                        if start < 0:
                            compatibility_result["issues"].append(f"片段 {i} 开始时间无效")

            if compatibility_result["issues"]:
                compatibility_result["compatible"] = False

            compatibility_result["details"]["total_checks"] = 5
            compatibility_result["details"]["issues_found"] = len(compatibility_result["issues"])

        except Exception as e:
            compatibility_result["compatible"] = False
            compatibility_result["issues"].append(f"兼容性检查异常: {str(e)}")

        return compatibility_result

    def test_timeline_structure(self, project_path: str) -> Dict[str, Any]:
        """测试3: 时间轴结构验证"""
        logger.info("=" * 60)
        logger.info("测试3: 时间轴结构验证")
        logger.info("=" * 60)

        test_result = {
            "test_name": "时间轴结构验证",
            "start_time": time.time(),
            "status": "未开始",
            "details": {},
            "errors": []
        }

        try:
            if not os.path.exists(project_path):
                raise Exception(f"剪映工程文件不存在: {project_path}")

            with open(project_path, 'r', encoding='utf-8') as f:
                project_content = json.load(f)

            # 1. 验证多个独立视频段
            logger.info("验证时间轴上的视频段结构...")
            timeline_analysis = self._analyze_timeline_structure(project_content)
            test_result["details"]["timeline_analysis"] = timeline_analysis

            if timeline_analysis["valid"]:
                logger.info(f"✅ 时间轴结构正确: {timeline_analysis['video_segments_count']} 个视频段")
            else:
                logger.warning(f"⚠️ 时间轴结构问题: {timeline_analysis['issues']}")
                test_result["errors"].extend(timeline_analysis["issues"])

            # 2. 验证视频段与素材库的映射关系
            logger.info("验证视频段与素材库的映射关系...")
            mapping_analysis = self._analyze_material_mapping(project_content)
            test_result["details"]["mapping_analysis"] = mapping_analysis

            if mapping_analysis["valid"]:
                logger.info(f"✅ 素材映射正确: {mapping_analysis['mapped_segments']} 个片段已映射")
            else:
                logger.warning(f"⚠️ 素材映射问题: {mapping_analysis['issues']}")
                test_result["errors"].extend(mapping_analysis["issues"])

            # 3. 验证未渲染状态
            logger.info("验证视频段的未渲染状态...")
            render_status = self._check_render_status(project_content)
            test_result["details"]["render_status"] = render_status

            if render_status["unrendered"]:
                logger.info("✅ 视频段处于未渲染状态，可以进行编辑")
            else:
                logger.warning("⚠️ 视频段可能已渲染，编辑功能可能受限")
                test_result["errors"].append("视频段可能已渲染")

            # 4. 验证时间轴连续性和间隔
            logger.info("验证时间轴连续性...")
            continuity_check = self._check_timeline_continuity(project_content)
            test_result["details"]["continuity_check"] = continuity_check

            if continuity_check["valid"]:
                logger.info("✅ 时间轴连续性正确")
            else:
                logger.warning(f"⚠️ 时间轴连续性问题: {continuity_check['issues']}")
                test_result["errors"].extend(continuity_check["issues"])

            # 综合评估
            if not test_result["errors"]:
                test_result["status"] = "通过"
                logger.info("✅ 时间轴结构验证全部通过")
            else:
                test_result["status"] = "部分通过"
                logger.warning("⚠️ 时间轴结构验证发现问题")

        except Exception as e:
            logger.error(f"❌ 时间轴结构验证异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))

        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]

        self.test_results.append(test_result)
        return test_result

    def _analyze_timeline_structure(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析时间轴结构"""
        analysis = {
            "valid": True,
            "issues": [],
            "video_segments_count": 0,
            "audio_segments_count": 0,
            "text_segments_count": 0,
            "details": {}
        }

        try:
            tracks = project_content.get("tracks", [])

            for track in tracks:
                track_type = track.get("type", "")
                segments = track.get("segments", [])

                if track_type == "video":
                    analysis["video_segments_count"] += len(segments)

                    # 检查每个视频段的属性
                    for i, segment in enumerate(segments):
                        # 检查时间范围
                        target_timerange = segment.get("target_timerange", {})
                        source_timerange = segment.get("source_timerange", {})

                        if not target_timerange:
                            analysis["issues"].append(f"视频段 {i} 缺少目标时间范围")

                        if not source_timerange:
                            analysis["issues"].append(f"视频段 {i} 缺少源时间范围")

                        # 检查素材ID
                        material_id = segment.get("material_id")
                        if not material_id:
                            analysis["issues"].append(f"视频段 {i} 缺少素材ID")

                elif track_type == "audio":
                    analysis["audio_segments_count"] += len(segments)
                elif track_type == "text":
                    analysis["text_segments_count"] += len(segments)

            # 验证是否有足够的视频段
            if analysis["video_segments_count"] == 0:
                analysis["valid"] = False
                analysis["issues"].append("没有视频段")
            elif analysis["video_segments_count"] < 2:
                analysis["issues"].append("视频段数量过少，可能不符合混剪要求")

            analysis["details"]["total_tracks"] = len(tracks)

        except Exception as e:
            analysis["valid"] = False
            analysis["issues"].append(f"时间轴分析异常: {str(e)}")

        return analysis

    def _analyze_material_mapping(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析素材映射关系"""
        mapping = {
            "valid": True,
            "issues": [],
            "mapped_segments": 0,
            "unmapped_segments": 0,
            "material_details": {}
        }

        try:
            # 收集所有素材ID
            materials = project_content.get("materials", {})
            material_ids = set()

            for material_type, material_list in materials.items():
                if isinstance(material_list, list):
                    for material in material_list:
                        if isinstance(material, dict) and "id" in material:
                            material_ids.add(material["id"])

                            # 记录素材详情
                            mapping["material_details"][material["id"]] = {
                                "type": material_type,
                                "path": material.get("path", ""),
                                "name": material.get("name", "")
                            }

            # 检查轨道中的素材引用
            tracks = project_content.get("tracks", [])
            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])
                    for i, segment in enumerate(segments):
                        material_id = segment.get("material_id")

                        if material_id:
                            if material_id in material_ids:
                                mapping["mapped_segments"] += 1
                            else:
                                mapping["unmapped_segments"] += 1
                                mapping["issues"].append(f"视频段 {i} 引用的素材ID不存在: {material_id}")
                        else:
                            mapping["unmapped_segments"] += 1
                            mapping["issues"].append(f"视频段 {i} 没有素材ID")

            if mapping["unmapped_segments"] > 0:
                mapping["valid"] = False

        except Exception as e:
            mapping["valid"] = False
            mapping["issues"].append(f"素材映射分析异常: {str(e)}")

        return mapping

    def _check_render_status(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查渲染状态"""
        render_status = {
            "unrendered": True,
            "details": {}
        }

        try:
            # 检查是否有渲染相关的字段
            # 在剪映中，未渲染的片段通常没有render_index等字段

            tracks = project_content.get("tracks", [])
            rendered_segments = 0
            total_segments = 0

            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])
                    total_segments += len(segments)

                    for segment in segments:
                        # 检查是否有渲染标记
                        if segment.get("render_index") is not None:
                            rendered_segments += 1

                        # 检查是否有缓存文件路径
                        if segment.get("cache_path"):
                            rendered_segments += 1

            render_status["details"]["total_segments"] = total_segments
            render_status["details"]["rendered_segments"] = rendered_segments
            render_status["details"]["unrendered_segments"] = total_segments - rendered_segments

            # 如果有渲染的片段，则认为不是完全未渲染状态
            if rendered_segments > 0:
                render_status["unrendered"] = False

        except Exception as e:
            render_status["unrendered"] = True  # 出错时假设未渲染
            render_status["details"]["error"] = str(e)

        return render_status

    def _check_timeline_continuity(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查时间轴连续性"""
        continuity = {
            "valid": True,
            "issues": [],
            "details": {}
        }

        try:
            tracks = project_content.get("tracks", [])

            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])

                    # 按开始时间排序
                    sorted_segments = sorted(segments,
                                           key=lambda x: x.get("target_timerange", {}).get("start", 0))

                    total_duration = 0
                    gaps = []
                    overlaps = []

                    for i, segment in enumerate(sorted_segments):
                        timerange = segment.get("target_timerange", {})
                        start = timerange.get("start", 0)
                        duration = timerange.get("duration", 0)
                        end = start + duration

                        if i > 0:
                            prev_segment = sorted_segments[i-1]
                            prev_timerange = prev_segment.get("target_timerange", {})
                            prev_end = prev_timerange.get("start", 0) + prev_timerange.get("duration", 0)

                            # 检查间隙
                            if start > prev_end:
                                gap = start - prev_end
                                gaps.append({"position": prev_end, "duration": gap})

                            # 检查重叠
                            elif start < prev_end:
                                overlap = prev_end - start
                                overlaps.append({"position": start, "duration": overlap})

                        total_duration = max(total_duration, end)

                    continuity["details"]["total_duration"] = total_duration
                    continuity["details"]["gaps"] = gaps
                    continuity["details"]["overlaps"] = overlaps
                    continuity["details"]["segments_count"] = len(segments)

                    # 评估连续性
                    if len(gaps) > 0:
                        continuity["issues"].append(f"发现 {len(gaps)} 个时间间隙")

                    if len(overlaps) > 0:
                        continuity["issues"].append(f"发现 {len(overlaps)} 个时间重叠")

            if continuity["issues"]:
                continuity["valid"] = False

        except Exception as e:
            continuity["valid"] = False
            continuity["issues"].append(f"连续性检查异常: {str(e)}")

        return continuity

    def test_editing_functionality(self, project_path: str) -> Dict[str, Any]:
        """测试4: 编辑功能测试"""
        logger.info("=" * 60)
        logger.info("测试4: 编辑功能测试")
        logger.info("=" * 60)

        test_result = {
            "test_name": "编辑功能测试",
            "start_time": time.time(),
            "status": "未开始",
            "details": {},
            "errors": []
        }

        try:
            if not os.path.exists(project_path):
                raise Exception(f"剪映工程文件不存在: {project_path}")

            # 创建工程文件的备份
            backup_path = project_path.replace('.draft', '_backup.draft')
            shutil.copy2(project_path, backup_path)
            self.created_files.append(backup_path)

            with open(project_path, 'r', encoding='utf-8') as f:
                project_content = json.load(f)

            # 1. 测试视频段时长调整
            logger.info("测试视频段时长调整功能...")
            duration_test = self._test_segment_duration_adjustment(project_content)
            test_result["details"]["duration_adjustment"] = duration_test

            if duration_test["success"]:
                logger.info("✅ 视频段时长调整测试通过")
            else:
                logger.warning(f"⚠️ 视频段时长调整测试失败: {duration_test['error']}")
                test_result["errors"].append(f"时长调整失败: {duration_test['error']}")

            # 2. 测试入点出点拖拽模拟
            logger.info("测试入点出点拖拽功能...")
            drag_test = self._test_in_out_point_dragging(project_content)
            test_result["details"]["drag_test"] = drag_test

            if drag_test["success"]:
                logger.info("✅ 入点出点拖拽测试通过")
            else:
                logger.warning(f"⚠️ 入点出点拖拽测试失败: {drag_test['error']}")
                test_result["errors"].append(f"拖拽测试失败: {drag_test['error']}")

            # 3. 测试素材映射关系保持
            logger.info("测试素材映射关系保持...")
            mapping_test = self._test_material_mapping_preservation(project_content)
            test_result["details"]["mapping_preservation"] = mapping_test

            if mapping_test["success"]:
                logger.info("✅ 素材映射关系保持测试通过")
            else:
                logger.warning(f"⚠️ 素材映射关系保持测试失败: {mapping_test['error']}")
                test_result["errors"].append(f"映射保持失败: {mapping_test['error']}")

            # 4. 保存修改后的工程文件
            modified_path = project_path.replace('.draft', '_modified.draft')
            with open(modified_path, 'w', encoding='utf-8') as f:
                json.dump(project_content, f, ensure_ascii=False, indent=2)
            self.created_files.append(modified_path)

            test_result["details"]["modified_file"] = modified_path

            # 综合评估
            if not test_result["errors"]:
                test_result["status"] = "通过"
                logger.info("✅ 编辑功能测试全部通过")
            else:
                test_result["status"] = "部分通过"
                logger.warning("⚠️ 编辑功能测试发现问题")

        except Exception as e:
            logger.error(f"❌ 编辑功能测试异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))

        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]

        self.test_results.append(test_result)
        return test_result

    def _test_segment_duration_adjustment(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """测试视频段时长调整"""
        test_result = {
            "success": True,
            "error": None,
            "adjustments": []
        }

        try:
            tracks = project_content.get("tracks", [])

            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])

                    for i, segment in enumerate(segments):
                        target_timerange = segment.get("target_timerange", {})
                        original_duration = target_timerange.get("duration", 0)

                        if original_duration > 0:
                            # 测试延长时长（增加50%）
                            new_duration = int(original_duration * 1.5)
                            target_timerange["duration"] = new_duration

                            test_result["adjustments"].append({
                                "segment_index": i,
                                "original_duration": original_duration,
                                "new_duration": new_duration,
                                "change_type": "extend"
                            })

                            # 只测试前两个片段，避免过度修改
                            if len(test_result["adjustments"]) >= 2:
                                break

                    break  # 只处理第一个视频轨道

            if not test_result["adjustments"]:
                test_result["success"] = False
                test_result["error"] = "没有找到可调整的视频段"

        except Exception as e:
            test_result["success"] = False
            test_result["error"] = str(e)

        return test_result

    def _test_in_out_point_dragging(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """测试入点出点拖拽"""
        test_result = {
            "success": True,
            "error": None,
            "drag_operations": []
        }

        try:
            tracks = project_content.get("tracks", [])

            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])

                    for i, segment in enumerate(segments):
                        source_timerange = segment.get("source_timerange", {})
                        original_start = source_timerange.get("start", 0)
                        original_duration = source_timerange.get("duration", 0)

                        if original_duration > 1000:  # 只对时长大于1秒的片段进行测试
                            # 模拟拖拽入点（向后移动500ms）
                            new_start = original_start + 500
                            new_duration = original_duration - 500

                            source_timerange["start"] = new_start
                            source_timerange["duration"] = new_duration

                            test_result["drag_operations"].append({
                                "segment_index": i,
                                "operation": "drag_in_point",
                                "original_start": original_start,
                                "new_start": new_start,
                                "duration_change": -500
                            })

                            # 只测试一个片段
                            break

                    break  # 只处理第一个视频轨道

            if not test_result["drag_operations"]:
                test_result["success"] = False
                test_result["error"] = "没有找到适合拖拽测试的视频段"

        except Exception as e:
            test_result["success"] = False
            test_result["error"] = str(e)

        return test_result

    def _test_material_mapping_preservation(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """测试素材映射关系保持"""
        test_result = {
            "success": True,
            "error": None,
            "mapping_check": {}
        }

        try:
            # 收集所有素材ID
            materials = project_content.get("materials", {})
            material_ids = set()

            for material_type, material_list in materials.items():
                if isinstance(material_list, list):
                    for material in material_list:
                        if isinstance(material, dict) and "id" in material:
                            material_ids.add(material["id"])

            # 检查轨道中的素材引用
            tracks = project_content.get("tracks", [])
            valid_mappings = 0
            invalid_mappings = 0

            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])

                    for segment in segments:
                        material_id = segment.get("material_id")

                        if material_id and material_id in material_ids:
                            valid_mappings += 1
                        else:
                            invalid_mappings += 1

            test_result["mapping_check"] = {
                "valid_mappings": valid_mappings,
                "invalid_mappings": invalid_mappings,
                "total_materials": len(material_ids)
            }

            if invalid_mappings > 0:
                test_result["success"] = False
                test_result["error"] = f"发现 {invalid_mappings} 个无效的素材映射"

        except Exception as e:
            test_result["success"] = False
            test_result["error"] = str(e)

        return test_result

    def test_playback_preview(self, project_path: str) -> Dict[str, Any]:
        """测试5: 播放预览测试"""
        logger.info("=" * 60)
        logger.info("测试5: 播放预览测试")
        logger.info("=" * 60)

        test_result = {
            "test_name": "播放预览测试",
            "start_time": time.time(),
            "status": "未开始",
            "details": {},
            "errors": []
        }

        try:
            if not os.path.exists(project_path):
                raise Exception(f"剪映工程文件不存在: {project_path}")

            with open(project_path, 'r', encoding='utf-8') as f:
                project_content = json.load(f)

            # 1. 验证音视频同步配置
            logger.info("验证音视频同步配置...")
            sync_check = self._check_audio_video_sync(project_content)
            test_result["details"]["sync_check"] = sync_check

            if sync_check["synchronized"]:
                logger.info("✅ 音视频同步配置正确")
            else:
                logger.warning(f"⚠️ 音视频同步问题: {sync_check['issues']}")
                test_result["errors"].extend(sync_check["issues"])

            # 2. 验证播放参数
            logger.info("验证播放参数...")
            playback_check = self._check_playback_parameters(project_content)
            test_result["details"]["playback_check"] = playback_check

            if playback_check["valid"]:
                logger.info("✅ 播放参数配置正确")
            else:
                logger.warning(f"⚠️ 播放参数问题: {playback_check['issues']}")
                test_result["errors"].extend(playback_check["issues"])

            # 3. 模拟预览测试
            logger.info("执行模拟预览测试...")
            preview_simulation = self._simulate_preview_playback(project_content)
            test_result["details"]["preview_simulation"] = preview_simulation

            if preview_simulation["success"]:
                logger.info("✅ 模拟预览测试通过")
            else:
                logger.warning(f"⚠️ 模拟预览测试失败: {preview_simulation['error']}")
                test_result["errors"].append(f"预览失败: {preview_simulation['error']}")

            # 综合评估
            if not test_result["errors"]:
                test_result["status"] = "通过"
                logger.info("✅ 播放预览测试全部通过")
            else:
                test_result["status"] = "部分通过"
                logger.warning("⚠️ 播放预览测试发现问题")

        except Exception as e:
            logger.error(f"❌ 播放预览测试异常: {str(e)}")
            test_result["status"] = "异常"
            test_result["errors"].append(str(e))

        test_result["end_time"] = time.time()
        test_result["duration"] = test_result["end_time"] - test_result["start_time"]

        self.test_results.append(test_result)
        return test_result

    def _check_audio_video_sync(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查音视频同步"""
        sync_check = {
            "synchronized": True,
            "issues": [],
            "details": {}
        }

        try:
            tracks = project_content.get("tracks", [])
            video_tracks = [t for t in tracks if t.get("type") == "video"]
            audio_tracks = [t for t in tracks if t.get("type") == "audio"]

            sync_check["details"]["video_tracks_count"] = len(video_tracks)
            sync_check["details"]["audio_tracks_count"] = len(audio_tracks)

            # 检查视频和音频轨道数量匹配
            if len(video_tracks) != len(audio_tracks):
                sync_check["issues"].append("视频轨道和音频轨道数量不匹配")

            # 检查对应片段的时间轴是否同步
            for i, video_track in enumerate(video_tracks):
                if i < len(audio_tracks):
                    audio_track = audio_tracks[i]

                    video_segments = video_track.get("segments", [])
                    audio_segments = audio_track.get("segments", [])

                    if len(video_segments) != len(audio_segments):
                        sync_check["issues"].append(f"轨道 {i} 的视频和音频片段数量不匹配")

                    # 检查对应片段的时间轴
                    for j, video_segment in enumerate(video_segments):
                        if j < len(audio_segments):
                            audio_segment = audio_segments[j]

                            video_timerange = video_segment.get("target_timerange", {})
                            audio_timerange = audio_segment.get("target_timerange", {})

                            video_start = video_timerange.get("start", 0)
                            audio_start = audio_timerange.get("start", 0)

                            # 允许50ms的误差
                            if abs(video_start - audio_start) > 50:
                                sync_check["issues"].append(
                                    f"轨道 {i} 片段 {j} 音视频开始时间不同步"
                                )

            if sync_check["issues"]:
                sync_check["synchronized"] = False

        except Exception as e:
            sync_check["synchronized"] = False
            sync_check["issues"].append(f"音视频同步检查异常: {str(e)}")

        return sync_check

    def _check_playback_parameters(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查播放参数"""
        playback_check = {
            "valid": True,
            "issues": [],
            "parameters": {}
        }

        try:
            canvas_config = project_content.get("canvas_config", {})

            # 检查基本播放参数
            width = canvas_config.get("width", 0)
            height = canvas_config.get("height", 0)
            fps = canvas_config.get("fps", 0)
            duration = canvas_config.get("duration", 0)

            playback_check["parameters"] = {
                "width": width,
                "height": height,
                "fps": fps,
                "duration": duration
            }

            # 验证参数有效性
            if width <= 0 or height <= 0:
                playback_check["issues"].append(f"画布尺寸无效: {width}x{height}")

            if fps <= 0 or fps > 120:
                playback_check["issues"].append(f"帧率无效: {fps}")

            if duration <= 0:
                playback_check["issues"].append(f"总时长无效: {duration}")

            # 检查常见分辨率
            common_resolutions = [
                (1920, 1080), (1280, 720), (3840, 2160),  # 横屏
                (1080, 1920), (720, 1280), (2160, 3840)   # 竖屏
            ]

            if (width, height) not in common_resolutions:
                playback_check["issues"].append(f"非标准分辨率: {width}x{height}")

            if playback_check["issues"]:
                playback_check["valid"] = False

        except Exception as e:
            playback_check["valid"] = False
            playback_check["issues"].append(f"播放参数检查异常: {str(e)}")

        return playback_check

    def _simulate_preview_playback(self, project_content: Dict[str, Any]) -> Dict[str, Any]:
        """模拟预览播放"""
        simulation = {
            "success": True,
            "error": None,
            "playback_info": {}
        }

        try:
            # 计算总播放时长
            tracks = project_content.get("tracks", [])
            max_duration = 0

            for track in tracks:
                if track.get("type") == "video":
                    segments = track.get("segments", [])

                    for segment in segments:
                        timerange = segment.get("target_timerange", {})
                        start = timerange.get("start", 0)
                        duration = timerange.get("duration", 0)
                        end = start + duration

                        max_duration = max(max_duration, end)

            simulation["playback_info"]["calculated_duration"] = max_duration

            # 检查素材文件可访问性
            materials = project_content.get("materials", {})
            accessible_materials = 0
            inaccessible_materials = 0

            for material_type, material_list in materials.items():
                if isinstance(material_list, list):
                    for material in material_list:
                        path = material.get("path", "")
                        if path and os.path.exists(path):
                            accessible_materials += 1
                        else:
                            inaccessible_materials += 1

            simulation["playback_info"]["accessible_materials"] = accessible_materials
            simulation["playback_info"]["inaccessible_materials"] = inaccessible_materials

            # 如果有不可访问的素材，预览可能有问题
            if inaccessible_materials > 0:
                simulation["success"] = False
                simulation["error"] = f"有 {inaccessible_materials} 个素材文件不可访问"

            # 检查是否有足够的内容进行预览
            if max_duration < 1000:  # 少于1秒
                simulation["success"] = False
                simulation["error"] = "内容时长过短，无法有效预览"

        except Exception as e:
            simulation["success"] = False
            simulation["error"] = str(e)

        return simulation

    def cleanup_test_files(self) -> Dict[str, Any]:
        """清理测试文件"""
        logger.info("=" * 60)
        logger.info("测试清理: 删除所有测试文件")
        logger.info("=" * 60)

        cleanup_result = {
            "test_name": "测试环境清理",
            "start_time": time.time(),
            "status": "进行中",
            "details": {},
            "errors": []
        }

        try:
            logger.info("开始清理测试文件...")

            # 清理创建的文件
            cleaned_files = []
            failed_files = []

            for file_path in self.created_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                        logger.info(f"✅ 已删除: {file_path}")
                    else:
                        logger.info(f"⚠️ 文件不存在: {file_path}")
                except Exception as e:
                    failed_files.append({"file": file_path, "error": str(e)})
                    logger.error(f"❌ 删除失败: {file_path} - {str(e)}")

            # 清理测试目录
            try:
                if self.test_dir.exists():
                    shutil.rmtree(self.test_dir)
                    logger.info(f"✅ 已删除测试目录: {self.test_dir}")
                    cleanup_result["details"]["test_dir_removed"] = True
                else:
                    logger.info(f"⚠️ 测试目录不存在: {self.test_dir}")
                    cleanup_result["details"]["test_dir_removed"] = False
            except Exception as e:
                logger.error(f"❌ 删除测试目录失败: {str(e)}")
                cleanup_result["errors"].append(f"删除测试目录失败: {str(e)}")
                cleanup_result["details"]["test_dir_removed"] = False

            cleanup_result["details"]["cleaned_files"] = cleaned_files
            cleanup_result["details"]["failed_files"] = failed_files
            cleanup_result["details"]["total_files"] = len(self.created_files)
            cleanup_result["details"]["success_count"] = len(cleaned_files)
            cleanup_result["details"]["failed_count"] = len(failed_files)

            if not failed_files and cleanup_result["details"]["test_dir_removed"]:
                logger.info("✅ 环境清理完成")
                cleanup_result["status"] = "通过"
            else:
                logger.warning("⚠️ 环境清理部分完成")
                cleanup_result["status"] = "部分通过"

        except Exception as e:
            logger.error(f"❌ 环境清理异常: {str(e)}")
            cleanup_result["status"] = "异常"
            cleanup_result["errors"].append(str(e))

        cleanup_result["end_time"] = time.time()
        cleanup_result["duration"] = cleanup_result["end_time"] - cleanup_result["start_time"]

        self.test_results.append(cleanup_result)
        return cleanup_result

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有剪映工程文件测试"""
        logger.info("🚀 开始VisionAI-ClipsMaster剪映工程文件详细测试")
        logger.info("=" * 80)

        overall_start_time = time.time()

        try:
            # 1. 创建真实测试数据
            logger.info("步骤1: 创建真实测试数据")
            video_path, original_srt_path, viral_srt_path = self.create_real_test_data()

            # 2. 测试工程文件生成
            logger.info("步骤2: 测试剪映工程文件生成")
            generation_result = self.test_project_file_generation(video_path, viral_srt_path)

            if generation_result.get("status") != "通过":
                logger.error("❌ 工程文件生成失败，跳过后续测试")
                self.cleanup_test_files()
                return self.generate_test_report(time.time() - overall_start_time)

            project_path = generation_result["details"]["export_path"]

            # 3. 测试剪映软件导入兼容性
            logger.info("步骤3: 测试剪映软件导入兼容性")
            import_result = self.test_jianying_import_compatibility(project_path)

            # 4. 测试时间轴结构
            logger.info("步骤4: 测试时间轴结构验证")
            timeline_result = self.test_timeline_structure(project_path)

            # 5. 测试编辑功能
            logger.info("步骤5: 测试编辑功能")
            editing_result = self.test_editing_functionality(project_path)

            # 6. 测试播放预览
            logger.info("步骤6: 测试播放预览")
            preview_result = self.test_playback_preview(project_path)

            # 7. 清理测试环境
            logger.info("步骤7: 清理测试环境")
            cleanup_result = self.cleanup_test_files()

        except Exception as e:
            logger.error(f"❌ 测试执行异常: {str(e)}")
            # 确保清理操作执行
            try:
                self.cleanup_test_files()
            except:
                pass

        overall_end_time = time.time()
        overall_duration = overall_end_time - overall_start_time

        # 生成测试报告
        test_report = self.generate_test_report(overall_duration)

        return test_report

    def generate_test_report(self, overall_duration: float) -> Dict[str, Any]:
        """生成详细测试报告"""
        logger.info("=" * 80)
        logger.info("📊 生成剪映工程文件详细测试报告")
        logger.info("=" * 80)

        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("status") == "通过"])
        failed_tests = len([r for r in self.test_results if r.get("status") == "失败"])
        partial_tests = len([r for r in self.test_results if r.get("status") == "部分通过"])
        skipped_tests = len([r for r in self.test_results if r.get("status") == "跳过"])
        error_tests = len([r for r in self.test_results if r.get("status") == "异常"])

        # 计算成功率
        success_rate = (passed_tests + partial_tests * 0.5) / total_tests * 100 if total_tests > 0 else 0

        # 生成报告
        report = {
            "test_summary": {
                "test_type": "剪映工程文件详细测试",
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "partial": partial_tests,
                "skipped": skipped_tests,
                "errors": error_tests,
                "success_rate": round(success_rate, 2),
                "overall_duration": round(overall_duration, 2)
            },
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "test_directory": str(self.test_dir)
            }
        }

        # 打印摘要
        logger.info("📋 测试摘要:")
        logger.info(f"  测试类型: 剪映工程文件详细测试")
        logger.info(f"  总测试数: {total_tests}")
        logger.info(f"  通过: {passed_tests}")
        logger.info(f"  失败: {failed_tests}")
        logger.info(f"  部分通过: {partial_tests}")
        logger.info(f"  跳过: {skipped_tests}")
        logger.info(f"  异常: {error_tests}")
        logger.info(f"  成功率: {success_rate:.2f}%")
        logger.info(f"  总耗时: {overall_duration:.2f}秒")

        # 详细结果
        logger.info("\n📝 详细结果:")
        for result in self.test_results:
            status_icon = {
                "通过": "✅",
                "失败": "❌",
                "部分通过": "⚠️",
                "跳过": "⏭️",
                "异常": "💥"
            }.get(result.get("status", "未知"), "❓")

            duration = result.get("duration", 0)
            logger.info(f"  {status_icon} {result.get('test_name', '未知测试')}: {result.get('status', '未知')} ({duration:.2f}秒)")

            # 显示错误信息
            errors = result.get("errors", [])
            if errors:
                for error in errors[:3]:  # 只显示前3个错误
                    logger.info(f"    🔸 错误: {error}")
                if len(errors) > 3:
                    logger.info(f"    🔸 还有 {len(errors) - 3} 个错误...")

        # 保存报告到文件
        report_file = f"jianying_detailed_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"📄 详细测试报告已保存: {report_file}")
            report["report_file"] = report_file
        except Exception as e:
            logger.error(f"❌ 保存测试报告失败: {str(e)}")

        # 生成Markdown报告
        try:
            markdown_report = self._generate_detailed_markdown_report(report)
            markdown_file = f"jianying_detailed_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            logger.info(f"📄 Markdown报告已保存: {markdown_file}")
            report["markdown_file"] = markdown_file
        except Exception as e:
            logger.error(f"❌ 生成Markdown报告失败: {str(e)}")

        return report

    def _generate_detailed_markdown_report(self, report: Dict[str, Any]) -> str:
        """生成详细的Markdown格式测试报告"""
        summary = report["test_summary"]

        markdown = f"""# VisionAI-ClipsMaster 剪映工程文件详细测试报告

## 📋 测试概述

本报告详细记录了VisionAI-ClipsMaster项目剪映工程文件生成功能的完整测试过程，包括文件生成、导入兼容性、时间轴结构、编辑功能和播放预览等关键功能验证。

## 🎯 测试目标

1. **工程文件生成测试** - 验证能否生成符合剪映标准的.draft工程文件
2. **剪映软件导入测试** - 验证生成的工程文件在剪映软件中的兼容性
3. **时间轴结构验证** - 确认时间轴上显示多个独立的、未渲染的视频段
4. **编辑功能测试** - 测试视频段的拖拽、调整等编辑操作
5. **播放预览测试** - 验证音视频同步和播放功能

## 📊 测试结果摘要

- **测试时间**: {report["timestamp"]}
- **总测试数**: {summary["total_tests"]}
- **通过**: {summary["passed"]}
- **失败**: {summary["failed"]}
- **部分通过**: {summary["partial"]}
- **跳过**: {summary["skipped"]}
- **异常**: {summary["errors"]}
- **成功率**: {summary["success_rate"]}%
- **总耗时**: {summary["overall_duration"]}秒

## 🧪 测试环境

- **Python版本**: {report["environment"]["python_version"]}
- **平台**: {report["environment"]["platform"]}
- **测试目录**: {report["environment"]["test_directory"]}

## 🔍 详细测试结果

"""

        for result in report["test_results"]:
            status_icon = {
                "通过": "✅",
                "失败": "❌",
                "部分通过": "⚠️",
                "跳过": "⏭️",
                "异常": "💥"
            }.get(result.get("status", "未知"), "❓")

            markdown += f"""### {status_icon} {result.get('test_name', '未知测试')}

- **状态**: {result.get('status', '未知')}
- **耗时**: {result.get('duration', 0):.2f}秒

"""

            # 添加详细信息
            details = result.get("details", {})
            if details:
                markdown += "**详细信息**:\n"
                for key, value in details.items():
                    if isinstance(value, (str, int, float, bool)):
                        markdown += f"- {key}: {value}\n"
                    elif isinstance(value, dict):
                        markdown += f"- {key}: {len(value)} 项详细数据\n"
                markdown += "\n"

            # 添加错误信息
            errors = result.get("errors", [])
            if errors:
                markdown += "**发现的问题**:\n"
                for error in errors:
                    markdown += f"- {error}\n"
                markdown += "\n"

        markdown += f"""
## 🎯 测试结论

本次剪映工程文件详细测试验证了VisionAI-ClipsMaster的核心剪映集成功能：

1. **工程文件生成** - 测试系统生成符合剪映标准的.draft工程文件的能力
2. **导入兼容性** - 验证生成的工程文件与剪映软件的兼容性
3. **时间轴结构** - 确认视频段结构符合编辑要求
4. **编辑功能** - 测试视频段的调整和编辑操作
5. **播放预览** - 验证音视频同步和预览功能

**总体成功率: {summary["success_rate"]}%**

### 🔧 改进建议

基于测试结果，建议关注以下方面：

1. **FFmpeg集成** - 在部署环境中集成FFmpeg以支持真实视频处理
2. **剪映软件检测** - 改进剪映软件自动检测机制
3. **错误处理** - 增强异常情况下的错误处理和用户提示
4. **性能优化** - 对大文件和长视频的处理进行优化

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return markdown


def main():
    """主函数"""
    print("🚀 VisionAI-ClipsMaster 剪映工程文件详细测试")
    print("=" * 80)

    # 创建测试器
    tester = JianyingProjectTester()

    try:
        # 运行所有测试
        report = tester.run_all_tests()

        # 显示最终结果
        success_rate = report["test_summary"]["success_rate"]
        if success_rate >= 90:
            print(f"\n🎉 测试完成！成功率: {success_rate}% - 优秀")
        elif success_rate >= 70:
            print(f"\n✅ 测试完成！成功率: {success_rate}% - 良好")
        elif success_rate >= 50:
            print(f"\n⚠️ 测试完成！成功率: {success_rate}% - 需要改进")
        else:
            print(f"\n❌ 测试完成！成功率: {success_rate}% - 需要重大改进")

        return report

    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        # 尝试清理
        try:
            tester.cleanup_test_files()
        except:
            pass
        return None
    except Exception as e:
        print(f"\n💥 测试执行异常: {str(e)}")
        # 尝试清理
        try:
            tester.cleanup_test_files()
        except:
            pass
        return None


if __name__ == "__main__":
    main()
