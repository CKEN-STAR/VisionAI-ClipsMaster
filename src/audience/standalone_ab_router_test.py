#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A/B测试路由器独立测试

这是一个完全独立的测试脚本，不依赖于项目的其他模块，可以直接运行。
此脚本包含了必要的模拟类和测试用例，验证A/B测试路由器的核心功能。
"""

import unittest
from unittest.mock import MagicMock
import json
import random
import numpy as np
from datetime import datetime, timedelta
import traceback

print("开始A/B测试路由器独立测试...")

class MockStorageManager:
    """模拟存储管理器"""
    
    def __init__(self):
        """初始化模拟存储管理器"""
        self.ab_tests = {}
        self.ab_assignments = {}
        self.ab_events = {}
    
    def save_ab_test(self, test_id, test_config):
        """保存A/B测试配置"""
        self.ab_tests[test_id] = test_config
        return True
    
    def get_ab_test(self, test_id):
        """获取A/B测试配置"""
        if test_id in self.ab_tests:
            return self.ab_tests[test_id]
        return None
    
    def save_ab_assignment(self, user_id, assignment):
        """保存用户分配结果"""
        if user_id not in self.ab_assignments:
            self.ab_assignments[user_id] = []
        self.ab_assignments[user_id].append(assignment)
        return True
    
    def save_ab_event(self, user_id, event):
        """保存用户事件"""
        if user_id not in self.ab_events:
            self.ab_events[user_id] = []
        self.ab_events[user_id].append(event)
        return True
    
    def get_ab_events(self, test_id):
        """获取测试事件"""
        events = []
        for user_events in self.ab_events.values():
            for event in user_events:
                if "test_id" in event and event["test_id"] == test_id:
                    events.append(event)
        return events

class MockProfileEngine:
    """模拟用户画像引擎"""
    
    def __init__(self):
        """初始化模拟用户画像引擎"""
        self.profiles = {}
    
    def get_profile(self, user_id):
        """获取用户画像"""
        if user_id in self.profiles:
            return self.profiles[user_id]
        
        # 为测试用户生成随机画像
        if user_id.startswith("test_"):
            profile = self._generate_test_profile()
            self.profiles[user_id] = profile
            return profile
        
        return None
    
    def _generate_test_profile(self):
        """生成测试用户画像"""
        return {
            "content_preferences": {
                "action": {"score": random.random()},
                "comedy": {"score": random.random()},
                "drama": {"score": random.random()}
            },
            "emotion_response": {
                "excitement": {"score": random.random()},
                "empathy": {"score": random.random()},
                "amusement": {"score": random.random()}
            },
            "editing_preferences": {
                "fast_cuts": {"score": random.random()},
                "transitions": {"score": random.random()},
                "effects": {"score": random.random()}
            }
        }

# 定义日志处理模块
def get_logger(name):
    """模拟日志处理器"""
    class MockLogger:
        def info(self, msg):
            print(f"INFO [{name}]: {msg}")
        
        def debug(self, msg):
            pass
        
        def warning(self, msg):
            print(f"WARNING [{name}]: {msg}")
        
        def error(self, msg):
            print(f"ERROR [{name}]: {msg}")
    
    return MockLogger()

class ABRouter:
    """A/B测试路由器
    
    基于用户画像特征，为用户分配最优的内容或功能变体，
    同时记录测试数据用于效果分析与优化。
    """
    
    def __init__(self):
        """初始化A/B测试路由器"""
        # 获取存储管理器
        self.storage = MockStorageManager()
        
        # 获取用户画像引擎
        self.profile_engine = MockProfileEngine()
        
        # 测试配置缓存
        self.test_configs = {}
        
        # 用户分配缓存
        self.user_assignments = {}
        
        # 特征向量缓存
        self.feature_vectors = {}
        
        # 默认分配策略
        self.default_assignment_strategy = "random"  # random, deterministic, weighted
        
        # 路由决策缓存有效期（秒）
        self.cache_ttl = 3600  # 1小时
        
        # 测量指标
        self.metrics = [
            "completion_rate",      # 完成率
            "engagement_time",      # 参与时间
            "interaction_count",    # 互动次数
            "share_rate",           # 分享率
            "retention_impact",     # 留存影响
            "conversion_rate"       # 转化率
        ]
        
        # 创建日志记录器
        self.logger = get_logger("ab_router")
        
        self.logger.info("A/B测试路由器初始化完成")
    
    def route_version(self, user_id, variants):
        """基于用户特征分配最优版本
        
        Args:
            user_id: 用户ID
            variants: 可选变体列表，每个变体应包含feature_vector

        Returns:
            Dict[str, Any]: 分配的最优变体
        """
        if not variants:
            self.logger.warning(f"用户 {user_id} 的变体列表为空")
            return {}
        
        # 检查缓存中是否有有效的分配结果
        cached_result = self._check_cache(user_id, variants)
        if cached_result:
            self.logger.debug(f"用户 {user_id} 使用缓存分配结果")
            return cached_result

        # 编码用户特征向量
        user_vector = self._encode_user(user_id)
        
        # 计算用户向量与各变体特征向量的相似度
        scores = [self._calculate_similarity(user_vector, v["feature_vector"]) for v in variants]
        
        # 选择最佳匹配的变体
        best_variant_index = np.argmax(scores)
        best_variant = variants[best_variant_index]
        
        # 记录分配结果
        self._record_assignment(user_id, best_variant, scores)
        
        # 缓存分配结果
        self._cache_assignment(user_id, best_variant)
        
        self.logger.info(f"用户 {user_id} 被分配到变体 {best_variant.get('id', 'unknown')}")
        return best_variant
    
    def _encode_user(self, user_id):
        """将用户特征编码为向量"""
        # 检查缓存
        if user_id in self.feature_vectors:
            return self.feature_vectors[user_id]['vector']
        
        # 获取用户画像
        user_profile = self.profile_engine.get_profile(user_id)
        if not user_profile:
            # 如果没有用户画像，返回默认向量
            self.logger.warning(f"用户 {user_id} 没有画像数据，使用默认向量")
            default_vector = np.zeros(64)  # 默认维度为64
            
            # 缓存默认向量
            self.feature_vectors[user_id] = {
                'vector': default_vector,
                'timestamp': datetime.now().timestamp()
            }
            
            return default_vector
        
        # 提取关键特征
        feature_dict = {
            # 内容偏好特征
            'content_preferences': self._normalize_preferences(user_profile.get('content_preferences', {})),
            
            # 情感响应特征
            'emotion_response': self._normalize_preferences(user_profile.get('emotion_response', {})),
            
            # 编辑风格偏好
            'editing_preferences': self._normalize_preferences(user_profile.get('editing_preferences', {}))
        }
        
        # 将特征字典转换为向量
        feature_vector = self._dict_to_vector(feature_dict)
        
        # 缓存用户向量
        self.feature_vectors[user_id] = {
            'vector': feature_vector,
            'timestamp': datetime.now().timestamp()
        }
        
        return feature_vector
    
    def _normalize_preferences(self, preferences):
        """规范化偏好数据"""
        result = {}
        
        # 提取偏好分数
        if isinstance(preferences, dict):
            for key, value in preferences.items():
                if isinstance(value, dict) and 'score' in value:
                    result[key] = float(value['score'])
                elif isinstance(value, (int, float)):
                    result[key] = float(value)
        
        # 如果偏好为空，返回空字典
        if not result:
            return {}
        
        # 规范化分数总和为1
        total = sum(result.values())
        if total > 0:
            for key in result:
                result[key] = result[key] / total
        
        return result
    
    def _dict_to_vector(self, feature_dict):
        """将特征字典转换为向量"""
        # 拼接所有特征值
        all_values = []
        
        # 处理每个特征类别
        for category, prefs in feature_dict.items():
            values = list(prefs.values())
            if values:
                all_values.extend(values)
            else:
                # 如果该类别没有值，添加一个默认值0
                all_values.append(0)
        
        # 转换为numpy数组
        return np.array(all_values)
    
    def _calculate_similarity(self, user_vector, variant_vector):
        """计算用户向量与变体向量的相似度"""
        # 如果向量长度不同，调整为相同长度
        variant_vector_np = np.array(variant_vector)
        
        if len(user_vector) != len(variant_vector_np):
            min_len = min(len(user_vector), len(variant_vector_np))
            user_vector = user_vector[:min_len]
            variant_vector_np = variant_vector_np[:min_len]
        
        # 检查向量是否为零向量
        if np.all(user_vector == 0) or np.all(variant_vector_np == 0):
            return 0.0
        
        # 计算余弦相似度
        try:
            # 确保向量非零
            user_norm = np.linalg.norm(user_vector)
            variant_norm = np.linalg.norm(variant_vector_np)
            
            if user_norm > 0 and variant_norm > 0:
                similarity = np.dot(user_vector, variant_vector_np) / (user_norm * variant_norm)
                return float(similarity)
            else:
                return 0.0
        except Exception as e:
            self.logger.error(f"计算相似度时出错: {str(e)}")
            return 0.0
    
    def _check_cache(self, user_id, variants):
        """检查缓存中是否有有效的分配结果"""
        # 检查用户是否在缓存中
        if user_id not in self.user_assignments:
            return None
        
        cached_assignment = self.user_assignments[user_id]
        
        # 检查缓存的变体是否在当前变体列表中
        variant_id = cached_assignment.get('variant_id')
        for v in variants:
            if v.get('id') == variant_id:
                return v
        
        return None
    
    def _cache_assignment(self, user_id, variant):
        """缓存用户的分配结果"""
        self.user_assignments[user_id] = {
            'variant_id': variant.get('id'),
            'timestamp': datetime.now().timestamp()
        }
    
    def _record_assignment(self, user_id, variant, scores):
        """记录用户分配结果"""
        try:
            assignment_record = {
                'user_id': user_id,
                'variant_id': variant.get('id'),
                'test_id': variant.get('test_id'),
                'timestamp': datetime.now().isoformat(),
                'scores': scores
            }
            
            # 存储分配记录
            self.storage.save_ab_assignment(user_id, assignment_record)
            
        except Exception as e:
            self.logger.error(f"记录用户 {user_id} 的分配结果时出错: {str(e)}")
    
    def create_test(self, test_id, variants, config=None):
        """创建新的A/B测试"""
        if not config:
            config = {}
        
        # 创建测试配置
        test_config = {
            'id': test_id,
            'variants': variants,
            'start_time': config.get('start_time', datetime.now().isoformat()),
            'end_time': config.get('end_time', None),
            'metrics': config.get('metrics', self.metrics),
            'assignment_strategy': config.get('assignment_strategy', self.default_assignment_strategy),
            'status': 'active',
            'created_at': datetime.now().isoformat()
        }
        
        # 缓存测试配置
        self.test_configs[test_id] = test_config
        
        # 存储测试配置
        try:
            self.storage.save_ab_test(test_id, test_config)
            self.logger.info(f"创建A/B测试 {test_id}")
        except Exception as e:
            self.logger.error(f"存储A/B测试 {test_id} 配置时出错: {str(e)}")
        
        return test_config
    
    def get_test(self, test_id):
        """获取测试配置"""
        # 检查缓存
        if test_id in self.test_configs:
            return self.test_configs[test_id]
        
        # 从存储中获取
        try:
            test_config = self.storage.get_ab_test(test_id)
            if test_config:
                # 更新缓存
                self.test_configs[test_id] = test_config
                return test_config
        except Exception as e:
            self.logger.error(f"获取A/B测试 {test_id} 配置时出错: {str(e)}")
        
        return {}


class TestABRouter(unittest.TestCase):
    """A/B测试路由器测试类"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建被测对象
        self.ab_router = ABRouter()
        
        # 测试用户ID
        self.test_user_id = "test_user_456"
        
        # 测试变体列表
        self.test_variants = [
            {
                "id": "variant_1",
                "name": "原始版本",
                "description": "当前使用的混剪版本",
                "feature_vector": [0.8, 0.2, 0.4, 0.6, 0.1]
            },
            {
                "id": "variant_2",
                "name": "情感强化版",
                "description": "增强情感变化的混剪版本",
                "feature_vector": [0.3, 0.9, 0.5, 0.2, 0.7]
            },
            {
                "id": "variant_3",
                "name": "节奏优化版",
                "description": "优化节奏变化的混剪版本",
                "feature_vector": [0.5, 0.4, 0.9, 0.3, 0.6]
            }
        ]
    
    def test_router_initialization(self):
        """测试路由器初始化"""
        self.assertIsNotNone(self.ab_router)
        self.assertEqual(self.ab_router.default_assignment_strategy, "random")
        self.assertEqual(len(self.ab_router.metrics), 6)  # 应该有6个默认指标
        print("✓ 路由器初始化测试通过")
    
    def test_route_version(self):
        """测试版本路由"""
        # 为测试用户模拟画像
        profile = {
            "content_preferences": {
                "action": {"score": 0.3},
                "drama": {"score": 0.9},
                "comedy": {"score": 0.4}
            },
            "emotion_response": {
                "excitement": {"score": 0.2},
                "empathy": {"score": 0.8},
                "amusement": {"score": 0.5}
            },
            "editing_preferences": {
                "fast_cuts": {"score": 0.3},
                "transitions": {"score": 0.8},
                "effects": {"score": 0.4}
            }
        }
        self.ab_router.profile_engine.profiles[self.test_user_id] = profile
        
        # 调用被测方法
        result = self.ab_router.route_version(self.test_user_id, self.test_variants)
        
        # 验证结果非空
        self.assertIsNotNone(result)
        self.assertIn("id", result)
        self.assertIn("name", result)
        
        print(f"✓ 版本路由测试通过，用户被分配到: {result['name']}")
    
    def test_create_test(self):
        """测试创建A/B测试"""
        # 准备测试数据
        test_id = "test_123"
        config = {"assignment_strategy": "weighted"}
        
        # 调用被测方法
        result = self.ab_router.create_test(test_id, self.test_variants, config)
        
        # 验证结果
        self.assertEqual(result["id"], test_id)
        self.assertEqual(result["variants"], self.test_variants)
        self.assertEqual(result["assignment_strategy"], "weighted")
        self.assertEqual(result["status"], "active")
        
        print("✓ 创建A/B测试测试通过")
    
    def test_get_test(self):
        """测试获取A/B测试配置"""
        # 准备测试数据
        test_id = "test_123"
        test_config = {
            "id": test_id, 
            "status": "active", 
            "variants": self.test_variants
        }
        
        # 预先存储测试配置
        self.ab_router.storage.save_ab_test(test_id, test_config)
        
        # 调用被测方法
        result = self.ab_router.get_test(test_id)
        
        # 验证结果
        self.assertEqual(result["id"], test_id)
        self.assertEqual(result["status"], "active")
        
        print("✓ 获取A/B测试配置测试通过")
    
    def test_normalize_preferences(self):
        """测试偏好规范化"""
        # 准备测试数据
        test_prefs = {
            "feature1": {"score": 2.0},
            "feature2": {"score": 3.0},
            "feature3": {"score": 5.0}
        }
        
        # 调用被测方法
        normalized = self.ab_router._normalize_preferences(test_prefs)
        
        # 验证结果
        self.assertEqual(sum(normalized.values()), 1.0)  # 总和应为1
        self.assertEqual(normalized["feature1"], 0.2)  # 2.0 / 10.0
        self.assertEqual(normalized["feature2"], 0.3)  # 3.0 / 10.0
        self.assertEqual(normalized["feature3"], 0.5)  # 5.0 / 10.0
        
        print("✓ 偏好规范化测试通过")
    
    def test_calculate_similarity(self):
        """测试相似度计算"""
        # 准备测试数据
        user_vector = np.array([0.5, 0.3, 0.9, 0.1])
        variant_vector = [0.6, 0.2, 0.8, 0.2]
        
        # 调用被测方法
        similarity = self.ab_router._calculate_similarity(user_vector, variant_vector)
        
        # 验证结果
        self.assertGreaterEqual(similarity, 0.0)
        self.assertLessEqual(similarity, 1.0)
        
        print(f"✓ 相似度计算测试通过，相似度: {similarity:.4f}")

if __name__ == "__main__":
    try:
        unittest.main()
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc() 