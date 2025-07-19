#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VisionAI-ClipsMaster 安全与合规测试

测试范围:
1. 版权水印检测功能
2. 用户协议绑定验证
3. 数据安全策略测试
4. 敏感信息保护
5. 文件完整性校验
6. 访问权限控制
"""

import pytest
import os
import tempfile
import hashlib
import json
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.utils.file_checker import FileChecker
from src.utils.security_policy import SecurityPolicy
from src.core.watermark_detector import WatermarkDetector


class TestSecurityCompliance:
    """安全与合规测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.file_checker = FileChecker()
        self.security_policy = SecurityPolicy()
        self.watermark_detector = WatermarkDetector()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        
        # 测试文件
        self.test_files = {
            "clean_video": os.path.join(self.temp_dir, "clean_video.mp4"),
            "watermarked_video": os.path.join(self.temp_dir, "watermarked_video.mp4"),
            "config_file": os.path.join(self.temp_dir, "config.json"),
            "user_data": os.path.join(self.temp_dir, "user_data.json")
        }
        
        # 创建测试文件
        self._create_test_files()

    def _create_test_files(self):
        """创建测试文件"""
        # 创建模拟视频文件
        with open(self.test_files["clean_video"], 'wb') as f:
            f.write(b"FAKE_VIDEO_DATA_WITHOUT_WATERMARK" + b"\x00" * 1000)
        
        with open(self.test_files["watermarked_video"], 'wb') as f:
            f.write(b"FAKE_VIDEO_DATA_WITH_WATERMARK_SIGNATURE" + b"\x00" * 1000)
        
        # 创建配置文件
        config_data = {
            "app_version": "1.0.0",
            "user_settings": {
                "language": "zh",
                "theme": "dark"
            },
            "security": {
                "encryption_enabled": True,
                "audit_logging": True
            }
        }
        with open(self.test_files["config_file"], 'w', encoding='utf-8') as f:
            json.dump(config_data, f)
        
        # 创建用户数据文件
        user_data = {
            "user_id": "test_user_001",
            "projects": ["project1", "project2"],
            "preferences": {
                "auto_save": True,
                "backup_enabled": True
            }
        }
        with open(self.test_files["user_data"], 'w', encoding='utf-8') as f:
            json.dump(user_data, f)

    def test_watermark_detection_functionality(self):
        """测试版权水印检测功能"""
        # 测试无水印视频
        clean_result = self.watermark_detector.detect_watermark(
            self.test_files["clean_video"]
        )
        assert clean_result["has_watermark"] == False, "无水印视频检测错误"
        assert clean_result["confidence"] < 0.3, f"无水印视频置信度过高: {clean_result['confidence']}"
        
        # 测试有水印视频
        watermarked_result = self.watermark_detector.detect_watermark(
            self.test_files["watermarked_video"]
        )
        assert watermarked_result["has_watermark"] == True, "有水印视频检测错误"
        assert watermarked_result["confidence"] > 0.7, f"有水印视频置信度过低: {watermarked_result['confidence']}"
        
        # 验证检测详情
        if watermarked_result["has_watermark"]:
            assert "watermark_type" in watermarked_result, "缺少水印类型信息"
            assert "detected_regions" in watermarked_result, "缺少检测区域信息"

    def test_common_watermark_patterns(self):
        """测试常见水印模式检测"""
        common_watermarks = [
            "抖音",
            "TikTok", 
            "快手",
            "Kuaishou",
            "微博",
            "Weibo",
            "B站",
            "Bilibili",
            "YouTube",
            "爱奇艺",
            "腾讯视频"
        ]
        
        for watermark in common_watermarks:
            # 创建包含特定水印的测试文件
            watermark_file = os.path.join(self.temp_dir, f"test_{watermark}.mp4")
            with open(watermark_file, 'wb') as f:
                # 模拟包含水印文本的视频数据
                f.write(f"VIDEO_DATA_WITH_{watermark}_WATERMARK".encode('utf-8') + b"\x00" * 1000)
            
            # 检测水印
            result = self.watermark_detector.detect_watermark(watermark_file)
            
            # 验证检测结果
            assert "has_watermark" in result, f"{watermark}水印检测结果格式错误"
            assert "confidence" in result, f"{watermark}水印检测缺少置信度"
            
            # 清理测试文件
            os.remove(watermark_file)

    def test_user_agreement_binding(self):
        """测试用户协议绑定验证"""
        # 测试协议接受状态
        agreement_status = self.security_policy.check_user_agreement_status("test_user_001")
        
        # 如果用户未接受协议
        if not agreement_status["accepted"]:
            # 模拟协议接受过程
            agreement_content = self.security_policy.get_user_agreement_content()
            assert len(agreement_content) > 0, "用户协议内容为空"
            
            # 验证协议内容包含关键条款
            required_clauses = [
                "版权声明",
                "使用限制", 
                "免责条款",
                "数据保护",
                "法律责任"
            ]
            
            for clause in required_clauses:
                assert clause in agreement_content, f"用户协议缺少{clause}条款"
            
            # 模拟用户接受协议
            accept_result = self.security_policy.accept_user_agreement(
                user_id="test_user_001",
                agreement_version="1.0",
                timestamp=1234567890
            )
            assert accept_result["success"], "用户协议接受失败"
        
        # 验证协议绑定状态
        updated_status = self.security_policy.check_user_agreement_status("test_user_001")
        assert updated_status["accepted"], "用户协议绑定验证失败"

    def test_data_security_policy_enforcement(self):
        """测试数据安全策略执行"""
        # 测试敏感数据加密
        sensitive_data = {
            "user_credentials": "test_password_123",
            "api_keys": "sk-test-key-12345",
            "personal_info": {
                "name": "测试用户",
                "email": "test@example.com"
            }
        }
        
        # 加密敏感数据
        encrypted_data = self.security_policy.encrypt_sensitive_data(sensitive_data)
        assert encrypted_data != sensitive_data, "敏感数据未加密"
        assert "encrypted" in encrypted_data, "加密数据格式错误"
        
        # 解密验证
        decrypted_data = self.security_policy.decrypt_sensitive_data(encrypted_data)
        assert decrypted_data == sensitive_data, "数据解密失败"

    def test_file_integrity_verification(self):
        """测试文件完整性校验"""
        # 计算文件哈希
        original_hash = self.file_checker.calculate_file_hash(
            self.test_files["config_file"]
        )
        assert len(original_hash) > 0, "文件哈希计算失败"
        
        # 验证文件完整性
        integrity_check = self.file_checker.verify_file_integrity(
            self.test_files["config_file"],
            expected_hash=original_hash
        )
        assert integrity_check["valid"], "文件完整性验证失败"
        
        # 模拟文件篡改
        with open(self.test_files["config_file"], 'a', encoding='utf-8') as f:
            f.write("\n// TAMPERED")
        
        # 验证篡改检测
        tampered_check = self.file_checker.verify_file_integrity(
            self.test_files["config_file"],
            expected_hash=original_hash
        )
        assert not tampered_check["valid"], "文件篡改检测失败"

    def test_access_permission_control(self):
        """测试访问权限控制"""
        # 定义权限级别
        permission_levels = ["read", "write", "admin"]
        
        for level in permission_levels:
            # 测试权限检查
            has_permission = self.security_policy.check_user_permission(
                user_id="test_user_001",
                resource="project_files",
                permission=level
            )
            
            # 验证权限检查结果
            assert isinstance(has_permission, bool), f"{level}权限检查结果类型错误"
        
        # 测试权限升级
        upgrade_result = self.security_policy.request_permission_upgrade(
            user_id="test_user_001",
            requested_permission="admin",
            justification="测试需要"
        )
        
        assert "status" in upgrade_result, "权限升级结果格式错误"
        assert upgrade_result["status"] in ["approved", "denied", "pending"], \
            f"权限升级状态无效: {upgrade_result['status']}"

    def test_audit_logging_functionality(self):
        """测试审计日志功能"""
        # 记录安全事件
        security_events = [
            {
                "event_type": "file_access",
                "user_id": "test_user_001",
                "resource": "sensitive_config.json",
                "action": "read",
                "timestamp": 1234567890
            },
            {
                "event_type": "permission_change",
                "user_id": "admin_user",
                "target_user": "test_user_001", 
                "old_permission": "read",
                "new_permission": "write",
                "timestamp": 1234567891
            },
            {
                "event_type": "watermark_detection",
                "file_path": "test_video.mp4",
                "detection_result": "watermark_found",
                "confidence": 0.85,
                "timestamp": 1234567892
            }
        ]
        
        for event in security_events:
            # 记录审计日志
            log_result = self.security_policy.log_security_event(event)
            assert log_result["success"], f"安全事件日志记录失败: {event['event_type']}"
        
        # 查询审计日志
        audit_logs = self.security_policy.query_audit_logs(
            start_time=1234567890,
            end_time=1234567900,
            event_types=["file_access", "permission_change", "watermark_detection"]
        )
        
        assert len(audit_logs) >= len(security_events), "审计日志查询结果不完整"

    def test_sensitive_information_protection(self):
        """测试敏感信息保护"""
        # 定义敏感信息模式
        sensitive_patterns = [
            r"\d{4}-\d{4}-\d{4}-\d{4}",  # 信用卡号
            r"\d{3}-\d{2}-\d{4}",        # 社会保险号
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # 邮箱
            r"\d{11}",                   # 手机号
            r"sk-[a-zA-Z0-9]{32,}",      # API密钥
        ]
        
        # 测试文本内容
        test_content = """
        用户信息：
        邮箱：user@example.com
        手机：13812345678
        API密钥：sk-test1234567890abcdef1234567890abcdef
        信用卡：1234-5678-9012-3456
        """
        
        # 检测敏感信息
        detection_result = self.security_policy.detect_sensitive_information(test_content)
        
        assert len(detection_result["found_patterns"]) > 0, "敏感信息检测失败"
        
        # 验证检测到的模式类型
        detected_types = [item["type"] for item in detection_result["found_patterns"]]
        expected_types = ["email", "phone", "api_key", "credit_card"]
        
        for expected_type in expected_types:
            assert expected_type in detected_types, f"未检测到{expected_type}类型的敏感信息"
        
        # 测试敏感信息脱敏
        sanitized_content = self.security_policy.sanitize_sensitive_information(test_content)
        
        # 验证脱敏效果
        for pattern in sensitive_patterns:
            import re
            matches = re.findall(pattern, sanitized_content)
            assert len(matches) == 0, f"敏感信息脱敏不完整: {pattern}"

    def test_copyright_compliance_workflow(self):
        """测试版权合规工作流程"""
        # 模拟视频上传流程
        video_file = self.test_files["watermarked_video"]
        
        # 第一步：水印检测
        watermark_result = self.watermark_detector.detect_watermark(video_file)
        
        if watermark_result["has_watermark"]:
            # 第二步：版权风险评估
            risk_assessment = self.security_policy.assess_copyright_risk(
                file_path=video_file,
                watermark_info=watermark_result
            )
            
            assert "risk_level" in risk_assessment, "缺少风险等级评估"
            assert risk_assessment["risk_level"] in ["low", "medium", "high"], \
                f"风险等级无效: {risk_assessment['risk_level']}"
            
            # 第三步：合规建议
            compliance_advice = self.security_policy.get_compliance_advice(risk_assessment)
            
            assert "recommendations" in compliance_advice, "缺少合规建议"
            assert len(compliance_advice["recommendations"]) > 0, "合规建议为空"
            
            # 第四步：用户确认
            user_confirmation = self.security_policy.request_user_confirmation(
                risk_info=risk_assessment,
                advice=compliance_advice
            )
            
            assert "confirmation_required" in user_confirmation, "缺少用户确认要求"

    def test_data_privacy_protection(self):
        """测试数据隐私保护"""
        # 测试个人数据处理
        personal_data = {
            "user_id": "test_user_001",
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "13812345678",
            "usage_history": [
                {"action": "video_upload", "timestamp": 1234567890},
                {"action": "model_training", "timestamp": 1234567891}
            ]
        }
        
        # 数据最小化处理
        minimized_data = self.security_policy.minimize_personal_data(
            personal_data,
            purpose="model_training"
        )
        
        # 验证数据最小化
        assert "email" not in minimized_data, "邮箱信息未被最小化"
        assert "phone" not in minimized_data, "电话信息未被最小化"
        assert "user_id" in minimized_data, "必要的用户ID被错误移除"
        
        # 测试数据匿名化
        anonymized_data = self.security_policy.anonymize_user_data(personal_data)
        
        assert anonymized_data["user_id"] != personal_data["user_id"], "用户ID未匿名化"
        assert "name" not in anonymized_data or anonymized_data["name"] != personal_data["name"], \
            "姓名未匿名化"

    def test_security_incident_response(self):
        """测试安全事件响应"""
        # 模拟安全事件
        security_incidents = [
            {
                "type": "unauthorized_access",
                "severity": "high",
                "description": "检测到未授权访问尝试",
                "affected_resources": ["user_data.json"],
                "timestamp": 1234567890
            },
            {
                "type": "data_breach",
                "severity": "critical", 
                "description": "敏感数据可能泄露",
                "affected_users": ["test_user_001", "test_user_002"],
                "timestamp": 1234567891
            },
            {
                "type": "malware_detection",
                "severity": "medium",
                "description": "检测到可疑文件",
                "file_path": "suspicious_file.exe",
                "timestamp": 1234567892
            }
        ]
        
        for incident in security_incidents:
            # 触发安全事件响应
            response_result = self.security_policy.handle_security_incident(incident)
            
            # 验证响应结果
            assert "response_actions" in response_result, f"安全事件{incident['type']}缺少响应动作"
            assert "notification_sent" in response_result, f"安全事件{incident['type']}缺少通知状态"
            
            # 验证响应动作的合理性
            actions = response_result["response_actions"]
            if incident["severity"] == "critical":
                assert "immediate_lockdown" in actions, "严重安全事件未触发立即锁定"
            elif incident["severity"] == "high":
                assert "enhanced_monitoring" in actions, "高危安全事件未启用增强监控"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
