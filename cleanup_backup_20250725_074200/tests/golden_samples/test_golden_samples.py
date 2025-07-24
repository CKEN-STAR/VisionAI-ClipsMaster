#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
黄金样本测试套件

测试黄金样本生成和对比功能的完整性和正确性。
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
import hashlib
from pathlib import Path

# 获取项目根目录并添加到系统路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

# 导入要测试的模块
from tests.golden_samples.generate_samples import (
    create_golden_sample,
    calculate_video_hash,
    calculate_xml_hash,
    generate_xml_config,
    generate_srt_subtitle,
    get_scene_types,
    update_golden_samples_index
)

from src.utils.log_handler import get_logger

# 设置日志记录器
logger = get_logger("test_golden_samples")

class TestGoldenSamples(unittest.TestCase):
    """黄金样本功能测试类"""
    
    def setUp(self):
        """测试前准备工作"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp(prefix="visionai_golden_test_")
        
        # 保存原始目录环境
        self.original_dirs = {}
        for dirname in ["output", "hashes", "reports"]:
            dir_path = os.path.join(PROJECT_ROOT, "tests", "golden_samples", dirname)
            if os.path.exists(dir_path):
                self.original_dirs[dirname] = dir_path
                shutil.move(dir_path, os.path.join(self.test_dir, dirname))
        
        # 创建测试目录结构
        for dirname in ["output", "hashes", "reports"]:
            os.makedirs(os.path.join(PROJECT_ROOT, "tests", "golden_samples", dirname), exist_ok=True)
    
    def tearDown(self):
        """测试后清理工作"""
        # 删除测试过程中创建的目录
        for dirname in ["output", "hashes", "reports"]:
            dir_path = os.path.join(PROJECT_ROOT, "tests", "golden_samples", dirname)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
        
        # 恢复原始目录
        for dirname, dir_path in self.original_dirs.items():
            shutil.move(os.path.join(self.test_dir, dirname), dir_path)
        
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_scene_types(self):
        """测试场景类型定义"""
        scene_types = get_scene_types()
        
        # 确保返回的是列表
        self.assertIsInstance(scene_types, list)
        
        # 确保至少包含10种类型
        self.assertGreaterEqual(len(scene_types), 10)
        
        # 确保包含必要的场景类型
        required_types = ["comedy", "action", "drama"]
        for scene_type in required_types:
            self.assertIn(scene_type, scene_types)
    
    def test_xml_generation(self):
        """测试XML配置文件生成"""
        # 测试目录
        output_dir = os.path.join(self.test_dir, "xml_test")
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成测试XML
        test_scenes = ["comedy", "action"]
        for scene in test_scenes:
            output_file = os.path.join(output_dir, f"{scene}.xml")
            generate_xml_config(scene, output_file)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(output_file))
            
            # 验证文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn(f"<type>{scene}</type>", content)
                self.assertIn("Golden Sample", content)
    
    def test_srt_generation(self):
        """测试SRT字幕文件生成"""
        # 测试目录
        output_dir = os.path.join(self.test_dir, "srt_test")
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成测试SRT
        test_scenes = ["comedy", "action", "unknown_type"]
        for scene in test_scenes:
            output_file = os.path.join(output_dir, f"{scene}.srt")
            generate_srt_subtitle(scene, output_file)
            
            # 验证文件存在
            self.assertTrue(os.path.exists(output_file))
            
            # 验证文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 至少包含3个字幕条目
                self.assertGreaterEqual(content.count("-->"), 3)
                # 包含场景类型或默认提示
                if scene in ["comedy", "action"]:
                    self.assertIn(scene, content.lower())
                else:
                    self.assertIn("黄金样本测试案例", content)
    
    def test_hash_calculation(self):
        """测试哈希值计算"""
        # 创建测试文件
        test_file = os.path.join(self.test_dir, "test_file.bin")
        test_content = b"This is a test file for hash calculation"
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # 计算预期哈希值
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # 测试视频哈希计算
        video_hash = calculate_video_hash(test_file)
        self.assertEqual(video_hash, expected_hash)
        
        # 测试XML哈希计算
        xml_hash = calculate_xml_hash(test_file)
        self.assertEqual(xml_hash, expected_hash)
        
        # 测试不存在文件的情况
        non_existent_file = os.path.join(self.test_dir, "non_existent.file")
        self.assertEqual(calculate_video_hash(non_existent_file), "FILE_NOT_FOUND")
    
    def test_golden_sample_creation(self):
        """测试黄金样本创建流程"""
        # 创建一个测试版本的样本
        test_version = "test_1.0.0"
        
        # 生成黄金样本
        golden_hash = create_golden_sample(test_version)
        
        # 验证结果
        self.assertIsInstance(golden_hash, dict)
        self.assertIn("video", golden_hash)
        self.assertIn("xml", golden_hash)
        
        # 验证输出目录
        output_dir = os.path.join(PROJECT_ROOT, "tests", "golden_samples", "output", test_version)
        self.assertTrue(os.path.exists(output_dir))
        
        # 验证文件生成
        files_count = 0
        for file in os.listdir(output_dir):
            if file.endswith(".mp4"):
                files_count += 1
                # 验证对应的XML和SRT文件
                self.assertTrue(os.path.exists(os.path.join(output_dir, file + ".xml")))
                self.assertTrue(os.path.exists(os.path.join(output_dir, file.replace(".mp4", ".srt"))))
        
        # 验证生成了所有场景类型的样本
        self.assertEqual(files_count, len(get_scene_types()) + 1)  # +1 是因为主输出文件
        
        # 验证哈希文件
        hash_file = os.path.join(PROJECT_ROOT, "tests", "golden_samples", "hashes", f"golden_hash_{test_version}.json")
        self.assertTrue(os.path.exists(hash_file))
        
        # 验证哈希文件内容
        with open(hash_file, 'r', encoding='utf-8') as f:
            hash_data = json.load(f)
            self.assertEqual(hash_data, golden_hash)
    
    def test_index_update(self):
        """测试索引文件更新"""
        # 先创建样本
        test_version = "index_test_1.0.0"
        create_golden_sample(test_version)
        
        # 更新索引
        update_golden_samples_index()
        
        # 验证索引文件
        index_file = os.path.join(PROJECT_ROOT, "tests", "golden_samples", "index.json")
        self.assertTrue(os.path.exists(index_file))
        
        # 验证索引内容
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
            
            # 验证基本结构
            self.assertIn("versions", index_data)
            self.assertIn("samples", index_data)
            self.assertIn("last_updated", index_data)
            
            # 验证版本信息
            self.assertIn(test_version, index_data["versions"])
            
            # 验证样本信息
            samples = index_data["versions"][test_version]["samples"]
            self.assertGreaterEqual(len(samples), len(get_scene_types()))
            
            # 验证每个样本的详细信息
            for sample_id in samples:
                self.assertIn(sample_id, index_data["samples"])
                sample_info = index_data["samples"][sample_id]
                self.assertIn("files", sample_info)
                self.assertIn("type", sample_info)

def run_tests():
    """运行所有测试"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestGoldenSamples))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)

if __name__ == "__main__":
    # 运行所有测试
    run_tests() 