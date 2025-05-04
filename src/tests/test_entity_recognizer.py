"""
VisionAI-ClipsMaster 多语言实体识别引擎单元测试

此模块包含对多语言实体识别功能的测试，包括：
- 正则表达式备用识别
- 实体类型映射
- 特定实体类型提取
- 语言自动检测
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 创建模拟的spacy依赖
sys.modules['spacy'] = MagicMock()
sys.modules['spacy.language'] = MagicMock()
sys.modules['spacy.tokens'] = MagicMock()

# 从被测试模块导入需要的函数和类
from nlp.entity_recognizer import (
    PolyglotNER,
    FALLBACK_PATTERNS,
    ENTITY_TYPE_MAPPING,
    extract_entities,
    get_global_ner
)


class TestFallbackRecognition(unittest.TestCase):
    """测试正则表达式备用识别功能"""
    
    def setUp(self):
        # 创建一个不加载模型的实例，强制使用备用识别
        self.ner = PolyglotNER(load_models=False)
        # 确保使用备用方法
        self.ner._fallback_recognition = self.ner._fallback_recognition
    
    def test_zh_person_recognition(self):
        """测试中文人名识别"""
        text = "张三先生是公司的技术总监，李四博士负责研发。"
        entities = self.ner._fallback_recognition(text, "zh")
        self.assertIn("PERSON", entities)
        self.assertIn("张三先生", entities["PERSON"])
        self.assertIn("李四博士", entities["PERSON"])
    
    def test_zh_location_detection(self):
        """测试中文地点检测"""
        # 使用更直接的地点词汇
        text = "北京是中国的首都，上海是经济中心。"
        entities = self.ner._fallback_recognition(text, "zh")
        
        # 查找包含北京或上海的任何结果
        has_beijing = False
        has_shanghai = False
        
        for category, items in entities.items():
            for item in items:
                if "北京" in item:
                    has_beijing = True
                if "上海" in item:
                    has_shanghai = True
        
        # 至少应该识别出一个地点
        self.assertTrue(has_beijing or has_shanghai, 
                       f"未能识别出北京或上海，识别结果: {entities}")
    
    def test_zh_organization_detection(self):
        """测试中文组织机构检测"""
        # 使用纯组织名
        text = "腾讯和华为是中国知名企业。北京大学是著名学府。"
        entities = self.ner._fallback_recognition(text, "zh")
        
        # 查找包含这些关键词的任何结果
        has_company = False
        
        for category, items in entities.items():
            for item in items:
                if any(name in item for name in ["腾讯", "华为", "北京大学"]):
                    has_company = True
                    break
        
        # 至少应该识别出一个组织
        self.assertTrue(has_company, 
                       f"未能识别出任何组织，识别结果: {entities}")
    
    def test_en_person_recognition(self):
        """测试英文人名识别"""
        text = "John Smith and Mary Johnson are working on the project."
        entities = self.ner._fallback_recognition(text, "en")
        self.assertIn("PERSON", entities)
        self.assertIn("John Smith", entities["PERSON"])
        self.assertIn("Mary Johnson", entities["PERSON"])
    
    def test_en_company_detection(self):
        """测试英文公司检测"""
        text = "Google and Facebook are leading technology companies."
        entities = self.ner._fallback_recognition(text, "en")
        
        # 查找包含这些关键词的任何结果
        has_company = False
        
        for category, items in entities.items():
            for item in items:
                if any(name in item for name in ["Google", "Facebook"]):
                    has_company = True
                    break
        
        # 至少应该识别出一个公司
        self.assertTrue(has_company, 
                       f"未能识别出任何公司，识别结果: {entities}")
    
    def test_no_duplicate_entities(self):
        """测试实体去重功能"""
        text = "张三先生和张三先生一起参加会议。"
        entities = self.ner._fallback_recognition(text, "zh")
        self.assertIn("PERSON", entities)
        # 确认张三先生只出现一次
        self.assertEqual(1, entities["PERSON"].count("张三先生"))
    
    def test_date_and_time_detection(self):
        """测试日期和时间检测"""
        text = "会议将于2023年10月1日下午3点在会议室举行。"
        entities = self.ner._fallback_recognition(text, "zh")
        
        # 查找包含日期或时间的任何结果
        has_datetime = False
        
        for category, items in entities.items():
            for item in items:
                if any(term in item for term in 
                      ["2023年", "10月", "1日", "下午", "3点"]):
                    has_datetime = True
                    break
        
        # 至少应该识别出一个日期或时间
        self.assertTrue(has_datetime, 
                       f"未能识别出任何日期或时间，识别结果: {entities}")


class TestEntityTypeMapping(unittest.TestCase):
    """测试实体类型映射"""
    
    def test_entity_mapping_consistency(self):
        """测试实体类型映射的一致性"""
        # 检查所有中文模型实体类型都有映射
        essential_types = ["PERSON", "LOC", "GPE", "ORG", "DATE", "TIME"]
        for entity_type in essential_types:
            self.assertIn(entity_type, ENTITY_TYPE_MAPPING)
        
        # 检查关键映射是否正确
        self.assertEqual("PERSON", ENTITY_TYPE_MAPPING["PERSON"])
        self.assertEqual("LOCATION", ENTITY_TYPE_MAPPING["LOC"])
        self.assertEqual("LOCATION", ENTITY_TYPE_MAPPING["GPE"])
        self.assertEqual("ORGANIZATION", ENTITY_TYPE_MAPPING["ORG"])


class TestSpecificEntityExtraction(unittest.TestCase):
    """测试特定实体类型提取"""
    
    def setUp(self):
        self.ner = PolyglotNER(load_models=False)
        # 模拟recognize方法返回
        self.mock_entities = {
            "PERSON": ["张三", "李四"],
            "LOCATION": ["北京", "上海"],
            "ORGANIZATION": ["腾讯", "阿里巴巴"],
            "DATE": ["2023年10月1日"],
            "TIME": ["下午3点"]
        }
        self.ner.recognize = MagicMock(return_value=self.mock_entities)
    
    def test_extract_specific_person(self):
        """测试提取特定类型：人物"""
        entities = self.ner.extract_specific_entities("dummy text", "zh", ["PERSON"])
        self.assertEqual(["张三", "李四"], entities)
    
    def test_extract_multiple_types(self):
        """测试提取多种类型"""
        entities = self.ner.extract_specific_entities("dummy text", "zh", ["PERSON", "LOCATION"])
        self.assertEqual(["张三", "李四", "北京", "上海"], entities)
    
    def test_extract_with_mapping(self):
        """测试带映射的提取"""
        # LOC应该映射到LOCATION
        entities = self.ner.extract_specific_entities("dummy text", "zh", ["LOC"])
        self.assertEqual(["北京", "上海"], entities)


class TestLanguageAutoDetection(unittest.TestCase):
    """测试语言自动检测"""
    
    def setUp(self):
        # 确保get_global_ner返回我们控制的对象
        self.mock_ner = MagicMock()
        self.original_get_global_ner = get_global_ner
        get_global_ner.__globals__['_global_ner'] = self.mock_ner
    
    def tearDown(self):
        # 恢复原始函数
        get_global_ner.__globals__['_global_ner'] = None
    
    def test_detect_chinese(self):
        """测试检测中文文本"""
        text = "这是中文文本"
        self.mock_ner.extract_specific_entities = MagicMock(return_value=[])
        self.mock_ner.recognize = MagicMock(return_value={})
        
        extract_entities(text)
        
        # 验证正确检测为中文
        self.mock_ner.recognize.assert_called_with(text, "zh")
    
    def test_detect_english(self):
        """测试检测英文文本"""
        text = "This is English text"
        self.mock_ner.extract_specific_entities = MagicMock(return_value=[])
        self.mock_ner.recognize = MagicMock(return_value={})
        
        extract_entities(text)
        
        # 验证正确检测为英文
        self.mock_ner.recognize.assert_called_with(text, "en")
    
    def test_mixed_text_defaults_to_chinese(self):
        """测试混合文本默认为中文"""
        text = "This is mixed 中文和英文 text"
        self.mock_ner.extract_specific_entities = MagicMock(return_value=[])
        self.mock_ner.recognize = MagicMock(return_value={})
        
        extract_entities(text)
        
        # 有中文时应该识别为中文
        self.mock_ner.recognize.assert_called_with(text, "zh")


class TestGlobalNER(unittest.TestCase):
    """测试全局NER单例"""
    
    def setUp(self):
        # 重置全局NER
        get_global_ner.__globals__['_global_ner'] = None
    
    def test_global_ner_is_singleton(self):
        """测试全局NER是否为单例模式"""
        ner1 = get_global_ner()
        ner2 = get_global_ner()
        
        # 应该是同一个对象
        self.assertIs(ner1, ner2)
    
    def test_global_ner_init_params(self):
        """测试全局NER初始化参数"""
        with patch('nlp.entity_recognizer.PolyglotNER') as mock_polyglot:
            get_global_ner()
            # 验证初始化时load_models为False，实现延迟加载
            mock_polyglot.assert_called_with(load_models=False)


if __name__ == '__main__':
    unittest.main() 